class_name DestinationCatalog
extends RefCounted
## Carga fichas científicas desde JSON. Separado de la presentación.

const DATA_DIR := "res://assets/data/destinations/"

var _by_id: Dictionary = {}


func load_all() -> void:
	_by_id.clear()
	var dir := DirAccess.open(DATA_DIR)
	if dir == null:
		push_warning("DestinationCatalog: no se pudo abrir %s" % DATA_DIR)
		return
	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and file_name.ends_with(".json"):
			_load_file(DATA_DIR.path_join(file_name))
		file_name = dir.get_next()
	dir.list_dir_end()


func _load_file(path: String) -> void:
	var raw := FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("DestinationCatalog: JSON inválido %s" % path)
		return
	var entry := DestinationEntry.from_dict(parsed)
	if entry.id.is_empty():
		push_warning("DestinationCatalog: id vacío en %s" % path)
		return
	_by_id[entry.id] = entry


func has_id(destination_id: String) -> bool:
	return _by_id.has(destination_id)


func get_entry(destination_id: String) -> DestinationEntry:
	return _by_id.get(destination_id, null) as DestinationEntry


func all_ids() -> PackedStringArray:
	return PackedStringArray(_by_id.keys())


func size() -> int:
	return _by_id.size()
