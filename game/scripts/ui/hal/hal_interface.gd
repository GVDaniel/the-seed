class_name HalInterface
extends CanvasLayer
## «Entrar en HAL»: pantalla completa con el ojo de HAL y siete pestañas
## (inventario, Andrés y ASTRA, mapa, misiones, cuaderno, tripulación, sistema).
## Tab/I abre y cierra; N abre el cuaderno; M, el mapa. Dentro: Q/E o 1–7 cambian de pestaña.

const EYE_TEXTURE := "res://assets/art/ui/hal_eye.png"
const GLOW_TEXTURE := "res://assets/art/ui/hal_glow.png"
const TAB_IDS := ["inventory", "status", "map", "missions", "notes", "crew", "system"]
const TAB_NAMES := ["Inventario", "Andrés", "Mapa", "Misiones", "Cuaderno", "Tripulación", "Sistema"]
const TYPE_SPEED := 45.0

## La escena anfitriona puede desactivarla (p. ej. durante una cinemática).
var enabled: bool = true

var _root: Control
var _eye: TextureRect
var _glow: TextureRect
var _status: Label
var _buttons: Dictionary = {}
var _tabs: Dictionary = {}
var _current: String = "inventory"
var _open: bool = false
var _dialogue_open: bool = false
var _analysis_open: bool = false
var _shop_open: bool = false
var _pulse: float = 0.0
var _typed: float = 0.0
var _tween: Tween


func _ready() -> void:
	layer = 22
	_build()
	_root.visible = false
	visible = false
	var bus := App.bus()
	bus.hal_interface_requested.connect(_on_requested)
	bus.dialogue_requested.connect(func(_s: String, _l: Array, _c: String) -> void: _dialogue_open = true)
	bus.dialogue_finished.connect(func(_c: String) -> void: _dialogue_open = false)
	bus.scan_completed.connect(func(_id: String, _new: bool) -> void: _analysis_open = true)
	bus.analysis_panel_closed.connect(func() -> void: _analysis_open = false)
	bus.shop_requested.connect(func(_id: String) -> void: _shop_open = true)
	bus.shop_closed.connect(func() -> void: _shop_open = false)


func is_open() -> bool:
	return _open


func can_open() -> bool:
	return enabled and not _open and not _dialogue_open and not _analysis_open and not _shop_open \
			and not App.router().is_busy()


## Contexto de la superficie para el mapa «Aquí».
func set_surface_context(map: Dictionary, player: Node2D) -> void:
	(_tabs["map"] as HalMapTab).set_surface_context(map, player)


func open(tab_id: String = "") -> void:
	if not tab_id.is_empty() and _tabs.has(tab_id):
		_current = tab_id
	_open = true
	visible = true
	_root.visible = true
	_select(_current, false)
	App.music().set_muffled(true)
	App.sfx().play("scan")
	App.bus().hal_interface_toggled.emit(true)
	if _tween != null:
		_tween.kill()
	_root.modulate.a = 0.0
	_eye.scale = Vector2(0.2, 0.2)
	_tween = create_tween().set_parallel(true)
	_tween.tween_property(_root, "modulate:a", 1.0, 0.18)
	_tween.tween_property(_eye, "scale", Vector2.ONE, 0.4).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func close() -> void:
	if not _open:
		return
	_open = false
	if _tween != null:
		_tween.kill()
	visible = false
	_root.visible = false
	App.music().set_muffled(false)
	App.sfx().play("blip", 0.8)
	App.bus().hal_interface_toggled.emit(false)


func current_tab() -> String:
	return _current


func _on_requested(tab_id: String) -> void:
	if tab_id == "close":
		close()
	elif _open:
		if not tab_id.is_empty():
			_select(tab_id)
	elif can_open():
		open(tab_id)


# ------------------------------------------------------------ entrada

func _input(event: InputEvent) -> void:
	if _open:
		_input_open(event)
	elif can_open():
		if event.is_action_pressed("hal_menu"):
			open()
		elif event.is_action_pressed("notebook_toggle"):
			open("notes")
		elif event.is_action_pressed("map_toggle"):
			open("map")
		else:
			return
		get_viewport().set_input_as_handled()


func _input_open(event: InputEvent) -> void:
	if event.is_action_pressed("hal_menu") or event.is_action_pressed("panel_close") or event.is_action_pressed("ui_cancel"):
		close()
	elif event.is_action_pressed("notebook_toggle"):
		_toggle_tab("notes")
	elif event.is_action_pressed("map_toggle"):
		_toggle_tab("map")
	elif event.is_action_pressed("hal_prev_tab"):
		_cycle(-1)
	elif event.is_action_pressed("hal_next_tab"):
		_cycle(1)
	elif event is InputEventKey and event.pressed and not event.echo \
			and (event as InputEventKey).keycode >= KEY_1 and (event as InputEventKey).keycode < KEY_1 + TAB_IDS.size():
		_select(TAB_IDS[(event as InputEventKey).keycode - KEY_1])
	elif event is InputEventKey:
		# El juego queda en pausa de controles mientras HAL está abierta.
		if event.is_action("interact") or event.is_action("scanner_scan") or event.is_action("interact_talk"):
			get_viewport().set_input_as_handled()
		return
	else:
		return
	get_viewport().set_input_as_handled()


