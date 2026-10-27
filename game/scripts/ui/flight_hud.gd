class_name FlightHud
extends CanvasLayer
## HUD futurista de vuelo: telemetría, combustible, casco, objetivo y avisos.

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
@onready var _fuel_label: Label = %FuelLabel
@onready var _fuel_bar: ProgressBar = %FuelBar
@onready var _hull_label: Label = %HullLabel
@onready var _hull_bar: ProgressBar = %HullBar

var _ship: ShipController
var _director: SpaceDirector
var _toast_timer: float = 0.0
var _warned_low_fuel: bool = false


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
	App.bus().ship_state_changed.connect(_refresh_ship)
	_refresh_ship()


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
	_refresh_fuel()


func _refresh_ship() -> void:
	_refresh_fuel()
	var ship := App.ship()
	_hull_label.text = "CASCO  %d%%" % int(round(ship.hull))
	_hull_bar.value = ship.hull_ratio()
	_hull_label.modulate = Color(1, 0.45, 0.45) if ship.hull_ratio() < 0.35 else Color.WHITE


func _refresh_fuel() -> void:
	var ship := App.ship()
	var ratio: float = ship.fuel_ratio()
	if ship.is_empty():
		_fuel_label.text = "RESERVA"
	else:
		_fuel_label.text = "COMB  %d/%d" % [int(ceil(ship.fuel)), int(round(ship.capacity()))]
	_fuel_bar.value = ratio
	var low := ratio < 0.2
	_fuel_label.modulate = Color(1, 0.45, 0.45) if low else Color.WHITE
	if low and not _warned_low_fuel:
		_warned_low_fuel = true
		_show_toast("HAL: combustible bajo. Reposta en una estación de servicio (surtidor dorado).")
	elif not low:
		_warned_low_fuel = false


func _on_hint(text: String) -> void:
	_hint.text = text


func _on_mode(mode: SpaceDirector.Mode) -> void:
	match mode:
		SpaceDirector.Mode.SPACE:
			_mode.text = "MODO  ÓRBITA"
		SpaceDirector.Mode.SURFACE:
			_mode.text = "MODO  SUPERFICIE"


func _on_xp(total_xp: int) -> void:
	_xp_label.text = "Nv %d · XP %d · %d cr" % [int(App.hero().level()), total_xp, int(App.game_state().credits)]


func _show_toast(text: String) -> void:
	_toast.text = text
	_toast.visible = true
	_toast_timer = 4.5


func _on_lab_pressed() -> void:
	App.router().open_free_lab("space")
