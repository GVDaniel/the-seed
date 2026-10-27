extends Node
## Andrés como personaje: salud, nivel (de GameState.experience) y puntos de mejora
## en aptitudes, conocimientos y destrezas. También arma el grupo para los combates.

const SAVE_PATH := "user://the_seed_hero.cfg"
const POINTS_PER_LEVEL := 1

var hp: int = 1
var points: Dictionary = {}
var unspent: int = 0
## Último nivel ya celebrado (para detectar subidas).
var known_level: int = 1

var _skills: SkillCatalog = SkillCatalog.new()


func _ready() -> void:
	_skills.load_all()
	_reset_values()
	load_local()
	App.bus().experience_changed.connect(_on_experience_changed)


func skills() -> SkillCatalog:
	return _skills


func level() -> int:
	return HeroProgression.level_for_xp(int(App.game_state().experience))


func xp_progress() -> Vector2i:
	var lvl := level()
	var base := HeroProgression.xp_for_level(lvl)
	var next := HeroProgression.xp_for_level(lvl + 1)
	return Vector2i(int(App.game_state().experience) - base, maxi(1, next - base))


func point(stat: String) -> int:
	return int(points.get(stat, 0))


func max_hp() -> int:
	return HeroProgression.max_hp(level(), point(HeroProgression.APTITUDES))


func attack() -> int:
	return HeroProgression.attack(level(), point(HeroProgression.DESTREZAS))


func defense() -> int:
	return HeroProgression.defense(level(), point(HeroProgression.APTITUDES))


func max_en() -> int:
	return HeroProgression.max_en(level(), point(HeroProgression.CONOCIMIENTOS))


func timing_window() -> float:
	return HeroProgression.timing_window(point(HeroProgression.DESTREZAS))


func hp_ratio() -> float:
	return clampf(float(hp) / float(maxi(1, max_hp())), 0.0, 1.0)


func heal(amount: int) -> int:
	var before := hp
	hp = clampi(hp + amount, 1, max_hp())
	_changed()
	return hp - before


func set_hp(value: int) -> void:
	hp = clampi(value, 1, max_hp())
	_changed()


func full_heal() -> void:
	set_hp(max_hp())


func spend_point(stat: String) -> bool:
	if unspent <= 0 or not stat in HeroProgression.stat_ids():
		return false
	var hp_missing := max_hp() - hp
	unspent -= 1
	points[stat] = point(stat) + 1
	hp = max_hp() - hp_missing
	_changed()
	App.bus().mission_status_message.emit("%s sube a %d." % [HeroProgression.stat_name(stat), point(stat)])
	return true


func known_skills(user: String) -> PackedStringArray:
	return _skills.known_by(user, points)


## Andrés y HAL listos para BattleEngine (Andrés entra con su salud actual).
func make_party() -> Array[Combatant]:
	var lvl := level()
	var andres := Combatant.new()
	andres.uid = "andres"
	andres.display_name = "Andrés"
	andres.sheet = "andres"
	andres.max_hp = max_hp()
	andres.hp = clampi(hp, 1, andres.max_hp)
	andres.attack = attack()
	andres.defense = defense()
	andres.max_en = max_en()
	andres.en = mini(4, andres.max_en)
	andres.skills = known_skills("andres")
	var hal := Combatant.new()
	var hs := HeroProgression.hal_stats(lvl, point(HeroProgression.CONOCIMIENTOS))
	hal.uid = "hal"
	hal.display_name = "HAL"
	hal.sheet = "hal"
	hal.flying = true
	hal.max_hp = int(hs["max_hp"])
	hal.hp = hal.max_hp
	hal.attack = int(hs["attack"])
	hal.defense = int(hs["defense"])
	hal.max_en = int(hs["max_en"])
	hal.en = mini(5, hal.max_en)
	hal.skills = known_skills("hal")
	var party: Array[Combatant] = [andres, hal]
	return party


func reset() -> void:
	_reset_values()
	_changed()


func _reset_values() -> void:
	points = {}
	for stat in HeroProgression.stat_ids():
		points[stat] = 0
	unspent = 0
	known_level = level()
	unspent = (known_level - 1) * POINTS_PER_LEVEL
	hp = max_hp()


func _on_experience_changed(_total: int) -> void:
	var lvl := level()
	if lvl <= known_level:
		return
	var gained := (lvl - known_level) * POINTS_PER_LEVEL
	known_level = lvl
	unspent += gained
	hp = max_hp()
	_changed()
	App.bus().level_up.emit(lvl, gained)
	App.bus().mission_status_message.emit("¡Andrés sube a nivel %d! Punto de mejora en HAL (Tab → Andrés)." % lvl)


func _changed() -> void:
	save_local()
	App.bus().hero_changed.emit()


func save_local() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("hero", "hp", hp)
	cfg.set_value("hero", "points", points)
	cfg.set_value("hero", "unspent", unspent)
	cfg.set_value("hero", "known_level", known_level)
	var err := cfg.save(SAVE_PATH)
	if err != OK:
		push_warning("Hero: no se pudo guardar (%s)" % error_string(err))


func load_local() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	var saved: Variant = cfg.get_value("hero", "points", {})
	if typeof(saved) == TYPE_DICTIONARY:
		for stat in HeroProgression.stat_ids():
			points[stat] = int(saved.get(stat, 0))
	unspent = int(cfg.get_value("hero", "unspent", unspent))
	known_level = int(cfg.get_value("hero", "known_level", known_level))
	hp = clampi(int(cfg.get_value("hero", "hp", max_hp())), 1, max_hp())
