class_name ProbeLabController
extends Control
## UI del laboratorio. La lógica vive en domain/lab.

const CHALLENGE_BASIC := "res://assets/data/lab/challenge_scan_transmit.json"
const CHALLENGE_LOOPS := "res://assets/data/lab/challenge_loop_corridor.json"
const MAX_CELL := 72.0
const FIRST_SOLVE_XP := 20

const CATEGORY_COLORS := {
	ProbeOpcodes.CATEGORY_MOVE: Color(0.239, 0.906, 0.788),
	ProbeOpcodes.CATEGORY_ACTION: Color(0.957, 0.827, 0.369),
	ProbeOpcodes.CATEGORY_CONTROL: Color(0.72, 0.58, 1.0),
}

const THEMES := {
	"lab": {"cell": Color(0.12, 0.18, 0.28), "line": Color(0.3, 0.45, 0.6), "rock": "rock_moon", "sample": "sample"},
	"earth": {"cell": Color(0.36, 0.3, 0.2), "line": Color(0.5, 0.42, 0.28), "rock": "dead_tree", "sample": "plant_alive"},
	"moon": {"cell": Color(0.3, 0.31, 0.36), "line": Color(0.45, 0.47, 0.52), "rock": "rock_moon", "sample": "ice"},
	"mars": {"cell": Color(0.52, 0.24, 0.15), "line": Color(0.68, 0.36, 0.22), "rock": "rock_mars", "sample": "sample"},
}

@onready var _title: Label = %TitleLabel
@onready var _briefing: Label = %BriefingLabel
@onready var _concepts: Label = %ConceptsLabel
@onready var _grid_host: Control = %GridHost
@onready var _program_list: ItemList = %ProgramList
@onready var _palette: HFlowContainer = %Palette
@onready var _status: Label = %StatusLabel
@onready var _step_label: Label = %StepLabel
@onready var _blocks_label: Label = %BlocksLabel
@onready var _btn_run: Button = %RunButton
@onready var _btn_step: Button = %StepButton
@onready var _btn_stop: Button = %StopButton
@onready var _btn_reset: Button = %ResetButton
@onready var _btn_back: Button = %BackButton
@onready var _btn_loops: Button = %LoopsChallengeButton
@onready var _btn_hint: Button = %HintButton
@onready var _btn_clear: Button = %ClearButton
@onready var _repeat_spin: SpinBox = %RepeatSpin
@onready var _repeat_label: Label = %RepeatLabel

var _challenge: ChallengeDef
var _world: ProbeWorldState
var _program: ProbeProgram = ProbeProgram.new()
var _interpreter: ProbeInterpreter = ProbeInterpreter.new()
var _catalog: ChallengeCatalog = ChallengeCatalog.new()
var _grid_draw: Control
var _step_delay_sec: float = 0.35
var _run_token: int = 0
## Reto pedido por una misión (vacío = modo libre).
var _story_challenge_id: String = ""
var _textures: Dictionary = {}


func _ready() -> void:
	_btn_run.pressed.connect(_on_run)
	_btn_step.pressed.connect(_on_step)
	_btn_stop.pressed.connect(_on_stop)
	_btn_reset.pressed.connect(_on_reset)
	_btn_back.pressed.connect(_on_back)
	_btn_loops.pressed.connect(_load_loops_challenge)
	_btn_hint.pressed.connect(_on_hint)
	_btn_clear.pressed.connect(_on_clear)
	_program.changed.connect(_refresh_program_list)
	_interpreter.step_executed.connect(_on_step_executed)
	_interpreter.finished.connect(_on_finished)
	_interpreter.failed.connect(_on_failed)
	_grid_host.resized.connect(func() -> void:
		if _grid_draw != null:
			_grid_draw.queue_redraw()
	)
	_catalog.load_all()
	_story_challenge_id = str(App.router().lab_challenge_id)
	if not _story_challenge_id.is_empty() and _catalog.has_id(_story_challenge_id):
		_set_challenge(_catalog.get_def(_story_challenge_id))
		_btn_back.text = "Volver a la misión"
	else:
		_story_challenge_id = ""
		_load_challenge(CHALLENGE_BASIC)


