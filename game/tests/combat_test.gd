extends SceneTree
## Combate: fórmulas, cerraduras, combos, IA enemiga y un combate real vía Router (autoplay).
## godot --headless --path game --script res://tests/combat_test.gd

var _failed: int = 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	print("[combat] start")
	var story: Node = root.get_node("StoryDirector")
	story.new_game()
	_test_progression()
	_test_rules()
	_test_locks_and_combo()
	_simulate("sentinel_ah7", 5, BattleRules.GOOD, true)
	_simulate("sentinel_ah7", 5, BattleRules.MISS, true)
	_simulate("sentinel_ah7", 2, BattleRules.MISS, false)
	_simulate("drones_meteorite", 5, BattleRules.GOOD, true)
	_simulate("drones_meteorite", 5, BattleRules.MISS, false)
	await _test_scene_flow()
	story.new_game()
	if _failed == 0:
		print("[combat] PASS")
		quit(0)
	else:
		printerr("[combat] FAIL (%d)" % _failed)
		quit(1)


func _test_progression() -> void:
	_check(HeroProgression.xp_for_level(1) == 0 and HeroProgression.xp_for_level(2) == 40, "XP: nivel 2 a los 40")
	_check(HeroProgression.level_for_xp(39) == 1 and HeroProgression.level_for_xp(40) == 2, "nivel según XP")
	_check(HeroProgression.level_for_xp(340) == 5, "tras los capítulos 1–3 (340 XP) Andrés es nivel 5")
	var hero: Node = root.get_node("Hero")
	var gs: Node = root.get_node("GameState")
	_check(int(hero.level()) == 1 and int(hero.unspent) == 0, "partida nueva: nivel 1 sin puntos")
	gs.add_experience(100)
	_check(int(hero.level()) == 3 and int(hero.unspent) == 2, "subir a nivel 3 da 2 puntos")
	var hp_before: int = hero.max_hp()
	_check(hero.spend_point("aptitudes"), "gastar punto en aptitudes")
	_check(int(hero.max_hp()) == hp_before + 12, "aptitudes: +12 de salud máxima")
	_check(hero.spend_point("conocimientos"), "gastar punto en conocimientos")
	_check(not hero.spend_point("destrezas"), "sin puntos no se gasta")
	_check(hero.known_skills("andres").has("solar_flash"), "conocimientos 1 desbloquea Destello solar")
	_check(not hero.known_skills("andres").has("comet_dash"), "Embestida cometa pide destrezas 2")
	hero.set_hp(10)
	var inv: Node = root.get_node("Inventory")
	gs.add_item("medkit")
	_check(inv.use("medkit") and int(hero.hp) == 55 and not inv.has("medkit"), "el botiquín cura 45 y se gasta (%d)" % int(hero.hp))
	gs.add_item("space_tortilla")
	hero.full_heal()
	_check(not inv.use("space_tortilla"), "con la salud llena no se come")
	root.get_node("StoryDirector").new_game()


func _test_rules() -> void:
	_check(BattleRules.judge(0.02, 0.16) == BattleRules.PERFECT, "pulsación perfecta")
	_check(BattleRules.judge(-0.12, 0.16) == BattleRules.GOOD, "pulsación buena")
	_check(BattleRules.judge(0.3, 0.16) == BattleRules.MISS, "pulsación fallida")
	var normal := BattleRules.damage(10, 2, 1.0, false)
	var weak := BattleRules.damage(10, 2, 1.0, true)
	var perfect := BattleRules.damage(10, 2, 1.0, false, BattleRules.attack_mult(BattleRules.PERFECT))
	_check(weak > normal and perfect > normal, "debilidad y golpe perfecto hacen más daño (%d/%d/%d)" % [normal, weak, perfect])
	var blocked := BattleRules.damage(10, 2, 1.0, false, 1.0, BattleRules.block_mult(BattleRules.PERFECT))
	_check(blocked < normal and blocked >= 1, "bloqueo perfecto reduce el daño (%d)" % blocked)


