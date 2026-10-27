class_name HalScanlines
extends Control
## Líneas de barrido de monitor sobre la interfaz de HAL.


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	resized.connect(queue_redraw)


func _draw() -> void:
	var y := 0.0
	while y < size.y:
		draw_line(Vector2(0, y), Vector2(size.x, y), Color(0.24, 0.9, 0.79, 0.035), 1.0)
		y += 4.0
