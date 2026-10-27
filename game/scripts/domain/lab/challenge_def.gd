class_name ChallengeDef
extends RefCounted
## Datos de un reto del laboratorio (JSON).

var id: String = ""
var title: String = ""
var briefing: String = ""
var concepts_text: String = ""
var allow_loops: bool = false
var allow_conditions: bool = false
## 0 = sin límite. Un límite bajo obliga a usar bucles.
var max_blocks: int = 0
var hint: String = ""
## Estética de la cuadrícula: lab, earth, moon, mars.
var theme: String = "lab"
var samples: Array[Vector2i] = []
var goal_scan: bool = true
var goal_transmit: bool = true
var goal_collect: bool = false
var width: int = 5
var height: int = 5
var start: Vector2i = Vector2i.ZERO
var start_dir: int = ProbeWorldState.DIR_E
var pois: Array[Vector2i] = []
var transmit: Vector2i = Vector2i.ZERO
var blocked: Array[Vector2i] = []
var available_ops: PackedStringArray = PackedStringArray()


static func from_dict(data: Dictionary) -> ChallengeDef:
	var def := ChallengeDef.new()
	def.id = str(data.get("id", ""))
	def.title = str(data.get("title", ""))
	def.briefing = str(data.get("briefing", ""))
	def.concepts_text = str(data.get("concepts_text", ""))
	def.allow_loops = bool(data.get("allow_loops", false))
	def.allow_conditions = bool(data.get("allow_conditions", false))
	def.max_blocks = int(data.get("max_blocks", 0))
	def.hint = str(data.get("hint", ""))
	def.theme = str(data.get("theme", "lab"))
	for item in data.get("samples", []):
		def.samples.append(_vec(item))
	var goal: Dictionary = data.get("goal", {})
	def.goal_scan = bool(goal.get("scan", true))
	def.goal_transmit = bool(goal.get("transmit", true))
	def.goal_collect = bool(goal.get("collect", false))
	def.width = int(data.get("width", 5))
	def.height = int(data.get("height", 5))
	def.start = _vec(data.get("start", [0, 0]))
	def.start_dir = _dir(str(data.get("start_dir", "E")))
	def.transmit = _vec(data.get("transmit", [0, 0]))
	for item in data.get("pois", []):
		def.pois.append(_vec(item))
	for item in data.get("blocked", []):
		def.blocked.append(_vec(item))
	var ops: Array = data.get("available_ops", [])
	if ops.is_empty():
		def.available_ops = ProbeOpcodes.basic_set()
	else:
		for op in ops:
			def.available_ops.append(str(op))
	return def


static func load_from_path(path: String) -> ChallengeDef:
	var raw := FileAccess.get_file_as_string(path)
	var parsed: Variant = JSON.parse_string(raw)
	if typeof(parsed) != TYPE_DICTIONARY:
		return null
	return from_dict(parsed)


func build_world() -> ProbeWorldState:
	var world := ProbeWorldState.new()
	world.width = width
	world.height = height
	world.start_x = start.x
	world.start_y = start.y
	world.start_dir = start_dir
	world.poi_cells = pois.duplicate()
	world.transmit_cell = transmit
	world.blocked = blocked.duplicate()
	world.sample_cells = samples.duplicate()
	world.goal_scan = goal_scan
	world.goal_transmit = goal_transmit
	world.goal_collect = goal_collect
	world.reset_to_start()
	return world


static func _vec(value: Variant) -> Vector2i:
	if typeof(value) == TYPE_ARRAY and value.size() >= 2:
		return Vector2i(int(value[0]), int(value[1]))
	if typeof(value) == TYPE_DICTIONARY:
		return Vector2i(int(value.get("x", 0)), int(value.get("y", 0)))
	return Vector2i.ZERO


static func _dir(name: String) -> int:
	match name.to_upper():
		"N", "NORTH", "UP":
			return ProbeWorldState.DIR_N
		"E", "EAST", "RIGHT":
			return ProbeWorldState.DIR_E
		"S", "SOUTH", "DOWN":
			return ProbeWorldState.DIR_S
		"W", "WEST", "LEFT":
			return ProbeWorldState.DIR_W
	return ProbeWorldState.DIR_E
