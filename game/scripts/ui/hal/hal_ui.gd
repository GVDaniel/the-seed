class_name HalUi
extends Object
## Colores y fábricas de controles compartidos por la interfaz de HAL.

const CYAN := Color("3de7c9")
const GOLD := Color("f4d35e")
const RED := Color("ff4a32")
const TEXT := Color(0.91, 0.945, 1.0)
const DIM := Color(0.55, 0.62, 0.72)
const LOCKED := Color(0.3, 0.36, 0.44)
const CARD_BG := Color(0.05, 0.09, 0.16, 0.92)


static func label(text: String, size: int = 16, color: Color = TEXT, wrap: bool = false) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l


static func box(border: Color = CYAN, margin: int = 10, bg: Color = CARD_BG) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = border
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(3)
	sb.set_content_margin_all(margin)
	return sb


static func panel(border: Color = CYAN, margin: int = 10) -> PanelContainer:
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", box(border, margin))
	return p


static func texture_rect(path: String, min_size: Vector2) -> TextureRect:
	var tr := TextureRect.new()
	tr.custom_minimum_size = min_size
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	if not path.is_empty() and ResourceLoader.exists(path):
		tr.texture = load(path)
	return tr


static func scroll(content: Control) -> ScrollContainer:
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(content)
	return sc


static func clear(node: Node) -> void:
	for child in node.get_children():
		node.remove_child(child)
		child.queue_free()


## Texto con contorno oscuro para dibujar sobre mapas.
static func draw_text(canvas: CanvasItem, pos: Vector2, text: String, size: int, color: Color) -> void:
	var font: Font = canvas.get_theme_default_font()
	if font == null:
		font = ThemeDB.fallback_font
	canvas.draw_string_outline(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, 4, Color(0.02, 0.035, 0.07, 0.95))
	canvas.draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)
