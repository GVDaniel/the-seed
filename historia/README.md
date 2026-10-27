# Historia de The Seed

Esta carpeta documenta la **narrativa, misiones, personajes y lugares** del juego. Sirve para escribir, revisar y ampliar la historia sin depender solo de los JSON de código.

## Cómo usarla

| Archivo | Contenido |
|---------|-----------|
| [00-premisa.md](00-premisa.md) | Premisa, tono, audiencia, mensaje |
| [01-arco-narrativo.md](01-arco-narrativo.md) | Capítulos y cinemáticas |
| [02-misiones.md](02-misiones.md) | Misiones jugables (detalle) |
| [03-personajes.md](03-personajes.md) | Tripulación y NPCs |
| [04-lugares.md](04-lugares.md) | Mundos, bases y puntos de interés |
| [05-laboratorio.md](05-laboratorio.md) | Retos de programación ligados a la trama |
| [06-roadmap-futuro.md](06-roadmap-futuro.md) | Capítulos planeados y huecos |
| [CHANGELOG-historia.md](CHANGELOG-historia.md) | Registro de cambios narrativos |

## Fuentes de verdad en el código

Cuando cambies historia **jugable**, actualiza también (o primero) estos datos:

- `game/assets/data/story/chapters.json`
- `game/assets/data/story/cutscenes.json`
- `game/assets/data/missions/*.json`
- `game/assets/data/characters/*.json`
- `game/assets/data/destinations/*.json`
- `game/assets/data/combat/` (técnicas y encuentros)
- `game/scripts/autoload/story_director.gd`

Esta carpeta es el **resumen humano**. Los JSON son lo que el juego ejecuta.

## Convención al ampliar

1. Escribe o edita el `.md` aquí (borrador / canon).
2. Refleja el cambio en el JSON correspondiente.
3. Anota una línea en `CHANGELOG-historia.md`.

## Estado del vertical slice (demo)

Capítulos **1–3** y **4 · parte 1** («Corazón de metano», con tres misiones secundarias y los dos primeros combates) jugables + teaser de **Júpiter / TRAPPIST-1e**. Resto del capítulo 4 y capítulos 5–8: solo diseño / roadmap.
