extends SceneTree
## Smoke test headless: carga autoloads y valida progreso local.
## Uso: godot --headless --path game --script res://tests/smoke_test.gd
## Nota: no usar identificadores de Autoload en compile-time; se resuelven en runtime vía /root.


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var failed := 0
	print("[smoke] The Seed — inicio")

	var game_state: Node = root.get_node_or_null("GameState")
	if game_state == null:
		printerr("[smoke] FAIL: GameState autoload ausente")
		failed += 1
		_finish(failed)
		return

	var before: int = int(game_state.get("stars_earned"))
	game_state.call("mark_lesson_completed", "smoke_lesson", 1)
	var lessons: PackedStringArray = game_state.get("completed_lessons")
	if not lessons.has("smoke_lesson"):
		printerr("[smoke] FAIL: lección no registrada")
		failed += 1
	var after: int = int(game_state.get("stars_earned"))
	if after < before + 1:
		printerr("[smoke] FAIL: estrellas no incrementaron")
		failed += 1
	else:
		print("[smoke] GameState OK (stars=%d)" % after)

	var snapshot := ProgressSnapshot.from_dict(game_state.call("as_dict"))
	if snapshot.player_name.is_empty():
		printerr("[smoke] FAIL: ProgressSnapshot vacío")
		failed += 1
	else:
		print("[smoke] ProgressSnapshot OK")

	var lesson_path := "res://assets/data/astronomy/demo_sol_overview.json"
	if not FileAccess.file_exists(lesson_path):
		printerr("[smoke] FAIL: falta %s" % lesson_path)
		failed += 1
	else:
		var raw := FileAccess.get_file_as_string(lesson_path)
		var data: Variant = JSON.parse_string(raw)
		if typeof(data) != TYPE_DICTIONARY or not (data as Dictionary).has("id"):
			printerr("[smoke] FAIL: JSON de lección inválido")
			failed += 1
		else:
			print("[smoke] Contenido astronomía OK (%s)" % data["id"])

	_finish(failed)


func _finish(failed: int) -> void:
	if failed == 0:
		print("[smoke] PASS")
		quit(0)
	else:
		printerr("[smoke] FAIL (%d)" % failed)
		quit(1)
