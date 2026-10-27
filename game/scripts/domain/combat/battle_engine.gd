class_name BattleEngine
extends RefCounted
## Combate por turnos al estilo Sea of Stars, sin nodos.
##
## Ronda: begin_round() anuncia qué hará cada enemigo (blanco, ataque o carga con cerraduras);
## después cada miembro vivo del grupo actúa en el orden que elija el jugador y por último
## resuelven los enemigos. Golpes y bloqueos a tiempo multiplican el resultado.
##
## Recursos del grupo:
## - Energía (EN) de cada uno: la gastan las técnicas; el ataque básico recupera 1.
## - Chispas solares (compartidas): las sueltan los ataques básicos; potencian la siguiente acción
##   (más daño o curación y cada golpe rompe una cerradura más).
## - Combo (compartido): lo llenan los golpes básicos; paga las técnicas en equipo.
##
## Cada acción devuelve eventos que la escena anima: {type: damage|heal|guard|ko|revive|weak|reveal|
## lock_broken|charge_start|charge_broken|charging|stunned|shield|shield_broken|drain|en|orbs|info, …}.

const VICTORY := "victory"
const DEFEAT := "defeat"
const COMBO_MAX := 6
const ORBS_MAX := 5
const REVIVE_RATIO := 0.25

var encounter: Dictionary = {}
var party: Array[Combatant] = []
var enemies: Array[Combatant] = []
var catalog: SkillCatalog
var combo_points: int = 0
var orbs: int = 0
var round_number: int = 0
var outcome: String = ""
var rng := RandomNumberGenerator.new()


func setup(encounter_data: Dictionary, party_members: Array[Combatant], skill_catalog: SkillCatalog,
		seed_value: int = 0) -> void:
	encounter = encounter_data
	party = party_members
	catalog = skill_catalog
	enemies.clear()
	var i := 0
	for row in encounter_data.get("enemies", []):
		if typeof(row) == TYPE_DICTIONARY:
			enemies.append(Combatant.from_enemy(row, "e%d" % i))
			i += 1
	combo_points = 0
	orbs = 0
	round_number = 0
	outcome = ""
	rng.seed = seed_value if seed_value != 0 else hash(str(encounter_data.get("id", "battle")))


func combatant(uid: String) -> Combatant:
	for c in party + enemies:
		if c.uid == uid:
			return c
	return null


func alive_enemies() -> Array[Combatant]:
	var out: Array[Combatant] = []
	for e in enemies:
		if e.is_alive():
			out.append(e)
	return out


func alive_party() -> Array[Combatant]:
	var out: Array[Combatant] = []
	for p in party:
		if p.is_alive():
			out.append(p)
	return out


func ready_actors() -> Array[Combatant]:
	var out: Array[Combatant] = []
	if not outcome.is_empty():
		return out
	for p in party:
		if p.is_alive() and not p.acted:
			out.append(p)
	return out


func is_party_phase_over() -> bool:
	return ready_actors().is_empty()


# ------------------------------------------------------------ ronda

## Empieza una ronda: cada enemigo decide y anuncia su acción.
func begin_round() -> Array[Dictionary]:
	var events: Array[Dictionary] = []
	round_number += 1
	for p in party:
		p.acted = false
		p.guard_mult = 1.0
	for enemy in alive_enemies():
		_decide(enemy, events)
	return events


func enemy_order() -> PackedStringArray:
	var out := PackedStringArray()
	for e in alive_enemies():
		out.append(e.uid)
	return out


func intent_of(enemy_uid: String) -> Dictionary:
	var enemy := combatant(enemy_uid)
	return enemy.intent if enemy != null else {}


## ¿Pide esta intención que el jugador bloquee?
static func needs_block(intent: Dictionary) -> bool:
	if not str(intent.get("kind", "")) in ["attack", "release"]:
		return false
	return str((intent.get("move", {}) as Dictionary).get("target", "one")) != "self"


## Fin de ronda: quien estaba fuera de combate se levanta si ya le toca; las corazas se gastan.
func end_round() -> Array[Dictionary]:
	var events: Array[Dictionary] = []
	for p in party:
		p.acted = false
		p.guard_mult = 1.0
		if p.is_alive() or not outcome.is_empty():
			continue
		p.ko_rounds -= 1
		if p.ko_rounds <= 0:
			p.heal(maxi(1, int(ceil(p.max_hp * REVIVE_RATIO))))
			events.append({"type": "revive", "uid": p.uid, "amount": p.hp})
	for e in alive_enemies():
		if e.shield_rounds > 0:
			e.shield_rounds -= 1
			if e.shield_rounds == 0:
				events.append({"type": "shield_broken", "uid": e.uid})
	return events


