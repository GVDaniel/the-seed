# The Seed — convenciones para agentes y desarrolladores

Demo educativa (Godot 4.x + Laravel) para ~12 años: RPG espacial pixel-art con UI futurista. Enseña astronomía, tecnología y bases de programación. Historia: Andrés lleva **La Semilla** desde la Tierra marchita (2187) hacia TRAPPIST-1e. Diseño: `game/docs/GDD.md`.

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
    autoload/      # EventBus, GameState, ApiClient, StoryDirector, Router, Music, Sfx, Inventory, Economy
    domain/        # Lógica pura / DTOs (astronomy, coding, progress)
    ui/            # Controladores de escena (una responsabilidad)
    net/           # Extensiones HTTP futuras
    boot/          # Arranque
  tests/           # Scripts headless (--script)

backend/
  routes/api.php   # /health, /lessons, /progress/sync
  app/Http/...     # Controllers delgados
```

**Flujo jugable:** Boot → Menú → cinemática intro → superficie Tierra → laboratorio → espacio → Luna → Marte → cinemática final. Navegación siempre vía autoload `Router` (fundidos, retorno del laboratorio, despegue).

**Historia (autoload `StoryDirector`):** traduce eventos del `EventBus` (`scan_completed`, `item_collected`, `challenge_solved`, `landed_on`, `took_off`, `world_interacted`, diálogos) en objetivos de misión; decide qué dice cada NPC (`offer` / objetivo `talk_to` / `reminder` / `after` / líneas idle). Reglas de acceso (`can_land`, `can_take_off`, `can_collect`, `can_interact`) viven aquí, no en escenas. Capítulos: `assets/data/story/chapters.json`; personajes: `assets/data/characters/`; cinemáticas: `assets/data/story/cutscenes.json`.

**Ciudades, vecinos y tiendas:** mapas generados por `tools/maps/build_maps.py` (no editar los JSON a mano: cambiar el script y regenerar). Entidades nuevas: `door` (con `target`/`spawn` lleva a otro mapa; sin ellos, lee `lines`), `light` y la clave `light` en cualquier entidad (`NeonLight`), `npc` con `wander` (pasea) o `shop` (abre `ShopPanel`), `z` para piezas planas. Interiores con `region` (p. ej. `moon_bar` → `moon`, en `GameState.region`). Personajes con `group` = `crew | local`. Autoload `Economy`: créditos (`GameState.credits`), recompensas y compras; tiendas en `assets/data/shops/`; mejoras de ASTRA vía `effects` en el objeto (`ShipUpgrades`).

**Superficies:** una escena genérica `scenes/surface/surface_level.tscn` carga `assets/data/maps/<id>.json` (leyenda ASCII → `TileMapLayer`, entidades `npc/scan/item/terminal/ship/object/sign/prop/spawn`). Previsualizar: `python3 tools/maps/preview_map.py <id> out.png`. Jugador: `scenes/player/andres.tscn` (`WalkerController` + `CharacterSprite`).

**HAL (compañera, homenaje a HAL 9000):** panel plateado con lente roja que sigue a Andrés (`HalFollower`). `Tab`/`I` o el botón del HUD abren `scenes/ui/hal/hal_interface.tscn` (pide abrir vía `EventBus.hal_interface_requested`, avisa con `hal_interface_toggled`). Pestañas, un script cada una en `scripts/ui/hal/`: inventario, mapa (`HalMinimap` dibuja el JSON del mapa; `HalSystemMap` la ruta), misiones, cuaderno, tripulación (`StoryDirector.has_met`), sistema (volumen). Las escenas anfitrionas bloquean movimiento/escáner mientras está abierta.

**Inventario (autoload `Inventory`):** objetos en `assets/data/items/*.json` (`starter`, `granted_by` = `solve_challenge | scan_destination`, `fact` real). Guarda en `GameState.items`.

**Audio:** autoload `Music` (`play("space" | "mission" | "title")`, fundido cruzado, filtro al entrar en HAL) y `Sfx`. Buses `Music`/`SFX` y volúmenes: `AudioSettings` (`user://the_seed_settings.cfg`). Cada escena pide su pista; los mapas pueden fijar `music` en su JSON. Música propia: `tools/audio/music.py` (numpy + scipy + ffmpeg).

**Arte:** propio generado por `tools/pixelart/generate.py` (no editar PNG a mano: cambiar el script y regenerar) + Kenney Tiny Town (CC0) para la Tierra. Licencias en `game/assets/CREDITS.md`. Tema UI global: `resources/ui/the_seed_theme.tres` (ligaduras de Pixelify desactivadas).

**ASTRA (prototipo):** movimiento en `ShipController` / `WalkerController`; cámara `FollowCamera`; HUD `FlightHud`; input `ControlAxis` + `DesktopInputReader` (listo para táctil). Parámetros en `resources/*.tres`. Controles: `game/docs/ASTRA_CONTROLS.md`.

**Descubrimientos:** datos en `assets/data/destinations/*.json`; catálogo/`ScienceNotebook`; escáner `ScannerSystem`; paneles análisis/cuaderno. Señales en `EventBus`. Fuentes: `docs/SCIENCE_REFERENCES.md`. El mapa arcade no representa distancias reales.

**Misiones:** JSON en `assets/data/missions/` (`chapter`, `order`, `requires`, `start_npc`, `auto_start`, `on_complete_event`; objetivos con `condition.type` = `talk_to | scan_destination | collect_item | solve_challenge | near_destination | land_on | takeoff | interact` y `location`/`target` para la flecha). Estados en `MissionLog` (persistente). Cadena: `last_seed` → `signal_from_moon` → `ice_of_shackleton` → `red_garden`.

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
- Ambientación **posapocalíptica cyberpunk apta para niños**: noche, neón, lluvia ácida, chatarra, megacorporaciones inventadas (AgroNet, MarsCorp). Nada de violencia, armas ni bebidas alcohólicas (los bares sirven batidos y jugos). Cada elemento cyberpunk debe poder enseñar algo real.
- Filtro de texturas: **nearest** (ya en `project.godot`).
- No violencia gráfica; tono explorador/científico.
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
| Godot | `tests/story_test.gd` | Historia cap. 1–3 completa por eventos |
| Godot | `tests/world_test.gd` | Mapas, fichas enlazadas, retos resolubles |
| Godot | `tests/flow_test.gd` | Escenas reales vía Router (intro → lab → despegue → Luna) |
| Godot | `tests/economy_test.gd` | Créditos, compras, mejoras de ASTRA, puerta → bar → tienda |
| Godot | `tests/hal_test.gd` | Inventario y entregas, música, buses, interfaz de HAL con teclado |
| Visual | `tests/capture_screens.gd` (con ventana) | Capturas de escenas clave |
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

- No implementar combate. Economía solo la simple que existe (créditos, tiendas de objetos únicos). Capítulos 4–8 solo en el GDD por ahora.
- No añadir assets pesados sin licencia clara.
- No commitear `.godot/`, `vendor/`, `.env`.
