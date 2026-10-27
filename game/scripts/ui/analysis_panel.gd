class_name AnalysisPanel
extends CanvasLayer
## Panel de análisis científico. Solo presentación.

@onready var _root: Control = %PanelRoot
@onready var _title: Label = %TitleLabel
@onready var _status: Label = %StatusLabel
@onready var _description: Label = %DescriptionLabel
@onready var _facts: VBoxContainer = %FactsBox
@onready var _disclaimer: Label = %DisclaimerLabel
@onready var _close_btn: Button = %CloseButton


func _ready() -> void:
	visible = false
	_root.visible = false
	_close_btn.pressed.connect(close)
	App.bus().scan_completed.connect(_on_scan_completed)


func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event.is_action_pressed("ui_cancel") or event.is_action_pressed("panel_close"):
		close()
		get_viewport().set_input_as_handled()


func open_for(destination_id: String, was_new: bool) -> void:
	var entry: DestinationEntry = App.notebook().get_catalog().get_entry(destination_id)
	if entry == null:
		return
	_title.text = entry.display_name
	_status.text = "NUEVO DESCUBRIMIENTO" if was_new else "YA EN EL CUADERNO"
	_status.modulate = Color(0.957, 0.827, 0.369) if was_new else Color(0.55, 0.72, 0.85)
	_description.text = entry.short_description
	_disclaimer.text = entry.arcade_disclaimer
	_rebuild_facts(entry)
	visible = true
	_root.visible = true


func close() -> void:
	visible = false
	_root.visible = false
	App.bus().analysis_panel_closed.emit()


func _on_scan_completed(destination_id: String, was_new: bool) -> void:
	open_for(destination_id, was_new)


func _rebuild_facts(entry: DestinationEntry) -> void:
	for child in _facts.get_children():
		child.queue_free()
	for fact in entry.scientific_facts:
		var block := VBoxContainer.new()
		block.add_theme_constant_override("separation", 2)
		var label := Label.new()
		label.text = str(fact.get("label", ""))
		label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		label.add_theme_font_size_override("font_size", 13)
		label.add_theme_color_override("font_color", Color(0.239, 0.906, 0.788))
		var value := Label.new()
		value.text = str(fact.get("value", ""))
		value.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		value.add_theme_font_size_override("font_size", 15)
		value.add_theme_color_override("font_color", Color(0.91, 0.945, 1.0))
		block.add_child(label)
		block.add_child(value)
		if bool(fact.get("is_game_simplification", false)):
			var note := Label.new()
			note.text = "Simplificación: %s" % str(
				fact.get("simplification_note", "dato redondeado para el juego")
			)
			note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			note.add_theme_font_size_override("font_size", 11)
			note.add_theme_color_override("font_color", Color(0.75, 0.7, 0.55))
			block.add_child(note)
		_facts.add_child(block)
