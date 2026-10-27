extends Node
## Inventario que HAL guarda: equipo inicial + objetos de GameState.items.
## Entrega objetos por eventos (programas resueltos, señales escaneadas) según assets/data/items/.

var _catalog: ItemCatalog = ItemCatalog.new()


func _ready() -> void:
	_catalog.load_all()
	var bus := App.bus()
	bus.challenge_solved.connect(func(id: String) -> void: _grant_for("solve_challenge", id))
	bus.scan_completed.connect(func(id: String, _new: bool) -> void: _grant_for("scan_destination", id))


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
