class_name HalNotesTab
extends HBoxContainer
## Pestaña Cuaderno: descubrimientos escaneados y su ficha científica.

var _count: Label
var _list: ItemList
var _detail: VBoxContainer
var _ids: PackedStringArray = PackedStringArray()
var _selected: String = ""


func _ready() -> void:
	add_theme_constant_override("separation", 16)
	var left := VBoxContainer.new()
	left.custom_minimum_size = Vector2(290, 0)
	left.add_theme_constant_override("separation", 6)
	_count = HalUi.label("", 14, HalUi.CYAN)
	left.add_child(_count)
	_list = ItemList.new()
	_list.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_list.add_theme_font_size_override("font_size", 16)
	_list.item_selected.connect(func(index: int) -> void:
		_selected = _ids[index]
		App.sfx().play("blip")
		_show_detail()
	)
	left.add_child(_list)
	add_child(left)
	_detail = VBoxContainer.new()
	_detail.add_theme_constant_override("separation", 8)
	add_child(HalUi.scroll(_detail))


func refresh() -> void:
	var notebook := App.notebook()
	var entries: Array = notebook.get_discovered_entries()
	_count.text = "ENTRADAS: %d de %d" % [entries.size(), notebook.get_catalog().all_ids().size()]
	_list.clear()
	_ids = PackedStringArray()
	for entry in entries:
		var dest := entry as DestinationEntry
		_list.add_item(dest.display_name)
		_ids.append(dest.id)
	if not _ids.has(_selected):
		_selected = _ids[_ids.size() - 1] if not _ids.is_empty() else ""
	if not _selected.is_empty():
		_list.select(_ids.find(_selected))
	_show_detail()


func _show_detail() -> void:
	HalUi.clear(_detail)
	var entry: DestinationEntry = App.notebook().get_catalog().get_entry(_selected) if not _selected.is_empty() else null
	if entry == null:
		_detail.add_child(HalUi.label("Aún no hay descubrimientos. Acércate a algo interesante y pulsa F para escanearlo.", 17, HalUi.DIM, true))
		return
	_detail.add_child(HalUi.label(entry.display_name, 24, HalUi.GOLD, true))
	_detail.add_child(HalUi.label(entry.kind.to_upper(), 13, HalUi.CYAN))
	_detail.add_child(HalUi.label(entry.short_description, 17, HalUi.TEXT, true))
	for fact in entry.scientific_facts:
		var row := HalUi.panel(HalUi.CYAN, 8)
		var col := VBoxContainer.new()
		col.add_child(HalUi.label(str(fact.get("label", "")), 14, HalUi.CYAN, true))
		col.add_child(HalUi.label(str(fact.get("value", "")), 17, HalUi.TEXT, true))
		if bool(fact.get("is_game_simplification", false)):
			col.add_child(HalUi.label("Simplificación del juego", 13, HalUi.GOLD))
		row.add_child(col)
		_detail.add_child(row)
	if not entry.arcade_disclaimer.is_empty():
		_detail.add_child(HalUi.label(entry.arcade_disclaimer, 14, HalUi.DIM, true))


func hal_line() -> String:
	var count: int = App.notebook().get_discovered_ids().size()
	if count == 0:
		return "Tu cuaderno está vacío. Observar, registrar, concluir: así trabaja la ciencia."
	return "Has registrado %d descubrimientos. Cada dato tiene su fuente, como debe ser." % count
