class_name ShipStats
extends Resource
## Parámetros de pilotaje arcade. Editar el .tres en el inspector, no el código.

@export var ship_name: String = "ASTRA"
@export_range(50.0, 2000.0, 1.0) var acceleration: float = 520.0
@export_range(50.0, 2000.0, 1.0) var max_speed: float = 420.0
@export_range(0.0, 20.0, 0.05) var turn_speed: float = 3.2
@export_range(0.0, 20.0, 0.05) var deceleration: float = 1.8
@export_range(1.0, 500.0, 1.0) var max_energy: float = 100.0
@export_range(0.0, 50.0, 0.1) var thrust_energy_cost: float = 4.0
@export_range(0.0, 50.0, 0.1) var energy_regen: float = 6.0
