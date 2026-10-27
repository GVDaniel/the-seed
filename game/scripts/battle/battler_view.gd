class_name BattlerView
extends Node2D
## Figura de un combatiente en el campo (coordenadas del campo, 428×240). Solo animación:
## la posición del nodo son los pies; idle/run/attack/cast/hurt/block/ko/victory/windup/charge/off.

const FLASH_SHADER := """
shader_type canvas_item;
uniform float flash : hint_range(0.0, 1.0) = 0.0;
uniform vec4 flash_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
void fragment() {
	vec4 c = COLOR;
	COLOR = vec4(mix(c.rgb, flash_color.rgb, flash), c.a);
}
"""

static var _shader: Shader

var uid: String = ""
var home: Vector2 = Vector2.ZERO
var facing_left: bool = false
var sprite: AnimatedSprite2D
var _static: Sprite2D
var _shadow: Sprite2D
var _mat: ShaderMaterial
var _hover: float = 0.0
var _t: float = 0.0
var _down: bool = false
var _stun_stars: Node2D
var _shield: Node2D
var _height: float = 32.0
var _fallback_off: Texture2D


func setup_sheet(sheet_id: String, left: bool, hover: float = 0.0) -> void:
	facing_left = left
	_hover = hover
	_add_shadow()
	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = BattleSheets.sprite_frames(sheet_id)
	sprite.centered = false
	var feet := BattleSheets.feet(sheet_id)
	var size := BattleSheets.frame_size(sheet_id)
	_height = feet.y
	sprite.offset = -feet
	sprite.flip_h = false
	sprite.material = _material()
	add_child(sprite)
	if facing_left != _sheet_faces_left(sheet_id):
		sprite.flip_h = true
		sprite.offset.x = -(size.x - feet.x)
	play("idle")


## Sin hoja de combate: textura fija (arte antiguo).
func setup_static(texture: Texture2D, left: bool, scale_factor: float, hover: float = 0.0,
		off_texture: Texture2D = null) -> void:
	facing_left = left
	_hover = hover
	_add_shadow()
	_static = Sprite2D.new()
	_static.texture = texture
	_static.flip_h = left
	_static.scale = Vector2(scale_factor, scale_factor)
	_static.material = _material()
	if texture != null:
		_height = texture.get_height() * scale_factor
		_static.offset = Vector2(0, -texture.get_height() * 0.5)
	add_child(_static)
	_fallback_off = off_texture


func _sheet_faces_left(sheet_id: String) -> bool:
	return sheet_id in ["ah7", "drone"]


func _add_shadow() -> void:
	_shadow = Sprite2D.new()
	_shadow.texture = BattleSheets.shadow_texture()
	_shadow.modulate = Color(1, 1, 1, 0.8)
	_shadow.z_index = -1
	add_child(_shadow)


func _material() -> ShaderMaterial:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = FLASH_SHADER
	_mat = ShaderMaterial.new()
	_mat.shader = _shader
	return _mat


func _body() -> Node2D:
	return sprite if sprite != null else _static


func height() -> float:
	return _height


func top_point() -> Vector2:
	return position + Vector2(0, -_height - _hover - 4)


func center_point() -> Vector2:
	return position + Vector2(0, -_height * 0.5 - _hover)


func _process(delta: float) -> void:
	_t += delta
	var body := _body()
	if body != null and _hover > 0.0 and not _down:
		body.position.y = -_hover + sin(_t * 2.6) * 2.0
	if _stun_stars != null:
		_stun_stars.rotation += delta * 3.0


func has_anim(anim_name: String) -> bool:
	return sprite != null and sprite.sprite_frames.has_animation(anim_name)


func play(anim_name: String) -> void:
	if sprite == null:
		return
	if not sprite.sprite_frames.has_animation(anim_name):
		anim_name = "idle"
	if sprite.sprite_frames.has_animation(anim_name):
		sprite.play(anim_name)


## Reproduce una animación sin bucle y espera a que acabe (o a la duración indicada).
func play_once(anim_name: String, fast: bool) -> void:
	if fast or sprite == null or not has_anim(anim_name):
		return
	sprite.play(anim_name)
	var sf := sprite.sprite_frames
	var seconds := float(sf.get_frame_count(anim_name)) / maxf(1.0, sf.get_animation_speed(anim_name))
	await get_tree().create_timer(seconds).timeout


