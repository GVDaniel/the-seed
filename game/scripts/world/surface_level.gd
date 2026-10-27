class_name SurfaceLevel
extends Node2D
## Escena a pie: construye el mapa desde JSON y enruta interacciones a StoryDirector / Router.
## Sirve igual para exteriores (Tierra, Luna, Marte) e interiores (tiendas, bares).

const MAPS_DIR := "res://assets/data/maps/"
const CAMERA_ZOOM := 3.0

## Mapa por defecto si no llega uno desde Router (útil en editor y tests).
@export var location_id: String = "earth"

@onready var _ground: TileMapLayer = %Ground
@onready var _objects: TileMapLayer = %Objects
@onready var _entities: Node2D = %Entities
@onready var _player: WalkerController = %Player
@onready var _camera: FollowCamera = %FollowCamera
@onready var _interaction: InteractionSystem = %InteractionSystem
@onready var _hud: SurfaceHud = %SurfaceHud
@onready var _dialogue: DialoguePanel = %DialoguePanel
@onready var _analysis: AnalysisPanel = %AnalysisPanel
@onready var _hal_ui: HalInterface = %HalInterface
@onready var _shop: ShopPanel = %ShopPanel
@onready var _void: ColorRect = %Void
@onready var _ambient: CanvasModulate = %Ambient
@onready var _weather: CPUParticles2D = %Weather

var map: Dictionary = {}
var spawner: SurfaceEntitySpawner = SurfaceEntitySpawner.new()
## Tráfico, máquinas, naves y peatones de fondo (clave "ambient_life" del mapa).
var ambient: AmbientLife
var _hal: HalFollower


func _ready() -> void:
	var router := App.router()
	if not str(router.pending_surface).is_empty():
		location_id = str(router.pending_surface)
	map = JsonDir.load_dict(MAPS_DIR + location_id + ".json")
	if map.is_empty():
		push_error("SurfaceLevel: mapa no encontrado %s" % location_id)
		return
	App.game_state().set_location(location_id, str(map.get("region", location_id)))
	_build_world()
	_place_player(str(router.pending_spawn))
	_setup_presentation()
	_hal_ui.set_surface_context(map, _player)
	App.music().play(str(map.get("music", "mission")))
	App.bus().interaction_requested.connect(_on_interaction)
	App.bus().story_event.connect(_on_story_event)
	App.bus().dialogue_finished.connect(_on_dialogue_finished)
	call_deferred("_on_arrival", str(router.pending_spawn))


func _build_world() -> void:
	var size := SurfaceMapBuilder.paint(map, _ground, _objects)
	SurfaceMapBuilder.add_bounds(self, size)
	spawner.spawn_all(map.get("entities", []), _entities)
	for entry in spawner.entities.values():
		var npc := entry["node"] as NpcActor
		if npc != null:
			npc.set_player(_player)
	var px := size * TileCatalog.TILE
	ambient = AmbientLife.new()
	ambient.name = "AmbientLife"
	add_child(ambient)
	ambient.setup(map, _entities, _player, Vector2(px))
	_camera.zoom = Vector2(CAMERA_ZOOM, CAMERA_ZOOM)
	_camera.limit_left = 0
	_camera.limit_top = 0
	_camera.limit_right = px.x
	_camera.limit_bottom = px.y


func _place_player(spawn: String) -> void:
	var pos: Vector2 = spawner.spawns.get("ship", spawner.spawns.get("entrance", Vector2(64, 64)))
	if spawn == "return" and App.router().return_position != Vector2.ZERO:
		pos = App.router().return_position
	elif spawner.spawns.has(spawn):
		pos = spawner.spawns[spawn]
	_player.activate_at(pos)
	_player.face("down")
	_camera.set_follow_target(_player, true)
	_hal = HalFollower.new()
	_hal.target = _player
	_hal.with_light = bool(map.get("dark", false))
	_entities.add_child(_hal)
	_hal.snap()
	var arrow := ObjectiveArrow.new()
	arrow.orbit_radius = 22.0
	arrow.hide_distance = 40.0
	arrow.arrow_scale = 0.8
	_player.add_child(arrow)


