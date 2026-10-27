class_name ProbeInterpreter
extends RefCounted
## Intérprete propio de opcodes. Sin eval, sin FS, sin código del jugador.

signal step_executed(index: int, op: String, message: String)
signal finished(success: bool, message: String)
signal failed(message: String)

var world: ProbeWorldState
var program: ProbeProgram
var allow_loops: bool = false
var allow_conditions: bool = false
## 0 = sin límite de bloques.
var max_blocks: int = 0

var _ip: int = 0
## Índice al que saltar tras la instrucción actual (SI falso), o -1.
var _jump_to: int = -1
var _running: bool = false
var _loop_stack: Array[Dictionary] = [] # {start, end, remaining}


func setup(
	p_world: ProbeWorldState,
	p_program: ProbeProgram,
	p_allow_loops: bool = false,
	p_allow_conditions: bool = false,
	p_max_blocks: int = 0
) -> void:
	world = p_world
	program = p_program
	allow_loops = p_allow_loops
	allow_conditions = p_allow_conditions
	max_blocks = p_max_blocks
	reset_execution()


func reset_execution() -> void:
	_ip = 0
	_jump_to = -1
	_running = false
	_loop_stack.clear()
	if world != null:
		world.reset_to_start()


func is_running() -> bool:
	return _running


func stop() -> void:
	_running = false


func start() -> String:
	if world == null or program == null:
		return "Laboratorio no inicializado."
	var err := program.validate_structure(allow_loops, allow_conditions)
	if not err.is_empty():
		return err
	if max_blocks > 0 and program.size() > max_blocks:
		return "Usaste %d bloques y el máximo es %d. Pista: un bucle ahorra bloques." % [program.size(), max_blocks]
	world.reset_to_start()
	_ip = 0
	_jump_to = -1
	_loop_stack.clear()
	_running = true
	return ""


## Ejecuta una instrucción. Devuelve mensaje de error o "".
func step() -> String:
	if not _running:
		return "La ejecución está detenida."
	if _ip >= program.size():
		_running = false
		if world.is_victory():
			finished.emit(true, _victory_message())
		else:
			var why := _failure_reason()
			finished.emit(false, why)
			failed.emit(why)
		return ""

	var op := program.get_op(_ip)
	var msg := _exec_op(op, _ip)
	if not msg.is_empty() and msg.begins_with("ERROR:"):
		_running = false
		var clean := msg.trim_prefix("ERROR:").strip_edges()
		failed.emit(clean)
		finished.emit(false, clean)
		return clean

	step_executed.emit(_ip, op, msg)
	if _jump_to >= 0:
		_ip = _jump_to
		_jump_to = -1
	_advance_ip()
	if _ip >= program.size() and _running:
		_running = false
		if world.is_victory():
			finished.emit(true, _victory_message())
		else:
			var why2 := _failure_reason()
			finished.emit(false, why2)
			failed.emit(why2)
	return ""


func run_all_sync(max_steps: int = 256) -> Dictionary:
	var start_err := start()
	if not start_err.is_empty():
		return {"ok": false, "message": start_err, "victory": false, "steps": 0}
	var steps := 0
	while _running and steps < max_steps:
		var err := step()
		steps += 1
		if not err.is_empty():
			return {
				"ok": false,
				"message": err,
				"victory": false,
				"steps": steps,
				"snapshot": world.to_snapshot(),
			}
	if _running:
		stop()
		return {
			"ok": false,
			"message": "El programa es demasiado largo o hay un bucle infinito.",
			"victory": false,
			"steps": steps,
			"snapshot": world.to_snapshot(),
		}
	return {
		"ok": world.is_victory(),
		"message": "OK" if world.is_victory() else _failure_reason(),
		"victory": world.is_victory(),
		"steps": steps,
		"snapshot": world.to_snapshot(),
	}


func _advance_ip() -> void:
	# Si estamos en un bucle, el IP lo gestiona _exec_op al encontrar FIN / salto
	_ip += 1
	# Tras incrementar, comprobar si hay que saltar al inicio del bucle
	while not _loop_stack.is_empty():
		var top: Dictionary = _loop_stack[_loop_stack.size() - 1]
		if _ip > int(top["end"]):
			var remaining: int = int(top["remaining"]) - 1
			if remaining > 0:
				top["remaining"] = remaining
				_loop_stack[_loop_stack.size() - 1] = top
				_ip = int(top["start"]) + 1
			else:
				_loop_stack.pop_back()
		else:
			break


func _exec_op(op: String, index: int) -> String:
	match op:
		ProbeOpcodes.FORWARD:
			return _do_forward()
		ProbeOpcodes.TURN_LEFT:
			world.probe_dir = (world.probe_dir + 3) % 4
			return "Gira a la izquierda."
		ProbeOpcodes.TURN_RIGHT:
			world.probe_dir = (world.probe_dir + 1) % 4
			return "Gira a la derecha."
		ProbeOpcodes.SCAN:
			return _do_scan()
		ProbeOpcodes.TRANSMIT:
			return _do_transmit()
		ProbeOpcodes.REPEAT_BEGIN:
			return _do_repeat_begin(index)
		ProbeOpcodes.REPEAT_END:
			return "Fin del bloque a repetir."
		ProbeOpcodes.COLLECT:
			return _do_collect()
		ProbeOpcodes.IF_SAMPLE:
			return _do_if_sample(index)
		ProbeOpcodes.IF_END:
			return "Fin de la condición."
		_:
			return "ERROR: Opcode no soportado."


