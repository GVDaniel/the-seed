"""Base Shackleton (polo sur de la Luna): distrito presurizado junto a un cráter con hielo en sombra perpetua.

Plano:
  y 1–11   Pista de aterrizaje de ASTRA (oeste) · fila norte de módulos: laboratorio de Kai, cúpula-jardín,
           hangar y dormitorios (fachadas al Corredor Armstrong).
  y 12–15  Corredor Armstrong (carril de rovers) con pasarelas.
  y 16–26  Fila sur: Bar Cráter, Repuestos, dormitorios; plaza del Apolo.
  y 27–29  Paseo sur y línea del tranvía minero hacia el cráter.
  x 37–54  Regolito y el cráter Shackleton con el hielo (este); taladro y terminal en el borde.
"""
from city import City, L, light

PINK, CYAN, GOLD, GREEN, WARM, RED, ICE = "#ff3ea5", "#3de7c9", "#f4d35e", "#7dff9a", "#ffb070", "#ff4a4a", "#9fd8ff"
W, H = 56, 34

BARKS = [
    "Aquí pesas seis veces menos. ¡Mira qué salto!",
    "El hielo del cráter lleva miles de millones de años sin ver el Sol.",
    "De un litro de agua sacamos oxígeno para respirar e hidrógeno para combustible.",
    "Sin aire, el sonido no viaja: fuera de la base todo es silencio.",
    "Desde aquí la Tierra nunca sale ni se pone: siempre está en el mismo sitio del cielo.",
    "Las cúpulas tienen paredes dobles para frenar los micrometeoritos.",
]


def build():
    c = City("moon", W, H, seed=1969)
    c.border("cliff")
    c.noise_patches("grass", 1, 1, W - 2, H - 2, 0.35, 5.0)
    c.noise_patches("rough", 1, 1, W - 2, H - 2, 0.18, 3.0)
    c.sprinkle("crater_s", 1, 1, W - 2, H - 2, 0.025, over=("soil", "grass"))
    _crater(c)
    _streets(c)
    _pad(c)
    _north_row(c)
    _south_row(c)
    _furniture(c)
    _life(c)
    c.check_paths([(8, 9)], [(e.get("id", e.get("sprite")), (int(e["pos"][0]), int(e["pos"][1])))
                             for e in c.entities if e["type"] in ("npc", "scan", "terminal", "ship", "door", "sign", "service")])
    legend, ground, objects = c.legend_and_rows()
    return {
        "id": "moon", "display_name": "Base Shackleton · Luna", "tileset": "city_moon",
        "void_color": "#05070d", "ambient": "#7a82aa", "weather": "", "dark": True, "music": "mission",
        "legend": legend, "ground": ground, "objects": objects, "entities": c.entities,
        "ambient_life": c.ambient(),
        "arrival_lines": [
            L("hal", "Alunizaje completado. Gravedad: una sexta parte de la terrestre. ¡Cuidado con los saltos!"),
            L("hal", "No hay aire para respirar: tu traje te protege. Kai trabaja en el laboratorio, al otro lado del corredor."),
            L("hal", "Al sur del corredor están el Bar Cráter y una tienda de repuestos. El cráter con hielo queda al este."),
        ],
    }, c


def _crater(c):
    # Cráter: borde elevado (roca sólida a trozos), fondo de polvo oscuro y hielo en el centro
    cx, cy = 47, 14
    c.ellipse(cx, cy, 8.5, 7.0, "grass")
    c.ellipse(cx, cy, 5.5, 4.5, "ice_edge")
    c.ellipse(cx, cy, 4.2, 3.4, "ice")
    for (x, y) in [(40, 9), (40, 19), (53, 8), (54, 16), (52, 21), (42, 6), (45, 22), (49, 5)]:
        c.solid_tile(x, y, "rock_solid")
    c.add({"type": "scan", "id": "moon_ice_crater", "pos": [47, 14], "sprite": "ice", "radius": 40}, reserve=1)
    c.prop("ice", [45, 15], solid=None, force=True)
    c.prop("ice", [49, 13], solid=None, force=True)
    c.add({"type": "light", "id": "light_ice", "pos": [47, 14], "light": light(ICE, (0, 0), 4.0, 0.7)})
    c.add({"type": "terminal", "id": "drill_terminal", "challenge_id": "ice_drill", "pos": [41, 15], "solid": [1, 1],
           "locked_text": "Terminal del taladro. Kai te dirá cuándo usarla."}, reserve=1)
    c.add({"type": "light", "id": "light_drill", "pos": [41, 15], "light": light(CYAN, (0, -10), 1.5, 0.8)})
    c.prop("drill_rig", [43, 12], lit=light(GOLD, (0, -20), 1.0, 0.6, True))
    c.add({"type": "npc", "id": "tomas", "pos": [42, 19], "facing": "right", "wander": 2}, reserve=1)
    # Huellas de rover del corredor al cráter
    for x in range(37, 42):
        c.set(x, 13, "track_h")


