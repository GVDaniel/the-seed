class_name ScannableDestination
extends Area2D
## Destino espacial interactivo con id estable. Solo mundo + proximidad.

const GROUP_NAME := "scannable_destinations"

@export var destination_id: String = ""
@export var body_radius: float = 90.0
@export var scan_radius: float = 220.0
@export var body_color: Color = Color(0.55, 0.62, 0.75, 1.0)
@export var ring_color: Color = Color(0.24, 0.91, 0.79, 0.22)
@export var label_override: String = ""
## Sprite pixel art; con hframes > 1 se anima en bucle.
@export var texture: Texture2D
@export var hframes: int = 1
@export var sprite_scale: int = 2
@export var spin_speed: float = 0.0
## Personaje con quien se habla aquí (T). Vacío = nadie.
@export var npc_id: String = ""

@onready var _body: Polygon2D = %BodyVisual
@onready var _ring: Polygon2D = %RingVisual
@onready var _label: Label = %DestLabel
@onready var _scan_shape: CollisionShape2D = %ScanShape


var _sprite: Sprite2D
var _anim_t: float = 0.0


func _ready() -> void:
	add_to_group(GROUP_NAME)
	add_to_group(ScannerSystem.TARGET_GROUP)
	add_to_group(Interactable.NAV_GROUP)
	monitoring = true
	monitorable = false
	_apply_visuals()
	_apply_label()
	_configure_scan_shape()
	NavAlias.attach(self, npc_id)
	set_process(_sprite != null and (hframes > 1 or not is_zero_approx(spin_speed)))


func get_nav_id() -> String:
	return destination_id


func _process(delta: float) -> void:
	_anim_t += delta
	_sprite.frame = int(_anim_t * 2.0) % hframes
	_sprite.rotation += delta * spin_speed


func get_stable_id() -> String:
	return destination_id


func get_scan_radius() -> float:
	return scan_radius


func is_in_scan_range(ship: Node2D) -> bool:
	if ship == null:
		return false
	return global_position.distance_to(ship.global_position) <= scan_radius


func _apply_label() -> void:
	if not label_override.is_empty():
		_label.text = label_override
	else:
		var entry: DestinationEntry = App.notebook().get_catalog().get_entry(destination_id)
		_label.text = entry.display_name if entry != null else destination_id
	_label.position = Vector2(-_label.size.x * 0.5, -body_radius - 40.0)


func _configure_scan_shape() -> void:
	var circle := CircleShape2D.new()
	circle.radius = scan_radius
	_scan_shape.shape = circle


func _apply_visuals() -> void:
	_ring.polygon = _ring_poly(scan_radius * 0.96, scan_radius, 56)
	_ring.color = ring_color
	if texture != null:
		_body.visible = false
		_sprite = Sprite2D.new()
		_sprite.texture = texture
		_sprite.hframes = maxi(1, hframes)
		_sprite.scale = Vector2(sprite_scale, sprite_scale)
		add_child(_sprite)
		return
	_body.polygon = _circle_poly(body_radius, 40)
	_body.color = body_color


func _circle_poly(radius: float, points: int) -> PackedVector2Array:
	var poly := PackedVector2Array()
	for i in points:
		var a := TAU * float(i) / float(points)
		poly.append(Vector2(cos(a), sin(a)) * radius)
	return poly


func _ring_poly(inner_r: float, outer_r: float, points: int) -> PackedVector2Array:
	var poly := PackedVector2Array()
	for i in points + 1:
		var a := TAU * float(i) / float(points)
		poly.append(Vector2(cos(a), sin(a)) * outer_r)
	for i in range(points, -1, -1):
		var a := TAU * float(i) / float(points)
		poly.append(Vector2(cos(a), sin(a)) * inner_r)
	return poly