func _load_loops_challenge() -> void:
	_load_challenge(CHALLENGE_LOOPS)


func _load_challenge(path: String) -> void:
	_set_challenge(ChallengeDef.load_from_path(path))


func _set_challenge(def: ChallengeDef) -> void:
	_run_token += 1
	_interpreter.stop()
	_challenge = def
	if _challenge == null:
		_status.text = "No se pudo cargar el reto."
		return
	_world = _challenge.build_world()
	_program.clear()
	_interpreter.setup(_world, _program, _challenge.allow_loops, _challenge.allow_conditions, _challenge.max_blocks)
	_title.text = _challenge.title
	_briefing.text = _challenge.briefing
	_concepts.text = _challenge.concepts_text
	_btn_loops.visible = _story_challenge_id.is_empty() and not _challenge.allow_loops
	_btn_hint.visible = not _challenge.hint.is_empty()
	_repeat_label.visible = _challenge.allow_loops
	_repeat_spin.visible = _challenge.allow_loops
	_build_palette()
	_ensure_grid()
	_grid_draw.queue_redraw()
	_set_status("Listo. Arma tu programa con los bloques y pulsa Ejecutar.", Color(0.91, 0.945, 1.0))
	_step_label.text = "Paso: —"
	_refresh_program_list()


func _build_palette() -> void:
	for child in _palette.get_children():
		child.queue_free()
	for op in _challenge.available_ops:
		var btn := Button.new()
		btn.text = "REPETIR ×N" if op == ProbeOpcodes.REPEAT_BEGIN else ProbeOpcodes.display_name(op)
		btn.tooltip_text = ProbeOpcodes.help_text(op)
		btn.custom_minimum_size = Vector2(0, 40)
		btn.add_theme_font_size_override("font_size", 16)
		btn.add_theme_color_override("font_color", CATEGORY_COLORS[ProbeOpcodes.category(op)])
		if op == ProbeOpcodes.REPEAT_BEGIN:
			btn.pressed.connect(_add_repeat)
		else:
			btn.pressed.connect(func() -> void: _add_op(op))
		_palette.add_child(btn)


func _add_op(op: String) -> void:
	var err := _program.append_op(op)
	if not err.is_empty():
		_set_status(err, Color(1.0, 0.6, 0.55))
	else:
		App.sfx().play("blip")


func _add_repeat() -> void:
	var times := int(_repeat_spin.value)
	var err := _program.append_op(ProbeOpcodes.REPEAT_BEGIN, times)
	if not err.is_empty():
		_set_status(err, Color(1.0, 0.6, 0.55))
	else:
		App.sfx().play("blip")


# ------------------------------------------------------------ cuadrícula

func _ensure_grid() -> void:
	if _grid_draw != null:
		_grid_draw.queue_redraw()
		return
	_grid_draw = Control.new()
	_grid_draw.name = "GridCanvas"
	_grid_draw.set_anchors_preset(Control.PRESET_FULL_RECT)
	_grid_draw.draw.connect(_draw_grid)
	_grid_host.add_child(_grid_draw)


func _cell_size() -> float:
	var avail := _grid_host.size
	if _world == null or avail.x <= 0.0:
		return 56.0
	var c := minf(avail.x / float(_world.width), avail.y / float(_world.height))
	return clampf(floorf(c / 8.0) * 8.0, 32.0, MAX_CELL)


