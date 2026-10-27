class_name MissionDef
extends RefCounted
## Definición de misión cargada desde JSON.

var id: String = ""
var title: String = ""
var summary: String = ""
var start_conditions: Dictionary = {}
var objectives: Array[MissionObjectiveDef] = []
var rewards: Dictionary = {}
var dialogues: Dictionary = {}
var objective_complete_messages: Dictionary = {}
var mission_complete_message: String = ""
var chapter: int = 1
var order: int = 0
var requires: PackedStringArray = PackedStringArray()
## NPC que ofrece la misión. Vacío + auto_start: arranca sola al cumplir requisitos.
var start_npc: String = ""
var auto_start: bool = false
## Evento narrativo al completar (p. ej. cinemática final).
var on_complete_event: String = ""


static func from_dict(data: Dictionary) -> MissionDef:
	var def := MissionDef.new()
	def.id = str(data.get("id", ""))
	def.title = str(data.get("title", def.id))
	def.summary = str(data.get("summary", ""))
	var start: Variant = data.get("start_conditions", {})
	if typeof(start) == TYPE_DICTIONARY:
		def.start_conditions = start
	var rewards_raw: Variant = data.get("rewards", {})
	if typeof(rewards_raw) == TYPE_DICTIONARY:
		def.rewards = rewards_raw
	var dialogues_raw: Variant = data.get("dialogues", {})
	if typeof(dialogues_raw) == TYPE_DICTIONARY:
		def.dialogues = dialogues_raw
	var msgs: Variant = data.get("objective_complete_messages", {})
	if typeof(msgs) == TYPE_DICTIONARY:
		def.objective_complete_messages = msgs
	def.mission_complete_message = str(data.get("mission_complete_message", ""))
	def.chapter = int(data.get("chapter", 1))
	def.order = int(data.get("order", 0))
	def.requires = PackedStringArray(data.get("requires", []))
	def.start_npc = str(data.get("start_npc", ""))
	def.auto_start = bool(data.get("auto_start", false))
	def.on_complete_event = str(data.get("on_complete_event", ""))
	var objs: Array = data.get("objectives", [])
	for item in objs:
		if typeof(item) == TYPE_DICTIONARY:
			def.objectives.append(MissionObjectiveDef.from_dict(item))
	return def


func get_objective(objective_id: String) -> MissionObjectiveDef:
	for obj in objectives:
		if obj.id == objective_id:
			return obj
	return null


func dialogue_lines(key: String) -> Array:
	var block: Variant = dialogues.get(key, [])
	return block if typeof(block) == TYPE_ARRAY else []
