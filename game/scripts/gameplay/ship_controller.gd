class_name ShipController
extends CharacterBody2D
## Solo física de pilotaje. No conoce cámara ni HUD.

signal telemetry_updated(speed: float, energy: float, ship_name: String)
signal land_requested

@export var stats: ShipStats
@export var consume_input: bool = true

var energy: float = 100.0
var _axis: ControlAxis = ControlAxis.new()
var _desktop: DesktopInputReader = DesktopInputReader.new()


func _ready() -> void:
	if stats == null:
		stats = ShipStats.new()
	energy = stats.max_energy
	add_to_group("player_ship")
	_emit_telemetry()


func get_control_axis() -> ControlAxis:
	return _axis


func get_speed() -> float:
	return velocity.length()


func _physics_process(delta: float) -> void:
	if not consume_input:
		return
	_desktop.read_ship(_axis)
	if _axis.land_pressed:
		land_requested.emit()
	_apply_steering(delta)
	_update_energy(delta)
	move_and_slide()
	_emit_telemetry()
	_axis.clear_pulses()


func _apply_steering(delta: float) -> void:
	rotation += _axis.turn * stats.turn_speed * delta

	var forward := Vector2.UP.rotated(rotation)
	if _axis.thrust > 0.0 and energy > 0.0:
		velocity += forward * stats.acceleration * _axis.thrust * delta
	elif _axis.thrust < 0.0:
		velocity += forward * stats.acceleration * _axis.thrust * 0.45 * delta

	var speed := velocity.length()
	if speed > stats.max_speed:
		velocity = velocity.normalized() * stats.max_speed

	if is_zero_approx(_axis.thrust) or energy <= 0.0:
		var damp := exp(-stats.deceleration * delta)
		velocity *= damp
		if velocity.length() < 4.0:
			velocity = Vector2.ZERO


func _update_energy(delta: float) -> void:
	if _axis.thrust > 0.0 and energy > 0.0:
		energy = maxf(0.0, energy - stats.thrust_energy_cost * _axis.thrust * delta)
	else:
		energy = minf(stats.max_energy, energy + stats.energy_regen * delta)


func _emit_telemetry() -> void:
	telemetry_updated.emit(get_speed(), energy, stats.ship_name)
