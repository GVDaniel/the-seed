class_name BattleScene
extends Node2D
## Combate por turnos (estilo Sea of Stars): orquesta BattleEngine, el campo (BattleStage), el menú,
## las pulsaciones a tiempo y el HUD. Coreografía: quien ataca corre hasta el blanco, prepara el
## golpe, el jugador pulsa y el golpe cae con efecto, sacudida y número. Los enemigos anuncian su
## acción al empezar la ronda. Los robots no se destruyen: se desactivan. Perder no castiga.

const PARTY_SPOTS := {"andres": Vector2(132, 202), "hal": Vector2(86, 188)}
const ENEMY_SPOTS := {
	1: [Vector2(318, 204)],
	2: [Vector2(298, 208), Vector2(360, 186)],
	3: [Vector2(298, 210), Vector2(362, 190), Vector2(250, 184)],
}
const HOVER := {"hal": 22.0, "drone": 26.0}
const FX_COLOR := {"hit": Color.WHITE, "zap": Color("3de7c9"), "light": Color("f4d35e"), "heal": Color("7dff9a")}

## Encuentro si Router no indica otro (editor y pruebas).
@export var encounter_id: String = "sentinel_ah7"

var engine: BattleEngine = BattleEngine.new()
var encounter: Dictionary = {}
var autoplay: bool = false
var finished: bool = false
var result: String = ""

var _stage: BattleStage
var _ui: CanvasLayer
var _views: Dictionary = {}
var _hud: BattleHud
var _menu: BattleMenu
var _ring: TimingRing
var _result_box: PanelContainer
var _fast: bool = false
var _last_actor: String = ""
var _taught: Dictionary = {}


func _ready() -> void:
	var router := App.router()
	if not str(router.battle_id).is_empty():
		encounter_id = str(router.battle_id)
	autoplay = bool(router.battle_autoplay)
	_fast = autoplay or DisplayServer.get_name() == "headless"
	encounter = EncounterCatalog.load_encounter(encounter_id)
	if encounter.is_empty():
		push_error("BattleScene: encuentro desconocido %s" % encounter_id)
		return
	engine.setup(encounter, App.hero().make_party(), App.hero().skills())
	_build()
	App.music().play(str(encounter.get("music", "battle")))
	call_deferred("_run")


# ------------------------------------------------------------ flujo

func _run() -> void:
	_hud.say(str(encounter.get("intro", "¡Combate!")))
	_stage.focus(_enemies_center(), 0.35)
	await _pause(1.3)
	_stage.reset_focus()
	while engine.outcome.is_empty() and not finished:
		await _animate(engine.begin_round())
		_hud.refresh()
		_teach_round()
		await _party_phase()
		if not engine.outcome.is_empty() or finished:
			break
		await _enemy_phase()
		if not engine.outcome.is_empty():
			break
		for p in engine.party:
			_view(p.uid).set_shielded(false)
		await _animate(engine.end_round())
		_hud.refresh()
	if not finished:
		await _show_result()


func _teach_round() -> void:
	if bool(encounter.get("tutorial", false)) and engine.round_number == 1:
		_hud.hint("Sobre cada enemigo ves qué hará al final de la ronda. Elige quién actúa y pulsa Espacio/E (o toca) cuando el anillo toque el círculo.")


func _party_phase() -> void:
	_hud.say("Ronda %d · vuestro turno" % engine.round_number)
	_last_actor = ""
	while not engine.is_party_phase_over() and engine.outcome.is_empty() and not finished:
		var pick: Array = await _ask_action()
		var actor_uid := str(pick[0])
		var action: Dictionary = pick[1]
		_last_actor = actor_uid
		_stage.unmark()
		if str(action.get("type", "")) != "analyze":
			_hud.hint("")
		match str(action.get("type", "")):
			"retreat":
				_retreat()
				return
			"item":
				await _use_item(actor_uid, str(action.get("item_id", "")))
			"analyze":
				await _analyze(str(action.get("target", "")))
			_:
				await _use_skill(actor_uid, str(action.get("skill_id", "")), str(action.get("target", "")),
					int(action.get("boost", 0)))
		_hud.set_active("")


