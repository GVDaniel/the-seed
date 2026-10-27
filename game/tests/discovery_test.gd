extends SceneTree
## Verifica catálogo, IDs estables y cuaderno sin duplicados.
## godot --headless --path game --script res://tests/discovery_test.gd


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var failed := 0
	print("[discovery] start")

	var notebook: Node = root.get_node("ScienceNotebook")
	notebook.clear_session()
	var catalog: DestinationCatalog = notebook.get_catalog()
	if catalog.size() < 4:
		catalog.load_all()

	var required := ["earth", "moon", "mars", "station_aurora"]
	for id in required:
		if not catalog.has_id(id):
			printerr("[discovery] FAIL: falta id %s" % id)
			failed += 1
		else:
			var entry := catalog.get_entry(id)
			if entry.display_name.is_empty() or entry.scientific_facts.is_empty():
				printerr("[discovery] FAIL: ficha incompleta %s" % id)
				failed += 1
			elif entry.arcade_disclaimer.is_empty():
				printerr("[discovery] FAIL: sin disclaimer arcade %s" % id)
				failed += 1
			else:
				print("[discovery] OK ficha %s (%s)" % [id, entry.display_name])

	if not notebook.record_discovery("earth"):
		printerr("[discovery] FAIL: primer descubrimiento earth debía ser nuevo")
		failed += 1
	if notebook.record_discovery("earth"):
		printerr("[discovery] FAIL: segundo escaneo earth no debe duplicar")
		failed += 1
	if notebook.get_discovered_ids().size() != 1:
		printerr("[discovery] FAIL: tamaño cuaderno != 1")
		failed += 1
	else:
		print("[discovery] Cuaderno sin duplicados OK")

	notebook.record_discovery("moon")
	notebook.record_discovery("mars")
	if notebook.get_discovered_ids().size() != 3:
		printerr("[discovery] FAIL: se esperaban 3 entradas")
		failed += 1

	var packed := load("res://scenes/space/space_main.tscn") as PackedScene
	if packed == null:
		printerr("[discovery] FAIL: space_main")
		failed += 1
		_finish(failed)
		return

	var scene_root := packed.instantiate()
	root.add_child(scene_root)
	await process_frame
	await process_frame

	var earth := scene_root.get_node_or_null("World/Earth")
	var moon := scene_root.get_node_or_null("World/Moon")
	var mars := scene_root.get_node_or_null("World/Mars")
	var station := scene_root.get_node_or_null("World/StationAurora")
	var scanner := scene_root.get_node_or_null("ScannerSystem")
	var analysis := scene_root.get_node_or_null("AnalysisPanel")
	var notebook_ui := scene_root.get_node_or_null("HalInterface")

	if earth == null or str(earth.get("destination_id")) != "earth":
		printerr("[discovery] FAIL: Earth id")
		failed += 1
	if moon == null or str(moon.get("destination_id")) != "moon":
		printerr("[discovery] FAIL: Moon id")
		failed += 1
	if mars == null or str(mars.get("destination_id")) != "mars":
		printerr("[discovery] FAIL: Mars id")
		failed += 1
	if station == null or str(station.get("destination_id")) != "station_aurora":
		printerr("[discovery] FAIL: Station id")
		failed += 1
	if scanner == null or analysis == null or notebook_ui == null:
		printerr("[discovery] FAIL: sistemas UI/escáner ausentes")
		failed += 1
	else:
		print("[discovery] Nodos de escena OK")

	var analysis_panel := analysis as AnalysisPanel
	var notebook_panel := notebook_ui as HalInterface
	analysis_panel.open_for("earth", false)
	if not analysis_panel.visible:
		printerr("[discovery] FAIL: analysis no abrió")
		failed += 1
	analysis_panel.close()
	if analysis_panel.visible:
		printerr("[discovery] FAIL: analysis no cerró")
		failed += 1
	notebook_panel.open("notes")
	if not notebook_panel.is_open() or notebook_panel.current_tab() != "notes":
		printerr("[discovery] FAIL: notebook no abrió")
		failed += 1
	notebook_panel.close()
	if notebook_panel.is_open():
		printerr("[discovery] FAIL: notebook no cerró")
		failed += 1
	else:
		print("[discovery] Paneles open/close OK")

	scene_root.queue_free()
	await process_frame
	notebook.clear_session()
	_finish(failed)


func _finish(failed: int) -> void:
	if failed == 0:
		print("[discovery] PASS")
		quit(0)
	else:
		printerr("[discovery] FAIL (%d)" % failed)
		quit(1)
