extends Node
## Hilo narrativo: traduce eventos del mundo (hablar, escanear, recoger, programar,
## aterrizar, combatir) en avances de misión y elige qué dice cada personaje.
## Una misión principal a la vez y varias secundarias en paralelo.
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
	bus.battle_finished.connect(_on_battle_finished)
	bus.mission_objective_completed.connect(_on_objective_completed)
	bus.mission_completed.connect(_on_mission_completed)
	bus.item_collected.connect(func(_id: String) -> void: _check_have_items())
	bus.mission_started.connect(func(_id: String) -> void:
		_check_have_items()
		_emit_nav_target())
	bus.mission_updated.connect(func(_id: String) -> void:
		_check_have_items()
		_emit_nav_target())
	_last_chapter = current_chapter()


func characters() -> CharacterCatalog:
	return _characters


# ------------------------------------------------------------ partida

func new_game() -> void:
	App.game_state().reset_progress()
	App.hero().reset()
	App.ship().reset()
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
		if def.is_side():
			continue
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
		if def.is_side():
			continue
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
		var summary := {
			"title": def.title,
			"hint": obj.hud_hint if obj != null else "",
			"chapter": def.chapter,
			"target": obj.target if obj != null else "",
			"location": obj.location if obj != null else "",
		}
		if obj != null and obj.condition_type() == "have_items":
			summary["hint"] = "%s Faltan: %s." % [obj.hud_hint, ", ".join(missing_items(obj))]
			var side := side_nav()
			if not side.is_empty():
				summary["target"] = side.get("target", "")
				summary["location"] = side.get("location", "")
		return summary
	for id in missions.ordered_mission_ids():
		var def: MissionDef = missions.get_def(id)
		if def.is_side():
			continue
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


## Misiones secundarias activas para el HUD: [{id, title, hint, target, location}].
func side_summaries() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var missions := App.missions()
	for id in missions.active_side_mission_ids():
		var def: MissionDef = missions.get_def(id)
		var obj: MissionObjectiveDef = missions.get_current_objective(id)
		if obj == null:
			continue
		out.append({"id": id, "title": def.title, "hint": obj.hud_hint, "target": obj.target,
			"location": obj.location})
	return out


## Secundarias que se pueden aceptar ahora: [{id, title, npc}].
func side_offers() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var missions := App.missions()
	for id in missions.ordered_mission_ids():
		var def: MissionDef = missions.get_def(id)
		if def.is_side() and missions.can_start(id) and missions.requirements_met(id):
			out.append({"id": id, "title": def.title, "npc": def.start_npc})
	return out


## Adónde apuntar cuando la principal espera a las secundarias.
func side_nav() -> Dictionary:
	var active := side_summaries()
	if not active.is_empty():
		return active[0]
	var offers := side_offers()
	if not offers.is_empty():
		var npc := str(offers[0]["npc"])
		return {"target": npc, "location": _npc_location(npc)}
	return {}


func missing_items(obj: MissionObjectiveDef) -> PackedStringArray:
	var out := PackedStringArray()
	for item_id in obj.item_ids():
		if not App.inventory().has(item_id):
			var def: ItemDef = App.inventory().catalog().get_def(item_id)
			out.append(def.display_name if def != null else item_id)
	return out


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
	var ship := App.ship()
	if ship.is_empty() and not ship.fuel_available():
		return "El motor de metano tiene el tanque vacío. Bruno dice que hay que destilar metano en su taller."
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


## Solo se combate cuando una misión lo pide (no hay peleas aleatorias).
func can_battle(encounter_id: String) -> bool:
	return _is_current("win_battle", encounter_id)


func is_current_objective(type: String, value: String) -> bool:
	return _is_current(type, value)


func _is_current(type: String, value: String) -> bool:
	return not _current_owner(type, value).is_empty()


## Misión activa (principal primero) cuyo objetivo actual es type/value.
func _current_owner(type: String, value: String) -> String:
	var missions := App.missions()
	for id in missions.active_mission_ids():
		var obj: MissionObjectiveDef = missions.get_current_objective(id)
		if obj != null and obj.condition_type() == type and obj.condition_value() == value:
			return id
	return ""


