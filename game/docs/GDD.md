# The Seed — Documento de diseño (GDD)

> Versión 0.8 · vertical slice (capítulos 1–3). Audiencia: ~12 años. Español.

## 1. Concepto en una frase

**Andrés, cadete de 13 años, debe sacar de la Tierra marchita la última bóveda de semillas —La Semilla— y encontrar un planeta donde la humanidad pueda volver a empezar.**

Pilares:

| Pilar | Qué siente el jugador | Qué aprende |
|-------|-----------------------|-------------|
| **Explorar** | Pilotar ASTRA y caminar por mundos distintos | Astronomía real (escala, gravedad, atmósferas, agua) |
| **Descubrir** | Escanear y llenar el Cuaderno científico | Método científico: observar → registrar → concluir |
| **Programar** | Hacer que una sonda resuelva un problema con órdenes | Secuencias → bucles → condiciones |
| **Cuidar** | Mantener viva La Semilla | Ecología: fotosíntesis, oxígeno, suelo, clima |

**Ambientación: posapocalíptica cyberpunk, apta para niños.** Ciudades bajo cúpulas, noches de neón, lluvia ácida, chatarra reciclada, anuncios holográficos y megacorporaciones inventadas (**AgroNet** en la Tierra, **MarsCorp** en Marte) que venden lo que antes era gratis: comida, agua y hasta aire embotellado. La gente común repara, recicla y se ayuda. Los peligros son ambientales y sociales, nunca violentos. Cada elemento cyberpunk enseña algo real: lluvia ácida, fotosíntesis, reciclaje de aire en bases, contaminación lumínica.

Tono: esperanza, curiosidad y trabajo en equipo. **Sin violencia**: los obstáculos son naturales (polvo, frío, radiación, falta de energía, basura espacial).

## 2. Historia

### Premisa — Año 2187

La Tierra sufre **La Marchitez**: una plaga de hongos, junto con décadas de calentamiento global, mató la mayoría de las plantas. El cielo es ocre, el aire cuesta respirarlo y los bosques son troncos secos. La humanidad sobrevive en ciudades-cúpula.

En el norte resiste la **Bóveda Semillera** (inspirada en la real *Svalbard Global Seed Vault*, Noruega). Su guardiana, la **abuela Lucía**, protege el último cofre de semillas sanas: **La Semilla**.

La Dra. Vega, desde la Estación Aurora, recibió datos del telescopio espacial (inspirados en observaciones reales del JWST) que apuntan a **TRAPPIST-1e**, un planeta rocoso en la zona habitable de otra estrella. Alguien debe llevar La Semilla hasta allí. Andrés, de la familia de Lucía y con las mejores notas de pilotaje de la academia de cadetes, se ofrece.

### Arco completo (8 capítulos)

| # | Capítulo | Lugar | Gancho narrativo | Ciencia | Programación |
|---|----------|-------|------------------|---------|--------------|
| 1 | **La Tierra Marchita** | Barrio Semilla (Tierra) | Recibir La Semilla y despegar | Atmósfera, fotosíntesis, CO₂ | Secuencias |
| 2 | **Agua en la oscuridad** | Aurora + Luna (cráter Shackleton) | Recuperar una señal y encontrar hielo para combustible | Fases, cráteres, hielo polar, gravedad 1/6 | Bucles (`REPETIR`) |
| 3 | **Un jardín rojo** | Marte (cráter Jezero) | Plantar el primer brote fuera de la Tierra… y descubrir que Marte no basta | Óxido de hierro, delta antiguo, presión, radiación | Condiciones (`SI … FIN_SI`) |
| 4 | Gigante de tormentas | Júpiter / Europa | Asistencia gravitatoria; océano bajo el hielo | Gravedad, mareas | Bucles anidados |
| 5 | Lagos de metano | Saturno / Titán | Repostar y reparar la vela solar | Anillos, química del metano | Variables (contadores) |
| 6 | El borde | Heliopausa | Encuentro con la Voyager 1 | Viento solar, heliosfera | Funciones (bloques con nombre) |
| 7 | Años luz | Viaje interestelar | Hibernación y la IA HAL al mando | Año luz, velocidad de la luz | Depuración |
| 8 | **Nueva Semilla** | TRAPPIST-1e | Plantar La Semilla. Final | Exoplanetas, zona habitable, acoplamiento de marea | Proyecto libre |

