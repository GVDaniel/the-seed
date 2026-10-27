class_name BattleMenu
extends PanelContainer
## Menú de acciones del turno: quién actúa, cuántas chispas solares gasta (← →), ataque, técnicas,
## combo, objetos, análisis de HAL o retirada. Teclado (flechas + Enter) o táctil.
## Emite chosen(actor_uid, action):
## {type: "skill", skill_id, target, boost} | {type: "item", item_id} | {type: "analyze", target} | {type: "retreat"}.
## Emite aimed(uid) al señalar un blanco ("" = ninguno) para que la escena lo marque en el campo.

signal chosen(actor_uid: String, action: Dictionary)
signal aimed(uid: String)

var _engine: BattleEngine
var _actor: String = ""
var _boost: int = 0
var _tabs: HBoxContainer
var _boost_row: HBoxContainer
var _boost_label: Label
var _boost_pips: ResourcePips
var _list: VBoxContainer
var _info: Label
var _fact: Label


func _ready() -> void:
	add_theme_stylebox_override("panel", HalUi.box(HalUi.CYAN, 10, Color(0.03, 0.06, 0.11, 0.93)))
	custom_minimum_size = Vector2(360, 0)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 6)
	_tabs = HBoxContainer.new()
	_tabs.add_theme_constant_override("separation", 6)
	_boost_row = HBoxContainer.new()
	_boost_row.add_theme_constant_override("separation", 8)
	_boost_label = HalUi.label("", 14, HalUi.CYAN)
	_boost_pips = ResourcePips.new()
	_boost_pips.setup(BattleRules.MAX_BOOST, HalUi.GOLD, true, 12)
	_boost_pips.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_boost_row.add_child(_boost_label)
	_boost_row.add_child(_step_button("−", -1))
	_boost_row.add_child(_boost_pips)
	_boost_row.add_child(_step_button("+", 1))
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 4)
	_info = HalUi.label("", 13, HalUi.TEXT, true)
	_info.custom_minimum_size = Vector2(336, 0)
	_fact = HalUi.label("", 12, HalUi.GOLD, true)
	_fact.custom_minimum_size = Vector2(336, 0)
	for c in [_tabs, _boost_row, _list, _info, _fact]:
		col.add_child(c)
	add_child(col)
	visible = false


func open(engine: BattleEngine, actor_uid: String = "") -> void:
	_engine = engine
	var available := engine.ready_actors()
	if available.is_empty():
		close()
		return
	if actor_uid != _actor:
		_boost = 0
	_actor = actor_uid
	if _engine.combatant(_actor) == null or not _engine.combatant(_actor) in available:
		_actor = available[0].uid
	_boost = mini(_boost, _engine.max_boost())
	_build_tabs(available)
	_refresh_boost()
	_root_page()
	visible = true


func close() -> void:
	visible = false
	aimed.emit("")


func current_actor() -> String:
	return _actor


func _input(event: InputEvent) -> void:
	if not visible or _engine == null:
		return
	if event.is_action_pressed("ui_right") or event.is_action_pressed("ui_left"):
		_step_boost(1 if event.is_action_pressed("ui_right") else -1)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_focus_next"):
		var available := _engine.ready_actors()
		if available.size() > 1:
			var idx := 0
			for i in available.size():
				if available[i].uid == _actor:
					idx = i
			App.sfx().play("blip")
			open(_engine, available[(idx + 1) % available.size()].uid)
			get_viewport().set_input_as_handled()


func _step_boost(step: int) -> void:
	var next := clampi(_boost + step, 0, _engine.max_boost())
	if next != _boost:
		_boost = next
		App.sfx().play("blip")
		_refresh_boost()


func _step_button(text: String, step: int) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(30, 26)
	b.pressed.connect(_step_boost.bind(step))
	return b


func _refresh_boost() -> void:
	var can := _engine.max_boost()
	_boost_row.visible = can > 0
	_boost_label.text = "Potenciar (← →): %d" % _boost
	_boost_pips.setup(can if can > 0 else 1, HalUi.GOLD, true, 12)
	_boost_pips.set_value(_boost, maxi(1, can))


