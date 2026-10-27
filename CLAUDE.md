# The Seed — convenciones para agentes y desarrolladores

Demo educativa (Godot 4.x + Laravel) para ~12 años: RPG espacial pixel-art con UI futurista. Enseña astronomía, tecnología y bases de programación. Historia: Andrés lleva **La Semilla** desde la Tierra marchita (2187) hacia TRAPPIST-1e. Diseño: `game/docs/GDD.md`. Documentación narrativa (premisa, misiones, personajes, roadmap): `historia/`.

## Stack

| Capa | Tecnología | Ruta |
|------|------------|------|
| Cliente | Godot **4.7.x**, GDScript tipado | `game/` |
| Backend | Laravel 13 (API JSON) | `backend/` |
| Target | Android (viewport 1280×720, stretch canvas_items) | export futuro |

Godot instalado en este entorno: `godot` → `~/.local/bin/godot` (4.7.2.stable).

## Arquitectura mínima

```
game/
  assets/data/     # Contenido (JSON): lecciones y puzzles — fuente de verdad local
  scenes/          # Escenas por área (boot, ui, ship, world, lessons)
  scripts/
    autoload/      # EventBus, GameState, ApiClient, StoryDirector, Router, Music, Sfx, Inventory, Economy, ShipState, Hero
    domain/        # Lógica pura / DTOs (astronomy, coding, progress, combat, hero, ship)
    battle/        # Escena de combate (vistas, menú, anillo de tiempo, HUD)
    ui/            # Controladores de escena (una responsabilidad)
    net/           # Extensiones HTTP futuras
    boot/          # Arranque
  tests/           # Scripts headless (--script)

backend/
  routes/api.php   # /health, /lessons, /progress/sync
  app/Http/...     # Controllers delgados
```

**Flujo jugable:** Boot → Menú → cinemática intro → superficie Tierra → laboratorio → espacio → Luna → Marte → (cap. 4) combate, taller y destilado → cinemática final. Navegación siempre vía autoload `Router` (fundidos, retorno del laboratorio y del combate, despegue).

**Historia (autoload `StoryDirector`):** traduce eventos del `EventBus` (`scan_completed`, `item_collected`, `challenge_solved`, `landed_on`, `took_off`, `world_interacted`, `battle_finished`, diálogos) en objetivos de misión; decide qué dice cada NPC (objetivo `talk_to` → `offer` → `reminder` → `after` → líneas idle). Reglas de acceso (`can_land`, `can_take_off`, `can_collect`, `can_interact`, `can_battle`) viven aquí, no en escenas. Aplica los `effects` de los objetivos (`install_engine`, `refuel`, `repair`, `set_flag`, `consume_items`) y da la recompensa de cada combate una sola vez. Capítulos: `assets/data/story/chapters.json`; personajes: `assets/data/characters/`; cinemáticas: `assets/data/story/cutscenes.json`.

**Ciudades, vecinos y tiendas:** los exteriores tienen urbanismo real, generado por `tools/maps/{earth,moon,mars}_city.py` sobre `tools/maps/city.py` (`City`: calles con `street_h`/`street_v` — calzada, aceras con bordillo calculado, línea guía, raíl maglev, cruces con paso de peatones —, filas de edificios con `row()` y tamaños del manifiesto `assets/art/props/buildings.json`, mobiliario a intervalos con `along_h/v`, `check_paths` que aborta si algo de la historia queda inalcanzable). Los edificios son sólidos en toda su silueta (tejado + fachada = `d + wall/16` filas) para que nada quede escondido tras un tejado; todos miran al sur. Nada de coches: aerovehículos, tranvía maglev, drones y robots (rovers solo en Luna/Marte). `tools/maps/build_maps.py` escribe los JSON (no editarlos a mano) y contiene los interiores. Entidades: `door` (con `target`/`spawn` lleva a otro mapa; sin ellos, lee `lines`; la flecha la encuentra por el id del mapa destino), `light` y la clave `light` en cualquier entidad (`NeonLight`), `npc` con `wander` (pasea) o `shop` (abre `ShopPanel`), `z` para piezas planas (calcas `decal_*` con `z: -1`), `enemy` (`encounter`, `done_flag`, `sprite_done`, `intro_lines`, `locked_text`, `done_lines`) y `service` (surtidor: `rate` créditos/unidad, `free_flag` para servicio gratis). Interiores con `region` (p. ej. `moon_bar` → `moon`, en `GameState.region`). Personajes con `group` = `crew | local`. Autoload `Economy`: créditos (`GameState.credits`), recompensas y compras; tiendas en `assets/data/shops/`; mejoras de ASTRA vía `effects` en el objeto (`ShipUpgrades`).

