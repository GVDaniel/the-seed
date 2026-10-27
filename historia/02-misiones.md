# Misiones

Datos jugables: `game/assets/data/missions/*.json`.

## Índice

| ID | Título | Capítulo | Requiere |
|----|--------|----------|----------|
| `last_seed` | La última semilla | 1 | — (auto_start) |
| `signal_from_moon` | Señal desde la Luna | 2 | `last_seed` |
| `ice_of_shackleton` | Hielo de Shackleton | 2 | `signal_from_moon` |
| `red_garden` | Un jardín rojo | 3 | `ice_of_shackleton` |
| `methane_heart` | Corazón de metano | 4 | `red_garden` |
| `side_ice_core` | Hielo bajo el polvo *(secundaria)* | 4 | `red_garden` |
| `side_co2` | El aire que sobra *(secundaria)* | 4 | `red_garden` |
| `side_catalyst` | La roca que cayó del cielo *(secundaria)* | 4 | `red_garden` |

**Principal vs. secundaria** (`kind`): solo puede haber una principal activa; las secundarias se aceptan cuando quieras y corren en paralelo. Dan materiales, XP y créditos, y a veces la principal las necesita (`have_items`).

---

## 1. La última semilla (`last_seed`)

**Resumen:** Lucía guarda La Semilla. Antes de llevársela, Andrés debe entender por qué enfermó la Tierra.

**NPC de inicio:** Lucía (Bóveda Semillera, Tierra).

### Objetivos

1. `talk_lucia` — Hablar con Lucía en la Bóveda.
2. `scan_dead_plant` — Escanear la planta marchita.
3. `scan_air` — Medir el aire (sensor al oeste).
4. `report_lucia` — Contarle a Lucía lo aprendido.
5. `collect_seed` — Recoger La Semilla.
6. `launch_program` — Programar la secuencia de despegue (lab `launch_sequence`).
7. `takeoff` — Despegar con ASTRA.

### Beats de diálogo

- Lucía pide escanear planta y aire para que Andrés **vea los datos**, no solo escuche.
- Andrés resume: sin plantas sanas → menos fotosíntesis → más CO₂.
- Lucía explica la bóveda (frío ~−18 °C, inspirada en Svalbard) y entrega el cofre.
- HAL presenta el escáner (tecla F).

**Recompensa:** 80 XP.  
**Mensaje fin:** Capítulo 1 completado.

---

## 2. Señal desde la Luna (`signal_from_moon`)

**Resumen:** Aurora recibió datos incompletos de una sonda lunar. Hay que recuperar la señal y devolverla.

**NPC de inicio:** Dra. Vega (Estación Aurora). Condición: cerca de la estación + hablar (T).

### Objetivos

1. `reach_moon_sector` — Llegar a la zona de la Luna.
2. `scan_probe_signal` — Escanear el faro de la sonda (`lunar_probe_signal`).
3. `report_to_station` — Volver a Aurora y entregar a Vega.

### Beats de diálogo

- Vega da la bienvenida con La Semilla a bordo.
- Para llegar lejos hace falta **combustible**; la sonda puede ayudar.
- Sin atmósfera densa, la radio en la Luna viaja “limpia”, pero el terreno tapa antenas.
- Al reportar: hay **hielo de agua** en Shackleton; H₂O → H₂ + O₂; permiso de aterrizar; buscar a **Kai**.

**Recompensa:** 60 XP + entrada `lunar_signal_analysis`.  
**Mensaje fin:** Aterrizaje lunar autorizado.

---

## 3. Hielo de Shackleton (`ice_of_shackleton`)

**Resumen:** En el fondo oscuro de un cráter lunar hay hielo de agua: el combustible para seguir el viaje.

**NPC de inicio:** Kai (base Shackleton, Luna).

### Objetivos

1. `scan_ice` — Escanear el hielo (`moon_ice_crater`).
2. `drill_program` — Programar el taladro (lab `ice_drill`).
3. `deliver_kai` — Entregar el hielo a Kai.

### Beats de diálogo

- Kai: el fondo del cráter está a más de 200 °C bajo cero (sombra permanente).
- Hay que escanear y programar la sonda de perforación.
- Electrólisis / ISRU → tanque lleno.
- HAL desbloquea Marte / Jezero; **Osei** espera.

**Recompensa:** 80 XP + entrada `lunar_water_fuel`.  
**Mensaje fin:** Aterrizaje en Marte autorizado.

---

## 4. Un jardín rojo (`red_garden`)

**Resumen:** En el cráter Jezero, Andrés intentará que un brote de La Semilla crezca fuera de la Tierra.

**NPC de inicio:** Cmte. Amara Osei (base Jezero, Marte).  
**Evento al completar:** `ending_teaser`.

### Objetivos