# ------------------------------------------------------------ grupo

## Por qué no se puede usar ahora una técnica ("" = sí se puede).
func block_reason(actor: Combatant, skill: CombatSkill) -> String:
	if skill == null or actor == null:
		return "No disponible."
	if skill.kind == "combo":
		if combo_points < skill.combo_cost:
			return "Faltan puntos de combo (%d/%d)." % [combo_points, skill.combo_cost]
		if alive_party().size() < party.size():
			return "El combo necesita a todo el equipo en pie."
		return ""
	if actor.en < skill.cost:
		return "Energía insuficiente (%d/%d)." % [actor.en, skill.cost]
	return ""


func can_use(actor_uid: String, skill_id: String) -> bool:
	return block_reason(combatant(actor_uid), catalog.get_def(skill_id)).is_empty()


func max_boost() -> int:
	return mini(orbs, BattleRules.MAX_BOOST)


## Ejecuta la acción de un miembro del grupo. timing = BattleRules.PERFECT | GOOD | MISS;
## hit_timings (opcional) da una pulsación por golpe. boost = chispas solares que gasta.
func perform(actor_uid: String, skill_id: String, target_uid: String, timing: String, boost: int = 0,
		hit_timings: PackedStringArray = PackedStringArray()) -> Array[Dictionary]:
	var events: Array[Dictionary] = []
	var actor := combatant(actor_uid)
	var skill := catalog.get_def(skill_id)
	if actor == null or skill == null or not actor.is_alive() or actor.acted or not outcome.is_empty():
		return events
	if not block_reason(actor, skill).is_empty():
		return events
	actor.acted = true
	boost = clampi(boost, 0, max_boost())
	if boost > 0:
		orbs -= boost
		events.append({"type": "boost", "uid": actor.uid, "amount": boost})
	match skill.kind:
		"basic", "attack":
			actor.en -= skill.cost
			_attack(actor, skill, target_uid, timing, boost, hit_timings, events)
			if skill.kind == "basic":
				var gained := actor.gain_en(1)
				if gained > 0:
					events.append({"type": "en", "uid": actor.uid, "amount": gained})
		"combo":
			combo_points -= skill.combo_cost
			_attack(actor, skill, target_uid, timing, boost, hit_timings, events)
		"heal":
			actor.en -= skill.cost
			var target := combatant(target_uid)
			if target == null or target.is_enemy:
				target = _weakest_ally()
			var amount := float(skill.amount) * (1.25 if timing == BattleRules.PERFECT else 1.0)
			amount *= BattleRules.boost_mult(boost)
			var was_down := not target.is_alive()
			var healed := target.heal(int(round(amount)))
			events.append({"type": "revive" if was_down else "heal", "uid": target.uid, "amount": healed})
		"guard":
			actor.en -= skill.cost
			var mult := BattleRules.guard_mult(boost)
			for p in alive_party():
				p.guard_mult = mult
			events.append({"type": "guard", "uid": actor.uid, "amount": int(round((1.0 - mult) * 100.0))})
	_check_outcome()
	return events


## Usar un objeto en combate gasta el turno de quien lo usa.
func use_item(actor_uid: String, target_uid: String, heal_amount: int) -> Array[Dictionary]:
	var events: Array[Dictionary] = []
	var actor := combatant(actor_uid)
	var target := combatant(target_uid)
	if actor == null or not actor.is_alive() or actor.acted:
		return events
	if target == null or target.is_enemy:
		target = actor
	actor.acted = true
	events.append({"type": "heal", "uid": target.uid, "amount": target.heal(heal_amount)})
	return events


## Análisis de HAL: revela las debilidades de un enemigo. No gasta turno; una vez por enemigo.
func can_analyze(enemy_uid: String) -> bool:
	var enemy := combatant(enemy_uid)
	var hal := combatant("hal")
	return enemy != null and enemy.is_enemy and enemy.is_alive() and not enemy.scanned \
		and hal != null and hal.is_alive() and outcome.is_empty()


