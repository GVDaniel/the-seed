extends SceneTree
## Vida ambiental: tráfico (flujo y persistentes), naves del cielo, peatones, tope de entidades,
## que nada choca ni roba la interacción, y que SurfaceLevel crea el sistema.
## godot --headless --path game --script res://tests/ambient_test.gd

var _failed: int = 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	print("[ambient] start")
	_register_test_art()
	await _test_life()
	await _test_cap_and_missing()
	_test_interaction()
	await _test_surface_integration()
	_unregister_test_art()
	if _failed == 0:
		print("[ambient] PASS")
		quit(0)
	else:
		printerr("[ambient] FAIL (%d)" % _failed)
		quit(1)


func _texture(w: int, h: int, color: Color) -> Texture2D:
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(color)
	return ImageTexture.create_from_image(img)


func _register_test_art() -> void:
	AmbientKinds.register("test_taxi", {"texture": _texture(64, 60, Color.YELLOW), "frame": [32, 20], "frames": 2,
		"fps": 6, "rows": {"right": 0, "down": 1, "up": 2}, "shadow": [24, 6],
		"light": {"color": "#3de7c9", "offset": [0, -8], "scale": 1.0, "energy": 0.6}})
	AmbientKinds.register("test_bot", {"texture": _texture(16, 16, Color.GRAY), "frame": [16, 16], "frames": 1})
	AmbientKinds.register("test_ship", {"texture": _texture(96, 36, Color.WHITE), "frame": [96, 36], "frames": 1})
	AmbientKinds.register("crowd:earth", {"sheets": [_texture(48, 96, Color.SKY_BLUE)]})


func _unregister_test_art() -> void:
	for k in ["test_taxi", "test_bot", "test_ship", "crowd:earth"]:
		AmbientKinds.unregister(k)


func _stage() -> Array:
	var world := Node2D.new()
	root.add_child(world)
	var ground := Node2D.new()
	ground.y_sort_enabled = true
	world.add_child(ground)
	var player := Node2D.new()
	player.position = Vector2(400, 400)
	ground.add_child(player)
	return [world, ground, player]


func _test_life() -> void:
	var s := _stage()
	var world: Node2D = s[0]
	var ground: Node2D = s[1]
	var player: Node2D = s[2]
	var map := {"tileset": "earth", "ambient": "#6e6c96", "ambient_life": {
		"movers": [
			{"kinds": ["test_taxi"], "path": [[-3, 5], [12, 5]], "interval": [0.15, 0.25], "speed": 300,
				"altitude": 30, "two_way": true, "lane_offset": 0.6},
			{"kinds": ["test_bot"], "path": [[2, 10], [8, 10], [8, 14]], "count": 1, "speed": 60,
				"altitude": 0, "loop": "pingpong", "pause": [0.1, 0.2]},
			{"kinds": ["test_taxi"], "path": [[2, 2], [10, 2], [6, 8]], "count": 2, "speed": 80,
				"altitude": 26, "loop": "cycle"},
		],
		"sky": {"kinds": ["test_ship"], "interval": [0.1, 0.2], "speed": [200, 300], "rows": [2, 6]},
		"crowd": [{"path": [[3, 20], [15, 20]], "count": 3, "speed": [40, 50], "pause": [0.1, 0.3],
			"barks": ["¿Has visto el precio del aire?"]}],
	}}
	_check(AmbientLife.tint_of(map) == "#6e6c96", "el color de luz ambiente sigue en «ambient»")
	var life := AmbientLife.new()
	world.add_child(life)
	life.setup(map, ground, player, Vector2(960, 540))
	var walkers := _of(ground, "AmbientWalker")
	_check(walkers.size() == 3, "tres peatones en el suelo (%d)" % walkers.size())
	var air := _of(life, "AmbientMover")
	_check(air.size() >= 2, "vehículos volando creados (%d)" % air.size())
	var bot := _of(ground, "AmbientMover")
	_check(bot.size() == 1, "robot a ras de suelo, ordenado con los personajes")
	var low := AmbientMover.new()
	low.setup(AmbientKinds.get_def("test_taxi"), PackedVector2Array([Vector2.ZERO, Vector2(50, 0)]), 10, 10, AmbientMover.FLOW)
	_check(not low.flies_high() and low.z_as_relative, "un aerotaxi bajo se ordena por profundidad con los personajes")
	low.free()
	var bot_start: Vector2 = bot[0].position
	var walker_start: Vector2 = walkers[0].position
	var flying: AmbientMover = air[0]
	_check(flying.z_index >= AmbientMover.AIR_Z and not flying.z_as_relative, "lo que vuela se pinta por encima")
	var flow: AmbientMover = null
	for m in air:
		if (m as AmbientMover).mode == AmbientMover.FLOW:
			flow = m
	var flow_ref: WeakRef = weakref(flow) if flow != null else null
	var bot_moved := 0.0
	for i in 6:
		await create_timer(0.2).timeout
		bot_moved = maxf(bot_moved, bot_start.distance_to(bot[0].position))
	_check(bot_moved > 4.0, "el robot avanza con el tiempo (%.0f px)" % bot_moved)
	_check(walker_start.distance_to(walkers[0].position) > 1.0 or walkers[0].position.distance_to(walkers[1].position) > 0.0,
		"los peatones caminan")
	_check(flow_ref != null and flow_ref.get_ref() == null, "un vehículo de flujo desaparece al final del camino")
	var flows := 0
	var two_way := false
	var ys := {}
	for m in _of(life, "AmbientMover"):
		if (m as AmbientMover).mode == AmbientMover.FLOW and (m as AmbientMover).altitude == 30.0:
			flows += 1
			ys[int((m as AmbientMover).path[0].y)] = true
	two_way = ys.size() >= 2
	_check(flows > 0, "el flujo sigue generando vehículos (%d)" % flows)
	_check(two_way, "doble sentido con carril desplazado")
	var sky := 0
	for m in _of(life, "AmbientMover"):
		if (m as AmbientMover).z_index == AmbientLife.SKY_Z:
			sky += 1
	_check(sky > 0, "naves cruzando el cielo (%d)" % sky)
	var w: AmbientWalker = walkers[0]
	_check(_has_collision(w) == false and not w.is_in_group(Interactable.GROUP), "los peatones no chocan ni se pueden usar con E")
	w.say("Hola")
	_check(w.is_saying(), "un peatón puede decir algo en un bocadillo")
	world.queue_free()
	await process_frame


