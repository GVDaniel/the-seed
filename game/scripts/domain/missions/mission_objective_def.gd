class_name MissionObjectiveDef
extends RefCounted
## Definición de un objetivo (datos, sin UI).

var id: String = ""
var description: String = ""
var hud_hint: String = ""
var condition: Dictionary = {}
## Id del objeto del mundo al que apunta la flecha de navegación (opcional).
var target: String = ""
## Lugar donde ocurre ("space", "earth", "moon", "mars"). La flecha lo usa si el objetivo no está en la escena.
var location: String = ""
## Consecuencias al cumplirlo: {install_engine, refuel, repair, set_flag} (StoryDirector las aplica).
var effects: Dictionary = {}


func condition_type() -> String:
	return str(condition.get("type", ""))


## Valor principal de la condición (npc_id, destination_id, item_id…).
func condition_value() -> String:
	for key in ["npc_id", "destination_id", "item_id", "challenge_id", "target_id", "encounter_id", "from"]:
		if condition.has(key):
			return str(condition[key])
	return ""


static func from_dict(data: Dictionary) -> MissionObjectiveDef:
	var obj := MissionObjectiveDef.new()
	obj.id = str(data.get("id", ""))
	obj.description = str(data.get("description", ""))
	obj.hud_hint = str(data.get("hud_hint", obj.description))
	var cond: Variant = data.get("condition", {})
	if typeof(cond) == TYPE_DICTIONARY:
		obj.condition = cond
	obj.target = str(data.get("target", obj.condition_value()))
	obj.location = str(data.get("location", ""))
	var fx: Variant = data.get("effects", {})
	obj.effects = fx if typeof(fx) == TYPE_DICTIONARY else {}
	return obj


## Objetos que pide una condición have_items.
func item_ids() -> PackedStringArray:
	return PackedStringArray(condition.get("item_ids", []))
