extends Node
## Créditos: se ganan con misiones, descubrimientos y retos; se gastan en tiendas y bares.
## El saldo vive en GameState; aquí están las reglas y las compras.

const REWARD_MISSION := 60
const REWARD_DISCOVERY := 10
const REWARD_CHALLENGE := 25

var _shops: ShopCatalog = ShopCatalog.new()


func _ready() -> void:
	_shops.load_all()
	var bus := App.bus()
	bus.mission_completed.connect(_on_mission_completed)
	bus.discovery_added.connect(func(_id: String) -> void: _reward(REWARD_DISCOVERY, "nuevo descubrimiento"))
	bus.challenge_solved.connect(_on_challenge_solved)


func shops() -> ShopCatalog:
	return _shops


## Razón por la que no se puede comprar ("" = se puede).
func buy_block_reason(shop_id: String, item_id: String) -> String:
	var shop := _shops.get_def(shop_id)
	if shop == null or shop.price_of(item_id) < 0:
		return "No está a la venta aquí."
	if App.inventory().has(item_id):
		return "Ya lo tienes."
	var missing: int = shop.price_of(item_id) - int(App.game_state().credits)
	if missing > 0:
		return "Te faltan %d créditos." % missing
	return ""


func buy(shop_id: String, item_id: String) -> bool:
	if not buy_block_reason(shop_id, item_id).is_empty():
		return false
	var price := _shops.get_def(shop_id).price_of(item_id)
	if not App.game_state().spend_credits(price):
		return false
	App.game_state().add_item(item_id)
	App.bus().item_bought.emit(item_id, shop_id)
	App.bus().item_collected.emit(item_id)
	return true


func _on_mission_completed(mission_id: String) -> void:
	var def: MissionDef = App.missions().get_def(mission_id)
	var amount := int(def.rewards.get("credits", REWARD_MISSION)) if def != null else REWARD_MISSION
	_reward(amount, "misión completada")


func _on_challenge_solved(challenge_id: String) -> void:
	var flag := "paid_challenge_%s" % challenge_id
	if App.game_state().has_flag(flag):
		return
	App.game_state().set_flag(flag)
	_reward(REWARD_CHALLENGE, "programa resuelto")


func _reward(amount: int, reason: String) -> void:
	App.game_state().add_credits(amount)
	App.bus().mission_status_message.emit("+%d créditos (%s)" % [amount, reason])