func analyze(enemy_uid: String) -> Array[Dictionary]:
	var events: Array[Dictionary] = []
	if not can_analyze(enemy_uid):
		return events
	var enemy := combatant(enemy_uid)
	enemy.scanned = true
	for el in enemy.weak:
		enemy.reveal(el)
	events.append({"type": "reveal", "uid": enemy.uid, "elements": enemy.weak, "text": enemy.scan_text})
	return events


# ------------------------------------------------------------ enemigos

func resolve_enemy(enemy_uid: String, block_timing: String) -> Array[Dictionary]:
	var events: Array[Dictionary] = []
	var enemy := combatant(enemy_uid)
	if enemy == null or not enemy.is_alive() or not outcome.is_empty():
		return events
	var intent := enemy.intent
	enemy.intent = {}
	match str(intent.get("kind", "")):
		"stunned":
			enemy.stun_rounds = maxi(0, enemy.stun_rounds - 1)
			events.append({"type": "stunned", "uid": enemy.uid})
		"charging":
			enemy.charge["turns_left"] = int(enemy.charge.get("turns_left", 1)) - 1
			events.append({"type": "charging", "uid": enemy.uid, "locks": enemy.locks(),
				"turns": int(enemy.charge["turns_left"])})
		"attack", "release":
			if str(intent["kind"]) == "release":
				enemy.charge = {}
			_enemy_move(enemy, intent, block_timing, events)
	_check_outcome()
	return events


func _decide(enemy: Combatant, events: Array[Dictionary]) -> void:
	if enemy.is_stunned():
		enemy.intent = {"kind": "stunned", "uid": enemy.uid}
		return
	if enemy.is_charging():
		var move: Dictionary = enemy.charge.get("move", {})
		var left := int(enemy.charge.get("turns_left", 1))
		enemy.intent = {"kind": "release" if left <= 1 else "charging", "uid": enemy.uid, "move": move,
			"targets": _pick_targets(enemy, move), "turns": left}
		return
	enemy.turns_taken += 1
	for move in enemy.moves:
		var every := int(move.get("every", 0))
		if every > 0 and enemy.turns_taken % every == 0:
			var turns := maxi(1, int(move.get("charge", 1)))
			enemy.charge = {"move": move, "turns_left": turns, "locks": PackedStringArray(move.get("locks", []))}
			enemy.intent = {"kind": "release" if turns <= 1 else "charging", "uid": enemy.uid, "move": move,
				"targets": _pick_targets(enemy, move), "turns": turns}
			events.append({"type": "charge_start", "uid": enemy.uid, "move": str(move.get("name", "")),
				"locks": enemy.locks(), "turns": turns})
			return
	var chosen := _weighted_move(enemy)
	enemy.intent = {"kind": "attack", "uid": enemy.uid, "move": chosen, "targets": _pick_targets(enemy, chosen)}


func _enemy_move(enemy: Combatant, intent: Dictionary, block_timing: String, events: Array[Dictionary]) -> void:
	var move: Dictionary = intent.get("move", {})
	var effect := str(move.get("effect", ""))
	if effect == "shield":
		enemy.shield_rounds = maxi(1, int(move.get("rounds", 2)))
		events.append({"type": "shield", "uid": enemy.uid, "move": str(move.get("name", "")),
			"turns": enemy.shield_rounds})
		return
	var targets := PackedStringArray(intent.get("targets", []))
	if targets.size() == 1 and combatant(targets[0]) != null and not combatant(targets[0]).is_alive():
		targets = _pick_targets(enemy, move)
	for t in targets:
		var target := combatant(str(t))
		if target == null or not target.is_alive():
			continue
		var dmg := BattleRules.damage(enemy.attack, target.defense, float(move.get("power", 1.0)),
			false, 1.0, BattleRules.block_mult(block_timing) * target.guard_mult)
		var dealt := target.take_damage(dmg)
		events.append({"type": "damage", "uid": target.uid, "amount": dealt, "from": enemy.uid,
			"move": str(move.get("name", "")), "timing": block_timing})
		if effect == "drain" and target.is_alive() and block_timing != BattleRules.PERFECT:
			var lost := -target.gain_en(-maxi(1, int(move.get("drain", 1))))
			if lost > 0:
				events.append({"type": "drain", "uid": target.uid, "amount": lost})
		if not target.is_alive():
			events.append({"type": "ko", "uid": target.uid})


