# Créditos y licencias de assets

| Asset | Autor | Licencia | Ruta |
|-------|-------|----------|------|
| Tiny Town (tiles de la Tierra, recoloreados a «marchito») | Kenney (kenney.nl) | CC0 1.0 | `art/third_party/kenney_tiny_town/` → `art/tiles/earth_tiles.png` |
| Roguelike Modern City (coches, mobiliario urbano, cajas, barreras, árboles; recortes recoloreados a noche/óxido/polvo) | Kenney (kenney.nl/assets/roguelike-modern-city) | CC0 1.0 | `art/third_party/kenney_roguelike_modern_city/` → `art/props/city_*.png` |
| Roguelike Indoors (sillas, mesas, alfombras, estantes, plantas de interior) | Kenney (kenney.nl/assets/roguelike-indoors) | CC0 1.0 | `art/third_party/kenney_roguelike_indoors/` → `art/props/in_*.png` |
| Pixelify Sans (texto) | The Pixelify Sans Project Authors (github.com/eifetx/Pixelify-Sans) | SIL Open Font License 1.1 (`fonts/PixelifySans_OFL.txt`) | `fonts/PixelifySans.ttf` |
| Kenney Future (títulos) | Kenney (kenney.nl) | CC0 1.0 (`fonts/KenneyFonts_License.txt`) | `fonts/KenneyFuture.ttf` |
| Personajes, retratos, HAL (homenaje visual a HAL 9000, diseño propio), nave, planetas, props, iconos de objetos, edificios y letreros de neón, props urbanos, decoración de escenarios y calcas (`decal_*`), tiles de interiores, Luna y Marte, ilustraciones | Proyecto The Seed (generados con `tools/pixelart/generate.py`) | Propios del proyecto | `art/characters`, `art/portraits`, `art/ui`, `art/items`, `art/ship`, `art/planets`, `art/props`, `art/tiles/{moon,mars}_tiles.png`, `art/story` |
| Ciudades vivas: atlas urbanos (aceras, calzadas con línea guía, pasos de peatones, raíles maglev, plazas, hielo, sedimento), edificios en vista 3/4 (`bld_e_*`, `bld_m_*`, `bld_r_*` + `buildings.json`), mobiliario urbano futurista y peatones (`crowd_*`) | Proyecto The Seed (generados con `tools/pixelart/city_art.py`, que llama `generate.py`) | Propios del proyecto | `art/tiles/city_{earth,moon,mars}.{png,json}`, `art/props/`, `art/crowd/`, `data/ambient/crowd.json` |
| Arte de combate: fondos en capas (Barranco de Óxido, cráter del meteorito), hojas de animación de Andrés, HAL, AH-7 y dron AH-D, efectos (impacto, chispa, luz, curación, orbe solar) | Proyecto The Seed (generados con `tools/pixelart/battle_art.py`) | Propios del proyecto | `art/battle/` (+ manifiesto `data/combat/sheets.json`) |
| Vida ambiental: aerotaxis, aerofurgonetas, aerobús, tranvía maglev, drones, robots (barrendero, mensajero, de carga), rovers lunar y marciano, naves del cielo | Proyecto The Seed (generados con `tools/pixelart/ambient_art.py`) | Propios del proyecto | `art/ambient/` (+ manifiesto `data/ambient/kinds.json`) |
| Efectos de sonido | Proyecto The Seed (sintetizados con `tools/pixelart/sfx.py`) | Propios del proyecto | `audio/sfx/` |
| Música: «Órbita silenciosa» (espacio), «Paso a paso» (misión), «La Semilla» (menú y cinemáticas), «Neón de cantina» (bares y tiendas) | Proyecto The Seed (compuesta y sintetizada con `tools/audio/music.py`) | Propia del proyecto | `audio/music/` |

Regenerar arte propio: `python3 tools/pixelart/generate.py` (requiere Pillow; también recorta y recolorea los packs de Kenney con `tools/pixelart/third_party.py` y genera las ciudades con `tools/pixelart/city_art.py`).
Regenerar arte de combate: `python3 tools/pixelart/battle_art.py` (después de generate.py).
Regenerar vida ambiental: `python3 tools/pixelart/ambient_art.py` (autónomo).
Regenerar sonidos: `python3 tools/pixelart/sfx.py`.
Regenerar música: `python3 tools/audio/music.py` (requiere numpy, scipy y ffmpeg con libvorbis).

Nota: la fuente Pixelify Sans tiene una ligadura «fi» que Godot dibuja mal; el tema
(`resources/ui/the_seed_theme.tres`) la desactiva con una `FontVariation` (`liga`/`clig` = 0).
