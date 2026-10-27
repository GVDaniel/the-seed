class_name AudioSettings
extends Object
## Buses «Music» y «SFX» (creados en tiempo de ejecución) y volúmenes guardados en disco.

const SETTINGS_PATH := "user://the_seed_settings.cfg"
const MUSIC_BUS := "Music"
const SFX_BUS := "SFX"
const DEFAULT_VOLUME := {MUSIC_BUS: 0.7, SFX_BUS: 0.85}


## Idempotente: crea los buses, su filtro y aplica los volúmenes guardados.
static func ensure_buses() -> void:
	if AudioServer.get_bus_index(MUSIC_BUS) != -1:
		return
	for bus_name in [MUSIC_BUS, SFX_BUS]:
		AudioServer.add_bus()
		var idx := AudioServer.bus_count - 1
		AudioServer.set_bus_name(idx, bus_name)
		AudioServer.set_bus_send(idx, "Master")
	var lpf := AudioEffectLowPassFilter.new()
	lpf.cutoff_hz = 900.0
	AudioServer.add_bus_effect(AudioServer.get_bus_index(MUSIC_BUS), lpf)
	set_muffled(false)
	var cfg := ConfigFile.new()
	cfg.load(SETTINGS_PATH)
	for bus_name in [MUSIC_BUS, SFX_BUS]:
		_apply(bus_name, float(cfg.get_value("audio", bus_name, DEFAULT_VOLUME[bus_name])))


static func get_volume(bus_name: String) -> float:
	var idx := AudioServer.get_bus_index(bus_name)
	if idx == -1:
		return float(DEFAULT_VOLUME.get(bus_name, 1.0))
	return 0.0 if AudioServer.is_bus_mute(idx) else db_to_linear(AudioServer.get_bus_volume_db(idx))


## Volumen lineal 0–1; se guarda en disco.
static func set_volume(bus_name: String, linear: float) -> void:
	_apply(bus_name, linear)
	var cfg := ConfigFile.new()
	cfg.load(SETTINGS_PATH)
	cfg.set_value("audio", bus_name, clampf(linear, 0.0, 1.0))
	cfg.save(SETTINGS_PATH)


## Música «apagada» (filtro paso bajo), p. ej. dentro de la interfaz de HAL.
static func set_muffled(on: bool) -> void:
	var idx := AudioServer.get_bus_index(MUSIC_BUS)
	if idx != -1 and AudioServer.get_bus_effect_count(idx) > 0:
		AudioServer.set_bus_effect_enabled(idx, 0, on)


static func _apply(bus_name: String, linear: float) -> void:
	var idx := AudioServer.get_bus_index(bus_name)
	if idx == -1:
		return
	linear = clampf(linear, 0.0, 1.0)
	AudioServer.set_bus_mute(idx, linear <= 0.001)
	AudioServer.set_bus_volume_db(idx, linear_to_db(maxf(linear, 0.001)))