def _streets(c):
    c.street_h(13, 1, 36, lanes=2, walk=2, line=False)      # aceras 11–12 y 15–16, calzada 13–14
    c.mover(["rover_moon"], [[-3, 13], [36, 13], [44, 11]], interval=[7, 14], speed=26, altitude=0)
    c.mover(["rover_moon"], [[44, 11], [36, 14], [-3, 14]], interval=[9, 16], speed=26, altitude=0)
    c.street_v(19, 1, 30, lanes=0, walk=2)                  # pasarela norte-sur x 17–18
    c.street_h(29, 1, W - 2, lanes=0, walk=2)               # paseo sur 27–28
    c.fill(1, 30, W - 2, 30, "rail_h")
    c.mover(["maglev_tram"], [[-9, 30], [W + 9, 30]], interval=[12, 20], speed=80, altitude=2)
    c.mover(["maglev_tram"], [[W + 9, 30], [-9, 30]], interval=[14, 22], speed=80, altitude=2)
    c.crosswalks()
    c.curbs()


def _pad(c):
    c.fill(2, 2, 13, 9, "pad_0")
    for x in range(2, 14):
        c.set(x, 2, "pad_mark")
    c.fill(7, 3, 8, 9, "pad_line")
    c.add({"type": "prop", "sprite": "launch_pad", "pos": [7.5, 7], "z": -1})
    c.add({"type": "ship", "id": "astra", "pos": [7.5, 6], "prompt": "Subir a ASTRA y despegar", "radius": 34}, reserve=2)
    c.add({"type": "spawn", "id": "ship", "pos": [7.5, 9]})
    c.add({"type": "light", "id": "light_ship", "pos": [7.5, 6], "light": light(GOLD, (0, 0), 3.0, 0.6)})
    c.add(_service("service_moon", [12, 8], "Shackleton", 0.4, "lunar_fuel_depot",
                   "Kai convierte el hielo lunar en combustible: servicio gratis para ASTRA."), reserve=1)
    for pos in ([2, 3], [13, 3], [2, 9]):
        c.prop("beacon", pos, solid=None, lit=light(RED, (0, -18), 0.8, 0.9, True))


def _north_row(c):
    # Fachadas al corredor (fondo en y = 10)
    c.row(20, 10, ["bld_m_lab_5", "bld_m_dome_6", "bld_m_hangar_6"], gap=1,
          lights={0: light(CYAN, (0, -30), 2.6, 0.7), 1: light(GREEN, (0, -20), 2.4, 0.6)})
    lab = next(e for e in c.entities if e.get("sprite") == "bld_m_lab_5")
    c.add({"type": "npc", "id": "kai", "pos": [lab["pos"][0], 11], "facing": "down"}, reserve=1)
    c.row(15, 10, ["bld_m_hab_3"], gap=0)


def _south_row(c):
    def dorm(id, family, note):
        return {"id": id, "prompt": "Llamar a la puerta",
                "lines": [L("hal", f"Casa de la familia {family}."), L("hal", note)]}

    # Fila sur: fachadas al paseo sur (fondo en y = 26)
    x = c.row(2, 26, ["bld_m_bar", "bld_m_shop", "bld_m_dorm"], gap=1, doors={
        0: {"id": "door_moon_bar", "label": "Bar Cráter", "prompt": "Entrar al Bar Cráter",
            "target": "moon_bar", "spawn": "entrance"},
        1: {"id": "door_moon_shop", "label": "Repuestos", "prompt": "Entrar en Repuestos Regolito",
            "target": "moon_shop", "spawn": "entrance"},
        2: dorm("dorm_a", "Tanaka", "Kai vive aquí. En la puerta: «Si oyes una explosión pequeña, es un experimento. Si es grande, llama»."),
    }, lights={0: light(PINK, (0, -36), 2.4, 0.8), 1: light(GOLD, (0, -36), 2.4, 0.8)})
    bar = next(e for e in c.entities if e.get("id") == "door_moon_bar")
    shop = next(e for e in c.entities if e.get("id") == "door_moon_shop")
    c.add({"type": "spawn", "id": "bar_door", "pos": [bar["pos"][0], 27]})
    c.add({"type": "spawn", "id": "shop_door", "pos": [shop["pos"][0], 27]})
    c.row(20, 26, ["bld_m_dorm", "bld_m_hab_4", "bld_m_dorm", "bld_m_dorm"], gap=1, doors={
        0: dorm("dorm_b", "Diallo", "Dentro se ve un telescopio apuntando a la Tierra."),
        2: dorm("dorm_c", "Larsen", "Huele a aceite de máquina. Ingrid duerme poco."),
        3: dorm("dorm_d", "Pérez", "Cartel: «Turno de minería. Volvemos con el hielo»."),
    })
    # Plaza del Apolo entre la fila sur y el corredor
    c.fill(3, 17, 15, 19, "plaza")
    c.set(9, 18, "plaza_center")
    c.add({"type": "sign", "id": "sign_apollo", "pos": [9, 18], "sprite": "sensor", "solid": [1, 1], "prompt": "Leer la placa",
           "lines": [L("hal", "Placa: «El 20 de julio de 1969, el Apolo 11 llevó a las primeras personas a la Luna»."),
                     L("hal", "Alunizó en el Mar de la Tranquilidad, lejos de aquí. Nosotros estamos en el polo sur lunar.")]},
          reserve=1)
    c.add({"type": "sign", "id": "holo_air_moon", "pos": [29, 27], "sprite": "holo_air", "solid": [1, 1],
           "prompt": "Mirar el anuncio", "light": light(CYAN, (0, -30), 2.2, 0.9, True),
           "lines": [L("hal", "Anuncio: «Aire reciclado AgroNet, ahora también en la Luna»."),
                     L("hal", "En las bases espaciales el aire se recicla: se quita el dióxido de carbono y se recupera el oxígeno.")]},
          reserve=1)


