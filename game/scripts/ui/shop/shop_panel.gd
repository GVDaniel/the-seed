class_name ShopPanel
extends CanvasLayer
## Mostrador de una tienda o bar: lista de productos, ficha con dato real y botón de compra.
## Se abre con EventBus.shop_requested; la compra la valida Economy.

var _root: Control
var _portrait: TextureRect
var _keeper: Label
var _shop_name: Label
var _greeting: Label
var _credits: Label
var _list: VBoxContainer
var _icon: TextureRect
var _name: Label
var _category: Label
var _description: Label
var _fact: Label
var _effect: Label
var _buy: Button
var _status: Label
var _shop: ShopDef
var _selected: String = ""


func _ready() -> void:
	layer = 21
	_build()
	_root.visible = false
	visible = false
	App.bus().shop_requested.connect(open)
	App.bus().credits_changed.connect(func(_c: int) -> void:
		if is_open():
			_refresh()
	)


func is_open() -> bool:
	return visible


func open(shop_id: String) -> void:
	_shop = App.economy().shops().get_def(shop_id)
	if _shop == null:
		push_warning("ShopPanel: tienda desconocida %s" % shop_id)
		App.bus().shop_closed.emit()
		return
	var keeper: CharacterDef = App.story().characters().get_def(_shop.keeper)
	_portrait.texture = load(keeper.portrait_path) if keeper != null and ResourceLoader.exists(keeper.portrait_path) else null
	_keeper.text = keeper.display_name if keeper != null else ""
	_shop_name.text = _shop.display_name
	_greeting.text = "«%s»" % _shop.greeting
	_selected = str(_shop.stock[0]["item"]) if not _shop.stock.is_empty() else ""
	_status.text = ""
	visible = true
	_root.visible = true
	App.sfx().play("confirm")
	_refresh()


func close() -> void:
	if not visible:
		return
	visible = false
	_root.visible = false
	App.bus().shop_closed.emit()


func _unhandled_input(event: InputEvent) -> void:
	if visible and (event.is_action_pressed("ui_cancel") or event.is_action_pressed("panel_close")):
		close()
		get_viewport().set_input_as_handled()


func _refresh() -> void:
	_credits.text = "Créditos: %d" % int(App.game_state().credits)
	HalUi.clear(_list)
	for row in _shop.stock:
		var def: ItemDef = App.inventory().catalog().get_def(str(row["item"]))
		if def == null:
			continue
		var b := Button.new()
		b.toggle_mode = true
		b.button_pressed = def.id == _selected
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.custom_minimum_size = Vector2(0, 52)
		b.expand_icon = true
		if ResourceLoader.exists(def.icon_path):
			b.icon = load(def.icon_path)
			b.add_theme_constant_override("icon_max_width", 36)
		var owned: bool = App.inventory().has(def.id)
		b.text = "%s   ·   %s" % [def.display_name, "TIENES" if owned else "%d cr" % int(row["price"])]
		var id := def.id
		b.pressed.connect(func() -> void:
			_selected = id
			_status.text = ""
			App.sfx().play("blip")
			_refresh()
		)
		_list.add_child(b)
	_show_detail()


func _show_detail() -> void:
	var def: ItemDef = App.inventory().catalog().get_def(_selected)
	if def == null:
		return
	_icon.texture = load(def.icon_path) if ResourceLoader.exists(def.icon_path) else null
	_name.text = def.display_name
	_category.text = def.category_name().to_upper()
	_description.text = def.description
	_fact.text = def.fact
	_effect.text = _effect_text(def)
	_effect.visible = not _effect.text.is_empty()
	var reason: String = App.economy().buy_block_reason(_shop.id, def.id)
	_buy.text = "Comprar por %d créditos" % _shop.price_of(def.id)
	_buy.disabled = not reason.is_empty()
	if not reason.is_empty() and _status.text.is_empty():
		_status.text = reason


