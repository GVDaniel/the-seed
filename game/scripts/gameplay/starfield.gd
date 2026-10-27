class_name Starfield
extends Node2D
## Campo de estrellas con wrap alrededor de la cámara (sin partículas).

@export var star_count: int = 180
@export var field_size: Vector2 = Vector2(2400, 1500)
@export var star_color: Color = Color(0.85, 0.92, 1.0, 0.85)
@export_range(0.0, 1.0, 0.01) var parallax: float = 0.4

var _offsets: PackedVector2Array = PackedVector2Array()
var _sizes: PackedFloat32Array = PackedFloat32Array()
var _colors: PackedColorArray = PackedColorArray()
var _camera: Camera2D


func _ready() -> void:
	_generate()


func bind_camera(camera: Camera2D) -> void:
	_camera = camera


func _generate() -> void:
	_offsets.resize(star_count)
	_sizes.resize(star_count)
	_colors.resize(star_count)
	var rng := RandomNumberGenerator.new()
	rng.seed = 47
	for i in star_count:
		_offsets[i] = Vector2(
			rng.randf_range(0.0, field_size.x),
			rng.randf_range(0.0, field_size.y)
		)
		_sizes[i] = [1.0, 2.0, 2.0, 3.0][rng.randi() % 4]
		var tint := [star_color, Color(1.0, 0.85, 0.6, 0.9), Color(0.6, 0.8, 1.0, 0.9), Color(0.957, 0.827, 0.369, 0.8)]
		_colors[i] = tint[rng.randi() % tint.size()]


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	var cam := _camera
	if cam == null and get_viewport() != null:
		cam = get_viewport().get_camera_2d()
	if cam == null:
		return

	var origin := cam.get_screen_center_position() * parallax
	var half := field_size * 0.5
	for i in _offsets.size():
		var x := fposmod(_offsets[i].x - origin.x, field_size.x) - half.x + origin.x
		var y := fposmod(_offsets[i].y - origin.y, field_size.y) - half.y + origin.y
		var p := to_local(Vector2(x, y)).floor()
		draw_rect(Rect2(p, Vector2(_sizes[i], _sizes[i])), _colors[i])