func _test_locks_and_combo() -> void:
	var hero: Node = root.get_node("Hero")
	var e := BattleEngine.new()
	e.setup(EncounterCatalog.load_encounter("sentinel_ah7"), hero.make_party(), hero.skills(), 7)
	_check(e.enemies.size() == 1 and e.enemies[0].weak.has("electricidad"), "AH-7 cargado, débil a electricidad")
	var ah7 := e.enemies[0]
	_check(not ah7.knows_weakness("electricidad"), "la debilidad empieza oculta")
	# Rondas 1 y 2: acciones normales anunciadas al empezar la ronda; la 3.ª anuncia el Martillo sísmico.
	for i in 2:
		e.begin_round()
		var intent := e.intent_of(ah7.uid)
		_check(str(intent["kind"]) == "attack", "ronda %d: AH-7 anuncia una acción normal (%s)" % [i + 1, str(intent.get("move", {}).get("name", ""))])
		e.resolve_enemy(ah7.uid, BattleRules.PERFECT)
		e.end_round()
	var ev := e.begin_round()
	_check(_has(ev, "charge_start") and str(e.intent_of(ah7.uid)["kind"]) == "release",
		"ronda 3: AH-7 anuncia el Martillo sísmico y lo suelta al final de la ronda")
	_check(ah7.is_charging() and ah7.locks().size() == 3, "tres cerraduras: electricidad, impacto, impacto")
	var hp_before := ah7.hp
	ev = e.perform("hal", "hal_pulse", ah7.uid, BattleRules.GOOD)
	_check(_has(ev, "weak") and _has(ev, "lock_broken") and _has(ev, "reveal"), "Pulso de HAL: golpe débil, rompe la cerradura eléctrica y revela la debilidad")
	_check(ah7.hp < hp_before and ah7.locks().size() == 2, "quedan dos cerraduras de impacto")
	e.orbs = 1
	ev = e.perform("andres", "basic_andres", ah7.uid, BattleRules.PERFECT, 1)
	_check(_has(ev, "boost") and _has(ev, "charge_broken") and ah7.is_stunned() and not ah7.is_charging(),
		"golpe potenciado con una chispa: rompe dos cerraduras, carga cancelada y AH-7 aturdido")
	_check(e.combo_points == 2 and e.orbs == 2, "golpe básico perfecto: +2 de combo y +2 chispas (%d/%d)" % [e.combo_points, e.orbs])
	_check(e.is_party_phase_over(), "los dos han actuado")
	ev = e.resolve_enemy(ah7.uid, BattleRules.MISS)
	_check(_has(ev, "stunned") and not _has(ev, "damage"), "aturdido: el martillo no llega a caer")
	e.end_round()
	_check(not ah7.is_stunned(), "se recupera para la ronda siguiente")
	e.begin_round()
	e.combo_points = 3
	_check(e.can_use("andres", "combo_double_spark"), "combo disponible con 3 puntos")
	ev = e.perform("andres", "combo_double_spark", ah7.uid, BattleRules.PERFECT, 0,
		PackedStringArray([BattleRules.PERFECT, BattleRules.MISS]))
	_check(e.combo_points == 0 and _count(ev, "damage") == 2, "Chispa doble: gasta el combo y da dos golpes")

	# Análisis de HAL: gratis y una vez.
	var scan := BattleEngine.new()
	scan.setup(EncounterCatalog.load_encounter("drones_meteorite"), hero.make_party(), hero.skills(), 5)
	scan.begin_round()
	_check(scan.can_analyze("e0"), "HAL puede analizar al dron")
	ev = scan.analyze("e0")
	_check(_has(ev, "reveal") and scan.enemies[0].knows_weakness("luz") and not scan.combatant("hal").acted,
		"analizar revela la debilidad a la luz sin gastar el turno")
	_check(not scan.can_analyze("e0"), "solo se analiza una vez")

	# Coraza enemiga: la debilidad la rompe.
	var drone_b := scan.enemies[1]
	drone_b.shield_rounds = 2
	var plain := scan.perform("andres", "basic_andres", drone_b.uid, BattleRules.GOOD)
	_check(not _has(plain, "shield_broken") and drone_b.shield_rounds == 2, "un golpe de impacto no rompe el blindaje")
	ev = scan.perform("hal", "basic_hal", drone_b.uid, BattleRules.GOOD)
	_check(_has(ev, "shield_broken") and drone_b.shield_rounds == 0, "la luz (su debilidad) rompe el blindaje")

	var party_ko := BattleEngine.new()
	party_ko.setup(EncounterCatalog.load_encounter("sentinel_ah7"), hero.make_party(), hero.skills(), 3)
	party_ko.begin_round()
	party_ko.party[1].take_damage(9999)
	_check(not party_ko.can_use("andres", "combo_double_spark"), "sin HAL en pie no hay combo")
	party_ko.end_round()
	_check(not party_ko.party[1].is_alive(), "HAL sigue fuera de combate una ronda")
	party_ko.end_round()
	_check(party_ko.party[1].is_alive(), "a la segunda ronda HAL se reinicia sola")
	party_ko.begin_round()
	party_ko.party[1].en = 5
	party_ko.party[0].take_damage(9999)
	ev = party_ko.perform("hal", "hal_repair", "andres", BattleRules.GOOD)
	_check(party_ko.party[0].is_alive() and _has(ev, "revive"), "Reparación de HAL levanta a Andrés")