**Vida ambiental (`scripts/world/ambient/`, `AmbientLife`):** clave `"ambient_life"` del mapa (`"ambient"` es el color de luz). `movers` (flujo con `interval` o persistentes con `count` + `loop` `pingpong|cycle`, `altitude` con sombra, filas right/down/up), `sky` (naves cruzando a gran altura) y `crowd` (peatones animados, no sólidos, con `barks` en bocadillo al acercarse; nunca roban la E). Tipos y hojas: `assets/data/ambient/kinds.json` (`tools/pixelart/ambient_art.py`) y `assets/data/ambient/crowd.json` (peatones por planeta en `assets/art/crowd/`). Tope de 40 entidades vivas por mapa.

**Superficies:** una escena genérica `scenes/surface/surface_level.tscn` carga `assets/data/maps/<id>.json` (leyenda ASCII → `TileMapLayer` con `z_index` −10, entidades `npc/scan/item/terminal/ship/object/sign/prop/spawn`). Exteriores con atlas `city_earth|city_moon|city_mars` (mismos nombres de tile en los tres, manifiesto `assets/art/tiles/city_<planeta>.json`; `TileCatalog.info()` lee cualquier atlas con manifiesto). Interiores con `interior_tiles.png`. Previsualizar: `python3 tools/maps/preview_map.py <id> out.png [escala]`. Jugador: `scenes/player/andres.tscn` (`WalkerController` + `CharacterSprite`).

**HAL (compañera, homenaje a HAL 9000):** panel plateado con lente roja que sigue a Andrés (`HalFollower`). `Tab`/`I` o el botón del HUD abren `scenes/ui/hal/hal_interface.tscn` (pide abrir vía `EventBus.hal_interface_requested`, avisa con `hal_interface_toggled`). Pestañas (teclas 1–7), un script cada una en `scripts/ui/hal/`: inventario (botón «Usar» en consumibles), Andrés (`HalStatusTab`: nivel, salud, puntos de mejora, técnicas y estado de ASTRA), mapa (`HalMinimap` dibuja el JSON del mapa; `HalSystemMap` la ruta), misiones (principal y secundarias), cuaderno, tripulación (`StoryDirector.has_met`), sistema (volumen). Las escenas anfitrionas bloquean movimiento/escáner mientras está abierta.

**Inventario (autoload `Inventory`):** objetos en `assets/data/items/*.json` (`starter`, `granted_by` = `solve_challenge | scan_destination | interact | win_battle`, `fact` real, `use` = `{heal}` o `{repair}` para consumibles). `Inventory.use(id)` cura a Andrés o repara ASTRA y gasta el objeto. Guarda en `GameState.items`.

**ASTRA (autoload `ShipState`):** motor (`assets/data/ship/engines.json`), combustible y casco persistentes (`user://the_seed_ship.cfg`). Se empieza con el motor químico CX-50 (lento, 40/60 de hidracina). Empujar gasta combustible (`ShipController.fuel_source`); con el tanque vacío quedan propulsores de reserva (30 % de aceleración, 50 % de velocidad: nunca hay bloqueo). La basura espacial abolla el casco y un casco dañado frena la nave. Surtidores en cada superficie (pago parcial, cuarto de tanque gratis si no hay créditos). Mejoras de tienda: `fuel_use`, `fuel_capacity` además de las de energía.

