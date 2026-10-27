class_name ShipController
extends CharacterBody2D
## Solo física de pilotaje. No conoce cámara ni HUD.
## Con un fuel_source (ShipState) el empuje gasta combustible; con el tanque vacío
## quedan los propulsores de reserva: menos aceleración y velocidad punta, nunca cero.

signal telemetry_updated(speed: float, energy: float, ship_name: String)
signal land_requested

@export var stats: ShipStats
@export var consume_input: bool = true

## Objeto con burn(throttle, delta) e is_empty(). null = combustible infinito (tests, prototipo).
var fuel_source: Object = null
const RESERVE_ACCEL := 0.3
const RESERVE_SPEED := 0.5

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


func is_on_reserve() -> bool:
	return fuel_source != null and bool(fuel_source.call("is_empty"))


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
	var reserve := is_on_reserve()
	var accel := stats.acceleration * (RESERVE_ACCEL if reserve else 1.0)
	var top := stats.max_speed * (RESERVE_SPEED if reserve else 1.0)
	if _axis.thrust > 0.0 and energy > 0.0:
		velocity += forward * accel * _axis.thrust * delta
		if fuel_source != null:
			fuel_source.call("burn", _axis.thrust, delta)
	elif _axis.thrust < 0.0:
		velocity += forward * accel * _axis.thrust * 0.45 * delta

	var speed := velocity.length()
	if speed > top:
		# Al quedarse sin combustible la nave frena poco a poco hasta la velocidad de reserva.
		var step := 260.0 * delta if reserve else speed - top
		velocity = velocity.move_toward(velocity.normalized() * top, step)

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
