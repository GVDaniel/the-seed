class_name ScanPoint
extends Node2D
## Punto científico en superficie. Compatible con ScannerSystem (F).

@export var destination_id: String = ""
@export var scan_radius: float = 34.0

var _marker: Sprite2D
var _t: float = 0.0


func _ready() -> void:
	add_to_group(ScannerSystem.TARGET_GROUP)
	add_to_group(Interactable.NAV_GROUP)
	_marker = Sprite2D.new()
	_marker.texture = _make_marker()
	_marker.position = Vector2(0, -30)
	add_child(_marker)


func get_stable_id() -> String:
	return destination_id


func get_nav_id() -> String:
	return destination_id


func get_scan_radius() -> float:
	return scan_radius


func is_in_scan_range(actor: Node2D) -> bool:
	return actor != null and global_position.distance_to(actor.global_position) <= scan_radius


func _process(delta: float) -> void:
	_t += delta
	_marker.position.y = -30.0 + sin(_t * 3.0) * 2.0
	var known: bool = App.notebook().is_discovered(destination_id)
	_marker.modulate = Color(0.55, 0.72, 0.85, 0.6) if known else Color(0.957, 0.827, 0.369, 1.0)


static func _make_marker() -> Texture2D:
	var img := Image.create(7, 7, false, Image.FORMAT_RGBA8)
	var c := Color(1, 1, 1)
	for i in 7:
		img.set_pixel(3, i, c)
		img.set_pixel(i, 3, c)
	img.set_pixel(3, 3, Color(0.24, 0.91, 0.79))
	return ImageTexture.create_from_image(img)
