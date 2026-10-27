class_name BattleHud
extends Control
## Información del combate (no decide nada): mensajes, fichas del grupo (retrato, salud, energía,
## «objetivo»), combo y chispas solares, y sobre cada enemigo su salud, debilidades conocidas y lo
## que hará al final de la ronda (con cerraduras y cuenta atrás). Números flotantes.

const ELEMENT_ICON := "res://assets/art/ui/element_%s.png"
const PORTRAIT := "res://assets/art/portraits/%s.png"
const RED := Color("ff5a6a")
const GREEN := Color("7dff9a")
const SHADOW := Color(0.02, 0.035, 0.07)

var stage: BattleStage
var _engine: BattleEngine
var _banner: PanelContainer
var _message: Label
var _hint: Label
var _cards: Dictionary = {}
var _plates: Dictionary = {}
var _combo_bar: ResourcePips
var _orb_bar: ResourcePips
var _combo_label: Label
var _orb_label: Label
var _views: Dictionary = {}
var _active_uid: String = ""
var _fast: bool = false


func build(engine: BattleEngine, field: BattleStage, views: Dictionary, fast: bool) -> void:
	_engine = engine
	stage = field
	_views = views
	_fast = fast
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

	var top := VBoxContainer.new()
	top.position = Vector2(290, 10)
	top.custom_minimum_size = Vector2(700, 0)
	top.add_theme_constant_override("separation", 6)
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner = PanelContainer.new()
	_banner.add_theme_stylebox_override("panel", HalUi.box(HalUi.CYAN, 8, Color(0.03, 0.06, 0.11, 0.86)))
	_message = HalUi.label("", 19, HalUi.TEXT, true)
	_message.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner.add_child(_message)
	_hint = HalUi.label("", 15, HalUi.GOLD, true)
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_outline(_hint, 5)
	top.add_child(_banner)
	top.add_child(_hint)
	add_child(top)

	var party_row := HBoxContainer.new()
	party_row.add_theme_constant_override("separation", 10)
	party_row.position = Vector2(14, 618)
	for member in engine.party:
		var card := _party_card(member)
		party_row.add_child(card["root"])
		_cards[member.uid] = card
	add_child(party_row)

	var res := HalUi.panel(HalUi.GOLD, 8)
	res.position = Vector2(1000, 630)
	res.custom_minimum_size = Vector2(266, 0)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 4)
	var combo_row := HBoxContainer.new()
	_combo_label = HalUi.label("COMBO", 14, HalUi.GOLD)
	_combo_label.custom_minimum_size = Vector2(84, 0)
	_combo_bar = ResourcePips.new()
	_combo_bar.setup(BattleEngine.COMBO_MAX, HalUi.GOLD, false)
	combo_row.add_child(_combo_label)
	combo_row.add_child(_combo_bar)
	var orb_row := HBoxContainer.new()
	_orb_label = HalUi.label("CHISPAS", 14, HalUi.CYAN)
	_orb_label.custom_minimum_size = Vector2(84, 0)
	_orb_bar = ResourcePips.new()
	_orb_bar.setup(BattleEngine.ORBS_MAX, HalUi.CYAN, true)
	orb_row.add_child(_orb_label)
	orb_row.add_child(_orb_bar)
	col.add_child(combo_row)
	col.add_child(orb_row)
	res.add_child(col)
	add_child(res)

	for enemy in engine.enemies:
		_plates[enemy.uid] = _enemy_plate(enemy)
	refresh()


func _process(_delta: float) -> void:
	if stage == null:
		return
	for uid in _plates.keys():
		var view: BattlerView = _views.get(uid)
		var plate: Dictionary = _plates[uid]
		var root := plate["root"] as Control
		if view == null:
			continue
		var top := stage.to_screen(view.top_point())
		root.position = (top + Vector2(-root.size.x * 0.5, -root.size.y - 4)).clamp(
			Vector2(8, 96), Vector2(1272 - root.size.x, 600))


func set_active(uid: String) -> void:
	_active_uid = uid
	refresh()


