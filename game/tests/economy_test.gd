extends SceneTree
## Créditos, compras, mejoras de ASTRA y el recorrido real puerta → bar → tienda.
## godot --headless --path game --script res://tests/economy_test.gd

var _failed: int = 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	print("[economy] start")
	var story: Node = root.get_node("StoryDirector")
	var bus: Node = root.get_node("EventBus")
	var gs: Node = root.get_node("GameState")
	var eco: Node = root.get_node("Economy")
	var inventory: Node = root.get_node("Inventory")
	var router: Node = root.get_node("Router")
	story.new_game()

	# --- Ganar créditos
	_check(int(gs.credits) == 30, "30 créditos al empezar")
	bus.challenge_solved.emit("launch_sequence")
	bus.challenge_solved.emit("launch_sequence")
	_check(int(gs.credits) == 55, "reto pagado una sola vez (%d)" % int(gs.credits))
	root.get_node("ScienceNotebook").record_discovery("earth_dead_plant")
	_check(int(gs.credits) == 65, "descubrimiento nuevo +10")
	var missions: Node = root.get_node("MissionLog")
	for obj in missions.get_def("last_seed").objectives:
		missions.complete_objective("last_seed", obj.id)
	_check(missions.is_completed("last_seed") and int(gs.credits) == 125, "misión completada +60 (%d)" % int(gs.credits))

	# --- Comprar
	_check(not str(eco.buy_block_reason("moon_parts", "battery_pack")).is_empty() == false, "batería al alcance (125 ≥ 70)")
	_check(eco.buy("moon_parts", "battery_pack"), "compra de la batería")
	_check(inventory.has("battery_pack") and int(gs.credits) == 55, "batería en el inventario, saldo 55")
	_check(not eco.buy("moon_parts", "battery_pack"), "no se compra dos veces")
	_check(str(eco.buy_block_reason("mars_market", "ion_thruster")).contains("25"), "faltan 25 para el motor iónico")
	_check(not eco.buy("moon_bar", "ion_thruster"), "no se vende en otro sitio")
	var stats := ShipUpgrades.apply(load("res://resources/ship_stats_astra.tres"))
	_check(is_equal_approx(stats.max_energy, 150.0), "ASTRA: energía máxima 150 (%.0f)" % stats.max_energy)
	_check(is_equal_approx((load("res://resources/ship_stats_astra.tres") as ShipStats).max_energy, 100.0), "el .tres original no cambia")
	gs.add_credits(100)
	eco.buy("moon_parts", "whipple_shield")
	_check(is_equal_approx(ShipUpgrades.multiplier("debris_damage"), 0.5), "escudo: mitad de daño")

	# --- Recorrido real: bar de la Luna
	story.new_game()
	router.go_surface("moon_bar", "entrance")
	await _wait_surface("moon_bar")
	var bar := current_scene as SurfaceLevel
	_check(str(gs.region) == "moon", "el bar pertenece a la Luna")
	_check(str(root.get_node("Music").current_track) == "cantina", "música de cantina")
	bus.dialogue_finished.emit("info")
	bus.interaction_requested.emit("lupe", "npc")
	await process_frame
	var shop := bar.get_node("%ShopPanel") as ShopPanel
	_check(shop.is_open(), "hablar con Lupe abre el Bar Cráter")
	await process_frame
	_check(not (bar.get_node("%Player") as WalkerController).consume_input, "Andrés quieto en el mostrador")
	shop._selected = "freeze_dried_shake"
	shop._on_buy()
	_check(inventory.has("freeze_dried_shake") and int(gs.credits) == 20, "batido comprado desde el panel")
	_check(root.get_node("StoryDirector").has_met("lupe"), "Lupe registrada en Tripulación")
	shop.close()
	await process_frame
	bus.interaction_requested.emit("exit", "door")
	await _wait_surface("moon")
	var moon := current_scene as SurfaceLevel
	_check((moon.get_node("%Player") as Node2D).global_position == moon.spawner.spawns["bar_door"], "sale frente a la puerta del bar")
	_check(str(gs.location) == "moon" and str(gs.region) == "moon", "ubicación: Luna")

	story.new_game()
	if _failed == 0:
		print("[economy] PASS")
		quit(0)
	else:
		printerr("[economy] FAIL (%d)" % _failed)
		quit(1)


func _wait_surface(map_id: String) -> void:
	for i in 120:
		await process_frame
		if current_scene is SurfaceLevel and (current_scene as SurfaceLevel).location_id == map_id \
				and not root.get_node("Router").is_busy():
			await process_frame
			return
	_check(false, "timeout esperando %s" % map_id)


func _check(ok: bool, label: String) -> void:
	if label.is_empty():
		return
	if ok:
		print("[economy] OK  %s" % label)
	else:
		printerr("[economy] FAIL %s" % label)
		_failed += 1
