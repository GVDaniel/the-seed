extends Node
## Hilo narrativo: traduce eventos del mundo (hablar, escanear, recoger, programar,
## aterrizar) en avances de misión y elige qué dice cada personaje.
## No conoce escenas concretas: solo EventBus, MissionLog y GameState.

const CHAPTERS_PATH := "res://assets/data/story/chapters.json"
const HAL_ID := "hal"

var _characters: CharacterCatalog = CharacterCatalog.new()
var _chapters: Array = []
var _last_chapter: int = 0


func _ready() -> void:
	_characters.load_all()
	_chapters = JsonDir.load_dict(CHAPTERS_PATH).get("chapters", [])
	var bus := App.bus()
	bus.dialogue_finished.connect(_on_dialogue_finished)
	bus.scan_completed.connect(func(id: String, _new: bool) -> void: _try_complete("scan_destination", id))
	bus.item_collected.connect(func(id: String) -> void: _try_complete("collect_item", id))
	bus.challenge_solved.connect(func(id: String) -> void: _try_complete("solve_challenge", id))
	bus.landed_on.connect(func(id: String) -> void: _try_complete("land_on", id))
	bus.took_off.connect(func(from: String) -> void: _try_complete("takeoff", from))
	bus.world_interacted.connect(func(id: String) -> void: _try_complete("interact", id))
	bus.mission_completed.connect(_on_mission_completed)
	bus.mission_started.connect(func(_id: String) -> void: _emit_nav_target())
	bus.mission_updated.connect(func(_id: String) -> void: _emit_nav_target())
	_last_chapter = current_chapter()


func characters() -> CharacterCatalog:
	return _characters


# ------------------------------------------------------------ partida

func new_game() -> void:
	App.game_state().reset_progress()
	App.notebook().clear_session()
	App.missions().clear_all_progress_for_tests()
	_auto_start_missions()
	_last_chapter = current_chapter()


func _auto_start_missions() -> void:
	var missions := App.missions()
	if not str(missions.get_active_mission_id()).is_empty():
		return
	for id in missions.ordered_mission_ids():
		var def: MissionDef = missions.get_def(id)
		if def.auto_start and missions.can_start(id) and missions.requirements_met(id):
			missions.start_mission(id)
			return


# ------------------------------------------------------------ capítulos

func current_chapter() -> int:
	var missions := App.missions()
	var active := str(missions.get_active_mission_id())
	if not active.is_empty():
		return (missions.get_def(active) as MissionDef).chapter
	var chapter := 1
	for id in missions.ordered_mission_ids():
		var def: MissionDef = missions.get_def(id)
		if missions.is_completed(id):
			chapter = def.chapter
		elif missions.requirements_met(id):
			return def.chapter
	return chapter


func chapter_info(chapter: int) -> Dictionary:
	for row in _chapters:
		if int(row.get("chapter", 0)) == chapter:
			return row
	return {"chapter": chapter, "title": "Capítulo %d" % chapter, "subtitle": ""}


## Resumen para HUD: {title, hint, chapter, target}.
func objective_summary() -> Dictionary:
	var missions := App.missions()
	var active := str(missions.get_active_mission_id())
	if not active.is_empty():
		var def: MissionDef = missions.get_def(active)
		var obj: MissionObjectiveDef = missions.get_current_objective(active)
		return {
			"title": def.title,
			"hint": obj.hud_hint if obj != null else "",
			"chapter": def.chapter,
			"target": obj.target if obj != null else "",
			"location": obj.location if obj != null else "",
		}
	for id in missions.ordered_mission_ids():
		var def: MissionDef = missions.get_def(id)
		if missions.can_start(id) and missions.requirements_met(id):
			var who := _characters.display_name(def.start_npc)
			return {
				"title": "NUEVA MISIÓN",
				"hint": "Habla con %s: «%s»" % [who, def.title],
				"chapter": def.chapter,
				"target": def.start_npc,
				"location": _npc_location(def.start_npc),
			}
	return {"title": "", "hint": "", "chapter": current_chapter(), "target": "", "location": ""}


func _npc_location(npc_id: String) -> String:
	var character := _characters.get_def(npc_id)
	return character.home if character != null else ""


func nav_target() -> String:
	return str(objective_summary().get("target", ""))


## Ids a buscar en la escena, en orden de preferencia: objetivo y luego su lugar.
func nav_candidates() -> PackedStringArray:
	var summary := objective_summary()
	var out := PackedStringArray()
	for key in ["target", "location"]:
		var v := str(summary.get(key, ""))
		if not v.is_empty() and v != str(App.game_state().location):
			out.append(v)
	return out


func _emit_nav_target() -> void:
	App.bus().nav_target_changed.emit(nav_target())


# ------------------------------------------------------------ reglas de acceso

func can_land(destination_id: String) -> bool:
	return land_block_reason(destination_id).is_empty()


func land_block_reason(destination_id: String) -> String:
	match destination_id:
		"moon":
			if not App.missions().is_completed("signal_from_moon"):
				return "Antes de aterrizar en la Luna, la Dra. Vega en Aurora tiene una misión para ti."
		"mars":
			if not App.missions().is_completed("ice_of_shackleton"):
				return "Sin combustible extra no llegamos a Marte. Kai, en la Luna, puede ayudarnos."
	return ""


