class_name ItemCatalog
extends RefCounted
## Carga objetos desde assets/data/items/ en orden.

const DATA_DIR := "res://assets/data/items/"

var _by_id: Dictionary = {}
var _ordered: Array[ItemDef] = []


func load_all() -> void:
	_by_id.clear()
	_ordered.clear()
	for data in JsonDir.load_dicts(DATA_DIR):
		var def := ItemDef.from_dict(data)
		if def.id.is_empty():
			continue
		_by_id[def.id] = def
		_ordered.append(def)
	_ordered.sort_custom(func(a: ItemDef, b: ItemDef) -> bool: return a.order < b.order)


func get_def(item_id: String) -> ItemDef:
	return _by_id.get(item_id, null) as ItemDef


func all() -> Array[ItemDef]:
	return _ordered


func granted_by(type: String, value: String) -> Array[ItemDef]:
	var out: Array[ItemDef] = []
	for def in _ordered:
		if def.is_granted_by(type, value):
			out.append(def)
	return out


func size() -> int:
	return _ordered.size()
