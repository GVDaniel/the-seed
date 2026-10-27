class_name AmbientLife
extends Node2D
## Vida de fondo de un mapa: tráfico y máquinas («movers»), naves que
## cruzan el cielo («sky») y peatones («crowd»). Todo decorativo: sin colisión ni interacción.
## Coordenadas del JSON en tiles, como "pos" de las entidades.
## Los datos van en la clave "ambient_life" del mapa ("ambient" es el color de la luz ambiente: ver
## tint_of). Los caminos pueden salirse del mapa (x = -3, W + 3) para entrar y salir por los bordes.

const MAX_LIVE := 40
const SKY_Z := 40

var _ground_parent: Node2D
var _player: Node2D
var _map_px: Vector2 = Vector2.ZERO
var _lanes: Array[Dictionary] = []
var _sky: Dictionary = {}
var _sky_timer: float = 0.0
var _live: int = 0


## ground_parent: nodo con y-sort donde van los que andan a ras de suelo (junto a los personajes).
func setup(map: Dictionary, ground_parent: Node2D, player: Node2D, map_size_px: Vector2) -> void:
	_ground_parent = ground_parent
	_player = player
	_map_px = map_size_px
	var data := data_of(map)
	if data.is_empty():
		return
	var planet := planet_of(map)
	for row in data.get("movers", []):
		if typeof(row) == TYPE_DICTIONARY:
			_add_mover_row(row)
	var sky: Variant = data.get("sky", {})
	if sky is Dictionary and not (sky as Dictionary).is_empty():
		var kinds := AmbientKinds.available(sky.get("kinds", []))
		if not kinds.is_empty():
			_sky = sky.duplicate()
			_sky["kinds"] = kinds
			# La primera nave llega pronto (antes del intervalo mínimo).
			_sky_timer = randf_range(0.0, _range(_sky.get("interval", [8, 18]), Vector2(8, 18)).x)
	for row in data.get("crowd", []):
		if typeof(row) == TYPE_DICTIONARY:
			_add_crowd_row(row, planet)


static func data_of(map: Dictionary) -> Dictionary:
	for key in ["ambient_life", "life", "ambient"]:
		var v: Variant = map.get(key, null)
		if v is Dictionary:
			return v
	return {}


## Color de la luz ambiente del mapa ("ambient" si es texto, si no "ambient_color" o ambient.color).
static func tint_of(map: Dictionary) -> String:
	var v: Variant = map.get("ambient", null)
	if v is String:
		return v
	if v is Dictionary and (v as Dictionary).has("color"):
		return str(v["color"])
	return str(map.get("ambient_color", "#ffffff"))


static func planet_of(map: Dictionary) -> String:
	var p := str(map.get("region", map.get("tileset", "earth")))
	if p.begins_with("city_"):
		p = p.substr(5)
	return p if p in ["earth", "moon", "mars"] else "earth"


func live_count() -> int:
	return _live


func _points(raw: Array, offset: Vector2 = Vector2.ZERO) -> PackedVector2Array:
	var out := PackedVector2Array()
	for p in raw:
		if p is Array and (p as Array).size() >= 2:
			out.append(SurfaceEntitySpawner.tile_to_world(p) + offset)
	return out


func _range(v: Variant, fallback: Vector2) -> Vector2:
	if v is Array and (v as Array).size() >= 2:
		return Vector2(float(v[0]), float(v[1]))
	if v is float or v is int:
		return Vector2(float(v), float(v))
	return fallback


func _add_mover_row(row: Dictionary) -> void:
	var kinds := AmbientKinds.available(row.get("kinds", []))
	var path := _points(row.get("path", []))
	if kinds.is_empty() or path.size() < 2:
		return
	var speed := _range(row.get("speed", 40.0), Vector2(40, 40))
	var altitude := float(row.get("altitude", 0.0))
	if row.has("count"):
		var mode := str(row.get("loop", AmbientMover.PINGPONG))
		var pause := _range(row.get("pause", [0.0, 0.0]), Vector2.ZERO)
		for i in int(row["count"]):
			_spawn_mover(kinds[randi() % kinds.size()], path, randf_range(speed.x, speed.y), altitude, mode,
				pause, randf())
		return
	var lane := {"kinds": kinds, "paths": [path], "speed": speed, "altitude": altitude,
		"interval": _range(row.get("interval", [3.0, 6.0]), Vector2(3, 6))}
	if bool(row.get("two_way", false)):
		var dir := (path[1] - path[0]).normalized()
		var off := Vector2(-dir.y, dir.x) * float(row.get("lane_offset", 0.6)) * TileCatalog.TILE
		var back := PackedVector2Array()
		for i in range(path.size() - 1, -1, -1):
			back.append(path[i] + off)
		lane["paths"].append(back)
	lane["timers"] = []
	for p in lane["paths"]:
		lane["timers"].append(randf_range(0.0, lane["interval"].y))
		_prepopulate(lane, p)
	_lanes.append(lane)


