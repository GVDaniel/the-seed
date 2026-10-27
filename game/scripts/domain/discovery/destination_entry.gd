class_name DestinationEntry
extends RefCounted
## Datos de un destino. Sin nodos ni UI.

var id: String = ""
var display_name: String = ""
var kind: String = ""
var short_description: String = ""
var scientific_facts: Array[Dictionary] = []
var arcade_disclaimer: String = ""


static func from_dict(data: Dictionary) -> DestinationEntry:
	var entry := DestinationEntry.new()
	entry.id = str(data.get("id", ""))
	entry.display_name = str(data.get("display_name", entry.id))
	entry.kind = str(data.get("kind", "unknown"))
	entry.short_description = str(data.get("short_description", ""))
	entry.arcade_disclaimer = str(data.get("arcade_disclaimer", ""))
	var facts: Array = data.get("scientific_facts", [])
	for fact in facts:
		if typeof(fact) == TYPE_DICTIONARY:
			entry.scientific_facts.append(fact)
	return entry


func to_summary_dict() -> Dictionary:
	return {
		"id": id,
		"display_name": display_name,
		"kind": kind,
		"short_description": short_description,
	}
