extends SceneTree
## Transiciones de misión + flujo completo «Señal desde la Luna».
## godot --headless --path game --script res://tests/mission_test.gd


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var failed := 0
	print("[mission] start")

	var missions: Node = root.get_node("MissionLog")
	var notebook: Node = root.get_node("ScienceNotebook")
	var game_state: Node = root.get_node("GameState")

	# Aísla persistencia de la prueba
	missions.clear_all_progress_for_tests()
	var xp_before: int = int(game_state.get("experience"))

	var def: MissionDef = missions.get_def("signal_from_moon")
	if def == null or def.objectives.size() != 3:
		printerr("[mission] FAIL: definición signal_from_moon")
		failed += 1
		_finish(failed)
		return
	print("[mission] Def OK (%s)" % def.title)

	var state: MissionState = missions.get_state("signal_from_moon")
	if state.status != MissionState.Status.AVAILABLE:
		printerr("[mission] FAIL: estado inicial no AVAILABLE")
		failed += 1

	# No se puede completar objetivo sin estar activa
	if missions.complete_objective("signal_from_moon", "reach_moon_sector"):
		printerr("[mission] FAIL: objetivo sin misión activa")
		failed += 1

	# Start
	if not missions.start_mission("signal_from_moon"):
		printerr("[mission] FAIL: no arrancó la misión")
		failed += 1
	state = missions.get_state("signal_from_moon")
	if state.status != MissionState.Status.ACTIVE:
		printerr("[mission] FAIL: no quedó ACTIVE")
		failed += 1
	else:
		print("[mission] AVAILABLE → ACTIVE OK")

	# No reiniciar si ya activa
	if missions.start_mission("signal_from_moon"):
		printerr("[mission] FAIL: no debería reiniciar misión activa")
		failed += 1

	# Objetivo fuera de orden
	if missions.complete_objective("signal_from_moon", "scan_probe_signal"):
		printerr("[mission] FAIL: permitió objetivo fuera de orden")
		failed += 1

	# Objetivo 1 una vez
	if not missions.complete_objective("signal_from_moon", "reach_moon_sector"):
		printerr("[mission] FAIL: reach_moon_sector")
		failed += 1
	if missions.complete_objective("signal_from_moon", "reach_moon_sector"):
		printerr("[mission] FAIL: duplicó reach_moon_sector")
		failed += 1
	else:
		print("[mission] Objetivo único OK")

	if not missions.complete_objective("signal_from_moon", "scan_probe_signal"):
		printerr("[mission] FAIL: scan_probe_signal")
		failed += 1

	# Simula escaneo previo del POI (el reward es otra entrada)
	notebook.record_discovery("lunar_probe_signal")

	if not missions.complete_objective("signal_from_moon", "report_to_station"):
		printerr("[mission] FAIL: report_to_station / completar misión")
		failed += 1

	state = missions.get_state("signal_from_moon")
	if state.status != MissionState.Status.COMPLETED:
		printerr("[mission] FAIL: no COMPLETED")
		failed += 1
	else:
		print("[mission] Flujo completo → COMPLETED OK")

	var xp_after: int = int(game_state.get("experience"))
	if xp_after < xp_before + 50:
		printerr("[mission] FAIL: XP no aplicada (%d -> %d)" % [xp_before, xp_after])
		failed += 1
	else:
		print("[mission] Recompensa XP OK")

	if not notebook.is_discovered("lunar_signal_analysis"):
		printerr("[mission] FAIL: no desbloqueó lunar_signal_analysis")
		failed += 1
	else:
		print("[mission] Unlock científico OK")

	# Persistencia: recargar desde disco
	missions.load_local()
	state = missions.get_state("signal_from_moon")
	if state.status != MissionState.Status.COMPLETED:
		printerr("[mission] FAIL: load reinició misión completada")
		failed += 1
	else:
		print("[mission] Persistencia COMPLETED OK")

	if missions.start_mission("signal_from_moon"):
		printerr("[mission] FAIL: se pudo reiniciar misión completada")
		failed += 1

	# Escena: nodos clave
	var packed := load("res://scenes/space/space_main.tscn") as PackedScene
	var scene := packed.instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	if scene.get_node_or_null("MissionDirector") == null:
		printerr("[mission] FAIL: MissionDirector ausente")
		failed += 1
	if scene.get_node_or_null("DialoguePanel") == null:
		printerr("[mission] FAIL: DialoguePanel ausente")
		failed += 1
	var probe := scene.get_node_or_null("World/LunarProbeSignal")
	if probe == null or str(probe.get("destination_id")) != "lunar_probe_signal":
		printerr("[mission] FAIL: faro lunar ausente")
		failed += 1
	else:
		print("[mission] Escena OK")

	scene.queue_free()
	await process_frame
	_finish(failed)


func _finish(failed: int) -> void:
	if failed == 0:
		print("[mission] PASS")
		quit(0)
	else:
		printerr("[mission] FAIL (%d)" % failed)
		quit(1)
