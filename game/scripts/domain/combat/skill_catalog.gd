class_name SkillCatalog
extends RefCounted
## Técnicas de combate cargadas desde JSON.

const PATH := "res://assets/data/combat/skills.json"

var _defs: Dictionary = {}
var _order: PackedStringArray = PackedStringArray()


func load_all() -> void:
	_defs.clear()
	_order.clear()
	for row in JsonDir.load_dict(PATH).get("skills", []):
		if typeof(row) != TYPE_DICTIONARY:
			continue
		var s := CombatSkill.from_dict(row)
		if not s.id.is_empty():
			_defs[s.id] = s
			_order.append(s.id)


func get_def(skill_id: String) -> CombatSkill:
	return _defs.get(skill_id, null) as CombatSkill


func all() -> Array[CombatSkill]:
	var out: Array[CombatSkill] = []
	for id in _order:
		out.append(_defs[id])
	return out


## Técnicas que el personaje conoce con sus puntos actuales (básico incluido, combos aparte).
func known_by(user: String, points: Dictionary) -> PackedStringArray:
	var out := PackedStringArray()
	for s in all():
		if s.user == user and HeroProgression.meets(s.requires, points):
			out.append(s.id)
	return out


func combos() -> Array[CombatSkill]:
	var out: Array[CombatSkill] = []
	for s in all():
		if s.kind == "combo":
			out.append(s)
	return out
