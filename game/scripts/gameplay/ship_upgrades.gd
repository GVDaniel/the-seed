class_name ShipUpgrades
extends Object
## Mejoras de ASTRA compradas en tiendas: multiplicadores en items/*.json → "effects".
## Claves: max_energy, max_speed, acceleration, energy_regen, debris_damage.


static func multiplier(key: String) -> float:
	var m := 1.0
	for def in App.inventory().owned():
		m *= float((def as ItemDef).effects.get(key, 1.0))
	return m


## Copia de las estadísticas con las mejoras aplicadas (el .tres no se toca).
static func apply(base: ShipStats) -> ShipStats:
	var stats := base.duplicate() as ShipStats
	for key in ["max_energy", "max_speed", "acceleration", "energy_regen"]:
		stats.set(key, float(stats.get(key)) * multiplier(key))
	return stats
