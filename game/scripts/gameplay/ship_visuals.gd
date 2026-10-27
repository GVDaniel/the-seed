class_name ShipVisuals
extends Node2D
## Sprite de ASTRA + llama del motor según el empuje. Sin física.

@export var ship_path: NodePath = ^".."

var _ship: ShipController
var _flame: Sprite2D
var _t: float = 0.0


func _ready() -> void:
	_ship = get_node_or_null(ship_path) as ShipController
	_flame = get_node_or_null("Flame") as Sprite2D


func _process(delta: float) -> void:
	if _ship == null or _flame == null:
		return
	var thrust := _ship.get_control_axis().thrust
	_flame.visible = thrust > 0.05 and _ship.energy > 0.0
	if _flame.visible:
		_t += delta
		_flame.frame = int(_t * 14.0) % 3
