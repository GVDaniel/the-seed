class_name EncounterCatalog
extends RefCounted
## Encuentros de combate: assets/data/combat/encounters/<id>.json.

const DIR := "res://assets/data/combat/encounters/"


static func load_encounter(encounter_id: String) -> Dictionary:
	var path := DIR.path_join("%s.json" % encounter_id)
	if not FileAccess.file_exists(path):
		return {}
	return JsonDir.load_dict(path)


static func all_ids() -> PackedStringArray:
	var out := PackedStringArray()
	for row in JsonDir.load_dicts(DIR):
		out.append(str(row.get("id", "")))
	return out