func _ask_action() -> Array:
	if autoplay:
		await _pause(0.0)
		var actor: Combatant = engine.ready_actors()[0]
		return [actor.uid, BattleAutopilot.choose(engine, actor)]
	_menu.open(engine, _last_actor)
	_hud.set_active(_menu.current_actor())
	var pick: Array = await _menu.chosen
	_menu.close()
	return pick


func _use_skill(actor_uid: String, skill_id: String, target_uid: String, boost: int) -> void:
	var skill := engine.catalog.get_def(skill_id)
	var actor := engine.combatant(actor_uid)
	var view := _view(actor_uid)
	if skill == null or actor == null or view == null:
		if actor != null:
			actor.acted = true
		return
	boost = clampi(boost, 0, engine.max_boost())
	_hud.set_active(actor_uid)
	_hud.say("%s · %s%s" % [actor.display_name, skill.display_name, ("  (potenciado ×%d)" % boost) if boost > 0 else ""])
	if boost > 0:
		_stage.spend_orbs(boost, view.center_point())
		view.flash(HalUi.GOLD, _fast, 0.35)
		App.sfx().play("pickup")
		await _pause(0.3)

	var aim := _aim_point(skill, target_uid)
	var target_view := _view(target_uid)
	if skill.is_offensive() and skill.melee and target_view != null and skill.target == "enemy":
		_stage.focus(target_view.position, 0.12)
		await view.move_to(target_view.position + Vector2(-_reach(target_view), 1), 0.32, _fast)
	elif skill.is_offensive() and skill.melee:
		await view.move_to(Vector2(196, view.home.y), 0.3, _fast)

	var timings := PackedStringArray()
	match skill.qte if skill.kind != "guard" else "none":
		CombatSkill.QTE_HOLD:
			view.hold(skill.anim, 0)
			timings.append(await _hold_press(view.top_point() + Vector2(0, -14)))
		CombatSkill.QTE_MULTI:
			for i in skill.presses():
				view.hold(skill.anim, 0)
				timings.append(await _press(aim, false, 1.0 + 0.35 * i))
				if i < skill.presses() - 1:
					view.play(skill.anim)
					await _pause(0.12)
		"none":
			timings.append(BattleRules.MISS)
		_:
			view.hold(skill.anim, 0)
			timings.append(await _press(aim, false))

	view.play(skill.anim)
	await _pause(0.1)
	if skill.is_offensive() and not skill.melee:
		for t in _skill_targets(skill, target_uid):
			_stage.beam(view.center_point() + Vector2(6, -4), t.center_point(),
				FX_COLOR.get(skill.fx, Color.WHITE), skill.fx == "zap")
	var timing := timings[0] if not timings.is_empty() else BattleRules.MISS
	var per_hit := timings if timings.size() > 1 else PackedStringArray()
	await _animate(engine.perform(actor_uid, skill_id, target_uid, timing, boost, per_hit), skill)
	_stage.reset_focus()
	await view.go_home(_fast)


func _use_item(actor_uid: String, item_id: String) -> void:
	var def: ItemDef = App.inventory().catalog().get_def(item_id)
	if def == null or not App.game_state().remove_item(item_id):
		return
	App.bus().item_used.emit(item_id)
	_hud.say("%s usa %s." % [engine.combatant(actor_uid).display_name, def.display_name])
	_view(actor_uid).play("cast")
	await _animate(engine.use_item(actor_uid, actor_uid, def.heal_amount()))
	_view(actor_uid).idle()


func _analyze(enemy_uid: String) -> void:
	var hal := _view("hal")
	var target := _view(enemy_uid)
	if hal == null or target == null:
		return
	hal.play("cast")
	App.sfx().play("scan")
	_stage.beam(hal.center_point(), target.center_point(), HalUi.CYAN, false)
	await _pause(0.25)
	await _animate(engine.analyze(enemy_uid))
	hal.idle()