**Andrés (autoload `Hero`):** nivel calculado de `GameState.experience` (`HeroProgression`: XP para nivel n = 10·(n−1)·(n+2)). Cada nivel da 1 punto para **aptitudes** (salud, defensa), **conocimientos** (energía de técnicas, ahorro de combustible) o **destrezas** (ataque, margen de pulsación). Salud persistente (`user://the_seed_hero.cfg`); se recupera con comida, botiquines o al subir de nivel. Las técnicas se desbloquean con puntos (`requires` en `assets/data/combat/skills.json`).

**Combate (`scenes/battle/battle.tscn`, dominio en `scripts/domain/combat/`):** por turnos estilo *Sea of Stars*, solo en tierra y solo cuando una misión lo pide (`win_battle`). Grupo: Andrés + HAL; cada uno actúa una vez por ronda en el orden que elija el jugador. **Ronda:** `begin_round()` anuncia sobre cada enemigo qué hará al final de la ronda (ataque y blanco, coraza o carga con **cerraduras** y cuenta atrás) → fase del grupo → `resolve_enemy(uid, bloqueo)` → `end_round()`. Pulsaciones (`TimingRing`, Espacio/E/toque) según `qte` de la técnica: `tap` (anillo), `multi` (una por golpe), `hold` (mantener y soltar en la zona dorada), `none`; también para bloquear. Debilidades de elemento (`impacto`, `electricidad`, `luz`) ocultas («?») hasta acertarlas o hasta que HAL **analiza** (gratis, una vez por enemigo, cuenta el dato `scan`). Recursos: **EN** por personaje (el básico recupera 1), **chispas solares** compartidas (las sueltan los básicos; ← → o −/+ gastan hasta 3 para potenciar: +35 % por chispa y cada golpe rompe una cerradura más) y **combo** compartido (técnicas en equipo `combo_*`). Romper todas las cerraduras cancela el ataque (aturdido esa ronda). Movimientos enemigos con `effect`: `shield` (blindaje: mitad de daño; su debilidad lo rompe) y `drain` (quita EN). Quien cae se levanta solo a las 2 rondas (o con Reparación de HAL). `BattleEngine` es puro (eventos); la escena: `BattleStage` (fondo en capas, cámara con enfoque/sacudida/zoom, efectos, chispas en el suelo), `BattlerView` (hojas animadas), `BattleHud`, `BattleMenu`, `BattleScene` (coreografía). Arte de combate: `tools/pixelart/battle_art.py` → `assets/art/battle/` + manifiesto `assets/data/combat/sheets.json` (hojas por filas: idle/run/attack/cast/hurt/block/ko/victory; enemigos windup/attack/charge/hurt/off; efectos; fondos `sky/far/ground/fg`). Encuentros: `assets/data/combat/encounters/*.json` (`backdrop` = id del manifiesto, `sheet`, `flying`, `scan`). `Router.start_battle` / `return_from_battle` (emite `battle_finished`). `Router.battle_autoplay` = el combate se juega solo (tests). Derrota o retirada no castigan: HAL os pone a salvo y Andrés queda al 50 %.

**Audio:** autoload `Music` (`play("space" | "mission" | "title")`, fundido cruzado, filtro al entrar en HAL) y `Sfx`. Buses `Music`/`SFX` y volúmenes: `AudioSettings` (`user://the_seed_settings.cfg`). Cada escena pide su pista; los mapas pueden fijar `music` en su JSON. Música propia: `tools/audio/music.py` (numpy + scipy + ffmpeg).

