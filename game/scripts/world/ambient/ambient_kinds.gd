class_name AmbientKinds
extends RefCounted
## Catálogo de vehículos, máquinas y naves de ambiente (assets/data/ambient/kinds.json)
## y de las hojas de peatones por planeta (assets/data/ambient/crowd.json).
## Un kind sin textura se ignora en silencio: el mapa funciona igual sin ese arte.

const KINDS_PATH := "res://assets/data/ambient/kinds.json"
const CROWD_PATH := "res://assets/data/ambient/crowd.json"

static var _kinds: Dictionary = {}
static var _crowd: Dictionary = {}
static var _loaded: bool = false
## Kinds registrados en memoria (pruebas): tienen prioridad sobre el JSON.
static var _extra: Dictionary = {}


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	if FileAccess.file_exists(KINDS_PATH):
		_kinds = JsonDir.load_dict(KINDS_PATH)
	if FileAccess.file_exists(CROWD_PATH):
		_crowd = JsonDir.load_dict(CROWD_PATH)


## Vuelve a leer los JSON (si el arte aparece mientras el juego corre, p. ej. en pruebas).
static func reload() -> void:
	_loaded = false
	_kinds = {}
	_crowd = {}
	_load()


## info = {texture: Texture2D o ruta, frame: [w, h], frames, fps, rows: {right, down, up}, shadow: [w, h], light}.
static func register(kind: String, info: Dictionary) -> void:
	_extra[kind] = info


static func unregister(kind: String) -> void:
	_extra.erase(kind)


## Definición lista para usar (con "texture" ya cargada) o {} si falta el arte.
static func get_def(kind: String) -> Dictionary:
	_load()
	var info: Dictionary = _extra.get(kind, _kinds.get(kind, {}))
	if info.is_empty():
		return {}
	var tex: Variant = info.get("texture", null)
	if tex is String:
		if not ResourceLoader.exists(tex):
			return {}
		tex = load(tex)
	if not tex is Texture2D:
		return {}
	var out := info.duplicate()
	out["texture"] = tex
	return out


static func available(kinds: Array) -> PackedStringArray:
	var out := PackedStringArray()
	for k in kinds:
		if not get_def(str(k)).is_empty():
			out.append(str(k))
	return out


## Hojas de peatones de un planeta (earth | moon | mars) que existen de verdad, como Texture2D.
## Las pruebas registran texturas en memoria con register("crowd:<planeta>", {"sheets": [Texture2D…]}).
static func crowd_sheets(planet: String) -> Array[Texture2D]:
	_load()
	var out: Array[Texture2D] = []
	var list: Array = (_extra["crowd:" + planet] as Dictionary).get("sheets", []) \
		if _extra.has("crowd:" + planet) else _crowd.get(planet, [])
	for p in list:
		if p is Texture2D:
			out.append(p)
		elif ResourceLoader.exists(str(p)):
			out.append(load(str(p)))
	return out
