"""Base Jezero (Marte): colonia de regolito impreso, delta del antiguo río y el Barranco de Óxido.

Plano:
  x 1–41   Colonia. Norte (fondo y = 9): base de mando de Osei, invernadero, silos y torre MarsCorp.
           y 10–13 Plaza Jezero (peatonal). Fila media (fondo y = 22): cantina, mercado, escuela, taller.
           y 23–29 Avenida Roja (aerovehículos y rovers). y 30–32 Patio de ciencias.
           Fila sur (fondo y = 39): viviendas con fachada al paseo sur (y 40–41).
           Pista de ASTRA al oeste (x 2–11, y 12–21).
  x 42–56  Delta de Jezero: sedimentos del antiguo río, el rover y la terminal de muestras.
  x 57     Pared de roca con dos pasos (y 11–13 y y 25–28).
  x 58–70  Barranco de Óxido (capítulo 4): carguero, Centinela AH-7, perforadora y meteorito.
"""
from city import City, L, light

PINK, CYAN, GOLD, GREEN, WARM, RED, ICE = "#ff3ea5", "#3de7c9", "#f4d35e", "#7dff9a", "#ffb070", "#e0283c", "#9fd8ff"
W, H = 72, 43
TRAFFIC = {"kinds": ["hover_taxi", "hover_van", "rover_mars"], "interval": [3.5, 7.5], "speed": 55, "altitude": 6,
           "two_way": False}

BARKS = [
    "Aquí el cielo es rosado de día… y el atardecer es azul.",
    "Un año en Marte dura 687 días terrestres. ¡Casi dos cumpleaños de espera!",
    "Imprimimos las casas con regolito: la arena de aquí, mezclada y calentada.",
    "Las tormentas de polvo pueden cubrir el planeta entero durante semanas.",
    "MarsCorp cobra el agua… pero la de Bruno es gratis.",
    "En el delta corría un río hace miles de millones de años.",
]


def build():
    c = City("mars", W, H, seed=2021)
    c.border("cliff")
    c.noise_patches("grass", 1, 1, W - 2, H - 2, 0.38, 5.0)
    c.noise_patches("rough", 1, 1, W - 2, H - 2, 0.2, 3.0)
    c.sprinkle("crater_s", 42, 1, W - 2, H - 2, 0.02, over=("soil", "grass"))
    _delta(c)
    _wall_and_canyon(c)
    _streets(c)
    _pad(c)
    _north_row(c)
    _middle_row(c)
    _science_yard(c)
    _south_row(c)
    _furniture(c)
    _life(c)
    c.check_paths([(6, 20)], [(e.get("id", e.get("sprite")), (int(e["pos"][0]), int(e["pos"][1])))
                              for e in c.entities if e["type"] in ("npc", "scan", "item", "terminal", "ship", "door",
                                                                   "sign", "service", "object", "enemy")])
    legend, ground, objects = c.legend_and_rows()
    return {
        "id": "mars", "display_name": "Base Jezero · Marte", "tileset": "city_mars",
        "void_color": "#2a120a", "ambient": "#9a7a80", "weather": "dust", "dark": True, "music": "mission",
        "legend": legend, "ground": ground, "objects": objects, "entities": c.entities,
        "ambient_life": c.ambient(),
        "arrival_lines": [
            L("hal", "Aterrizaje en el cráter Jezero. Hay una pequeña tormenta de polvo: visibilidad reducida."),
            L("hal", "Un día en Marte (un «sol») dura unas 24 h y 40 min. La comandante Osei está en la base de mando, al norte."),
            L("hal", "La Avenida Roja cruza la colonia: cantina, mercado, escuela y taller. MarsCorp lo controla casi todo."),
            L("hal", "Al este quedan el delta del antiguo río y, tras la pared de roca, el Barranco de Óxido. Dicen que allí patrullan robots."),
        ],
    }, c


