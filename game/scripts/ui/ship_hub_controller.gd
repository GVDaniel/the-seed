extends Control
## Hub de la nave: placeholder de exploración y lecciones.

@onready var _info: Label = %InfoLabel


func _ready() -> void:
	_info.text = (
		"Bienvenido a bordo, %s.\n"
		+ "Desde aquí partirán misiones de astronomía y retos de código.\n"
		+ "(Demo mínima — contenido en construcción.)"
	) % GameState.player_name


func _on_demo_lesson_pressed() -> void:
	# Marca una lección demo para validar el flujo de progreso.
	GameState.mark_lesson_completed("demo_sol_overview", 1)
	_info.text = "Lección demo completada. Estrellas: %d" % GameState.stars_earned


func _on_back_pressed() -> void:
	get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")
