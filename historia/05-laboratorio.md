# Laboratorio de sondas (ligado a la trama)

El laboratorio enseña **secuencias**, **órdenes**, **depuración** y luego **bucles** sencillos.  
Intérprete propio (opcodes fijos): sin `eval` ni código libre del jugador.

Escena: `game/scenes/lab/probe_lab.tscn`  
Datos: `game/assets/data/lab/`

## Conceptos que el juego explica

| Concepto | En palabras de ~12 años |
|----------|-------------------------|
| **Secuencia** | Las órdenes se hacen una tras otra, en el orden de la lista. |
| **Condición** | Una pregunta sí/no (¿puedo escanear aquí?). El intérprete la comprueba al ejecutar. |
| **Bucle** | Repetir un bloque varias veces (`REPETIR` … `FIN_REPETIR`) sin copiar lo mismo. |

## Retos unidos a misiones

| ID lab | Título | Misión | Briefing narrativo |
|--------|--------|--------|--------------------|
| `launch_sequence` | Secuencia de despegue | `last_seed` | Antes de despegar, la sonda de mantenimiento revisa el tanque (estrella) y envía «TODO LISTO» desde la antena. |
| `ice_drill` | Taladro de hielo | `ice_of_shackleton` | 4 bloques de hielo en fila; recoger todos y transmitir. Límite corto de programa (fuerza a pensar). |
| `delta_samples` | Muestras del delta | `red_garden` | Recoger solo donde hay muestra y transmitir; límite de bloques. |

## Otros retos (práctica, no misión)

| ID | Título | Notas |
|----|--------|-------|
| `challenge_scan_transmit` | Recoger y enviar | Primer reto tutorial (secuencia básica) |
| `challenge_loop_corridor` | Pasillo con bucle | Segunda dificultad; introduce `REPETIR` |

## Instrucciones disponibles (opcodes)

`AVANZAR` · `GIRAR_IZQUIERDA` · `GIRAR_DERECHA` · `ESCANEAR` · `TRANSMITIR`  
(+ `REPETIR` / `FIN_REPETIR` cuando el reto lo permite)

## Idea al escribir nuevos labs de historia

1. El reto debe **resolver un problema de la misión** (despegar, taladrar, muestrear…).
2. Briefing en voz de NPC o de HAL.
3. Victoria = estado del mundo (escaneado + transmitido), no “el jugador apretó el botón”.
