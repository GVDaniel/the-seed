class_name MissionState
extends RefCounted
## Estado runtime de una misión.

enum Status { AVAILABLE, ACTIVE, COMPLETED }

var mission_id: String = ""
var status: Status = Status.AVAILABLE
var completed_objective_ids: PackedStringArray = PackedStringArray()


func status_name() -> String:
	match status:
		Status.AVAILABLE:
			return "available"
		Status.ACTIVE:
			return "active"
		Status.COMPLETED:
			return "completed"
	return "available"


static func status_from_name(name: String) -> Status:
	match name:
		"active":
			return Status.ACTIVE
		"completed":
			return Status.COMPLETED
		_:
			return Status.AVAILABLE


func is_objective_done(objective_id: String) -> bool:
	return completed_objective_ids.has(objective_id)


func to_dict() -> Dictionary:
	return {
		"mission_id": mission_id,
		"status": status_name(),
		"completed_objective_ids": Array(completed_objective_ids),
	}


static func from_dict(data: Dictionary) -> MissionState:
	var state := MissionState.new()
	state.mission_id = str(data.get("mission_id", ""))
	state.status = status_from_name(str(data.get("status", "available")))
	var ids: Array = data.get("completed_objective_ids", [])
	state.completed_objective_ids = PackedStringArray(ids)
	return state
