class_name ObjectiveArrow
extends Node2D
## Flecha que orbita al portador y apunta al objetivo actual (nav_targets).

@export var orbit_radius: float = 30.0
@export var hide_distance: float = 60.0
@export var arrow_scale: float = 1.0

var _candidates: PackedStringArray = PackedStringArray()


func _ready() -> void:
	z_index = 20
	App.bus().nav_target_changed.connect(_on_target_changed)
	_on_target_changed("")


func _on_target_changed(_target_id: String) -> void:
	_candidates = App.story().nav_candidates()


func _process(_delta: float) -> void:
	var holder := get_parent() as Node2D
	var target := _find_target()
	if holder == null or target == null:
		visible = false
		return
	var to_target := target.global_position - holder.global_position
	if to_target.length() < hide_distance:
		visible = false
		return
	visible = true
	global_rotation = 0.0
	global_position = holder.global_position + to_target.normalized() * orbit_radius
	queue_redraw()
	set_meta("angle", to_target.angle())


func _draw() -> void:
	var a: float = get_meta("angle", 0.0)
	var s := 7.0 * arrow_scale
	var tip := Vector2.RIGHT.rotated(a) * s
	var l := Vector2(-s * 0.7, -s * 0.7).rotated(a)
	var r := Vector2(-s * 0.7, s * 0.7).rotated(a)
	draw_colored_polygon(PackedVector2Array([tip, l, Vector2.RIGHT.rotated(a) * (-s * 0.2), r]), Color(0.957, 0.827, 0.369, 0.95))


func _find_target() -> Node2D:
	var nodes := get_tree().get_nodes_in_group(Interactable.NAV_GROUP)
	for id in _candidates:
		for node in nodes:
			if node.has_method("get_nav_id") and str(node.call("get_nav_id")) == id:
				return node as Node2D
	return null
