class_name HalCrewTab
extends ScrollContainer
## Pestaña Tripulación: equipo de la misión y gente de cada lugar.
## A quien aún no conoces lo ves como silueta.

var _col: VBoxContainer


func _ready() -> void:
	horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_col = VBoxContainer.new()
	_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_col.add_theme_constant_override("separation", 10)
	add_child(_col)


func refresh() -> void:
	HalUi.clear(_col)
	var groups := {"crew": [], "local": []}
	for def in App.story().characters().all():
		groups["crew" if def.group == "crew" else "local"].append(def)
	_section("EQUIPO DE LA MISIÓN", groups["crew"])
	_section("GENTE DE LA TIERRA, LA LUNA Y MARTE", groups["local"])


func _section(title: String, defs: Array) -> void:
	_col.add_child(HalUi.label(title, 14, HalUi.CYAN))
	var grid := GridContainer.new()
	grid.columns = 2
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	for def in defs:
		grid.add_child(_card(def, bool(App.story().has_met((def as CharacterDef).id))))
	_col.add_child(grid)


func _card(def: CharacterDef, met: bool) -> PanelContainer:
	var card := HalUi.panel(HalUi.CYAN if met else HalUi.LOCKED, 10)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	var portrait := HalUi.texture_rect(def.portrait_path, Vector2(96, 96))
	portrait.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	if not met:
		portrait.modulate = Color(0, 0, 0, 0.85)
	row.add_child(portrait)
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_theme_constant_override("separation", 3)
	col.add_child(HalUi.label(def.display_name if met else "???", 19, HalUi.GOLD if met else HalUi.LOCKED))
	col.add_child(HalUi.label(def.role if met else "Desconocido", 14, HalUi.CYAN if met else HalUi.LOCKED, true))
	col.add_child(HalUi.label(def.bio if met else "Todavía no se conocen.", 15, HalUi.TEXT if met else HalUi.LOCKED, true))
	row.add_child(col)
	card.add_child(row)
	return card


func hal_line() -> String:
	var met := 0
	var all: Array[CharacterDef] = App.story().characters().all()
	for def in all:
		if App.story().has_met(def.id):
			met += 1
	return "Personas registradas: %d de %d. Nadie cruza el espacio en solitario." % [met, all.size()]