## Llamado desde el espacio cuando la nave entra en el anillo de un destino.
func notify_near(destination_id: String) -> void:
	_try_complete("near_destination", destination_id)


func _try_complete(type: String, value: String) -> bool:
	var owner := _current_owner(type, value)
	if owner.is_empty():
		return false
	var missions := App.missions()
	var obj: MissionObjectiveDef = missions.get_current_objective(owner)
	return missions.complete_objective(owner, obj.id)


func _check_have_items() -> void:
	var missions := App.missions()
	for id in missions.active_mission_ids():
		var obj: MissionObjectiveDef = missions.get_current_objective(id)
		if obj == null or obj.condition_type() != "have_items":
			continue
		if missing_items(obj).is_empty():
			missions.complete_objective(id, obj.id)
			return


func _on_objective_completed(_mission_id: String, objective_id: String) -> void:
	var obj := _find_objective(_mission_id, objective_id)
	if obj == null or obj.effects.is_empty():
		return
	var fx := obj.effects
	var gs := App.game_state()
	if fx.has("set_flag"):
		gs.set_flag(str(fx["set_flag"]))
	for item_id in fx.get("consume_items", []):
		gs.remove_item(str(item_id))
	if fx.has("install_engine"):
		App.ship().install_engine(str(fx["install_engine"]))
		gs.remove_item(str(fx["install_engine"]))
	if bool(fx.get("refuel", false)):
		App.ship().fill_fuel()
	if bool(fx.get("repair", false)):
		App.ship().repair(100.0)


func _find_objective(mission_id: String, objective_id: String) -> MissionObjectiveDef:
	var def: MissionDef = App.missions().get_def(mission_id)
	return def.get_objective(objective_id) if def != null else null


func _on_battle_finished(encounter_id: String, result: String) -> void:
	if result != "victory":
		return
	var flag := "won_%s" % encounter_id
	var first_time: bool = not App.game_state().has_flag(flag)
	App.game_state().set_flag(flag)
	if first_time:
		var rewards: Dictionary = EncounterCatalog.load_encounter(encounter_id).get("rewards", {})
		App.game_state().add_experience(int(rewards.get("experience", 0)))
		var credits := int(rewards.get("credits", 0))
		if credits > 0:
			App.game_state().add_credits(credits)
	_try_complete("win_battle", encounter_id)


# ------------------------------------------------------------ diálogos

## Decide qué dice un personaje según el estado de las misiones.
func talk_to(npc_id: String) -> void:
	App.game_state().set_flag("met_%s" % npc_id)
	var missions := App.missions()
	var active_ids: PackedStringArray = missions.active_mission_ids()
	for id in active_ids:
		var obj: MissionObjectiveDef = missions.get_current_objective(id)
		if obj != null and obj.condition_type() == "talk_to" and obj.condition_value() == npc_id:
			_request((missions.get_def(id) as MissionDef).dialogue_lines(obj.id), "obj:%s:%s" % [id, obj.id])
			return
	var main_free := str(missions.get_active_mission_id()).is_empty()
	for id in missions.ordered_mission_ids():
		var def: MissionDef = missions.get_def(id)
		if def.start_npc != npc_id or not missions.can_start(id) or not missions.requirements_met(id):
			continue
		if def.is_side() or main_free:
			_request(def.dialogue_lines("offer"), "offer:%s" % id)
			return
	for id in active_ids:
		var def: MissionDef = missions.get_def(id)
		if def.start_npc == npc_id:
			var obj: MissionObjectiveDef = missions.get_current_objective(id)
			var lines := def.dialogue_lines("reminder")
			if obj != null:
				lines = lines + [{"who": npc_id, "text": "Objetivo: %s" % obj.description}]
			_request(lines, "info")
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
			var msg := ("Misión secundaria: %s" if def.is_side() else "Misión iniciada: %s") % def.title
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
