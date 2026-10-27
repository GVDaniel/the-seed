extends SceneTree
## Carga los mapas de superficie, comprueba entidades clave y que los retos de la historia tienen solución.
## godot --headless --path game --script res://tests/world_test.gd

const MAPS := {
	"earth": ["lucia", "the_seed", "earth_dead_plant", "earth_air_sensor", "launch_terminal", "astra",
		"door_earth_shop", "zoe", "mateo", "amaru", "service_earth", "holo_antihuman_earth"],
	"moon": ["kai", "moon_ice_crater", "drill_terminal", "astra", "door_moon_bar", "door_moon_shop", "tomas",
		"service_moon"],
	"mars": ["osei", "mars_delta", "mars_rover", "delta_terminal", "mars_greenhouse", "astra",
		"door_mars_bar", "door_mars_shop", "door_mars_garage", "yusuf", "ada", "service_mars", "co2_compressor",
		"ah7_sentinel", "methane_engine", "mars_buried_ice", "mars_ice_core", "mars_iron_meteorite", "ah_drones",
		"nickel_catalyst"],
	"mars_garage": ["bruno", "mars_workbench", "methane_distiller", "exit"],
	"earth_shop": ["ramiro", "exit"],
	"moon_bar": ["lupe", "amina", "exit"],
	"moon_shop": ["ingrid", "exit"],
	"mars_bar": ["rosa", "nia", "exit"],
	"mars_shop": ["chen", "exit"],
}
const PROPS_DIR := "res://assets/art/props/"

var _failed: int = 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	print("[world] start")
	_check_catalog_links()
	_check_challenges()
	_check_map_links()
	_check_people_and_shops()
	_check_combat_data()
	for map_id in MAPS.keys():
		await _check_map(map_id, MAPS[map_id])
	await _check_scene("res://scenes/story/cutscene.tscn")
	await _check_scene("res://scenes/ui/main_menu.tscn")
	if _failed == 0:
		print("[world] PASS")
		quit(0)
	else:
		printerr("[world] FAIL (%d)" % _failed)
		quit(1)


func _check_map(map_id: String, required: Array) -> void:
	var arrive := "ship" if map_id in ["earth", "moon", "mars"] else "entrance"
	root.get_node("Router").pending_surface = map_id
	root.get_node("Router").pending_spawn = arrive
	var scene := (load("res://scenes/surface/surface_level.tscn") as PackedScene).instantiate() as SurfaceLevel
	_check(scene != null, "%s: escena de superficie instanciada" % map_id)
	if scene == null:
		return
	root.add_child(scene)
	await process_frame
	await process_frame
	var ground := scene.get_node("%Ground") as TileMapLayer
	_check(ground.get_used_cells().size() > (300 if arrive == "ship" else 150), "%s: suelo pintado (%d celdas)" % [map_id, ground.get_used_cells().size()])
	for id in required:
		_check(scene.spawner.entities.has(id), "%s: entidad %s" % [map_id, id])
	var player := scene.get_node("%Player") as Node2D
	_check(scene.spawner.spawns.has(arrive) and player.global_position == scene.spawner.spawns[arrive], "%s: jugador en %s" % [map_id, arrive])
	# Ningún punto de aparición dentro de un tile sólido
	var objects := scene.get_node("%Objects") as TileMapLayer
	for spawn_id in scene.spawner.spawns.keys():
		var p: Vector2 = scene.spawner.spawns[spawn_id]
		var cell := objects.local_to_map(p - Vector2(0, 4))
		_check(objects.get_cell_source_id(cell) == -1, "%s: spawn %s libre" % [map_id, spawn_id])
	scene.queue_free()
	await process_frame


## Puertas que llevan a mapas y puntos de aparición que existen; sprites presentes.
func _check_map_links() -> void:
	for map_id in MAPS.keys():
		var map := JsonDir.load_dict("res://assets/data/maps/%s.json" % map_id)
		_check(not map.is_empty(), "mapa %s cargado" % map_id)
		for e in map.get("entities", []):
			var sprite := str(e.get("sprite", ""))
			if not sprite.is_empty():
				_check(ResourceLoader.exists(PROPS_DIR + sprite + ".png"), "%s: sprite %s" % [map_id, sprite])
			if str(e.get("type", "")) == "door" and e.has("target"):
				var target := JsonDir.load_dict("res://assets/data/maps/%s.json" % str(e["target"]))
				var spawn_ok := false
				for t in target.get("entities", []):
					if str(t.get("type", "")) == "spawn" and str(t.get("id", "")) == str(e.get("spawn", "entrance")):
						spawn_ok = true
				_check(spawn_ok, "%s: puerta %s → %s:%s" % [map_id, e.get("id", ""), e["target"], e.get("spawn", "entrance")])


