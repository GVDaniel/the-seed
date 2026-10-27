class_name FlightHud
extends CanvasLayer
## HUD futurista de vuelo: telemetría, rango, objetivo y avisos.

@export var ship_path: NodePath
@export var director_path: NodePath

@onready var _ship_name: Label = %ShipNameLabel
@onready var _speed: Label = %SpeedLabel
@onready var _energy: Label = %EnergyLabel
@onready var _energy_bar: ProgressBar = %EnergyBar
@onready var _hint: Label = %HintLabel
@onready var _mode: Label = %ModeLabel
@onready var _xp_label: Label = %XpLabel
@onready var _toast: Label = %ToastLabel
@onready var _lab_btn: Button = %LabButton

var _ship: ShipController
var _director: SpaceDirector
var _toast_timer: float = 0.0


func _ready() -> void:
	_ship = get_node(ship_path) as ShipController
	_director = get_node(director_path) as SpaceDirector
	_toast.visible = false
	if _lab_btn != null:
		_lab_btn.pressed.connect(_on_lab_pressed)
	(%HalButton as Button).pressed.connect(func() -> void: App.bus().hal_interface_requested.emit(""))
	if _ship != null:
		_ship.telemetry_updated.connect(_on_telemetry)
		_ship_name.text = _ship.stats.ship_name if _ship.stats else "ASTRA"
	if _director != null:
		_director.hint_changed.connect(_on_hint)
		_director.mode_changed.connect(_on_mode)
		_on_mode(_director.mode)
	App.bus().mission_status_message.connect(_show_toast)
	App.bus().experience_changed.connect(_on_xp)
	App.bus().credits_changed.connect(func(_c: int) -> void: _on_xp(int(App.game_state().experience)))
	_on_xp(int(App.game_state().get("experience")))


func _process(delta: float) -> void:
	if _toast_timer > 0.0:
		_toast_timer -= delta
		if _toast_timer <= 0.0:
			_toast.visible = false


func _on_telemetry(speed: float, energy: float, ship_name: String) -> void:
	_ship_name.text = ship_name
	_speed.text = "VEL  %03d" % int(speed)
	_energy.text = "NRG  %03d" % int(energy)
	_energy_bar.max_value = _ship.stats.max_energy if _ship and _ship.stats else 100.0
	_energy_bar.value = energy


func _on_hint(text: String) -> void:
	_hint.text = text


func _on_mode(mode: SpaceDirector.Mode) -> void:
	match mode:
		SpaceDirector.Mode.SPACE:
			_mode.text = "MODO  ÓRBITA"
		SpaceDirector.Mode.SURFACE:
			_mode.text = "MODO  SUPERFICIE"


func _on_xp(total_xp: int) -> void:
	_xp_label.text = "%s · XP %d · %d cr" % [App.game_state().rank_name(), total_xp, int(App.game_state().credits)]


func _show_toast(text: String) -> void:
	_toast.text = text
	_toast.visible = true
	_toast_timer = 4.5


func _on_lab_pressed() -> void:
	App.router().open_free_lab("space")