func _setup_presentation() -> void:
	if bool(map.get("dark", false)):
		# Mundo nocturno: una luz suave acompaña a Andrés para que siempre se vea.
		_player.add_child(NeonLight.from_data({"color": "#cfe8ff", "energy": 0.55, "scale": 2.6, "offset": [0, -10]}))
	_hud.set_location_name(str(map.get("display_name", location_id)))
	_void.color = Color(str(map.get("void_color", "#0b1220")))
	_ambient.color = Color(AmbientLife.tint_of(map))
	match str(map.get("weather", "")):
		"dust":
			_weather.emitting = true
			_weather.color = Color(1.0, 0.86, 0.7, 0.75)
		"haze":
			_weather.emitting = true
			_weather.color = Color(1.0, 0.95, 0.8, 0.35)
			_weather.amount = 60
		"rain":
			_weather.texture = load("res://assets/art/fx/rain_drop.png")
			_weather.position = Vector2(640, -20)
			_weather.emission_rect_extents = Vector2(760, 10)
			_weather.direction = Vector2(-0.18, 1)
			_weather.initial_velocity_min = 520.0
			_weather.initial_velocity_max = 700.0
			_weather.scale_amount_min = 2.0
			_weather.scale_amount_max = 3.0
			_weather.lifetime = 1.6
			_weather.preprocess = 2.0
			_weather.amount = 220
			_weather.color = Color(0.75, 0.95, 1.0, 0.55)
			_weather.emitting = true
		_:
			_weather.emitting = false


func _on_arrival(spawn: String) -> void:
	if spawn == "ship" and spawner.spawns.has("ship"):
		App.bus().landed_on.emit(location_id)
	var flag := "arrived_%s" % location_id
	if not App.game_state().has_flag(flag):
		App.game_state().set_flag(flag)
		var lines: Array = map.get("arrival_lines", [])
		if not lines.is_empty():
			App.story().play_lines(lines)


func _process(_delta: float) -> void:
	var busy: bool = _dialogue.is_open() or _analysis.visible or _hal_ui.is_open() or _shop.is_open() \
			or App.router().is_busy()
	_player.consume_input = not busy
	_interaction.enabled = not busy


# ------------------------------------------------------------ interacciones

func _on_interaction(target_id: String, kind: String) -> void:
	var entry: Dictionary = spawner.entities.get(target_id, {})
	var data: Dictionary = entry.get("data", {})
	match kind:
		"npc":
			if data.has("shop"):
				App.story().mark_met(target_id)
				App.bus().shop_requested.emit(str(data["shop"]))
			else:
				App.story().talk_to(target_id)
		"door":
			_use_door(data)
		"item":
			_collect(target_id, data)
		"terminal":
			_use_terminal(target_id, data)
		"ship":
			_try_takeoff()
		"object":
			_use_object(target_id, data)
		"sign":
			App.story().play_lines(data.get("lines", []))
		"enemy":
			_approach_enemy(target_id, data)
		"service":
			_use_service(data)


func _collect(item_id: String, data: Dictionary) -> void:
	var story := App.story()
	if not story.can_collect(item_id):
		story.hal_says(str(data.get("locked_text", "Todavía no. Revisa el objetivo, arriba a la derecha.")))
		App.sfx().play("error")
		return
	App.game_state().add_item(item_id)
	var node: Node2D = spawner.entities[item_id]["node"]
	node.visible = false
	App.sfx().play("pickup")
	App.bus().item_collected.emit(item_id)
	var lines: Array = data.get("collect_lines", [])
	if not lines.is_empty():
		story.play_lines(lines)


