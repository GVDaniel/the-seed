class_name HalMapTab
extends VBoxContainer
## Pestaña Mapa: superficie actual («Aquí») o ruta de ASTRA por el espacio.

const DISTANCES := "El mapa no está a escala. Distancias reales: Tierra–Luna ≈ 384 400 km · Tierra–Marte: entre 55 y 400 millones de km, según la época · TRAPPIST-1: ≈ 40 años luz."

var _here_btn: Button
var _route_btn: Button
var _minimap: HalMinimap
var _route: HalSystemMap
var _note: Label
var _view: String = "here"


func _ready() -> void:
	add_theme_constant_override("separation", 10)
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 8)
	var group := ButtonGroup.new()
	_here_btn = _view_button("Aquí", group, "here")
	_route_btn = _view_button("Ruta de ASTRA", group, "route")
	bar.add_child(_here_btn)
	bar.add_child(_route_btn)
	add_child(bar)
	_minimap = HalMinimap.new()
	_route = HalSystemMap.new()
	for view in [_minimap, _route]:
		view.size_flags_vertical = Control.SIZE_EXPAND_FILL
		view.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		add_child(view)
	_note = HalUi.label("", 14, HalUi.DIM, true)
	add_child(_note)


func _view_button(text: String, group: ButtonGroup, view: String) -> Button:
	var b := Button.new()
	b.text = text
	b.toggle_mode = true
	b.button_group = group
	b.pressed.connect(func() -> void:
		App.sfx().play("blip")
		_show(view)
	)
	return b


func set_surface_context(map: Dictionary, player: Node2D) -> void:
	_minimap.setup(map, player)


func refresh() -> void:
	var on_surface := _minimap.has_map() and str(App.game_state().location) != "space"
	_here_btn.disabled = not on_surface
	_show(_view if on_surface else "route")


func _show(view: String) -> void:
	_view = view
	_minimap.visible = view == "here"
	_route.visible = view == "route"
	_here_btn.set_pressed_no_signal(view == "here")
	_route_btn.set_pressed_no_signal(view == "route")
	_note.text = "Los rombos cian son cosas por escanear; los grises ya están en tu cuaderno." if view == "here" else DISTANCES


func hal_line() -> String:
	var summary: Dictionary = App.story().objective_summary()
	var hint := str(summary.get("hint", ""))
	if hint.is_empty():
		return "Ruta calculada. El anillo dorado marca adónde ir."
	return "Siguiente paso: %s" % hint
