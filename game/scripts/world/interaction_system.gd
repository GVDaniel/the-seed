class_name InteractionSystem
extends Node
## Busca el interactuable más cercano al jugador, muestra el texto y lo activa con E.

@export var player_path: NodePath

var enabled: bool = true
var _player: Node2D
var _focus: Interactable
var _last_prompt: String = "-"


func _ready() -> void:
	_player = get_node_or_null(player_path) as Node2D


func get_focus() -> Interactable:
	return _focus


func _physics_process(_delta: float) -> void:
	if _player == null:
		return
	_focus = _find_nearest() if enabled else null
	var text := ""
	if _focus != null:
		text = "E — %s" % _focus.prompt
	if text != _last_prompt:
		_last_prompt = text
		App.bus().interaction_prompt_changed.emit(text)
	if enabled and _focus != null and Input.is_action_just_pressed("interact"):
		_focus.interact()


func _find_nearest() -> Interactable:
	var best: Interactable = null
	var best_d := INF
	for node in get_tree().get_nodes_in_group(Interactable.GROUP):
		var it := node as Interactable
		if it == null or not it.visible or not it.is_in_range(_player):
			continue
		var d := it.global_position.distance_to(_player.global_position)
		if d < best_d:
			best_d = d
			best = it
	return best
