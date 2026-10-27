class_name BattleAutopilot
extends RefCounted
## Elige acciones razonables para el grupo (pruebas headless y demostraciones):
## romper cerraduras (potenciando si hace falta) > combo > curar > golpear la debilidad > ataque básico.
## Devuelve {type: "skill", skill_id, target, boost}.


static func choose(engine: BattleEngine, actor: Combatant) -> Dictionary:
	var skills: Array[CombatSkill] = []
	for id in actor.skills:
		var s := engine.catalog.get_def(id)
		if s != null and engine.block_reason(actor, s).is_empty():
			skills.append(s)
	var basic: CombatSkill = null
	for s in skills:
		if s.kind == "basic":
			basic = s
	for enemy in engine.alive_enemies():
		if enemy.is_charging():
			for s in skills:
				if s.is_offensive() and _shares(s.elements, enemy.locks()):
					var needed := _count(enemy.locks(), s.elements) - s.hits
					return _action(s, enemy.uid, clampi(needed, 0, engine.max_boost()))
	for combo in engine.catalog.combos():
		if engine.block_reason(actor, combo).is_empty():
			return _action(combo, _first_enemy(engine), engine.max_boost())
	for s in skills:
		if s.kind == "heal":
			for member in engine.party:
				if float(member.hp) < float(member.max_hp) * 0.4:
					return _action(s, member.uid, mini(1, engine.max_boost()))
	for enemy in engine.alive_enemies():
		for s in skills:
			if s.kind == "attack" and _shares(s.elements, enemy.weak):
				return _action(s, enemy.uid, 1 if engine.orbs >= 4 else 0)
	if basic != null:
		return _action(basic, _first_enemy(engine), 0)
	return {"type": "skill", "skill_id": actor.skills[0] if not actor.skills.is_empty() else "", "target": "", "boost": 0}


static func _action(skill: CombatSkill, target_uid: String, boost: int) -> Dictionary:
	return {"type": "skill", "skill_id": skill.id, "target": target_uid, "boost": boost}


static func _first_enemy(engine: BattleEngine) -> String:
	var alive := engine.alive_enemies()
	return alive[0].uid if not alive.is_empty() else ""


static func _shares(a: PackedStringArray, b: PackedStringArray) -> bool:
	for x in a:
		if x in b:
			return true
	return false


static func _count(locks: PackedStringArray, elements: PackedStringArray) -> int:
	var n := 0
	for l in locks:
		if l in elements:
			n += 1
	return n
