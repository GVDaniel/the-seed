class_name Interactable
extends Node2D
## Algo con lo que el jugador puede interactuar (E). Solo emite al EventBus.

const GROUP := "interactables"
const NAV_GROUP := "nav_targets"

@export var target_id: String = ""
## npc | item | terminal | ship | object
@export var kind: String = "object"
@export var prompt: String = "Interactuar"
@export var radius: float = 26.0
## Datos extra (p. ej. challenge_id de una terminal).
@export var payload: String = ""


func _ready() -> void:
	add_to_group(GROUP)
	add_to_group(NAV_GROUP)


func get_nav_id() -> String:
	return target_id


func is_in_range(actor: Node2D) -> bool:
	return actor != null and global_position.distance_to(actor.global_position) <= radius


func interact() -> void:
	App.bus().interaction_requested.emit(target_id, kind)
