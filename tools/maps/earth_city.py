"""Barrio Semilla (Tierra, 2187): ciudad marchita, de noche, con lluvia ácida y neón.

Plano (norte → sur):
  y 1–8    Fila norte: casas del barrio (la de Andrés), Bóveda Semillera al centro, bloques al este.
  y 9–12   Paseo de la Semilla (peatonal) con la plaza de la Bóveda.
  y 13–25  Parque Marchito y tiendas con fachada a la avenida (oeste) · puerto espacial de ASTRA
           (centro) · Chatarrería de Chispa (este).
  y 26–34  Avenida Neón: 4 carriles de aerovehículos y tranvía maglev en el centro.
  y 35–43  Mercado nocturno, paradas y patios junto a la avenida; casas con la fachada a la Calle Sur.
  y 44–47  Calle Sur.
  Calles verticales x 19–25 y x 40–46 cosen el barrio de norte a sur.
Los edificios son sólidos en toda su silueta (tejado + fachada): ocupan d + wall/16 filas.
"""
from city import City, L, light

PINK, CYAN, GOLD, GREEN, WARM, RED = "#ff3ea5", "#3de7c9", "#f4d35e", "#7dff9a", "#ffb070", "#e0283c"
W, H = 64, 49
TRAFFIC = {"kinds": ["hover_taxi", "hover_van", "hover_taxi", "hover_bus"], "interval": [2.2, 5.5],
           "speed": 70, "altitude": 8, "two_way": False}
SIDE_TRAFFIC = {"kinds": ["hover_taxi", "hover_van", "delivery_drone"], "interval": [5.0, 11.0],
                "speed": 55, "altitude": 8, "two_way": False}

BARKS_PASEO = [
    "Mi abuela dice que aquí antes había un parque con 200 árboles.",
    "¿Has visto? ¡Están regando el huerto con agua de lluvia filtrada!",
    "La lluvia ácida se forma con el humo de quemar carbón y petróleo.",
    "Hoy la cúpula de aire funciona. ¡Qué alivio!",
    "Dicen que en la Luna hay hielo en los cráteres que nunca ven el Sol.",
]
BARKS_AVENUE = [
    "El tranvía maglev flota sobre imanes: casi no hace ruido.",
    "AgroNet ha vuelto a subir el precio del aire embotellado…",
    "¡Cuidado con los charcos, que pican!",
    "Mi hermana trabaja en la cúpula de aire. Dice que las algas producen oxígeno.",
    "¿Ese es el chico de la nave? ¡Suerte, Andrés!",
    "Los aerotaxis funcionan con baterías que se cargan con luz solar.",
]
BARKS_SOUTH = [
    "Las plantas del balcón crecen mejor con luz de lámparas LED.",
    "¿Sabías que un árbol puede dar oxígeno a dos personas?",
    "Esta noche se ve Marte: es el punto rojizo sobre la torre.",
]
BARKS_MARKET = [
    "¡Batidos de alga espirulina! ¡Tienen mucha proteína!",
    "Se reparan visores, radios y robots. ¡Precio justo!",
    "Semillas de verdad no quedan… solo esquejes de laboratorio.",
]


def build():
    c = City("earth", W, H, seed=2187)
    c.border("cliff")
    _ground(c)
    _north_row(c)
    _park(c)
    _spaceport(c)
    _scrapyard(c)
    _avenue_front(c)
    _south_row(c)
    _street_furniture(c)
    _life(c)
    starts = [(4, 9)]
    targets = [(e.get("id", e.get("sprite")), (int(e["pos"][0]), int(e["pos"][1])))
               for e in c.entities if e["type"] in ("npc", "scan", "item", "terminal", "ship", "door", "sign", "service")]
    c.check_paths(starts, targets)
    legend, ground, objects = c.legend_and_rows()
    return {
        "id": "earth", "display_name": "Barrio Semilla · Tierra", "tileset": "city_earth",
        "void_color": "#141020", "ambient": "#6e6c96", "weather": "rain", "dark": True, "music": "mission",
        "legend": legend, "ground": ground, "objects": objects, "entities": c.entities,
        "ambient_life": c.ambient(),
        "arrival_lines": [
            L("hal", "Buenos días, Andrés. Sistemas de HAL en línea. Calidad del aire: mala. Ánimo: ¡bueno!"),
            L("andres", "HAL, hoy es el día. La abuela Lucía nos espera en la Bóveda Semillera."),
            L("hal", "Sigue la flecha dorada. Muévete con WASD y habla con la gente pulsando E."),
            L("hal", "Llovizna ácida de nivel bajo. Los aerotaxis vuelan bajo por la Avenida Neón: mejor cruzar por los pasos de peatones."),
        ],
    }, c


