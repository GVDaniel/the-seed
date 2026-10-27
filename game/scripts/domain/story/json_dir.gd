class_name JsonDir
extends Object
## Lee todos los .json (diccionarios) de una carpeta res://.


static func load_dicts(dir_path: String) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var dir := DirAccess.open(dir_path)
	if dir == null:
		push_warning("JsonDir: no se pudo abrir %s" % dir_path)
		return out
	var files := Array(dir.get_files())
	files.sort()
	for file_name in files:
		if not str(file_name).ends_with(".json"):
			continue
		var parsed: Variant = load_dict(dir_path.path_join(file_name))
		if typeof(parsed) == TYPE_DICTIONARY and not (parsed as Dictionary).is_empty():
			out.append(parsed)
	return out


static func load_dict(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("JsonDir: JSON inválido %s" % path)
		return {}
	return parsed
