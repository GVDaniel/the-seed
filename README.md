# The Seed

Demo educativa de **RPG espacial** (pixel art + UI futurista) para ~12 años. Enseña astronomía, tecnología y bases de programación.

**Historia:** año 2187. La Marchitez secó las plantas de la Tierra. Andrés, cadete piloto, recibe de la abuela Lucía **La Semilla** (la última bóveda de semillas sanas) y viaja con la IA **HAL** en la nave **ASTRA** —Tierra → Luna → Marte— rumbo a **TRAPPIST-1e**, un exoplaneta real. Diseño completo: [`game/docs/GDD.md`](game/docs/GDD.md). Resumen narrativo vivo (misiones, personajes, roadmap): [`historia/`](historia/).

Monorepo:

- `game/` — cliente Godot 4.7
- `backend/` — API Laravel (progreso y lecciones)
- `historia/` — documentación de la historia del juego

## Requisitos

- [Godot 4.7.x](https://godotengine.org/) en el `PATH` como `godot` (en este equipo: `~/.local/bin/godot`)
- PHP **8.2+** y [Composer](https://getcomposer.org/) para el backend
- (Opcional) Android SDK + plantillas de export Godot para APK

Comprobar Godot:

```bash
godot --version
# esperado: 4.7.x.stable...
```

## Arrancar el juego

```bash
cd /ruta/a/OPORTUNITY
godot --path game          # Boot → Menú → «Nueva aventura»
```

Vertical slice jugable (capítulos 1–3 y parte 1 del capítulo 4):

1. **La Tierra Marchita** — Barrio Semilla: hablar con la abuela Lucía, escanear la planta y el aire, recoger La Semilla, programar la secuencia de despegue y despegar.
2. **Agua en la oscuridad** — Estación Aurora (Dra. Vega) → faro lunar → aterrizar en la Luna (Kai): hielo del cráter Shackleton + reto con bucles.
3. **Un jardín rojo** — Marte, base Jezero (Cmte. Osei): delta, rover, reto con condiciones y plantar el primer brote.
4. **Corazón de metano** — Bruno, en su taller, necesita un motor nuevo para ASTRA. Primer **combate por turnos** contra el Centinela AH-7 de los **Antihumanistas**, instalar el motor y fabricar metano con tres ingredientes de **misiones secundarias** (Yusuf, Nia, Ada). Final con avance de Júpiter, Europa y TRAPPIST-1e.

ASTRA empieza lenta y con poco combustible (surtidores en cada plataforma, kits de reparación en tiendas). Andrés tiene salud, niveles y puntos de **aptitudes / conocimientos / destrezas** (HAL → pestaña *Andrés*). Combate: elige acción, pulsa **Espacio/E** cuando el anillo toque el círculo para golpear fuerte o bloquear, rompe las cerraduras con el elemento correcto.

La flecha dorada siempre apunta al siguiente objetivo. Controles: [`game/docs/ASTRA_CONTROLS.md`](game/docs/ASTRA_CONTROLS.md).

```bash
# Ir directo a una escena
godot --path game res://scenes/space/space_main.tscn
godot --path game res://scenes/surface/surface_level.tscn   # Tierra por defecto
godot --path game --editor
```

### Reiniciar progreso

Desde el menú: **Nueva aventura** (pide confirmación). A mano:

```bash
rm ~/.local/share/godot/app_userdata/The\ Seed/the_seed_*.cfg
```

## Arrancar el backend

```bash
cd backend
cp .env.example .env   # solo la primera vez
php artisan key:generate
php artisan serve
```

API base: `http://127.0.0.1:8000/api`

| Método | Ruta | Uso |
|--------|------|-----|
| GET | `/health` | Estado del servicio |
| GET | `/lessons` | Catálogo de lecciones |
| POST | `/progress/sync` | Sincronizar progreso del cadete |

El cliente intenta `GET /health` al abrir el menú; si no hay backend, el juego sigue en modo offline.

## Tests headless (Godot)

```bash
godot --headless --path game --script res://tests/smoke_test.gd
godot --headless --path game --script res://tests/astra_prototype_test.gd
godot --headless --path game --script res://tests/discovery_test.gd
godot --headless --path game --script res://tests/mission_test.gd
godot --headless --path game --script res://tests/probe_interpreter_test.gd
godot --headless --path game --script res://tests/story_test.gd   # historia cap. 1–4 + secundarias por eventos
godot --headless --path game --script res://tests/world_test.gd   # mapas, fichas, encuentros y retos resolubles
godot --headless --path game --script res://tests/flow_test.gd    # escenas reales vía Router
godot --headless --path game --script res://tests/economy_test.gd # créditos, tiendas, mejoras
godot --headless --path game --script res://tests/hal_test.gd     # inventario, audio, interfaz de HAL
godot --headless --path game --script res://tests/combat_test.gd  # niveles, combate (motor + escena real)
godot --headless --path game --script res://tests/ship_test.gd    # combustible, casco, surtidores, vuelo
```

Capturas para revisión visual (abre ventana):

```bash
godot --path game --script res://tests/capture_screens.gd -- /tmp/screens
godot --path game --script res://tests/capture_screens.gd -- /tmp/screens ch4   # solo capítulo 4
```

## Herramientas de arte

```bash
python3 tools/pixelart/generate.py     # personajes, retratos, nave, planetas, props, tiles, ilustraciones
python3 tools/pixelart/sfx.py          # efectos de sonido
python3 tools/audio/music.py [pista]   # música (space, mission, title, cantina, battle) → .ogg
python3 tools/maps/build_maps.py       # genera todos los mapas (exteriores e interiores)
python3 tools/maps/preview_map.py mars /tmp/mars.png   # vista previa de un mapa JSON
```

Licencias: [`game/assets/CREDITS.md`](game/assets/CREDITS.md).

Laboratorio de sondas: menú → *Laboratorio de sondas*, o botón en el HUD espacial.

Referencias científicas: [`game/docs/SCIENCE_REFERENCES.md`](game/docs/SCIENCE_REFERENCES.md)

## Tests Laravel

```bash
cd backend
php artisan test
```

## Estructura (resumen)

Ver `CLAUDE.md` para convenciones, arquitectura y restricciones de diseño.

```
OPORTUNITY/
├── CLAUDE.md
├── README.md
├── game/                 # proyecto Godot
│   ├── project.godot
│   ├── scenes/
│   ├── scripts/
│   ├── assets/data/
│   └── tests/
├── tools/                # generadores de pixel art, sonido y previsualización de mapas
└── backend/              # Laravel API
```

## Pasos manuales pendientes

- Abrir el proyecto una vez en el editor Godot para completar el import de recursos (`.godot/`).
- Configurar preset de export **Android** cuando se necesite APK.
- Definir política de privacidad / edad antes de auth real en producción.
- Controles táctiles para Android (el `ControlAxis` ya admite entrada virtual).
- Música (buscar CC0 o encargar).
- Capítulo 4 parte 2 (Júpiter/Europa) y capítulos 5–8 (ver GDD).
- Controles táctiles del combate en Android (ya funciona con toque/ratón; falta probar en dispositivo).
