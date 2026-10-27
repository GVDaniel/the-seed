class_name NavAlias
extends Node2D
## Alias de navegación: permite que la flecha encuentre un nodo por otro id (p. ej. "vega" → Estación Aurora).

var nav_id: String = ""


static func attach(host: Node2D, id: String) -> void:
	if id.is_empty():
		return
	var alias := NavAlias.new()
	alias.nav_id = id
	host.add_child(alias)


func _ready() -> void:
	add_to_group(Interactable.NAV_GROUP)


func get_nav_id() -> String:
	return nav_id