func _enemy_phase() -> void:
	_hud.say("Turno de los Antihumanistas")
	for uid in engine.enemy_order():
		if not engine.outcome.is_empty():
			return
		var enemy := engine.combatant(uid)
		var intent := engine.intent_of(uid)
		var view := _view(uid)
		var move: Dictionary = intent.get("move", {})
		match str(intent.get("kind", "")):
			"attack", "release":
				_hud.say("%s · %s" % [enemy.display_name, str(move.get("name", "ataque"))])
				_maybe_taunt(enemy)
				if not BattleEngine.needs_block(intent):
					view.play("charge")
					await _pause(0.4)
					await _animate(engine.resolve_enemy(uid, BattleRules.MISS))
					view.idle()
					continue
				var big := str(intent["kind"]) == "release"
				view.play("windup")
				view.flash(Color("ff5a6a"), _fast, 0.3)
				if big:
					_stage.focus(view.position, 0.2)
					_stage.shake(1.5)
				await _pause(0.45)
				var dest := _enemy_dash_point(intent)
				_stage.focus(dest, 0.1)
				await view.move_to(dest, 0.28, _fast)
				view.hold("windup", 1)
				var block := await _press(_targets_point(intent), true, 1.25 if big else 1.0)
				view.play("attack")
				await _pause(0.08)
				await _animate(engine.resolve_enemy(uid, block))
				_stage.reset_focus()
				await view.go_home(_fast)
			"charging":
				await _animate(engine.resolve_enemy(uid, BattleRules.MISS))
				_hud.say("%s sigue cargando %s…" % [enemy.display_name, str(move.get("name", ""))])
				await _pause(0.7)
			"stunned":
				_hud.say("%s está aturdido y pierde el turno." % enemy.display_name)
				await _animate(engine.resolve_enemy(uid, BattleRules.MISS))
				if not enemy.is_stunned():
					view.set_stunned(false)
				await _pause(0.6)
		_hud.refresh()


func _press(field_point: Vector2, blocking: bool, speed: float = 1.0) -> String:
	if autoplay:
		return BattleRules.PERFECT
	_ring.start(_stage.to_screen(field_point), blocking, App.hero().timing_window(), speed)
	var timing: String = await _ring.resolved
	_feedback(timing, blocking)
	return timing


func _hold_press(field_point: Vector2) -> String:
	if autoplay:
		return BattleRules.PERFECT
	_ring.start_hold(_stage.to_screen(field_point), App.hero().timing_window() * 1.6)
	var timing: String = await _ring.resolved
	_feedback(timing, false)
	return timing


func _feedback(timing: String, blocking: bool) -> void:
	match timing:
		BattleRules.PERFECT:
			App.sfx().play("success" if blocking else "confirm")
		BattleRules.GOOD:
			App.sfx().play("blip")


# ------------------------------------------------------------ eventos → animación