func can_take_off(location_id: String) -> bool:
	return takeoff_block_reason(location_id).is_empty()


func takeoff_block_reason(location_id: String) -> String:
	if location_id != "earth":
		return ""
	var missions := App.missions()
	if missions.is_completed("last_seed"):
		return ""
	var obj: MissionObjectiveDef = missions.get_current_objective("last_seed")
	if obj != null and obj.condition_type() == "takeoff":
		return ""
	return "Lo siento, Andrés. Me temo que no puedo hacer eso… todavía. Primero completa los objetivos en la Tierra."


func can_collect(item_id: String) -> bool:
	return _is_current("collect_item", item_id)


func can_interact(target_id: String) -> bool:
	return _is_current("interact", target_id)


func is_current_objective(type: String, value: String) -> bool:
	return _is_current(type, value)


func _is_current(type: String, value: String) -> bool:
	var missions := App.missions()
	var active := str(missions.get_active_mission_id())
	if active.is_empty():
		return false
	var obj: MissionObjectiveDef = missions.get_current_objective(active)
	return obj != null and obj.condition_type() == type and obj.condition_value() == value


## Llamado desde el espacio cuando la nave entra en el anillo de un destino.
func notify_near(destination_id: String) -> void:
	_try_complete("near_destination", destination_id)


func _try_complete(type: String, value: String) -> bool:
	if not _is_current(type, value):
		return false
	var missions := App.missions()
	var active := str(missions.get_active_mission_id())
	var obj: MissionObjectiveDef = missions.get_current_objective(active)
	return missions.complete_objective(active, obj.id)


# ------------------------------------------------------------ diálogos

## Decide qué dice un personaje según el estado de las misiones.
func talk_to(npc_id: String) -> void:
	App.game_state().set_flag("met_%s" % npc_id)
	var missions := App.missions()
	var active := str(missions.get_active_mission_id())
	if not active.is_empty():
		var def: MissionDef = missions.get_def(active)
		var obj: MissionObjectiveDef = missions.get_current_objective(active)
		if obj != null and obj.condition_type() == "talk_to" and obj.condition_value() == npc_id:
			_request(def.dialogue_lines(obj.id), "obj:%s:%s" % [active, obj.id])
			return
		if def.start_npc == npc_id:
			var lines := def.dialogue_lines("reminder")
			if obj != null:
				lines = lines + [{"who": npc_id, "text": "Objetivo: %s" % obj.description}]
			_request(lines, "info")
			return
	else:
		for id in missions.ordered_mission_ids():
			var def: MissionDef = missions.get_def(id)
			if def.start_npc == npc_id and missions.can_start(id) and missions.requirements_met(id):
				_request(def.dialogue_lines("offer"), "offer:%s" % id)
				return
	var after := _after_lines(npc_id)
	if not after.is_empty():
		_request(after, "info")
		return
	var character := _characters.get_def(npc_id)
	if character != null:
		_request(character.idle_dialogue(), "info")


## HAL comenta algo (bloqueos, pistas). No cambia el estado.
func mark_met(character_id: String) -> void:
	App.game_state().set_flag("met_%s" % character_id)


func has_met(character_id: String) -> bool:
	return character_id in ["andres", HAL_ID] or App.game_state().has_flag("met_%s" % character_id)


func hal_says(text: String) -> void:
	_request([{"who": HAL_ID, "text": text}], "info")


func play_lines(lines: Array, context: String = "info") -> void:
	_request(lines, context)


func _after_lines(npc_id: String) -> Array:
	var missions := App.missions()
	var ids: PackedStringArray = missions.ordered_mission_ids()
	for i in range(ids.size() - 1, -1, -1):
		var def: MissionDef = missions.get_def(ids[i])
		if def.start_npc == npc_id and missions.is_completed(ids[i]):
			return def.dialogue_lines("after")
	return []


func _request(lines: Array, context: String) -> void:
	if lines.is_empty():
		_on_dialogue_finished(context)
		return
	var first: Dictionary = lines[0] if typeof(lines[0]) == TYPE_DICTIONARY else {}
	var speaker := _characters.display_name(str(first.get("who", "")))
	App.bus().dialogue_requested.emit(speaker, lines, context)


func _on_dialogue_finished(context: String) -> void:
	var missions := App.missions()
	if context.begins_with("offer:"):
		var mission_id := context.trim_prefix("offer:")
		if missions.start_mission(mission_id):
			var def: MissionDef = missions.get_def(mission_id)
			var msg := "Misión iniciada: %s" % def.title
			App.bus().mission_status_message.emit(msg)
			App.sfx().play("confirm")
	elif context.begins_with("obj:"):
		var parts := context.split(":")
		if parts.size() == 3:
			missions.complete_objective(parts[1], parts[2])


func _on_mission_completed(mission_id: String) -> void:
	App.sfx().play("success")
	var def: MissionDef = App.missions().get_def(mission_id)
	_auto_start_missions()
	var chapter := current_chapter()
	if chapter != _last_chapter:
		_last_chapter = chapter
		App.bus().chapter_changed.emit(chapter)
	if def != null and not def.on_complete_event.is_empty():
		App.bus().story_event.emit(def.on_complete_event)
	_emit_nav_target()