func _use_terminal(_terminal_id: String, data: Dictionary) -> void:
	var challenge_id := str(data.get("challenge_id", ""))
	var story := App.story()
	var solved: bool = App.game_state().solved_puzzles.has(challenge_id)
	var current: bool = story.is_current_objective("solve_challenge", challenge_id)
	if not current and not solved:
		story.hal_says(str(data.get("locked_text", "Esta terminal se activará cuando la misión lo pida.")))
		App.sfx().play("error")
		return
	App.sfx().play("confirm")
	App.router().return_position = _player.global_position
	App.router().open_lab(challenge_id)


func _use_object(object_id: String, data: Dictionary) -> void:
	var story := App.story()
	var flag := str(data.get("done_flag", ""))
	if not flag.is_empty() and App.game_state().has_flag(flag):
		story.play_lines(data.get("done_lines", []))
		return
	if not story.can_interact(object_id):
		story.hal_says(str(data.get("locked_text", "Aún no es el momento.")))
		App.sfx().play("error")
		return
	if not flag.is_empty():
		App.game_state().set_flag(flag)
	var done_sprite := str(data.get("sprite_done", ""))
	if not done_sprite.is_empty():
		spawner.set_sprite(object_id, done_sprite)
	App.sfx().play("success")
	App.bus().world_interacted.emit(object_id)
	var lines: Array = data.get("use_lines", [])
	if not lines.is_empty():
		story.play_lines(lines)


func _approach_enemy(enemy_id: String, data: Dictionary) -> void:
	var story := App.story()
	var encounter := str(data.get("encounter", ""))
	var flag := str(data.get("done_flag", ""))
	if not flag.is_empty() and App.game_state().has_flag(flag):
		story.play_lines(data.get("done_lines", []))
		return
	if not story.can_battle(encounter):
		story.hal_says(str(data.get("locked_text", "Mejor no acercarse todavía.")))
		App.sfx().play("error")
		return
	App.router().return_position = _player.global_position + Vector2(-20, 6)
	var intro: Array = data.get("intro_lines", [])
	if intro.is_empty():
		App.router().start_battle(encounter)
		return
	story.play_lines(intro, "battle:%s:%s" % [encounter, enemy_id])


func _on_dialogue_finished(context: String) -> void:
	if not context.begins_with("battle:"):
		return
	var parts := context.split(":")
	if parts.size() >= 2:
		App.sfx().play("confirm")
		App.router().start_battle(parts[1])


func _use_service(data: Dictionary) -> void:
	var free_flag := str(data.get("free_flag", ""))
	var free: bool = not free_flag.is_empty() and App.game_state().has_flag(free_flag)
	var ship := App.ship()
	var quote: Dictionary = ship.service_quote(float(data.get("rate", 0.5)))
	var msg: String = ship.service(float(data.get("rate", 0.5)), free)
	var lines: Array = []
	if free:
		lines.append({"who": "hal", "text": str(data.get("free_text", "Servicio gratuito."))})
	elif int(quote["cost"]) > 0:
		lines.append({"who": "hal", "text": "Presupuesto: %d créditos por llenar el tanque y reparar el casco." % int(quote["cost"])})
	lines.append({"who": "hal", "text": msg})
	lines.append({"who": "hal", "text": "ASTRA: combustible %d/%d · casco %d %%." % [
		int(round(ship.fuel)), int(round(ship.capacity())), int(round(ship.hull))]})
	App.sfx().play("pickup")
	App.story().play_lines(lines)


func _use_door(data: Dictionary) -> void:
	var target := str(data.get("target", ""))
	if target.is_empty():
		App.story().play_lines(data.get("lines", []))
		return
	App.sfx().play("confirm")
	App.router().go_surface(target, str(data.get("spawn", "entrance")))


func _try_takeoff() -> void:
	var story := App.story()
	var reason: String = story.takeoff_block_reason(location_id)
	if not reason.is_empty():
		story.hal_says(reason)
		App.sfx().play("error")
		return
	App.sfx().play("takeoff")
	App.router().go_space(location_id, true)


func _on_story_event(event_id: String) -> void:
	if event_id == "ending_teaser":
		App.router().play_cutscene("ending", location_id)