func _animate(events: Array[Dictionary], skill: CombatSkill = null) -> void:
	for ev in events:
		var uid := str(ev.get("uid", ""))
		var view := _view(uid)
		var c := engine.combatant(uid)
		var at := view.center_point() if view != null else BattleStage.FIELD * 0.5
		match str(ev.get("type", "")):
			"damage":
				await _animate_damage(ev, view, c, at, skill)
			"weak":
				_hud.float_text(at + Vector2(0, -18), "¡DÉBIL!", HalUi.GOLD, 22)
			"reveal":
				var names := PackedStringArray()
				for el in ev.get("elements", []):
					names.append(BattleRules.element_name(str(el)))
				if not str(ev.get("text", "")).is_empty():
					_hud.hint("HAL: %s" % str(ev["text"]))
				_hud.say("%s es débil a: %s." % [c.display_name, ", ".join(names)])
				_hud.refresh()
				await _pause(0.6 if ev.has("text") else 0.2)
			"lock_broken":
				_hud.float_text(at + Vector2(0, -26), "¡Cerradura rota!", HalUi.CYAN, 20)
				_stage.sparks(at, HalUi.CYAN, 18)
				_hud.refresh()
				_hud.pulse_plate(uid)
				App.sfx().play("blip")
				await _pause(0.15)
			"charge_broken":
				_stage.flash_screen(HalUi.GOLD)
				_stage.punch(0.25)
				view.set_stunned(true)
				view.idle()
				_hud.say("¡Todas las cerraduras rotas! %s queda aturdido y pierde su turno." % c.display_name)
				App.sfx().play("success")
				await _pause(0.7)
			"ko":
				view.set_down(true)
				if c.is_enemy:
					_stage.sparks(at, HalUi.CYAN, 24)
					_stage.shake(3.0)
					_hud.say("%s desactivado." % c.display_name)
					App.sfx().play("success")
				else:
					_hud.say("%s no puede seguir. Se levantará en %d rondas, o HAL puede repararlo." % [c.display_name, c.ko_rounds])
				await _pause(0.5)
			"revive":
				view.set_down(false)
				_stage.spawn_fx("heal", at)
				_hud.float_text(at, "¡En pie! +%d" % int(ev.get("amount", 0)), Color("7dff9a"), 22)
				App.sfx().play("pickup")
				await _pause(0.4)
			"heal":
				_stage.spawn_fx("heal", at)
				view.flash(Color("7dff9a"), _fast, 0.3)
				_hud.float_text(at, "+%d" % int(ev.get("amount", 0)), Color("7dff9a"))
				App.sfx().play("pickup")
				await _pause(0.3)
			"guard":
				for p in engine.alive_party():
					_view(p.uid).set_shielded(true)
				_hud.say("Escudo de chatarra: el grupo recibe un %d %% menos de daño este turno." % int(ev.get("amount", 50)))
				App.sfx().play("confirm")
				await _pause(0.4)
			"orbs":
				_stage.set_orbs(engine.orbs, at)
				if not _taught.has("orbs"):
					_taught["orbs"] = true
					_hud.hint("¡Chispas solares! Antes de actuar, gástalas con ← → para potenciar: más fuerza y una cerradura más por golpe.")
			"en":
				_hud.float_text(at + Vector2(0, -10), "+%d EN" % int(ev.get("amount", 0)), HalUi.CYAN, 18)
			"drain":
				_hud.float_text(at + Vector2(0, -10), "−%d EN" % int(ev.get("amount", 0)), HalUi.CYAN, 18)
			"shield":
				view.set_shielded(true, Color("ff8a5a"))
				_hud.say("%s usa %s: recibe la mitad de daño salvo con su debilidad." % [c.display_name, str(ev.get("move", ""))])
				App.sfx().play("blip")
				await _pause(0.6)
			"shield_broken":
				view.set_shielded(false)
				if c.is_alive():
					_hud.float_text(at + Vector2(0, -22), "¡Blindaje roto!", HalUi.GOLD, 20)
					_stage.sparks(at, Color("ff8a5a"), 16)
			"charge_start":
				view.play("charge")
				_stage.focus(view.position, 0.25)
				var names := PackedStringArray()
				for el in ev.get("locks", []):
					names.append(BattleRules.element_name(str(el)))
				_hud.say("¡%s prepara %s! Rompe sus cerraduras: %s." % [c.display_name, str(ev.get("move", "")), ", ".join(names)])
				if not _taught.has("locks"):
					_taught["locks"] = true
					_hud.hint("Cada golpe del elemento correcto rompe una cerradura (con chispas, una más por golpe). Rómpelas todas y quedará aturdido.")
				_hud.refresh()
				App.sfx().play("error", 0.7)
				await _pause(1.4)
				_stage.reset_focus()
			"charging":
				view.play("charge")
			"stunned":
				pass
	_hud.refresh()
	_stage.set_orbs(engine.orbs)
	await _pause(0.25)


func _animate_damage(ev: Dictionary, view: BattlerView, c: Combatant, at: Vector2, skill: CombatSkill) -> void:
	var timing := str(ev.get("timing", BattleRules.MISS))
	var party_hit := c != null and not c.is_enemy
	var amount := int(ev.get("amount", 0))
	var attacker := _view(str(ev.get("from", "")))
	var fx := "hit"
	if skill != null and not party_hit:
		fx = skill.fx
	var blocked := party_hit and timing != BattleRules.MISS
	_stage.spawn_fx(fx, at + Vector2(randf_range(-4, 4), randf_range(-4, 4)), party_hit)
	_stage.sparks(at, FX_COLOR.get(fx, Color.WHITE), 8 if blocked else 14)
	_stage.shake(clampf(1.0 + amount / 12.0, 1.0, 5.0) * (0.5 if blocked else 1.0))
	if timing == BattleRules.PERFECT or bool(ev.get("weak", false)):
		_stage.punch(0.1)
	if view != null:
		view.hit(_fast, blocked)
	if attacker != null:
		attacker.freeze(0.07, _fast)
	var color := Color("ff6b6b") if party_hit else (HalUi.GOLD if timing == BattleRules.PERFECT else Color.WHITE)
	_hud.float_text(at, str(amount), color, 34 if timing == BattleRules.PERFECT and not party_hit else 30)
	App.sfx().play("bump")
	await _pause(0.2)


