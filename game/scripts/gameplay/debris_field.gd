class_name DebrisField
extends Node2D
## Anillo de basura espacial alrededor de un planeta. Al chocar: rebote y −energía.

const TEXTURE := "res://assets/art/planets/debris.png"
const HIT_RADIUS := 22.0
const HIT_ENERGY := 12.0
const HIT_COOLDOWN := 1.0

@export var ship_path: NodePath
@export var inner_radius: float = 560.0
@export var outer_radius: float = 680.0
@export var count: int = 26
@export var orbit_speed: float = 0.05

var _ship: ShipController
var _pieces: Array[Sprite2D] = []
var _angles: PackedFloat32Array = PackedFloat32Array()
var _radii: PackedFloat32Array = PackedFloat32Array()
var _spins: PackedFloat32Array = PackedFloat32Array()
var _cooldown: float = 0.0


func _ready() -> void:
	_ship = get_node_or_null(ship_path) as ShipController
	var tex: Texture2D = load(TEXTURE)
	var rng := RandomNumberGenerator.new()
	rng.seed = 2187
	for i in count:
		var s := Sprite2D.new()
		s.texture = tex
		s.hframes = 3
		s.frame = i % 3
		s.scale = Vector2(3, 3)
		add_child(s)
		_pieces.append(s)
		_angles.append(rng.randf() * TAU)
		_radii.append(rng.randf_range(inner_radius, outer_radius))
		_spins.append(rng.randf_range(-1.5, 1.5))


func _physics_process(delta: float) -> void:
	_cooldown = maxf(0.0, _cooldown - delta)
	for i in _pieces.size():
		_angles[i] += orbit_speed * delta * (inner_radius / _radii[i])
		var p := _pieces[i]
		p.position = Vector2(cos(_angles[i]), sin(_angles[i])) * _radii[i]
		p.rotation += _spins[i] * delta
		if _ship != null and _ship.visible and _cooldown <= 0.0:
			if p.global_position.distance_to(_ship.global_position) < HIT_RADIUS:
				_hit(p.global_position)


func _hit(at: Vector2) -> void:
	_cooldown = HIT_COOLDOWN
	var away := (_ship.global_position - at).normalized()
	_ship.velocity = away * maxf(160.0, _ship.velocity.length() * 0.6)
	var damage := HIT_ENERGY * ShipUpgrades.multiplier("debris_damage")
	_ship.energy = maxf(0.0, _ship.energy - damage)
	App.sfx().play("bump")
	var first: bool = App.notebook().record_discovery("space_debris")
	var msg := "¡Choque con basura espacial! −%d de energía." % int(damage)
	if first:
		msg += " Nueva ficha en el cuaderno."
	App.bus().mission_status_message.emit(msg)
