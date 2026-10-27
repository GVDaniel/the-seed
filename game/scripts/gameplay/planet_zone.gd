class_name PlanetZone
extends Area2D
## Planeta escaneable y, si tiene superficie, aterrizable (id estable).

const SCAN_GROUP := "scannable_targets"
const LANDABLE_GROUP := "landable_planets"

@export var destination_id: String = "earth"
@export var planet_name: String = "Tierra"
@export var body_radius: float = 180.0
@export var landing_radius: float = 280.0
@export var scan_radius: float = 340.0
@export var surface_spawn_offset: Vector2 = Vector2(0, -40)
@export var body_color: Color = Color(0.25, 0.45, 0.85, 1.0)
## Sprite pixel art (si falta, se dibuja un círculo).
@export var texture: Texture2D
@export var sprite_scale: int = 3
## Id del mapa de superficie ("earth", "moon", "mars"). Vacío = no aterrizable.
@export var surface_location: String = ""

@onready var _body_visual: Polygon2D = %BodyVisual
@onready var _ring_visual: Polygon2D = %RingVisual
@onready var _label: Label = %PlanetLabel
@onready var _collision: CollisionShape2D = %LandingShape


func _ready() -> void:
	add_to_group(SCAN_GROUP)
	add_to_group(ScannerSystem.TARGET_GROUP)
	add_to_group(Interactable.NAV_GROUP)
	if not surface_location.is_empty():
		add_to_group(LANDABLE_GROUP)
	monitoring = true
	monitorable = false
	_resolve_label()
	_configure_shapes()
	_build_visuals()


func get_stable_id() -> String:
	return destination_id


func get_nav_id() -> String:
	return destination_id


func get_scan_radius() -> float:
	return scan_radius


func is_landable() -> bool:
	return not surface_location.is_empty()


func is_in_scan_range(ship: Node2D) -> bool:
	if ship == null:
		return false
	return global_position.distance_to(ship.global_position) <= scan_radius


func get_surface_spawn_global() -> Vector2:
	return global_position + surface_spawn_offset


func contains_ship(ship: Node2D) -> bool:
	return global_position.distance_to(ship.global_position) <= landing_radius


func _resolve_label() -> void:
	var entry: DestinationEntry = App.notebook().get_catalog().get_entry(destination_id)
	if entry != null:
		_label.text = entry.display_name
		planet_name = entry.display_name
	else:
		_label.text = planet_name
	_label.position = Vector2(-_label.size.x * 0.5, -body_radius - 46.0)


func _configure_shapes() -> void:
	var circle := CircleShape2D.new()
	circle.radius = landing_radius
	_collision.shape = circle


func _build_visuals() -> void:
	_ring_visual.polygon = _make_ring_poly(scan_radius * 0.97, scan_radius, 72)
	_ring_visual.color = Color(0.24, 0.91, 0.79, 0.16)
	if texture != null:
		_body_visual.visible = false
		var sprite := Sprite2D.new()
		sprite.name = "BodySprite"
		sprite.texture = texture
		sprite.scale = Vector2(sprite_scale, sprite_scale)
		add_child(sprite)
		move_child(sprite, _ring_visual.get_index() + 1)
		return
	_body_visual.polygon = _make_circle_poly(body_radius, 48)
	_body_visual.color = body_color


func _make_circle_poly(radius: float, points: int) -> PackedVector2Array:
	var poly := PackedVector2Array()
	for i in points:
		var a := TAU * float(i) / float(points)
		poly.append(Vector2(cos(a), sin(a)) * radius)
	return poly


func _make_ring_poly(inner_r: float, outer_r: float, points: int) -> PackedVector2Array:
	var poly := PackedVector2Array()
	for i in points + 1:
		var a := TAU * float(i) / float(points)
		poly.append(Vector2(cos(a), sin(a)) * outer_r)
	for i in range(points, -1, -1):
		var a := TAU * float(i) / float(points)
		poly.append(Vector2(cos(a), sin(a)) * inner_r)
	return poly
