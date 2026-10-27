class_name BattleStage
extends Node2D
## El campo de combate: fondo en capas, cámara (enfoque con zoom, sacudidas, zoom de impacto),
## combatientes ordenados por profundidad, efectos, rayos y las chispas solares en el suelo.
## Coordenadas del campo: 428×240, dibujado a ×3.

const FIELD := Vector2(428, 240)
const ZOOM := 3.0
## Donde flotan las chispas solares (entre el grupo y los enemigos).
const ORB_POOL := Vector2(176, 214)

var camera: Camera2D
var actors: Node2D
var fx_layer: Node2D
var _orb_nodes: Array[Node2D] = []
var _marker: Polygon2D
var _shake: float = 0.0
var _focus: Vector2 = FIELD * 0.5
var _zoom: float = ZOOM
var _punch: float = 0.0
var _t: float = 0.0
var _fast: bool = false
var _dust: CPUParticles2D


func build(backdrop_id: String, fast: bool) -> void:
	_fast = fast
	var under := ColorRect.new()
	under.color = Color("0b1220")
	under.position = Vector2(-60, -60)
	under.size = FIELD + Vector2(120, 120)
	under.z_index = -11
	add_child(under)
	var layers := BattleSheets.backdrop(backdrop_id)
	if layers.is_empty():
		layers = BattleSheets.backdrop("res://assets/art/battle/mars_canyon.png")
	if layers.has("sky"):
		_layer(str(layers["sky"]), -10)
		_layer(str(layers.get("far", "")), -9)
		_layer(str(layers.get("ground", "")), -8)
	else:
		_layer(str(layers.get("flat", "")), -8)

	actors = Node2D.new()
	actors.y_sort_enabled = true
	add_child(actors)
	fx_layer = Node2D.new()
	fx_layer.z_index = 5
	add_child(fx_layer)
	if layers.has("fg"):
		_layer(str(layers["fg"]), 8)

	_dust = CPUParticles2D.new()
	_dust.amount = 26
	_dust.lifetime = 7.0
	_dust.preprocess = 7.0
	_dust.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	_dust.emission_rect_extents = Vector2(FIELD.x * 0.6, FIELD.y * 0.5)
	_dust.position = FIELD * 0.5
	_dust.direction = Vector2(-1, -0.15)
	_dust.spread = 12.0
	_dust.gravity = Vector2.ZERO
	_dust.initial_velocity_min = 6.0
	_dust.initial_velocity_max = 16.0
	_dust.scale_amount_min = 1.0
	_dust.scale_amount_max = 1.0
	_dust.color = Color(1.0, 0.82, 0.62, 0.35)
	_dust.z_index = 6
	add_child(_dust)

	_marker = Polygon2D.new()
	_marker.polygon = PackedVector2Array([Vector2(-4, -6), Vector2(4, -6), Vector2(0, 0)])
	_marker.color = HalUi.GOLD
	_marker.z_index = 9
	_marker.visible = false
	add_child(_marker)

	camera = Camera2D.new()
	camera.zoom = Vector2(ZOOM, ZOOM)
	camera.position = _focus
	add_child(camera)
	camera.make_current()


func _layer(path: String, z: int) -> void:
	if path.is_empty() or not ResourceLoader.exists(path):
		return
	var s := Sprite2D.new()
	s.texture = load(path)
	s.centered = false
	s.z_index = z
	add_child(s)


func _process(delta: float) -> void:
	_t += delta
	if camera == null:
		return
	var shake := Vector2.ZERO
	if _shake > 0.0:
		shake = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * _shake
		_shake = maxf(0.0, _shake - delta * 18.0)
	var k := minf(1.0, delta * 4.0)
	camera.position = camera.position.lerp(_focus, k)
	var z := lerpf(camera.zoom.x - _punch, _zoom, k) + _punch
	camera.zoom = Vector2(z, z)
	camera.offset = shake
	for i in _orb_nodes.size():
		var orb := _orb_nodes[i]
		if is_instance_valid(orb) and not orb.has_meta("flying"):
			orb.position = _orb_slot(i) + Vector2(0, sin(_t * 2.2 + i) * 1.5)
	if _marker.visible:
		_marker.position.y = float(_marker.get_meta("y", 0.0)) + sin(_t * 8.0) * 2.0


# ------------------------------------------------------------ cámara

## Acerca la cámara hacia un punto del campo sin enseñar los bordes del fondo.
func focus(point: Vector2, zoom_in: float = 0.22) -> void:
	_zoom = ZOOM + zoom_in
	var margin := FIELD * 0.5 * (1.0 - ZOOM / _zoom)
	var c := FIELD * 0.5
	var d := point - c
	_focus = c + Vector2(clampf(d.x, -margin.x, margin.x), clampf(d.y, -margin.y, margin.y))


func reset_focus() -> void:
	_zoom = ZOOM
	_focus = FIELD * 0.5


func shake(strength: float) -> void:
	if not _fast:
		_shake = maxf(_shake, strength)


## Golpe de zoom breve en los impactos fuertes.
func punch(amount: float = 0.12) -> void:
	if _fast or camera == null:
		return
	var t := create_tween()
	t.tween_property(self, "_punch", amount, 0.05)
	t.tween_property(self, "_punch", 0.0, 0.22).set_trans(Tween.TRANS_QUAD)


## Posición en pantalla (para el HUD) de un punto del campo.
func to_screen(field_point: Vector2) -> Vector2:
	return get_viewport().get_canvas_transform() * field_point


# ------------------------------------------------------------ efectos

