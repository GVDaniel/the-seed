extends SceneTree
## Valida carga de escena ASTRA, stats y nodos críticos.
## godot --headless --path game --script res://tests/astra_prototype_test.gd


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var failed := 0
	print("[astra] prototype check — start")

	var stats := load("res://resources/ship_stats_astra.tres") as ShipStats
	if stats == null or stats.ship_name != "ASTRA":
		printerr("[astra] FAIL: ship_stats_astra.tres")
		failed += 1
	else:
		print("[astra] ShipStats OK (%s max_speed=%.0f)" % [stats.ship_name, stats.max_speed])

	var walker_stats := load("res://resources/walker_stats_cadet.tres") as WalkerStats
	if walker_stats == null:
		printerr("[astra] FAIL: walker_stats")
		failed += 1
	else:
		print("[astra] WalkerStats OK")

	var packed := load("res://scenes/space/space_main.tscn") as PackedScene
	if packed == null:
		printerr("[astra] FAIL: no se pudo cargar space_main.tscn")
		failed += 1
		_finish(failed)
		return

	var root := packed.instantiate()
	root.name = "SpaceMainTest"
	root_node_add(root)

	await process_frame
	await process_frame

	var ship := root.get_node_or_null("World/AstraShip") as ShipController
	var cam := root.get_node_or_null("FollowCamera") as FollowCamera
	var director := root.get_node_or_null("SpaceDirector") as SpaceDirector
	var planet := root.get_node_or_null("World/Earth") as PlanetZone
	var hud := root.get_node_or_null("FlightHud")

	if ship == null:
		printerr("[astra] FAIL: AstraShip ausente")
		failed += 1
	if cam == null:
		printerr("[astra] FAIL: FollowCamera ausente")
		failed += 1
	if director == null:
		printerr("[astra] FAIL: SpaceDirector ausente")
		failed += 1
	if planet == null or planet.get_stable_id() != "earth":
		printerr("[astra] FAIL: Tierra ausente o id incorrecto")
		failed += 1
	if hud == null:
		printerr("[astra] FAIL: FlightHud ausente")
		failed += 1

	if ship != null and cam != null and director != null:
		if director.mode != SpaceDirector.Mode.SPACE:
			printerr("[astra] FAIL: modo inicial no es SPACE")
			failed += 1
		if cam.target != ship:
			printerr("[astra] FAIL: cámara no sigue a la nave al inicio")
			failed += 1
		else:
			print("[astra] Cámara → nave OK")

		# Simula un impulso de thrust programático
		var axis := ship.get_control_axis()
		axis.set_virtual_thrust(1.0)
		ship.consume_input = false
		for i in 10:
			ship._apply_steering(0.016)
		if ship.velocity.length() <= 0.0:
			printerr("[astra] FAIL: la nave no aceleró con thrust virtual")
			failed += 1
		else:
			print("[astra] Thrust virtual OK (speed=%.1f)" % ship.velocity.length())

	root.queue_free()
	await process_frame
	_finish(failed)


func root_node_add(node: Node) -> void:
	root.add_child(node)


func _finish(failed: int) -> void:
	if failed == 0:
		print("[astra] PASS")
		quit(0)
	else:
		printerr("[astra] FAIL (%d)" % failed)
		quit(1)
