# Lugares y puntos de interés

Datos: `game/assets/data/destinations/*.json` y mapas en `game/assets/data/maps/`.

**Aviso:** las posiciones en el mapa de ASTRA son **arcade**. No representan distancias ni escalas reales del sistema solar.

## Mundos principales

| Lugar | Rol en la historia |
|-------|-------------------|
| **Tierra** | Origen; Marchitez; Bóveda; despegue |
| **Estación Aurora** | Hub científico; Vega; puente a la Luna |
| **Luna** | Señal de sonda; Shackleton; combustible |
| **Marte (Jezero)** | Delta antiguo; invernadero; lección “no hay planeta B” |
| **TRAPPIST-1e** | Destino lejano (teaser / unlock tras cap. 3) |

---

## Tierra

| ID | Nombre | Notas |
|----|--------|-------|
| `seed_vault` | Bóveda Semillera | Inspirada en Svalbard; Lucía; frío ~−18 °C; ficción de ubicación en el juego |
| `earth_dead_plant` | Planta marchita | Enseña fotosíntesis; Marchitez = evento de ficción |
| `earth_air_sensor` | Sensor de aire | Lectura 2187 inventada (~900 ppm CO₂) para efecto invernadero |
| `earth` | Planeta Tierra | Mapa de superficie / tienda |

## Espacio / Aurora

| ID | Nombre | Notas |
|----|--------|-------|
| `station_aurora` | Estación Aurora | Estación orbital **ficticia**; cerca de la Tierra en el mapa jugable |
| `space_debris` | Basura espacial | Educativo; sin misión propia por ahora |
| `lunar_probe_signal` | Faro de sonda lunar | Objetivo de escaneo de `signal_from_moon` |
| `lunar_signal_analysis` | Análisis de telemetría | Entrada de cuaderno (recompensa) |

## Luna

| ID | Nombre | Notas |
|----|--------|-------|
| `moon` | Luna | Satélite; aterrizaje tras misión de la señal |
| `moon_ice_crater` | Cráter Shackleton (sombra) | Hielo polar real como idea; base/Kai ficción |
| `lunar_water_fuel` | Del hielo al combustible | Electrólisis / ISRU (simplificado) |

## Marte

| ID | Nombre | Notas |
|----|--------|-------|
| `mars` | Marte | Planeta rojo; aterrizaje tras hielo lunar |
| `mars_delta` | Delta de Jezero | Agua antigua ~3 500 Ma (ciencia real simplificada) |
| `mars_rover` | Rover explorador | Inspirado en Perseverance; unidad del juego ficticia |
| `mars_greenhouse` | Invernadero | Usado en misión `plant_seed` — **falta ficha destination dedicada en datos** (hueco a documentar/crear) |
| `mars_garage` | Taller de Bruno | Interior (puerta en la colonia). Banco de trabajo (instalar el motor) y destilador de metano |
| — | Barranco de Óxido | Al este de la base, tras una pared de rocas con dos pasos. Carguero de MarsCorp, AH-7, perforadora, meteorito, Ada |
| `mars_buried_ice` | Hielo bajo el polvo | Hielo de agua enterrado (Phoenix, 2008; real) |
| `mars_iron_meteorite` | Meteorito de hierro | Hierro-níquel, como *Heat Shield Rock* (Opportunity, 2005; real) |
| `sabatier_methane` | Metano marciano | Reacción de Sabatier (CO₂ + 4 H₂ → CH₄ + 2 H₂O; real; Nobel 1912). Se desbloquea con `methane_heart` |

## Más allá

| ID | Nombre | Notas |
|----|--------|-------|
| `trappist1e` | TRAPPIST-1e | ~40 al; zona habitable; unlock post `red_garden`; sin gameplay profundo aún |

---

## Tiendas / interiores (ambientación)

Mapas y shops (economía suave; el combate solo ocurre en el Barranco de Óxido):

- Tierra: tienda / barrio Semilla  
- Luna: bar (batidos), repuestos  
- Marte: cantina, mercado, Taller de Bruno  
- **Surtidores de ASTRA** junto a cada nave: AgroNet (Tierra, de pago), Shackleton (Luna, gratis tras ayudar a Kai), MarsCorp (Marte, gratis tras destilar metano)  

Ver `game/assets/data/shops/` y `game/assets/data/maps/`.

## Plantilla para nuevos lugares

```md
### Nombre (`id`)
- Planeta / zona:
- ¿Real, ficción o mezcla?
- Misión / POI:
- Hecho científico que enseña:
- Disclaimer arcade:
```
