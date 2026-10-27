class_name ResourcePips
extends Control
## Fila de puntos (energía, combo o chispas solares): llenos, vacíos y un brillo al cambiar.

var _max: int = 1
var _value: int = 0
var _color: Color = Color.WHITE
var _round: bool = false
var _size: float = 12.0
var _glow: float = 0.0


func setup(maximum: int, color: Color, round_pips: bool, pip_size: float = 12.0) -> void:
	_max = maxi(1, maximum)
	_color = color
	_round = round_pips
	_size = pip_size
	_resize()


func set_value(value: int, maximum: int = -1) -> void:
	if maximum > 0 and maximum != _max:
		_max = maximum
		_resize()
	if value > _value:
		_glow = 1.0
	_value = clampi(value, 0, _max)
	queue_redraw()


func _resize() -> void:
	custom_minimum_size = Vector2(_max * (_size + 4.0), _size + 2.0)
	queue_redraw()


func _process(delta: float) -> void:
	if _glow > 0.0:
		_glow = maxf(0.0, _glow - delta * 2.5)
		queue_redraw()


func _draw() -> void:
	for i in _max:
		var c := Vector2(i * (_size + 4.0) + _size * 0.5, _size * 0.5 + 1.0)
		var full := i < _value
		var col := _color if full else Color(_color, 0.18)
		if full and i == _value - 1 and _glow > 0.0:
			col = col.lerp(Color.WHITE, _glow * 0.7)
		if _round:
			draw_circle(c, _size * 0.5, col)
			if full:
				draw_circle(c + Vector2(-1.5, -1.5), _size * 0.18, Color(1, 1, 1, 0.6))
		else:
			var r := Rect2(c - Vector2(_size, _size) * 0.5, Vector2(_size, _size * 0.75))
			draw_rect(r, col)
			draw_rect(r, Color(_color, 0.6), false, 1.0)