# ------------------------------------------------------------ final

func _show_result() -> void:
	finished = true
	result = engine.outcome
	_menu.close()
	var andres := engine.combatant("andres")
	var hero := App.hero()
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 10)
	if result == BattleEngine.VICTORY:
		hero.set_hp(maxi(1, andres.hp))
		for p in engine.party:
			if not p.is_alive():
				p.heal(1)
				_view(p.uid).set_down(false)
			_view(p.uid).play("victory")
		_stage.focus((PARTY_SPOTS["andres"] + PARTY_SPOTS["hal"]) * 0.5, 0.3)
		App.sfx().play("success")
		_hud.say("¡Victoria!")
		await _pause(1.2)
		col.add_child(HalUi.label("¡VICTORIA!", 34, HalUi.GOLD))
		var already: bool = App.game_state().has_flag("won_%s" % encounter_id)
		var rewards: Dictionary = encounter.get("rewards", {})
		if not already:
			var xp := int(rewards.get("experience", 0))
			col.add_child(HalUi.label("+%d XP   ·   +%d créditos" % [xp, int(rewards.get("credits", 0))], 22, HalUi.CYAN))
			var now := int(App.game_state().experience)
			var next_level := HeroProgression.level_for_xp(now + xp)
			if next_level > HeroProgression.level_for_xp(now):
				col.add_child(HalUi.label("¡Andrés sube a nivel %d! Reparte el punto de mejora en HAL (Tab → Andrés)." % next_level, 18, HalUi.GOLD, true))
		for line in encounter.get("victory_lines", []):
			var who: String = App.story().characters().display_name(str(line.get("who", "")))
			col.add_child(HalUi.label("%s: %s" % [who, str(line.get("text", ""))], 17, HalUi.TEXT, true))
	else:
		hero.set_hp(maxi(1, int(hero.max_hp() * 0.5)))
		col.add_child(HalUi.label("RETIRADA DE EMERGENCIA", 30, HalUi.CYAN))
		col.add_child(HalUi.label("HAL activa el escudo y os pone a salvo. Andrés descansa y recupera la mitad de su salud.", 18, HalUi.TEXT, true))
		col.add_child(HalUi.label("Consejo: analiza a los enemigos con HAL, guarda chispas solares para romper cerraduras y lleva comida o medicinas.", 16, HalUi.GOLD, true))
	var go := Button.new()
	go.text = "Continuar"
	go.custom_minimum_size = Vector2(220, 46)
	go.pressed.connect(func() -> void: App.router().return_from_battle(result))
	col.add_child(go)
	_result_box.add_child(col)
	_result_box.visible = true
	if not _fast:
		_result_box.modulate.a = 0.0
		create_tween().tween_property(_result_box, "modulate:a", 1.0, 0.3)
	if autoplay:
		await _pause(0.0)
		App.router().return_from_battle(result)
	else:
		go.grab_focus.call_deferred()


func _retreat() -> void:
	finished = true
	result = "retreat"
	App.hero().set_hp(maxi(1, engine.combatant("andres").hp))
	_menu.close()
	_hud.say("HAL: ¡Retirada! Volveremos mejor preparados.")
	App.router().return_from_battle("retreat")


# ------------------------------------------------------------ construcción

