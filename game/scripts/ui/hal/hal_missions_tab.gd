class_name HalMissionsTab
extends VBoxContainer
## Pestaña Misiones: capítulo actual, historia principal y misiones secundarias.

var _chapter: Label
var _subtitle: Label
var _list: VBoxContainer


func _ready() -> void:
	add_theme_constant_override("separation", 8)
	_chapter = HalUi.label("", 22, HalUi.GOLD)
	_subtitle = HalUi.label("", 15, HalUi.DIM, true)
	add_child(_chapter)
	add_child(_subtitle)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 10)
	add_child(HalUi.scroll(_list))


func refresh() -> void:
	var story := App.story()
	var info: Dictionary = story.chapter_info(int(story.current_chapter()))
	_chapter.text = "Capítulo %d · %s" % [int(info.get("chapter", 1)), str(info.get("title", ""))]
	_subtitle.text = str(info.get("subtitle", ""))
	HalUi.clear(_list)
	_list.add_child(HalUi.label("HISTORIA PRINCIPAL", 14, HalUi.CYAN))
	_add_cards(false)
	_list.add_child(HalUi.label("MISIONES SECUNDARIAS · consiguen materiales y experiencia", 14, HalUi.CYAN))
	_add_cards(true)


func _add_cards(side: bool) -> void:
	var missions := App.missions()
	for id in missions.ordered_mission_ids():
		var def: MissionDef = missions.get_def(id)
		if def.is_side() != side:
			continue
		if missions.is_completed(id):
			_list.add_child(_card(def, "COMPLETADA", HalUi.CYAN, false))
		elif missions.is_active(id):
			_list.add_child(_card(def, "EN CURSO", HalUi.GOLD, true))
		elif missions.requirements_met(id):
			_list.add_child(_card(def, "DISPONIBLE", HalUi.GOLD, false))
		else:
			_list.add_child(_locked_card(def))


func _card(def: MissionDef, status: String, color: Color, detailed: bool) -> PanelContainer:
	var card := HalUi.panel(color, 12)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 4)
	var head := HBoxContainer.new()
	var title := HalUi.label(def.title, 19, HalUi.TEXT, true)
	head.add_child(title)
	head.add_child(HalUi.label(status, 13, color))
	col.add_child(head)
	if not def.summary.is_empty():
		col.add_child(HalUi.label(def.summary, 15, HalUi.DIM, true))
	if detailed:
		var state: MissionState = App.missions().get_state(def.id)
		var current: MissionObjectiveDef = App.missions().get_current_objective(def.id)
		for obj in def.objectives:
			var done := state != null and state.is_objective_done(obj.id)
			var is_current := current != null and current.id == obj.id
			var mark := "[x] " if done else ("[>] " if is_current else "[ ] ")
			var c := HalUi.DIM if done else (HalUi.GOLD if is_current else HalUi.TEXT)
			col.add_child(HalUi.label(mark + obj.description, 16, c, true))
	elif status == "DISPONIBLE":
		var who: String = App.story().characters().display_name(def.start_npc)
		col.add_child(HalUi.label("Habla con %s para empezarla." % who, 15, HalUi.GOLD, true))
	card.add_child(col)
	return card


func _locked_card(def: MissionDef) -> PanelContainer:
	var card := HalUi.panel(HalUi.LOCKED, 12)
	var head := HBoxContainer.new()
	var label := "Secundaria · capítulo %d · ???" if def.is_side() else "Capítulo %d · ???"
	head.add_child(HalUi.label(label % def.chapter, 18, HalUi.LOCKED, true))
	head.add_child(HalUi.label("BLOQUEADA", 13, HalUi.LOCKED))
	card.add_child(head)
	return card


func hal_line() -> String:
	var done := 0
	var ids: PackedStringArray = App.missions().ordered_mission_ids()
	for id in ids:
		if App.missions().is_completed(id):
			done += 1
	if done == ids.size():
		return "Todas las misiones completadas. Calculando rumbo a TRAPPIST-1e…"
	var sides: Array = App.story().side_offers()
	if not sides.is_empty():
		return "Hay misiones secundarias disponibles. Ayudar a la gente también nos da materiales y experiencia."
	return "Misiones completadas: %d de %d. Vamos paso a paso, como en un programa." % [done, ids.size()]
