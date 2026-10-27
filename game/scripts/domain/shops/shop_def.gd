class_name ShopDef
extends RefCounted
## Tienda o bar: quién atiende y qué vende (datos, sin nodos).

var id: String = ""
var display_name: String = ""
var keeper: String = ""
var greeting: String = ""
## [{item: String, price: int}]
var stock: Array[Dictionary] = []


static func from_dict(data: Dictionary) -> ShopDef:
	var def := ShopDef.new()
	def.id = str(data.get("id", ""))
	def.display_name = str(data.get("display_name", def.id))
	def.keeper = str(data.get("keeper", ""))
	def.greeting = str(data.get("greeting", ""))
	for row in data.get("stock", []):
		if typeof(row) == TYPE_DICTIONARY and row.has("item"):
			def.stock.append({"item": str(row["item"]), "price": int(row.get("price", 0))})
	return def


func price_of(item_id: String) -> int:
	for row in stock:
		if row["item"] == item_id:
			return int(row["price"])
	return -1
