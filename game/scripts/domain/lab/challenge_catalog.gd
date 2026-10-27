class_name ChallengeCatalog
extends RefCounted
## Retos del laboratorio indexados por id (assets/data/lab/*.json).

const DATA_DIR := "res://assets/data/lab/"

var _by_id: Dictionary = {}


func load_all() -> void:
	_by_id.clear()
	for data in JsonDir.load_dicts(DATA_DIR):
		var def := ChallengeDef.from_dict(data)
		if not def.id.is_empty():
			_by_id[def.id] = def


func get_def(challenge_id: String) -> ChallengeDef:
	return _by_id.get(challenge_id, null) as ChallengeDef


func has_id(challenge_id: String) -> bool:
	return _by_id.has(challenge_id)
