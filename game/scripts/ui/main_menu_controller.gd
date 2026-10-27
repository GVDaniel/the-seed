extends Control
## Menú principal: continuar, nueva aventura, laboratorio libre.

@onready var _stars: Label = %StarsLabel
@onready var _api_status: Label = %ApiStatusLabel
@onready var _continue_btn: Button = %ContinueButton
@onready var _start_btn: Button = %StartButton
@onready var _confirm: ConfirmationDialog = %ConfirmNew


func _ready() -> void:
	App.music().play("title")
	_refresh_stars()
	EventBus.progress_changed.connect(_on_progress_changed)
	EventBus.api_error.connect(_on_api_error)
	_confirm.confirmed.connect(_start_new_game)
	var has_save: bool = GameState.has_save()
	_continue_btn.visible = has_save
	(_continue_btn if has_save else _start_btn).grab_focus.call_deferred()
	ApiClient.health_check()


func _refresh_stars() -> void:
	_stars.text = "%s · XP %d · Estrellas %d" % [GameState.rank_name(), GameState.experience, GameState.stars_earned]


func _on_progress_changed(_progress: Dictionary) -> void:
	_refresh_stars()


func _on_api_error(message: String) -> void:
	_api_status.text = "API: offline (%s) — el juego sigue sin conexión" % message


func _on_continue_pressed() -> void:
	App.sfx().play("confirm")
	App.router().go_location(str(GameState.location), "ship")


func _on_start_pressed() -> void:
	if GameState.has_save():
		_confirm.popup_centered()
		return
	_start_new_game()


func _start_new_game() -> void:
	App.sfx().play("confirm")
	App.story().new_game()
	App.router().play_cutscene("intro", "earth")


func _on_lab_pressed() -> void:
	App.router().open_free_lab("menu")


func _on_quit_pressed() -> void:
	get_tree().quit()
