class_name ObjectivePanel
extends PanelContainer
## Caja de objetivo: capítulo, misión y siguiente paso. Lee StoryDirector.

@onready var _chapter: Label = %ChapterLabel
@onready var _title: Label = %ObjectiveTitle
@onready var _hint: Label = %ObjectiveHint


func _ready() -> void:
	var bus := App.bus()
	bus.mission_updated.connect(func(_id: String) -> void: refresh())
	bus.mission_started.connect(func(_id: String) -> void: refresh())
	bus.mission_completed.connect(func(_id: String) -> void: refresh())
	bus.chapter_changed.connect(func(_c: int) -> void: refresh())
	refresh()


func refresh() -> void:
	var story := App.story()
	var summary: Dictionary = story.objective_summary()
	var chapter := int(summary.get("chapter", 1))
	var info: Dictionary = story.chapter_info(chapter)
	_chapter.text = "CAP. %d · %s" % [chapter, str(info.get("title", "")).to_upper()]
	var title := str(summary.get("title", ""))
	var hint := str(summary.get("hint", ""))
	if title.is_empty():
		title = "SIN MISIÓN ACTIVA"
		hint = "Explora y escanea con F."
	_title.text = title
	_hint.text = hint