func _build_tabs(available: Array[Combatant]) -> void:
	HalUi.clear(_tabs)
	for member in _engine.party:
		var b := Button.new()
		b.toggle_mode = true
		b.button_pressed = member.uid == _actor
		b.text = member.display_name
		b.disabled = not member in available
		b.focus_mode = Control.FOCUS_NONE
		var portrait := "res://assets/art/portraits/%s.png" % member.uid
		if ResourceLoader.exists(portrait):
			b.icon = load(portrait)
			b.expand_icon = true
			b.add_theme_constant_override("icon_max_width", 24)
		var uid := member.uid
		b.pressed.connect(func() -> void:
			App.sfx().play("blip")
			open(_engine, uid))
		_tabs.add_child(b)
	if available.size() > 1:
		_tabs.add_child(HalUi.label("Tab: cambiar", 12, HalUi.DIM))


func _root_page() -> void:
	HalUi.clear(_list)
	aimed.emit("")
	var actor := _engine.combatant(_actor)
	var basic := _first_of_kind(actor, "basic")
	if basic != null:
		_add_button("Atacar · %s" % basic.display_name, basic, func() -> void: _pick_target(basic))
	var techniques := _skills_of(actor, ["attack", "heal", "guard"])
	if not techniques.is_empty():
		_add_button("Técnicas  ▸", null, _skills_page.bind(techniques),
			"Gastan energía (EN). El ataque básico recupera 1 EN y suelta chispas solares.")
	var combos := _engine.catalog.combos()
	if not combos.is_empty():
		_add_button("Combo en equipo  ▸  (%d/%d)" % [_engine.combo_points, combos[0].combo_cost], null,
			_skills_page.bind(combos), "Los golpes básicos llenan el combo; un golpe perfecto suma el doble.")
	var heals: Array[ItemDef] = App.inventory().consumables("heal")
	if not heals.is_empty():
		_add_button("Objetos  ▸", null, _items_page.bind(heals), "Comida y medicinas: curan, pero gastan el turno.")
	var to_scan := _unscanned()
	if not to_scan.is_empty():
		_add_button("Analizar (HAL)  ▸", null, _analyze_page.bind(to_scan),
			"HAL escanea a un enemigo y descubre sus debilidades. No gasta el turno.")
	_add_button("Retirarse", null, func() -> void: chosen.emit(_actor, {"type": "retreat"}),
		"HAL os saca de aquí. Podrás volver cuando estés listo.")
	_focus_first()


func _unscanned() -> Array[Combatant]:
	var out: Array[Combatant] = []
	for e in _engine.alive_enemies():
		if _engine.can_analyze(e.uid):
			out.append(e)
	return out


func _skills_page(skills: Array[CombatSkill]) -> void:
	HalUi.clear(_list)
	var actor := _engine.combatant(_actor)
	for skill in skills:
		var cost := "%d combo" % skill.combo_cost if skill.kind == "combo" else "%d EN" % skill.cost
		var reason := _engine.block_reason(actor, skill)
		var s := skill
		var b := _add_button("%s · %s" % [skill.display_name, cost], skill, func() -> void: _pick_target(s))
		if not reason.is_empty():
			b.disabled = true
			b.focus_mode = Control.FOCUS_ALL
			b.tooltip_text = reason
			var why := reason
			b.focus_entered.connect(func() -> void: _info.text = "%s  ·  %s" % [s.description, why])
	_add_button("◂ Volver", null, _root_page)
	_focus_first()


func _items_page(items: Array[ItemDef]) -> void:
	HalUi.clear(_list)
	for def in items:
		var id := def.id
		var b := _add_button("%s · +%d salud" % [def.display_name, def.heal_amount()], null,
			func() -> void: chosen.emit(_actor, {"type": "item", "item_id": id}), def.description)
		if ResourceLoader.exists(def.icon_path):
			b.icon = load(def.icon_path)
			b.expand_icon = true
			b.add_theme_constant_override("icon_max_width", 24)
	_add_button("◂ Volver", null, _root_page)
	_focus_first()


func _analyze_page(enemies: Array[Combatant]) -> void:
	HalUi.clear(_list)
	_list.add_child(HalUi.label("¿Qué analiza HAL?", 14, HalUi.GOLD))
	for enemy in enemies:
		var uid := enemy.uid
		var b := _add_button(enemy.display_name, null,
			func() -> void: chosen.emit(_actor, {"type": "analyze", "target": uid}))
		_aim_on_focus(b, uid)
	_add_button("◂ Volver", null, _root_page)
	_focus_first()


