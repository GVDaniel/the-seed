extends SceneTree
## Recorre la historia completa (capítulos 1–3) solo con eventos, sin escenas.
## godot --headless --path game --script res://tests/story_test.gd

var _failed: int = 0
var _last_context: String = ""
var _last_lines: Array = []
var _events: PackedStringArray = PackedStringArray()


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	print("[story] start")
	var bus: Node = root.get_node("EventBus")
	var story: Node = root.get_node("StoryDirector")
	var missions: Node = root.get_node("MissionLog")
	var gs: Node = root.get_node("GameState")
	bus.dialogue_requested.connect(func(_s: String, lines: Array, ctx: String) -> void:
		_last_context = ctx
		_last_lines = lines
	)
	bus.story_event.connect(func(id: String) -> void: _events.append(id))

	story.new_game()
	_check(missions.get_active_mission_id() == "last_seed", "nueva partida activa last_seed")
	_check(int(story.current_chapter()) == 1, "capítulo 1 al empezar")
	_check(not story.can_take_off("earth"), "no se puede despegar al inicio")
	_check(not story.can_land("moon"), "Luna bloqueada al inicio")
	_check(story.characters().size() >= 6, "personajes cargados")

	# --- Capítulo 1
	_talk(story, bus, "lucia")
	_check(_current(missions) == "scan_dead_plant", "tras hablar con Lucía → escanear planta")
	_check(not story.can_collect("the_seed"), "no se puede recoger La Semilla todavía")
	bus.scan_completed.emit("earth_dead_plant", true)
	bus.scan_completed.emit("earth_air_sensor", true)
	_talk(story, bus, "lucia")
	_check(_current(missions) == "collect_seed", "tras el informe → recoger semilla")
	_check(story.can_collect("the_seed"), "ahora sí se puede recoger")
	gs.add_item("the_seed")
	bus.item_collected.emit("the_seed")
	_check(not story.can_take_off("earth"), "sin programa no se despega")
	bus.challenge_solved.emit("launch_sequence")
	_check(story.can_take_off("earth"), "con programa se puede despegar")
	bus.took_off.emit("earth")
	_check(missions.is_completed("last_seed"), "capítulo 1 completado")
	_check(int(story.current_chapter()) == 2, "capítulo 2 tras despegar")

	# --- Capítulo 2: Aurora → Luna
	var summary: Dictionary = story.objective_summary()
	_check(str(summary.get("target", "")) == "vega", "la flecha apunta a Vega")
	_talk(story, bus, "vega")
	_check(_last_context == "offer:signal_from_moon", "Vega ofrece la misión")
	_check(missions.get_active_mission_id() == "signal_from_moon", "misión de la señal activa")
	story.notify_near("moon")
	bus.scan_completed.emit("lunar_probe_signal", true)
	_talk(story, bus, "vega")
	_check(missions.is_completed("signal_from_moon"), "señal entregada")
	_check(story.can_land("moon"), "Luna desbloqueada")
	_check(not story.can_land("mars"), "Marte aún bloqueado")
	_talk(story, bus, "kai")
	_check(missions.get_active_mission_id() == "ice_of_shackleton", "Kai ofrece el hielo")
	_check(not story.is_current_objective("solve_challenge", "ice_drill"), "taladro antes de escanear: bloqueado")
	bus.scan_completed.emit("moon_ice_crater", true)
	bus.challenge_solved.emit("ice_drill")
	_talk(story, bus, "kai")
	_check(missions.is_completed("ice_of_shackleton"), "hielo entregado")
	_check(story.can_land("mars"), "Marte desbloqueado")

	# --- Capítulo 3: Marte
	_talk(story, bus, "osei")
	_check(missions.get_active_mission_id() == "red_garden", "Osei ofrece el jardín rojo")
	_check(int(story.current_chapter()) == 3, "capítulo 3")
	_check(not story.can_interact("mars_greenhouse"), "invernadero bloqueado al inicio")
	bus.scan_completed.emit("mars_delta", true)
	bus.scan_completed.emit("mars_rover", true)
	bus.challenge_solved.emit("delta_samples")
	_check(story.can_interact("mars_greenhouse"), "invernadero disponible")
	bus.world_interacted.emit("mars_greenhouse")
	_talk(story, bus, "osei")
	_check(missions.is_completed("red_garden"), "capítulo 3 completado")
	_check(_events.has("ending_teaser"), "evento final emitido")
	_check(root.get_node("ScienceNotebook").is_discovered("trappist1e"), "TRAPPIST-1e en el cuaderno")
	_check(int(gs.experience) >= 340, "XP acumulada (%d)" % int(gs.experience))

	# Diálogo tras completar: líneas "after"
	_talk(story, bus, "lucia", false)
	_check(_last_context == "info" and not _last_lines.is_empty(), "Lucía tiene líneas posteriores")

	story.new_game()
	if _failed == 0:
		print("[story] PASS")
		quit(0)
	else:
		printerr("[story] FAIL (%d)" % _failed)
		quit(1)


func _talk(story: Node, bus: Node, npc: String, finish: bool = true) -> void:
	_last_context = ""
	story.talk_to(npc)
	if finish and not _last_context.is_empty():
		bus.dialogue_finished.emit(_last_context)


func _current(missions: Node) -> String:
	var id := str(missions.get_active_mission_id())
	if id.is_empty():
		return ""
	var obj: MissionObjectiveDef = missions.get_current_objective(id)
	return obj.id if obj != null else ""


func _check(ok: bool, label: String) -> void:
	if ok:
		print("[story] OK  %s" % label)
	else:
		printerr("[story] FAIL %s" % label)
		_failed += 1
