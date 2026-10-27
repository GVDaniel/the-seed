class_name HalSystemTab
extends VBoxContainer
## Pestaña Sistema: estado del cadete, volumen y salida al menú.

const CONTROLS := "WASD — Caminar o pilotar · E — Interactuar · F — Escanear · T — Hablar (en el espacio)\nTab o I — Entrar en HAL · N — Cuaderno · M — Mapa\nDentro de HAL: Q / E o 1–6 — Cambiar pestaña · Esc — Salir"

var _rank: Label
var _xp_bar: ProgressBar
var _xp_label: Label
var _music: HSlider
var _sfx: HSlider


func _ready() -> void:
	add_theme_constant_override("separation", 10)
	add_child(HalUi.label("ESTADO DEL CADETE", 14, HalUi.CYAN))
	_rank = HalUi.label("", 22, HalUi.GOLD)
	add_child(_rank)
	_xp_bar = ProgressBar.new()
	_xp_bar.show_percentage = false
	_xp_bar.custom_minimum_size = Vector2(0, 16)
	add_child(_xp_bar)
	_xp_label = HalUi.label("", 15, HalUi.DIM)
	add_child(_xp_label)

	add_child(HalUi.label("AUDIO", 14, HalUi.CYAN))
	_music = _slider_row("Música", AudioSettings.MUSIC_BUS)
	_sfx = _slider_row("Efectos", AudioSettings.SFX_BUS)

	add_child(HalUi.label("CONTROLES", 14, HalUi.CYAN))
	add_child(HalUi.label(CONTROLS, 15, HalUi.TEXT, true))

	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_child(spacer)
	var bottom := HBoxContainer.new()
	bottom.add_child(HalUi.label("Tu progreso se guarda solo.", 15, HalUi.DIM, true))
	var menu_btn := Button.new()
	menu_btn.text = "Volver al menú principal"
	menu_btn.pressed.connect(func() -> void:
		App.bus().hal_interface_requested.emit("close")
		App.router().go_menu()
	)
	bottom.add_child(menu_btn)
	add_child(bottom)


func _slider_row(text: String, bus_name: String) -> HSlider:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	var l := HalUi.label(text, 17)
	l.custom_minimum_size = Vector2(110, 0)
	row.add_child(l)
	var slider := HSlider.new()
	slider.min_value = 0.0
	slider.max_value = 1.0
	slider.step = 0.05
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.custom_minimum_size = Vector2(0, 28)
	slider.value_changed.connect(func(v: float) -> void:
		AudioSettings.set_volume(bus_name, v)
		if bus_name == AudioSettings.SFX_BUS:
			App.sfx().play("blip")
	)
	row.add_child(slider)
	add_child(row)
	return slider


func refresh() -> void:
	var gs := App.game_state()
	var xp := int(gs.experience)
	_rank.text = "%s · XP %d" % [gs.rank_name(), xp]
	var prev := 0
	var next := -1
	var next_name := ""
	for row in gs.RANKS:
		if xp >= int(row[0]):
			prev = int(row[0])
		elif next < 0:
			next = int(row[0])
			next_name = str(row[1])
	if next < 0:
		_xp_bar.max_value = 1
		_xp_bar.value = 1
		_xp_label.text = "Rango máximo de esta demo."
	else:
		_xp_bar.max_value = next - prev
		_xp_bar.value = xp - prev
		_xp_label.text = "Faltan %d XP para «%s»." % [next - xp, next_name]
	_music.set_value_no_signal(AudioSettings.get_volume(AudioSettings.MUSIC_BUS))
	_sfx.set_value_no_signal(AudioSettings.get_volume(AudioSettings.SFX_BUS))


func hal_line() -> String:
	return "Todos mis circuitos funcionan perfectamente. Estoy al cien por cien de mi capacidad."