**Arte:** propio generado por `tools/pixelart/generate.py` (no editar PNG a mano: cambiar el script y regenerar; llama a `city_art.py` para atlas urbanos, edificios, mobiliario y peatones) + `tools/pixelart/ambient_art.py` (vehículos, drones, robots, naves) + `tools/pixelart/battle_art.py` (combate) + Kenney Tiny Town, Roguelike Modern City e Indoors (CC0; recortes recoloreados con `tools/pixelart/third_party.py`). Licencias en `game/assets/CREDITS.md`. Tema UI global: `resources/ui/the_seed_theme.tres` (ligaduras de Pixelify desactivadas).

**ASTRA (prototipo):** movimiento en `ShipController` / `WalkerController`; cámara `FollowCamera`; HUD `FlightHud`; input `ControlAxis` + `DesktopInputReader` (listo para táctil). Parámetros en `resources/*.tres`. Controles: `game/docs/ASTRA_CONTROLS.md`.

**Descubrimientos:** datos en `assets/data/destinations/*.json`; catálogo/`ScienceNotebook`; escáner `ScannerSystem`; paneles análisis/cuaderno. Señales en `EventBus`. Fuentes: `docs/SCIENCE_REFERENCES.md`. El mapa arcade no representa distancias reales.

**Misiones:** JSON en `assets/data/missions/` (`chapter`, `order`, `kind` = `main | side`, `requires`, `start_npc`, `auto_start`, `on_complete_event`; objetivos con `condition.type` = `talk_to | scan_destination | collect_item | solve_challenge | near_destination | land_on | takeoff | interact | win_battle | have_items` y `location`/`target` para la flecha, `effects` opcionales). Una principal activa a la vez; las **secundarias** (`kind: side`) corren en paralelo y la flecha las sigue cuando la principal espera (`have_items`). Estados en `MissionLog` (persistente). Cadena principal: `last_seed` → `signal_from_moon` → `ice_of_shackleton` → `red_garden` → `methane_heart`. Secundarias del cap. 4: `side_ice_core` (Yusuf), `side_co2` (Nia), `side_catalyst` (Ada, con combate).

**Lab sondas:** `scenes/lab/probe_lab.tscn`; dominio en `scripts/domain/lab/` (opcodes + intérprete sin eval); retos en `assets/data/lab/` (`goal`, `samples`, `max_blocks`, `allow_loops`, `allow_conditions`, `theme`, `hint`). Progresión: secuencia (`launch_sequence`) → bucle (`ice_drill`) → condición `SI_MUESTRA … FIN_SI` (`delta_samples`). Las terminales del mapa abren el reto con `Router.open_lab(id)`.

**Principios**

1. Scripts pequeños, **una responsabilidad**.
2. UI no conoce HTTP: usa `EventBus` / `GameState` / `ApiClient`.
3. Dominio (`scripts/domain/`) sin nodos de escena cuando sea posible (`RefCounted` / `Resource`).
4. Offline-first: si falla la API, el juego sigue.
5. Sin plugins externos salvo necesidad justificada documentada aquí.

## Convenciones GDScript

- Tipado estático cuando aporta claridad (`func foo(id: String) -> void`).
- `snake_case` archivos/funciones; `PascalCase` `class_name`.
- Señales en `EventBus`; no acoplar escenas entre sí.
- Textos de UI en español (audiencia ~12 años); IDs de contenido en `snake_case` inglés (`demo_sol_overview`).
- Comentarios solo si aclaran intención no obvia.

## Diseño (restricciones)

- Pixel art retro + UI futurista (cian `#3de7c9`, oro `#f4d35e`, fondo `#0b1220`). En el mundo, acentos de neón fucsia `#ff3ea5` y verde `#7dff9a`.
- Ambientación **posapocalíptica cyberpunk apta para niños**: noche, neón, lluvia ácida, chatarra, megacorporaciones inventadas (AgroNet, MarsCorp). Nada de armas, sangre ni bebidas alcohólicas (los bares sirven batidos y jugos). Cada elemento cyberpunk debe poder enseñar algo real.
- **Combate apto para niños:** solo contra robots y drones de los **Antihumanistas** (clan de humanos y máquinas que no quiere que la humanidad se reconstruya). Nunca contra personas ni animales. Las herramientas son la llave magnética y el escáner de HAL; los robots se **desactivan**, no se destruyen. Perder no castiga. Cada técnica lleva un dato real.
- Filtro de texturas: **nearest** (ya en `project.godot`).
- No violencia gráfica; tono explorador/científico (el combate es un puzzle de ritmo y elementos).
- Contenido astronómico factual; puzzles de programación = secuencias, condiciones, bucles simples (sin jerga pesada).
- Una idea por pantalla; tipografía legible en móvil.

