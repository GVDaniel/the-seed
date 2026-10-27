extends Node
## Inventario que HAL guarda: equipo inicial + objetos de GameState.items.
## Entrega objetos por eventos (programas, escaneos, interacciones, combates) según assets/data/items/.
## Los consumibles (comida, medicinas, repuestos) se gastan con use().

var _catalog: ItemCatalog = ItemCatalog.new()


func _ready() -> void:
	_catalog.load_all()
	var bus := App.bus()
	bus.challenge_solved.connect(func(id: String) -> void: _grant_for("solve_challenge", id))
	bus.scan_completed.connect(func(id: String, _new: bool) -> void: _grant_for("scan_destination", id))
	bus.world_interacted.connect(func(id: String) -> void: _grant_for("interact", id))
	bus.battle_finished.connect(_on_battle_finished)


func catalog() -> ItemCatalog:
	return _catalog


func has(item_id: String) -> bool:
	var def := _catalog.get_def(item_id)
	return (def != null and def.starter) or App.game_state().has_item(item_id)


## Objetos que lleva el jugador, en el orden del catálogo.
func owned() -> Array[ItemDef]:
	var out: Array[ItemDef] = []
	for def in _catalog.all():
		if has(def.id):
			out.append(def)
	return out


func _grant_for(type: String, value: String) -> void:
	for def in _catalog.granted_by(type, value):
		if App.game_state().add_item(def.id):
			App.bus().item_collected.emit(def.id)
			App.bus().mission_status_message.emit("HAL guardó: %s  (Tab)" % def.display_name)


## Por qué no se puede usar ahora ("" = se puede).
func use_block_reason(item_id: String) -> String:
	var def := _catalog.get_def(item_id)
	if def == null or not def.is_consumable() or not has(item_id):
		return "Este objeto no se puede usar."
	if def.heal_amount() > 0 and App.hero().hp >= App.hero().max_hp():
		return "Andrés ya tiene la salud al máximo."
	if def.repair_amount() > 0 and App.ship().is_hull_full():
		return "El casco de ASTRA ya está entero."
	return ""


## Consume el objeto: cura a Andrés o repara ASTRA.
func use(item_id: String) -> bool:
	if not use_block_reason(item_id).is_empty():
		return false
	var def := _catalog.get_def(item_id)
	if def.heal_amount() > 0:
		App.hero().heal(def.heal_amount())
	if def.repair_amount() > 0:
		App.ship().repair(def.repair_amount())
	App.game_state().remove_item(item_id)
	App.bus().item_used.emit(item_id)
	App.bus().mission_status_message.emit("%s usado. %s" % [def.display_name, def.use_text().trim_prefix("Usar: ")])
	return true


func consumables(kind: String = "") -> Array[ItemDef]:
	var out: Array[ItemDef] = []
	for def in owned():
		if not def.is_consumable():
			continue
		if kind == "heal" and def.heal_amount() <= 0:
			continue
		if kind == "repair" and def.repair_amount() <= 0:
			continue
		out.append(def)
	return out


func _on_battle_finished(encounter_id: String, result: String) -> void:
	if result == "victory":
		_grant_for("win_battle", encounter_id)
