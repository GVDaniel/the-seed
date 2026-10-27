class_name NeonLight
extends PointLight2D
## Luz de neón para mapas oscuros. Opcionalmente parpadea como un letrero viejo.

const TEXTURE := "res://assets/art/fx/light_radial.png"

@export var flicker: bool = false

var _base_energy: float = 1.0
var _t: float = 0.0


static func from_data(data: Dictionary) -> NeonLight:
	var light := NeonLight.new()
	light.color = Color(str(data.get("color", "#ffffff")))
	light.energy = float(data.get("energy", 1.0))
	light.texture_scale = float(data.get("scale", 2.0))
	light.flicker = bool(data.get("flicker", false))
	var off: Array = data.get("offset", [0, 0])
	light.position = Vector2(float(off[0]), float(off[1]))
	return light


func _ready() -> void:
	texture = load(TEXTURE)
	_base_energy = energy
	_t = randf() * 10.0


func _process(delta: float) -> void:
	if not flicker:
		return
	_t += delta
	# Mayormente encendido, con apagones breves e irregulares.
	var off := sin(_t * 13.0) > 0.93 or sin(_t * 2.3 + 1.0) > 0.985
	energy = _base_energy * (0.25 if off else 1.0)
