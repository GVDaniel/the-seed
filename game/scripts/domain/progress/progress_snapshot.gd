class_name ProgressSnapshot
extends RefCounted
## DTO inmutable del progreso del cadete (sin lógica de UI).

var player_name: String
var completed_lessons: PackedStringArray
var solved_puzzles: PackedStringArray
var stars_earned: int


func _init(
	p_name: String = "Cadete",
	p_lessons: PackedStringArray = PackedStringArray(),
	p_puzzles: PackedStringArray = PackedStringArray(),
	p_stars: int = 0
) -> void:
	player_name = p_name
	completed_lessons = p_lessons
	solved_puzzles = p_puzzles
	stars_earned = p_stars


static func from_dict(data: Dictionary) -> ProgressSnapshot:
	return ProgressSnapshot.new(
		str(data.get("player_name", "Cadete")),
		PackedStringArray(data.get("completed_lessons", [])),
		PackedStringArray(data.get("solved_puzzles", [])),
		int(data.get("stars_earned", 0))
	)


func to_dict() -> Dictionary:
	return {
		"player_name": player_name,
		"completed_lessons": Array(completed_lessons),
		"solved_puzzles": Array(solved_puzzles),
		"stars_earned": stars_earned,
	}