# ---------------------------------------------------------------- suelo y calles
def _ground(c):
    c.noise_patches("grass", 1, 1, W - 2, H - 2, 0.35, 4.0)
    c.noise_patches("rough", 1, 1, W - 2, H - 2, 0.12, 3.0, over=("soil",))
    # Paseo de la Semilla (peatonal) y plaza de la Bóveda
    c.street_h(11, 1, W - 2, lanes=0, walk=2)          # filas 9–12
    c.fill(26, 9, 35, 12, "plaza")
    c.set(30, 11, "plaza_center")
    c.set(31, 11, "plaza_center")
    # Avenida Neón con tranvía
    c.street_h(28, 1, W - 2, lanes=5, walk=2, rail=True, traffic=TRAFFIC)
    # Calle Sur
    c.street_h(45, 1, W - 2, lanes=2, walk=1, line=False)
    c.movers.append(dict(SIDE_TRAFFIC, path=[[W + 3, 45], [-3, 45]]))
    c.movers.append(dict(SIDE_TRAFFIC, path=[[-3, 46], [W + 3, 46]]))
    # Calles verticales (de la avenida a la Calle Sur, y peatonales hasta el paseo)
    for x in (21, 42):
        c.street_v(x, 13, 44, lanes=3, walk=2)
        c.movers.append(dict(SIDE_TRAFFIC, path=[[x, 26], [x, 44]]))
        c.movers.append(dict(SIDE_TRAFFIC, path=[[x + 2, 44], [x + 2, 26]]))
    # Del paseo a la avenida las verticales son peatonales (sin calzada).
    for x in (21, 42):
        c.fill(x, 13, x + 2, 25, "pave")
    c.crosswalks()
    c.curbs()
    # Charcas, alcantarillas
    for (x, y) in [(10, 11), (52, 10), (20, 33), (44, 36), (6, 46), (58, 46)]:
        c.set(x, y, "grate")


