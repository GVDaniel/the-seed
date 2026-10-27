extends SceneTree
## Pruebas del intérprete y victoria del reto básico (+ bucles tras básico OK).
## godot --headless --path game --script res://tests/probe_interpreter_test.gd


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var failed := 0
	print("[lab] interpreter tests — start")

	failed += _test_basic_movement()
	failed += _test_reset()
	failed += _test_invalid_program()
	failed += _test_scan_without_poi()
	failed += _test_challenge_victory()
	failed += _test_challenge_incomplete()

	if failed == 0:
		print("[lab] básico OK — habilitando pruebas de bucle")
		failed += _test_loop_victory()
	else:
		printerr("[lab] se omiten bucles: el intérprete básico falló")

	failed += await _test_scene_loads()

	if failed == 0:
		print("[lab] PASS")
		quit(0)
	else:
		printerr("[lab] FAIL (%d)" % failed)
		quit(1)


func _test_basic_movement() -> int:
	var world := ProbeWorldState.new()
	world.width = 5
	world.height = 5
	world.start_x = 1
	world.start_y = 1
	world.start_dir = ProbeWorldState.DIR_E
	world.reset_to_start()
	var program := ProbeProgram.new()
	program.append_op(ProbeOpcodes.FORWARD)
	program.append_op(ProbeOpcodes.TURN_LEFT)
	program.append_op(ProbeOpcodes.FORWARD)
	var interp := ProbeInterpreter.new()
	interp.setup(world, program, false)
	var result := interp.run_all_sync()
	if world.probe_x != 2 or world.probe_y != 0:
		printerr("[lab] FAIL movement pos (%d,%d)" % [world.probe_x, world.probe_y])
		return 1
	if world.probe_dir != ProbeWorldState.DIR_N:
		printerr("[lab] FAIL movement dir %d" % world.probe_dir)
		return 1
	print("[lab] movimiento/giro OK (steps=%d)" % int(result.get("steps", 0)))
	return 0


func _test_reset() -> int:
	var world := ProbeWorldState.new()
	world.width = 4
	world.height = 4
	world.start_x = 0
	world.start_y = 0
	world.start_dir = ProbeWorldState.DIR_S
	world.poi_cells = [Vector2i(0, 0)]
	world.reset_to_start()
	var program := ProbeProgram.new()
	program.append_op(ProbeOpcodes.FORWARD)
	program.append_op(ProbeOpcodes.SCAN)
	var interp := ProbeInterpreter.new()
	interp.setup(world, program, false)
	interp.run_all_sync()
	interp.reset_execution()
	if world.probe_x != 0 or world.probe_y != 0 or world.probe_dir != ProbeWorldState.DIR_S:
		printerr("[lab] FAIL reset pose")
		return 1
	if not world.scanned_pois.is_empty() or world.has_transmitted:
		printerr("[lab] FAIL reset sensors")
		return 1
	print("[lab] reset OK")
	return 0


func _test_invalid_program() -> int:
	var world := ProbeWorldState.new()
	world.width = 3
	world.height = 3
	world.reset_to_start()
	var program := ProbeProgram.new()
	var bad := program.append_op("EXPLOTAR_TODO")
	if bad.is_empty():
		printerr("[lab] FAIL debió rechazar opcode ilegal")
		return 1
	var interp := ProbeInterpreter.new()
	interp.setup(world, program, false)
	var err := interp.start()
	if err.is_empty():
		printerr("[lab] FAIL start con programa vacío debió fallar")
		return 1
	print("[lab] mensajes inválidos OK (%s)" % err)
	return 0


func _test_scan_without_poi() -> int:
	var world := ProbeWorldState.new()
	world.width = 3
	world.height = 3
	world.start_x = 1
	world.start_y = 1
	world.poi_cells = [Vector2i(2, 2)]
	world.reset_to_start()
	var program := ProbeProgram.new()
	program.append_op(ProbeOpcodes.SCAN)
	var interp := ProbeInterpreter.new()
	interp.setup(world, program, false)
	var result := interp.run_all_sync()
	if bool(result.get("victory", false)):
		printerr("[lab] FAIL escaneo vacío no es victoria")
		return 1
	if str(result.get("message", "")).findn("escanear") < 0:
		printerr("[lab] FAIL mensaje poco claro: %s" % result.get("message", ""))
		return 1
	print("[lab] error de escaneo OK")
	return 0


