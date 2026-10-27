# Personajes

Datos: `game/assets/data/characters/*.json`.

## Tripulación / arco principal

### Andrés (`andres`)
- **Rol:** Cadete piloto · ~13 años · protagonista.
- **Rasgo:** Curiosidad e impaciencia; aprende mirando datos.
- **Cita:** *«Abuela, te prometo que La Semilla llegará a un lugar seguro.»*

### Abuela Lucía (`lucia`)
- **Rol:** Guardiana de la Bóveda Semillera (Tierra).
- **Rasgo:** Botánica; recuerda cuando había bosques verdes.
- **Citas:** *«Una semilla es una planta dormida…»* · *«Cuida a HAL…»*
- **Misión:** `last_seed`.

### Dra. Alexandra Vega (`vega`)
- **Rol:** Astrobióloga, jefa de la Estación Aurora.
- **Rasgo:** Sigue señales y enseña a preguntar a los datos.
- **Cita:** *«Una buena científica pregunta siempre: ¿qué dicen los datos?»*
- **Misión:** `signal_from_moon`.

### HAL (`hal`)
- **Rol:** IA de ASTRA (serie HAL 9000, tono amable).
- **Rasgo:** Calma, protocolo, humor seco; “casi” nunca se equivoca.
- **Citas:** *«Todos mis circuitos funcionan perfectamente…»* · *«Ningún ordenador de la serie HAL 9000 ha cometido nunca un error. Bueno… casi nunca.»*
- **Función:** Tutor de controles, bloqueos de historia, compañero en cutscenes.

### Kai Tanaka (`kai`)
- **Rol:** Ingeniero de la base Shackleton (Luna) · ~16 años.
- **Rasgo:** Inventos, frío extremo, bromas sobre sondas.
- **Cita:** *«En la Luna pesas como una sexta parte…»*
- **Misión:** `ice_of_shackleton`.

### Cmte. Amara Osei (`osei`)
- **Rol:** Comandante de la base Jezero (Marte); antes geóloga.
- **Rasgo:** Firme; protege al equipo; lee historia en las rocas.
- **Cita:** *«Antes fui geóloga. Las rocas de Marte cuentan la historia de un planeta que tuvo agua.»*
- **Misión:** `red_garden`.

---

## NPCs de ambientación

No tienen misiones propias (por ahora). Dan color local e idle dialogue.

### Tierra
| ID | Nombre | Rol |
|----|--------|-----|
| `ramiro` | Don Ramiro | Tendero *El Último Brote* |
| `mateo` | Mateo | Vecino del Barrio Semilla · 10 años |
| `amaru` | Amaru Quispe | Técnica de la cúpula de aire |
| `zoe` | Zoe «Chispa» | Chatarrera |

### Luna
| ID | Nombre | Rol |
|----|--------|-----|
| `lupe` | Lupe | Dueña del Bar Cráter (batidos/jugos) |
| `ingrid` | Ingrid Larsen | Mecánica, Repuestos Regolito |
| `tomas` | Tomás | Minero de hielo |
| `amina` | Dra. Amina Diallo | Astrónoma del observatorio lunar |

### Marte
| ID | Nombre | Rol |
|----|--------|-----|
| `chen` | Chen Wei | Comerciante del Mercado Jezero |
| `rosa` | Rosa | Dueña de la Cantina Polvo Rojo |
| `yusuf` | Yusuf | Maestro de la escuela Jezero |
| `nia` | Nia | Alumna; nació en Marte. Ofrece «El aire que sobra» (compresor de CO₂). Vive en la Cantina |
| `bruno` | Bruno | Mecánico de rovers y naves; dueño del **Taller** (`mars_garage`). Ofrece «Corazón de metano» |
| `ada` | Ada Okonkwo | Geóloga de la colonia, en el borde del Barranco de Óxido. Ofrece «La roca que cayó del cielo». *«Las rocas son libros.»* |

Yusuf, además, ofrece «Hielo bajo el polvo» (perforadora junto al barranco).

## Máquinas antihumanistas (enemigos)

Solo máquinas. Se **desactivan** (sprite apagado), nunca se destruyen. Datos: `game/assets/data/combat/encounters/`.

| ID | Nombre | Dónde | Rasgos |
|----|--------|-------|--------|
| `sentinel_ah7` | Centinela AH-7 | Barranco de Óxido, junto al carguero | Robot de chatarra, débil a la **electricidad**. Cada 3 turnos carga el *Martillo sísmico* (cerraduras: electricidad + impacto). Frases: *«ORDEN ANTIHUMANISTA N.º 1: NINGUNA NAVE SALE DE MARTE.»* Suelta el **chip de órdenes** |
| `drones_meteorite` | Drones vigía AH-D1 y AH-D2 | Meteorito de hierro | Dos drones pequeños, débiles a la **luz** (láser de HAL). Uno carga un *Zumbido* (cerraduras: luz + impacto) |

## Facciones / marcas del mundo

- **AgroNet** — monopolio de recursos en Tierra (comida, agua, aire).
- **MarsCorp** — mencionada en idle de Marte; su carguero estrellado guarda el motor de metano; tiene el surtidor de Marte.
- **Antihumanistas** — clan de **humanos y máquinas** que cree que la Tierra estaría mejor sin la humanidad. Sabotean invernaderos, naves y estaciones; quieren impedir que La Semilla salga del sistema solar. Emblema: círculo rojo con una X sobre una silueta humana (pintadas holográficas en Tierra, Luna y Marte). Contrapunto educativo: es cierto que dañamos el clima, pero también podemos repararlo. Sus líderes humanos aún no aparecen.

## Plantilla para nuevos personajes

Al añadir alguien, completa en esta carpeta **y** en `characters/<id>.json`:

```md
### Nombre (`id`)
- Rol / edad / hogar:
- Función en la trama:
- 1–2 citas:
- Misión o solo ambientación:
```
