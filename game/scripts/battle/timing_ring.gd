class_name TimingRing
extends Control
## Pulsaciones a tiempo (Espacio, E, clic o toque) en coordenadas de pantalla.
## - start(): un anillo se cierra sobre un círculo; pulsa cuando lo toque (golpear o bloquear).
## - start_hold(): mantén pulsado; el medidor se llena; suelta en la zona dorada.

signal resolved(timing: String)

const TARGET_RADIUS := 22.0
const START_RADIUS := 84.0
const HOLD_SECONDS := 1.15
const HOLD_SIZE := Vector2(150, 16)

var duration: float = 0.8
var window: float = 0.15
var blocking: bool = false
var _hold_mode: bool = false
var _holding: bool = false
var _t: float = 0.0
var _active: bool = false
var _center: Vector2 = Vector2.ZERO
var _result_text: String = ""
var _result_color: Color = Color.WHITE
var _result_timer: float = 0.0
var _font: Font


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_font = get_theme_default_font()


func is_active() -> bool:
	return _active


func start(at: Vector2, is_block: bool, half_window: float, speed: float = 1.0) -> void:
	_center = at
	blocking = is_block
	window = half_window
	duration = 0.8 / maxf(0.5, speed)
	_hold_mode = false
	_begin()


func start_hold(at: Vector2, half_window: float) -> void:
	_center = at
	blocking = false
	window = half_window
	_hold_mode = true
	_holding = false
	_begin()


func _begin() -> void:
	_t = 0.0
	_active = true
	_result_text = ""
	queue_redraw()


## Para pruebas y autoplay: resuelve sin esperar input.
func force(timing: String) -> void:
	if _active:
		_finish(timing)


func _process(delta: float) -> void:
	if _result_timer > 0.0:
		_result_timer -= delta
		if _result_timer <= 0.0:
			_result_text = ""
		queue_redraw()
	if not _active:
		return
	if _hold_mode:
		if _holding:
			_t += delta
			if _t > HOLD_SECONDS * 1.15:
				_finish(BattleRules.MISS)
		else:
			# Espera a que empiece a mantener (con un límite generoso).
			_t -= delta
			if _t < -4.0:
				_finish(BattleRules.MISS)
	else:
		_t += delta
		if _t > duration + window:
			_finish(BattleRules.MISS)
	queue_redraw()


func _input(event: InputEvent) -> void:
	if not _active:
		return
	var pressed := event.is_action_pressed("ui_accept") or event.is_action_pressed("interact")
	var released := event.is_action_released("ui_accept") or event.is_action_released("interact")
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		pressed = event.pressed
		released = not event.pressed
	if event is InputEventScreenTouch:
		pressed = event.pressed
		released = not event.pressed
	if not pressed and not released:
		return
	get_viewport().set_input_as_handled()
	if _hold_mode:
		if pressed and not _holding:
			_holding = true
			_t = 0.0
		elif released and _holding:
			_finish(BattleRules.judge_hold(_t / HOLD_SECONDS, window))
	elif pressed:
		_finish(BattleRules.judge(_t - duration, window))


func _finish(timing: String) -> void:
	_active = false
	_holding = false
	_result_text = BattleRules.timing_text(timing, blocking)
	_result_color = HalUi.GOLD if timing == BattleRules.PERFECT else (HalUi.CYAN if timing == BattleRules.GOOD else HalUi.DIM)
	if _result_text.is_empty():
		if _hold_mode:
			_result_text = "Demasiado…" if _t / HOLD_SECONDS > BattleRules.HOLD_SWEET else "Poco…"
		else:
			_result_text = "Tarde…" if _t > duration else "Pronto…"
	_result_timer = 0.7
	queue_redraw()
	resolved.emit(timing)


func _draw() -> void:
	var color := HalUi.CYAN if blocking else HalUi.GOLD
	if _active and _hold_mode:
		_draw_hold()
	elif _active:
		var k := clampf(_t / duration, 0.0, 1.0)
		var r := lerpf(START_RADIUS, TARGET_RADIUS, k * k * (3.0 - 2.0 * k))
		var near := 1.0 - clampf(absf(_t - duration) / (window * 2.0), 0.0, 1.0)
		draw_circle(_center, TARGET_RADIUS, Color(color, 0.12 + 0.25 * near))
		draw_arc(_center, TARGET_RADIUS, 0.0, TAU, 40, color, 3.0, true)
		draw_arc(_center, TARGET_RADIUS + 5.0, 0.0, TAU, 40, Color(color, 0.35), 1.0, true)
		draw_arc(_center, r, 0.0, TAU, 48, Color(1, 1, 1, 0.55 + 0.45 * k), 2.0 + 2.0 * k, true)
		_text(_center + Vector2(0, -TARGET_RADIUS - 12), "¡BLOQUEA!" if blocking else "¡AHORA!", 18, color)
	if not _result_text.is_empty():
		var rise := (0.7 - _result_timer) * 30.0
		_text(_center + Vector2(0, TARGET_RADIUS + 28 - rise), _result_text, 22, _result_color)


func _draw_hold() -> void:
	var origin := _center - HOLD_SIZE * 0.5
	var rect := Rect2(origin, HOLD_SIZE)
	draw_rect(rect.grow(3), Color(0.02, 0.04, 0.08, 0.85))
	var zone := window * 0.5
	var zx0 := clampf(BattleRules.HOLD_SWEET - zone, 0, 1) * HOLD_SIZE.x
	var zx1 := clampf(BattleRules.HOLD_SWEET + zone, 0, 1) * HOLD_SIZE.x
	draw_rect(Rect2(origin + Vector2(zx0, 0), Vector2(zx1 - zx0, HOLD_SIZE.y)), Color(HalUi.GOLD, 0.45))
	var px0 := clampf(BattleRules.HOLD_SWEET - zone * 0.4, 0, 1) * HOLD_SIZE.x
	var px1 := clampf(BattleRules.HOLD_SWEET + zone * 0.4, 0, 1) * HOLD_SIZE.x
	draw_rect(Rect2(origin + Vector2(px0, 0), Vector2(px1 - px0, HOLD_SIZE.y)), Color(HalUi.GOLD, 0.85))
	var fill := clampf(_t / HOLD_SECONDS, 0.0, 1.0) if _holding else 0.0
	draw_rect(Rect2(origin, Vector2(fill * HOLD_SIZE.x, HOLD_SIZE.y)), Color(HalUi.CYAN, 0.75))
	draw_rect(rect, HalUi.CYAN, false, 2.0)
	var label := "¡Suelta en lo dorado!" if _holding else "Mantén pulsado…"
	_text(_center + Vector2(0, -HOLD_SIZE.y - 6), label, 18, HalUi.GOLD)


func _text(center: Vector2, text: String, size: int, color: Color) -> void:
	var w := _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var pos := center - Vector2(w * 0.5, 0)
	draw_string_outline(_font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, 6, Color(0.02, 0.035, 0.07))
	draw_string(_font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)
