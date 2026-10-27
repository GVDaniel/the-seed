class_name HalFollower
extends Node2D
## HAL flota detrás de Andrés: panel plateado con la lente roja que late (homenaje a HAL 9000).

const SHEET := "res://assets/art/characters/hal.png"
const GLOW := "res://assets/art/ui/hal_glow.png"
const PULSE_FRAMES := [0, 1, 2, 3]

@export var follow_offset: Vector2 = Vector2(-16, -26)
## En mapas oscuros, la lente de HAL ilumina un poco de rojo su alrededor.
var with_light: bool = false

var target: Node2D
var _sprite: Sprite2D
var _glow: Sprite2D
var _t: float = 0.0


func _ready() -> void:
	_glow = Sprite2D.new()
	_glow.texture = load(GLOW)
	_glow.scale = Vector2(0.6, 0.6)
	_glow.position = Vector2(0, -1)
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_glow.material = additive
	add_child(_glow)
	_sprite = Sprite2D.new()
	_sprite.texture = load(SHEET)
	_sprite.hframes = 4
	add_child(_sprite)
	if with_light:
		add_child(NeonLight.from_data({"color": "#ff4a32", "energy": 0.7, "scale": 0.9}))
	z_index = 5


func snap() -> void:
	if target != null:
		global_position = target.global_position + follow_offset


func _process(delta: float) -> void:
	_t += delta
	if target != null:
		var side := follow_offset
		var v: Variant = target.get("velocity")
		if typeof(v) == TYPE_VECTOR2 and (v as Vector2).x < -10.0:
			side.x = absf(follow_offset.x)
		var goal := target.global_position + side + Vector2(0, sin(_t * 2.6) * 2.5)
		global_position = global_position.lerp(goal, 1.0 - exp(-5.0 * delta))
	_sprite.frame = PULSE_FRAMES[int(_t * 5.0) % PULSE_FRAMES.size()]
	_glow.modulate.a = 0.55 + 0.35 * sin(_t * 3.1)
