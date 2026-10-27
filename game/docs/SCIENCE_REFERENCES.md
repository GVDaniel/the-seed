# Referencias científicas — destinos ASTRA

Los datos de `assets/data/destinations/*.json` combinan **hechos reales** (marcados `is_game_simplification: false`) y **simplificaciones educativas** (`true`, con nota).

## Aviso importante sobre el mapa arcade

Las posiciones, tamaños en pantalla y tiempos de viaje de ASTRA **no representan** distancias, escalas ni dinámicas reales del sistema solar. Son layout de jugabilidad. Cada ficha incluye `arcade_disclaimer`.

## Fuentes (ids usados en JSON)

| ID | Fuente | Uso |
|----|--------|-----|
| `nasa_earth_facts` | NASA Solar System Exploration — Earth Facts | Diámetro, 1 ua, rotación, atmósfera |
| `nasa_moon_facts` | NASA Solar System Exploration — Moon Facts | Diámetro, distancia Tierra–Luna, gravedad, exosfera |
| `nasa_mars_facts` | NASA Solar System Exploration — Mars Facts | Diámetro, distancia al Sol, sol marciano, atmósfera |
| `nasa_iss_facts` | NASA — International Space Station (overview / science) | Altitud típica ~400 km, microgravedad, líneas de investigación (contexto para la estación **ficticia** Aurora) |
| `nasa_climate` | NASA Science — Climate Change | Efecto invernadero, fotosíntesis (contexto) |
| `noaa_co2` | NOAA Global Monitoring Laboratory — Trends in CO₂ | CO₂ atmosférico > 420 ppm (2024) |
| `noaa_ocean_oxygen` | NOAA Ocean Service — How much oxygen comes from the ocean? | ~50 % del O₂ lo produce el fitoplancton |
| `croptrust_svalbard` | Crop Trust — Svalbard Global Seed Vault | Apertura 2008, −18 °C, capacidad 4,5 millones de muestras |
| `nasa_shackleton` | NASA Science — Moon (polo sur, cráter Shackleton) | Diámetro ~21 km, sombra permanente |
| `nasa_lro_diviner` | NASA — Lunar Reconnaissance Orbiter (Diviner) | Temperaturas < −200 °C en sombras polares |
| `nasa_moon_ice_2018` | NASA Science — Moon (hielo en los polos, datos M3/Chandrayaan-1, 2018) | Hielo de agua confirmado |
| `nasa_isru` | NASA — In-Situ Resource Utilization | Electrólisis, combustible H₂/O₂, uso de recursos locales |
| `nasa_perseverance` | NASA Science — Mars 2020 Perseverance | Jezero ~45 km, lago hace ~3 500 Ma, aterrizaje 18/02/2021, ~1 025 kg, MMRTG |
| `esa_space_debris` | ESA — Space Debris / Space debris by the numbers | ~36 500 objetos > 10 cm, ~28 000 km/h en LEO |
| `nasa_trappist1` | NASA Science — Exoplanet Catalog: TRAPPIST-1 e | ~40 años luz, órbita de 6,1 días, anunciado en 2017, ~0,92 radios terrestres |
| `nasa_phoenix` | NASA — Phoenix Mars Lander (2008) | Hielo de agua excavado a pocos centímetros, cerca del polo norte |
| `nasa_opportunity_meteorite` | NASA/JPL — Opportunity: «Heat Shield Rock» (2005) | Primer meteorito (hierro y níquel) identificado en otro planeta |
| `nasa_moxie` | NASA — Mars 2020 MOXIE | Oxígeno producido a partir del CO₂ marciano (2021–2023) |
| `nobel_sabatier` | NobelPrize.org — Paul Sabatier, Química 1912 | Hidrogenación con metales finamente divididos (níquel); reacción CO₂ + 4 H₂ → CH₄ + 2 H₂O |

URLs de consulta (revisar periódicamente; NASA puede reorganizar rutas):

- Earth: https://science.nasa.gov/earth/facts/
- Moon: https://science.nasa.gov/moon/facts/
- Mars: https://science.nasa.gov/mars/facts/
- ISS: https://www.nasa.gov/international-space-station/
- Clima: https://science.nasa.gov/climate-change/
- CO₂ (NOAA): https://gml.noaa.gov/ccgg/trends/
- Oxígeno del océano (NOAA): https://oceanservice.noaa.gov/facts/ocean-oxygen.html
- Bóveda de Svalbard: https://www.croptrust.org/work/svalbard-global-seed-vault/
- Luna / hielo polar: https://science.nasa.gov/moon/
- LRO: https://science.nasa.gov/mission/lro/
- ISRU: https://www.nasa.gov/overview-in-situ-resource-utilization/
- Perseverance: https://science.nasa.gov/mission/mars-2020-perseverance/
- Basura espacial (ESA): https://www.esa.int/Space_Safety/Space_Debris
- TRAPPIST-1 e: https://science.nasa.gov/exoplanet-catalog/trappist-1-e/
- Phoenix: https://science.nasa.gov/mission/phoenix/
- Opportunity (Heat Shield Rock): https://science.nasa.gov/mission/mer-opportunity/
- MOXIE: https://science.nasa.gov/mission/mars-2020-perseverance/
- Sabatier (Nobel 1912): https://www.nobelprize.org/prizes/chemistry/1912/sabatier/facts/

## Qué es ficción del juego

- **Estación Aurora**: inventada. Solo se inspiran hechos genéricos de estaciones reales.
- **Faro / sonda lunar de la misión**: inventados para el gameplay; la idea de telemetría y radio en vacío lunar se basa en hechos reales simplificados.
- **Layout espacial** Tierra / Luna / Marte / Aurora: posiciones artísticas.
- Porcentajes atmosféricos y fracciones (p. ej. gravedad lunar ~1/6): redondeos didácticos cuando `is_game_simplification` es `true`.
- **La Marchitez**, el año 2187 y la lectura de CO₂ de ~900 ppm: historia inventada.
- **Bóveda Semillera, base Shackleton, base Jezero** y sus personajes: ficción inspirada en lugares y misiones reales.
- **Rover explorador**: homenaje a Perseverance, no una réplica.
- **Colores y vegetación de TRAPPIST-1e**: imaginados; su superficie no se ha observado.
- **Anillo de basura espacial**: agrupado para el juego; la basura real está dispersa en muchas órbitas.
- **Antihumanistas, robots AH-7 y drones AH-D, Barranco de Óxido, carguero de MarsCorp**: ficción del capítulo 4.
- **Combustible de ASTRA** (unidades, consumo, tanques): números de juego, no físicos. El metano y la reacción de Sabatier sí son reales.
- **Hielo junto a Jezero**: Jezero está cerca del ecuador; el hielo superficial abunda a latitudes más altas.