**Este vertical slice implementa los capítulos 1–3** y termina con un avance de TRAPPIST-1e.

### Tema y mensaje

Marte enseña la lección central: **no existe un "planeta B" fácil**. Hace falta ciencia, paciencia y cuidar lo que se tiene. El viaje a TRAPPIST-1e es la esperanza, no una huida.

## 3. Personajes

| Personaje | Rol | Personalidad | Diseño visual |
|-----------|-----|--------------|---------------|
| **Andrés** | Protagonista, cadete piloto (13) | Curiosidad, valentía y algo de impaciencia; aprende a planear antes de actuar | Traje blanco con franjas cian, mochila-cofre dorada (La Semilla), pelo castaño |
| **HAL** | IA de ASTRA y compañera flotante (serie HAL 9000) | Calma absoluta, muy lógica y un poco literal; presume de no equivocarse nunca. Enseña a programar | **Homenaje a HAL 9000** (*2001: Una odisea del espacio*): panel plateado, cara negra y lente roja con centro dorado que late al hablar. Amable, nunca amenazante |
| **Abuela Lucía** | Guardiana de la Bóveda Semillera | Sabia, cálida, botánica | Pelo blanco recogido, delantal verde, bastón |
| **Dra. Elena Vega** | Astrobióloga, jefa de Aurora | Rigurosa y entusiasta: "¿qué dicen los datos?" | Bata morada, gafas, tablet |
| **Kai Tanaka** | Ingeniero de la base lunar Shackleton (16) | Bromista, inventor, le encantan las sondas | Mono naranja, casco con visera, llave inglesa |
| **Cmte. Amara Osei** | Comandante de la base marciana Jezero | Firme, protectora, ex geóloga | Traje rojo terracota, insignia, trenzas |

Diálogo: frases cortas (≤ 140 caracteres), una idea por línea, y retratos en pixel art.

### Gente de cada lugar (vecinos)

Personajes con biografía, implantes, visores o crestas de neón. Cada uno cuenta datos reales en su diálogo.

| Lugar | Personajes |
|-------|-----------|
| Tierra (Barrio Semilla) | **Don Ramiro**, tendero de *El Último Brote*; **Mateo**, vecino de 10 años; **Amaru Quispe**, técnica de la cúpula de aire (lluvia ácida); **Zoe «Chispa»**, chatarrera (reciclaje) |
| Luna (Shackleton) | **Lupe**, dueña del *Bar Cráter*; **Ingrid Larsen**, mecánica de *Repuestos Regolito*; **Tomás**, minero de hielo; **Dra. Amina Diallo**, astrónoma |
| Marte (Jezero) | **Chen Wei**, *Mercado de Jezero*; **Rosa**, *Cantina Polvo Rojo*; **Yusuf**, maestro; **Nia**, alumna nacida en Marte; **Bruno**, mecánico de rovers |

## 4. Mundos y mapas

Distancias del mapa espacial: arcade, no reales (ver `SCIENCE_REFERENCES.md`).

### Capítulo 1 — Barrio Semilla (Tierra, superficie)

```
 Bosque seco ─────────── Bóveda Semillera (Lucía)
     │                          │
 Casa de Andrés ── Plaza ── Invernadero muerto
     │                │
 Sensor de aire    Plataforma de lanzamiento (ASTRA + terminal HAL)
```

- Paleta: verdes apagados, árboles naranjas o secos y cielo ocre (Tiny Town de Kenney, recoloreado).
- Puntos de escaneo: planta marchita (fotosíntesis), sensor de aire (CO₂), panel solar (energía del Sol).
- Objeto clave: **La Semilla** (cofre en la bóveda).
- Reto de programación: **Secuencia de despegue** (ordenar comprobaciones de la nave).

### Capítulo 2 — Órbita, Estación Aurora y Luna (base Shackleton)

- Espacio: Tierra, Aurora, Luna, faro de la sonda y anillo de **basura espacial** (concepto real; resta energía al chocar).
- Superficie lunar: regolito gris, cráteres, base modular, y el cráter en sombra permanente con **hielo de agua** (hecho real en el polo sur lunar).
- Reto: **Taladro de hielo** con `REPETIR`.