# ---------------------------------------------------------------- fila norte
def _north_row(c):
    c.add({"type": "spawn", "id": "start", "pos": [3.5, 9]})
    c.row(2, 8, ["bld_e_home_andres", "bld_e_house_3a", "bld_e_house_3b", "bld_e_house_4a"], gap=1,
          lights={0: light(WARM, (0, -20), 2.2, 0.7)})
    # Huerto comunitario entre las casas y la Bóveda
    c.fill(20, 5, 24, 8, "soil_bed")
    c.prop("planter_hydro", [20, 8], lit=light(GREEN, (0, -10), 1.0, 0.6))
    c.prop("planter_dead", [22, 8])
    c.prop("planter_hydro", [24, 8], lit=light(GREEN, (0, -10), 1.0, 0.6))
    c.prop("barrel_water", [21, 6])
    c.prop("solar_tree", [23, 6], lit=light(CYAN, (0, -40), 1.2, 0.5))
    # Bóveda Semillera y su plaza
    c.building("bld_e_vault", 30.5, 8, lit=light(GOLD, (0, -24), 3.0, 0.8))
    c.add({"type": "scan", "id": "seed_vault", "pos": [30.5, 9], "radius": 30}, reserve=1)
    c.add({"type": "npc", "id": "lucia", "pos": [28, 10], "facing": "down"}, reserve=1)
    c.add({"type": "item", "id": "the_seed", "pos": [33, 10], "sprite": "seed_chest", "prompt": "Tomar La Semilla",
           "locked_text": "Es el cofre de La Semilla. La abuela Lucía te lo dará cuando llegue el momento.",
           "collect_lines": [L("andres", "La Semilla… pesa poco, pero lleva el futuro de todo un planeta."),
                             L("hal", "Cofre asegurado en la mochila. Siguiente paso: la terminal del puerto espacial, al sur del paseo.")]},
          reserve=1)
    c.add({"type": "light", "id": "light_vault", "pos": [30.5, 10], "light": light(GOLD, (0, -10), 3.2, 0.8)})
    # Bloques del este
    x = c.row(37, 8, ["bld_e_kiosk_2"], gap=1)
    c.row(x + 1, 8, ["bld_e_apt_5a", "bld_e_house_4a", "bld_e_apt_5b", "bld_e_tower_6"], gap=1, doors={
        1: {"id": "house_okafor", "prompt": "Llamar a la puerta",
            "lines": [L("hal", "Casa de la familia Okafor."),
                      L("hal", "Nota en la puerta: «Turno de noche en la cúpula de aire. Volvemos al amanecer».")]},
        2: {"id": "house_lindqvist", "prompt": "Llamar a la puerta",
            "lines": [L("hal", "Casa de la familia Lindqvist."),
                      L("hal", "Se oye una radio: «…AgroNet anuncia otra subida del precio del aire embotellado…».")]},
    }, lights={0: light(PINK, (0, -50), 2.0, 0.6, True), 2: light(CYAN, (0, -50), 2.0, 0.6),
               3: light(GREEN, (0, -100), 3.0, 0.7, True)})


# ---------------------------------------------------------------- parque
def _park(c):
    # x 1–17, y 13–19: caminos de baldosa en cruz y una fuente seca en el centro
    c.fill(1, 13, 17, 19, "grass")
    c.noise_patches("soil", 1, 13, 17, 19, 0.4, 2.5, over=("grass",))
    c.fill(2, 16, 16, 16, "pave")
    c.fill(9, 13, 10, 19, "pave")
    c.fill(7, 15, 12, 18, "plaza")
    c.prop("fountain_dry", [9.5, 17], solid=(2, 2), lit=light(CYAN, (0, -12), 1.6, 0.5))
    c.add({"type": "sign", "id": "sign_town", "pos": [11, 13], "sprite": "sign_arrow", "solid": [1, 1],
           "prompt": "Leer el cartel",
           "lines": [L("hal", "«Parque Marchito. Barrio Semilla. Población: 312. Cúpula de aire más cercana: 4 km.»"),
                     L("hal", "Antes de La Marchitez, este parque tenía 200 árboles. Hoy quedan troncos secos.")]}, reserve=1)
    # Invernadero comunitario y la planta muerta que hay que escanear
    c.building("bld_e_greenhouse_4", 3.5, 15, lit=light(GREEN, (0, -14), 2.0, 0.5, True))
    c.add({"type": "scan", "id": "earth_dead_plant", "pos": [6, 17], "sprite": "plant_dead"}, reserve=1)
    # Sensor de aire del barrio con su panel
    c.add({"type": "scan", "id": "earth_air_sensor", "pos": [15, 14], "sprite": "sensor", "solid": [1, 1]}, reserve=1)
    c.add({"type": "light", "id": "light_sensor", "pos": [15, 14], "light": light(CYAN, (0, -8), 1.2, 0.7)})
    c.prop("solar_panel", [16, 13], force=True)
    c.add({"type": "npc", "id": "amaru", "pos": [4, 18], "facing": "right", "wander": 1.5}, reserve=1)
    for pos in ([7, 14], [12, 14], [7, 19], [12, 19]):
        c.prop("bench_holo", pos, solid=None)
    for pos in ([2, 19], [15, 18], [16, 19], [13, 13], [7, 13], [14, 17]):
        c.prop("tree_dead_big", pos)
    c.scatter(["planter_dead"], (1, 13, 17, 19), 2, on=("grass", "soil"))
    c.scatter(["decal_leaves"], (1, 13, 17, 19), 5, z=-1)