## Al cargar el mapa, el tráfico ya está en marcha (no empieza vacío).
func _prepopulate(lane: Dictionary, path: PackedVector2Array) -> void:
	var length := 0.0
	for i in path.size() - 1:
		length += path[i].distance_to(path[i + 1])
	var spd: Vector2 = lane["speed"]
	var iv: Vector2 = lane["interval"]
	var avg_gap := (spd.x + spd.y) * 0.5 * (iv.x + iv.y) * 0.5
	var n := clampi(int(length / maxf(avg_gap, 1.0)), 0, 4)
	for i in n:
		var kinds: PackedStringArray = lane["kinds"]
		_spawn_mover(kinds[randi() % kinds.size()], path, randf_range(spd.x, spd.y), lane["altitude"],
			AmbientMover.FLOW, Vector2.ZERO, (i + randf()) / float(n + 1))


func _add_crowd_row(row: Dictionary, planet: String) -> void:
	var sheets := AmbientKinds.crowd_sheets(planet)
	var path := _points(row.get("path", []))
	if sheets.is_empty() or path.is_empty():
		return
	var speed := _range(row.get("speed", [16.0, 26.0]), Vector2(16, 26))
	var pause := _range(row.get("pause", [0.5, 4.0]), Vector2(0.5, 4.0))
	var barks := PackedStringArray(row.get("barks", []))
	for i in int(row.get("count", 1)):
		if _live >= MAX_LIVE:
			return
		var w := AmbientWalker.new()
		w.name = "Walker%d" % _live
		w.setup(sheets[randi() % sheets.size()], path, randf_range(speed.x, speed.y), pause, barks, _player)
		w.tree_exited.connect(_on_gone)
		_ground_parent.add_child(w)
		_live += 1


func _spawn_mover(kind: String, path: PackedVector2Array, speed: float, altitude: float, mode: String,
		pause: Vector2 = Vector2.ZERO, progress: float = 0.0, z: int = AmbientMover.AIR_Z) -> AmbientMover:
	if _live >= MAX_LIVE:
		return null
	var def := AmbientKinds.get_def(kind)
	if def.is_empty():
		return null
	var m := AmbientMover.new()
	m.kind = kind
	m.air_z = z
	m.setup(def, path, speed, altitude, mode, pause, progress)
	m.tree_exited.connect(_on_gone)
	if m.flies_high():
		add_child(m)
	else:
		_ground_parent.add_child(m)
	_live += 1
	return m


func _on_gone() -> void:
	_live = maxi(0, _live - 1)


func _process(delta: float) -> void:
	for lane in _lanes:
		var timers: Array = lane["timers"]
		for i in timers.size():
			timers[i] = float(timers[i]) - delta
			if float(timers[i]) > 0.0:
				continue
			var iv: Vector2 = lane["interval"]
			timers[i] = randf_range(iv.x, iv.y)
			var kinds: PackedStringArray = lane["kinds"]
			var spd: Vector2 = lane["speed"]
			_spawn_mover(kinds[randi() % kinds.size()], lane["paths"][i], randf_range(spd.x, spd.y),
				lane["altitude"], AmbientMover.FLOW)
	if not _sky.is_empty():
		_sky_timer -= delta
		if _sky_timer <= 0.0:
			var iv := _range(_sky.get("interval", [8, 18]), Vector2(8, 18))
			_sky_timer = randf_range(iv.x, iv.y)
			_launch_sky()


## Nave cruzando el mapa de lado a lado, por encima de todo y algo transparente.
func _launch_sky() -> void:
	var kinds: PackedStringArray = _sky["kinds"]
	var kind := kinds[randi() % kinds.size()]
	var rows := _range(_sky.get("rows", [2, 20]), Vector2(2, 20))
	var y := (randf_range(rows.x, rows.y) + 1.0) * TileCatalog.TILE
	var margin := 200.0
	var path := PackedVector2Array([Vector2(-margin, y), Vector2(_map_px.x + margin, y)])
	if randf() < 0.5:
		path.reverse()
	var spd := _range(_sky.get("speed", [18, 35]), Vector2(18, 35))
	var m := _spawn_mover(kind, path, randf_range(spd.x, spd.y), 70.0, AmbientMover.FLOW, Vector2.ZERO, 0.0, SKY_Z)
	if m != null:
		m.modulate = Color(1, 1, 1, 0.85)