## Cada NPC tiene ficha, sprite y retrato; cada tienda, dueño y productos válidos.
func _check_people_and_shops() -> void:
	var characters: CharacterCatalog = root.get_node("StoryDirector").characters()
	for def in characters.all():
		_check(ResourceLoader.exists(def.sprite_path) and ResourceLoader.exists(def.portrait_path), "arte de %s" % def.id)
		_check(not def.idle_lines.is_empty() and not def.bio.is_empty(), "diálogo y bio de %s" % def.id)
	var shops: ShopCatalog = root.get_node("Economy").shops()
	var items: ItemCatalog = root.get_node("Inventory").catalog()
	for map_id in MAPS.keys():
		for e in JsonDir.load_dict("res://assets/data/maps/%s.json" % map_id).get("entities", []):
			if str(e.get("type", "")) != "npc":
				continue
			_check(characters.get_def(str(e["id"])) != null, "%s: ficha de %s" % [map_id, e["id"]])
			if e.has("shop"):
				var shop := shops.get_def(str(e["shop"]))
				_check(shop != null and shop.keeper == str(e["id"]), "%s: tienda %s atendida por %s" % [map_id, e["shop"], e["id"]])
	for shop_id in shops.all_ids():
		for row in shops.get_def(shop_id).stock:
			var item := items.get_def(str(row["item"]))
			_check(item != null and ResourceLoader.exists(item.icon_path) and not item.fact.is_empty(), "%s vende %s" % [shop_id, row["item"]])
			_check(int(row["price"]) > 0, "%s: precio de %s" % [shop_id, row["item"]])


## Encuentros con sprites; enemigos del mapa con encuentro válido; técnicas con dato real.
func _check_combat_data() -> void:
	for id in EncounterCatalog.all_ids():
		var enc := EncounterCatalog.load_encounter(id)
		_check(not enc.get("enemies", []).is_empty() and not BattleSheets.backdrop(str(enc.get("backdrop", ""))).is_empty(), "encuentro %s" % id)
		for enemy in enc.get("enemies", []):
			_check(ResourceLoader.exists(str(enemy.get("sprite", ""))) and ResourceLoader.exists(str(enemy.get("sprite_off", ""))), "%s: sprites de %s" % [id, enemy.get("id", "")])
	for map_id in MAPS.keys():
		for e in JsonDir.load_dict("res://assets/data/maps/%s.json" % map_id).get("entities", []):
			if str(e.get("type", "")) == "enemy":
				_check(not EncounterCatalog.load_encounter(str(e.get("encounter", ""))).is_empty(), "%s: %s lleva a un encuentro" % [map_id, e.get("id", "")])
				_check(ResourceLoader.exists(PROPS_DIR + str(e.get("sprite_done", "")) + ".png"), "%s: sprite apagado de %s" % [map_id, e.get("id", "")])
	var skills := SkillCatalog.new()
	skills.load_all()
	for skill in skills.all():
		_check(not skill.fact.is_empty() and not skill.description.is_empty(), "técnica %s con dato real" % skill.id)
	var missions: Node = root.get_node("MissionLog")
	for mission_id in missions.all_mission_ids():
		for obj in missions.get_def(mission_id).objectives:
			if obj.condition_type() == "win_battle":
				_check(not EncounterCatalog.load_encounter(obj.condition_value()).is_empty(), "%s: encuentro %s existe" % [mission_id, obj.condition_value()])
			if obj.condition_type() == "have_items":
				for item_id in obj.item_ids():
					_check(root.get_node("Inventory").catalog().get_def(item_id) != null, "%s: objeto %s existe" % [mission_id, item_id])