func _on_buy() -> void:
	var def: ItemDef = App.inventory().catalog().get_def(_selected)
	if def == null:
		return
	if App.economy().buy(_shop.id, def.id):
		App.sfx().play("pickup")
		_status.text = "¡Comprado! HAL lo guardó en tu inventario." if def.effects.is_empty() \
				else "¡Comprado! HAL instalará la mejora en ASTRA."
	else:
		App.sfx().play("error")
		_status.text = App.economy().buy_block_reason(_shop.id, def.id)
	_refresh()


func _on_chat() -> void:
	var keeper := _shop.keeper
	close()
	App.story().talk_to(keeper)


static func _effect_text(def: ItemDef) -> String:
	var names := {
		"max_energy": "energía máxima", "max_speed": "velocidad máxima", "acceleration": "aceleración",
		"energy_regen": "recarga de energía", "debris_damage": "daño por basura espacial",
	}
	var parts := PackedStringArray()
	for key in def.effects.keys():
		var pct := int(round((float(def.effects[key]) - 1.0) * 100.0))
		parts.append("%s %s%d %%" % [names.get(key, key), "+" if pct > 0 else "", pct])
	return "" if parts.is_empty() else "ASTRA: " + ", ".join(parts)


# ------------------------------------------------------------ construcción

func _build() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	var dim := ColorRect.new()
	dim.color = Color(0.02, 0.035, 0.07, 0.75)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(center)
	var card := HalUi.panel(HalUi.GOLD, 18)
	card.custom_minimum_size = Vector2(980, 590)
	center.add_child(card)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 12)
	card.add_child(col)

	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 14)
	_portrait = HalUi.texture_rect("", Vector2(88, 88))
	head.add_child(_portrait)
	var who := VBoxContainer.new()
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_shop_name = HalUi.label("", 24, HalUi.GOLD)
	_keeper = HalUi.label("", 15, HalUi.CYAN)
	_greeting = HalUi.label("", 16, HalUi.TEXT, true)
	for c in [_shop_name, _keeper, _greeting]:
		who.add_child(c)
	head.add_child(who)
	_credits = HalUi.label("", 20, HalUi.GOLD)
	_credits.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	head.add_child(_credits)
	col.add_child(head)

	var body := HBoxContainer.new()
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 18)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 6)
	var scroll := HalUi.scroll(_list)
	scroll.custom_minimum_size = Vector2(400, 0)
	scroll.size_flags_horizontal = Control.SIZE_FILL
	body.add_child(scroll)
	var detail := VBoxContainer.new()
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail.add_theme_constant_override("separation", 6)
	_icon = HalUi.texture_rect("", Vector2(72, 72))
	_icon.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_name = HalUi.label("", 22, HalUi.GOLD, true)
	_category = HalUi.label("", 13, HalUi.CYAN)
	_description = HalUi.label("", 16, HalUi.TEXT, true)
	var fact_box := HalUi.panel(HalUi.CYAN, 10)
	var fact_col := VBoxContainer.new()
	fact_col.add_child(HalUi.label("DATO REAL", 13, HalUi.CYAN))
	_fact = HalUi.label("", 15, HalUi.TEXT, true)
	fact_col.add_child(_fact)
	fact_box.add_child(fact_col)
	_effect = HalUi.label("", 15, HalUi.GOLD, true)
	for c in [_icon, _name, _category, _description, fact_box, _effect]:
		detail.add_child(c)
	body.add_child(detail)
	col.add_child(body)

	var foot := HBoxContainer.new()
	foot.add_theme_constant_override("separation", 10)
	_status = HalUi.label("", 16, HalUi.GOLD, true)
	foot.add_child(_status)
	var chat := Button.new()
	chat.text = "Charlar"
	chat.pressed.connect(_on_chat)
	foot.add_child(chat)
	_buy = Button.new()
	_buy.text = "Comprar"
	_buy.pressed.connect(_on_buy)
	foot.add_child(_buy)
	var exit := Button.new()
	exit.text = "Salir (Esc)"
	exit.pressed.connect(close)
	foot.add_child(exit)
	col.add_child(foot)