### Capítulo 3 — Marte (base Jezero)

- Superficie: suelo rojo (óxido de hierro), el delta del antiguo río, la cúpula-invernadero y un rover inspirado en *Perseverance*.
- Evento: tormenta de polvo (visual, sin daño) que obliga a la sonda a decidir.
- Reto: **Muestras del delta** con `SI_MUESTRA … FIN_SI`.
- Cierre: el brote crece en el invernadero, pero Osei explica por qué Marte no puede ser un hogar abierto. Vega comunica las coordenadas de TRAPPIST-1e. *Continuará…*

### Ciudades e interiores

- **Tierra:** *Calle Neón* (al este) con la tienda *El Último Brote*, casas, máquina de aire embotellado, anuncios de AgroNet y la chatarrería de Zoe; *calle sur* con más casas. Siempre es de noche y llueve ácido.
- **Luna:** distrito Shackleton al sur de la nave: *Bar Cráter*, *Repuestos Regolito* y módulos-vivienda.
- **Marte:** colonia Jezero al sur: *Cantina Polvo Rojo*, *Mercado de Jezero*, escuela, taller y casas. Tormenta de polvo.
- **Interiores** (puertas `door` → otro mapa): `earth_shop`, `moon_bar`, `moon_shop`, `mars_bar`, `mars_shop`. Las casas no se abren: al llamar a la puerta se lee una nota o una pista.
- **Luz:** mapas oscuros (`"dark": true`) con luces de neón reales (`PointLight2D`). Algunos letreros parpadean. Andrés lleva una luz suave y la lente de HAL ilumina en rojo.

## 5. Jugabilidad

### Bucle principal

```
Hablar (misión) → Viajar (pilotar) → Explorar (caminar) → Escanear (aprender)
      ↑                                                    ↓
   Recompensa (XP, rango, ficha) ← Programar (resolver) ←──┘
```

### Sistemas

| Sistema | Implementación |
|---------|----------------|
| Pilotaje | `ShipController` (empuje, giro, energía) |
| Caminar | `WalkerController` + animación en 4 direcciones (`CharacterSprite`) |
| Interacción | `Interactable` (Área + texto) → `EventBus.interaction_requested` |
| Diálogo | `DialoguePanel` con retrato y efecto máquina de escribir |
| Misiones | JSON con `requires`, `start_npc`, `chapter` y objetivos `talk_to / scan / collect / solve_challenge / land_on / near_destination / interact` |
| Historia | Autoload `StoryDirector`: traduce eventos a objetivos (sin escenas acopladas) |
| Mundos | Mapas ASCII en JSON → `SurfaceMap` pinta `TileMapLayer` |
| Laboratorio | Intérprete de opcodes + `RECOGER`, `SI_MUESTRA` / `FIN_SI` |
| Progreso | XP → **rango de cadete** (Aprendiz → Explorador → Navegante → Pionero) |
| Economía | **Créditos**: 30 al empezar, +60 por misión, +10 por descubrimiento, +25 por programa resuelto (solo la primera vez). Se gastan en tiendas y bares (`Economy`, `assets/data/shops/`) |
| Tiendas | Hablar con el dependiente abre el mostrador: productos con precio, ficha y **dato real**. Las **mejoras de ASTRA** cambian el vuelo: batería (+50 % de energía), escudo Whipple (−50 % de daño por basura), motor iónico (+25 % de velocidad). Los recuerdos y la comida son coleccionables con dato científico |

### Controles

Escritorio: `WASD` para mover o pilotar, `E` para interactuar, aterrizar o despegar, `F` para escanear, `Tab` para entrar en HAL (`N` cuaderno, `M` mapa) y `Esc` para cerrar. Táctil: pendiente (el `ControlAxis` ya está listo).

### HAL: entrar en su sistema

HAL no es solo una voz: el jugador puede **entrar en ella** (`Tab` / `I` o el botón del HUD). La pantalla se llena con su ojo rojo, la música se apaga como si estuvieras dentro y aparecen seis pestañas:

