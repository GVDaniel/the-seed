extends SceneTree
## Herramienta de revisión visual (no es un test): guarda capturas de las escenas clave.
## Requiere ventana (no --headless):
##   godot --path game --script res://tests/capture_screens.gd -- /ruta/salida [ch4]
## Con «ch4» solo captura el capítulo 4 (combate, taller, HAL Andrés).

var _out: String = "user://screens"
var _only_ch4: bool = false


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		_out = args[0]
	_only_ch4 = args.size() > 1 and args[1] == "ch4"
	DirAccess.make_dir_recursive_absolute(_out)
	call_deferred("_run")


func _run() -> void:
	var story: Node = root.get_node("StoryDirector")
	var router: Node = root.get_node("Router")
	var bus: Node = root.get_node("EventBus")
	story.new_game()
	if _only_ch4:
		await _capture_chapter4()
		story.new_game()
		quit(0)
		return

	await _show("res://scenes/ui/main_menu.tscn", "01_menu", 30)

	router.cutscene_id = "intro"
	await _show("res://scenes/story/cutscene.tscn", "02_intro", 150)

	router.pending_surface = "earth"
	router.pending_spawn = "start"
	await _show("res://scenes/surface/surface_level.tscn", "03_earth_arrival", 120)
	bus.dialogue_finished.emit("info")
	_close_dialogue()
	await _frames(20)
	await _shot("04_earth")
	var player := current_scene.get_node("%Player") as Node2D
	player.global_position = Vector2(29 * 16 + 8, 11 * 16)
	await _frames(40)
	await _shot("05_earth_lucia")
	story.talk_to("lucia")
	await _frames(120)
	await _shot("06_dialogue")
	_close_dialogue()
	bus.scan_completed.emit("earth_dead_plant", true)
	await _frames(30)
	await _shot("07_analysis")
	(current_scene.get_node("%AnalysisPanel") as AnalysisPanel).close()
	bus.challenge_solved.emit("launch_sequence")
	root.get_node("GameState").add_item("the_seed")
	var hal := current_scene.get_node("%HalInterface") as HalInterface
	hal.open("inventory")
	for id in HalInterface.TAB_IDS:
		hal._select(id)
		await _frames(70)
		await _shot("hal_%s" % id)
	hal.close()
	await _frames(5)
	await _shot("07b_earth_hal_follower")

	router.lab_challenge_id = "delta_samples"
	await _show("res://scenes/lab/probe_lab.tscn", "08_lab", 30)
	var lab := current_scene
	for op in ["REPETIR", "AVANZAR", "SI_MUESTRA", "RECOGER", "FIN_SI", "FIN_REPETIR"]:
		if op == "REPETIR":
			lab.call("_add_repeat")
		else:
			lab.call("_add_op", op)
	await _frames(10)
	await _shot("09_lab_program")

	router.space_spawn_near = "earth"
	await _show("res://scenes/space/space_main.tscn", "10_space", 60)
	var ship := current_scene.get_node("World/AstraShip") as Node2D
	ship.global_position = Vector2(1100, -200)
	await _frames(60)
	await _shot("11_space_moon")
	var hal_space := current_scene.get_node("HalInterface") as HalInterface
	hal_space.open("map")
	await _frames(40)
	await _shot("hal_space_route")
	hal_space.close()

	for map_id in ["moon", "mars"]:
		router.pending_surface = map_id
		router.pending_spawn = "ship"
		root.get_node("GameState").set_flag("arrived_%s" % map_id)
		await _show("res://scenes/surface/surface_level.tscn", "12_%s" % map_id, 60)

	# Mundo cyberpunk: calles, interiores y tienda
	for place in [["earth", Vector2(16, 27), "15_earth_neon"], ["earth", Vector2(32, 36), "16_earth_market"],
			["earth", Vector2(52, 19), "17_earth_scrap"], ["earth", Vector2(9, 18), "17b_earth_park"],
			["moon", Vector2(12, 16), "18_moon_district"], ["moon", Vector2(42, 17), "18b_moon_crater"],
			["mars", Vector2(22, 24), "19_mars_colony"], ["mars", Vector2(25, 12), "19b_mars_plaza"]]:
		router.pending_surface = place[0]
		router.pending_spawn = "ship"
		await _show("res://scenes/surface/surface_level.tscn", "_tmp", 10)
		_close_dialogue()
		var p := current_scene.get_node("%Player") as Node2D
		p.global_position = (place[1] as Vector2) * 16.0 + Vector2(8, 16)
		(current_scene.get_node("%FollowCamera") as Node2D).global_position = p.global_position
		await _frames(150)
		_close_dialogue()
		await _frames(5)
		await _shot(place[2])
	for interior_id in ["moon_bar", "earth_shop", "mars_bar"]:
		router.pending_surface = interior_id
		router.pending_spawn = "entrance"
		await _show("res://scenes/surface/surface_level.tscn", "20_%s" % interior_id, 50)
		_close_dialogue()
	bus.shop_requested.emit("mars_cantina")
	await _frames(30)
	await _shot("21_shop_panel")
	(current_scene.get_node("%ShopPanel") as ShopPanel).close()
	var hal_crew := current_scene.get_node("%HalInterface") as HalInterface
	hal_crew.open("crew")
	await _frames(60)
	await _shot("22_hal_crew")
	hal_crew.close()

	router.cutscene_id = "ending"
	await _show("res://scenes/story/cutscene.tscn", "14_ending", 150)
	await _capture_chapter4()
	story.new_game()
	quit(0)