# ---------------------------------------------------------------- terreno natural
def _delta(c):
    # Abanico de sedimentos que baja del noroeste del delta
    for y in range(1, 24):
        for x in range(43, 57):
            dx, dy = x - 43, y - 2
            if dx * dx + dy * dy * 1.4 <= 190:
                c.set(x, y, "sediment")
    c.noise_patches("soil", 43, 1, 56, 23, 0.25, 2.0, over=("sediment",))
    c.add({"type": "scan", "id": "mars_rover", "pos": [48.5, 7], "sprite": "rover", "solid": [2, 1], "radius": 40}, reserve=1)
    c.add({"type": "scan", "id": "mars_delta", "pos": [51, 16], "sprite": "sample", "radius": 40}, reserve=1)
    c.add({"type": "terminal", "id": "delta_terminal", "challenge_id": "delta_samples", "pos": [45, 19], "solid": [1, 1],
           "locked_text": "Terminal de muestras. Primero escanea el delta y el rover."}, reserve=1)
    c.add({"type": "light", "id": "light_delta_terminal", "pos": [45, 19], "light": light(CYAN, (0, -10), 1.5, 0.8)})
    for x in range(44, 49):
        c.set(x, 8, "track_h")
    for y in range(9, 19):
        c.set(48, y, "track_v")


