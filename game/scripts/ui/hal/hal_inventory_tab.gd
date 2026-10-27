class_name HalInventoryTab
extends HBoxContainer
## Pestaña Inventario: casillas de carga y ficha del objeto elegido.

const SLOTS := 20

var _grid: GridContainer
var _icon: TextureRect
var _name: Label
var _category: Label
var _description: Label
var _fact: Label
var _fact_box: PanelContainer
var _selected: String = ""
var _header: Label


func _ready() -> void:
	add_theme_constant_override("separation", 22)
	var left := VBoxContainer.new()
	left.add_theme_constant_override("separation", 8)
	_header = HalUi.label("", 14, HalUi.CYAN)
	left.add_child(_header)
	_grid = GridContainer.new()
	_grid.columns = 5
	_grid.add_theme_constant_override("h_separation", 8)
	_grid.add_theme_constant_override("v_separation", 8)
	left.add_child(_grid)
	add_child(left)

	var detail := VBoxContainer.new()
	detail.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail.add_theme_constant_override("separation", 8)
	_icon = HalUi.texture_rect("", Vector2(96, 96))
	_icon.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_name = HalUi.label("", 24, HalUi.GOLD, true)
	_category = HalUi.label("", 14, HalUi.CYAN)
	_description = HalUi.label("", 17, HalUi.TEXT, true)
	_fact_box = HalUi.panel(HalUi.GOLD, 12)
	var fact_col := VBoxContainer.new()
	fact_col.add_child(HalUi.label("DATO REAL", 13, HalUi.GOLD))
	_fact = HalUi.label("", 16, HalUi.TEXT, true)
	fact_col.add_child(_fact)
	_fact_box.add_child(fact_col)
	for c in [_icon, _name, _category, _description, _fact_box]:
		detail.add_child(c)
	add_child(detail)


func refresh() -> void:
	HalUi.clear(_grid)
	_header.text = "CASILLAS DE CARGA · CRÉDITOS: %d" % int(App.game_state().credits)
	var owned: Array[ItemDef] = App.inventory().owned()
	if _selected.is_empty() or not App.inventory().has(_selected):
		_selected = owned[0].id if not owned.is_empty() else ""
	for i in SLOTS:
		var slot := Button.new()
		slot.custom_minimum_size = Vector2(76, 76)
		if i < owned.size():
			var def := owned[i]
			if ResourceLoader.exists(def.icon_path):
				slot.icon = load(def.icon_path)
			slot.expand_icon = true
			slot.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
			slot.tooltip_text = def.display_name
			slot.toggle_mode = true
			slot.button_pressed = def.id == _selected
			var id := def.id
			slot.pressed.connect(func() -> void: _select(id))
		else:
			slot.disabled = true
		_grid.add_child(slot)
	_show_detail()


func _select(item_id: String) -> void:
	_selected = item_id
	App.sfx().play("blip")
	refresh()


func _show_detail() -> void:
	var def: ItemDef = App.inventory().catalog().get_def(_selected)
	_fact_box.visible = def != null and not def.fact.is_empty()
	if def == null:
		_icon.texture = null
		_name.text = "Inventario vacío"
		_category.text = ""
		_description.text = ""
		return
	_icon.texture = load(def.icon_path) if ResourceLoader.exists(def.icon_path) else null
	_name.text = def.display_name
	_category.text = def.category_name().to_upper()
	_description.text = def.description
	_fact.text = def.fact


func hal_line() -> String:
	var count: int = App.inventory().owned().size()
	var credits := int(App.game_state().credits)
	if App.inventory().has("the_seed"):
		return "Llevas %d objetos y %d créditos. La Semilla está fría y seca, como en la bóveda." % [count, credits]
	return "Llevas %d objetos y %d créditos. Tengo una casilla reservada para algo muy importante." % [count, credits]