func refresh() -> void:
	var targeted := _targeted()
	for member in _engine.party:
		var card: Dictionary = _cards.get(member.uid, {})
		if card.is_empty():
			continue
		var hp_bar := card["hp_bar"] as ProgressBar
		hp_bar.max_value = member.max_hp
		if _fast:
			hp_bar.value = member.hp
		else:
			create_tween().tween_property(hp_bar, "value", float(member.hp), 0.3)
		(card["hp"] as Label).text = "%d/%d" % [member.hp, member.max_hp]
		(card["en"] as ResourcePips).set_value(member.en, member.max_en)
		var status := card["status"] as Label
		if not member.is_alive():
			status.text = "K.O. · se levanta en %d" % maxi(1, member.ko_rounds)
			status.add_theme_color_override("font_color", RED)
		elif member.uid in targeted:
			status.text = "¡Objetivo!"
			status.add_theme_color_override("font_color", RED)
		elif member.guard_mult < 1.0:
			status.text = "Escudo −%d %%" % int(round((1.0 - member.guard_mult) * 100.0))
			status.add_theme_color_override("font_color", HalUi.CYAN)
		elif member.acted:
			status.text = "Ya actuó"
			status.add_theme_color_override("font_color", HalUi.DIM)
		else:
			status.text = "Listo"
			status.add_theme_color_override("font_color", GREEN)
		var active := member.uid == _active_uid
		var border := HalUi.GOLD if active else (HalUi.DIM if member.acted or not member.is_alive() else HalUi.CYAN)
		(card["root"] as PanelContainer).add_theme_stylebox_override("panel", HalUi.box(border, 8))
		(card["root"] as Control).modulate = Color(0.7, 0.7, 0.75) if not member.is_alive() else Color.WHITE
	_combo_bar.set_value(_engine.combo_points, BattleEngine.COMBO_MAX)
	_orb_bar.set_value(_engine.orbs, BattleEngine.ORBS_MAX)
	for enemy in _engine.enemies:
		_refresh_plate(enemy)


func _targeted() -> PackedStringArray:
	var out := PackedStringArray()
	for e in _engine.alive_enemies():
		if BattleEngine.needs_block(e.intent):
			for t in e.intent.get("targets", []):
				out.append(str(t))
	return out


func say(text: String) -> void:
	_message.text = text


func hint(text: String) -> void:
	_hint.text = text


func float_text(field_pos: Vector2, text: String, color: Color, size: int = 30) -> void:
	if _fast:
		return
	var l := HalUi.label(text, size, color)
	_outline(l, 8)
	add_child(l)
	var at := stage.to_screen(field_pos)
	l.position = at + Vector2(-l.get_minimum_size().x * 0.5 + randf_range(-10, 10), -20)
	l.pivot_offset = l.get_minimum_size() * 0.5
	l.scale = Vector2(0.4, 0.4)
	var t := create_tween()
	t.tween_property(l, "scale", Vector2(1.25, 1.25), 0.08)
	t.tween_property(l, "scale", Vector2.ONE, 0.1)
	t.parallel().tween_property(l, "position:y", l.position.y - 30, 0.18).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	t.tween_property(l, "position:y", l.position.y - 44, 0.55)
	t.parallel().tween_property(l, "modulate:a", 0.0, 0.45).set_delay(0.2)
	t.tween_callback(l.queue_free)


## Rebote del icono de una cerradura rota y del número de cerraduras.
func pulse_plate(uid: String) -> void:
	var plate: Dictionary = _plates.get(uid, {})
	if plate.is_empty() or _fast:
		return
	var root := plate["root"] as Control
	root.pivot_offset = root.size * 0.5
	var t := create_tween()
	t.tween_property(root, "scale", Vector2(1.12, 1.12), 0.06)
	t.tween_property(root, "scale", Vector2.ONE, 0.14)


# ------------------------------------------------------------ construcción

func _party_card(member: Combatant) -> Dictionary:
	var root := PanelContainer.new()
	root.add_theme_stylebox_override("panel", HalUi.box(HalUi.CYAN, 8))
	root.custom_minimum_size = Vector2(300, 0)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	var face := HalUi.texture_rect(PORTRAIT % member.uid, Vector2(64, 64))
	face.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 3)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var top := HBoxContainer.new()
	var title := HalUi.label(member.display_name, 18, HalUi.GOLD)
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var status := HalUi.label("", 13, GREEN)
	top.add_child(title)
	top.add_child(status)
	var hp_row := HBoxContainer.new()
	hp_row.add_theme_constant_override("separation", 8)
	var bar := _bar(GREEN)
	bar.custom_minimum_size = Vector2(130, 12)
	bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var hp := HalUi.label("", 14)
	hp_row.add_child(bar)
	hp_row.add_child(hp)
	var en_row := HBoxContainer.new()
	en_row.add_theme_constant_override("separation", 8)
	en_row.add_child(HalUi.label("EN", 13, HalUi.CYAN))
	var en := ResourcePips.new()
	en.setup(member.max_en, HalUi.CYAN, false, 9)
	en_row.add_child(en)
	for c in [top, hp_row, en_row]:
		col.add_child(c)
	row.add_child(face)
	row.add_child(col)
	root.add_child(row)
	return {"root": root, "hp_bar": bar, "hp": hp, "en": en, "status": status}