## Ejecución

```bash
# Cliente
godot --path game                    # editor / run (ventana)
godot --path game --editor

# Smoke test headless
godot --headless --path game --script res://tests/smoke_test.gd

# Backend
cd backend && cp .env.example .env   # si aún no existe
cd backend && php artisan key:generate
cd backend && php artisan serve       # http://127.0.0.1:8000
```

`ApiClient` apunta por defecto a `http://127.0.0.1:8000/api`.

## Pruebas

| Capa | Herramienta | Qué valida |
|------|-------------|------------|
| Godot | `tests/smoke_test.gd` + `--headless --script` | Autoloads, progreso, JSON |
| Godot | `tests/story_test.gd` | Historia cap. 1–4 + secundarias completa por eventos |
| Godot | `tests/world_test.gd` | Mapas, fichas enlazadas, retos resolubles |
| Godot | `tests/flow_test.gd` | Escenas reales vía Router (intro → lab → despegue → Luna) |
| Godot | `tests/economy_test.gd` | Créditos, compras, mejoras de ASTRA, puerta → bar → tienda |
| Godot | `tests/hal_test.gd` | Inventario y entregas, música, buses, interfaz de HAL con teclado |
| Godot | `tests/combat_test.gd` | Niveles y puntos, fórmulas, intenciones, cerraduras/chispas/combo, análisis, blindaje, levantarse tras K.O., simulaciones de equilibrio, combate real vía Router (autoplay) |
| Godot | `tests/ambient_test.gd` | Vida ambiental: tráfico, naves, peatones, tope de entidades, sin robar la interacción |
| Godot | `tests/ship_test.gd` | Combustible, casco, motores, mejoras, surtidores, reserva y HUD en vuelo real |
| Godot | `tests/astra_prototype_test.gd`, `discovery_test.gd`, `mission_test.gd`, `probe_interpreter_test.gd` | Vuelo, descubrimientos, misiones, intérprete del lab |
| Visual | `tests/capture_screens.gd` (con ventana; `-- <dir> ch4` solo capítulo 4) | Capturas de escenas clave |
| Godot | Ejecución manual Boot→Menú→Hub | Navegación UI |
| Laravel | `php artisan test` (PHPUnit) | Health + sync contract |
| Integración | API up + menú muestra estado | Manual / futuro script |

No inventar resultados: solo reportar salidas realmente ejecutadas.

## Backend — qué pertenece a Laravel

- `GET /api/health` — liveness
- `GET /api/lessons` — catálogo (opcional remoto)
- `POST /api/progress/sync` — progreso del cadete (sin auth en demo; auth COPPA/GDPR más adelante)

No poner secretos en el cliente. `.env` solo en `backend/`.

## Android (pendiente manual)

1. Instalar Android SDK / templates de export Godot 4.7.
2. Crear preset Android en el editor (generará `export_presets.cfg`, ignorado en git si contiene rutas locales).
3. Orientación landscape ya contemplada en `project.godot`.

## Qué no hacer en este repo (aún)

- Combate solo el descrito arriba (por turnos, en tierra, activado por misiones, contra máquinas antihumanistas). Nada de combate en el espacio ni encuentros aleatorios. Economía solo la simple que existe (créditos, tiendas, surtidores). Capítulo 4 parte 1 jugable; resto del 4 y capítulos 5–8 solo en el GDD por ahora.
- No añadir assets pesados sin licencia clara.
- No commitear `.godot/`, `vendor/`, `.env`.
