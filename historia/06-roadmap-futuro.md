# Roadmap narrativo y huecos

## Planeado (diseño / GDD — aún no jugable)

Nombres mencionados en ending / GDD. **No hay** misiones ni cutscenes implementadas salvo el teaser.

| Cap. | Título tentativo | Idea |
|------|------------------|------|
| 4 · parte 2 | Gigante de tormentas | Júpiter / Europa (base semipermanente; ASTRA ya tiene el motor de metano) |
| 5 | Lagos de metano | Titán |
| 6 | El borde | Heliopausa / Voyager |
| 7 | Años luz | Tránsito interestelar |
| 8 | Nueva Semilla | Llegada / plantación en TRAPPIST-1e |

Al implementar un capítulo nuevo:

1. Añadir entrada en `chapters.json`.
2. Crear `missions/<id>.json` con `requires` encadenado.
3. Actualizar [02-misiones.md](02-misiones.md) y este archivo.
4. Registrar en [CHANGELOG-historia.md](CHANGELOG-historia.md).

## Huecos conocidos (datos actuales)

| Hueco | Notas |
|-------|-------|
| Cap. 4 parte 2 y caps. 5–8 | Solo teaser HAL + nombres en GDD |
| Líderes de los Antihumanistas | Solo robots y el chip de órdenes; falta la cara humana del clan |
| Uso del chip de órdenes | Objeto clave sin uso posterior todavía (¿descifrarlo en el lab?) |
| Combates fuera de Marte | Solo dos encuentros; pensar uno por capítulo (no aleatorios) |
| Diálogo `offer` de `last_seed` | Auto-start; no hay oferta hablada |
| Unlock de destinations tras `last_seed` | No hay `unlock_destination_id` en esa misión |
| Ficha `mars_greenhouse` | Usada en objetivo; falta destination JSON dedicado |
| Arcos de NPCs locales | Solo ambientación / idle |
| Gameplay en TRAPPIST-1e | Unlock + informe + cinemática; sin mapa profundo |
| Relación AgroNet / MarsCorp | Mencionado; sin misión de conflicto |

## Preguntas abiertas (para decidir en equipo)

- ¿La Semilla se planta solo en TRAPPIST o también deja brotes en cada mundo?
- ¿HAL tiene un arco emocional / “error” amable en caps. posteriores?
- ¿Vega viaja con Andrés o se queda en Aurora?
- ¿Qué tono exacto para el “Gigante de tormentas” (miedo respetuoso vs maravilla)?
- ¿Los Antihumanistas pueden cambiar de bando (un robot reprogramado que se une)?
- ¿Qué mejora de ASTRA hace falta para Europa (escudo de radiación)?

Añade aquí decisiones cuando se tomen.