func spawn_fx(fx_id: String, at: Vector2, flip: bool = false, scale_factor: float = 1.0) -> void:
	if _fast:
		return
	var frames := BattleSheets.fx_frames(fx_id)
	if frames == null:
		_burst(at, _fx_color(fx_id))
		return
	var fx := AnimatedSprite2D.new()
	fx.sprite_frames = frames
	fx.position = at
	fx.flip_h = flip
	fx.scale = Vector2.ONE * scale_factor
	fx_layer.add_child(fx)
	fx.play("default")
	fx.animation_finished.connect(fx.queue_free)


func _fx_color(fx_id: String) -> Color:
	match fx_id:
		"zap":
			return HalUi.CYAN
		"light":
			return HalUi.GOLD
		"heal":
			return Color("7dff9a")
	return Color.WHITE


## Chispas de partículas (para todo golpe, encima del efecto animado).
func _burst(at: Vector2, color: Color, amount: int = 12) -> void:
	var p := CPUParticles2D.new()
	p.position = at
	p.one_shot = true
	p.emitting = true
	p.amount = amount
	p.lifetime = 0.45
	p.explosiveness = 1.0
	p.spread = 180.0
	p.initial_velocity_min = 30.0
	p.initial_velocity_max = 80.0
	p.gravity = Vector2(0, 120)
	p.color = color
	fx_layer.add_child(p)
	get_tree().create_timer(0.8).timeout.connect(p.queue_free)


func sparks(at: Vector2, color: Color, amount: int = 12) -> void:
	if not _fast:
		_burst(at, color, amount)


## Rayo desde el lanzador (luz del escáner o descarga eléctrica).
func beam(from: Vector2, to: Vector2, color: Color, electric: bool) -> void:
	if _fast:
		return
	var line := Line2D.new()
	line.width = 2.0
	line.default_color = color
	line.z_index = 4
	var pts := PackedVector2Array([from])
	if electric:
		var steps := 7
		for i in range(1, steps):
			var p := from.lerp(to, float(i) / steps)
			pts.append(p + Vector2(randf_range(-3, 3), randf_range(-5, 5)))
	pts.append(to)
	line.points = pts
	var glow := line.duplicate() as Line2D
	glow.width = 6.0
	glow.default_color = Color(color, 0.3)
	fx_layer.add_child(glow)
	fx_layer.add_child(line)
	var t := create_tween()
	t.tween_interval(0.08)
	t.tween_property(line, "modulate:a", 0.0, 0.18)
	t.parallel().tween_property(glow, "modulate:a", 0.0, 0.18)
	t.tween_callback(func() -> void:
		line.queue_free()
		glow.queue_free())


## Destello de pantalla completa del campo (combos, cerraduras rotas).
func flash_screen(color: Color) -> void:
	if _fast:
		return
	var r := ColorRect.new()
	r.color = Color(color, 0.0)
	r.position = Vector2(-40, -40)
	r.size = FIELD + Vector2(80, 80)
	r.z_index = 20
	add_child(r)
	var t := create_tween()
	t.tween_property(r, "color:a", 0.45, 0.04)
	t.tween_property(r, "color:a", 0.0, 0.3)
	t.tween_callback(r.queue_free)


# ------------------------------------------------------------ chispas solares

func _orb_slot(i: int) -> Vector2:
	return ORB_POOL + Vector2((i - 2) * 11, (i % 2) * 4)


func _make_orb() -> Node2D:
	var frames := BattleSheets.fx_frames("orb")
	if frames != null:
		var a := AnimatedSprite2D.new()
		a.sprite_frames = frames
		a.play("default")
		a.z_index = 7
		return a
	var p := Polygon2D.new()
	p.polygon = PackedVector2Array([Vector2(0, -4), Vector2(3, 0), Vector2(0, 4), Vector2(-3, 0)])
	p.color = HalUi.GOLD
	p.z_index = 7
	return p


## Ajusta las chispas visibles; las nuevas salen volando desde el golpe.
func set_orbs(count: int, from: Vector2 = Vector2.ZERO) -> void:
	_orb_nodes = _orb_nodes.filter(func(n: Node2D) -> bool: return is_instance_valid(n))
	while _orb_nodes.size() < count:
		var orb := _make_orb()
		var slot := _orb_slot(_orb_nodes.size())
		add_child(orb)
		_orb_nodes.append(orb)
		if _fast or from == Vector2.ZERO:
			orb.position = slot
			continue
		orb.position = from
		orb.set_meta("flying", true)
		var mid := (from + slot) * 0.5 + Vector2(0, -40)
		var t := create_tween()
		t.tween_method(func(k: float) -> void:
			orb.position = from.lerp(mid, k).lerp(mid.lerp(slot, k), k), 0.0, 1.0, 0.5)
		t.tween_callback(func() -> void: orb.remove_meta("flying"))
	while _orb_nodes.size() > count:
		_orb_nodes.pop_back().queue_free()


## Las chispas gastadas vuelan hacia quien potencia su acción.
func spend_orbs(amount: int, to: Vector2) -> void:
	for i in amount:
		_orb_nodes = _orb_nodes.filter(func(n: Node2D) -> bool: return is_instance_valid(n))
		if _orb_nodes.is_empty():
			return
		var orb: Node2D = _orb_nodes.pop_back()
		if _fast:
			orb.queue_free()
			continue
		orb.set_meta("flying", true)
		var t := create_tween()
		t.tween_property(orb, "position", to, 0.25).set_delay(i * 0.06).set_trans(Tween.TRANS_QUAD)
		t.tween_callback(orb.queue_free)


# ------------------------------------------------------------ selección

func mark(point: Vector2) -> void:
	_marker.visible = true
	_marker.position = point
	_marker.set_meta("y", point.y)


func unmark() -> void:
	_marker.visible = false
