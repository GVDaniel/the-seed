class_name ScannerSystem
extends Node
## Escanea el destino más cercano en rango. No dibuja UI.

const TARGET_GROUP := "scannable_targets"

signal scan_focus_changed(destination_id: String, display_name: String)
signal scan_completed(destination_id: String, was_new: bool)
signal scan_failed(reason: String)

@export var ship_path: NodePath

var _ship: Node2D
var _focus_id: String = ""
var _blocked: bool = false


func _ready() -> void:
	_ship = get_node_or_null(ship_path) as Node2D
	App.bus().hal_interface_toggled.connect(func(open: bool) -> void: _blocked = open)


func _physics_process(_delta: float) -> void:
	if _ship == null or not _ship.visible:
		_set_focus("")
		return
	var nearest := _find_nearest_in_range()
	var new_id := ""
	if nearest != null and nearest.has_method("get_stable_id"):
		new_id = str(nearest.call("get_stable_id"))
	_set_focus(new_id)
	if not _blocked and Input.is_action_just_pressed("scanner_scan"):
		_try_scan()


func get_focus_id() -> String:
	return _focus_id


func _set_focus(destination_id: String) -> void:
	if destination_id == _focus_id:
		return
	_focus_id = destination_id
	var name := ""
	if not destination_id.is_empty():
		var entry: DestinationEntry = App.notebook().get_catalog().get_entry(destination_id)
		name = entry.display_name if entry != null else destination_id
	scan_focus_changed.emit(destination_id, name)
	App.bus().scan_focus_changed.emit(destination_id, name)


func _try_scan() -> void:
	if _focus_id.is_empty():
		scan_failed.emit("Fuera de rango de escaneo")
		App.bus().scan_failed.emit("Fuera de rango de escaneo")
		return
	App.bus().destination_scanned.emit(_focus_id)
	var was_new: bool = App.notebook().record_discovery(_focus_id)
	scan_completed.emit(_focus_id, was_new)
	App.bus().scan_completed.emit(_focus_id, was_new)


func _find_nearest_in_range() -> Node:
	var best: Node = null
	var best_dist := INF
	for node in get_tree().get_nodes_in_group(TARGET_GROUP):
		if not node.has_method("is_in_scan_range"):
			continue
		if not bool(node.call("is_in_scan_range", _ship)):
			continue
		var spatial := node as Node2D
		if spatial == null:
			continue
		var d := _ship.global_position.distance_to(spatial.global_position)
		if d < best_dist:
			best_dist = d
			best = node
	return best
