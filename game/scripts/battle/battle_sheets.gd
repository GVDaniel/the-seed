class_name BattleSheets
extends RefCounted
## Hojas de animación, efectos y fondos del combate (assets/data/combat/sheets.json).
## Convierte cada hoja en SpriteFrames (una animación por fila) y los guarda en caché.

const PATH := "res://assets/data/combat/sheets.json"

static var _data: Dictionary = {}
static var _frames: Dictionary = {}


static func data() -> Dictionary:
	if _data.is_empty() and FileAccess.file_exists(PATH):
		_data = JsonDir.load_dict(PATH)
	return _data


static func has_sheet(sheet_id: String) -> bool:
	var info: Dictionary = data().get("sheets", {}).get(sheet_id, {})
	return not info.is_empty() and ResourceLoader.exists(str(info.get("texture", "")))


## Píxel del cuadro que toca el suelo.
static func feet(sheet_id: String) -> Vector2:
	var info: Dictionary = data().get("sheets", {}).get(sheet_id, {})
	var f: Array = info.get("feet", info.get("frame", [32, 32]))
	return Vector2(float(f[0]), float(f[1]))


static func frame_size(sheet_id: String) -> Vector2:
	var info: Dictionary = data().get("sheets", {}).get(sheet_id, {})
	var f: Array = info.get("frame", [32, 32])
	return Vector2(float(f[0]), float(f[1]))


static func sprite_frames(sheet_id: String) -> SpriteFrames:
	if _frames.has(sheet_id):
		return _frames[sheet_id]
	var info: Dictionary = data().get("sheets", {}).get(sheet_id, {})
	var tex: Texture2D = load(str(info["texture"]))
	var size := frame_size(sheet_id)
	var sf := SpriteFrames.new()
	sf.remove_animation("default")
	var anims: Dictionary = info.get("anims", {})
	for anim_name in anims.keys():
		var a: Dictionary = anims[anim_name]
		sf.add_animation(anim_name)
		sf.set_animation_speed(anim_name, float(a.get("fps", 8)))
		sf.set_animation_loop(anim_name, bool(a.get("loop", false)))
		var row := int(a.get("row", 0))
		for i in int(a.get("frames", 1)):
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2(Vector2(i * size.x, row * size.y), size)
			sf.add_frame(anim_name, at)
	_frames[sheet_id] = sf
	return sf


static func fx_frames(fx_id: String) -> SpriteFrames:
	var key := "fx:" + fx_id
	if _frames.has(key):
		return _frames[key]
	var info: Dictionary = data().get("fx", {}).get(fx_id, {})
	if info.is_empty() or not ResourceLoader.exists(str(info.get("texture", ""))):
		return null
	var tex: Texture2D = load(str(info["texture"]))
	var f: Array = info.get("frame", [32, 32])
	var size := Vector2(float(f[0]), float(f[1]))
	var sf := SpriteFrames.new()
	sf.set_animation_speed("default", float(info.get("fps", 16)))
	sf.set_animation_loop("default", fx_id == "orb")
	for i in int(info.get("frames", 1)):
		var at := AtlasTexture.new()
		at.atlas = tex
		at.region = Rect2(Vector2(i * size.x, 0), size)
		sf.add_frame("default", at)
	_frames[key] = sf
	return sf


## Capas del fondo: {sky, far, ground, fg, flat}. Acepta un id del manifiesto o una ruta res://.
static func backdrop(id_or_path: String) -> Dictionary:
	if id_or_path.begins_with("res://"):
		return {"flat": id_or_path}
	var out: Dictionary = {}
	var info: Dictionary = data().get("backdrops", {}).get(id_or_path, {})
	for key in info.keys():
		if ResourceLoader.exists(str(info[key])):
			out[key] = str(info[key])
	return out


static func shadow_texture() -> Texture2D:
	var path := "res://assets/art/battle/shadow.png"
	return load(path) if ResourceLoader.exists(path) else null
