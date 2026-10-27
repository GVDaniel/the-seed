class_name Combatant
extends RefCounted
## Participante de un combate (grupo o enemigo). Solo datos y contadores.

## Rondas que tarda en levantarse quien queda fuera de combate (si nadie le repara antes).
const KO_RECOVERY_ROUNDS := 2

var uid: String = ""
var display_name: String = ""
var is_enemy: bool = false
var max_hp: int = 1
var hp: int = 1
var max_en: int = 0
var en: int = 0
var attack: int = 1
var defense: int = 0
var weak: PackedStringArray = PackedStringArray()
var skills: PackedStringArray = PackedStringArray()
## Hoja de animación de combate (assets/data/combat/sheets.json).
var sheet: String = ""
var sprite_path: String = ""
var sprite_off_path: String = ""
var flying: bool = false
var moves: Array = []
var taunts: Array = []
## Lo que HAL cuenta al analizarlo (dato real sobre su tecnología).
var scan_text: String = ""

var acted: bool = false
## Escudo de chatarra: menos daño durante el turno enemigo.
var guard_mult: float = 1.0
## Turnos propios jugados (los enemigos cargan su ataque fuerte cada «every» turnos).
var turns_taken: int = 0
## Ataque cargado en curso: {move, turns_left, locks: PackedStringArray}.
var charge: Dictionary = {}
## Rondas que pierde por aturdimiento.
var stun_rounds: int = 0
## Coraza: mitad de daño mientras dure, salvo golpes de su debilidad (que la rompen).
var shield_rounds: int = 0
## Lo que hará en la fase enemiga de esta ronda (se anuncia al empezar la ronda).
var intent: Dictionary = {}
## Debilidades que el jugador ya conoce (golpeándolas o con el análisis de HAL).
var revealed: PackedStringArray = PackedStringArray()
var scanned: bool = false
## Rondas que faltan para levantarse tras quedar fuera de combate.
var ko_rounds: int = 0


static func from_enemy(data: Dictionary, enemy_uid: String) -> Combatant:
	var c := Combatant.new()
	c.uid = enemy_uid
	c.is_enemy = true
	c.display_name = str(data.get("display_name", enemy_uid))
	c.max_hp = int(data.get("max_hp", 30))
	c.hp = c.max_hp
	c.attack = int(data.get("attack", 5))
	c.defense = int(data.get("defense", 0))
	c.weak = PackedStringArray(data.get("weak", []))
	c.sheet = str(data.get("sheet", ""))
	c.sprite_path = str(data.get("sprite", ""))
	c.sprite_off_path = str(data.get("sprite_off", c.sprite_path))
	c.flying = bool(data.get("flying", false))
	c.moves = data.get("moves", [])
	c.taunts = data.get("taunts", [])
	c.scan_text = str(data.get("scan", ""))
	return c


func is_alive() -> bool:
	return hp > 0


func is_charging() -> bool:
	return not charge.is_empty()


func is_stunned() -> bool:
	return stun_rounds > 0


func locks() -> PackedStringArray:
	return charge.get("locks", PackedStringArray())


func knows_weakness(element: String) -> bool:
	return element in revealed


func reveal(element: String) -> bool:
	if element in weak and not element in revealed:
		revealed.append(element)
		return true
	return false


func take_damage(amount: int) -> int:
	var dealt := mini(hp, maxi(0, amount))
	hp -= dealt
	if hp <= 0 and not is_enemy:
		ko_rounds = KO_RECOVERY_ROUNDS
	return dealt


func heal(amount: int) -> int:
	var healed := mini(max_hp - hp, maxi(0, amount))
	hp += healed
	if hp > 0:
		ko_rounds = 0
	return healed


func gain_en(amount: int) -> int:
	var before := en
	en = clampi(en + amount, 0, max_en)
	return en - before
