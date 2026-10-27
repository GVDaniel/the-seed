class_name MissionDirector
extends Node
## En el espacio: «T» habla con el personaje del destino cercano (p. ej. Vega en Aurora)
## y pausa la nave mientras hay paneles abiertos (diálogo, análisis, HAL). Las reglas viven en StoryDirector.

@export var ship_path: NodePath
@export var director_path: NodePath = ^"../SpaceDirector"

var _ship: Node2D
var _director: SpaceDirector
var _dialogue_open: bool = false
var _panels_open: int = 0
var _hal_open: bool = false
var _ignore_talk_frames: int = 0


func _ready() -> void:
	_ship = get_node_or_null(ship_path) as Node2D
	_director = get_node_or_null(director_path) as SpaceDirector
	var bus := App.bus()
	bus.dialogue_requested.connect(func(_s: String, _l: Array, _c: String) -> void:
		_dialogue_open = true
		_sync_busy()
	)
	bus.dialogue_finished.connect(func(_c: String) -> void:
		_dialogue_open = false
		_ignore_talk_frames = 3
		_sync_busy()
	)
	bus.scan_completed.connect(func(_id: String, _new: bool) -> void:
		_panels_open = 1
		_sync_busy()
	)
	bus.analysis_panel_closed.connect(func() -> void:
		_panels_open = 0
		_sync_busy()
	)
	bus.hal_interface_toggled.connect(func(open: bool) -> void:
		_hal_open = open
		_sync_busy()
	)


func _sync_busy() -> void:
	if _director != null:
		_director.set_ui_busy(_dialogue_open or _panels_open > 0 or _hal_open)


func _physics_process(_delta: float) -> void:
	if _ignore_talk_frames > 0:
		_ignore_talk_frames -= 1
		return
	if _ship == null or not _ship.visible or _dialogue_open or _hal_open:
		return
	if Input.is_action_just_pressed("interact_talk"):
		var npc := _npc_in_range()
		if not npc.is_empty():
			App.story().talk_to(npc)


func _npc_in_range() -> String:
	for node in get_tree().get_nodes_in_group(ScannerSystem.TARGET_GROUP):
		var npc := str(node.get("npc_id")) if "npc_id" in node else ""
		if npc.is_empty():
			continue
		if node.has_method("is_in_scan_range") and bool(node.call("is_in_scan_range", _ship)):
			return npc
	return ""