func _test_challenge_victory() -> int:
	var def := ChallengeDef.load_from_path("res://assets/data/lab/challenge_scan_transmit.json")
	if def == null:
		printerr("[lab] FAIL load challenge")
		return 1
	var world := def.build_world()
	var program := ProbeProgram.new()
	for op in [
		ProbeOpcodes.FORWARD,
		ProbeOpcodes.FORWARD,
		ProbeOpcodes.SCAN,
		ProbeOpcodes.TURN_RIGHT,
		ProbeOpcodes.FORWARD,
		ProbeOpcodes.FORWARD,
		ProbeOpcodes.TRANSMIT,
	]:
		program.append_op(op)
	var interp := ProbeInterpreter.new()
	interp.setup(world, program, false)
	var result := interp.run_all_sync()
	if not bool(result.get("victory", false)):
		printerr("[lab] FAIL victoria reto: %s snap=%s" % [result.get("message"), result.get("snapshot")])
		return 1
	if world.probe_x != 3 or world.probe_y != 4:
		printerr("[lab] FAIL posición final")
		return 1
	print("[lab] victoria reto básico OK")
	return 0


func _test_challenge_incomplete() -> int:
	var def := ChallengeDef.load_from_path("res://assets/data/lab/challenge_scan_transmit.json")
	var world := def.build_world()
	var program := ProbeProgram.new()
	program.append_op(ProbeOpcodes.FORWARD)
	program.append_op(ProbeOpcodes.FORWARD)
	program.append_op(ProbeOpcodes.SCAN)
	var interp := ProbeInterpreter.new()
	interp.setup(world, program, false)
	var result := interp.run_all_sync()
	if bool(result.get("victory", false)):
		printerr("[lab] FAIL no debía ganar sin transmitir")
		return 1
	if not world.all_pois_scanned():
		printerr("[lab] FAIL debía haber escaneado")
		return 1
	if world.has_transmitted:
		printerr("[lab] FAIL no debía transmitir")
		return 1
	print("[lab] estado parcial (escaneado, no transmitido) OK")
	return 0


func _test_loop_victory() -> int:
	var def := ChallengeDef.load_from_path("res://assets/data/lab/challenge_loop_corridor.json")
	var world := def.build_world()
	var program := ProbeProgram.new()
	program.append_op(ProbeOpcodes.REPEAT_BEGIN, 4)
	program.append_op(ProbeOpcodes.FORWARD)
	program.append_op(ProbeOpcodes.REPEAT_END)
	program.append_op(ProbeOpcodes.SCAN)
	program.append_op(ProbeOpcodes.TURN_RIGHT)
	program.append_op(ProbeOpcodes.FORWARD)
	program.append_op(ProbeOpcodes.FORWARD)
	program.append_op(ProbeOpcodes.TRANSMIT)
	var interp := ProbeInterpreter.new()
	interp.setup(world, program, true)
	var result := interp.run_all_sync()
	if not bool(result.get("victory", false)):
		printerr("[lab] FAIL victoria bucle: %s" % result.get("message"))
		return 1
	print("[lab] victoria reto bucles OK")
	return 0


func _test_scene_loads() -> int:
	var packed := load("res://scenes/lab/probe_lab.tscn") as PackedScene
	if packed == null:
		printerr("[lab] FAIL scene missing")
		return 1
	var root := packed.instantiate()
	get_root().add_child(root)
	await process_frame
	await process_frame
	if root.get_node_or_null("%ProgramList") == null:
		printerr("[lab] FAIL UI nodes")
		root.queue_free()
		return 1
	root.queue_free()
	await process_frame
	print("[lab] escena OK")
	return 0
