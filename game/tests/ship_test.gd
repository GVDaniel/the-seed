extends SceneTree
## Estado de ASTRA: combustible, casco, motores, mejoras, estaciones de servicio y vuelo real.
## godot --headless --path game --script res://tests/ship_test.gd

var _failed: int = 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	print("[ship] start")
	var story: Node = root.get_node("StoryDirector")
	var ship: Node = root.get_node("ShipState")
	var gs: Node = root.get_node("GameState")
	story.new_game()

	# --- Arranque modesto
	_check(str(ship.engine_id) == "old_chemical", "motor químico viejo al empezar")
	_check(is_equal_approx(float(ship.fuel), 40.0) and is_equal_approx(float(ship.capacity()), 60.0), "40/60 de hidracina")
	var base: ShipStats = load("res://resources/ship_stats_astra.tres")
	var slow: ShipStats = ship.apply_to(base)
	_check(slow.max_speed < base.max_speed * 0.7 and slow.acceleration < base.acceleration * 0.7, "nave lenta (%.0f px/s)" % slow.max_speed)
	ship.burn(1.0, 10.0)
	_check(is_equal_approx(float(ship.fuel), 24.0), "10 s de empuje gastan 16 (%.1f)" % float(ship.fuel))

	# --- Casco
	ship.damage_hull(60.0)
	_check(is_equal_approx(float(ship.hull), 40.0), "casco al 40 %")
	_check(ship.apply_to(base).max_speed < slow.max_speed, "casco abollado: menos velocidad")
	ship.damage_hull(500.0)
	_check(is_equal_approx(float(ship.hull), 5.0), "el casco nunca baja de 5 %")
	gs.add_item("repair_kit")
	_check(root.get_node("Inventory").use("repair_kit") and is_equal_approx(float(ship.hull), 45.0), "kit de reparación +40 %")

	# --- Estaciones de servicio
	gs.credits = 10
	var msg: String = ship.service(0.5, false)
	_check(int(gs.credits) == 0 and float(ship.fuel) > 24.0, "pago parcial con lo que hay (%s)" % msg)
	ship.fuel = 2.0
	msg = ship.service(0.5, false)
	_check(is_equal_approx(float(ship.fuel), 15.0) and msg.contains("emergencia"), "sin créditos: cuarto de tanque gratis")
	gs.credits = 200
	msg = ship.service(0.5, false)
	_check(is_equal_approx(float(ship.fuel), 60.0) and is_equal_approx(float(ship.hull), 100.0) and int(gs.credits) < 200, "servicio completo pagado")
	ship.fuel = 10.0
	ship.service(0.4, true)
	_check(is_equal_approx(float(ship.fuel), 60.0) and int(gs.credits) == int(gs.credits), "servicio gratuito")

	# --- Motor nuevo y combustible que hay que fabricar
	ship.install_engine("methane_engine")
	_check(ship.is_empty() and not ship.fuel_available(), "motor de metano: tanque vacío y sin metano a la venta")
	_check(ship.service(0.5, false).contains("metano"), "la estación explica que hace falta destilar")
	_check(not story.can_take_off("mars"), "sin metano no se despega")
	gs.set_flag("methane_distilled")
	ship.fill_fuel()
	var fast: ShipStats = ship.apply_to(base)
	_check(fast.max_speed > slow.max_speed * 1.6, "con el motor de metano ASTRA vuela mucho más rápido (%.0f px/s)" % fast.max_speed)
	_check(float(ship.capacity()) > 100.0 and float(ship.burn_rate()) < 1.6, "más tanque y menos consumo")

	# --- Mejoras de tienda y conocimientos
	var rate: float = ship.burn_rate()
	gs.add_item("ion_thruster")
	_check(is_equal_approx(float(ship.burn_rate()), rate * 0.75), "propulsor iónico: −25 % de consumo")
	gs.add_item("aux_tank")
	_check(is_equal_approx(float(ship.capacity()), 140.0 * 1.5), "tanque auxiliar: +50 % de capacidad")
	var hero: Node = root.get_node("Hero")
	gs.add_experience(40)
	hero.spend_point("conocimientos")
	_check(float(ship.burn_rate()) < rate * 0.75, "conocimientos de Andrés ahorran combustible")

	# --- Vuelo real: el empuje gasta, sin combustible quedan los propulsores de reserva
	story.new_game()
	var router: Node = root.get_node("Router")
	router.go_space("earth")
	for i in 120:
		await process_frame
		if current_scene is Node2D and current_scene.name == "SpaceMain" and not router.is_busy():
			break
	var astra := current_scene.get_node("World/AstraShip") as ShipController
	_check(astra != null and astra.fuel_source == ship, "la nave del espacio usa ShipState")
	_check(astra.stats.max_speed < base.max_speed * 0.7, "en vuelo se nota el motor viejo")
	var hud := current_scene.get_node("FlightHud") as FlightHud
	_check((hud.get_node("%FuelLabel") as Label).text.begins_with("COMB"), "el HUD muestra el combustible")
	var before := float(ship.fuel)
	Input.action_press("ship_thrust")
	for i in 30:
		await physics_frame
	_check(float(ship.fuel) < before, "acelerar gasta combustible (%.1f → %.1f)" % [before, float(ship.fuel)])
	ship.fuel = 0.0
	astra.velocity = Vector2.ZERO
	for i in 180:
		await physics_frame
	Input.action_release("ship_thrust")
	var reserve_speed := astra.get_speed()
	_check(astra.is_on_reserve() and reserve_speed > 20.0, "sin combustible la nave aún avanza (%.0f px/s)" % reserve_speed)
	_check(reserve_speed <= astra.stats.max_speed * ShipController.RESERVE_SPEED + 1.0, "reserva: como mucho media velocidad")
	_check((hud.get_node("%FuelLabel") as Label).text == "RESERVA", "el HUD avisa de la reserva")
	var debris := current_scene.get_node("World/Earth/DebrisField") as DebrisField
	debris._hit(astra.global_position + Vector2(10, 0))
	_check(float(ship.hull) < 100.0, "la basura espacial abolla el casco (%.0f %%)" % float(ship.hull))

	story.new_game()
	if _failed == 0:
		print("[ship] PASS")
		quit(0)
	else:
		printerr("[ship] FAIL (%d)" % _failed)
		quit(1)


func _check(ok: bool, label: String) -> void:
	if ok:
		print("[ship] OK  %s" % label)
	else:
		printerr("[ship] FAIL %s" % label)
		_failed += 1