def _wall_and_canyon(c):
    # Pared de roca de 2–3 tiles con borde irregular y dos pasos
    for y in range(1, H - 1):
        if 11 <= y <= 13 or 25 <= y <= 28:
            continue
        c.solid_tile(57, y, "cliff")
        c.solid_tile(58, y, "rock_solid" if c.rng.random() < 0.5 else "cliff")
        near_pass = 9 <= y <= 15 or 23 <= y <= 30
        if not near_pass and c.rng.random() < 0.6:
            c.solid_tile(56, y, "rock_solid")
        if not near_pass and c.rng.random() < 0.35:
            c.solid_tile(59, y, "rock_solid")
    c.noise_patches("rough", 58, 1, W - 2, H - 2, 0.4, 2.5, over=("soil", "grass"))
    for (x, y) in [(62, 4), (68, 7), (60, 18), (69, 16), (64, 21), (61, 35), (69, 33), (66, 39), (59, 30)]:
        c.solid_tile(x, y, "rock_solid")
    c.add({"type": "sign", "id": "sign_canyon", "pos": [56, 10], "sprite": "holo_antihuman", "solid": [1, 1],
           "prompt": "Mirar el cartel", "light": light(RED, (0, -30), 2.2, 0.9, True),
           "lines": [L("hal", "Pintada holográfica: «MARTE SIN HUMANOS. FIRMADO: LOS ANTIHUMANISTAS»."),
                     L("andres", "¿Por qué alguien querría que la gente no pueda empezar de nuevo?"),
                     L("hal", "Creen que las personas solo rompemos planetas. Nosotros vamos a demostrar que también sabemos repararlos.")]},
          reserve=1)
    c.add({"type": "prop", "sprite": "wreck_marscorp", "pos": [65, 9], "solid": [3, 1],
           "light": light(PINK, (0, -12), 2.0, 0.6, True)}, reserve=1)
    c.add({"type": "enemy", "id": "ah7_sentinel", "encounter": "sentinel_ah7", "pos": [61, 12], "sprite": "robot_ah7",
           "sprite_done": "robot_ah7_off", "done_flag": "won_sentinel_ah7", "radius": 34,
           "prompt": "Enfrentarte al Centinela AH-7", "light": light(RED, (0, -30), 1.6, 0.8, True),
           "locked_text": "Un robot enorme vigila el carguero. Mejor no acercarse sin un plan. (Habla con Bruno, en el Taller.)",
           "intro_lines": [{"who": "", "speaker": "Centinela AH-7", "text": "HUMANO DETECTADO. ORDEN ANTIHUMANISTA: PROTEGER EL CARGUERO."},
                           L("andres", "Ese motor es para La Semilla. ¡Apártate!"),
                           L("hal", "Pulsa cuando el anillo dorado toque el círculo: golpearás más fuerte. Cuando ataque, pulsa a tiempo para bloquear.")],
           "done_lines": [L("hal", "AH-7 sigue apagado. Su luz roja ya no parpadea.")]}, reserve=1)
    c.add({"type": "item", "id": "methane_engine", "pos": [66, 12], "sprite": "engine_part", "prompt": "Recoger el motor de metano",
           "locked_text": "Un motor de metano entre los restos. El Centinela no te deja acercarte.",
           "collect_lines": [L("andres", "¡Uf! Pesa como un rover entero."),
                             L("hal", "Activo los propulsores del traje para ayudarte. Llevémoslo al Taller de Bruno, en la colonia.")]},
          reserve=1)
    c.add({"type": "scan", "id": "mars_buried_ice", "pos": [63, 33], "sprite": "drill_rig", "solid": [1, 1], "radius": 40}, reserve=1)
    c.add({"type": "item", "id": "mars_ice_core", "pos": [64.5, 34], "sprite": "ice", "prompt": "Recoger el testigo de hielo",
           "locked_text": "La perforadora del profesor Yusuf. Él te dirá qué hacer.",
           "collect_lines": [L("hal", "Testigo de hielo guardado en frío. ¡Que no se derrita!")]}, reserve=1)
    c.add({"type": "light", "id": "light_ice", "pos": [63, 33], "light": light(ICE, (0, -10), 2.4, 0.7)})
    c.add({"type": "scan", "id": "mars_iron_meteorite", "pos": [67, 24], "sprite": "meteorite", "solid": [1, 1], "radius": 40},
          reserve=1)
    c.add({"type": "enemy", "id": "ah_drones", "encounter": "drones_meteorite", "pos": [64, 22], "sprite": "drone_ah",
           "sprite_done": "drone_ah_off", "done_flag": "won_drones_meteorite", "radius": 32,
           "prompt": "Enfrentarte a los drones vigía", "light": light(RED, (0, -10), 1.2, 0.8, True),
           "locked_text": "Drones zumbando sobre el meteorito. Primero escanea la roca.",
           "intro_lines": [{"who": "", "speaker": "Dron vigía", "text": "BZZZ. ZONA RESTRINGIDA. ALÉJESE DEL METEORITO."},
                           L("hal", "Son débiles a la luz: mi láser de escaneo les hará daño extra.")],
           "done_lines": [L("hal", "Los drones descansan en la arena, apagados.")]}, reserve=1)
    c.add({"type": "item", "id": "nickel_catalyst", "pos": [68.5, 26], "sprite": "sample", "prompt": "Recoger virutas de níquel",
           "locked_text": "Virutas brillantes del meteorito. Los drones no te dejan acercarte.",
           "collect_lines": [L("hal", "Virutas de níquel guardadas. Brillan como monedas nuevas.")]}, reserve=1)
    c.add({"type": "light", "id": "light_meteorite", "pos": [67, 24], "light": light(GOLD, (0, -6), 1.6, 0.5)})
    c.add({"type": "npc", "id": "ada", "pos": [55, 29], "facing": "left"}, reserve=1)
    # Pistas de rover por el barranco
    for x in range(42, 70):
        if c.get(x, 26) in ("soil", "grass", "rough", "sediment", "crater_s"):
            c.set(x, 26, "track_h")
    for y in range(13, 34):
        if c.get(63, y) in ("soil", "grass", "rough", "crater_s"):
            c.set(63, y, "track_v")
    c.prop("rover_wreck", [59.5, 20], solid=(2, 1))
    # Campamento de Ada junto al paso sur y balizas en los dos pasos de la pared
    for pos, sprite in (([53, 30], "crate_stack"), ([53, 31], "barrel_water"), ([52, 29], "antenna_small"),
                        ([54, 32], "solar_panel")):
        c.prop(sprite, pos)
    for pos in ([56, 12], [58, 14], [56, 24], [58, 29]):
        c.prop("beacon", pos, solid=None, lit=light("#ff4a4a", (0, -18), 0.8, 0.9, True))
    c.prop("city_barrier_mars", [59, 11])
    c.prop("city_barrier_mars", [59, 13])
    c.scatter(["boulder_mars"], (58, 1, W - 2, H - 2), 9, solid=(2, 1))
    c.scatter(["boulder_mars"], (43, 24, 55, 40), 4, solid=(2, 1))
    c.scatter(["rocks_mars"], (42, 1, W - 2, H - 2), 30, solid=None, on=("soil", "grass", "rough", "sediment"))
    c.scatter(["decal_crater_mars", "decal_drift_mars"], (42, 1, W - 2, H - 2), 10, z=-1,
              on=("soil", "grass", "rough", "sediment"))


