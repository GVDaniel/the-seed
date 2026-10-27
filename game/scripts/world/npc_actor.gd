class_name NpcActor
extends Interactable
## Personaje del mundo: mira al jugador cuando está cerca. Si tiene wander_radius,
## pasea despacio alrededor de su sitio (sin física: el mapa deja ese espacio libre).

const WALK_SPEED := 22.0

@export var sheet_path: String = ""
@export var default_facing: String = "down"
## Radio de paseo en píxeles (0 = se queda quieto).
@export var wander_radius: float = 0.0

var _sprite: CharacterSprite
var _player: Node2D
var _home: Vector2
var _goal: Vector2
var _pause: float = 0.0


func _ready() -> void:
	super._ready()
	kind = "npc"
	_sprite = CharacterSprite.new()
	add_child(_sprite)
	_sprite.set_sheet(sheet_path)
	_sprite.set_facing(default_facing)
	var shadow := Polygon2D.new()
	shadow.color = Color(0, 0, 0, 0.25)
	shadow.polygon = PackedVector2Array([Vector2(-6, 0), Vector2(6, 0), Vector2(5, 2), Vector2(-5, 2)])
	shadow.show_behind_parent = true
	add_child(shadow)
	_home = position
	_goal = position
	_pause = randf_range(0.5, 2.5)


func set_player(player: Node2D) -> void:
	_player = player


func _process(delta: float) -> void:
	var near := false
	if _player != null:
		var to_player := _player.global_position - global_position
		near = to_player.length() < radius * 2.2
		if near:
			_sprite.update_motion(Vector2.ZERO, delta)
			_sprite.face_vector(to_player)
			return
	if wander_radius > 0.0:
		_wander(delta)
	elif _player != null:
		_sprite.set_facing(default_facing)


func _wander(delta: float) -> void:
	if _pause > 0.0:
		_pause -= delta
		_sprite.update_motion(Vector2.ZERO, delta)
		return
	var to_goal := _goal - position
	if to_goal.length() < 2.0:
		_pause = randf_range(1.5, 4.0)
		var axis := Vector2.RIGHT if randf() < 0.5 else Vector2.DOWN
		_goal = _home + axis * randf_range(-wander_radius, wander_radius)
		return
	var step := to_goal.normalized() * WALK_SPEED
	position += step * delta
	_sprite.update_motion(step, delta)
