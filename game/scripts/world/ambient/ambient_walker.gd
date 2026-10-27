class_name AmbientWalker
extends Node2D
## Peatón de ambiente: anda de un punto a otro de su camino (ida y vuelta), se para, mira alrededor
## y, si el jugador pasa cerca, a veces dice algo en un bocadillo. Sin colisión ni interacción (E).

const BARK_DISTANCE := 30.0
const BARK_TIME := 2.8
const BARK_COOLDOWN := 9.0
const BARK_CHANCE := 0.45
## Entre todos los peatones: como mucho un bocadillo cada tantos segundos.
const GLOBAL_COOLDOWN := 3.0

static var _last_bark_ms: int = -100000

var path: PackedVector2Array = PackedVector2Array()
var speed: float = 20.0
var pause_range: Vector2 = Vector2(0.5, 3.0)
var barks: PackedStringArray = PackedStringArray()
var player: Node2D

var _sprite: CharacterSprite
var _bubble: Label
var _bubble_t: float = 0.0
var _cooldown: float = 0.0
var _was_near: bool = false
var _target: int = 1
var _dir: int = 1
var _wait: float = 0.0


func setup(sheet: Texture2D, points: PackedVector2Array, walk_speed: float, pause: Vector2,
		lines: PackedStringArray, player_node: Node2D) -> void:
	path = points
	speed = walk_speed
	pause_range = pause
	barks = lines
	player = player_node
	_sprite = CharacterSprite.new()
	_sprite.texture = sheet
	add_child(_sprite)
	var shadow := Polygon2D.new()
	shadow.color = Color(0, 0, 0, 0.22)
	shadow.polygon = PackedVector2Array([Vector2(-5, 0), Vector2(5, 0), Vector2(4, 2), Vector2(-4, 2)])
	shadow.show_behind_parent = true
	add_child(shadow)
	# Empieza en un punto al azar del camino, mirando hacia donde va.
	if path.size() >= 2:
		var i := randi_range(0, path.size() - 2)
		position = path[i].lerp(path[i + 1], randf())
		_target = i + 1
		_dir = 1
		if randf() < 0.5:
			_target = i
			_dir = -1
	elif not path.is_empty():
		position = path[0]
	_wait = randf_range(0.0, pause_range.y)
	_cooldown = randf_range(0.0, BARK_COOLDOWN)


func _process(delta: float) -> void:
	_update_bubble(delta)
	if path.size() < 2:
		_sprite.update_motion(Vector2.ZERO, delta)
		return
	if _wait > 0.0:
		_wait -= delta
		_sprite.update_motion(Vector2.ZERO, delta)
		return
	var goal := path[_target]
	var to_goal := goal - position
	var d := to_goal.length()
	var step := speed * delta
	if d <= step:
		position = goal
		_next_target()
		_sprite.update_motion(Vector2.ZERO, delta)
		if randf() < 0.6:
			_wait = randf_range(pause_range.x, pause_range.y)
			if randf() < 0.5:
				_sprite.set_facing(["down", "left", "right", "up"][randi() % 4])
		return
	var v := to_goal / d * speed
	position += v * delta
	_sprite.update_motion(v, delta)


func _next_target() -> void:
	var nt := _target + _dir
	if nt < 0 or nt >= path.size():
		_dir = -_dir
		nt = _target + _dir
	_target = clampi(nt, 0, path.size() - 1)


func _update_bubble(delta: float) -> void:
	_cooldown = maxf(0.0, _cooldown - delta)
	if _bubble != null:
		_bubble_t -= delta
		if _bubble_t <= 0.0:
			_bubble.queue_free()
			_bubble = null
	if barks.is_empty() or player == null or not is_instance_valid(player):
		return
	var near := global_position.distance_to(player.global_position) < BARK_DISTANCE
	if near and not _was_near and _cooldown <= 0.0 and _bubble == null:
		var since := Time.get_ticks_msec() - _last_bark_ms
		if since > GLOBAL_COOLDOWN * 1000.0 and randf() < BARK_CHANCE:
			say(barks[randi() % barks.size()])
	_was_near = near


func say(text: String) -> void:
	_last_bark_ms = Time.get_ticks_msec()
	_cooldown = BARK_COOLDOWN
	if _bubble != null:
		_bubble.queue_free()
	_bubble = Label.new()
	_bubble.text = text
	_bubble.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_bubble.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_bubble.add_theme_font_size_override("font_size", 16)
	_bubble.add_theme_color_override("font_color", Color("e8f1ff"))
	var box := StyleBoxFlat.new()
	box.bg_color = Color(0.03, 0.06, 0.11, 0.88)
	box.border_color = Color("3de7c9")
	box.set_border_width_all(1)
	box.set_corner_radius_all(3)
	box.content_margin_left = 6
	box.content_margin_right = 6
	box.content_margin_top = 2
	box.content_margin_bottom = 2
	_bubble.add_theme_stylebox_override("normal", box)
	# El texto se dibuja a escala 1/3 para verse nítido con la cámara a ×3.
	_bubble.scale = Vector2(1.0 / 3.0, 1.0 / 3.0)
	_bubble.custom_minimum_size = Vector2(minf(320.0, 18.0 + text.length() * 8.0), 0)
	_bubble.z_as_relative = false
	_bubble.z_index = 60
	add_child(_bubble)
	_bubble.size = _bubble.get_combined_minimum_size()
	_bubble.position = Vector2(-_bubble.size.x / 6.0, -30.0 - _bubble.size.y / 3.0)
	_bubble_t = BARK_TIME


func is_saying() -> bool:
	return _bubble != null