| Pestaña | Qué muestra | Qué aprende o decide el jugador |
|---------|-------------|---------------------------------|
| **Inventario** | 12 casillas: equipo (traje, escáner), La Semilla, programas y muestras | Cada objeto trae un **dato real** (Svalbard, electrólisis, Perseverance…) |
| **Mapa** | «Aquí»: plano de la superficie con personajes, puntos por escanear, terminales, nave y objetivo. «Ruta de ASTRA»: Tierra → Aurora → Luna → Marte → ? → TRAPPIST-1e | Orientarse sin perderse; las distancias reales van en el pie (el mapa no está a escala) |
| **Misiones** | Capítulo actual y bitácora: hechas, en curso (con lista de pasos) y bloqueadas | Planear: ver el programa de la misión paso a paso |
| **Cuaderno** | Fichas científicas escaneadas, con datos y simplificaciones marcadas | Método científico: observar, registrar y concluir |
| **Tripulación** | Retratos y biografías; los desconocidos aparecen como silueta | Ganas de explorar para conocer a todos |
| **Sistema** | Rango y XP para el siguiente, volumen de música y efectos, controles, volver al menú | — |

Los objetos llegan por la historia: el **Programa de despegue** al resolver el reto, los **Datos de la sonda** al escanear la señal, el **Hielo lunar** con el taladro y las **Muestras del delta** en Marte.

## 6. Programación: progresión didáctica

| Reto | Concepto | Nueva instrucción | Ejemplo de solución |
|------|----------|-------------------|---------------------|
| Secuencia de despegue | Orden importa | — | `AVANZAR, AVANZAR, ESCANEAR, GIRAR_DERECHA, AVANZAR, TRANSMITIR` |
| Recoger y enviar (existente) | Secuencia | — | |
| Pasillo (existente) | Bucle | `REPETIR` | |
| Taladro de hielo | Bucle útil | `RECOGER` | `REPETIR 3 [AVANZAR, RECOGER]` |
| Muestras del delta | Condición | `SI_MUESTRA` | `REPETIR 5 [AVANZAR, SI_MUESTRA [RECOGER]]` |

Regla de diseño: cada reto se resuelve en ≤ 12 bloques y tiene **una** idea nueva.

## 7. Arte

- **Personajes, nave, planetas, retratos y props**: generados con `tools/pixelart/generate.py` (propios, mismo estilo: 16 px, contorno oscuro, paleta limitada).
- **Tiles de la Tierra**: Kenney *Tiny Town* (CC0), recoloreados a "marchito".
- **Tiles de la Luna y Marte**: generados (ruido con tramado).
- **Tipografía**: Pixelify Sans (OFL) para texto y Kenney Future (CC0) para títulos.
- **UI**: `StyleBoxFlat` futurista (cian `#3de7c9`, oro `#f4d35e`, fondo `#0b1220`).
- Licencias: `game/assets/CREDITS.md`.

## 8. Audio

Efectos (blip, escaneo, éxito, error y despegue) sintetizados por `tools/pixelart/sfx.py` (propios).

Música original, compuesta y sintetizada por `tools/audio/music.py` (bucles sin corte, OGG):

| Pista | Dónde suena | Carácter |
|-------|-------------|----------|
| «Órbita silenciosa» (`space`) | Vuelo espacial | 72 BPM, re menor: pads lentos, arpegio con eco, campanas lejanas. Inmensidad y calma |
| «Paso a paso» (`mission`) | Superficies (Tierra, Luna, Marte) | 112 BPM, la menor: melodía de pulso tipo chiptune, bajo triangular y batería. Aventura |
| «La Semilla» (`title`) | Menú y cinemáticas | 66 BPM, mi menor: piano y cuerdas. Melancolía con esperanza |

| «Neón de cantina» (`cantina`) | Bares y tiendas | 100 BPM, do mayor: piano eléctrico, bajo caminante, vibráfono. Acogedora |

Al entrar en HAL, la música pasa por un filtro paso bajo. Las transiciones nunca solapan dos pistas: la actual se apaga y después entra la nueva. El volumen se ajusta en la pestaña Sistema.

## 9. Fuera de alcance (por ahora)

Combate, economía compleja (comercio entre jugadores, venta de objetos, precios variables), inventario con usos o crafteo, cuentas de usuario y capítulos 4–8 jugables.
