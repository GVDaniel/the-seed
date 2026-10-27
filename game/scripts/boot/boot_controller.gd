extends Control
## Arranque: carga mínima y pasa al menú principal.

@onready var _status: Label = %StatusLabel


func _ready() -> void:
	_status.text = "Inicializando The Seed…"
	await get_tree().create_timer(0.35).timeout
	_status.text = "Listo"
	get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")