func _build() -> void:
	_stage = BattleStage.new()
	add_child(_stage)
	_stage.build(str(encounter.get("backdrop", "mars_canyon")), _fast)

	for member in engine.party:
		var spot: Vector2 = PARTY_SPOTS.get(member.uid, Vector2(110, 200))
		_add_view(member, spot, false)
	var spots: Array = ENEMY_SPOTS.get(clampi(engine.enemies.size(), 1, 3), ENEMY_SPOTS[3])
	for i in engine.enemies.size():
		_add_view(engine.enemies[i], spots[mini(i, spots.size() - 1)], true)

	_ui = CanvasLayer.new()
	_ui.layer = 5
	add_child(_ui)
	_hud = BattleHud.new()
	_ui.add_child(_hud)
	_hud.build(engine, _stage, _views, _fast)

	_menu = BattleMenu.new()
	_ui.add_child(_menu)
	_menu.position = Vector2(446, 300)
	_menu.chosen.connect(func(_a: String, _b: Dictionary) -> void: App.sfx().play("blip"))
	_menu.aimed.connect(func(uid: String) -> void:
		var v := _view(uid)
		if v == null:
			_stage.unmark()
		else:
			_stage.mark(v.top_point() + Vector2(0, -2)))

	_ring = TimingRing.new()
	_ui.add_child(_ring)

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ui.add_child(center)
	_result_box = HalUi.panel(HalUi.GOLD, 22)
	_result_box.custom_minimum_size = Vector2(720, 0)
	_result_box.visible = false
	center.add_child(_result_box)


func _add_view(c: Combatant, spot: Vector2, is_enemy: bool) -> void:
	var view := BattlerView.new()
	view.uid = c.uid
	view.position = spot
	view.home = spot
	var hover: float = HOVER.get(c.sheet, 0.0) if c.flying or c.sheet == "hal" else 0.0
	if BattleSheets.has_sheet(c.sheet):
		view.setup_sheet(c.sheet, is_enemy, hover)
	else:
		var tex: Texture2D = load(c.sprite_path) if ResourceLoader.exists(c.sprite_path) else null
		var off: Texture2D = load(c.sprite_off_path) if ResourceLoader.exists(c.sprite_off_path) else null
		view.setup_static(tex, is_enemy, 2.0, hover, off)
	_stage.actors.add_child(view)
	_views[c.uid] = view


func _view(uid: String) -> BattlerView:
	return _views.get(uid, null) as BattlerView


## Distancia a la que se planta quien ataca cuerpo a cuerpo (según el tamaño del blanco).
func _reach(target: BattlerView) -> float:
	return 16.0 + target.height() * 0.3


func _aim_point(skill: CombatSkill, target_uid: String) -> Vector2:
	if skill.target == "all_enemies":
		return _enemies_center() + Vector2(0, -24)
	var v := _view(target_uid)
	if v == null and skill.is_offensive():
		var alive := engine.alive_enemies()
		v = _view(alive[0].uid) if not alive.is_empty() else null
	return v.center_point() if v != null else BattleStage.FIELD * 0.5


func _skill_targets(skill: CombatSkill, target_uid: String) -> Array[BattlerView]:
	var out: Array[BattlerView] = []
	if skill.target == "all_enemies":
		for e in engine.alive_enemies():
			out.append(_view(e.uid))
	elif _view(target_uid) != null:
		out.append(_view(target_uid))
	elif not engine.alive_enemies().is_empty():
		out.append(_view(engine.alive_enemies()[0].uid))
	return out


func _enemies_center() -> Vector2:
	var sum := Vector2.ZERO
	var n := 0
	for e in engine.alive_enemies():
		sum += _view(e.uid).position
		n += 1
	return sum / n if n > 0 else Vector2(320, 200)


func _enemy_dash_point(intent: Dictionary) -> Vector2:
	var targets: Array = Array(intent.get("targets", []))
	if targets.size() == 1 and _view(str(targets[0])) != null:
		var t := _view(str(targets[0]))
		return t.position + Vector2(18.0 + t.height() * 0.3 + 10.0, 2)
	return Vector2(196, 200)


func _targets_point(intent: Dictionary) -> Vector2:
	var targets: Array = Array(intent.get("targets", []))
	if targets.size() == 1 and _view(str(targets[0])) != null:
		return _view(str(targets[0])).center_point()
	return (PARTY_SPOTS["andres"] + PARTY_SPOTS["hal"]) * 0.5 + Vector2(0, -26)


func _maybe_taunt(enemy: Combatant) -> void:
	if enemy.taunts.is_empty() or engine.round_number % 2 == 0:
		return
	_hud.hint("«%s»" % str(enemy.taunts[int(engine.round_number * 0.5) % enemy.taunts.size()]))


func _pause(seconds: float) -> void:
	if _fast or seconds <= 0.0:
		await get_tree().process_frame
		return
	await get_tree().create_timer(seconds).timeout
