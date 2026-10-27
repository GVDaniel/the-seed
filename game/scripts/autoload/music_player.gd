extends Node
## Música de fondo por pista (assets/audio/music/<pista>.ogg) con fundido cruzado.
## Cada escena pide su pista: menú/cinemáticas «title», superficie «mission», espacio «space».

const MUSIC_DIR := "res://assets/audio/music/"
const FADE_OUT_TIME := 0.7
const FADE_IN_TIME := 1.2
const SILENT_DB := -40.0

var current_track: String = ""
var _players: Array[AudioStreamPlayer] = []
var _active: int = 0
var _tween: Tween


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	AudioSettings.ensure_buses()
	for i in 2:
		var p := AudioStreamPlayer.new()
		p.bus = AudioSettings.MUSIC_BUS
		p.volume_db = SILENT_DB
		add_child(p)
		_players.append(p)


## Cambia de pista: baja la actual y, cuando ya calla, sube la nueva.
## Nunca suenan dos pistas a la vez (están en tonalidades distintas).
func play(track: String) -> void:
	if track == current_track:
		return
	current_track = track
	if DisplayServer.get_name() == "headless":
		return
	var stream := load_track(track)
	if stream == null:
		return
	if _tween != null:
		_tween.kill()
	var old := _players[_active]
	_active = 1 - _active
	var new := _players[_active]
	new.stop()
	new.stream = stream
	new.volume_db = SILENT_DB
	_tween = create_tween()
	if old.playing:
		_tween.tween_property(old, "volume_db", SILENT_DB, FADE_OUT_TIME)
	_tween.tween_callback(old.stop)
	_tween.tween_callback(new.play)
	_tween.tween_property(new, "volume_db", 0.0, FADE_IN_TIME)


func stop() -> void:
	current_track = ""
	for p in _players:
		p.stop()


func set_muffled(on: bool) -> void:
	AudioSettings.set_muffled(on)


static func load_track(track: String) -> AudioStream:
	var path := MUSIC_DIR + track + ".ogg"
	if not ResourceLoader.exists(path):
		push_warning("Music: pista no encontrada %s" % path)
		return null
	var stream := load(path) as AudioStreamOggVorbis
	if stream != null:
		stream.loop = true
	return stream
