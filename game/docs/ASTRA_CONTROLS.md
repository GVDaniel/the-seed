# ASTRA — controles y parámetros

## Controles (escritorio)

| Acción | Teclas | InputMap |
|--------|--------|----------|
| Acelerar | `W` / ↑ | `ship_thrust` |
| Frenar / retro | `S` / ↓ | `ship_brake` |
| Girar | `A` `D` / ← → | `ship_turn_left` / `ship_turn_right` |
| Aterrizar | `E` (dentro del anillo de la Tierra, Luna o Marte) | `interact_land` |
| Escanear destino | `F` (en rango) | `scanner_scan` |
| Hablar (estación) | `T` (cerca de Aurora) | `interact_talk` |
| Entrar en HAL (inventario, mapa, misiones, cuaderno, tripulación, sistema) | `Tab` / `I` o botón «HAL» del HUD | `hal_menu` |
| HAL → Cuaderno científico | `N` | `notebook_toggle` |
| HAL → Mapa | `M` | `map_toggle` |
| Cambiar pestaña dentro de HAL | `Q` / `E` o `1`–`6` | `hal_prev_tab` / `hal_next_tab` |
| Cerrar paneles | `Esc` | `panel_close` / `ui_cancel` |
| Caminar | `WASD` / flechas | `walk_*` |
| Interactuar (hablar, comprar, entrar por una puerta, recoger, terminal, subir a ASTRA) | `E` (en superficie) | `interact` |
| Escanear punto científico (estrella dorada) | `F` (en superficie) | `scanner_scan` |
| Avanzar diálogo | `Espacio` / `E` / `Enter` | `ui_accept` / `interact` |

Táctil (futuro): escribir en el mismo `ControlAxis` vía `set_virtual_thrust`, `set_virtual_turn`, `set_virtual_move` sin tocar `ShipController` / `WalkerController`.

## Parámetros (sin tocar código)

| Recurso | Ruta | Qué ajusta |
|---------|------|------------|
| `ShipStats` | `resources/ship_stats_astra.tres` | aceleración, velocidad máx., giro, desaceleración, energía |
| `WalkerStats` | `resources/walker_stats_cadet.tres` | aceleración, velocidad, fricción a pie |

También editables en el inspector sobre la instancia de la nave / cadete.

## Escenas

| Escena | Rol |
|--------|-----|
| `scenes/space/space_main.tscn` | Vuelo: Tierra, Aurora, Luna, faro, Marte, basura espacial |
| `scenes/surface/surface_level.tscn` | Superficie genérica (mapa JSON) |
| `scenes/ship/astra_ship.tscn` | Nave (sprite + llama) |
| `scenes/player/andres.tscn` | Andrés a pie (4 direcciones) |
| `scenes/planet/planet_zone.tscn` | Planeta escaneable / aterrizable (`surface_location`) |
| `scenes/space/scannable_destination.tscn` | Estación Aurora (`npc_id = vega`), faro lunar |
| `scenes/story/cutscene.tscn` | Cinemáticas intro / final |
| `scenes/ui/flight_hud.tscn` | HUD (vel, energía, nombre) |
| `scenes/ui/analysis_panel.tscn` | Ficha científica tras escanear |
| `scenes/ui/hal/hal_interface.tscn` | Interfaz de HAL: 6 pestañas (`scripts/ui/hal/`) |

## Descubrimientos

- Datos: `assets/data/destinations/*.json` (separados de la UI)
- Catálogo / cuaderno: `DestinationCatalog`, autoload `ScienceNotebook`
- Señales: `EventBus.destination_scanned`, `discovery_added`, `scan_completed`, …
- Referencias y distinción real/simplificación: `docs/SCIENCE_REFERENCES.md`
- El mapa arcade **no** representa distancias reales del sistema solar.

## Misiones

- Datos: `assets/data/missions/*.json` (independientes de la UI)
- Estados: `available` → `active` → `completed` (`MissionLog`)
- Primera misión: **Señal desde la Luna** — Aurora → Luna → faro `lunar_probe_signal` → volver a Aurora
- HUD: registro de misión + toasts de objetivo
- Persistencia: `user://the_seed_missions.cfg` (una misión completada no se reinicia al cargar)

## Laboratorio de sondas

- Escena: `scenes/lab/probe_lab.tscn`
- Retos JSON: `assets/data/lab/`
- Instrucciones (opcodes fijos, sin eval): `AVANZAR`, `GIRAR_IZQUIERDA`, `GIRAR_DERECHA`, `ESCANEAR`, `TRANSMITIR` (+ `REPETIR`/`FIN_REPETIR` en reto 2)
- Intérprete: `ProbeInterpreter` — solo lista de opcodes validados
- Victoria: escanear POI + transmitir en la antena (estado real del mundo)

## Separación de responsabilidades

- **Movimiento:** `ShipController`, `WalkerController`
- **Cámara:** `FollowCamera`
- **HUD:** `FlightHud`
- **Escáner:** `ScannerSystem`
- **Misiones:** `MissionLog` + `MissionDirector` + `DialoguePanel`
- **Modos espacio/superficie:** `SpaceDirector`
- **Input:** `DesktopInputReader` + `ControlAxis`
