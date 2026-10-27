class_name ShopCatalog
extends RefCounted
## Carga tiendas desde assets/data/shops/.

const DATA_DIR := "res://assets/data/shops/"

var _by_id: Dictionary = {}


func load_all() -> void:
	_by_id.clear()
	for data in JsonDir.load_dicts(DATA_DIR):
		var def := ShopDef.from_dict(data)
		if not def.id.is_empty():
			_by_id[def.id] = def


func get_def(shop_id: String) -> ShopDef:
	return _by_id.get(shop_id, null) as ShopDef


func all_ids() -> PackedStringArray:
	return PackedStringArray(_by_id.keys())