def _furniture(c):
    # Granja hidropónica entre el corredor y la fila sur
    c.fill(20, 17, 35, 20, "plaza")
    for y in (18, 20):
        c.fill(21, y, 34, y, "soil_bed")
        for x in range(21, 35, 3):
            c.prop("planter_hydro", [x, y], lit=light(GREEN, (0, -10), 0.8, 0.45) if x % 6 == 0 else None)
    c.prop("solar_tree", [35, 17], lit=light(CYAN, (0, -40), 1.2, 0.5))
    c.prop("barrel_water", [20, 17])
    c.along_h(11, 2, 35, 6, ["lamp_smart_m"], lit=light(CYAN, (0, -30), 2.0, 0.65), offset=3)
    c.along_h(16, 2, 35, 6, ["lamp_smart_m"], lit=light(PINK, (0, -30), 2.0, 0.6), offset=6)
    c.along_h(27, 2, W - 3, 7, ["lamp_smart_m"], lit=light(CYAN, (0, -30), 2.0, 0.6), offset=4)
    c.along_h(28, 2, W - 3, 8, ["bench_holo", "bin_smart", "planter_hydro", "kiosk_info"], solid=None, offset=2)
    for pos in ([4, 17], [14, 17], [4, 19], [14, 19]):
        c.prop("planter_hydro", pos, lit=light(GREEN, (0, -10), 0.9, 0.5))
    c.prop("bench_holo", [6, 19], solid=None)
    c.prop("bench_holo", [12, 19], solid=None)
    c.prop("tram_stop", [27, 28], solid=(3, 1), lit=light(CYAN, (0, -24), 1.8, 0.7))
    # Junto al hangar y la pista
    c.scatter(["crate_stack", "barrel_water", "solar_tree", "antenna_small"], (15, 2, 36, 4), 6)
    c.prop("solar_panel", [2, 11], force=True)
    c.prop("solar_panel", [4, 11], force=True)
    # Exterior: paneles, rocas, huellas
    c.scatter(["boulder_moon", "rocks_moon"], (38, 24, 54, 26), 4)
    c.scatter(["rocks_moon"], (36, 1, 54, 25), 10, solid=None, on=("soil", "grass", "rough"))
    c.scatter(["decal_crater_moon"], (36, 1, 54, 26), 5, z=-1, on=("soil", "grass", "rough"))
    c.scatter(["decal_crack"], (1, 11, 36, 28), 8, z=-1, on=("pave", "road"))


def _service(id, pos, label, rate, free_flag, free_text):
    return {"type": "service", "id": id, "pos": list(pos), "sprite": "service_pump", "solid": [1, 1],
            "prompt": f"Estación de servicio · {label}", "rate": rate, "light": light(GOLD, (0, -22), 1.4, 0.8),
            "free_flag": free_flag, "free_text": free_text}


def _life(c):
    c.walkers([[2, 12], [35, 12]], 3, BARKS)
    c.walkers([[2, 15], [35, 15]], 3, BARKS)
    c.walkers([[2, 28], [53, 28]], 4, BARKS)
    c.walkers([[17, 3], [17, 26]], 2, BARKS)
    c.mover(["bot_worker"], [[15, 5], [15, 12], [36, 12]], count=1, speed=10, altitude=0, loop="pingpong", pause=[1.0, 3.0])
    c.mover(["bot_cleaner"], [[2, 27], [53, 27]], count=1, speed=12, altitude=0, loop="pingpong", pause=[1.0, 2.0])
    c.mover(["cargo_drone"], [[8, 4], [44, 10], [30, 22], [8, 12]], count=1, speed=26, altitude=34, loop="cycle")
    c.mover(["patrol_drone"], [[40, 6], [52, 14], [44, 22], [38, 14]], count=1, speed=18, altitude=28, loop="cycle")
    c.sky = {"kinds": ["sky_hopper", "sky_shuttle"], "interval": [10, 22], "speed": [16, 30], "rows": [2, 30]}
