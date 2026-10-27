extends Node
## Navegación entre escenas con fundido. Guarda el "a dónde volver" (lab, combate, despegue).

const SURFACE_SCENE := "res://scenes/surface/surface_level.tscn"
const SPACE_SCENE := "res://scenes/space/space_main.tscn"
const LAB_SCENE := "res://scenes/lab/probe_lab.tscn"
const MENU_SCENE := "res://scenes/ui/main_menu.tscn"
const CUTSCENE_SCENE := "res://scenes/story/cutscene.tscn"
const BATTLE_SCENE := "res://scenes/battle/battle.tscn"

## Superficie a cargar ("earth", "moon", "mars").
var pending_surface: String = ""
## Punto de aparición dentro del mapa ("start", "ship"…).
var pending_spawn: String = "ship"
## Al volver al espacio, aparecer junto a este destino.
var space_spawn_near: String = ""
var lab_challenge_id: String = ""
var lab_return_location: String = ""
## Posición del jugador al dejar la superficie por una terminal o un combate.
var return_position: Vector2 = Vector2.ZERO
## La próxima escena espacial debe avisar de un despegue (objetivo "takeoff").
var took_off_pending: bool = false
var battle_id: String = ""
var battle_return_location: String = ""
## Pruebas headless: el combate elige acciones y pulsa a tiempo él solo.
var battle_autoplay: bool = false
var cutscene_id: String = ""
var cutscene_next_location: String = ""

var _fade_layer: CanvasLayer
var _fade: ColorRect
var _busy: bool = false


func _ready() -> void:
	_fade_layer = CanvasLayer.new()
	_fade_layer.layer = 100
	add_child(_fade_layer)
	_fade = ColorRect.new()
	_fade.color = Color(0.043, 0.071, 0.125, 0.0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade_layer.add_child(_fade)


func go_location(location_id: String, spawn: String = "ship") -> void:
	if location_id == "space" or location_id.is_empty():
		go_space(space_spawn_near)
	else:
		go_surface(location_id, spawn)


func go_surface(location_id: String, spawn: String = "ship") -> void:
	pending_surface = location_id
	pending_spawn = spawn
	App.game_state().set_location(location_id)
	_change(SURFACE_SCENE)


func go_space(near_destination: String = "", from_takeoff: bool = false) -> void:
	space_spawn_near = near_destination
	took_off_pending = from_takeoff
	App.game_state().set_location("space")
	_change(SPACE_SCENE)


func open_lab(challenge_id: String) -> void:
	lab_challenge_id = challenge_id
	lab_return_location = str(App.game_state().location)
	_change(LAB_SCENE)


## Laboratorio libre (menú o HUD de vuelo): al salir vuelve a donde estaba.
func open_free_lab(return_to: String = "menu") -> void:
	lab_challenge_id = ""
	lab_return_location = return_to
	_change(LAB_SCENE)


func return_from_lab() -> void:
	var back := lab_return_location
	lab_challenge_id = ""
	lab_return_location = ""
	if back == "menu" or back.is_empty():
		go_menu()
	elif back == "space":
		go_space(space_spawn_near)
	else:
		go_surface(back, "return")


## La superficie guarda return_position antes de llamar.
func start_battle(encounter_id: String) -> void:
	battle_id = encounter_id
	battle_return_location = str(App.game_state().location)
	_change(BATTLE_SCENE)


## result = "victory" | "defeat" | "retreat".
func return_from_battle(result: String) -> void:
	var id := battle_id
	var back := battle_return_location
	battle_id = ""
	battle_return_location = ""
	App.bus().battle_finished.emit(id, result)
	go_surface(back if not back.is_empty() else str(App.game_state().region), "return")


func play_cutscene(id: String, next_location: String) -> void:
	cutscene_id = id
	cutscene_next_location = next_location
	_change(CUTSCENE_SCENE)


func go_menu() -> void:
	_change(MENU_SCENE)


func is_busy() -> bool:
	return _busy


func _change(path: String) -> void:
	if _busy:
		return
	_busy = true
	var tree := get_tree()
	if DisplayServer.get_name() != "headless":
		var t := create_tween()
		t.tween_property(_fade, "color:a", 1.0, 0.25)
		await t.finished
	tree.change_scene_to_file(path)
	await tree.process_frame
	await tree.process_frame
	if DisplayServer.get_name() != "headless":
		var t2 := create_tween()
		t2.tween_property(_fade, "color:a", 0.0, 0.3)
		await t2.finished
	_busy = false
