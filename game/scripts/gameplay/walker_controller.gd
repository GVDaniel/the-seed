class_name WalkerController
extends CharacterBody2D
## Movimiento a pie en el planeta. Independiente de la nave.

signal moved(speed: float)
signal takeoff_requested

@export var stats: WalkerStats
@export var consume_input: bool = true

@export var start_active: bool = false
@export var sheet_path: String = "res://assets/art/characters/andres.png"

var _axis: ControlAxis = ControlAxis.new()
var _desktop: DesktopInputReader = DesktopInputReader.new()
var _avatar: CharacterSprite


func _ready() -> void:
	if stats == null:
		stats = WalkerStats.new()
	add_to_group("player_walker")
	_avatar = get_node_or_null("Avatar") as CharacterSprite
	if _avatar != null:
		_avatar.set_sheet(sheet_path)
	if start_active:
		activate_at(global_position)
	else:
		visible = false
		set_physics_process(false)


func face(dir_name: String) -> void:
	if _avatar != null:
		_avatar.set_facing(dir_name)


func get_control_axis() -> ControlAxis:
	return _axis


func activate_at(global_pos: Vector2) -> void:
	global_position = global_pos
	velocity = Vector2.ZERO
	visible = true
	set_physics_process(true)
	consume_input = true


func deactivate() -> void:
	visible = false
	velocity = Vector2.ZERO
	set_physics_process(false)
	consume_input = false


func _physics_process(delta: float) -> void:
	if not consume_input:
		velocity = Vector2.ZERO
		if _avatar != null:
			_avatar.update_motion(velocity, delta)
		return
	_desktop.read_walker(_axis)
	if _axis.takeoff_pressed:
		takeoff_requested.emit()
	var wish := _axis.move
	if wish.length_squared() > 0.0:
		velocity = velocity.move_toward(wish.normalized() * stats.max_speed, stats.acceleration * delta)
	else:
		velocity = velocity.move_toward(Vector2.ZERO, stats.friction * stats.max_speed * delta)
	move_and_slide()
	if _avatar != null and _avatar.update_motion(velocity, delta):
		App.sfx().play("step", randf_range(0.9, 1.1))
	moved.emit(velocity.length())
	_axis.clear_pulses()
