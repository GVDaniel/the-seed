extends Node
## Estado físico de ASTRA entre escenas: motor instalado, combustible y casco.
## Empieza con el viejo motor químico y poco combustible; las estaciones de servicio
## cobran por repostar y HAL siempre puede pedir una recarga de emergencia (sin bloqueos).

const SAVE_PATH := "user://the_seed_ship.cfg"
const ENGINES_PATH := "res://assets/data/ship/engines.json"

const STARTING_ENGINE := "old_chemical"
const STARTING_FUEL := 40.0
const MAX_HULL := 100.0
const MIN_HULL := 5.0
## Con el tanque vacío quedan los propulsores de reserva (más lentos, pero nunca te quedas varado).
const RESERVE_ACCEL := 0.3
const RESERVE_SPEED := 0.5
const EMERGENCY_FRACTION := 0.25
const HULL_PRICE := 0.3
const METHANE_FLAG := "methane_distilled"

var engine_id: String = STARTING_ENGINE
var fuel: float = STARTING_FUEL
var hull: float = MAX_HULL

var _engines: Dictionary = {}
var _unsaved: float = 0.0


func _ready() -> void:
	for row in JsonDir.load_dict(ENGINES_PATH).get("engines", []):
		if typeof(row) == TYPE_DICTIONARY:
			var def := EngineDef.from_dict(row)
			_engines[def.id] = def
	load_local()


func engine() -> EngineDef:
	return engine_def(engine_id)


func engine_def(id: String) -> EngineDef:
	var def := _engines.get(id, null) as EngineDef
	if def == null:
		def = _engines.get(STARTING_ENGINE, EngineDef.new()) as EngineDef
	return def


func capacity() -> float:
	return engine().fuel_capacity * ShipUpgrades.multiplier("fuel_capacity")


func fuel_ratio() -> float:
	return clampf(fuel / maxf(1.0, capacity()), 0.0, 1.0)


func hull_ratio() -> float:
	return clampf(hull / MAX_HULL, 0.0, 1.0)


func is_empty() -> bool:
	return fuel <= 0.01


func is_hull_full() -> bool:
	return hull >= MAX_HULL - 0.01


## Unidades por segundo con empuje máximo: motor × mejoras × conocimientos de Andrés.
func burn_rate() -> float:
	var know := int(App.hero().points.get(HeroProgression.CONOCIMIENTOS, 0))
	return engine().fuel_use * ShipUpgrades.multiplier("fuel_use") * HeroProgression.fuel_efficiency(know)


func burn(throttle: float, delta: float) -> void:
	if is_empty() or throttle <= 0.0:
		return
	var amount := burn_rate() * clampf(throttle, 0.0, 1.0) * delta
	fuel = maxf(0.0, fuel - amount)
	_unsaved += amount
	if _unsaved >= 5.0 or is_empty():
		_unsaved = 0.0
		save_local()
		App.bus().ship_state_changed.emit()


func add_fuel(amount: float) -> void:
	fuel = clampf(fuel + amount, 0.0, capacity())
	_changed()


func fill_fuel() -> void:
	add_fuel(capacity())


func damage_hull(amount: float) -> void:
	hull = clampf(hull - amount, MIN_HULL, MAX_HULL)
	_changed()


func repair(amount: float) -> void:
	hull = clampf(hull + amount, MIN_HULL, MAX_HULL)
	_changed()


## Un casco abollado frena la nave (hasta un 30 % menos de velocidad punta).
func hull_speed_factor() -> float:
	return lerpf(0.7, 1.0, hull_ratio())


func has_engine(id: String) -> bool:
	return engine_id == id


## El motor nuevo llega con el tanque vacío: hay que fabricarle su combustible.
func install_engine(id: String) -> void:
	if not _engines.has(id):
		return
	engine_id = id
	fuel = 0.0
	_changed()


## Copia de las estadísticas con motor, casco y combustible aplicados.
func apply_to(stats: ShipStats) -> ShipStats:
	var out := stats.duplicate() as ShipStats
	var def := engine()
	out.max_speed = stats.max_speed * def.speed_factor * hull_speed_factor()
	out.acceleration = stats.acceleration * def.accel_factor
	return out


## ¿Puede esta estación vender el combustible que usa el motor instalado?
func fuel_available() -> bool:
	return engine_id == STARTING_ENGINE or App.game_state().has_flag(METHANE_FLAG)


## Presupuesto de la estación: {fuel, hull, cost}.
func service_quote(rate: float) -> Dictionary:
	var fuel_need := capacity() - fuel if fuel_available() else 0.0
	var hull_need := MAX_HULL - hull
	return {
		"fuel": fuel_need,
		"hull": hull_need,
		"cost": int(ceil(fuel_need * rate + hull_need * HULL_PRICE)),
	}


## Repostaje y reparación en una estación. Devuelve el mensaje para la pantalla.
func service(rate: float, free: bool) -> String:
	var quote := service_quote(rate)
	if not fuel_available() and float(quote["hull"]) < 0.5:
		return "Aquí solo hay hidracina. El motor de metano necesita metano y oxígeno: hay que destilarlos."
	if float(quote["fuel"]) < 0.5 and float(quote["hull"]) < 0.5:
		return "ASTRA ya tiene el tanque lleno y el casco entero."
	if free:
		if fuel_available():
			fill_fuel()
		repair(MAX_HULL)
		return "Servicio completo sin coste: tanque lleno y casco reparado."
	var gs := App.game_state()
	var cost := int(quote["cost"])
	if gs.credits >= cost:
		gs.spend_credits(cost)
		if fuel_available():
			fill_fuel()
		repair(MAX_HULL)
		return "Servicio completo por %d créditos." % cost
	if gs.credits > 0:
		var budget := float(gs.credits)
		gs.spend_credits(gs.credits)
		if fuel_available():
			var units := minf(float(quote["fuel"]), budget / maxf(0.01, rate))
			add_fuel(units)
			budget -= units * rate
		repair(budget / HULL_PRICE)
		return "No te alcanzaba para todo: ASTRA recibió lo que pagaste con tus créditos."
	if fuel_available() and fuel < capacity() * EMERGENCY_FRACTION:
		fuel = capacity() * EMERGENCY_FRACTION
		_changed()
		return "HAL activa la reserva de emergencia: un cuarto de tanque gratis. ¡Gana créditos con misiones!"
	return "Sin créditos. Gana más con misiones, descubrimientos y programas."


func reset() -> void:
	engine_id = STARTING_ENGINE
	fuel = STARTING_FUEL
	hull = MAX_HULL
	_changed()


func as_dict() -> Dictionary:
	return {"engine_id": engine_id, "fuel": fuel, "hull": hull}


func _changed() -> void:
	_unsaved = 0.0
	save_local()
	App.bus().ship_state_changed.emit()


func save_local() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("ship", "engine_id", engine_id)
	cfg.set_value("ship", "fuel", fuel)
	cfg.set_value("ship", "hull", hull)
	var err := cfg.save(SAVE_PATH)
	if err != OK:
		push_warning("ShipState: no se pudo guardar (%s)" % error_string(err))


func load_local() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	engine_id = str(cfg.get_value("ship", "engine_id", STARTING_ENGINE))
	fuel = clampf(float(cfg.get_value("ship", "fuel", STARTING_FUEL)), 0.0, capacity())
	hull = clampf(float(cfg.get_value("ship", "hull", MAX_HULL)), MIN_HULL, MAX_HULL)