func _draw_grid() -> void:
	if _world == null or _grid_draw == null:
		return
	var look: Dictionary = THEMES.get(_challenge.theme, THEMES["lab"])
	var cell := _cell_size()
	var grid_px := Vector2(_world.width, _world.height) * cell
	var origin := ((_grid_host.size - grid_px) * 0.5).floor()
	var inner := Vector2(cell - 2.0, cell - 2.0)
	for y in _world.height:
		for x in _world.width:
			var rect := Rect2(origin + Vector2(x, y) * cell, inner)
			var color: Color = look["cell"]
			if (x + y) % 2 == 1:
				color = color.darkened(0.08)
			if _world.transmit_cell == Vector2i(x, y):
				color = color.lerp(Color(0.24, 0.91, 0.79), 0.25)
			_grid_draw.draw_rect(rect, color)
			_grid_draw.draw_rect(rect, look["line"], false, 1.0)
			if _world.is_blocked(x, y):
				_draw_sprite(str(look["rock"]), rect)
	for cell_pos in _world.poi_cells:
		var r := _cell_rect(origin, cell, cell_pos)
		var scanned := _world.scanned_pois.has(_world.poi_key(cell_pos.x, cell_pos.y))
		_draw_star(r.get_center(), cell * 0.28, Color(0.55, 0.72, 0.85) if scanned else Color(0.96, 0.83, 0.37))
	for cell_pos in _world.sample_cells:
		if _world.has_sample(cell_pos.x, cell_pos.y):
			_draw_sprite(str(look["sample"]), _cell_rect(origin, cell, cell_pos))
	var t := _world.transmit_cell
	if t.x >= 0:
		_draw_sprite("antenna", _cell_rect(origin, cell, t))
	var probe_rect := _cell_rect(origin, cell, Vector2i(_world.probe_x, _world.probe_y))
	var hal := _texture("res://assets/art/characters/hal.png")
	if hal != null:
		_grid_draw.draw_texture_rect_region(hal, probe_rect.grow(-cell * 0.12), Rect2(32, 0, 16, 16))
	var c := probe_rect.get_center()
	var dir := Vector2(_world.dir_vector())
	var tip := c + dir * cell * 0.46
	var side := dir.orthogonal() * cell * 0.1
	_grid_draw.draw_colored_polygon(
		PackedVector2Array([tip, c + dir * cell * 0.3 + side, c + dir * cell * 0.3 - side]),
		Color(0.96, 0.83, 0.37)
	)


func _cell_rect(origin: Vector2, cell: float, pos: Vector2i) -> Rect2:
	return Rect2(origin + Vector2(pos) * cell, Vector2(cell - 2.0, cell - 2.0))


func _draw_sprite(sprite_name: String, rect: Rect2) -> void:
	var tex := _texture("res://assets/art/props/%s.png" % sprite_name)
	if tex == null:
		return
	var s := rect.size * 0.8
	var draw_size := Vector2(s.x, s.x * tex.get_height() / float(tex.get_width()))
	if draw_size.y > s.y:
		draw_size = Vector2(s.y * tex.get_width() / float(tex.get_height()), s.y)
	_grid_draw.draw_texture_rect(tex, Rect2(rect.get_center() - draw_size * 0.5, draw_size), false)


func _draw_star(center: Vector2, radius: float, color: Color) -> void:
	var pts := PackedVector2Array()
	for i in 10:
		var r := radius if i % 2 == 0 else radius * 0.45
		var a := -PI * 0.5 + TAU * float(i) / 10.0
		pts.append(center + Vector2(cos(a), sin(a)) * r)
	_grid_draw.draw_colored_polygon(pts, color)


func _texture(path: String) -> Texture2D:
	if not _textures.has(path):
		_textures[path] = load(path) if ResourceLoader.exists(path) else null
	return _textures[path]


# ------------------------------------------------------------ programa

func _refresh_program_list() -> void:
	_program_list.clear()
	for i in _program.size():
		var op := _program.get_op(i)
		var label := ProbeOpcodes.display_name(op)
		if op == ProbeOpcodes.REPEAT_BEGIN:
			label = "REPETIR ×%d" % _program.get_repeat_times(i)
		var indent := "    ".repeat(_program.depth_at(i))
		var idx := _program_list.add_item("%2d. %s%s" % [i + 1, indent, label])
		_program_list.set_item_custom_fg_color(idx, CATEGORY_COLORS[ProbeOpcodes.category(op)])
	var limit := ""
	if _challenge != null and _challenge.max_blocks > 0:
		limit = " / %d" % _challenge.max_blocks
	_blocks_label.text = "Bloques: %d%s" % [_program.size(), limit]
	var over := _challenge != null and _challenge.max_blocks > 0 and _program.size() > _challenge.max_blocks
	_blocks_label.modulate = Color(1.0, 0.6, 0.55) if over else Color(1, 1, 1)