# ---------------------------------------------------------------- puerto espacial
def _spaceport(c):
    # x 27–38, y 14–24: pista vallada con la entrada desde la avenida
    c.fill(27, 14, 38, 24, "pad_0")
    for x in range(27, 39):
        c.set(x, 14, "pad_mark")
        c.set(x, 24, "pad_mark")
    c.fill(32, 15, 33, 23, "pad_line")
    c.fill(31, 25, 34, 25, "pave")
    c.solid_rect(26, 13, 39, 13, "wall_low_h")
    c.solid_rect(26, 14, 26, 25, "hedge_v")
    c.solid_rect(39, 14, 39, 25, "hedge_v")
    for x in list(range(27, 31)) + list(range(35, 39)):
        c.solid_tile(x, 25, "wall_low_h")
    c.add({"type": "prop", "sprite": "launch_pad", "pos": [32.5, 20], "z": -1})
    c.add({"type": "ship", "id": "astra", "pos": [32.5, 19], "prompt": "Subir a ASTRA y despegar", "radius": 34},
          reserve=2)
    c.add({"type": "spawn", "id": "ship", "pos": [32.5, 22]})
    c.add({"type": "terminal", "id": "launch_terminal", "challenge_id": "launch_sequence", "pos": [28, 22], "solid": [1, 1],
           "locked_text": "La terminal de despegue necesita que primero tengas La Semilla."}, reserve=1)
    c.add({"type": "light", "id": "light_terminal", "pos": [28, 22], "light": light(CYAN, (0, -10), 1.5, 0.9)})
    c.add(_service("service_earth", [37, 22], "AgroNet", 0.5), reserve=1)
    c.add({"type": "light", "id": "light_pad", "pos": [32.5, 18], "light": light(CYAN, (0, 0), 4.0, 0.8)})
    c.prop("antenna_small", [37, 16], lit=light(RED, (0, -30), 0.8, 0.9, True))
    c.prop("crate_stack", [28, 16])
    c.prop("barrel_water", [29, 16])
    c.prop("crate_stack", [36, 16])
    for pos in ([27, 23], [38, 23], [27, 15], [38, 15]):
        c.prop("bollard_light", pos, lit=light(GOLD, (0, -6), 0.8, 0.8, True))


# ---------------------------------------------------------------- chatarrería
def _scrapyard(c):
    # x 48–61, y 14–24 vallada; entrada por el oeste (calle vertical)
    c.fill(48, 14, 61, 24, "soil")
    c.noise_patches("rough", 48, 14, 61, 24, 0.5, 2.0, over=("soil",))
    c.solid_rect(47, 13, 62, 13, "wall_low_h")
    c.solid_rect(62, 13, 62, 25, "hedge_v")
    c.solid_rect(47, 25, 62, 25, "wall_low_h")
    c.solid_rect(47, 13, 47, 17, "hedge_v")
    c.solid_rect(47, 21, 47, 25, "hedge_v")
    c.add({"type": "sign", "id": "sign_scrapyard", "pos": [46, 18], "sprite": "sign_arrow", "solid": [1, 1],
           "prompt": "Leer el cartel", "light": light(PINK, (0, -16), 1.2, 0.8, True),
           "lines": [L("hal", "Cartel pintado a mano: «Chatarrería de Chispa. Si se rompe, se arregla»."),
                     L("hal", "Reutilizar piezas ahorra energía y materiales: es lo contrario de tirar.")]}, reserve=1)
    c.add({"type": "npc", "id": "zoe", "pos": [53, 19], "facing": "left", "wander": 1.5}, reserve=1)
    c.prop("scrap_pile", [57.5, 16], solid=(2, 1))
    c.prop("scrap_pile", [59.5, 20], solid=(2, 1))
    c.prop("scrap_pile", [55.5, 23], solid=(2, 1))
    c.prop("scrap_pile", [50.5, 23], solid=(2, 1))
    c.prop("crate_stack", [50, 15])
    c.prop("barrel_rust", [51, 15])
    c.prop("barrel_toxic", [60, 15], lit=light(GREEN, (0, -8), 0.8, 0.6))
    c.prop("trash_robot_dock", [49, 19], lit=light(CYAN, (0, -10), 0.8, 0.6))
    c.prop("vendor_cart", [57, 19], solid=None)
    c.scatter(["decal_oil", "decal_crack"], (48, 14, 61, 24), 5, z=-1)