func _attack(actor: Combatant, skill: CombatSkill, target_uid: String, timing: String, boost: int,
		hit_timings: PackedStringArray, events: Array[Dictionary]) -> void:
	var targets: Array[Combatant] = []
	if skill.target == "all_enemies":
		targets = alive_enemies()
	else:
		var t := combatant(target_uid)
		if t == null or not t.is_enemy or not t.is_alive():
			var alive := alive_enemies()
			if alive.is_empty():
				return
			t = alive[0]
		targets.append(t)
	var attack_value := actor.attack
	if skill.kind == "combo":
		for p in party:
			attack_value = maxi(attack_value, p.attack)
	var power := skill.power * BattleRules.boost_mult(boost)
	for target in targets:
		var weak := false
		for el in skill.elements:
			if el in target.weak:
				weak = true
				if target.reveal(el):
					events.append({"type": "reveal", "uid": target.uid, "elements": PackedStringArray([el])})
		if weak and target.shield_rounds > 0:
			target.shield_rounds = 0
			events.append({"type": "shield_broken", "uid": target.uid})
		for hit in skill.hits:
			if not target.is_alive():
				break
			var hit_timing := hit_timings[hit] if hit < hit_timings.size() else timing
			var shield := BattleRules.SHIELD_MULT if target.shield_rounds > 0 else 1.0
			var dmg := BattleRules.damage(attack_value, target.defense, power, weak,
				BattleRules.attack_mult(hit_timing), shield)
			var dealt := target.take_damage(dmg)
			events.append({"type": "damage", "uid": target.uid, "amount": dealt, "from": actor.uid,
				"timing": hit_timing, "weak": weak, "hit": hit})
			for el in skill.elements:
				for _i in 1 + boost:
					if not _break_lock(target, el, events):
						break
			if skill.kind == "basic":
				combo_points = mini(COMBO_MAX, combo_points + (2 if hit_timing == BattleRules.PERFECT else 1))
				var drop := mini(ORBS_MAX - orbs, BattleRules.orbs_for(hit_timing))
				if drop > 0:
					orbs += drop
					events.append({"type": "orbs", "uid": target.uid, "amount": drop})
			if not target.is_alive():
				target.charge = {}
				target.intent = {}
				events.append({"type": "ko", "uid": target.uid})
		if weak:
			events.append({"type": "weak", "uid": target.uid})


## Rompe una cerradura de ese elemento. Devuelve si había alguna.
func _break_lock(enemy: Combatant, element: String, events: Array[Dictionary]) -> bool:
	if not enemy.is_charging() or not enemy.is_alive():
		return false
	var locks := enemy.locks()
	var idx := locks.find(element)
	if idx < 0:
		return false
	locks.remove_at(idx)
	enemy.charge["locks"] = locks
	events.append({"type": "lock_broken", "uid": enemy.uid, "element": element, "left": locks.size()})
	if locks.is_empty():
		enemy.charge = {}
		# Pierde la acción de esta ronda.
		enemy.stun_rounds = 1
		enemy.intent = {"kind": "stunned", "uid": enemy.uid}
		events.append({"type": "charge_broken", "uid": enemy.uid})
	return true


func _weighted_move(enemy: Combatant) -> Dictionary:
	var pool: Array = []
	var total := 0
	for move in enemy.moves:
		if int(move.get("every", 0)) > 0:
			continue
		if str(move.get("effect", "")) == "shield" and enemy.shield_rounds > 0:
			continue
		var w := maxi(1, int(move.get("weight", 1)))
		pool.append([move, w])
		total += w
	if pool.is_empty():
		return {"name": "Golpe", "power": 1.0, "target": "one"}
	var roll := rng.randi_range(1, total)
	for entry in pool:
		roll -= int(entry[1])
		if roll <= 0:
			return entry[0]
	return pool[0][0]


func _pick_targets(enemy: Combatant, move: Dictionary) -> PackedStringArray:
	var out := PackedStringArray()
	match str(move.get("target", "one")):
		"self":
			out.append(enemy.uid)
			return out
		"all":
			for p in party:
				out.append(p.uid)
			return out
	var alive := alive_party()
	if not alive.is_empty():
		out.append(alive[rng.randi_range(0, alive.size() - 1)].uid)
	return out


func _weakest_ally() -> Combatant:
	var best: Combatant = party[0]
	for p in party:
		if float(p.hp) / float(p.max_hp) < float(best.hp) / float(best.max_hp):
			best = p
	return best


func _check_outcome() -> void:
	if not outcome.is_empty():
		return
	if alive_enemies().is_empty():
		outcome = VICTORY
	elif alive_party().is_empty():
		outcome = DEFEAT