func _on_run() -> void:
	_run_token += 1
	var token := _run_token
	var err := _interpreter.start()
	if not err.is_empty():
		_set_status(err, Color(1.0, 0.75, 0.55))
		App.sfx().play("error")
		_grid_draw.queue_redraw()
		return
	_set_status("Ejecutando…", Color(0.91, 0.945, 1.0))
	_btn_run.disabled = true
	while _interpreter.is_running() and token == _run_token:
		var step_err := _interpreter.step()
		_grid_draw.queue_redraw()
		if not step_err.is_empty():
			break
		await get_tree().create_timer(_step_delay_sec).timeout
	_btn_run.disabled = false
	_grid_draw.queue_redraw()


func _on_step() -> void:
	if not _interpreter.is_running():
		var err := _interpreter.start()
		if not err.is_empty():
			_set_status(err, Color(1.0, 0.75, 0.55))
			return
	var step_err := _interpreter.step()
	if not step_err.is_empty():
		_set_status(step_err, Color(1.0, 0.6, 0.55))
	_grid_draw.queue_redraw()


func _on_stop() -> void:
	_run_token += 1
	_interpreter.stop()
	_set_status("Ejecución detenida.", Color(0.91, 0.945, 1.0))
	_btn_run.disabled = false


func _on_reset() -> void:
	_run_token += 1
	_interpreter.stop()
	_interpreter.reset_execution()
	_set_status("Reiniciado: sonda y sensores como al inicio.", Color(0.91, 0.945, 1.0))
	_step_label.text = "Paso: —"
	_btn_run.disabled = false
	_grid_draw.queue_redraw()


func _on_clear() -> void:
	_on_reset()
	_program.clear()


func _on_hint() -> void:
	if _challenge != null:
		_set_status("HAL: %s" % _challenge.hint, Color(0.239, 0.906, 0.788))


func _on_back() -> void:
	_run_token += 1
	_interpreter.stop()
	App.router().return_from_lab()


func _on_step_executed(index: int, op: String, message: String) -> void:
	_step_label.text = "Paso %d: %s — %s" % [index + 1, ProbeOpcodes.display_name(op), message]
	_program_list.select(index)


func _on_finished(success: bool, message: String) -> void:
	_btn_run.disabled = false
	if not success:
		_set_status(message, Color(1.0, 0.75, 0.55))
		App.sfx().play("error")
		return
	_set_status(message, Color(0.5, 1.0, 0.7))
	App.sfx().play("success")
	var gs := App.game_state()
	var puzzle_id := _challenge.id
	var first_time: bool = not gs.solved_puzzles.has(puzzle_id)
	if first_time:
		gs.mark_puzzle_solved(puzzle_id)
		gs.add_experience(FIRST_SOLVE_XP)
	if not _story_challenge_id.is_empty():
		App.bus().challenge_solved.emit(_story_challenge_id)
		_set_status("%s Pulsa «Volver a la misión»." % message, Color(0.5, 1.0, 0.7))


func _on_failed(message: String) -> void:
	_set_status(message, Color(1.0, 0.6, 0.55))


func _set_status(text: String, color: Color) -> void:
	_status.text = text
	_status.modulate = color


func _on_remove_pressed() -> void:
	var selected := _program_list.get_selected_items()
	if selected.is_empty():
		return
	_program.remove_at(selected[0])


func _on_up_pressed() -> void:
	var selected := _program_list.get_selected_items()
	if selected.is_empty():
		return
	var i: int = selected[0]
	_program.move_up(i)
	_program_list.select(maxi(i - 1, 0))


func _on_down_pressed() -> void:
	var selected := _program_list.get_selected_items()
	if selected.is_empty():
		return
	var i: int = selected[0]
	_program.move_down(i)
	_program_list.select(mini(i + 1, _program.size() - 1))