# ---------------------------------------------------------------- frente de la avenida (norte)
def _avenue_front(c):
    # Tiendas y bloques con la fachada hacia la Avenida Neón (fondo y = 22), oeste y este
    c.row(1, 25, ["bld_e_apt_4b", "bld_e_ruin_4", "bld_e_shop", "bld_e_kiosk_2", "bld_e_house_3a"], gap=0, doors={
        2: {"id": "door_earth_shop", "label": "El Último Brote", "prompt": "Entrar en El Último Brote",
             "target": "earth_shop", "spawn": "entrance"}}, lights={2: light(GREEN, (0, -40), 2.4, 0.8),
                                                                0: light(PINK, (0, -50), 2.0, 0.6, True)})
    shop = next(e for e in c.entities if e.get("id") == "door_earth_shop")
    c.add({"type": "spawn", "id": "shop_door", "pos": [shop["pos"][0], 26]})


# ---------------------------------------------------------------- fila sur
def _south_row(c):
    def house(id, family, note):
        return {"id": id, "prompt": "Llamar a la puerta",
                "lines": [L("hal", f"Casa de la familia {family}."), L("hal", note)]}

    c.row(2, 43, ["bld_e_house_3a", "bld_e_house_3b", "bld_e_ruin_4", "bld_e_apt_4a"], gap=1, doors={
        0: house("house_quispe", "Quispe", "Amaru vive aquí. En la ventana hay una planta de plástico… y una de verdad, muy pequeña."),
        1: house("house_mateo", "de Mateo", "Dibujo pegado en el cristal: un cohete, una estrella y la palabra «ANDRÉS»."),
    })
    c.row(26, 43, ["bld_e_apt_4b", "bld_e_house_4a", "bld_e_apt_4b"], gap=1, doors={
        1: house("house_ruiz", "Ruiz", "Nadie responde. Por la rendija sale olor a sopa de algas."),
    })
    c.row(47, 43, ["bld_e_house_3b", "bld_e_ruin_3", "bld_e_house_4a", "bld_e_kiosk_2"], gap=1, doors={
        0: house("house_nakamura", "Nakamura", "Un letrero: «Se reparan visores y radios. Pregunte por la abuela Nakamura»."),
        2: house("house_ramiro", "de Don Ramiro", "El tendero vive aquí… y guarda las cajas de repuesto de El Último Brote."),
    })
    c.add({"type": "npc", "id": "mateo", "pos": [12, 44], "facing": "down", "wander": 2}, reserve=1)
    # Patios traseros (dan a la avenida): huertos y setos con hueco para pasar
    for x0, x1 in ((1, 18), (47, 62)):
        c.fill(x0, 35, x1, 37, "grass")
        c.fill(x0 + 1, 36, x1 - 1, 37, "soil_bed")
        c.scatter(["planter_hydro", "barrel_water", "solar_tree", "planter_dead"], (x0, 36, x1, 37), 4)
    c.fill(26, 35, 39, 37, "plaza")