## expect_win = false: solo comprobamos que el combate termina (ganar o perder) sin bloquearse.
func _simulate(encounter_id: String, level: int, timing: String, expect_win: bool) -> void:
	var gs: Node = root.get_node("GameState")
	var hero: Node = root.get_node("Hero")
	root.get_node("StoryDirector").new_game()
	gs.add_experience(HeroProgression.xp_for_level(level))
	while int(hero.unspent) > 0:
		hero.spend_point(HeroProgression.stat_ids()[int(hero.unspent) % 3])
	var e := BattleEngine.new()
	e.setup(EncounterCatalog.load_encounter(encounter_id), hero.make_party(), hero.skills(), 11)
	var rounds := 0
	while e.outcome.is_empty() and rounds < 40:
		e.begin_round()
		while not e.is_party_phase_over() and e.outcome.is_empty():
			var actor: Combatant = e.ready_actors()[0]
			var act := BattleAutopilot.choose(e, actor)
			var before := actor.acted
			e.perform(actor.uid, str(act["skill_id"]), str(act["target"]), timing, int(act["boost"]))
			if actor.acted == before:
				actor.acted = true
		for uid in e.enemy_order():
			e.resolve_enemy(uid, timing)
		e.end_round()
		rounds += 1
	var label := "%s nivel %d, pulsaciones «%s»: %s en %d rondas (salud del grupo %d/%d)" % [encounter_id, level,
		timing, e.outcome, rounds, e.party[0].hp + e.party[1].hp, e.party[0].max_hp + e.party[1].max_hp]
	if expect_win:
		_check(e.outcome == BattleEngine.VICTORY and rounds >= 5, label)
	else:
		_check(not e.outcome.is_empty(), label)


func _test_scene_flow() -> void:
	var story: Node = root.get_node("StoryDirector")
	var missions: Node = root.get_node("MissionLog")
	var gs: Node = root.get_node("GameState")
	var router: Node = root.get_node("Router")
	var bus: Node = root.get_node("EventBus")
	story.new_game()
	for id in ["last_seed", "signal_from_moon", "ice_of_shackleton", "red_garden"]:
		if not missions.is_active(id):
			missions.start_mission(id)
		for obj in missions.get_def(id).objectives:
			missions.complete_objective(id, obj.id)
	_check(missions.is_completed("red_garden"), "capítulos 1–3 completados")
	_check(not story.can_battle("sentinel_ah7"), "sin la misión de Bruno no hay combate")
	story.talk_to("bruno")
	bus.dialogue_finished.emit("offer:methane_heart")
	_check(missions.is_active("methane_heart"), "Bruno ofrece «Corazón de metano»")
	_check(story.can_battle("sentinel_ah7"), "ahora AH-7 espera en el barranco")
	var xp_before := int(gs.experience)
	var credits_before := int(gs.credits)
	router.battle_autoplay = true
	router.go_surface("mars", "ship")
	await _wait_scene(func() -> bool: return current_scene is SurfaceLevel and not router.is_busy())
	bus.dialogue_finished.emit("info")
	var mars := current_scene as SurfaceLevel
	var robot_pos: Vector2 = (mars.spawner.entities["ah7_sentinel"]["node"] as Node2D).global_position
	(mars.get_node("%Player") as Node2D).global_position = robot_pos + Vector2(-24, 0)
	bus.interaction_requested.emit("ah7_sentinel", "enemy")
	await process_frame
	bus.dialogue_finished.emit("battle:sentinel_ah7:ah7_sentinel")
	await _wait_scene(func() -> bool: return current_scene is BattleScene)
	_check(current_scene is BattleScene, "la escena de combate se abre")
	await _wait_scene(func() -> bool: return current_scene is SurfaceLevel and not router.is_busy(), 3000)
	router.battle_autoplay = false
	_check(current_scene is SurfaceLevel and (current_scene as SurfaceLevel).location_id == "mars", "vuelta a Marte tras el combate")
	_check(gs.has_flag("won_sentinel_ah7"), "AH-7 desactivado (bandera)")
	_check(str(missions.get_current_objective("methane_heart").id) == "take_engine", "objetivo siguiente: recoger el motor")
	_check(root.get_node("Inventory").has("orders_chip"), "HAL guarda el chip de órdenes")
	_check(int(gs.experience) >= xp_before + 60 + 0 and int(gs.credits) >= credits_before + 40, "recompensa: +60 XP y +40 créditos")
	var level := current_scene as SurfaceLevel
	var robot: Node2D = level.spawner.entities["ah7_sentinel"]["node"]
	_check((level.get_node("%Player") as Node2D).global_position.distance_to(robot.global_position) < 60.0, "Andrés reaparece junto al robot")


func _wait_scene(cond: Callable, frames: int = 240) -> void:
	for i in frames:
		await process_frame
		if cond.call():
			await process_frame
			return


func _has(events: Array[Dictionary], type: String) -> bool:
	for ev in events:
		if str(ev.get("type", "")) == type:
			return true
	return false


func _count(events: Array[Dictionary], type: String) -> int:
	var n := 0
	for ev in events:
		if str(ev.get("type", "")) == type:
			n += 1
	return n


func _check(ok: bool, label: String) -> void:
	if ok:
		print("[combat] OK  %s" % label)
	else:
		printerr("[combat] FAIL %s" % label)
		_failed += 1