func _test_cap_and_missing() -> void:
	var s := _stage()
	var world: Node2D = s[0]
	var map := {"tileset": "earth", "ambient_life": {
		"movers": [{"kinds": ["no_existe"], "path": [[0, 0], [5, 0]], "interval": [0.1, 0.1]},
			{"kinds": ["test_bot"], "path": [[0, 0], [5, 0]], "count": 30, "speed": 10}],
		"crowd": [{"path": [[0, 3], [9, 3]], "count": 30}],
	}}
	var life := AmbientLife.new()
	world.add_child(life)
	life.setup(map, s[1], s[2], Vector2(320, 320))
	_check(life.live_count() == AmbientLife.MAX_LIVE, "tope de %d entidades vivas (%d)" % [AmbientLife.MAX_LIVE, life.live_count()])
	var nodes := _of(s[1], "AmbientMover").size() + _of(s[1], "AmbientWalker").size() + _of(life, "AmbientMover").size()
	_check(nodes == AmbientLife.MAX_LIVE,
		"no se crean más nodos que el tope (%d)" % nodes)
	await create_timer(0.3).timeout
	_check(life.live_count() <= AmbientLife.MAX_LIVE, "un kind sin arte se ignora sin errores")
	var empty := AmbientLife.new()
	world.add_child(empty)
	empty.setup({"tileset": "mars", "ambient": "#ffaa88"}, s[1], s[2], Vector2(320, 320))
	_check(empty.live_count() == 0, "mapa sin vida ambiental: nada")
	world.queue_free()
	await process_frame


func _test_interaction() -> void:
	var s := _stage()
	var world: Node2D = s[0]
	var ground: Node2D = s[1]
	var player: Node2D = s[2]
	var npc := Interactable.new()
	npc.target_id = "lucia"
	npc.kind = "npc"
	npc.radius = 28.0
	npc.position = player.position + Vector2(20, 0)
	ground.add_child(npc)
	var life := AmbientLife.new()
	world.add_child(life)
	life.setup({"tileset": "earth", "ambient_life": {"crowd": [{"path": [[25, 25], [25, 25]], "count": 3,
		"barks": ["Hola"]}]}}, ground, player, Vector2(960, 960))
	for w in _of(ground, "AmbientWalker"):
		(w as Node2D).position = player.position + Vector2(4, 0)
	var sys := InteractionSystem.new()
	world.add_child(sys)
	sys._player = player
	_check(sys._find_nearest() == npc, "con peatones encima, E sigue siendo para el NPC de la historia")
	world.queue_free()


func _test_surface_integration() -> void:
	var router: Node = root.get_node("Router")
	root.get_node("StoryDirector").new_game()
	router.pending_surface = "earth"
	router.pending_spawn = "start"
	change_scene_to_file("res://scenes/surface/surface_level.tscn")
	for i in 30:
		await process_frame
	var level := current_scene as SurfaceLevel
	_check(level != null and level.ambient != null, "SurfaceLevel crea la vida ambiental")
	var tint := (level.get_node("%Ambient") as CanvasModulate).color
	_check(tint == Color(AmbientLife.tint_of(level.map)), "la luz ambiente del mapa no cambia")
	_check(level.get_node("%Player") != null, "el jugador sigue en el mapa")


func _of(node: Node, cls: String) -> Array:
	var out: Array = []
	for c in node.get_children():
		if c.get_script() != null and (c.get_script() as Script).get_global_name() == cls and not c.is_queued_for_deletion():
			out.append(c)
	return out


func _has_collision(node: Node) -> bool:
	for c in node.get_children():
		if c is CollisionObject2D or _has_collision(c):
			return true
	return false


func _check(ok: bool, label: String) -> void:
	if ok:
		print("[ambient] OK  ", label)
	else:
		_failed += 1
		printerr("[ambient] FAIL ", label)
