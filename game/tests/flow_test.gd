extends SceneTree
## Flujo real de escenas vía Router: intro → Tierra → laboratorio → Tierra → espacio → Luna.
## godot --headless --path game --script res://tests/flow_test.gd

var _failed: int = 0
var _ctx: String = ""


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	print("[flow] start")
	var bus: Node = root.get_node("EventBus")
	var story: Node = root.get_node("StoryDirector")
	var router: Node = root.get_node("Router")
	var missions: Node = root.get_node("MissionLog")
	bus.dialogue_requested.connect(func(_s: String, _l: Array, c: String) -> void: _ctx = c)

	story.new_game()
	router.play_cutscene("intro", "earth")
	await _wait_scene("Cutscene")
	(current_scene as CutscenePlayer)._finish()
	await _wait_scene("SurfaceLevel")
	_check(current_scene is SurfaceLevel and (current_scene as SurfaceLevel).location_id == "earth", "intro → Tierra")
	var level := current_scene as SurfaceLevel
	var start: Vector2 = level.spawner.spawns["start"]
	_check((level.get_node("%Player") as Node2D).global_position == start, "aparece en la casa")
	_check(_ctx == "info", "HAL da la bienvenida al llegar")
	_finish_dialogue(bus)

	# Interacciones del capítulo 1 a través de la escena
	bus.interaction_requested.emit("lucia", "npc")
	_finish_dialogue(bus)
	bus.interaction_requested.emit("the_seed", "item")
	_check(not root.get_node("GameState").has_item("the_seed"), "La Semilla bloqueada antes de tiempo")
	_finish_dialogue(bus)
	bus.scan_completed.emit("earth_dead_plant", true)
	bus.scan_completed.emit("earth_air_sensor", true)
	bus.interaction_requested.emit("lucia", "npc")
	_finish_dialogue(bus)
	bus.interaction_requested.emit("the_seed", "item")
	_finish_dialogue(bus)
	_check(root.get_node("GameState").has_item("the_seed"), "La Semilla recogida")
	_check(not level.spawner.entities["the_seed"]["node"].visible, "el cofre desaparece")
	bus.interaction_requested.emit("astra", "ship")
	_check(_ctx == "info", "HAL impide despegar sin programa")
	_finish_dialogue(bus)

	# Laboratorio y regreso
	var player_pos := Vector2(27 * 16 + 8, 19 * 16)
	(level.get_node("%Player") as Node2D).global_position = player_pos
	bus.interaction_requested.emit("launch_terminal", "terminal")
	await _wait_scene("ProbeLab")
	_check(str(router.lab_challenge_id) == "launch_sequence", "terminal abre el reto de despegue")
	bus.challenge_solved.emit("launch_sequence")
	router.return_from_lab()
	await _wait_scene("SurfaceLevel")
	level = current_scene as SurfaceLevel
	_check((level.get_node("%Player") as Node2D).global_position == player_pos, "vuelve junto a la terminal")

	# Despegue
	bus.interaction_requested.emit("astra", "ship")
	await _wait_scene("SpaceMain")
	await process_frame
	_check(missions.is_completed("last_seed"), "despegue completa el capítulo 1")
	var ship := current_scene.get_node("World/AstraShip") as ShipController
	var earth := current_scene.get_node("World/Earth") as PlanetZone
	_check(ship.global_position.distance_to(earth.global_position) < earth.scan_radius, "la nave aparece junto a la Tierra")

	# Aterrizar en la Luna está bloqueado hasta la misión de Vega
	var moon := current_scene.get_node("World/Moon") as PlanetZone
	ship.global_position = moon.global_position + Vector2(0, -moon.body_radius - 30)
	await physics_frame
	await physics_frame
	(current_scene.get_node("SpaceDirector") as SpaceDirector)._on_land_requested()
	await _frames(3)
	_check(current_scene.name == "SpaceMain", "Luna bloqueada: seguimos en el espacio")

	missions.start_mission("signal_from_moon")
	for obj in ["reach_moon_sector", "scan_probe_signal", "report_to_station"]:
		missions.complete_objective("signal_from_moon", obj)
	(current_scene.get_node("SpaceDirector") as SpaceDirector)._on_land_requested()
	await _wait_scene("SurfaceLevel")
	_check((current_scene as SurfaceLevel).location_id == "moon", "aterrizaje en la Luna")

	story.new_game()
	if _failed == 0:
		print("[flow] PASS")
		quit(0)
	else:
		printerr("[flow] FAIL (%d)" % _failed)
		quit(1)


func _finish_dialogue(bus: Node) -> void:
	if not _ctx.is_empty():
		var c := _ctx
		_ctx = ""
		var panel := current_scene.get_node_or_null("%DialoguePanel")
		if panel != null and panel.visible:
			panel.call("_finish")
		else:
			bus.dialogue_finished.emit(c)


func _wait_scene(scene_name: String) -> void:
	for i in 120:
		await process_frame
		if current_scene != null and current_scene.name == scene_name and not root.get_node("Router").is_busy():
			await process_frame
			return
	_check(false, "timeout esperando escena %s" % scene_name)


func _frames(n: int) -> void:
	for i in n:
		await process_frame


func _check(ok: bool, label: String) -> void:
	if ok:
		print("[flow] OK  %s" % label)
	else:
		printerr("[flow] FAIL %s" % label)
		_failed += 1
