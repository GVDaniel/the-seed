class_name SurfaceEntitySpawner
extends RefCounted
## Crea NPCs, puntos de escaneo, objetos, puertas, enemigos, surtidores, luces y props
## a partir de la lista "entities" del mapa.
## Cualquier entidad puede llevar "light": {color, offset, scale, energy, flicker}.

const PROPS_DIR := "res://assets/art/props/"
const SHIP_SPRITE := "res://assets/art/ship/astra.png"

## id -> {"node": Node2D, "data": Dictionary}
var entities: Dictionary = {}
## id -> Vector2 (posición global de aparición)
var spawns: Dictionary = {}


static func tile_to_world(pos: Variant) -> Vector2:
	var p := Vector2(float(pos[0]), float(pos[1]))
	return Vector2(p.x * TileCatalog.TILE + TileCatalog.TILE * 0.5, (p.y + 1.0) * TileCatalog.TILE)


func spawn_all(list: Array, container: Node2D) -> void:
	for data in list:
		if typeof(data) != TYPE_DICTIONARY:
			continue
		_spawn(data, container)


func _spawn(data: Dictionary, container: Node2D) -> void:
	var type := str(data.get("type", "prop"))
	var id := str(data.get("id", ""))
	var pos := tile_to_world(data.get("pos", [0, 0]))
	var node: Node2D
	match type:
		"spawn":
			spawns[id] = pos
			return
		"npc":
			node = _make_npc(data)
		"scan":
			node = _make_scan(data)
		"item", "terminal", "ship", "object", "sign", "door", "enemy", "service":
			node = _make_interactable(type, data)
		_:
			node = Node2D.new()
	node.name = id if not id.is_empty() else type.capitalize()
	node.position = pos
	# Piezas planas del suelo (plataformas, alfombras) bajo todo lo demás.
	node.z_index = int(data.get("z", 0))
	_add_sprite(node, data, type)
	_add_solid(node, data)
	if typeof(data.get("light", null)) == TYPE_DICTIONARY:
		node.add_child(NeonLight.from_data(data["light"]))
	container.add_child(node)
	if not id.is_empty():
		entities[id] = {"node": node, "data": data}


func _make_npc(data: Dictionary) -> Node2D:
	var npc := NpcActor.new()
	var id := str(data.get("id", ""))
	var character: CharacterDef = App.story().characters().get_def(id)
	npc.target_id = id
	npc.kind = "npc"
	npc.sheet_path = character.sprite_path if character != null else ""
	npc.default_facing = str(data.get("facing", "down"))
	var who := character.display_name if character != null else id
	npc.prompt = ("Comprar a %s" if data.has("shop") else "Hablar con %s") % who
	npc.radius = float(data.get("radius", 28.0))
	npc.wander_radius = float(data.get("wander", 0.0)) * TileCatalog.TILE
	return npc


func _make_scan(data: Dictionary) -> Node2D:
	var point := ScanPoint.new()
	point.destination_id = str(data.get("id", ""))
	point.scan_radius = float(data.get("radius", 34.0))
	return point


func _make_interactable(type: String, data: Dictionary) -> Node2D:
	var it := Interactable.new()
	it.target_id = str(data.get("id", ""))
	it.kind = type
	it.payload = str(data.get("challenge_id", ""))
	it.radius = float(data.get("radius", 28.0))
	it.prompt = str(data.get("prompt", _default_prompt(type)))
	if type == "item" and App.game_state().has_item(it.target_id):
		it.visible = false
	if type == "door":
		NavAlias.attach(it, str(data.get("target", "")))
	return it


func _default_prompt(type: String) -> String:
	match type:
		"terminal":
			return "Usar terminal de programación"
		"ship":
			return "Subir a ASTRA"
		"item":
			return "Recoger"
		"sign":
			return "Leer"
		"door":
			return "Entrar"
		"enemy":
			return "Enfrentarte"
		"service":
			return "Estación de servicio"
	return "Usar"


func _add_sprite(node: Node2D, data: Dictionary, type: String) -> void:
	var sprite_name := str(data.get("sprite", ""))
	if type == "ship":
		sprite_name = "astra"
	elif type == "terminal" and sprite_name.is_empty():
		sprite_name = "terminal"
	if type == "object" or type == "enemy":
		var flag := str(data.get("done_flag", ""))
		if not flag.is_empty() and App.game_state().has_flag(flag):
			sprite_name = str(data.get("sprite_done", sprite_name))
	if sprite_name.is_empty():
		return
	var path := SHIP_SPRITE if sprite_name == "astra" else PROPS_DIR + sprite_name + ".png"
	if not ResourceLoader.exists(path):
		push_warning("SurfaceEntitySpawner: falta sprite %s" % path)
		return
	var sprite := Sprite2D.new()
	sprite.name = "Sprite"
	sprite.texture = load(path)
	sprite.offset = Vector2(0, -sprite.texture.get_height() * 0.5)
	node.add_child(sprite)


func _add_solid(node: Node2D, data: Dictionary) -> void:
	var solid: Variant = data.get("solid", null)
	if typeof(solid) != TYPE_ARRAY or (solid as Array).size() < 2:
		return
	var w := float(solid[0]) * TileCatalog.TILE
	var h := float(solid[1]) * TileCatalog.TILE
	var body := StaticBody2D.new()
	body.collision_layer = TileCatalog.PHYSICS_LAYER_WORLD
	body.collision_mask = 0
	var shape := CollisionShape2D.new()
	var box := RectangleShape2D.new()
	box.size = Vector2(w, h)
	shape.shape = box
	shape.position = Vector2(0, -h * 0.5)
	body.add_child(shape)
	node.add_child(body)


func set_sprite(entity_id: String, sprite_name: String) -> void:
	if not entities.has(entity_id):
		return
	var node: Node2D = entities[entity_id]["node"]
	var sprite := node.get_node_or_null("Sprite") as Sprite2D
	var path := PROPS_DIR + sprite_name + ".png"
	if sprite != null and ResourceLoader.exists(path):
		sprite.texture = load(path)
		sprite.offset = Vector2(0, -sprite.texture.get_height() * 0.5)