1. `scan_delta` — Estudiar el delta (`mars_delta`).
2. `scan_rover` — Escanear el rover (`mars_rover`).
3. `sample_program` — Programar sonda de muestras (lab `delta_samples`).
4. `plant_seed` — Plantar en el invernadero (`mars_greenhouse`).
5. `talk_osei` — Hablar con Osei.

### Beats de diálogo

- Osei: Jezero tuvo un lago hace ~3 500 millones de años; Marte es rojo por óxido de hierro.
- Tras plantar: el brote solo vive **bajo cúpula**. Aire casi todo CO₂, presión &lt;1 % de la Tierra; sin campo magnético global fuerte.
- Marte = parada y laboratorio, no hogar abierto.
- Vega: rumbo a TRAPPIST-1e (~40 años luz).

**Recompensa:** 120 XP + entrada `trappist1e`.  
**Mensaje fin:** Capítulo 3 completado. Al terminar, HAL y Osei señalan a Bruno (el final ya no llega aquí).

---

## 5. Corazón de metano (`methane_heart`)

**Resumen:** ASTRA es demasiado lenta para Júpiter. En el Barranco de Óxido hay un motor de metano… y un robot de los Antihumanistas que no quiere que lo tengas.

**NPC de inicio:** Bruno (Taller de Bruno, `mars_garage`).

### Objetivos
1. `win_sentinel` — vencer al **Centinela AH-7** (`win_battle: sentinel_ah7`). Primer combate, tutorial.
2. `take_engine` — recoger el **motor de metano** junto al carguero.
3. `install_engine` — usar el **banco de trabajo** del Taller (`effects.install_engine`): ASTRA cambia de motor y queda con el tanque vacío.
4. `gather_ingredients` — tener **hielo, CO₂ y níquel** (`have_items`) → misiones secundarias.
5. `distill_fuel` — usar el **destilador** (Sabatier): tanque lleno, casco reparado, ingredientes consumidos.
6. `talk_osei` — contárselo a Osei; mensaje de Vega: rumbo a Júpiter y Europa.

### Beats de diálogo
- Bruno: el CX-50 *«es más viejo que mi abuela»*; carguero de MarsCorp; un robot antihumanista patrulla.
- HAL presenta a los **Antihumanistas**: humanos y máquinas que sabotean todo lo que ayude a empezar de nuevo.
- Tras la victoria: AH-7 *apagado, no roto*; chip de órdenes. *«Un robot no es bueno ni malo, hace lo que dice su programa.»*
- Osei: el chip confirma que quieren detener a ASTRA. Vega: Europa esconde un océano bajo el hielo.

**Recompensa:** 150 XP + 80 créditos + ficha `sabatier_methane`. Al completar → `ending_teaser`.

---

## 6. Hielo bajo el polvo (`side_ice_core`) · secundaria

**NPC:** Yusuf, maestro. Quiere enseñar a sus alumnos que en Marte hay agua escondida.

1. Escanear la perforadora (`mars_buried_ice`, como el hielo que encontró *Phoenix* en 2008).
2. Recoger el **testigo de hielo** (`mars_ice_core`).
3. Volver con Yusuf.

**Recompensa:** 40 XP + 30 créditos.

## 7. El aire que sobra (`side_co2`) · secundaria

**NPC:** Nia, alumna nacida en Marte. Su compresor de ciencias no arranca.

1. Encender el **compresor de CO₂** (`co2_compressor`): entrega la **bombona de CO₂** (el aire de Marte es ~95 % CO₂; MOXIE fabricó oxígeno con él).
2. Contárselo a Nia (en la Cantina Polvo Rojo).

**Recompensa:** 35 XP + 25 créditos.

## 8. La roca que cayó del cielo (`side_catalyst`) · secundaria

**NPC:** Ada Okonkwo, geóloga. Encontró un meteorito de hierro y níquel vigilado por dos drones antihumanistas.

1. Escanear el **meteorito** (`mars_iron_meteorite`, como *Heat Shield Rock*, el que halló *Opportunity*).
2. Desactivar a los **drones vigía** (`win_battle: drones_meteorite`; débiles a la luz).
3. Recoger las **virutas de níquel** (catalizador de Sabatier).
4. Volver con Ada.

**Recompensa:** 50 XP + 30 créditos.

---

## Notas de diseño de misiones

- Estados: `available` → `active` → `completed` (`MissionLog`).
- Objetivos en **orden**; cada uno solo una vez.
- Diálogos **lineales** (sin árbol complejo).
- Orden al hablar con un NPC: objetivo `talk_to` de cualquier misión activa → oferta (principal si no hay otra activa; secundarias siempre) → recordatorio → líneas `after` → idle.
- Combates solo como objetivo `win_battle`; retirarse o perder no completa ni castiga. La recompensa del encuentro se da una vez.
- Objetivos pueden tener `effects` (`install_engine`, `refuel`, `repair`, `set_flag`, `consume_items`).
- Ciencia real + simplificaciones marcadas en destinations / SCIENCE_REFERENCES.
- El mapa arcade **no** representa distancias reales del sistema solar.
