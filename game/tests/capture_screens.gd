extends SceneTree
## Herramienta de revisión visual (no es un test): guarda capturas de las escenas clave.
## Requiere ventana (no --headless):
##   godot --path game --script res://tests/capture_screens.gd -- /ruta/salida

var _out: String = "user://screens"


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		_out = args[0]
	DirAccess.make_dir_recursive_absolute(_out)
	call_deferred("_run")


func _run() -> void:
	var story: Node = root.get_node("StoryDirector")
	var router: Node = root.get_node("Router")
	var bus: Node = root.get_node("EventBus")
	story.new_game()

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
	player.global_position = Vector2(26 * 16 + 8, 10 * 16)
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
	for place in [["earth", Vector2(48, 13), "15_earth_neon"], ["earth", Vector2(14, 27), "16_earth_south"],
			["earth", Vector2(53, 23), "17_earth_scrap"], ["moon", Vector2(15, 30), "18_moon_district"],
			["mars", Vector2(18, 31), "19_mars_colony"]]:
		router.pending_surface = place[0]
		router.pending_spawn = "ship"
		await _show("res://scenes/surface/surface_level.tscn", "_tmp", 10)
		_close_dialogue()
		var p := current_scene.get_node("%Player") as Node2D
		p.global_position = (place[1] as Vector2) * 16.0 + Vector2(8, 16)
		(current_scene.get_node("%FollowCamera") as Node2D).global_position = p.global_position
		await _frames(60)
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
	story.new_game()
	quit(0)


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
