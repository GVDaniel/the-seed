class_name SpaceDirector
extends Node
## Orquesta el vuelo: aparición junto al planeta de despegue, aterrizajes y textos de ayuda.
## No mueve la nave ni dibuja HUD.

enum Mode { SPACE, SURFACE }

signal mode_changed(mode: Mode)
signal hint_changed(text: String)

const SPAWN_GAP := 110.0

@export var ship_path: NodePath
@export var walker_path: NodePath
@export var camera_path: NodePath
@export var planet_path: NodePath
@export var starfield_path: NodePath

var mode: Mode = Mode.SPACE

var _ship: ShipController
var _camera: FollowCamera
var _starfield: Starfield
var _near_planet: PlanetZone
var _scan_focus_name: String = ""
var _scan_focus_id: String = ""
var _ui_busy: bool = false


func _ready() -> void:
	_ship = get_node(ship_path) as ShipController
	_camera = get_node(camera_path) as FollowCamera
	_starfield = get_node_or_null(starfield_path) as Starfield

	if _starfield != null and _camera != null:
		_starfield.bind_camera(_camera)
	_ship.land_requested.connect(_on_land_requested)
	App.bus().scan_focus_changed.connect(_on_scan_focus)

	var arrow := ObjectiveArrow.new()
	arrow.orbit_radius = 64.0
	arrow.hide_distance = 260.0
	arrow.arrow_scale = 1.8
	_ship.add_child(arrow)

	App.music().play("space")
	_ship.stats = ShipUpgrades.apply(_ship.stats)
	_ship.energy = _ship.stats.max_energy
	var router := App.router()
	_spawn_near(str(router.space_spawn_near))
	_camera.set_follow_target(_ship, true)
	mode_changed.emit(mode)
	hint_changed.emit(_compose_hint())
	if router.took_off_pending:
		router.took_off_pending = false
		var from := str(router.space_spawn_near)
		App.bus().took_off.emit.call_deferred(from)


func _spawn_near(destination_id: String) -> void:
	if destination_id.is_empty():
		return
	for node in get_tree().get_nodes_in_group(PlanetZone.LANDABLE_GROUP):
		var planet := node as PlanetZone
		if planet != null and planet.destination_id == destination_id:
			_ship.global_position = planet.global_position + Vector2(-(planet.body_radius + SPAWN_GAP), 0)
			_ship.rotation = 0.0
			_ship.velocity = Vector2.ZERO
			return


func set_ui_busy(busy: bool) -> void:
	_ui_busy = busy
	_ship.consume_input = not busy
	if busy:
		_ship.velocity = _ship.velocity * 0.5


func _physics_process(_delta: float) -> void:
	if _ship == null:
		return
	var near := _find_landable_in_range()
	if near != _near_planet:
		_near_planet = near
		hint_changed.emit(_compose_hint())
	for node in get_tree().get_nodes_in_group(ScannerSystem.TARGET_GROUP):
		if node.has_method("is_in_scan_range") and bool(node.call("is_in_scan_range", _ship)):
			App.story().notify_near(str(node.call("get_stable_id")))


func _find_landable_in_range() -> PlanetZone:
	for node in get_tree().get_nodes_in_group(PlanetZone.LANDABLE_GROUP):
		var planet := node as PlanetZone
		if planet != null and planet.contains_ship(_ship):
			return planet
	return null


func _on_scan_focus(destination_id: String, display_name: String) -> void:
	_scan_focus_name = display_name
	_scan_focus_id = destination_id
	hint_changed.emit(_compose_hint())


func _compose_hint() -> String:
	var parts: PackedStringArray = PackedStringArray()
	parts.append("W/S — Motor · A/D — Girar")
	if not _scan_focus_name.is_empty():
		parts.append("F — Escanear %s" % _scan_focus_name)
		if _scan_focus_id == "station_aurora":
			parts.append("T — Hablar con la Dra. Vega")
	if _near_planet != null:
		parts.append("E — Aterrizar en %s" % _near_planet.planet_name)
	parts.append("Tab — HAL")
	return " · ".join(parts)


func _on_land_requested() -> void:
	if _ui_busy or App.router().is_busy():
		return
	var planet := _find_landable_in_range()
	if planet == null:
		return
	var reason: String = App.story().land_block_reason(planet.destination_id)
	if not reason.is_empty():
		App.bus().mission_status_message.emit("HAL: %s" % reason)
		App.sfx().play("error")
		return
	App.sfx().play("land")
	App.router().go_surface(planet.surface_location, "ship")
