class_name DialoguePanel
extends CanvasLayer
## Diálogo lineal con retrato y texto que aparece letra a letra.

const CHARS_PER_SEC := 55.0

@onready var _root: Control = %PanelRoot
@onready var _speaker: Label = %SpeakerLabel
@onready var _body: Label = %BodyLabel
@onready var _portrait: TextureRect = %Portrait
@onready var _next_btn: Button = %NextButton

var _lines: Array = []
var _index: int = 0
var _context: String = ""
var _reveal: float = 0.0
var _blip_counter: int = 0


func _ready() -> void:
	visible = false
	_root.visible = false
	_next_btn.pressed.connect(_on_next)
	App.bus().dialogue_requested.connect(_on_requested)


func is_open() -> bool:
	return visible


func _process(delta: float) -> void:
	if not visible or _body.visible_ratio >= 1.0:
		return
	var total := maxi(1, _body.text.length())
	_reveal += delta * CHARS_PER_SEC
	_body.visible_characters = int(_reveal)
	if _body.visible_characters >= total:
		_body.visible_characters = -1
	_blip_counter += 1
	if _blip_counter % 4 == 0:
		App.sfx().play("blip", randf_range(0.9, 1.15))


func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event.is_action_pressed("ui_accept") or event.is_action_pressed("interact") or event.is_action_pressed("interact_talk"):
		_on_next()
		get_viewport().set_input_as_handled()


func _on_requested(_speaker_name: String, lines: Array, context: String) -> void:
	_lines = lines
	_index = 0
	_context = context
	if _lines.is_empty():
		_finish()
		return
	visible = true
	_root.visible = true
	_show_line()


func _show_line() -> void:
	var line: Variant = _lines[_index]
	if typeof(line) != TYPE_DICTIONARY:
		_finish()
		return
	var who := str(line.get("who", ""))
	var character: CharacterDef = App.story().characters().get_def(who)
	if character != null:
		_speaker.text = character.display_name
		_portrait.texture = load(character.portrait_path) if ResourceLoader.exists(character.portrait_path) else null
	else:
		_speaker.text = str(line.get("speaker", "???"))
		_portrait.texture = null
	_portrait.get_parent().visible = _portrait.texture != null
	_body.text = str(line.get("text", ""))
	_body.visible_characters = 0
	_reveal = 0.0
	var last := _index >= _lines.size() - 1
	if _context.begins_with("offer") and last:
		_next_btn.text = "Aceptar misión"
	elif last:
		_next_btn.text = "Cerrar"
	else:
		_next_btn.text = "Continuar"


func _on_next() -> void:
	if _body.visible_characters != -1:
		_body.visible_characters = -1
		return
	if _index >= _lines.size() - 1:
		_finish()
		return
	_index += 1
	_show_line()


func _finish() -> void:
	visible = false
	_root.visible = false
	var ctx := _context
	_context = ""
	_lines.clear()
	App.bus().dialogue_finished.emit(ctx)
