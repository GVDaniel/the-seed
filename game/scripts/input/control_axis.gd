class_name ControlAxis
extends RefCounted
## Eje virtual compartido: teclado ahora, táctil después (set_virtual_*).

var thrust: float = 0.0
var turn: float = 0.0
var move: Vector2 = Vector2.ZERO
var land_pressed: bool = false
var takeoff_pressed: bool = false


func clear_pulses() -> void:
	land_pressed = false
	takeoff_pressed = false


func set_virtual_thrust(value: float) -> void:
	thrust = clampf(value, -1.0, 1.0)


func set_virtual_turn(value: float) -> void:
	turn = clampf(value, -1.0, 1.0)


func set_virtual_move(value: Vector2) -> void:
	move = value.limit_length(1.0)
