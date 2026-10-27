class_name HeroProgression
extends RefCounted
## Fórmulas de nivel y estadísticas de Andrés (y HAL). Sin estado: todo se calcula.
## Tres ramas de puntos: aptitudes (cuerpo), conocimientos (ciencia) y destrezas (habilidad).

const MAX_LEVEL := 20
const APTITUDES := "aptitudes"
const CONOCIMIENTOS := "conocimientos"
const DESTREZAS := "destrezas"


static func stat_ids() -> PackedStringArray:
	return PackedStringArray([APTITUDES, CONOCIMIENTOS, DESTREZAS])


static func stat_name(stat: String) -> String:
	match stat:
		APTITUDES:
			return "Aptitudes"
		CONOCIMIENTOS:
			return "Conocimientos"
		DESTREZAS:
			return "Destrezas"
	return stat.capitalize()


static func stat_help(stat: String) -> String:
	match stat:
		APTITUDES:
			return "Cuerpo y resistencia: +12 de salud máxima y +1 de defensa por punto."
		CONOCIMIENTOS:
			return "Ciencia: +2 de energía de técnicas por punto y ASTRA gasta un 5 % menos de combustible."
		DESTREZAS:
			return "Habilidad: +2 de ataque por punto y más margen para golpear y bloquear a tiempo."
	return ""


## Experiencia total necesaria para alcanzar un nivel (nivel 1 = 0 XP).
static func xp_for_level(level: int) -> int:
	var n := clampi(level, 1, MAX_LEVEL)
	return 10 * (n - 1) * (n + 2)


static func level_for_xp(xp: int) -> int:
	var level := 1
	while level < MAX_LEVEL and xp >= xp_for_level(level + 1):
		level += 1
	return level


static func max_hp(level: int, aptitudes: int) -> int:
	return 40 + 6 * level + 12 * aptitudes


static func attack(level: int, destrezas: int) -> int:
	return 6 + level + 2 * destrezas


static func defense(level: int, aptitudes: int) -> int:
	return 1 + floori(level / 2.0) + aptitudes


static func max_en(level: int, conocimientos: int) -> int:
	return 6 + floori(level / 4.0) + 2 * conocimientos


## Mitad del margen (segundos) alrededor del instante perfecto para golpear o bloquear.
static func timing_window(destrezas: int) -> float:
	return minf(0.3, 0.16 + 0.025 * float(destrezas))


## Multiplicador del consumo de combustible de ASTRA.
static func fuel_efficiency(conocimientos: int) -> float:
	return maxf(0.7, 1.0 - 0.05 * float(conocimientos))


static func hal_stats(level: int, conocimientos: int) -> Dictionary:
	return {
		"max_hp": 34 + 4 * level,
		"attack": 5 + level,
		"defense": 2 + floori(level / 2.0),
		"max_en": 8 + floori(level / 4.0) + conocimientos,
	}


## ¿Cumple el personaje los requisitos de una técnica? requires = {"conocimientos": 1, …}.
static func meets(requires: Dictionary, points: Dictionary) -> bool:
	for key in requires.keys():
		if int(points.get(key, 0)) < int(requires[key]):
			return false
	return true
