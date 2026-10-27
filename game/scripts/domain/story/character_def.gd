class_name CharacterDef
extends RefCounted
## Ficha de personaje (datos, sin nodos).

var id: String = ""
var display_name: String = ""
var role: String = ""
var portrait_path: String = ""
var sprite_path: String = ""
var idle_lines: PackedStringArray = PackedStringArray()
## Dónde vive (para la flecha de navegación desde otra escena).
var home: String = ""
var bio: String = ""
## "crew" (equipo de la historia) o "local" (vecinos, tenderos…).
var group: String = "crew"
var order: int = 0


static func from_dict(data: Dictionary) -> CharacterDef:
	var def := CharacterDef.new()
	def.id = str(data.get("id", ""))
	def.display_name = str(data.get("display_name", def.id))
	def.role = str(data.get("role", ""))
	def.portrait_path = str(data.get("portrait", ""))
	def.sprite_path = str(data.get("sprite", ""))
	def.idle_lines = PackedStringArray(data.get("idle_lines", []))
	def.home = str(data.get("home", ""))
	def.bio = str(data.get("bio", ""))
	def.group = str(data.get("group", "crew"))
	def.order = int(data.get("order", 0))
	return def


func idle_dialogue() -> Array:
	var lines: Array = []
	for text in idle_lines:
		lines.append({"who": id, "text": text})
	return lines