func _capture_chapter4() -> void:
	var story: Node = root.get_node("StoryDirector")
	var router: Node = root.get_node("Router")
	var bus: Node = root.get_node("EventBus")
	var missions: Node = root.get_node("MissionLog")
	var gs: Node = root.get_node("GameState")
	story.new_game()
	for id in ["last_seed", "signal_from_moon", "ice_of_shackleton", "red_garden"]:
		if not missions.is_active(id):
			missions.start_mission(id)
		for obj in missions.get_def(id).objectives:
			missions.complete_objective(id, obj.id)
	for flag in ["arrived_mars", "arrived_mars_garage"]:
		gs.set_flag(flag)
	story.talk_to("bruno")
	bus.dialogue_finished.emit("offer:methane_heart")
	story.talk_to("yusuf")
	bus.dialogue_finished.emit("offer:side_ice_core")
	gs.add_item("medkit")
	gs.add_item("space_tortilla")
	router.pending_surface = "mars"
	router.pending_spawn = "ship"
	await _show("res://scenes/surface/surface_level.tscn", "_tmp", 20)
	_close_dialogue()
	var p := current_scene.get_node("%Player") as Node2D
	p.global_position = Vector2(59 * 16 + 8, 13 * 16)
	(current_scene.get_node("%FollowCamera") as Node2D).global_position = p.global_position
	await _frames(60)
	_close_dialogue()
	await _frames(5)
	await _shot("30_mars_canyon")
	var hal := current_scene.get_node("%HalInterface") as HalInterface
	hal.open("status")
	await _frames(70)
	await _shot("31_hal_status")
	hal._select("missions")
	await _frames(60)
	await _shot("32_hal_missions_side")
	hal.close()

	router.battle_id = "sentinel_ah7"
	router.battle_return_location = "mars"
	await _show("res://scenes/battle/battle.tscn", "33_battle_intro", 60)
	var battle := current_scene as BattleScene
	await _frames(90)
	await _shot("34_battle_menu")
	var menu := battle._menu
	menu._skills_page(_skills(battle, "andres"))
	await _frames(10)
	await _shot("35_battle_skills")
	menu.chosen.emit("andres", {"type": "skill", "skill_id": "basic_andres", "target": "e0", "boost": 0})
	await _frames(55)
	await _shot("36_battle_timing")
	battle._ring.force(BattleRules.PERFECT)
	await _frames(14)
	await _shot("36b_battle_impact")
	await _frames(80)
	var ah7: Combatant = battle.engine.enemies[0]
	ah7.charge = {"move": {"name": "Martillo sísmico", "target": "all"}, "turns_left": 1,
		"locks": PackedStringArray(["electricidad", "impacto", "impacto"])}
	ah7.intent = {"kind": "release", "uid": ah7.uid, "move": ah7.charge["move"], "turns": 1}
	ah7.reveal("electricidad")
	battle.engine.orbs = 3
	battle._stage.set_orbs(3)
	battle._view(ah7.uid).play("charge")
	battle._hud.say("¡Centinela AH-7 prepara Martillo sísmico! Rompe sus cerraduras: electricidad, impacto, impacto.")
	battle._hud.refresh()
	await _frames(40)
	await _shot("37_battle_locks")
	router.battle_id = "drones_meteorite"
	await _show("res://scenes/battle/battle.tscn", "38_battle_drones", 150)

	router.pending_surface = "mars_garage"
	router.pending_spawn = "entrance"
	await _show("res://scenes/surface/surface_level.tscn", "39_mars_garage", 50)
	_close_dialogue()


func _skills(battle: BattleScene, user: String) -> Array[CombatSkill]:
	var out: Array[CombatSkill] = []
	for id in battle.engine.combatant(user).skills:
		var s := battle.engine.catalog.get_def(id)
		if s != null and s.kind != "basic":
			out.append(s)
	return out


func _close_dialogue() -> void:
	var dlg := current_scene.get_node_or_null("%DialoguePanel")
	if dlg == null:
		dlg = current_scene.get_node_or_null("DialoguePanel")
	if dlg != null and dlg.visible:
		dlg.call("_finish")


func _show(path: String, shot_name: String, frames: int) -> void:
	change_scene_to_file(path)
	await _frames(frames)
	await _shot(shot_name)


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _shot(shot_name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	img.save_png(_out.path_join(shot_name + ".png"))
	print("[capture] ", shot_name)
