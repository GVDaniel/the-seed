class_name App
extends Object
## Acceso a autoloads sin identificadores globales (compatible con --script headless).


static func bus() -> Node:
	return Engine.get_main_loop().root.get_node("EventBus")


static func notebook() -> Node:
	return Engine.get_main_loop().root.get_node("ScienceNotebook")


static func game_state() -> Node:
	return Engine.get_main_loop().root.get_node("GameState")


static func missions() -> Node:
	return Engine.get_main_loop().root.get_node("MissionLog")


static func story() -> Node:
	return Engine.get_main_loop().root.get_node("StoryDirector")


static func router() -> Node:
	return Engine.get_main_loop().root.get_node("Router")


static func sfx() -> Node:
	return Engine.get_main_loop().root.get_node("Sfx")


static func music() -> Node:
	return Engine.get_main_loop().root.get_node("Music")


static func inventory() -> Node:
	return Engine.get_main_loop().root.get_node("Inventory")


static func economy() -> Node:
	return Engine.get_main_loop().root.get_node("Economy")
