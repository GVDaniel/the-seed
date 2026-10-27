class_name CharacterSprite
extends Sprite2D
## Hoja 3×4 (quieto, paso A, paso B) × (abajo, izquierda, derecha, arriba).

const FRAME_SIZE := Vector2i(16, 24)
const ROW := {"down": 0, "left": 1, "right": 2, "up": 3}
const STEP_TIME := 0.14

var facing: String = "down"
var _moving: bool = false
var _timer: float = 0.0
var _step: int = 0


func _ready() -> void:
	hframes = 3
	vframes = 4
	centered = true
	offset = Vector2(0, -FRAME_SIZE.y * 0.5 + 2)
	_apply()


func set_sheet(path: String) -> void:
	if ResourceLoader.exists(path):
		texture = load(path)
	_apply()


func face_vector(dir: Vector2) -> void:
	if dir.length_squared() < 0.01:
		return
	if absf(dir.x) > absf(dir.y):
		facing = "right" if dir.x > 0.0 else "left"
	else:
		facing = "down" if dir.y > 0.0 else "up"
	_apply()


func set_facing(dir_name: String) -> void:
	if ROW.has(dir_name):
		facing = dir_name
		_apply()


func update_motion(velocity: Vector2, delta: float) -> bool:
	var moving := velocity.length() > 12.0
	var stepped := false
	if moving:
		face_vector(velocity)
		_timer += delta
		if _timer >= STEP_TIME:
			_timer = 0.0
			_step = (_step + 1) % 4
			stepped = _step % 2 == 1
	else:
		_step = 0
		_timer = 0.0
	_moving = moving
	_apply()
	return stepped


func _apply() -> void:
	if texture == null:
		return
	var col := 0
	if _moving:
		col = [1, 0, 2, 0][_step]
	frame = int(ROW.get(facing, 0)) * 3 + col