# ---------------------------------------------------------------- colonia
def _streets(c):
    c.street_h(12, 13, 41, lanes=0, walk=2)                    # Plaza Jezero, filas 10–13
    c.fill(13, 10, 41, 13, "pave")
    c.street_h(25, 1, 41, lanes=3, walk=2, traffic=TRAFFIC)    # Avenida Roja, calzada 25–27
    c.fill(1, 40, 41, 41, "pave")                              # paseo sur, filas 40–41
    c.street_v(42, 10, 41, lanes=0, walk=1)                    # acera este de la colonia
    c.crosswalks()
    c.curbs()


def _pad(c):
    c.fill(2, 11, 11, 21, "pad_0")
    for x in range(2, 12):
        c.set(x, 11, "pad_mark")
    c.fill(6, 12, 7, 21, "pad_line")
    c.add({"type": "prop", "sprite": "launch_pad", "pos": [6.5, 17], "z": -1})
    c.add({"type": "ship", "id": "astra", "pos": [6.5, 16], "prompt": "Subir a ASTRA y despegar", "radius": 34}, reserve=2)
    c.add({"type": "spawn", "id": "ship", "pos": [6.5, 20]})
    c.add({"type": "light", "id": "light_ship", "pos": [6.5, 16], "light": light(CYAN, (0, 0), 3.0, 0.6)})
    c.add(_service("service_mars", [10, 20], "MarsCorp", 0.6, "methane_distilled",
                   "El destilador de Bruno abastece la estación: servicio gratis para ASTRA."), reserve=1)
    for pos in ([2, 12], [11, 12], [2, 21]):
        c.prop("beacon", pos, solid=None, lit=light("#ff4a4a", (0, -18), 0.8, 0.9, True))


def _north_row(c):
    # Base de mando, invernadero de Osei, silos y torre de MarsCorp (fondo y = 9)
    c.row(2, 9, ["bld_r_lab_5", "bld_r_silo_2"], gap=1, lights={0: light(GOLD, (0, -30), 2.6, 0.6)})
    lab = next(e for e in c.entities if e.get("sprite") == "bld_r_lab_5")
    gh = c.building("bld_r_greenhouse", 14.5, 9, lit=light(GREEN, (0, -12), 2.6, 0.7))
    gh.update({"type": "object", "id": "mars_greenhouse", "sprite": "bld_r_greenhouse",
               "sprite_done": "bld_r_greenhouse_alive", "done_flag": "mars_planted", "radius": 30,
               "prompt": "Plantar un brote de La Semilla",
               "locked_text": "El invernadero de la base. Primero termina los estudios que pidió la comandante.",
               "use_lines": [L("andres", "Un poco de suelo tratado, agua de la Luna… y luz. ¡Crece, pequeño!"),
                             L("hal", "Temperatura interior: 21 °C. Presión: como en la Tierra. ¡El brote está vivo!")],
               "done_lines": [L("hal", "El brote sigue creciendo dentro de la cúpula.")]})
    gh.pop("light", None)
    c.add({"type": "light", "id": "light_greenhouse", "pos": [14.5, 10], "light": light(GREEN, (0, -10), 2.6, 0.7)})
    c.reserved |= {(14, 10), (15, 10), (14, 11), (15, 11)}
    c.row(18, 9, ["bld_r_dome_5", "bld_r_block_4", "bld_r_tower_4", "bld_r_silo_2", "bld_r_silo_2"], gap=1,
          lights={2: light(PINK, (0, -80), 3.0, 0.7, True)})
    c.add({"type": "npc", "id": "osei", "pos": [lab["pos"][0] + 2, 10], "facing": "down"}, reserve=1)
    c.add({"type": "light", "id": "light_base", "pos": [lab["pos"][0], 10], "light": light(GOLD, (0, -8), 3.4, 0.6)})


