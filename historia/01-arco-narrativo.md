# Arco narrativo

## Capítulos (canon demo)

| # | Título | Subtítulo | Estado |
|---|--------|-----------|--------|
| 1 | La Tierra Marchita | Año 2187. Las plantas se apagan; una semilla puede encenderlas de nuevo. | Jugable |
| 2 | Agua en la oscuridad | Una señal perdida y el hielo escondido en los cráteres de la Luna. | Jugable |
| 3 | Un jardín rojo | Marte guarda la memoria de un río. ¿Puede guardar también un brote? | Jugable |
| 4 | Corazón de metano | ASTRA necesita un motor nuevo para llegar a Júpiter… y los Antihumanistas no quieren que despegue. | Jugable (parte 1) |
| 5 | Continuará… | Rumbo a Júpiter y su luna Europa. | Teaser |

Fuente: `game/assets/data/story/chapters.json`.

## Cadena de progreso

```
last_seed  →  signal_from_moon  →  ice_of_shackleton  →  red_garden  →  methane_heart  →  (teaser)
   Cap.1            Cap.2 (1/2)           Cap.2 (2/2)           Cap.3        Cap.4 (parte 1)
                                                                              ├─ side_ice_core   (Yusuf)
                                                                              ├─ side_co2        (Nia)
                                                                              └─ side_catalyst   (Ada)
```

Las tres **misiones secundarias** se desbloquean con `red_garden` y corren en paralelo con la principal. `methane_heart` espera sus tres ingredientes en el objetivo `gather_ingredients` (`have_items`).

Bloqueos de gameplay (StoryDirector):

- No despegar de Tierra hasta terminar objetivos de `last_seed`.
- No aterrizar en Luna hasta completar `signal_from_moon`.
- No aterrizar en Marte hasta completar `ice_of_shackleton`.
- Solo se combate cuando una misión lo pide (`can_battle`).
- No despegar de Marte con el motor de metano y el tanque vacío (hay que destilar).

## Cinemática de intro

1. Tierra 2187: algo va mal.
2. La Marchitez: cúpulas, lluvia ácida, neón; AgroNet.
3. Bóveda Semillera; Lucía y La Semilla.
4. Vega detectó un mundo lejano; Andrés + HAL parten.  
   HAL: *«Buenas noches, Andrés… ¿Empezamos?»*

## Cinemática de cierre (demo)

Tras completar `methane_heart` (`ending_teaser`; antes llegaba con `red_garden`):

1. Un brote crece en Marte **bajo cúpula**. Lección: no hay planeta B fácil. ASTRA tiene un corazón nuevo: metano hecho con aire, hielo y una roca de Marte.
2. Rumbo a **TRAPPIST-1** (~40 años luz). TRAPPIST-1e en zona habitable. Los Antihumanistas leen el mismo mapa estelar.  
   HAL: *«Fin del demo. Próxima parada: Júpiter y su luna Europa… ¡continuará!»*

Fuente: `game/assets/data/story/cutscenes.json`.

## Resumen por acto (para escritores)

### Acto I — Tierra
Andrés entiende la crisis (planta muerta + aire), recibe La Semilla de Lucía, programa el despegue y parte en ASTRA.

### Acto II — Luna / Aurora
Vega necesita más que esperanza: combustible. Una sonda lunar perdida lleva a Shackleton, hielo de agua y electrólisis → tanques listos para Marte.

### Acto III — Marte
En Jezero, Osei guía el estudio del delta y un rover. Andrés planta un brote: solo sobrevive bajo cúpula. Marte es laboratorio, no escape. Vega apunta a TRAPPIST-1e.

### Acto IV · parte 1 — Corazón de metano (Marte) · jugable
Osei ha visto el brote, pero Bruno ve otra cosa: ASTRA vuela con un motor químico de 2150, lento y gastón. Con él no se llega a Júpiter. En el **Barranco de Óxido** se estrelló un carguero de MarsCorp con un motor de metano… custodiado por el **Centinela AH-7**, un robot de los **Antihumanistas**.

Andrés y HAL tienen su **primera batalla** (tutorial: pulsar a tiempo, debilidad a la electricidad, cerraduras del Martillo sísmico). AH-7 queda apagado —no roto— y suelta un **chip de órdenes**: alguien le programó para que ninguna nave saliera de Marte.

Bruno instala el motor, pero llega vacío: hay que **fabricar metano** con la reacción de Sabatier. La colonia ayuda —misiones secundarias—: Yusuf aporta **hielo enterrado**, Nia **CO₂** de su compresor y Ada **níquel** de un meteorito vigilado por drones (segunda batalla). El destilador ruge, Osei lo celebra y el chip confirma la amenaza. Vega: *«Con ese motor ya podéis llegar a Júpiter»*.

Lección del acto: *los recursos de un planeta se aprovechan con ciencia y con ayuda de la comunidad; y un robot hace lo que dice su programa: lo importante es quién lo escribe.*

### Acto IV · parte 2 — Gigante de tormentas (Júpiter / Europa) · borrador
ASTRA aún no está lista para el salto interestelar: primero debe acercarse a **Júpiter**, el gigante de tormentas, y establecer una **base semipermanente en Europa**, su luna de hielo.

Europa es un laboratorio perfecto para la historia: un océano bajo una corteza helada, lejos del Sol, bajo la radiación del planeta. Antes de aterrizar allí, Andrés debe **preparar la nave y la tripulación** —mejoras de escudo y potencia, reservas de agua y alimento— porque en el sistema joviano no hay “tienda de barrio”: cada recurso se gana con ciencia, escaneos y programas de sonda.

Lección del acto: *llegar lejos no es solo apuntar al mapa; es sobrevivir al camino.* El hielo de Europa no es un tesoro para escapar de la Tierra, sino un paso: entender un mundo de agua en la oscuridad… y dejar ASTRA lista para lo que viene (Titán, el borde del sistema, TRAPPIST).