func _check_catalog_links() -> void:
	var notebook: Node = root.get_node("ScienceNotebook")
	var catalog: DestinationCatalog = notebook.get_catalog()
	var missions: Node = root.get_node("MissionLog")
	for mission_id in missions.all_mission_ids():
		var def: MissionDef = missions.get_def(mission_id)
		for obj in def.objectives:
			if obj.condition_type() == "scan_destination":
				_check(catalog.has_id(obj.condition_value()), "ficha para escaneo %s" % obj.condition_value())
		var unlock := str(def.rewards.get("unlock_destination_id", ""))
		if not unlock.is_empty():
			_check(catalog.has_id(unlock), "ficha desbloqueable %s" % unlock)
	for id in catalog.all_ids():
		var entry := catalog.get_entry(id)
		_check(not entry.scientific_facts.is_empty() and not entry.arcade_disclaimer.is_empty(), "ficha completa %s" % id)


func _check_challenges() -> void:
	var catalog := ChallengeCatalog.new()
	catalog.load_all()
	var F := ProbeOpcodes.FORWARD
	var solutions := {
		"launch_sequence": [[F], [F], [ProbeOpcodes.SCAN], [ProbeOpcodes.TURN_LEFT], [F], [F], [ProbeOpcodes.TRANSMIT]],
		"ice_drill": [[ProbeOpcodes.REPEAT_BEGIN, 4], [F], [ProbeOpcodes.COLLECT], [ProbeOpcodes.REPEAT_END], [F], [ProbeOpcodes.TRANSMIT]],
		"delta_samples": [
			[ProbeOpcodes.REPEAT_BEGIN, 6], [F], [ProbeOpcodes.IF_SAMPLE], [ProbeOpcodes.COLLECT], [ProbeOpcodes.IF_END],
			[ProbeOpcodes.REPEAT_END], [ProbeOpcodes.TRANSMIT],
		],
	}
	for id in solutions.keys():
		var def := catalog.get_def(id)
		_check(def != null, "reto %s cargado" % id)
		if def == null:
			continue
		var result := _run_program(def, solutions[id])
		_check(bool(result.get("victory", false)), "reto %s resoluble (%s)" % [id, result.get("message", "")])
	# Sin bucle, el taladro supera el límite de bloques
	var drill := catalog.get_def("ice_drill")
	var unrolled: Array = []
	for i in 4:
		unrolled.append([F])
		unrolled.append([ProbeOpcodes.COLLECT])
	unrolled.append([F])
	unrolled.append([ProbeOpcodes.TRANSMIT])
	var r2 := _run_program(drill, unrolled)
	_check(not bool(r2.get("victory", false)) and str(r2.get("message", "")).findn("máximo") >= 0, "taladro exige bucle")
	# Sin condición, RECOGER en casilla vacía falla
	var delta := catalog.get_def("delta_samples")
	var naive := [[ProbeOpcodes.REPEAT_BEGIN, 6], [F], [ProbeOpcodes.COLLECT], [ProbeOpcodes.REPEAT_END], [ProbeOpcodes.TRANSMIT]]
	var r3 := _run_program(delta, naive)
	_check(not bool(r3.get("victory", false)), "delta exige condición")
	# SI mal cerrado
	var program := ProbeProgram.new()
	program.append_op(ProbeOpcodes.IF_SAMPLE)
	program.append_op(ProbeOpcodes.REPEAT_END)
	_check(not program.validate_structure(true, true).is_empty(), "bloques cruzados rechazados")


func _run_program(def: ChallengeDef, ops: Array) -> Dictionary:
	var world := def.build_world()
	var program := ProbeProgram.new()
	for item in ops:
		program.append_op(str(item[0]), int(item[1]) if item.size() > 1 else 0)
	var interp := ProbeInterpreter.new()
	interp.setup(world, program, def.allow_loops, def.allow_conditions, def.max_blocks)
	return interp.run_all_sync()


func _check_scene(path: String) -> void:
	var packed := load(path) as PackedScene
	_check(packed != null, "escena %s" % path)
	if packed == null:
		return
	var node := packed.instantiate()
	root.add_child(node)
	await process_frame
	node.queue_free()
	await process_frame


func _check(ok: bool, label: String) -> void:
	if ok:
		print("[world] OK  %s" % label)
	else:
		printerr("[world] FAIL %s" % label)
		_failed += 1
