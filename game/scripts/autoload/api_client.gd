extends Node
## Cliente HTTP hacia el backend Laravel. Fallo suave: el juego sigue offline.

const DEFAULT_BASE_URL := "http://127.0.0.1:8000/api"

@export var base_url: String = DEFAULT_BASE_URL

var _http: HTTPRequest


func _ready() -> void:
	_http = HTTPRequest.new()
	_http.name = "HttpRequest"
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)


func health_check() -> void:
	_request(HTTPClient.METHOD_GET, "/health")


func sync_progress(payload: Dictionary) -> void:
	_request(HTTPClient.METHOD_POST, "/progress/sync", payload)


func fetch_lessons() -> void:
	_request(HTTPClient.METHOD_GET, "/lessons")


func _request(method: int, path: String, body: Dictionary = {}) -> void:
	var url := base_url.rstrip("/") + path
	var headers := PackedStringArray(["Accept: application/json", "Content-Type: application/json"])
	var err: Error
	if body.is_empty():
		err = _http.request(url, headers, method)
	else:
		err = _http.request(url, headers, method, JSON.stringify(body))
	if err != OK:
		EventBus.api_error.emit("No se pudo iniciar petición: %s" % error_string(err))


func _on_request_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray
) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		EventBus.api_error.emit("Red no disponible (result=%d)" % result)
		return
	if response_code < 200 or response_code >= 300:
		EventBus.api_error.emit("API respondió %d" % response_code)
		return
	var text := body.get_string_from_utf8()
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	# Extensión futura: despachar por endpoint. Por ahora solo loguea éxito.
	print("[ApiClient] OK: ", parsed)
