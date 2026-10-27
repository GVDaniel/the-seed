class_name BattleRules
extends RefCounted
## Fórmulas del combate: daño, debilidades, pulsaciones a tiempo (golpe y bloqueo) y potenciación.

const PERFECT := "perfect"
const GOOD := "good"
const MISS := "miss"

const WEAK_MULT := 1.5
const GUARD_MULT := 0.5
const SHIELD_MULT := 0.5
## Cada chispa solar gastada al potenciar.
const BOOST_POWER := 0.35
const MAX_BOOST := 3
## Medidor de «mantener y soltar»: centro de la zona buena (0..1 del medidor).
const HOLD_SWEET := 0.86


## Calidad de la pulsación según lo lejos (en segundos) que quedó del instante perfecto.
static func judge(offset_seconds: float, window: float) -> String:
	var d := absf(offset_seconds)
	if d <= window * 0.5:
		return PERFECT
	if d <= window:
		return GOOD
	return MISS


## «Mantener y soltar»: value = llenado del medidor al soltar (0..1). La zona crece con la destreza.
static func judge_hold(value: float, window: float) -> String:
	var d := absf(value - HOLD_SWEET)
	var zone := window * 0.5
	if d <= zone * 0.4:
		return PERFECT
	if d <= zone:
		return GOOD
	return MISS


static func attack_mult(timing: String) -> float:
	match timing:
		PERFECT:
			return 1.5
		GOOD:
			return 1.2
	return 1.0


static func block_mult(timing: String) -> float:
	match timing:
		PERFECT:
			return 0.4
		GOOD:
			return 0.7
	return 1.0


static func boost_mult(boost: int) -> float:
	return 1.0 + BOOST_POWER * float(clampi(boost, 0, MAX_BOOST))


## Escudo de chatarra: cada chispa lo hace un poco más resistente.
static func guard_mult(boost: int) -> float:
	return maxf(0.25, GUARD_MULT - 0.08 * float(clampi(boost, 0, MAX_BOOST)))


## Chispas solares que suelta un golpe básico.
static func orbs_for(timing: String) -> int:
	return 2 if timing == PERFECT else 1


static func timing_text(timing: String, blocking: bool) -> String:
	match timing:
		PERFECT:
			return "¡BLOQUEO PERFECTO!" if blocking else "¡PERFECTO!"
		GOOD:
			return "¡Bloqueo!" if blocking else "¡Bien!"
	return ""


static func damage(attack: int, defense: int, power: float, weak: bool, timing_mult: float = 1.0,
		guard: float = 1.0) -> int:
	var raw := float(attack) * power * timing_mult - float(defense) * 0.6
	if weak:
		raw *= WEAK_MULT
	raw *= guard
	return maxi(1, int(round(raw)))


static func element_name(element: String) -> String:
	match element:
		"impacto":
			return "impacto"
		"electricidad":
			return "electricidad"
		"luz":
			return "luz"
	return element
