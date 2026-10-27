class_name DesktopInputReader
extends RefCounted
## Lee InputMap de escritorio y rellena un ControlAxis.
## El HUD táctil futuro puede escribir el mismo ControlAxis sin tocar el movimiento.

const ACTION_THRUST := "ship_thrust"
const ACTION_BRAKE := "ship_brake"
const ACTION_TURN_LEFT := "ship_turn_left"
const ACTION_TURN_RIGHT := "ship_turn_right"
const ACTION_LAND := "interact_land"
const ACTION_TAKEOFF := "interact_takeoff"
const ACTION_MOVE_LEFT := "walk_left"
const ACTION_MOVE_RIGHT := "walk_right"
const ACTION_MOVE_UP := "walk_up"
const ACTION_MOVE_DOWN := "walk_down"


func read_ship(axis: ControlAxis) -> void:
	var thrust := 0.0
	if Input.is_action_pressed(ACTION_THRUST):
		thrust += 1.0
	if Input.is_action_pressed(ACTION_BRAKE):
		thrust -= 0.55
	axis.thrust = clampf(thrust, -1.0, 1.0)

	var turn := 0.0
	if Input.is_action_pressed(ACTION_TURN_LEFT):
		turn -= 1.0
	if Input.is_action_pressed(ACTION_TURN_RIGHT):
		turn += 1.0
	axis.turn = clampf(turn, -1.0, 1.0)

	axis.land_pressed = Input.is_action_just_pressed(ACTION_LAND)


func read_walker(axis: ControlAxis) -> void:
	axis.move = Input.get_vector(
		ACTION_MOVE_LEFT,
		ACTION_MOVE_RIGHT,
		ACTION_MOVE_UP,
		ACTION_MOVE_DOWN
	)
	axis.takeoff_pressed = Input.is_action_just_pressed(ACTION_TAKEOFF)