func _toggle_tab(tab_id: String) -> void:
	if _current == tab_id:
		close()
	else:
		_select(tab_id)


func _cycle(step: int) -> void:
	var i := TAB_IDS.find(_current)
	_select(TAB_IDS[(i + step + TAB_IDS.size()) % TAB_IDS.size()])


func _select(tab_id: String, with_sound: bool = true) -> void:
	_current = tab_id
	for id in _tabs.keys():
		(_tabs[id] as Control).visible = id == tab_id
		(_buttons[id] as Button).set_pressed_no_signal(id == tab_id)
	var tab: Control = _tabs[tab_id]
	tab.call("refresh")
	_say(str(tab.call("hal_line")))
	if with_sound:
		App.sfx().play("blip")


func _say(text: String) -> void:
	_status.text = text
	_status.visible_characters = 0
	_typed = 0.0


func _process(delta: float) -> void:
	if not _open:
		return
	_pulse += delta
	var k := 0.5 + 0.5 * sin(_pulse * 2.2)
	var talking := _status.visible_characters >= 0 and _status.visible_characters < _status.text.length()
	if talking:
		_typed += delta * TYPE_SPEED
		_status.visible_characters = int(_typed)
		if _status.visible_characters >= _status.text.length():
			_status.visible_characters = -1
		k = 0.6 + 0.4 * absf(sin(_pulse * 14.0))
	_glow.modulate.a = 0.45 + 0.55 * k
	_eye.modulate = Color(1, 1, 1).lerp(Color(1.3, 1.12, 1.08), k)


# ------------------------------------------------------------ construcción

func _build() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	var backdrop := ColorRect.new()
	backdrop.color = Color(0.02, 0.035, 0.07, 1.0)
	backdrop.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(backdrop)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right"]:
		margin.add_theme_constant_override("margin_" + side, 28)
	for side in ["top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 22)
	_root.add_child(margin)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	margin.add_child(row)
	row.add_child(_build_left())
	row.add_child(_build_right())
	_root.add_child(HalScanlines.new())


func _build_left() -> Control:
	var left := VBoxContainer.new()
	left.custom_minimum_size = Vector2(300, 0)
	left.add_theme_constant_override("separation", 10)
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(300, 280)
	_glow = HalUi.texture_rect(GLOW_TEXTURE, Vector2(300, 300))
	_glow.position = Vector2(0, -10)
	_glow.size = Vector2(300, 300)
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_glow.material = additive
	holder.add_child(_glow)
	_eye = HalUi.texture_rect(EYE_TEXTURE, Vector2(256, 256))
	_eye.position = Vector2(22, 12)
	_eye.size = Vector2(256, 256)
	_eye.pivot_offset = Vector2(128, 128)
	holder.add_child(_eye)
	left.add_child(holder)
	var name_label := HalUi.label("HAL 9000", 28, HalUi.GOLD)
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	left.add_child(name_label)
	var role := HalUi.label("IA de la nave ASTRA", 15, HalUi.CYAN)
	role.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	left.add_child(role)
	var bubble := HalUi.panel(HalUi.RED, 12)
	_status = HalUi.label("", 17, HalUi.TEXT, true)
	_status.custom_minimum_size = Vector2(0, 130)
	_status.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	bubble.add_child(_status)
	left.add_child(bubble)
	return left


func _build_right() -> Control:
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.add_theme_constant_override("separation", 10)
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", 6)
	var group := ButtonGroup.new()
	for i in TAB_IDS.size():
		var id: String = TAB_IDS[i]
		var b := Button.new()
		b.text = "%d %s" % [i + 1, TAB_NAMES[i]]
		b.toggle_mode = true
		b.button_group = group
		b.focus_mode = Control.FOCUS_NONE
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(func() -> void: _select(id))
		bar.add_child(b)
		_buttons[id] = b
	right.add_child(bar)
	var content := HalUi.panel(HalUi.CYAN, 16)
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(content)
	var stack := Control.new()
	content.add_child(stack)
	for id in TAB_IDS:
		var tab := _make_tab(id)
		tab.set_anchors_preset(Control.PRESET_FULL_RECT)
		tab.visible = false
		stack.add_child(tab)
		_tabs[id] = tab
	var footer := HBoxContainer.new()
	var hint := HalUi.label("Q / E — Cambiar pestaña · Tab o Esc — Salir de HAL", 14, HalUi.DIM)
	hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(hint)
	var exit := Button.new()
	exit.text = "Salir de HAL"
	exit.focus_mode = Control.FOCUS_NONE
	exit.pressed.connect(close)
	footer.add_child(exit)
	right.add_child(footer)
	return right


func _make_tab(id: String) -> Control:
	match id:
		"inventory":
			return HalInventoryTab.new()
		"status":
			return HalStatusTab.new()
		"map":
			return HalMapTab.new()
		"missions":
			return HalMissionsTab.new()
		"notes":
			return HalNotesTab.new()
		"crew":
			return HalCrewTab.new()
		_:
			return HalSystemTab.new()