# ---------------------------------------------------------------- mobiliario y anuncios
def _street_furniture(c):
    lamp = lambda s: light(CYAN if s.endswith("e") else PINK, (0, -30), 2.0, 0.65)
    # Paseo: farolas y jardineras alternas en el borde norte, bancos y papeleras en el sur
    c.along_h(9, 2, W - 3, 6, ["lamp_smart_e"], lit=light(CYAN, (0, -30), 2.0, 0.6), offset=4)
    c.along_h(12, 2, W - 3, 6, ["planter_hydro", "bench_holo", "planter_dead", "bin_smart"], solid=None, offset=1)
    # Avenida: farolas a los dos lados, postes de carga y bolardos
    c.along_h(26, 2, W - 3, 7, ["lamp_smart_e"], lit=light(PINK, (0, -30), 2.2, 0.7), offset=3)
    c.along_h(34, 2, W - 3, 7, ["lamp_smart_e"], lit=light(CYAN, (0, -30), 2.2, 0.7), offset=6)
    c.along_h(27, 2, W - 3, 9, ["charge_post", "bin_smart", "hydrant_water"], offset=6)
    # Anuncios y máquinas de la Calle Neón
    c.add({"type": "sign", "id": "holo_agronet_east", "pos": [48, 34], "sprite": "holo_agronet", "solid": [1, 1],
           "prompt": "Mirar el anuncio", "light": light(GREEN, (0, -30), 2.4, 1.0, True),
           "lines": [L("hal", "Anuncio: «¿Cansado de toser? Aire embotellado AgroNet: ¡solo 5 créditos!»."),
                     L("hal", "Dato: el oxígeno no se fabrica en botellas. Lo producen las plantas y el fitoplancton del mar con la fotosíntesis.")]},
          reserve=1)
    c.add({"type": "sign", "id": "vending_air", "pos": [20, 26], "sprite": "vending_air", "solid": [1, 1],
           "prompt": "Mirar la máquina", "light": light(CYAN, (0, -14), 1.4, 0.9),
           "lines": [L("hal", "Máquina expendedora: «AIRE DE MONTAÑA, sabor menta»."),
                     L("hal", "Una persona respira unos 11 000 litros de aire al día. Esta botella dura… unos minutos.")]},
          reserve=1)
    c.add({"type": "sign", "id": "holo_air_east", "pos": [56, 34], "sprite": "holo_air", "solid": [1, 1],
           "prompt": "Mirar el anuncio", "light": light(CYAN, (0, -30), 2.2, 0.9),
           "lines": [L("hal", "Anuncio holográfico: «Aire limpio. 5 créditos la botella»."),
                     L("andres", "Antes el aire era gratis para todo el mundo…"),
                     L("hal", "Y puede volver a serlo. Para eso llevamos La Semilla.")]}, reserve=1)
    c.add({"type": "sign", "id": "holo_antihuman_earth", "pos": [8, 34], "sprite": "holo_antihuman", "solid": [1, 1],
           "prompt": "Mirar la pintada", "light": light(RED, (0, -30), 2.2, 0.9, True),
           "lines": [L("hal", "Pintada holográfica: «LA TIERRA RESPIRA MEJOR SIN HUMANOS. — LOS ANTIHUMANISTAS»."),
                     L("andres", "¿Quiénes son?"),
                     L("hal", "Un clan de humanos y máquinas que no quiere que la humanidad se reconstruya. Sabotean invernaderos y naves."),
                     L("hal", "Es verdad que las personas dañamos el clima. Pero también podemos repararlo: para eso llevamos La Semilla.")]},
          reserve=1)
    c.add({"type": "sign", "id": "holo_agronet_south", "pos": [26, 35], "sprite": "holo_agronet", "solid": [1, 1],
           "prompt": "Mirar el anuncio", "light": light(GREEN, (0, -30), 2.4, 1.0, True),
           "lines": [L("hal", "Anuncio: «AgroNet: la única comida que no se marchita»."),
                     L("hal", "Comida de laboratorio. Útil, pero no sustituye a un huerto de verdad.")]}, reserve=1)
    # Paradas: tranvía en el centro de la avenida (lado sur) y aerobús
    c.prop("tram_stop", [32, 34], solid=(3, 1), lit=light(CYAN, (0, -24), 1.8, 0.7))
    c.prop("hover_stop", [14, 34], solid=(3, 1), lit=light(GOLD, (0, -24), 1.6, 0.6))
    c.prop("kiosk_info", [37, 34], lit=light(CYAN, (0, -16), 1.0, 0.7))
    # Mercado nocturno (y 33–35) entre la avenida y la torre de AgroNet
    stalls = ["stall_food", "stall_tech", "stall_plants", "stall_food"]
    for i, x in enumerate([27.5, 30.5, 34.5, 37.5]):
        c.prop(stalls[i], [x, 36], solid=(2, 1), lit=light([WARM, CYAN, GREEN, PINK][i], (0, -14), 1.4, 0.7, True))
    c.prop("vendor_cart", [44, 35], solid=None, lit=light(WARM, (0, -10), 1.0, 0.6))
    c.prop("vendor_cart", [24, 35], solid=None, lit=light(PINK, (0, -10), 1.0, 0.6))
    # Calle Sur: farolas y algún banco
    c.along_h(44, 3, W - 4, 8, ["lamp_smart_e"], lit=light(PINK, (0, -30), 2.0, 0.6), offset=2)
    c.along_h(47, 3, W - 4, 9, ["bin_smart", "planter_dead", "hydrant_water"], offset=4, solid=None)
    # Calles verticales: farolas
    for x in (19, 25, 40, 46):
        c.along_v(x, 14, 42, 8, ["lamp_smart_e"], lit=light(CYAN, (0, -30), 1.8, 0.55), offset=2)
    # Calcas del suelo: charcos con neón, grietas, hojas
    c.scatter(["decal_puddle", "decal_puddle_s", "decal_puddle_l"], (1, 9, W - 2, H - 2), 26, z=-1,
              on=("pave", "road", "plaza"))
    c.scatter(["decal_crack", "decal_crack_b", "decal_leaves"], (1, 1, W - 2, H - 2), 22, z=-1)
    # Detrás de las casas del norte: patios con setos secos
    for x0, x1 in ((1, 18), (37, 62)):
        c.scatter(["tree_dead_big", "planter_dead", "ac_unit"], (x0, 1, x1, 3), 5)


