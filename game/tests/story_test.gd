extends SceneTree
## Recorre la historia completa (capítulos 1–4 y misiones secundarias) solo con eventos, sin escenas.
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
	_check(not _events.has("ending_teaser"), "el final ya no llega en el capítulo 3")
	_check(root.get_node("ScienceNotebook").is_discovered("trappist1e"), "TRAPPIST-1e en el cuaderno")
	_check(int(gs.experience) >= 340, "XP acumulada (%d)" % int(gs.experience))
	_chapter_four(bus, story, missions, gs)

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


func _chapter_four(bus: Node, story: Node, missions: Node, gs: Node) -> void:
	var ship: Node = root.get_node("ShipState")
	var inv: Node = root.get_node("Inventory")
	_check(int(story.current_chapter()) == 4, "capítulo 4 disponible")
	_check(str(story.objective_summary().get("target", "")) == "bruno", "la flecha lleva a Bruno")
	_check(str(story.objective_summary().get("location", "")) == "mars_garage", "Bruno está en su taller")
	_check(str(ship.engine_id) == "old_chemical", "ASTRA empieza con el motor viejo")
	# Secundaria aceptada antes que la principal: corren en paralelo.
	_talk(story, bus, "yusuf")
	_check(_last_context == "offer:side_ice_core" and missions.is_active("side_ice_core"), "Yusuf ofrece una secundaria")
	_check(str(missions.get_active_mission_id()).is_empty(), "una secundaria no ocupa el hueco de la principal")
	_talk(story, bus, "bruno")
	_check(missions.get_active_mission_id() == "methane_heart", "Bruno ofrece «Corazón de metano»")
	_check(missions.is_active("side_ice_core"), "la secundaria sigue activa")
	_check(not story.can_collect("methane_engine"), "el motor está custodiado")
	_check(story.can_battle("sentinel_ah7") and not story.can_battle("drones_meteorite"), "solo se combate cuando la misión lo pide")
	bus.battle_finished.emit("sentinel_ah7", "retreat")
	_check(_current(missions) == "win_sentinel", "retirarse no completa el objetivo")
	var xp := int(gs.experience)
	bus.battle_finished.emit("sentinel_ah7", "victory")
	_check(_current(missions) == "take_engine" and int(gs.experience) >= xp + 60, "victoria → recoger el motor (+60 XP)")
	_check(inv.has("orders_chip"), "chip de órdenes antihumanista")
	bus.battle_finished.emit("sentinel_ah7", "victory")
	_check(int(gs.experience) < xp + 120 + 1, "la recompensa del combate se da una vez")
	gs.add_item("methane_engine")
	bus.item_collected.emit("methane_engine")
	_check(_current(missions) == "install_engine" and str(story.nav_candidates()[0]) == "mars_workbench", "→ instalar en el banco del taller")
	bus.world_interacted.emit("mars_workbench")
	_check(str(ship.engine_id) == "methane_engine" and ship.is_empty(), "motor de metano instalado, tanque vacío")
	_check(not inv.has("methane_engine"), "el motor sale del inventario (va en la nave)")
	_check(not story.can_take_off("mars"), "sin metano no se despega")
	_check(_current(missions) == "gather_ingredients", "faltan los ingredientes")
	_check(str(story.objective_summary().get("hint", "")).contains("Faltan"), "el HUD lista lo que falta")
	_check(str(story.objective_summary().get("target", "")) == "mars_buried_ice", "la flecha guía a la secundaria activa")
	# Secundaria 1: hielo (Yusuf)
	bus.scan_completed.emit("mars_buried_ice", true)
	_check(story.can_collect("mars_ice_core"), "se puede sacar el testigo de hielo")
	gs.add_item("mars_ice_core")
	bus.item_collected.emit("mars_ice_core")
	_talk(story, bus, "yusuf")
	_check(missions.is_completed("side_ice_core"), "secundaria del hielo completada")
	# Secundaria 2: CO₂ (Nia) — el compresor entrega el tanque.
	_talk(story, bus, "nia")
	_check(missions.is_active("side_co2"), "Nia ofrece el CO₂")
	bus.world_interacted.emit("co2_compressor")
	_check(inv.has("co2_tank"), "el compresor llena el tanque de CO₂")
	_talk(story, bus, "nia")
	_check(missions.is_completed("side_co2"), "secundaria del CO₂ completada")
	# Secundaria 3: níquel (Ada) — con combate.
	_talk(story, bus, "ada")
	_check(missions.is_active("side_catalyst"), "Ada ofrece el níquel")
	bus.scan_completed.emit("mars_iron_meteorite", true)
	_check(story.can_battle("drones_meteorite"), "los drones custodian el meteorito")
	bus.battle_finished.emit("drones_meteorite", "victory")
	gs.add_item("nickel_catalyst")
	bus.item_collected.emit("nickel_catalyst")
	_check(_current(missions) == "distill_fuel", "con los tres ingredientes → destilar")
	_talk(story, bus, "ada")
	_check(missions.is_completed("side_catalyst"), "secundaria del níquel completada")
	bus.world_interacted.emit("methane_distiller")
	_check(not ship.is_empty() and is_equal_approx(float(ship.fuel), float(ship.capacity())), "tanque de metano lleno (%d)" % int(ship.fuel))
	_check(gs.has_flag("methane_distilled") and not inv.has("co2_tank"), "ingredientes gastados en el destilador")
	_check(story.can_take_off("mars"), "ya se puede despegar")
	_talk(story, bus, "osei")
	_check(missions.is_completed("methane_heart"), "capítulo 4 · parte 1 completado")
	_check(_events.has("ending_teaser"), "evento final tras «Corazón de metano»")
	_check(root.get_node("ScienceNotebook").is_discovered("sabatier_methane"), "ficha de la reacción de Sabatier")


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
