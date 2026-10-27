class_name CombatSkill
extends RefCounted
## Acción de combate (assets/data/combat/skills.json): básico, técnica, curación, escudo o combo.

## Pulsaciones: una al impactar, una por golpe, o mantener y soltar en la zona.
const QTE_TAP := "tap"
const QTE_MULTI := "multi"
const QTE_HOLD := "hold"

var id: String = ""
var user: String = ""
## basic | attack | heal | guard | combo
var kind: String = "attack"
var display_name: String = ""
var description: String = ""
var fact: String = ""
var cost: int = 0
var combo_cost: int = 0
var power: float = 1.0
var hits: int = 1
var amount: int = 0
## enemy | all_enemies | ally | party
var target: String = "enemy"
var elements: PackedStringArray = PackedStringArray()
var requires: Dictionary = {}
var qte: String = QTE_TAP
## Animación del lanzador (attack | cast) y efecto en el blanco (hit | zap | light | heal).
var anim: String = "attack"
var fx: String = "hit"
## El lanzador corre hasta el blanco (golpes cuerpo a cuerpo) o actúa desde su sitio.
var melee: bool = true


static func from_dict(data: Dictionary) -> CombatSkill:
	var s := CombatSkill.new()
	s.id = str(data.get("id", ""))
	s.user = str(data.get("user", ""))
	s.kind = str(data.get("kind", "attack"))
	s.display_name = str(data.get("display_name", s.id))
	s.description = str(data.get("description", ""))
	s.fact = str(data.get("fact", ""))
	s.cost = int(data.get("cost", 0))
	s.combo_cost = int(data.get("combo_cost", 0))
	s.power = float(data.get("power", 1.0))
	s.hits = maxi(1, int(data.get("hits", 1)))
	s.amount = int(data.get("amount", 0))
	s.target = str(data.get("target", "enemy"))
	if data.has("elements"):
		s.elements = PackedStringArray(data["elements"])
	elif data.has("element"):
		s.elements = PackedStringArray([str(data["element"])])
	var req: Variant = data.get("requires", {})
	s.requires = req if typeof(req) == TYPE_DICTIONARY else {}
	s.qte = str(data.get("qte", QTE_TAP))
	s.anim = str(data.get("anim", "attack"))
	s.fx = str(data.get("fx", "hit"))
	s.melee = bool(data.get("melee", s.anim == "attack"))
	return s


func is_offensive() -> bool:
	return kind in ["basic", "attack", "combo"]


func targets_enemy() -> bool:
	return target == "enemy"


func targets_ally() -> bool:
	return target == "ally"


## Pulsaciones que pide la técnica (una por golpe en las «multi»).
func presses() -> int:
	return hits if qte == QTE_MULTI else 1
