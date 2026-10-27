extends Node
## Efectos de sonido por nombre (assets/audio/sfx/<nombre>.wav). Pool pequeño.

const SFX_DIR := "res://assets/audio/sfx/"
const POOL_SIZE := 6

var enabled: bool = true
var _streams: Dictionary = {}
var _players: Array[AudioStreamPlayer] = []
var _next: int = 0


func _ready() -> void:
	AudioSettings.ensure_buses()
	for i in POOL_SIZE:
		var p := AudioStreamPlayer.new()
		p.bus = AudioSettings.SFX_BUS
		p.volume_db = -6.0
		add_child(p)
		_players.append(p)


func play(sfx_name: String, pitch: float = 1.0) -> void:
	if not enabled or DisplayServer.get_name() == "headless":
		return
	var stream := _get_stream(sfx_name)
	if stream == null:
		return
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = stream
	p.pitch_scale = pitch
	p.play()


func _get_stream(sfx_name: String) -> AudioStream:
	if _streams.has(sfx_name):
		return _streams[sfx_name]
	var path := SFX_DIR + sfx_name + ".wav"
	var stream: AudioStream = load(path) if ResourceLoader.exists(path) else null
	_streams[sfx_name] = stream
	return stream
