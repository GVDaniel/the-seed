class_name ItemDef
extends RefCounted
## Objeto del inventario de HAL (datos, sin nodos).

const CATEGORY_NAMES := {
	"equipo": "Equipo",
	"clave": "Objeto clave",
	"programa": "Programa",
	"muestra": "Muestra",
	"mejora": "Mejora de ASTRA",
	"recuerdo": "Recuerdo",
	"comida": "Comida y bebida",
}

var id: String = ""
var display_name: String = ""
var description: String = ""
var fact: String = ""
var category: String = ""
var icon_path: String = ""
var order: int = 0
## Equipo inicial: siempre está en el inventario.
var starter: bool = false
## Evento que lo entrega: {type: "solve_challenge" | "scan_destination", value: id}.
var granted_by: Dictionary = {}
## Multiplicadores para ASTRA (ver ShipUpgrades).
var effects: Dictionary = {}


static func from_dict(data: Dictionary) -> ItemDef:
	var def := ItemDef.new()
	def.id = str(data.get("id", ""))
	def.display_name = str(data.get("display_name", def.id))
	def.description = str(data.get("description", ""))
	def.fact = str(data.get("fact", ""))
	def.category = str(data.get("category", ""))
	def.icon_path = str(data.get("icon", ""))
	def.order = int(data.get("order", 0))
	def.starter = bool(data.get("starter", false))
	var grant: Variant = data.get("granted_by", {})
	def.granted_by = grant if typeof(grant) == TYPE_DICTIONARY else {}
	var fx: Variant = data.get("effects", {})
	def.effects = fx if typeof(fx) == TYPE_DICTIONARY else {}
	return def


func category_name() -> String:
	return str(CATEGORY_NAMES.get(category, category.capitalize()))


func is_granted_by(type: String, value: String) -> bool:
	return str(granted_by.get("type", "")) == type and str(granted_by.get("value", "")) == value
