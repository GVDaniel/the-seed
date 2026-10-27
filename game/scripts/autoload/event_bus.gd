extends Node
## Bus de señales desacoplado. Dominios emiten; UI y sistemas escuchan.

signal lesson_started(lesson_id: String)
signal lesson_completed(lesson_id: String, score: int)
signal puzzle_solved(puzzle_id: String)
signal progress_changed(progress: Dictionary)
signal api_error(message: String)
signal experience_changed(total_xp: int)
signal credits_changed(total: int)

# Tiendas
## Abre la tienda shop_id (la escena decide cómo mostrarla).
signal shop_requested(shop_id: String)
signal shop_closed
signal item_bought(item_id: String, shop_id: String)

# Descubrimientos / escáner
signal destination_scanned(destination_id: String)
signal destination_discovered(destination_id: String)
signal discovery_added(destination_id: String)
signal discovery_already_known(destination_id: String)
signal scan_focus_changed(destination_id: String, display_name: String)
signal scan_completed(destination_id: String, was_new: bool)
signal scan_failed(reason: String)
signal analysis_panel_closed

# HAL (interfaz: inventario, mapa, notas…)
## tab_id vacío = última pestaña; "close" = cerrar.
signal hal_interface_requested(tab_id: String)
signal hal_interface_toggled(open: bool)

# Misiones
signal mission_started(mission_id: String)
signal mission_completed(mission_id: String)
signal mission_updated(mission_id: String)
signal mission_objective_completed(mission_id: String, objective_id: String)
signal mission_status_message(text: String)
signal dialogue_requested(speaker: String, lines: Array, context: String)
signal dialogue_finished(context: String)

# Historia / mundo
signal interaction_requested(target_id: String, kind: String)
signal interaction_prompt_changed(text: String)
signal item_collected(item_id: String)
signal challenge_solved(challenge_id: String)
signal landed_on(destination_id: String)
signal took_off(from_location: String)
signal world_interacted(target_id: String)
signal story_event(event_id: String)
signal chapter_changed(chapter: int)
signal nav_target_changed(target_id: String)
