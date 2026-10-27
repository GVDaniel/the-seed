class_name HalStatusTab
extends HBoxContainer
## Pestaña Andrés: nivel, salud, puntos de mejora y técnicas; y el estado de ASTRA
## (motor, combustible, casco).

const PORTRAIT := "res://assets/art/portraits/andres.png"

var _hero_col: VBoxContainer
var _ship_col: VBoxContainer


func _ready() -> void:
	add_theme_constant_override("separation", 22)
	_hero_col = VBoxContainer.new()
	_hero_col.add_theme_constant_override("separation", 6)
	_hero_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	add_child(HalUi.scroll(_hero_col))
	_ship_col = VBoxContainer.new()
	_ship_col.add_theme_constant_override("separation", 6)
	_ship_col.custom_minimum_size = Vector2(330, 0)
	add_child(_ship_col)


func refresh() -> void:
	_fill_hero()
	_fill_ship()


func _fill_hero() -> void:
	HalUi.clear(_hero_col)
	var hero := App.hero()
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 12)
	head.add_child(HalUi.texture_rect(PORTRAIT, Vector2(72, 72)))
	var who := VBoxContainer.new()
	who.add_child(HalUi.label("ANDRÉS · NIVEL %d" % int(hero.level()), 22, HalUi.GOLD))
	var xp: Vector2i = hero.xp_progress()
	who.add_child(HalUi.label("Experiencia: %d / %d para el nivel %d" % [xp.x, xp.y, int(hero.level()) + 1], 14, HalUi.DIM))
	who.add_child(_bar(float(xp.x) / float(xp.y), HalUi.GOLD))
	head.add_child(who)
	_hero_col.add_child(head)
	_hero_col.add_child(HalUi.label("Salud %d / %d" % [int(hero.hp), int(hero.max_hp())], 16))
	_hero_col.add_child(_bar(float(hero.hp_ratio()), Color("7dff9a")))
	_hero_col.add_child(HalUi.label("Ataque %d · Defensa %d · Energía de técnicas %d" % [
		int(hero.attack()), int(hero.defense()), int(hero.max_en())], 15, HalUi.CYAN))

	var unspent := int(hero.unspent)
	_hero_col.add_child(HalUi.label("PUNTOS DE MEJORA: %d" % unspent, 15, HalUi.GOLD if unspent > 0 else HalUi.DIM))
	for stat in HeroProgression.stat_ids():
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		var name_label := HalUi.label("%s  %d" % [HeroProgression.stat_name(stat), int(hero.point(stat))], 17, HalUi.TEXT)
		name_label.custom_minimum_size = Vector2(170, 0)
		row.add_child(name_label)
		var plus := Button.new()
		plus.text = "+"
		plus.custom_minimum_size = Vector2(40, 32)
		plus.disabled = unspent <= 0
		var s := stat
		plus.pressed.connect(func() -> void:
			if App.hero().spend_point(s):
				App.sfx().play("confirm")
			refresh())
		row.add_child(plus)
		row.add_child(HalUi.label(HeroProgression.stat_help(stat), 13, HalUi.DIM, true))
		_hero_col.add_child(row)

	_hero_col.add_child(HalUi.label("TÉCNICAS DE COMBATE", 15, HalUi.CYAN))
	for skill in hero.skills().all():
		if skill.kind == "combo":
			_hero_col.add_child(HalUi.label("%s (en equipo): %s" % [skill.display_name, skill.description], 14, HalUi.GOLD, true))
			continue
		var owner := "Andrés" if skill.user == "andres" else "HAL"
		var known := HeroProgression.meets(skill.requires, hero.points)
		var text := "%s · %s" % [owner, skill.display_name]
		if not known:
			var reqs := PackedStringArray()
			for key in skill.requires.keys():
				reqs.append("%s %d" % [HeroProgression.stat_name(key), int(skill.requires[key])])
			text += "  (necesita %s)" % ", ".join(reqs)
		_hero_col.add_child(HalUi.label(text, 14, HalUi.TEXT if known else HalUi.LOCKED, true))


func _fill_ship() -> void:
	HalUi.clear(_ship_col)
	var ship := App.ship()
	var engine: EngineDef = ship.engine()
	_ship_col.add_child(HalUi.label("ASTRA", 22, HalUi.GOLD))
	_ship_col.add_child(HalUi.label(engine.display_name, 17, HalUi.CYAN, true))
	_ship_col.add_child(HalUi.label(engine.description, 14, HalUi.DIM, true))
	_ship_col.add_child(HalUi.label("Combustible (%s): %d / %d" % [engine.fuel_name, int(ceil(ship.fuel)),
		int(round(ship.capacity()))], 15))
	_ship_col.add_child(_bar(float(ship.fuel_ratio()), HalUi.GOLD))
	_ship_col.add_child(HalUi.label("Casco: %d %%" % int(round(ship.hull)), 15))
	_ship_col.add_child(_bar(float(ship.hull_ratio()), Color("7dff9a")))
	_ship_col.add_child(HalUi.label("Velocidad punta ×%.2f · consumo %.2f/s" % [
		engine.speed_factor * float(ship.hull_speed_factor()), float(ship.burn_rate())], 14, HalUi.TEXT, true))
	if not engine.fact.is_empty():
		var box := HalUi.panel(HalUi.GOLD, 10)
		var col := VBoxContainer.new()
		col.add_child(HalUi.label("DATO REAL", 12, HalUi.GOLD))
		col.add_child(HalUi.label(engine.fact, 14, HalUi.TEXT, true))
		box.add_child(col)
		_ship_col.add_child(box)


func _bar(ratio: float, color: Color) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.show_percentage = false
	bar.max_value = 1.0
	bar.step = 0.001
	bar.value = clampf(ratio, 0.0, 1.0)
	bar.custom_minimum_size = Vector2(220, 12)
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	bar.add_theme_stylebox_override("fill", fill)
	return bar


func hal_line() -> String:
	var hero := App.hero()
	if int(hero.unspent) > 0:
		return "Tienes %d punto(s) de mejora. Aptitudes te hace más resistente, conocimientos me da energía y ahorra combustible, destrezas mejora tus golpes." % int(hero.unspent)
	var ship := App.ship()
	if float(ship.fuel_ratio()) < 0.25:
		return "Combustible bajo. Busca un surtidor dorado en la superficie."
	if float(ship.hull_ratio()) < 0.5:
		return "El casco está abollado y vamos más lentos. Un kit de reparación o una estación lo arreglan."
	return "Andrés en nivel %d. ASTRA lista para volar." % int(hero.level())
