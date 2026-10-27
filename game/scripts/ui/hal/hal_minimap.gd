class_name HalMinimap
extends Control
## Mapa de la superficie actual, dibujado desde el JSON del mapa:
## colores de los tiles, puntos de interés, jugador y objetivo.

const LEGEND_HEIGHT := 30.0
const DOOR_COLOR := Color("ff3ea5")

var _map: Dictionary = {}
var _player: Node2D
var _colors: Dictionary = {}
var _grid := Vector2i.ZERO
var _t: float = 0.0


func setup(map: Dictionary, player: Node2D) -> void:
	_map = map
	_player = player
	_colors = _legend_colors(map)
	_grid = Vector2i.ZERO
	for layer in ["ground", "objects"]:
		var rows: Array = map.get(layer, [])
		_grid.y = maxi(_grid.y, rows.size())
		for row in rows:
			_grid.x = maxi(_grid.x, str(row).length())
	queue_redraw()


func has_map() -> bool:
	return not _map.is_empty() and _grid.x > 0


func _process(delta: float) -> void:
	if is_visible_in_tree():
		_t += delta
		queue_redraw()


func _draw() -> void:
	if not has_map():
		return
	var avail := size - Vector2(0, LEGEND_HEIGHT)
	var cell := maxf(2.0, floorf(minf(avail.x / _grid.x, avail.y / _grid.y)))
	var origin := ((avail - Vector2(_grid) * cell) * 0.5).floor()
	var frame := Rect2(origin - Vector2(4, 4), Vector2(_grid) * cell + Vector2(8, 8))
	draw_rect(frame, Color(0.02, 0.035, 0.07), true)
	for layer in ["ground", "objects"]:
		var rows: Array = _map.get(layer, [])
		for y in rows.size():
			var row := str(rows[y])
			for x in row.length():
				var ch := row[x]
				if _colors.has(ch):
					draw_rect(Rect2(origin + Vector2(x, y) * cell, Vector2(cell, cell)), _colors[ch])
	draw_rect(frame, HalUi.CYAN, false, 2.0)
	_draw_entities(origin, cell)
	_draw_player(origin, cell)
	_draw_legend()


func _to_screen(tile_pos: Vector2, origin: Vector2, cell: float) -> Vector2:
	return origin + (tile_pos + Vector2(0.5, 0.5)) * cell


func _draw_entities(origin: Vector2, cell: float) -> void:
	var targets: PackedStringArray = App.story().nav_candidates()
	var r := maxf(3.0, cell * 0.55)
	for data in _map.get("entities", []):
		var e: Dictionary = data
		var id := str(e.get("id", ""))
		var p: Array = e.get("pos", [0, 0])
		var at := _to_screen(Vector2(float(p[0]), float(p[1])), origin, cell)
		match str(e.get("type", "")):
			"npc":
				draw_circle(at, r * 1.15, HalUi.GOLD)
				HalUi.draw_text(self, at + Vector2(r + 3, -r), App.story().characters().display_name(id), 13, HalUi.GOLD)
			"scan":
				var col := HalUi.DIM if App.notebook().is_discovered(id) else HalUi.CYAN
				draw_colored_polygon(_diamond(at, r * 1.2), col)
			"item":
				if not App.game_state().has_item(id):
					draw_rect(Rect2(at - Vector2(r, r), Vector2(r, r) * 2), HalUi.GOLD)
			"terminal":
				draw_rect(Rect2(at - Vector2(r, r), Vector2(r, r) * 2), HalUi.CYAN, false, 2.0)
			"ship":
				draw_colored_polygon(_triangle(at, r * 1.6), Color.WHITE)
				HalUi.draw_text(self, at + Vector2(r * 1.6 + 3, 4), "ASTRA", 13, Color.WHITE)
			"object":
				draw_circle(at, r * 0.7, HalUi.CYAN)
			"door":
				draw_rect(Rect2(at - Vector2(r, r * 1.2), Vector2(r * 2, r * 2.2)), DOOR_COLOR)
				var door_label := str(e.get("label", ""))
				if not door_label.is_empty():
					HalUi.draw_text(self, at + Vector2(-door_label.length() * 3.2, -r * 1.6), door_label, 13, DOOR_COLOR)
			_:
				continue
		if targets.has(id):
			var pulse := 1.0 + 0.25 * sin(_t * 5.0)
			draw_arc(at, r * 2.4 * pulse, 0, TAU, 24, HalUi.GOLD, 2.0)


