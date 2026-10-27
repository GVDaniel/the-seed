extends Node
## Catálogo y progreso de misiones. Persistente en disco.

const SAVE_PATH := "user://the_seed_missions.cfg"
const DATA_DIR := "res://assets/data/missions/"

signal mission_started(mission_id: String)
signal mission_completed(mission_id: String)
signal objective_completed(mission_id: String, objective_id: String)
signal mission_updated(mission_id: String)
signal status_message(text: String)

var _defs: Dictionary = {} # id -> MissionDef
var _states: Dictionary = {} # id -> MissionState


func _ready() -> void:
	_load_defs()
	_ensure_states()
	load_local()


func get_def(mission_id: String) -> MissionDef:
	return _defs.get(mission_id, null) as MissionDef


func get_state(mission_id: String) -> MissionState:
	return _states.get(mission_id, null) as MissionState


func all_mission_ids() -> PackedStringArray:
	return PackedStringArray(_defs.keys())


## Ids en orden narrativo (capítulo, orden).
func ordered_mission_ids() -> PackedStringArray:
	var defs: Array = _defs.values()
	defs.sort_custom(func(a: MissionDef, b: MissionDef) -> bool:
		if a.chapter != b.chapter:
			return a.chapter < b.chapter
		return a.order < b.order
	)
	var ids := PackedStringArray()
	for def in defs:
		ids.append((def as MissionDef).id)
	return ids


func is_completed(mission_id: String) -> bool:
	var state := get_state(mission_id)
	return state != null and state.status == MissionState.Status.COMPLETED


func requirements_met(mission_id: String) -> bool:
	var def := get_def(mission_id)
	if def == null:
		return false
	for req in def.requires:
		if not is_completed(req):
			return false
	return true


## Misión principal activa (las secundarias van aparte).
func get_active_mission_id() -> String:
	for id in ordered_mission_ids():
		var st: MissionState = _states[id]
		if st.status == MissionState.Status.ACTIVE and not get_def(id).is_side():
			return id
	return ""


func active_side_mission_ids() -> PackedStringArray:
	var out := PackedStringArray()
	for id in ordered_mission_ids():
		var st: MissionState = _states[id]
		if st.status == MissionState.Status.ACTIVE and get_def(id).is_side():
			out.append(id)
	return out


## Todas las activas: la principal primero.
func active_mission_ids() -> PackedStringArray:
	var out := PackedStringArray()
	var main := get_active_mission_id()
	if not main.is_empty():
		out.append(main)
	out.append_array(active_side_mission_ids())
	return out


func is_active(mission_id: String) -> bool:
	var state := get_state(mission_id)
	return state != null and state.status == MissionState.Status.ACTIVE


func get_current_objective(mission_id: String) -> MissionObjectiveDef:
	var def := get_def(mission_id)
	var state := get_state(mission_id)
	if def == null or state == null or state.status != MissionState.Status.ACTIVE:
		return null
	for obj in def.objectives:
		if not state.is_objective_done(obj.id):
			return obj
	return null


func can_start(mission_id: String) -> bool:
	var state := get_state(mission_id)
	return state != null and state.status == MissionState.Status.AVAILABLE


func start_mission(mission_id: String) -> bool:
	if not can_start(mission_id):
		return false
	# Una sola principal a la vez; las secundarias corren en paralelo.
	if not get_def(mission_id).is_side() and not get_active_mission_id().is_empty():
		return false
	var state := get_state(mission_id)
	state.status = MissionState.Status.ACTIVE
	state.completed_objective_ids = PackedStringArray()
	save_local()
	mission_started.emit(mission_id)
	App.bus().mission_started.emit(mission_id)
	mission_updated.emit(mission_id)
	App.bus().mission_updated.emit(mission_id)
	return true


## Completa un objetivo si es el siguiente pendiente. Una sola vez.
func complete_objective(mission_id: String, objective_id: String) -> bool:
	var def := get_def(mission_id)
	var state := get_state(mission_id)
	if def == null or state == null:
		return false
	if state.status != MissionState.Status.ACTIVE:
		return false
	if state.is_objective_done(objective_id):
		return false
	var current := get_current_objective(mission_id)
	if current == null or current.id != objective_id:
		return false
	state.completed_objective_ids.append(objective_id)
	var msg := str(def.objective_complete_messages.get(objective_id, "Objetivo cumplido."))
	status_message.emit(msg)
	App.bus().mission_status_message.emit(msg)
	objective_completed.emit(mission_id, objective_id)
	App.bus().mission_objective_completed.emit(mission_id, objective_id)
	if _all_objectives_done(def, state):
		_finish_mission(def, state)
	else:
		save_local()
		mission_updated.emit(mission_id)
		App.bus().mission_updated.emit(mission_id)
	return true


func _all_objectives_done(def: MissionDef, state: MissionState) -> bool:
	for obj in def.objectives:
		if not state.is_objective_done(obj.id):
			return false
	return true


func _finish_mission(def: MissionDef, state: MissionState) -> void:
	state.status = MissionState.Status.COMPLETED
	var xp := int(def.rewards.get("experience", 0))
	if xp > 0:
		App.game_state().add_experience(xp)
	var unlock_id := str(def.rewards.get("unlock_destination_id", ""))
	if not unlock_id.is_empty():
		App.notebook().record_discovery(unlock_id)
	var done_msg := def.mission_complete_message
	if done_msg.is_empty():
		done_msg = "Misión completada: %s" % def.title
	status_message.emit(done_msg)
	App.bus().mission_status_message.emit(done_msg)
	save_local()
	mission_completed.emit(def.id)
	App.bus().mission_completed.emit(def.id)
	mission_updated.emit(def.id)
	App.bus().mission_updated.emit(def.id)


func _load_defs() -> void:
	_defs.clear()
	var dir := DirAccess.open(DATA_DIR)
	if dir == null:
		push_warning("MissionLog: no se pudo abrir %s" % DATA_DIR)
		return
	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and file_name.ends_with(".json"):
			var path := DATA_DIR.path_join(file_name)
			var raw := FileAccess.get_file_as_string(path)
			var parsed: Variant = JSON.parse_string(raw)
			if typeof(parsed) == TYPE_DICTIONARY:
				var def := MissionDef.from_dict(parsed)
				if not def.id.is_empty():
					_defs[def.id] = def
		file_name = dir.get_next()
	dir.list_dir_end()


func _ensure_states() -> void:
	for id in _defs.keys():
		if not _states.has(id):
			var st := MissionState.new()
			st.mission_id = id
			st.status = MissionState.Status.AVAILABLE
			_states[id] = st


func save_local() -> void:
	var cfg := ConfigFile.new()
	for id in _states.keys():
		var st: MissionState = _states[id]
		cfg.set_value(id, "status", st.status_name())
		cfg.set_value(id, "completed_objective_ids", Array(st.completed_objective_ids))
	var err := cfg.save(SAVE_PATH)
	if err != OK:
		push_warning("MissionLog: no se pudo guardar (%s)" % error_string(err))


func load_local() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	for id in _defs.keys():
		if not cfg.has_section(id):
			continue
		var st: MissionState = _states[id]
		st.status = MissionState.status_from_name(str(cfg.get_value(id, "status", "available")))
		var ids: Array = cfg.get_value(id, "completed_objective_ids", [])
		st.completed_objective_ids = PackedStringArray(ids)


func clear_all_progress_for_tests() -> void:
	for id in _states.keys():
		var st: MissionState = _states[id]
		st.status = MissionState.Status.AVAILABLE
		st.completed_objective_ids = PackedStringArray()
	save_local()