def _middle_row(c):
    doors = {
        0: {"id": "door_mars_bar", "label": "Cantina", "prompt": "Entrar en la Cantina Polvo Rojo",
            "target": "mars_bar", "spawn": "entrance"},
        1: {"id": "door_mars_shop", "label": "Mercado", "prompt": "Entrar en el Mercado de Jezero",
            "target": "mars_shop", "spawn": "entrance"},
        2: {"id": "door_school", "label": "Escuela", "prompt": "Mirar por la ventana de la escuela",
            "lines": [L("hal", "En la pizarra: «Marte: 4.º planeta. Día: 24 h 40 min. Año: 687 días terrestres»."),
                      L("hal", "Hoy no hay clase: los alumnos están fuera con el profesor Yusuf.")]},
        3: {"id": "door_mars_garage", "label": "Taller", "prompt": "Entrar en el Taller de Bruno",
            "target": "mars_garage", "spawn": "entrance"},
    }
    c.row(14, 22, ["bld_r_bar", "bld_r_shop", "bld_r_school", "bld_r_garage", "bld_r_silo_2"], gap=1, doors=doors,
          lights={0: light(PINK, (0, -40), 2.4, 0.8), 1: light(GREEN, (0, -40), 2.4, 0.8),
                  2: light(CYAN, (0, -40), 2.2, 0.7), 3: light(GOLD, (0, -40), 2.4, 0.8, True)})
    for door_id, spawn in (("door_mars_bar", "bar_door"), ("door_mars_shop", "shop_door"),
                           ("door_mars_garage", "garage_door")):
        d = next(e for e in c.entities if e.get("id") == door_id)
        c.add({"type": "spawn", "id": spawn, "pos": [d["pos"][0], 23]})


def _science_yard(c):
    # y 30–32: patio de ciencias entre la avenida y las viviendas
    c.fill(13, 30, 40, 32, "plaza")
    c.add({"type": "npc", "id": "yusuf", "pos": [22, 31], "facing": "down", "wander": 2}, reserve=1)
    c.add({"type": "object", "id": "co2_compressor", "pos": [30, 31], "sprite": "compressor_off", "sprite_done": "compressor_on",
           "solid": [1, 1], "done_flag": "co2_compressed", "prompt": "Encender el compresor de Nia",
           "locked_text": "Un compresor casero con una pegatina: «Proyecto de ciencias de Nia. ¡No tocar!».",
           "use_lines": [L("andres", "El interruptor estaba atascado con polvo. Un golpecito… ¡y arranca!"),
                         L("hal", "El compresor aprieta el aire de Marte dentro de una bombona. Casi todo es CO₂. Bombona guardada.")],
           "done_lines": [L("hal", "El compresor de Nia sigue llenando bombonas. Ronronea como un gato.")]}, reserve=1)
    c.add({"type": "sign", "id": "holo_marscorp", "pos": [37, 30], "sprite": "holo_mars", "solid": [1, 1],
           "prompt": "Mirar el anuncio", "light": light(PINK, (0, -30), 2.4, 1.0, True),
           "lines": [L("hal", "Anuncio: «MarsCorp: agua, aire y trabajo. Todo bajo control»."),
                     L("hal", "Hmm. Yo prefiero que cada colonia controle su propia agua.")]}, reserve=1)
    for pos in ([15, 31], [18, 32], [26, 32], [34, 32]):
        c.prop("planter_hydro", pos, lit=light(GREEN, (0, -10), 0.9, 0.5))
    c.prop("solar_tree", [25, 31], lit=light(CYAN, (0, -40), 1.2, 0.5))
    c.prop("antenna_small", [39, 32], lit=light(RED, (0, -30), 0.8, 0.9, True))
    c.prop("bench_holo", [20, 32], solid=None)
    c.prop("bench_holo", [28, 32], solid=None)
    c.prop("kiosk_info", [33, 31], lit=light(CYAN, (0, -16), 1.0, 0.7))


