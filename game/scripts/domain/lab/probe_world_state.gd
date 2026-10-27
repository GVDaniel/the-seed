class_name ProbeWorldState
extends RefCounted
## Estado del mundo de la sonda. Sin UI.

const DIR_N := 0
const DIR_E := 1
const DIR_S := 2
const DIR_W := 3

var width: int = 5
var height: int = 5
var start_x: int = 0
var start_y: int = 0
var start_dir: int = DIR_E
var probe_x: int = 0
var probe_y: int = 0
var probe_dir: int = DIR_E
var poi_cells: Array[Vector2i] = []
var transmit_cell: Vector2i = Vector2i(-1, -1)
var blocked: Array[Vector2i] = []
var sample_cells: Array[Vector2i] = []
## Qué hace falta para ganar.
var goal_scan: bool = true
var goal_transmit: bool = true
var goal_collect: bool = false
var scanned_pois: Dictionary = {} # "x,y" -> true
var collected_samples: Dictionary = {} # "x,y" -> true
var has_transmitted: bool = false
var last_scan_ok: bool = false
var last_transmit_ok: bool = false


func reset_to_start() -> void:
	probe_x = start_x
	probe_y = start_y
	probe_dir = start_dir
	scanned_pois.clear()
	collected_samples.clear()
	has_transmitted = false
	last_scan_ok = false
	last_transmit_ok = false


func clone_initial_from_self() -> void:
	start_x = probe_x
	start_y = probe_y
	start_dir = probe_dir


func dir_vector(dir: int = -1) -> Vector2i:
	var d := probe_dir if dir < 0 else dir
	match d:
		DIR_N:
			return Vector2i(0, -1)
		DIR_E:
			return Vector2i(1, 0)
		DIR_S:
			return Vector2i(0, 1)
		DIR_W:
			return Vector2i(-1, 0)
	return Vector2i.ZERO


func in_bounds(x: int, y: int) -> bool:
	return x >= 0 and y >= 0 and x < width and y < height


func is_blocked(x: int, y: int) -> bool:
	return blocked.has(Vector2i(x, y))


func is_poi(x: int, y: int) -> bool:
	return poi_cells.has(Vector2i(x, y))


func poi_key(x: int, y: int) -> String:
	return "%d,%d" % [x, y]


func all_pois_scanned() -> bool:
	if poi_cells.is_empty():
		return false
	for cell in poi_cells:
		if not scanned_pois.has(poi_key(cell.x, cell.y)):
			return false
	return true


## Hay una muestra sin recoger en la casilla.
func has_sample(x: int, y: int) -> bool:
	return sample_cells.has(Vector2i(x, y)) and not collected_samples.has(poi_key(x, y))


func all_samples_collected() -> bool:
	for cell in sample_cells:
		if not collected_samples.has(poi_key(cell.x, cell.y)):
			return false
	return true


func is_victory() -> bool:
	if goal_scan and not all_pois_scanned():
		return false
	if goal_collect and not all_samples_collected():
		return false
	if goal_transmit and not has_transmitted:
		return false
	return goal_scan or goal_collect or goal_transmit


func to_snapshot() -> Dictionary:
	return {
		"probe_x": probe_x,
		"probe_y": probe_y,
		"probe_dir": probe_dir,
		"scanned_pois": scanned_pois.duplicate(),
		"collected_samples": collected_samples.duplicate(),
		"has_transmitted": has_transmitted,
		"victory": is_victory(),
	}
