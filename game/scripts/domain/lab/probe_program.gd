class_name ProbeProgram
extends RefCounted
## Lista de órdenes validadas. Solo opcodes conocidos; sin código arbitrario.

signal changed

var _ops: PackedStringArray = PackedStringArray()
## Veces de cada REPETIR alineado por índice de op (0 si no aplica).
var _repeat_times: PackedInt32Array = PackedInt32Array()


func clear() -> void:
	_ops.clear()
	_repeat_times.clear()
	changed.emit()


func size() -> int:
	return _ops.size()


func get_op(index: int) -> String:
	if index < 0 or index >= _ops.size():
		return ""
	return _ops[index]


func get_repeat_times(index: int) -> int:
	if index < 0 or index >= _repeat_times.size():
		return 0
	return _repeat_times[index]


func as_array() -> PackedStringArray:
	return _ops.duplicate()


func append_op(op: String, repeat_times: int = 0) -> String:
	if not ProbeOpcodes.is_known(op):
		return "Instrucción no permitida: %s" % op
	if op == ProbeOpcodes.REPEAT_BEGIN:
		var times := clampi(repeat_times, 2, 6)
		_ops.append(op)
		_repeat_times.append(times)
		changed.emit()
		return ""
	_ops.append(op)
	_repeat_times.append(0)
	changed.emit()
	return ""


func remove_at(index: int) -> void:
	if index < 0 or index >= _ops.size():
		return
	_ops.remove_at(index)
	_repeat_times.remove_at(index)
	changed.emit()


func move_up(index: int) -> void:
	if index <= 0 or index >= _ops.size():
		return
	_swap(index, index - 1)
	changed.emit()


func move_down(index: int) -> void:
	if index < 0 or index >= _ops.size() - 1:
		return
	_swap(index, index + 1)
	changed.emit()


func _swap(a: int, b: int) -> void:
	var op_a := _ops[a]
	_ops[a] = _ops[b]
	_ops[b] = op_a
	var t_a := _repeat_times[a]
	_repeat_times[a] = _repeat_times[b]
	_repeat_times[b] = t_a


## Profundidad de anidamiento de cada instrucción (para sangría en la UI).
func depth_at(index: int) -> int:
	var depth := 0
	for i in mini(index + 1, _ops.size()):
		var op := _ops[i]
		if ProbeOpcodes.is_block_close(op):
			depth -= 1
		if i == index:
			return maxi(depth, 0)
		if ProbeOpcodes.is_block_open(op):
			depth += 1
	return 0


## Valida estructura (bloques REPETIR/SI bien cerrados) sin ejecutar.
func validate_structure(allow_loops: bool, allow_conditions: bool = false) -> String:
	if _ops.is_empty():
		return "Añade al menos una instrucción."
	var stack: Array[String] = []
	for i in _ops.size():
		var op := _ops[i]
		if not allow_loops and ProbeOpcodes.loop_set().has(op):
			return "Este reto no permite bucles todavía. Usa solo una secuencia."
		if not allow_conditions and ProbeOpcodes.condition_set().has(op):
			return "Este reto no permite condiciones todavía."
		if not ProbeOpcodes.is_known(op):
			return "Instrucción desconocida en la posición %d." % (i + 1)
		if op == ProbeOpcodes.REPEAT_BEGIN and _repeat_times[i] < 2:
			return "REPETIR necesita un número ≥ 2."
		if ProbeOpcodes.is_block_open(op):
			stack.append(op)
		elif ProbeOpcodes.is_block_close(op):
			if stack.is_empty():
				return "Hay un %s sin su bloque de inicio (posición %d)." % [op, i + 1]
			var opener: String = stack.pop_back()
			if ProbeOpcodes.closer_for(opener) != op:
				return "El bloque %s debe cerrarse con %s antes de %s." % [
					ProbeOpcodes.display_name(opener), ProbeOpcodes.closer_for(opener), op
				]
	if not stack.is_empty():
		var open_op: String = stack.back()
		return "Falta cerrar %s con %s." % [ProbeOpcodes.display_name(open_op), ProbeOpcodes.closer_for(open_op)]
	return ""
