class_name EngineDef
extends RefCounted
## Motor de ASTRA (datos de assets/data/ship/engines.json).

var id: String = ""
var display_name: String = ""
var fuel_name: String = ""
var fuel_capacity: float = 60.0
## Unidades por segundo con el empuje al máximo.
var fuel_use: float = 1.0
## Multiplicadores sobre ShipStats (el .tres es la referencia).
var speed_factor: float = 1.0
var accel_factor: float = 1.0
var description: String = ""
var fact: String = ""


static func from_dict(data: Dictionary) -> EngineDef:
	var def := EngineDef.new()
	def.id = str(data.get("id", ""))
	def.display_name = str(data.get("display_name", def.id))
	def.fuel_name = str(data.get("fuel_name", "combustible"))
	def.fuel_capacity = float(data.get("fuel_capacity", 60.0))
	def.fuel_use = float(data.get("fuel_use", 1.0))
	def.speed_factor = float(data.get("speed_factor", 1.0))
	def.accel_factor = float(data.get("accel_factor", 1.0))
	def.description = str(data.get("description", ""))
	def.fact = str(data.get("fact", ""))
	return def
