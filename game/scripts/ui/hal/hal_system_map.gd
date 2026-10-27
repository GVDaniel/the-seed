class_name HalSystemMap
extends Control
## Ruta de ASTRA: de la Tierra a TRAPPIST-1e. Marca dónde estás, lo visitado y el objetivo.
## No está a escala (las distancias reales van en el texto de la pestaña).

const PLAYABLE_CHAPTERS := 3
const STOPS := [
	{"id": "earth", "name": "Tierra", "texture": "res://assets/art/planets/earth_withered.png", "chapter": 1},
	{"id": "station_aurora", "name": "Aurora", "texture": "res://assets/art/planets/station_aurora.png", "chapter": 2},
	{"id": "moon", "name": "Luna", "texture": "res://assets/art/planets/moon.png", "chapter": 2},
	{"id": "mars", "name": "Marte", "texture": "res://assets/art/planets/mars.png", "chapter": 3},
	{"id": "jupiter", "name": "Júpiter", "texture": "", "chapter": 4},
	{"id": "saturn", "name": "Saturno", "texture": "", "chapter": 5},
	{"id": "heliopause", "name": "Heliopausa", "texture": "", "chapter": 6},
	{"id": "trappist1e", "name": "TRAPPIST-1e", "texture": "res://assets/art/planets/trappist1e.png", "chapter": 8},
]
## Personaje → parada donde se le encuentra.
const NPC_STOPS := {"lucia": "earth", "vega": "station_aurora", "kai": "moon", "osei": "mars", "bruno": "mars",
	"yusuf": "mars", "nia": "mars", "ada": "mars"}

var _textures: Dictionary = {}
var _t: float = 0.0


func _ready() -> void:
	for stop in STOPS:
		var path := str(stop["texture"])
		if not path.is_empty() and ResourceLoader.exists(path):
			_textures[stop["id"]] = load(path)


func _process(delta: float) -> void:
	if is_visible_in_tree():
		_t += delta
		queue_redraw()


func current_stop() -> String:
	var loc := str(App.game_state().location)
	if loc == "space":
		var near := str(App.router().space_spawn_near)
		return near if not near.is_empty() else "earth"
	return str(App.game_state().region)


func objective_stop() -> String:
	var summary: Dictionary = App.story().objective_summary()
	var target := str(summary.get("target", ""))
	if NPC_STOPS.has(target):
		return NPC_STOPS[target]
	for key in ["target", "location"]:
		var v := str(summary.get(key, ""))
		for stop in STOPS:
			if stop["id"] == v or v.begins_with(str(stop["id"]) + "_"):
				return str(stop["id"])
	return ""


func is_visited(stop_id: String) -> bool:
	match stop_id:
		"earth":
			return true
		"station_aurora":
			return App.story().has_met("vega")
		_:
			return App.game_state().has_flag("arrived_%s" % stop_id)


func _draw() -> void:
	var n := STOPS.size()
	var margin := 70.0
	var step := (size.x - margin * 2) / float(n - 1)
	var points: Array[Vector2] = []
	for i in n:
		points.append(Vector2(margin + step * i, size.y * 0.42 + sin(i * 1.3) * size.y * 0.12))
	var current := current_stop()
	var objective := objective_stop()
	for i in n - 1:
		var reached := int(STOPS[i + 1]["chapter"]) <= PLAYABLE_CHAPTERS and is_visited(str(STOPS[i + 1]["id"]))
		_dotted(points[i], points[i + 1], HalUi.CYAN if reached else HalUi.LOCKED, reached)
	for i in n:
		var stop: Dictionary = STOPS[i]
		var id := str(stop["id"])
		var at := points[i]
		var locked := int(stop["chapter"]) > PLAYABLE_CHAPTERS
		var r := 30.0 if id != "trappist1e" else 38.0
		if _textures.has(id):
			var tint := Color(0.35, 0.38, 0.45) if locked else (Color.WHITE if is_visited(id) else Color(0.7, 0.75, 0.8))
			draw_texture_rect(_textures[id], Rect2(at - Vector2(r, r), Vector2(r, r) * 2), false, tint)
		else:
			draw_circle(at, r * 0.7, Color(0.12, 0.16, 0.22))
			draw_arc(at, r * 0.7, 0, TAU, 24, HalUi.LOCKED, 2.0)
			HalUi.draw_text(self, at + Vector2(-5, 7), "?", 22, HalUi.LOCKED)
		var name_text := str(stop["name"]) if not locked or id == "trappist1e" else "Capítulo %d" % int(stop["chapter"])
		var name_color := HalUi.LOCKED if locked and id != "trappist1e" else (HalUi.GOLD if id == "trappist1e" else HalUi.TEXT)
		HalUi.draw_text(self, at + Vector2(-name_text.length() * 4.0, r + 22), name_text, 15, name_color)
		if id == current:
			var pulse := 1.0 + 0.08 * sin(_t * 4.0)
			draw_arc(at, (r + 8) * pulse, 0, TAU, 32, HalUi.RED, 3.0)
			var here := "En órbita" if str(App.game_state().location) == "space" else "Estás aquí"
			HalUi.draw_text(self, at + Vector2(-here.length() * 4.0, -r - 16), here, 14, HalUi.RED)
		if id == objective and id != current:
			var bob := sin(_t * 5.0) * 4.0
			var tip := at + Vector2(0, -r - 10 + bob)
			draw_colored_polygon(PackedVector2Array([tip, tip + Vector2(-9, -14), tip + Vector2(9, -14)]), HalUi.GOLD)
			HalUi.draw_text(self, tip + Vector2(-32, -20), "Objetivo", 14, HalUi.GOLD)


func _dotted(a: Vector2, b: Vector2, color: Color, solid: bool) -> void:
	if solid:
		draw_line(a, b, color, 2.0)
		return
	var length := a.distance_to(b)
	var dir := (b - a) / length
	var d := 0.0
	while d < length:
		draw_line(a + dir * d, a + dir * minf(d + 6.0, length), color, 2.0)
		d += 14.0