func _enemy_plate(enemy: Combatant) -> Dictionary:
	var root := PanelContainer.new()
	root.add_theme_stylebox_override("panel", HalUi.box(Color(RED, 0.8), 6, Color(0.04, 0.05, 0.09, 0.82)))
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 3)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 6)
	var title := HalUi.label(enemy.display_name, 14, RED)
	var weak := HBoxContainer.new()
	weak.add_theme_constant_override("separation", 2)
	head.add_child(title)
	head.add_child(weak)
	var bar := _bar(RED)
	bar.custom_minimum_size = Vector2(180, 10)
	var intent := HBoxContainer.new()
	intent.add_theme_constant_override("separation", 4)
	for c in [head, bar, intent]:
		col.add_child(c)
	root.add_child(col)
	add_child(root)
	return {"root": root, "bar": bar, "name": title, "weak": weak, "intent": intent}


func _refresh_plate(enemy: Combatant) -> void:
	var plate: Dictionary = _plates.get(enemy.uid, {})
	if plate.is_empty():
		return
	var root := plate["root"] as Control
	root.visible = enemy.is_alive()
	var bar := plate["bar"] as ProgressBar
	bar.max_value = enemy.max_hp
	if _fast:
		bar.value = enemy.hp
	else:
		create_tween().tween_property(bar, "value", float(enemy.hp), 0.3)
	var tags := PackedStringArray()
	if enemy.shield_rounds > 0:
		tags.append("blindado")
	(plate["name"] as Label).text = enemy.display_name + ("  · " + ", ".join(tags) if not tags.is_empty() else "")
	var weak := plate["weak"] as HBoxContainer
	HalUi.clear(weak)
	for el in enemy.weak:
		if enemy.knows_weakness(el):
			weak.add_child(_element_icon(el, 18, "Débil a %s" % BattleRules.element_name(el)))
		else:
			var q := HalUi.label("?", 14, HalUi.DIM)
			q.tooltip_text = "Debilidad desconocida: HAL puede analizarlo."
			weak.add_child(q)
	_fill_intent(plate["intent"] as HBoxContainer, enemy)


func _fill_intent(row: HBoxContainer, enemy: Combatant) -> void:
	HalUi.clear(row)
	var intent := enemy.intent
	var move: Dictionary = intent.get("move", {})
	match str(intent.get("kind", "")):
		"stunned":
			row.add_child(HalUi.label("Aturdido: pierde el turno", 13, HalUi.GOLD))
		"attack":
			var text := str(move.get("name", "Ataque"))
			if str(move.get("target", "one")) == "self":
				text += " (se protege)"
			else:
				text += " → " + _target_text(intent)
			row.add_child(HalUi.label(text, 13, HalUi.TEXT))
		"charging", "release":
			var turns := int(intent.get("turns", 1))
			var when := "¡al final de la ronda!" if str(intent["kind"]) == "release" else "en %d rondas" % turns
			row.add_child(HalUi.label("%s %s" % [str(move.get("name", "")), when], 13, HalUi.GOLD))
	if enemy.is_charging():
		var locks := HBoxContainer.new()
		locks.add_theme_constant_override("separation", 2)
		for el in enemy.locks():
			locks.add_child(_element_icon(el, 24, "Rompe con %s" % BattleRules.element_name(el)))
		row.add_child(locks)


func _target_text(intent: Dictionary) -> String:
	var targets: Array = Array(intent.get("targets", []))
	if targets.size() > 1:
		return "todos"
	if targets.is_empty():
		return "?"
	var c := _engine.combatant(str(targets[0]))
	return c.display_name if c != null else "?"


func _element_icon(el: String, px: int, tip: String) -> TextureRect:
	var icon := HalUi.texture_rect(ELEMENT_ICON % el, Vector2(px, px))
	icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	icon.tooltip_text = tip
	return icon


func _bar(color: Color) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.show_percentage = false
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	fill.set_corner_radius_all(2)
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.05, 0.08, 0.14, 0.95)
	bg.border_color = Color(color, 0.55)
	bg.set_border_width_all(1)
	bg.set_corner_radius_all(2)
	bar.add_theme_stylebox_override("fill", fill)
	bar.add_theme_stylebox_override("background", bg)
	return bar


func _outline(l: Label, size: int) -> void:
	l.add_theme_color_override("font_outline_color", SHADOW)
	l.add_theme_constant_override("outline_size", size)
