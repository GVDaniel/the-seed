extends SceneTree
## HAL: inventario y entregas por eventos, música, buses de audio e interfaz con pestañas.
## godot --headless --path game --script res://tests/hal_test.gd

var _failed: int = 0
var _toggles: Array = []


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	print("[hal] start")
	var story: Node = root.get_node("StoryDirector")
	var bus: Node = root.get_node("EventBus")
	var inventory: Node = root.get_node("Inventory")
	var gs: Node = root.get_node("GameState")
	story.new_game()

	# --- Inventario
	var owned: Array = inventory.owned()
	_check(owned.size() == 2 and owned[0].id == "suit" and owned[1].id == "scanner", "equipo inicial: traje y escáner")
	_check(not inventory.has("the_seed"), "sin La Semilla al empezar")
	var catalog: ItemCatalog = inventory.catalog()
	for def in catalog.all():
		_check(ResourceLoader.exists(def.icon_path), "icono de %s" % def.id)
		_check(not def.fact.is_empty(), "dato real en %s" % def.id)
	var toasts: Array = []
	bus.mission_status_message.connect(func(t: String) -> void: toasts.append(t))
	bus.challenge_solved.emit("launch_sequence")
	_check(inventory.has("launch_program"), "resolver el despegue entrega el programa")
	bus.challenge_solved.emit("launch_sequence")
	_check(toasts.filter(func(t: String) -> bool: return t.contains("Programa de despegue")).size() == 1, "aviso solo la primera vez")
	bus.scan_completed.emit("lunar_probe_signal", true)
	_check(inventory.has("probe_data"), "escanear la señal entrega los datos")
	_check(inventory.owned()[-1].id == "probe_data", "orden del catálogo respetado")

	# --- Tripulación
	_check(story.has_met("andres") and story.has_met("hal"), "Andrés y HAL siempre conocidos")
	_check(not story.has_met("kai"), "Kai desconocido al inicio")
	story.talk_to("kai")
	bus.dialogue_finished.emit("info")
	_check(story.has_met("kai"), "hablar registra a Kai")
	var crew: Array = story.characters().all()
	_check(crew.size() >= 19 and crew[0].id == "andres" and crew[1].id == "hal", "personajes ordenados (%d)" % crew.size())
	_check(crew.filter(func(c: CharacterDef) -> bool: return c.group == "crew").size() == 6, "equipo de 6 + vecinos")

	# --- Música y audio
	for track in ["space", "mission", "title"]:
		var stream := MusicPlayerScript().load_track(track) as AudioStreamOggVorbis
		_check(stream != null and stream.loop, "pista %s en bucle" % track)
		if stream != null:
			_check(stream.get_length() > 20.0, "pista %s dura %.0f s" % [track, stream.get_length()])
	_check(AudioServer.get_bus_index("Music") != -1 and AudioServer.get_bus_index("SFX") != -1, "buses Music y SFX")
	root.get_node("Music").play("title")
	_check(str(root.get_node("Music").current_track) == "title", "Music recuerda la pista")

	# --- Interfaz en una superficie real
	story.new_game()
	root.get_node("Router").pending_surface = "earth"
	root.get_node("Router").pending_spawn = "start"
	var level := (load("res://scenes/surface/surface_level.tscn") as PackedScene).instantiate() as SurfaceLevel
	root.add_child(level)
	await process_frame
	await process_frame
	_check(str(root.get_node("Music").current_track) == "mission", "la superficie pone la música de misión")
	bus.dialogue_finished.emit("info") # bienvenida de HAL
	var hal := level.get_node("%HalInterface") as HalInterface
	bus.hal_interface_toggled.connect(func(open: bool) -> void: _toggles.append(open))
	_check(hal.can_open(), "HAL disponible a pie")
	_press(KEY_TAB)
	await process_frame
	_check(hal.is_open(), "Tab entra en HAL")
	await process_frame
	_check(not (level.get_node("%Player") as WalkerController).consume_input, "Andrés no se mueve con HAL abierta")
	for id in HalInterface.TAB_IDS:
		hal._select(id)
		await process_frame
		_check(hal.current_tab() == id, "pestaña %s" % id)
	_press(KEY_Q)
	_check(hal.current_tab() == "crew", "Q vuelve a la pestaña anterior")
	_press(KEY_2)
	_check(hal.current_tab() == "map", "2 abre el mapa")
	var map_tab := hal._tabs["map"] as HalMapTab
	_check(map_tab._minimap.has_map() and map_tab._minimap.visible, "mapa «Aquí» de la Tierra")
	_check(map_tab._route.objective_stop() == "earth", "la ruta marca la Tierra como objetivo")
	_press(KEY_M)
	_check(not hal.is_open(), "M sobre el mapa cierra HAL")
	_press(KEY_N)
	_check(hal.is_open() and hal.current_tab() == "notes", "N abre el cuaderno")
	_press(KEY_ESCAPE)
	_check(not hal.is_open(), "Esc sale de HAL")
	_check(_toggles == [true, false, true, false], "avisos de apertura y cierre (%s)" % str(_toggles))
	story.talk_to("lucia")
	_press(KEY_TAB)
	_check(not hal.is_open(), "no se abre durante un diálogo")
	bus.dialogue_finished.emit("obj:last_seed:talk_lucia")
	bus.hal_interface_requested.emit("inventory")
	_check(hal.is_open() and hal.current_tab() == "inventory", "el botón del HUD abre el inventario")
	hal.close()
	level.queue_free()
	await process_frame

	story.new_game()
	if _failed == 0:
		print("[hal] PASS")
		quit(0)
	else:
		printerr("[hal] FAIL (%d)" % _failed)
		quit(1)


func MusicPlayerScript() -> GDScript:
	return load("res://scripts/autoload/music_player.gd")


func _press(keycode: Key) -> void:
	var ev := InputEventKey.new()
	ev.keycode = keycode
	ev.physical_keycode = keycode
	ev.pressed = true
	root.push_input(ev)
	var up := ev.duplicate() as InputEventKey
	up.pressed = false
	root.push_input(up)


func _check(ok: bool, label: String) -> void:
	if ok:
		print("[hal] OK  %s" % label)
	else:
		printerr("[hal] FAIL %s" % label)
		_failed += 1
