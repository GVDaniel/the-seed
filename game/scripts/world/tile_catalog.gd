class_name TileCatalog
extends Object
## Atlas de tiles (16 px) y construcción de TileSet con colisiones por índice.

const TILE := 16
const PHYSICS_LAYER_WORLD := 1

const ATLASES := {
	"earth": {"path": "res://assets/art/tiles/earth_tiles.png", "columns": 12, "rows": 11},
	"moon": {"path": "res://assets/art/tiles/moon_tiles.png", "columns": 8, "rows": 2},
	"mars": {"path": "res://assets/art/tiles/mars_tiles.png", "columns": 8, "rows": 2},
	"interior": {"path": "res://assets/art/tiles/interior_tiles.png", "columns": 8, "rows": 2},
}


static func has_atlas(atlas_id: String) -> bool:
	return ATLASES.has(atlas_id)


static func coords(atlas_id: String, index: int) -> Vector2i:
	var cols := int(ATLASES[atlas_id]["columns"])
	return Vector2i(index % cols, index / cols)


static func build(atlas_id: String, solid_indices: Array) -> TileSet:
	var info: Dictionary = ATLASES[atlas_id]
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)
	ts.add_physics_layer()
	ts.set_physics_layer_collision_layer(0, PHYSICS_LAYER_WORLD)
	ts.set_physics_layer_collision_mask(0, 0)
	var src := TileSetAtlasSource.new()
	src.texture = load(str(info["path"]))
	src.texture_region_size = Vector2i(TILE, TILE)
	ts.add_source(src, 0)
	var half := TILE * 0.5
	var square := PackedVector2Array([
		Vector2(-half, -half), Vector2(half, -half), Vector2(half, half), Vector2(-half, half)
	])
	for i in int(info["columns"]) * int(info["rows"]):
		var c := coords(atlas_id, i)
		src.create_tile(c)
		if solid_indices.has(i):
			var data := src.get_tile_data(c, 0)
			data.add_collision_polygon(0)
			data.set_collision_polygon_points(0, 0, square)
	return ts