def _service(id, pos, label, rate):
    return {"type": "service", "id": id, "pos": list(pos), "sprite": "service_pump", "solid": [1, 1],
            "prompt": f"Estación de servicio · {label}", "rate": rate, "light": light(GOLD, (0, -22), 1.4, 0.8)}


# ---------------------------------------------------------------- vida
def _life(c):
    c.walkers([[2, 10], [61, 10]], 5, BARKS_PASEO)
    c.walkers([[2, 27], [61, 27]], 4, BARKS_AVENUE)
    c.walkers([[2, 33], [61, 33]], 4, BARKS_AVENUE)
    c.walkers([[26, 37], [39, 37]], 3, BARKS_MARKET, speed=(10, 16), pause=(1.5, 5.0))
    c.walkers([[2, 44], [61, 44]], 3, BARKS_SOUTH)
    c.walkers([[3, 16], [16, 16]], 2, BARKS_PASEO, speed=(10, 16))
    c.walkers([[20, 14], [20, 43]], 2, BARKS_AVENUE)
    c.walkers([[45, 14], [45, 43]], 2, BARKS_AVENUE)
    c.mover(["bot_cleaner"], [[3, 11], [60, 11]], count=1, speed=12, altitude=0, loop="pingpong", pause=[1.0, 3.0])
    c.mover(["bot_courier"], [[3, 33], [60, 33]], count=1, speed=22, altitude=0, loop="pingpong", pause=[0.5, 2.0])
    c.mover(["cargo_drone"], [[4, 6], [32, 17], [55, 19], [60, 4], [30, 3]], count=2, speed=28, altitude=34, loop="cycle")
    c.mover(["delivery_drone"], [[14, 24], [14, 39], [50, 39], [50, 9], [14, 9]], count=1, speed=34, altitude=26, loop="cycle")
    c.mover(["patrol_drone"], [[2, 30], [61, 30]], count=1, speed=20, altitude=40, loop="pingpong", pause=[0.5, 1.5])
    c.sky = {"kinds": ["sky_shuttle", "sky_hopper", "sky_freighter"], "interval": [8, 18], "speed": [18, 34],
             "rows": [2, 44]}
