class_name AmbientMover
extends Node2D
## Vehículo, máquina o nave de ambiente que recorre un camino (píxeles del mundo).
## mode: "flow" (de punta a punta y desaparece), "pingpong" (ida y vuelta) o "cycle" (en bucle).
## Con altitude > 0 vuela: el dibujo se eleva y deja sombra en el suelo. Desde HIGH_FLY se pinta por
## encima de todo; más bajo (aerotaxis por la calzada) se ordena por profundidad con los personajes.
## No tiene colisión ni interacción.

signal finished

const FLOW := "flow"
const PINGPONG := "pingpong"
const CYCLE := "cycle"
## z de lo que vuela (por encima de personajes) y de la sombra (sobre el suelo, bajo personajes).
const AIR_Z := 20
const SHADOW_Z := -5
const HIGH_FLY := 24.0

var kind: String = ""
var path: PackedVector2Array = PackedVector2Array()
var speed: float = 40.0
var altitude: float = 0.0
var mode: String = FLOW
var pause_range: Vector2 = Vector2.ZERO
var air_z: int = AIR_Z

var _sprite: Sprite2D
var _shadow: Polygon2D
var _rows: Dictionary = {}
var _frames: int = 1
var _fps: float = 6.0
var _anim_t: float = 0.0
var _seg: int = 0
var _dir: int = 1
var _wait: float = 0.0
var _row: int = 0


## def = AmbientKinds.get_def(kind). progress = 0..1 del camino donde empieza (para poblar al cargar).
func setup(def: Dictionary, points: PackedVector2Array, move_speed: float, alt: float, move_mode: String,
		pause: Vector2 = Vector2.ZERO, progress: float = 0.0) -> void:
	path = points
	if move_mode == CYCLE and path.size() > 2 and path[0] != path[-1]:
		path.append(path[0])
	speed = maxf(1.0, move_speed)
	altitude = alt
	mode = move_mode
	pause_range = pause
	var tex: Texture2D = def["texture"]
	var frame: Array = def.get("frame", [tex.get_width(), tex.get_height()])
	var fsize := Vector2(float(frame[0]), float(frame[1]))
	_frames = maxi(1, int(def.get("frames", 1)))
	_fps = float(def.get("fps", 6.0))
	_rows = def.get("rows", {"right": 0})
	var nrows := 1
	for r in _rows.values():
		nrows = maxi(nrows, int(r) + 1)
	_sprite = Sprite2D.new()
	_sprite.texture = tex
	_sprite.hframes = _frames
	_sprite.vframes = maxi(1, mini(nrows, int(round(tex.get_height() / fsize.y))))
	_sprite.offset = Vector2(0, -fsize.y * 0.5 - altitude)
	add_child(_sprite)
	var shadow_size: Array = def.get("shadow", [])
	if altitude > 0.0 or not shadow_size.is_empty():
		var sw := float(shadow_size[0]) if shadow_size.size() >= 2 else fsize.x * 0.7
		var sh := float(shadow_size[1]) if shadow_size.size() >= 2 else 5.0
		_shadow = _ellipse(sw, sh, 0.28 if altitude < 60.0 else 0.12)
		_shadow.z_as_relative = false
		_shadow.z_index = SHADOW_Z
		add_child(_shadow)
	if flies_high():
		z_as_relative = false
		z_index = air_z
	var light: Variant = def.get("light", null)
	if light is Dictionary:
		var l := NeonLight.from_data(light)
		l.position.y -= altitude
		add_child(l)
	_anim_t = randf() * 2.0
	_place_at(progress)
	_update_facing()


static func _ellipse(w: float, h: float, alpha: float) -> Polygon2D:
	var p := Polygon2D.new()
	var pts := PackedVector2Array()
	for i in 14:
		var a := TAU * i / 14.0
		pts.append(Vector2(cos(a) * w * 0.5, sin(a) * h * 0.5))
	p.polygon = pts
	p.color = Color(0, 0, 0, alpha)
	return p


func flies_high() -> bool:
	return altitude >= HIGH_FLY


func _place_at(progress: float) -> void:
	position = path[0] if not path.is_empty() else Vector2.ZERO
	if path.size() < 2 or progress <= 0.0:
		return
	var total := length()
	var target := total * clampf(progress, 0.0, 1.0)
	for i in path.size() - 1:
		var seg_len := path[i].distance_to(path[i + 1])
		if target <= seg_len:
			_seg = i
			position = path[i].lerp(path[i + 1], target / maxf(seg_len, 0.001))
			return
		target -= seg_len
	_seg = path.size() - 2
	position = path[-1]


func length() -> float:
	var total := 0.0
	for i in path.size() - 1:
		total += path[i].distance_to(path[i + 1])
	return total


func _process(delta: float) -> void:
	if _frames > 1:
		_anim_t += delta
		_sprite.frame = _row * _frames + int(_anim_t * _fps) % _frames
	if path.size() < 2:
		return
	if _wait > 0.0:
		_wait -= delta
		return
	var step := speed * delta
	while step > 0.0:
		var goal := _goal()
		var to_goal := goal - position
		var d := to_goal.length()
		if d > step:
			position += to_goal / d * step
			break
		position = goal
		step -= d
		if not _advance():
			return
		_update_facing()
		if pause_range.y > 0.0 and mode != FLOW:
			_wait = randf_range(pause_range.x, pause_range.y)
			break


func _goal() -> Vector2:
	return path[_seg + 1] if _dir > 0 else path[_seg]


## Pasa al siguiente tramo. Devuelve false si el recorrido terminó (y el nodo se va).
func _advance() -> bool:
	if _dir > 0:
		if _seg + 1 < path.size() - 1:
			_seg += 1
			return true
	elif _seg > 0:
		_seg -= 1
		return true
	match mode:
		PINGPONG:
			_dir = -_dir
		CYCLE:
			_seg = 0
			position = path[0]
		_:
			finished.emit()
			queue_free()
			return false
	return true


func _update_facing() -> void:
	if path.size() < 2:
		return
	var d := _goal() - position
	if d.length_squared() < 0.01:
		return
	if absf(d.x) >= absf(d.y) or (not _rows.has("down") and not _rows.has("up")):
		_row = int(_rows.get("right", 0))
		if absf(d.x) > 0.01:
			_sprite.flip_h = d.x < 0.0
	else:
		var key := "down" if d.y > 0.0 else "up"
		_row = int(_rows.get(key, _rows.get("right", 0)))
		_sprite.flip_h = false
	_sprite.frame = _row * _frames + (_sprite.frame % _frames)