## Se queda en un cuadro (p. ej. la preparación de un golpe).
func hold(anim_name: String, frame: int = 0) -> void:
	if sprite == null or not has_anim(anim_name):
		return
	sprite.animation = anim_name
	sprite.frame = mini(frame, sprite.sprite_frames.get_frame_count(anim_name) - 1)
	sprite.pause()


func idle() -> void:
	if not _down:
		play("idle")


func move_to(target: Vector2, duration: float, fast: bool) -> void:
	if fast:
		position = target
		return
	if target.distance_to(position) > 2.0:
		play("run")
	var t := create_tween()
	t.tween_property(self, "position", target, duration).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	await t.finished


func go_home(fast: bool) -> void:
	if position.distance_to(home) < 1.0:
		idle()
		return
	await move_to(home, 0.28, fast)
	idle()


func flash(color: Color, fast: bool, duration: float = 0.16) -> void:
	if fast or _mat == null:
		return
	_mat.set_shader_parameter("flash_color", color)
	var t := create_tween()
	t.tween_method(func(v: float) -> void: _mat.set_shader_parameter("flash", v), 0.9, 0.0, duration)


## Encaja un golpe: destello, retroceso y animación de daño (o de bloqueo).
func hit(fast: bool, blocked: bool = false) -> void:
	if fast:
		return
	flash(Color.WHITE, fast)
	play("block" if blocked and has_anim("block") else "hurt")
	var push := 4.0 if facing_left else -4.0
	var body := _body()
	if body != null:
		var t := create_tween()
		t.tween_property(body, "position:x", push, 0.05)
		t.tween_property(body, "position:x", 0.0, 0.16).set_trans(Tween.TRANS_BACK)
	await get_tree().create_timer(0.32).timeout
	if not _down:
		idle()


func freeze(seconds: float, fast: bool) -> void:
	if fast or sprite == null:
		return
	sprite.speed_scale = 0.0
	await get_tree().create_timer(seconds).timeout
	sprite.speed_scale = 1.0


func set_down(down: bool) -> void:
	_down = down
	if sprite != null:
		if down:
			play("off" if has_anim("off") else "ko")
		else:
			play("idle")
		sprite.position.y = 0.0 if down else sprite.position.y
	elif _static != null:
		if down and _fallback_off != null:
			_static.texture = _fallback_off
		_static.modulate = Color(0.6, 0.6, 0.66) if down else Color.WHITE
	if _shadow != null:
		_shadow.modulate.a = 0.5 if down else 0.8
	if down:
		set_stunned(false)
		set_shielded(false)


func set_stunned(stunned: bool) -> void:
	if stunned and _stun_stars == null:
		_stun_stars = Node2D.new()
		_stun_stars.position = Vector2(0, -_height - _hover - 2)
		for i in 3:
			var star := Polygon2D.new()
			star.polygon = PackedVector2Array([Vector2(0, -2), Vector2(1, 0), Vector2(0, 2), Vector2(-1, 0)])
			star.color = HalUi.GOLD
			star.position = Vector2(8, 0).rotated(TAU * i / 3.0)
			star.scale = Vector2(1.5, 1.5)
			_stun_stars.add_child(star)
		add_child(_stun_stars)
	elif not stunned and _stun_stars != null:
		_stun_stars.queue_free()
		_stun_stars = null


## Placas de escudo (escudo de chatarra del grupo o blindaje enemigo).
func set_shielded(on: bool, color: Color = HalUi.CYAN) -> void:
	if on and _shield == null:
		_shield = Node2D.new()
		var w := maxf(14.0, _height * 0.42)
		for i in 5:
			var plate := Polygon2D.new()
			var a := lerpf(-1.1, 1.1, i / 4.0)
			var dir := -1.0 if facing_left else 1.0
			var p := Vector2(cos(a) * w * dir, sin(a) * _height * 0.5)
			plate.polygon = PackedVector2Array([p + Vector2(0, -4), p + Vector2(2 * dir, -2),
				p + Vector2(2 * dir, 3), p + Vector2(0, 5)])
			plate.color = Color(color, 0.75)
			_shield.add_child(plate)
		_shield.position = Vector2(0, -_height * 0.5 - _hover)
		add_child(_shield)
		if is_inside_tree():
			_shield.modulate.a = 0.0
			create_tween().tween_property(_shield, "modulate:a", 1.0, 0.25)
	elif not on and _shield != null:
		var s := _shield
		_shield = null
		if is_inside_tree():
			var t := create_tween()
			t.tween_property(s, "modulate:a", 0.0, 0.2)
			t.tween_callback(s.queue_free)
		else:
			s.queue_free()


func is_down() -> bool:
	return _down
