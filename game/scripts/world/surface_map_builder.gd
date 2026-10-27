class_name SurfaceMapBuilder
extends RefCounted
## Pinta las capas de tiles de un mapa ASCII (JSON) y añade límites del mundo.


## Devuelve el tamaño del mapa en tiles.
static func paint(map: Dictionary, ground: TileMapLayer, objects: TileMapLayer) -> Vector2i:
	var atlas := str(map.get("tileset", "earth"))
	var legend: Dictionary = map.get("legend", {})
	var solid: Array = []
	for key in legend.keys():
		var def: Dictionary = legend[key]
		if bool(def.get("solid", false)):
			for idx in _indices(def.get("tile", 0)):
				solid.append(idx)
	var ts := TileCatalog.build(atlas, solid)
	ground.tile_set = ts
	objects.tile_set = ts
	var size := Vector2i.ZERO
	size = size.max(_paint_layer(map.get("ground", []), legend, atlas, ground))
	size = size.max(_paint_layer(map.get("objects", []), legend, atlas, objects))
	return size


static func add_bounds(parent: Node, size_tiles: Vector2i) -> void:
	var body := StaticBody2D.new()
	body.name = "WorldBounds"
	body.collision_layer = TileCatalog.PHYSICS_LAYER_WORLD
	body.collision_mask = 0
	var w := float(size_tiles.x * TileCatalog.TILE)
	var h := float(size_tiles.y * TileCatalog.TILE)
	var t := 16.0
	for rect in [
		Rect2(-t, -t, w + t * 2.0, t), Rect2(-t, h, w + t * 2.0, t),
		Rect2(-t, 0, t, h), Rect2(w, 0, t, h),
	]:
		var shape := CollisionShape2D.new()
		var box := RectangleShape2D.new()
		box.size = rect.size
		shape.shape = box
		shape.position = rect.position + rect.size * 0.5
		body.add_child(shape)
	parent.add_child(body)


static func _paint_layer(rows: Array, legend: Dictionary, atlas: String, layer: TileMapLayer) -> Vector2i:
	var size := Vector2i.ZERO
	for y in rows.size():
		var row := str(rows[y])
		size.x = maxi(size.x, row.length())
		size.y = y + 1
		for x in row.length():
			var ch := row[x]
			if ch == " " or not legend.has(ch):
				continue
			var options := _indices((legend[ch] as Dictionary).get("tile", 0))
			var idx: int = options[_hash(x, y) % options.size()]
			layer.set_cell(Vector2i(x, y), 0, TileCatalog.coords(atlas, idx))
	return size


static func _indices(value: Variant) -> Array:
	if typeof(value) == TYPE_ARRAY:
		return value
	return [int(value)]


static func _hash(x: int, y: int) -> int:
	return absi((x * 73856093) ^ (y * 19349663)) % 9973