func _pick_target(skill: CombatSkill) -> void:
	if skill.target == "enemy":
		var alive := _engine.alive_enemies()
		if alive.size() > 1:
			HalUi.clear(_list)
			_list.add_child(HalUi.label("¿A quién?", 14, HalUi.GOLD))
			for enemy in alive:
				var uid := enemy.uid
				var label := enemy.display_name
				if enemy.is_charging():
					label += "  (cerraduras: %d)" % enemy.locks().size()
				var b := _add_button(label, skill, func() -> void: _emit_skill(skill, uid))
				_aim_on_focus(b, uid)
			_add_button("◂ Volver", null, _root_page)
			_focus_first()
			return
		_emit_skill(skill, alive[0].uid if not alive.is_empty() else "")
	elif skill.target == "ally":
		HalUi.clear(_list)
		_list.add_child(HalUi.label("¿A quién reparas?", 14, HalUi.GOLD))
		for member in _engine.party:
			var uid := member.uid
			var state := "K.O." if not member.is_alive() else "%d/%d" % [member.hp, member.max_hp]
			var b := _add_button("%s  (%s)" % [member.display_name, state], skill,
				func() -> void: _emit_skill(skill, uid))
			_aim_on_focus(b, uid)
		_add_button("◂ Volver", null, _root_page)
		_focus_first()
	else:
		_emit_skill(skill, "")


func _aim_on_focus(b: Button, uid: String) -> void:
	b.focus_entered.connect(func() -> void: aimed.emit(uid))
	b.mouse_entered.connect(func() -> void: aimed.emit(uid))


func _emit_skill(skill: CombatSkill, target_uid: String) -> void:
	chosen.emit(_actor, {"type": "skill", "skill_id": skill.id, "target": target_uid, "boost": _boost})
	_boost = 0


func _add_button(text: String, skill: CombatSkill, action: Callable, info: String = "") -> Button:
	var b := Button.new()
	b.text = text
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.custom_minimum_size = Vector2(0, 32)
	b.add_theme_font_size_override("font_size", 16)
	b.focus_neighbor_left = NodePath(".")
	b.focus_neighbor_right = NodePath(".")
	if skill != null and not skill.elements.is_empty():
		var icon_path := BattleHud.ELEMENT_ICON % skill.elements[0]
		if ResourceLoader.exists(icon_path):
			b.icon = load(icon_path)
			b.expand_icon = true
			b.add_theme_constant_override("icon_max_width", 20)
	var text_info := info
	var fact := ""
	if skill != null:
		text_info = skill.description
		if not skill.elements.is_empty():
			var names := PackedStringArray()
			for el in skill.elements:
				names.append(BattleRules.element_name(el))
			text_info += "  [%s]" % ", ".join(names)
		if not skill.fact.is_empty():
			fact = "Dato: " + skill.fact
	var show_info := func() -> void:
		_info.text = text_info
		_fact.text = fact
	b.focus_entered.connect(show_info)
	b.mouse_entered.connect(show_info)
	b.pressed.connect(func() -> void:
		App.sfx().play("confirm")
		action.call())
	_list.add_child(b)
	return b


## Siempre pegado por abajo, encima de las fichas del grupo, crezca o encoja la lista.
func _stick_to_bottom() -> void:
	size = Vector2.ZERO
	await get_tree().process_frame
	position.y = 606.0 - size.y


func _focus_first() -> void:
	_stick_to_bottom()
	for child in _list.get_children():
		if child is Button and not (child as Button).disabled:
			(child as Button).grab_focus.call_deferred()
			return


func _first_of_kind(actor: Combatant, kind: String) -> CombatSkill:
	for id in actor.skills:
		var s := _engine.catalog.get_def(id)
		if s != null and s.kind == kind:
			return s
	return null


func _skills_of(actor: Combatant, kinds: Array) -> Array[CombatSkill]:
	var out: Array[CombatSkill] = []
	for id in actor.skills:
		var s := _engine.catalog.get_def(id)
		if s != null and s.kind in kinds:
			out.append(s)
	return out
