class_name FollowCamera
extends Camera2D
## Sigue un Node2D con suavizado. Sin lógica de juego.

@export var target: Node2D
@export_range(0.5, 30.0, 0.1) var follow_speed: float = 8.0
@export var snap_on_retarget: bool = true


func _ready() -> void:
	make_current()


func set_follow_target(new_target: Node2D, snap: bool = true) -> void:
	target = new_target
	if target != null and (snap or snap_on_retarget):
		global_position = target.global_position


func _physics_process(delta: float) -> void:
	if target == null:
		return
	global_position = global_position.lerp(target.global_position, 1.0 - exp(-follow_speed * delta))
