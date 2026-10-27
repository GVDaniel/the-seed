class_name WalkerStats
extends Resource
## Movimiento a pie en superficie planetaria.

@export var display_name: String = "Cadete"
@export_range(50.0, 800.0, 1.0) var acceleration: float = 900.0
@export_range(50.0, 600.0, 1.0) var max_speed: float = 180.0
@export_range(0.0, 30.0, 0.1) var friction: float = 12.0
