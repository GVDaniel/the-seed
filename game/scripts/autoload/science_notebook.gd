extends Node
## Cuaderno científico. Persistente durante partidas (disco local).

const SAVE_PATH := "user://the_seed_notebook.cfg"

signal discovery_added(destination_id: String)
signal discovery_already_known(destination_id: String)
signal notebook_changed(count: int)

var _catalog: DestinationCatalog = DestinationCatalog.new()
var _discovered_ids: PackedStringArray = PackedStringArray()


func _ready() -> void:
	_catalog.load_all()
	load_local()


func get_catalog() -> DestinationCatalog:
	return _catalog


func is_discovered(destination_id: String) -> bool:
	return _discovered_ids.has(destination_id)


func get_discovered_ids() -> PackedStringArray:
	return _discovered_ids.duplicate()


func get_discovered_entries() -> Array[DestinationEntry]:
	var list: Array[DestinationEntry] = []
	for id in _discovered_ids:
		var entry := _catalog.get_entry(id)
		if entry != null:
			list.append(entry)
	return list


## Registra un descubrimiento. Devuelve true solo si es nuevo.
func record_discovery(destination_id: String) -> bool:
	if destination_id.is_empty() or not _catalog.has_id(destination_id):
		return false
	if _discovered_ids.has(destination_id):
		discovery_already_known.emit(destination_id)
		App.bus().discovery_already_known.emit(destination_id)
		return false
	_discovered_ids.append(destination_id)
	save_local()
	discovery_added.emit(destination_id)
	App.bus().discovery_added.emit(destination_id)
	App.bus().destination_discovered.emit(destination_id)
	notebook_changed.emit(_discovered_ids.size())
	return true


func clear_session() -> void:
	_discovered_ids.clear()
	save_local()
	notebook_changed.emit(0)


func save_local() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("notebook", "discovered_ids", Array(_discovered_ids))
	cfg.save(SAVE_PATH)


func load_local() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	var ids: Array = cfg.get_value("notebook", "discovered_ids", [])
	_discovered_ids = PackedStringArray(ids)