func _draw_player(origin: Vector2, cell: float) -> void:
	if _player == null or not is_instance_valid(_player):
		return
	var tile := _player.global_position / float(TileCatalog.TILE) - Vector2(0.5, 1.0)
	var at := _to_screen(tile, origin, cell)
	var r := maxf(3.0, cell * 0.6)
	draw_circle(at, r * (2.2 + 0.4 * sin(_t * 4.0)), Color(1, 0.29, 0.2, 0.25))
	draw_circle(at, r, HalUi.RED)
	draw_circle(at, r * 0.35, HalUi.GOLD)
	HalUi.draw_text(self, at + Vector2(r + 4, r + 10), "Tú", 14, HalUi.RED)


func _draw_legend() -> void:
	var y := size.y - 10.0
	var x := 6.0
	var items := [
		["player", "Tú"], ["npc", "Personaje"], ["scan", "Escanear"], ["terminal", "Terminal"],
		["item", "Objeto"], ["door", "Puerta"], ["ship", "Nave"], ["target", "Objetivo"],
	]
	for row in items:
		var at := Vector2(x + 6, y - 5)
		match str(row[0]):
			"player":
				draw_circle(at, 5, HalUi.RED)
			"npc":
				draw_circle(at, 5, HalUi.GOLD)
			"scan":
				draw_colored_polygon(_diamond(at, 6), HalUi.CYAN)
			"terminal":
				draw_rect(Rect2(at - Vector2(5, 5), Vector2(10, 10)), HalUi.CYAN, false, 2.0)
			"item":
				draw_rect(Rect2(at - Vector2(5, 5), Vector2(10, 10)), HalUi.GOLD)
			"ship":
				draw_colored_polygon(_triangle(at, 7), Color.WHITE)
			"target":
				draw_arc(at, 6, 0, TAU, 16, HalUi.GOLD, 2.0)
			"door":
				draw_rect(Rect2(at - Vector2(4, 6), Vector2(8, 12)), DOOR_COLOR)
		HalUi.draw_text(self, Vector2(x + 16, y), str(row[1]), 14, HalUi.DIM)
		x += 30.0 + str(row[1]).length() * 8.0


static func _diamond(c: Vector2, r: float) -> PackedVector2Array:
	return PackedVector2Array([c + Vector2(0, -r), c + Vector2(r, 0), c + Vector2(0, r), c + Vector2(-r, 0)])


static func _triangle(c: Vector2, r: float) -> PackedVector2Array:
	return PackedVector2Array([c + Vector2(0, -r), c + Vector2(r * 0.8, r * 0.7), c + Vector2(-r * 0.8, r * 0.7)])


## Color medio del tile de cada símbolo de la leyenda (atlas real del mapa).
static func _legend_colors(map: Dictionary) -> Dictionary:
	var atlas := str(map.get("tileset", "earth"))
	if not TileCatalog.has_atlas(atlas):
		return {}
	var tex := load(str(TileCatalog.info(atlas)["path"])) as Texture2D
	var img := tex.get_image() if tex != null else null
	if img == null:
		return {}
	if img.is_compressed():
		img.decompress()
	var out := {}
	var legend: Dictionary = map.get("legend", {})
	for ch in legend.keys():
		var tile: Variant = (legend[ch] as Dictionary).get("tile", 0)
		var index := int(tile[0]) if typeof(tile) == TYPE_ARRAY else int(tile)
		var col := _average(img, TileCatalog.coords(atlas, index) * TileCatalog.TILE)
		if bool((legend[ch] as Dictionary).get("solid", false)):
			col = col.darkened(0.25)
		out[ch] = col
	return out


static func _average(img: Image, corner: Vector2i) -> Color:
	var sum := Vector3.ZERO
	var n := 0
	for y in TileCatalog.TILE:
		for x in TileCatalog.TILE:
			var c := img.get_pixel(corner.x + x, corner.y + y)
			if c.a < 0.5:
				continue
			sum += Vector3(c.r, c.g, c.b)
			n += 1
	if n == 0:
		return Color(0, 0, 0, 0)
	sum /= float(n)
	return Color(sum.x, sum.y, sum.z)
