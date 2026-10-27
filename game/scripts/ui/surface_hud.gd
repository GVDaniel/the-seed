class_name SurfaceHud
extends CanvasLayer
## HUD a pie: lugar, nivel/salud/XP, objetivo, texto de interacción y avisos.

@onready var _location: Label = %LocationLabel
@onready var _rank: Label = %RankLabel
@onready var _prompt: Label = %PromptLabel
@onready var _prompt_box: Control = %PromptBox
@onready var _toast: Label = %ToastLabel
@onready var _toast_box: Control = %ToastBox
@onready var _help: Label = %HelpLabel

var _toast_timer: float = 0.0
var _scan_text: String = ""
var _interact_text: String = ""


func _ready() -> void:
	var bus := App.bus()
	bus.interaction_prompt_changed.connect(_on_prompt)
	bus.mission_status_message.connect(show_toast)
	bus.experience_changed.connect(func(_xp: int) -> void: _refresh_rank())
	bus.credits_changed.connect(func(_c: int) -> void: _refresh_rank())
	bus.hero_changed.connect(_refresh_rank)
	bus.scan_focus_changed.connect(_on_scan_focus)
	_prompt_box.visible = false
	_toast_box.visible = false
	(%HalButton as Button).pressed.connect(func() -> void: bus.hal_interface_requested.emit(""))
	_refresh_rank()


func set_location_name(text: String) -> void:
	_location.text = text


func set_help(text: String) -> void:
	_help.text = text


func _refresh_rank() -> void:
	var gs := App.game_state()
	var hero := App.hero()
	var points := "  ·  ¡%d punto(s) de mejora!" % int(hero.unspent) if int(hero.unspent) > 0 else ""
	_rank.text = "Andrés Nv %d · Salud %d/%d · XP %d · %d créditos%s" % [int(hero.level()), int(hero.hp),
		int(hero.max_hp()), int(gs.experience), int(gs.credits), points]


func _on_prompt(text: String) -> void:
	_interact_text = text
	_update_prompt()


func _on_scan_focus(_id: String, display_name: String) -> void:
	_scan_text = "" if display_name.is_empty() else "F — Escanear %s" % display_name
	_update_prompt()


func _update_prompt() -> void:
	var parts := PackedStringArray()
	if not _interact_text.is_empty():
		parts.append(_interact_text)
	if not _scan_text.is_empty():
		parts.append(_scan_text)
	_prompt.text = "    ".join(parts)
	_prompt_box.visible = not parts.is_empty()


func show_toast(text: String) -> void:
	_toast.text = text
	_toast_box.visible = true
	_toast_timer = 4.0


func _process(delta: float) -> void:
	if _toast_timer > 0.0:
		_toast_timer -= delta
		if _toast_timer <= 0.0:
			_toast_box.visible = false
