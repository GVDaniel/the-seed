class_name CutscenePlayer
extends Control
## Cinemática de diapositivas (pixel art 320×180 a pantalla completa) con texto narrado.

const DATA_PATH := "res://assets/data/story/cutscenes.json"
const CHARS_PER_SEC := 45.0

## Cinemática por defecto si Router no indica otra.
@export var cutscene_id: String = "intro"

@onready var _image: TextureRect = %SlideImage
@onready var _speaker: Label = %SpeakerLabel
@onready var _text: Label = %TextLabel
@onready var _next_btn: Button = %NextButton
@onready var _skip_btn: Button = %SkipButton

var _data: Dictionary = {}
var _slides: Array = []
var _slide: int = 0
var _line: int = 0
var _reveal: float = 0.0
var _done: bool = false


func _ready() -> void:
	var router := App.router()
	if not str(router.cutscene_id).is_empty():
		cutscene_id = str(router.cutscene_id)
	_data = JsonDir.load_dict(DATA_PATH).get(cutscene_id, {})
	_slides = _data.get("slides", [])
	App.music().play(str(_data.get("music", "title")))
	_next_btn.pressed.connect(_advance)
	_skip_btn.pressed.connect(_finish)
	if _slides.is_empty():
		_finish.call_deferred()
		return
	_show_slide(0)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_accept") or event.is_action_pressed("interact"):
		_advance()
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_cancel"):
		_finish()
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	if _text.visible_characters < 0:
		return
	_reveal += delta * CHARS_PER_SEC
	_text.visible_characters = int(_reveal)
	if _text.visible_characters >= _text.text.length():
		_text.visible_characters = -1


func _show_slide(index: int) -> void:
	_slide = index
	_line = 0
	var slide: Dictionary = _slides[index]
	var path := str(slide.get("image", ""))
	_image.texture = load(path) if ResourceLoader.exists(path) else null
	_image.modulate.a = 0.0
	create_tween().tween_property(_image, "modulate:a", 1.0, 0.6)
	_show_line()


func _show_line() -> void:
	var lines: Array = (_slides[_slide] as Dictionary).get("lines", [])
	if lines.is_empty():
		_text.text = ""
		return
	var line: Dictionary = lines[_line]
	var who := str(line.get("who", ""))
	_speaker.text = App.story().characters().display_name(who) if not who.is_empty() else ""
	_speaker.visible = not who.is_empty()
	_text.text = str(line.get("text", ""))
	_text.visible_characters = 0
	_reveal = 0.0


func _advance() -> void:
	if _done:
		return
	if _text.visible_characters >= 0:
		_text.visible_characters = -1
		return
	App.sfx().play("blip")
	var lines: Array = (_slides[_slide] as Dictionary).get("lines", [])
	if _line < lines.size() - 1:
		_line += 1
		_show_line()
	elif _slide < _slides.size() - 1:
		_show_slide(_slide + 1)
	else:
		_finish()


func _finish() -> void:
	if _done:
		return
	_done = true
	var router := App.router()
	if cutscene_id == "intro":
		App.game_state().intro_seen = true
		App.game_state().save_local()
	var next := str(router.cutscene_next_location)
	if next.is_empty():
		next = str(_data.get("next", "earth"))
	router.cutscene_id = ""
	router.cutscene_next_location = ""
	router.go_location(next, str(_data.get("spawn", "ship")))