def _south_row(c):
    def house(id, family, note):
        return {"id": id, "prompt": "Llamar a la puerta",
                "lines": [L("hal", f"Casa de la familia {family}."), L("hal", note)]}

    c.row(2, 39, ["bld_r_house", "bld_r_block_4", "bld_r_house", "bld_r_dome_5", "bld_r_block_4", "bld_r_house",
                  "bld_r_block_4"], gap=1, doors={
        0: house("mars_house_a", "Osei", "La comandante casi nunca está en casa. En la puerta hay una piedra con forma de corazón."),
        2: house("mars_house_b", "de Nia", "Una nota infantil: «Fui a la cantina. Vuelvo antes del atardecer azul»."),
        5: house("mars_house_c", "Wei", "Cajas apiladas hasta el techo: Chen guarda aquí la mercancía."),
    })


def _furniture(c):
    c.along_h(23, 2, 40, 6, ["lamp_smart_r"], lit=light(PINK, (0, -30), 2.0, 0.65), offset=2)
    c.along_h(29, 2, 40, 6, ["lamp_smart_r"], lit=light(CYAN, (0, -30), 2.0, 0.65), offset=5)
    c.along_h(24, 2, 40, 9, ["charge_post", "bin_smart", "hydrant_water"], offset=7)
    c.along_h(10, 13, 40, 6, ["lamp_smart_r"], lit=light(GOLD, (0, -30), 2.0, 0.6), offset=3)
    c.along_h(13, 13, 40, 5, ["planter_hydro", "bench_holo", "bin_smart"], solid=None, offset=2)
    c.along_h(40, 2, 40, 7, ["lamp_smart_r"], lit=light(PINK, (0, -30), 2.0, 0.6), offset=4)
    c.along_h(41, 2, 40, 8, ["bin_smart", "planter_hydro", "barrel_water"], solid=None, offset=3)
    c.prop("hover_stop", [33, 29], solid=(3, 1), lit=light(GOLD, (0, -24), 1.6, 0.6))
    c.scatter(["crate_marscorp", "barrel_water", "crate_stack"], (12, 14, 41, 16), 4)
    c.scatter(["decal_crack", "decal_oil"], (1, 10, 41, 41), 10, z=-1, on=("pave", "road", "plaza"))


def _service(id, pos, label, rate, free_flag, free_text):
    return {"type": "service", "id": id, "pos": list(pos), "sprite": "service_pump", "solid": [1, 1],
            "prompt": f"Estación de servicio · {label}", "rate": rate, "light": light(GOLD, (0, -22), 1.4, 0.8),
            "free_flag": free_flag, "free_text": free_text}


def _life(c):
    c.walkers([[13, 11], [41, 11]], 4, BARKS)
    c.walkers([[2, 24], [41, 24]], 3, BARKS)
    c.walkers([[2, 28], [41, 28]], 3, BARKS)
    c.walkers([[14, 31], [39, 31]], 3, BARKS, speed=(10, 16), pause=(1.5, 5.0))
    c.walkers([[2, 40], [41, 40]], 3, BARKS)
    c.mover(["bot_worker"], [[12, 14], [40, 14]], count=1, speed=10, altitude=0, loop="pingpong", pause=[1.0, 3.0])
    c.mover(["bot_cleaner"], [[2, 41], [41, 41]], count=1, speed=12, altitude=0, loop="pingpong", pause=[1.0, 2.0])
    c.mover(["rover_mars"], [[42, 26], [56, 26], [70, 26]], interval=[16, 28], speed=18, altitude=0)
    c.mover(["cargo_drone"], [[8, 6], [30, 18], [48, 12], [30, 4]], count=2, speed=26, altitude=34, loop="cycle")
    c.mover(["delivery_drone"], [[20, 24], [20, 35], [38, 35], [38, 12], [20, 12]], count=1, speed=30, altitude=26, loop="cycle")
    c.sky = {"kinds": ["sky_hopper", "sky_shuttle", "sky_freighter"], "interval": [9, 20], "speed": [16, 30],
             "rows": [2, 40]}