func _do_forward() -> String:
	var delta := world.dir_vector()
	var nx := world.probe_x + delta.x
	var ny := world.probe_y + delta.y
	if not world.in_bounds(nx, ny):
		return "ERROR: No puedes avanzar: saldrías de la cuadrícula."
	if world.is_blocked(nx, ny):
		return "ERROR: No puedes avanzar: hay un obstáculo."
	world.probe_x = nx
	world.probe_y = ny
	return "Avanza a (%d, %d)." % [nx, ny]


func _do_scan() -> String:
	if world.is_poi(world.probe_x, world.probe_y):
		world.scanned_pois[world.poi_key(world.probe_x, world.probe_y)] = true
		world.last_scan_ok = true
		return "Escaneo correcto: punto de interés registrado."
	world.last_scan_ok = false
	return "ERROR: Aquí no hay nada que escanear. Muévete al punto de interés."


func _do_collect() -> String:
	if world.has_sample(world.probe_x, world.probe_y):
		world.collected_samples[world.poi_key(world.probe_x, world.probe_y)] = true
		return "Muestra recogida."
	return "ERROR: Aquí no hay muestra que recoger. Pista: usa SI hay muestra."


func _do_if_sample(index: int) -> String:
	if not allow_conditions:
		return "ERROR: Las condiciones no están habilitadas en este reto."
	var end_idx := _find_matching(index, ProbeOpcodes.IF_SAMPLE, ProbeOpcodes.IF_END)
	if end_idx < 0:
		return "ERROR: SI sin FIN_SI."
	if world.has_sample(world.probe_x, world.probe_y):
		return "¿Hay muestra? SÍ → entra en el bloque."
	_jump_to = end_idx
	return "¿Hay muestra? NO → salta el bloque."


func _do_transmit() -> String:
	if world.transmit_cell.x < 0:
		return "ERROR: Este reto no tiene zona de transmisión."
	if world.probe_x != world.transmit_cell.x or world.probe_y != world.transmit_cell.y:
		world.last_transmit_ok = false
		return "ERROR: Debes estar en la antena de transmisión para enviar datos."
	if world.goal_scan and not world.all_pois_scanned():
		world.last_transmit_ok = false
		return "ERROR: Aún no has escaneado todos los puntos de interés."
	if world.goal_collect and not world.all_samples_collected():
		world.last_transmit_ok = false
		return "ERROR: Aún faltan muestras por recoger."
	world.has_transmitted = true
	world.last_transmit_ok = true
	return "Transmisión enviada a la estación."


func _do_repeat_begin(index: int) -> String:
	if not allow_loops:
		return "ERROR: Los bucles no están habilitados en este reto."
	var end_idx := _find_matching(index, ProbeOpcodes.REPEAT_BEGIN, ProbeOpcodes.REPEAT_END)
	if end_idx < 0:
		return "ERROR: REPETIR sin FIN_REPETIR."
	var times := program.get_repeat_times(index)
	_loop_stack.append({"start": index, "end": end_idx, "remaining": times})
	return "Empieza un bucle ×%d." % times


func _find_matching(begin_idx: int, open_op: String, close_op: String) -> int:
	var depth := 0
	for i in range(begin_idx, program.size()):
		var op := program.get_op(i)
		if op == open_op:
			depth += 1
		elif op == close_op:
			depth -= 1
			if depth == 0:
				return i
	return -1


func _victory_message() -> String:
	if world.goal_collect:
		return "¡Reto superado! Recogiste todas las muestras y enviaste los datos."
	return "¡Reto superado! Escaneaste y transmitiste los datos."


func _failure_reason() -> String:
	var missing := PackedStringArray()
	if world.goal_scan and not world.all_pois_scanned():
		missing.append("escanear")
	if world.goal_collect and not world.all_samples_collected():
		missing.append("recoger todas las muestras")
	if world.goal_transmit and not world.has_transmitted:
		missing.append("transmitir")
	if missing.size() == 2 and missing.has("escanear") and missing.has("transmitir"):
		return "Programa terminado, pero faltó escanear y transmitir."
	if missing.size() == 1 and missing[0] == "escanear":
		return "Programa terminado, pero no escaneaste el punto de interés."
	if missing.size() == 1 and missing[0] == "transmitir":
		return "Programa terminado, pero no transmitiste desde la antena."
	if not missing.is_empty():
		return "Programa terminado, pero faltó: %s." % ", ".join(missing)
	return "Programa terminado sin cumplir el objetivo."
