extends Node
## Estado de sesión del jugador. Persistencia local mínima; sync vía ApiClient.

const SAVE_PATH := "user://the_seed_progress.cfg"

var player_name: String = "Andrés"
var completed_lessons: PackedStringArray = PackedStringArray()
var solved_puzzles: PackedStringArray = PackedStringArray()
var stars_earned: int = 0
var experience: int = 0
## "space" o id de superficie ("earth", "moon", "mars").
var location: String = "earth"
## Planeta o zona a la que pertenece la ubicación (un interior «moon_bar» → «moon»).
var region: String = "earth"
## Créditos para tiendas y bares.
var credits: int = STARTING_CREDITS
var items: PackedStringArray = PackedStringArray()
var world_flags: PackedStringArray = PackedStringArray()
var intro_seen: bool = false

const STARTING_CREDITS := 30

const RANKS := [
	[0, "Cadete aprendiz"],
	[100, "Cadete explorador"],
	[250, "Navegante"],
	[450, "Pionero estelar"],
]


func _ready() -> void:
	load_local()


func add_experience(amount: int) -> void:
	if amount <= 0:
		return
	experience += amount
	save_local()
	App.bus().experience_changed.emit(experience)
	App.bus().progress_changed.emit(as_dict())


func rank_name() -> String:
	var title := str(RANKS[0][1])
	for row in RANKS:
		if experience >= int(row[0]):
			title = str(row[1])
	return title


func has_item(item_id: String) -> bool:
	return items.has(item_id)


func add_item(item_id: String) -> bool:
	if item_id.is_empty() or items.has(item_id):
		return false
	items.append(item_id)
	save_local()
	return true


func has_flag(flag: String) -> bool:
	return world_flags.has(flag)


func set_flag(flag: String) -> void:
	if flag.is_empty() or world_flags.has(flag):
		return
	world_flags.append(flag)
	save_local()


func set_location(location_id: String, region_id: String = "") -> void:
	location = location_id
	region = region_id if not region_id.is_empty() else (location_id if location_id != "space" else region)
	save_local()


func add_credits(amount: int) -> void:
	if amount == 0:
		return
	credits = maxi(0, credits + amount)
	save_local()
	App.bus().credits_changed.emit(credits)


## Paga si alcanza; devuelve false si no hay créditos suficientes.
func spend_credits(amount: int) -> bool:
	if amount < 0 or credits < amount:
		return false
	add_credits(-amount)
	return true


func has_save() -> bool:
	return FileAccess.file_exists(SAVE_PATH) and intro_seen


## Nueva partida: limpia progreso local (cuaderno y misiones los limpia StoryDirector).
func reset_progress() -> void:
	completed_lessons = PackedStringArray()
	solved_puzzles = PackedStringArray()
	stars_earned = 0
	experience = 0
	location = "earth"
	region = "earth"
	credits = STARTING_CREDITS
	items = PackedStringArray()
	world_flags = PackedStringArray()
	intro_seen = false
	save_local()
	App.bus().experience_changed.emit(experience)
	App.bus().credits_changed.emit(credits)


func mark_lesson_completed(lesson_id: String, score: int = 1) -> void:
	if lesson_id.is_empty():
		return
	if not completed_lessons.has(lesson_id):
		completed_lessons.append(lesson_id)
	stars_earned += maxi(score, 0)
	save_local()
	App.bus().lesson_completed.emit(lesson_id, score)
	App.bus().progress_changed.emit(as_dict())


func mark_puzzle_solved(puzzle_id: String) -> void:
	if puzzle_id.is_empty():
		return
	if not solved_puzzles.has(puzzle_id):
		solved_puzzles.append(puzzle_id)
		stars_earned += 1
	save_local()
	App.bus().puzzle_solved.emit(puzzle_id)
	App.bus().progress_changed.emit(as_dict())


func as_dict() -> Dictionary:
	return {
		"player_name": player_name,
		"completed_lessons": Array(completed_lessons),
		"solved_puzzles": Array(solved_puzzles),
		"stars_earned": stars_earned,
		"experience": experience,
		"location": location,
		"credits": credits,
		"items": Array(items),
	}


func save_local() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("progress", "player_name", player_name)
	cfg.set_value("progress", "completed_lessons", Array(completed_lessons))
	cfg.set_value("progress", "solved_puzzles", Array(solved_puzzles))
	cfg.set_value("progress", "stars_earned", stars_earned)
	cfg.set_value("progress", "experience", experience)
	cfg.set_value("progress", "location", location)
	cfg.set_value("progress", "region", region)
	cfg.set_value("progress", "credits", credits)
	cfg.set_value("progress", "items", Array(items))
	cfg.set_value("progress", "world_flags", Array(world_flags))
	cfg.set_value("progress", "intro_seen", intro_seen)
	var err := cfg.save(SAVE_PATH)
	if err != OK:
		push_warning("GameState: no se pudo guardar (%s)" % error_string(err))


func load_local() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	player_name = str(cfg.get_value("progress", "player_name", player_name))
	var lessons: Array = cfg.get_value("progress", "completed_lessons", [])
	var puzzles: Array = cfg.get_value("progress", "solved_puzzles", [])
	completed_lessons = PackedStringArray(lessons)
	solved_puzzles = PackedStringArray(puzzles)
	stars_earned = int(cfg.get_value("progress", "stars_earned", 0))
	experience = int(cfg.get_value("progress", "experience", 0))
	location = str(cfg.get_value("progress", "location", "earth"))
	region = str(cfg.get_value("progress", "region", location))
	credits = int(cfg.get_value("progress", "credits", STARTING_CREDITS))
	items = PackedStringArray(cfg.get_value("progress", "items", []))
	world_flags = PackedStringArray(cfg.get_value("progress", "world_flags", []))
	intro_seen = bool(cfg.get_value("progress", "intro_seen", false))
