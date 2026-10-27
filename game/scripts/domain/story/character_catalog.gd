class_name CharacterCatalog
extends RefCounted
## Carga personajes desde JSON.

const DATA_DIR := "res://assets/data/characters/"

var _by_id: Dictionary = {}


func load_all() -> void:
	_by_id.clear()
	for data in JsonDir.load_dicts(DATA_DIR):
		var def := CharacterDef.from_dict(data)
		if not def.id.is_empty():
			_by_id[def.id] = def


func get_def(character_id: String) -> CharacterDef:
	return _by_id.get(character_id, null) as CharacterDef


func display_name(character_id: String) -> String:
	var def := get_def(character_id)
	return def.display_name if def != null else character_id


func size() -> int:
	return _by_id.size()


## Personajes en orden de presentación.
func all() -> Array[CharacterDef]:
	var out: Array[CharacterDef] = []
	for def in _by_id.values():
		out.append(def)
	out.sort_custom(func(a: CharacterDef, b: CharacterDef) -> bool: return a.order < b.order)
	return out
