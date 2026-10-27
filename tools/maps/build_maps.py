"""Genera los mapas JSON de superficie e interiores de The Seed.

Uso:  python3 tools/maps/build_maps.py   (reescribe game/assets/data/maps/*.json)
Vista previa: python3 tools/maps/preview_map.py <id> salida.png

Mundo posapocalíptico cyberpunk: noches con neón ("dark": true + entidades con "light"),
lluvia ácida en la Tierra, tiendas y bares con interior (puertas "door" → otro mapa).
Las posiciones de la historia (misiones) no se mueven: las zonas nuevas se añaden alrededor.
"""
import json, math, os, random

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "game", "assets", "data", "maps"))


class Grid:
    def __init__(self, w, h, fill=" "):
        self.w, self.h = w, h
        self.g = [[fill] * w for _ in range(h)]

    def set(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = ch

    def rect(self, x0, y0, x1, y1, ch):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, ch)

    def rows(self):
        return ["".join(r) for r in self.g]


def L(who, text):
    return {"who": who, "text": text}


def light(color, offset=(0, -30), scale=2.0, energy=1.0, flicker=False):
    d = {"color": color, "offset": list(offset), "scale": scale, "energy": energy}
    if flicker:
        d["flicker"] = True
    return d


PINK, CYAN, GOLD, GREEN, WARM = "#ff3ea5", "#3de7c9", "#f4d35e", "#7dff9a", "#ffb070"


def building(sprite, pos, w, h_px, color, door=None, flicker=False):
    """Fachada sólida con luz de neón en el letrero. door: dict de puerta (target/spawn o lines)."""
    e = {"type": "door" if door else "prop", "sprite": sprite, "pos": list(pos), "solid": [w, 2],
         "light": light(color, (0, -(h_px - 9)), 2.3, 0.75, flicker)}
    if door:
        e.update(door)
        e.setdefault("radius", 26)
    return e


def lamp(pos, color):
    sprite = "lamp_pink" if color == PINK else "lamp_cyan"
    return {"type": "prop", "sprite": sprite, "pos": list(pos), "solid": [1, 1],
            "light": light(color, (0, -30), 2.0, 0.65)}


def house_door(id, pos, sprite, w, h_px, color, family, note):
    return building(sprite, pos, w, h_px, color, {
        "id": id, "prompt": "Llamar a la puerta",
        "lines": [L("hal", f"Casa de la familia {family}."), L("hal", note)],
    })


# ------------------------------------------------------------------ TIERRA
def earth():
    # 0–39 × 0–25: barrio original (historia). Nuevo: Calle Neón (x 41–58) y calle sur (y 26–33).
    W, H = 60, 34
    gr = Grid(W, H, ".")
    ob = Grid(W, H, " ")
    rng = random.Random(3)
    # borde de árboles
    for x in range(W):
        for y in (0, H - 1):
            ob.set(x, y, rng.choice("TtYg"))
    for y in range(H):
        for x in (0, W - 1):
            ob.set(x, y, rng.choice("TtYg"))
    # caminos
    gr.rect(4, 6, 4, 12, ":")
    gr.rect(4, 12, 13, 12, ":")
    gr.rect(13, 9, 23, 15, "#")
    gr.rect(24, 12, 30, 12, ":")
    gr.rect(26, 7, 26, 12, ":")
    gr.rect(27, 7, 32, 8, "#")
    gr.rect(30, 12, 30, 15, ":")
    gr.rect(6, 13, 6, 15, ":")
    gr.rect(26, 15, 36, 23, "_")
    gr.rect(9, 6, 9, 11, ":")
    # casa de Andrés (roja)
    for (x, y), ch in zip([(3, 3), (4, 3), (5, 3), (3, 4), (4, 4), (5, 4), (3, 5), (4, 5), (5, 5)], "ryuhjkvbn"):
        ob.set(x, y, ch)
    # casa vecina (gris)
    for (x, y), ch in zip([(8, 3), (9, 3), (10, 3), (8, 4), (9, 4), (10, 4), (8, 5), (9, 5), (10, 5)], "qoeasdzxz"):
        ob.set(x, y, ch)
    # casas del sur
    for (x, y), ch in zip([(3, 19), (4, 19), (5, 19), (3, 20), (4, 20), (5, 20), (3, 21), (4, 21), (5, 21)], "qoeasdzxz"):
        ob.set(x, y, ch)
    for (x, y), ch in zip([(9, 19), (10, 19), (11, 19), (9, 20), (10, 20), (11, 20), (9, 21), (10, 21), (11, 21)], "ryuhjkvbn"):
        ob.set(x, y, ch)
    # bóveda
    ob.rect(24, 2, 33, 2, "M")
    ob.rect(24, 3, 33, 6, "W")
    # vallas plataforma
    ob.rect(26, 14, 36, 14, "f")
    ob.set(25, 14, "F")
    ob.set(37, 14, "G")
    ob.set(30, 14, " ")
    ob.set(29, 14, "G")
    ob.set(31, 14, "F")
    # cartel
    ob.set(12, 8, "S")
    # árboles interiores y macetas
    for (x, y) in [(15, 4), (19, 3), (36, 9), (2, 15), (14, 20), (20, 21), (35, 4), (22, 5)]:
        ob.set(x, y, rng.choice("Tt"))
    for (x, y) in [(13, 16), (23, 16), (12, 10)]:
        ob.set(x, y, "B")
    for (x, y) in [(7, 9), (16, 18), (24, 20), (18, 23), (34, 11)]:
        ob.set(x, y, "m")
    # Calle Neón y conexiones
    gr.rect(30, 11, 47, 11, ":")
    ob.rect(30, 11, 47, 11, " ")
    gr.rect(47, 2, 49, 31, "#")
    gr.rect(2, 26, 49, 27, "#")
    gr.rect(19, 16, 19, 25, ":")
    gr.rect(50, 21, 57, 29, "_")
    legend = {
        ".": {"tile": [0, 0, 0, 1]}, ":": {"tile": [25, 25, 40, 41]}, "#": {"tile": 43}, "_": {"tile": 109},
        "m": {"tile": 29},
        "T": {"tile": 15, "solid": True}, "t": {"tile": 27, "solid": True}, "Y": {"tile": 3, "solid": True},
        "g": {"tile": 4, "solid": True},
        "f": {"tile": 81, "solid": True}, "F": {"tile": 80, "solid": True}, "G": {"tile": 82, "solid": True},
        "q": {"tile": 48, "solid": True}, "o": {"tile": 49, "solid": True}, "e": {"tile": 50, "solid": True},
        "a": {"tile": 60, "solid": True}, "s": {"tile": 61, "solid": True}, "d": {"tile": 62, "solid": True},
        "z": {"tile": 88, "solid": True}, "x": {"tile": 89, "solid": True},
        "r": {"tile": 52, "solid": True}, "y": {"tile": 53, "solid": True}, "u": {"tile": 54, "solid": True},
        "h": {"tile": 64, "solid": True}, "j": {"tile": 65, "solid": True}, "k": {"tile": 66, "solid": True},
        "v": {"tile": 84, "solid": True}, "b": {"tile": 85, "solid": True}, "n": {"tile": 84, "solid": True},
        "M": {"tile": [99, 100, 100, 101], "solid": True}, "W": {"tile": 126, "solid": True},
        "S": {"tile": 83, "solid": True}, "B": {"tile": 107, "solid": True},
    }
    entities = [
        {"type": "spawn", "id": "start", "pos": [4, 7]},
        {"type": "spawn", "id": "ship", "pos": [31, 23]},
        {"type": "npc", "id": "lucia", "pos": [26, 8], "facing": "down"},
        {"type": "scan", "id": "seed_vault", "pos": [28.5, 6], "sprite": "vault_door"},
        {"type": "item", "id": "the_seed", "pos": [31, 8], "sprite": "seed_chest", "prompt": "Tomar La Semilla",
         "locked_text": "Es el cofre de La Semilla. La abuela Lucía te lo dará cuando llegue el momento.",
         "collect_lines": [L("andres", "La Semilla… pesa poco, pero lleva el futuro de todo un planeta."),
                           L("hal", "Cofre asegurado en la mochila. Siguiente paso: la terminal de la plataforma de lanzamiento, al sureste.")]},
        {"type": "prop", "sprite": "greenhouse_dead", "pos": [18, 8], "solid": [3, 1]},
        {"type": "scan", "id": "earth_dead_plant", "pos": [21, 9], "sprite": "plant_dead"},
        {"type": "prop", "sprite": "plant_dead", "pos": [15, 9]},
        {"type": "scan", "id": "earth_air_sensor", "pos": [6, 15], "sprite": "sensor", "solid": [1, 1]},
        {"type": "prop", "sprite": "solar_panel", "pos": [8, 15], "solid": [1, 1]},
        {"type": "sign", "id": "sign_town", "pos": [12, 8], "prompt": "Leer el cartel",
         "lines": [L("hal", "«Barrio Semilla. Población: 312. Cúpula de aire más cercana: 4 km.»"),
                   L("hal", "Antes de La Marchitez, este barrio tenía un parque con 200 árboles.")]},
        {"type": "prop", "sprite": "launch_pad", "pos": [31, 22], "z": -1},
        {"type": "ship", "id": "astra", "pos": [31, 21], "prompt": "Subir a ASTRA y despegar", "radius": 34},
        {"type": "terminal", "id": "launch_terminal", "challenge_id": "launch_sequence", "pos": [27, 17], "solid": [1, 1],
         "locked_text": "La terminal de despegue necesita que primero tengas La Semilla."},
        {"type": "prop", "sprite": "antenna", "pos": [35, 17], "solid": [1, 1]},
    ]
    for (x, y) in [(11, 6), (14, 6), (20, 6), (36, 12), (2, 17), (13, 21), (22, 18), (7, 23), (33, 10)]:
        entities.append({"type": "prop", "sprite": "dead_tree", "pos": [x, y], "solid": [1, 1]})
    entities += earth_city()
    return {
        "id": "earth", "display_name": "Barrio Semilla · Tierra", "tileset": "earth",
        "void_color": "#141020", "ambient": "#6e6c96", "weather": "rain", "dark": True, "music": "mission",
        "legend": legend, "ground": gr.rows(), "objects": ob.rows(), "entities": entities,
        "arrival_lines": [
            L("hal", "Buenos días, Andrés. Sistemas de HAL en línea. Calidad del aire: mala. Ánimo: ¡bueno!"),
            L("andres", "HAL, hoy es el día. La abuela Lucía nos espera en la Bóveda Semillera."),
            L("hal", "Sigue la flecha dorada. Muévete con WASD y habla con la gente pulsando E."),
            L("hal", "Llovizna ácida de nivel bajo y apagón en medio barrio. Por suerte, los letreros de neón nunca se apagan."),
        ],
    }


def earth_city():
    """Calle Neón, chatarrería y calle sur: tienda, casas, anuncios, vecinos."""
    e = [
        building("bld_earth_shop", [44.5, 9], 4, 56, GREEN, {
            "id": "door_earth_shop", "label": "El Último Brote", "prompt": "Entrar en El Último Brote",
            "target": "earth_shop", "spawn": "entrance"}),
        {"type": "spawn", "id": "shop_door", "pos": [44.5, 10]},
        house_door("house_okafor", [52, 9], "bld_earth_house_a", 3, 52, GOLD, "Okafor",
                   "Nota en la puerta: «Turno de noche en la cúpula de aire. Volvemos al amanecer»."),
        house_door("house_lindqvist", [56, 9], "bld_earth_house_b", 3, 60, PINK, "Lindqvist",
                   "Se oye una radio: «…AgroNet anuncia otra subida del precio del aire embotellado…»."),
        building("bld_earth_ruin", [43, 20], 3, 44, CYAN, flicker=True),
        {"type": "sign", "id": "holo_agronet_east", "pos": [45, 15], "sprite": "holo_agronet", "solid": [1, 1],
         "prompt": "Mirar el anuncio", "light": light(GREEN, (0, -30), 2.4, 1.0, True),
         "lines": [L("hal", "Anuncio: «¿Cansado de toser? Aire embotellado AgroNet: ¡solo 5 créditos!»."),
                   L("hal", "Dato: el oxígeno no se fabrica en botellas. Lo producen las plantas y el fitoplancton del mar con la fotosíntesis.")]},
        {"type": "sign", "id": "vending_air", "pos": [51, 12], "sprite": "vending_air", "solid": [1, 1],
         "prompt": "Mirar la máquina", "light": light(CYAN, (0, -14), 1.4, 0.9),
         "lines": [L("hal", "Máquina expendedora: «AIRE DE MONTAÑA, sabor menta»."),
                   L("hal", "Una persona respira unos 11 000 litros de aire al día. Esta botella dura… unos minutos.")]},
        {"type": "sign", "id": "holo_air_east", "pos": [51, 16], "sprite": "holo_air", "solid": [1, 1],
         "prompt": "Mirar el anuncio", "light": light(CYAN, (0, -30), 2.2, 0.9),
         "lines": [L("hal", "Anuncio holográfico: «Aire limpio. 5 créditos la botella»."),
                   L("andres", "Antes el aire era gratis para todo el mundo…"),
                   L("hal", "Y puede volver a serlo. Para eso llevamos La Semilla.")]},
        lamp([46, 4], CYAN), lamp([50, 19], PINK), lamp([46, 25], CYAN),
        {"type": "prop", "sprite": "cable_pole", "pos": [41, 13], "solid": [1, 1]},
        {"type": "prop", "sprite": "cable_pole", "pos": [55, 17], "solid": [1, 1]},
        # Chatarrería de Zoe
        {"type": "sign", "id": "sign_scrapyard", "pos": [51, 20], "sprite": "crate", "solid": [1, 1],
         "prompt": "Leer el cartel", "light": light(PINK, (0, -10), 1.2, 0.8, True),
         "lines": [L("hal", "Cartel pintado a mano: «Chatarrería de Chispa. Si se rompe, se arregla»."),
                   L("hal", "Reutilizar piezas ahorra energía y materiales: es lo contrario de tirar.")]},
        {"type": "prop", "sprite": "scrap_pile", "pos": [52.5, 25], "solid": [2, 1]},
        {"type": "prop", "sprite": "scrap_pile", "pos": [56.5, 26], "solid": [2, 1]},
        {"type": "prop", "sprite": "scrap_pile", "pos": [54.5, 28], "solid": [2, 1]},
        {"type": "prop", "sprite": "barrel_rust", "pos": [57, 22], "solid": [1, 1]},
        {"type": "prop", "sprite": "barrel_toxic", "pos": [50, 24], "solid": [1, 1],
         "light": light(GREEN, (0, -8), 0.8, 0.6)},
        {"type": "prop", "sprite": "crate", "pos": [57, 29], "solid": [1, 1]},
        {"type": "npc", "id": "zoe", "pos": [54, 22], "facing": "down", "wander": 1.5},
        # Calle sur
        house_door("house_quispe", [6, 32], "bld_earth_house_a", 3, 52, CYAN, "Quispe",
                   "Amaru vive aquí. En la ventana hay una planta de plástico… y una de verdad, muy pequeña."),
        building("bld_earth_ruin", [11, 32], 3, 44, PINK, flicker=True),
        house_door("house_mateo", [16, 32], "bld_earth_house_b", 3, 60, PINK, "de Mateo",
                   "Dibujo pegado en el cristal: un cohete, una estrella y la palabra «ANDRÉS»."),
        house_door("house_ruiz", [26, 32], "bld_earth_house_a", 3, 52, GOLD, "Ruiz",
                   "Nadie responde. Por la rendija sale olor a sopa de algas."),
        house_door("house_nakamura", [31, 32], "bld_earth_house_b", 3, 60, CYAN, "Nakamura",
                   "Un letrero: «Se reparan visores y radios. Pregunte por la abuela Nakamura»."),
        building("bld_earth_ruin", [36, 32], 3, 44, GOLD),
        house_door("house_ramiro", [42, 32], "bld_earth_house_a", 3, 52, GREEN, "de Don Ramiro",
                   "El tendero vive encima de su tienda… y aquí guarda las cajas de repuesto."),
        lamp([9, 25], PINK), lamp([23, 25], CYAN), lamp([34, 25], PINK),
        {"type": "sign", "id": "holo_agronet_south", "pos": [28, 25], "sprite": "holo_agronet", "solid": [1, 1],
         "prompt": "Mirar el anuncio", "light": light(GREEN, (0, -30), 2.4, 1.0, True),
         "lines": [L("hal", "Anuncio: «AgroNet: la única comida que no se marchita»."),
                   L("hal", "Comida de laboratorio. Útil, pero no sustituye a un huerto de verdad.")]},
        {"type": "npc", "id": "mateo", "pos": [13, 26], "facing": "down", "wander": 2},
        {"type": "npc", "id": "amaru", "pos": [10, 17], "facing": "left", "wander": 1},
        # Luces del barrio original
        {"type": "light", "id": "light_vault", "pos": [28.5, 7], "light": light(GOLD, (0, -10), 3.0, 0.8)},
        {"type": "light", "id": "light_pad", "pos": [31, 20], "light": light(CYAN, (0, 0), 4.0, 0.8)},
        {"type": "light", "id": "light_terminal", "pos": [27, 17], "light": light(CYAN, (0, -10), 1.5, 0.9)},
        {"type": "light", "id": "light_houses", "pos": [7, 6], "light": light(WARM, (0, 0), 3.0, 0.6)},
        {"type": "light", "id": "light_south_houses", "pos": [7, 21], "light": light(WARM, (0, 0), 3.0, 0.6)},
        {"type": "light", "id": "light_greenhouse", "pos": [18, 8], "light": light(GREEN, (0, -8), 2.0, 0.5, True)},
        {"type": "light", "id": "light_sensor", "pos": [6, 15], "light": light(CYAN, (0, -8), 1.2, 0.7)},
    ]
    return e


def interior(id, region, name, wall, floor, shelf, keeper, shop, label_out, back_spawn, extras, arrival):
    """Interior de 16×11: muro con estantes, mostrador, salida abajo."""
    W, H = 16, 11
    gr = Grid(W, H, floor)
    ob = Grid(W, H, " ")
    ob.rect(0, 0, W - 1, 0, "#")
    ob.rect(0, 0, 0, H - 1, "#")
    ob.rect(W - 1, 0, W - 1, H - 1, "#")
    ob.rect(0, H - 1, W - 1, H - 1, "#")
    ob.rect(1, 1, W - 2, 1, wall)
    ob.rect(1, 1, 8, 1, shelf)
    ob.set(10, 1, "s")
    ob.set(13, 1, "s")
    ob.rect(1, 3, 8, 3, "C")
    gr.rect(7, 9, 8, 9, "x")
    gr.rect(10, 5, 13, 7, "r")
    legend = {
        ".": {"tile": [0, 1]}, ",": {"tile": [2, 3]}, ";": {"tile": [4, 5]}, "r": {"tile": 6}, "x": {"tile": 7},
        "#": {"tile": 8, "solid": True}, "w": {"tile": 9, "solid": True}, "c": {"tile": 10, "solid": True},
        "m": {"tile": 11, "solid": True}, "s": {"tile": 12, "solid": True}, "C": {"tile": 13, "solid": True},
        "S": {"tile": 14, "solid": True}, "B": {"tile": 15, "solid": True},
    }
    entities = [
        {"type": "spawn", "id": "entrance", "pos": [7.5, 7]},
        {"type": "door", "id": "exit", "pos": [7.5, 9], "label": "Salida", "prompt": label_out,
         "target": region, "spawn": back_spawn, "radius": 18},
        {"type": "npc", "id": keeper, "pos": [4, 2], "facing": "down", "shop": shop, "radius": 46},
        {"type": "prop", "sprite": "plant_pot", "pos": [14, 2], "solid": [1, 1]},
        {"type": "light", "id": "light_counter", "pos": [4.5, 3], "light": light(WARM, (0, -6), 3.0, 0.9)},
        {"type": "light", "id": "light_room", "pos": [11.5, 6], "light": light(PINK, (0, 0), 3.2, 0.6, True)},
        {"type": "light", "id": "light_exit", "pos": [7.5, 9], "light": light(CYAN, (0, -4), 1.6, 0.8)},
    ] + extras
    return {
        "id": id, "region": region, "display_name": name, "tileset": "interior",
        "void_color": "#0b0812", "ambient": "#8a84a8", "weather": "", "dark": True, "music": "cantina",
        "legend": legend, "ground": gr.rows(), "objects": ob.rows(), "entities": entities,
        "arrival_lines": arrival,
    }


def interiors():
    table = lambda x, y: {"type": "prop", "sprite": "table", "pos": [x, y], "solid": [1, 1]}
    stool = lambda x, y: {"type": "prop", "sprite": "stool", "pos": [x, y]}
    return [
        interior("earth_shop", "earth", "El Último Brote · Tierra", "c", ",", "S", "ramiro", "earth_store",
                 "Salir a la Calle Neón", "shop_door",
                 [{"type": "prop", "sprite": "crate", "pos": [12, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "crate", "pos": [13, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "screen_news", "pos": [11.5, 1]},
                  {"type": "sign", "id": "shop_radio", "pos": [2, 6], "sprite": "jukebox", "solid": [1, 1],
                   "prompt": "Escuchar la radio",
                   "lines": [L("hal", "Radio: «…tercer día de lluvia ácida. Se recomienda usar capucha y no tocar los charcos…»."),
                             L("hal", "La lluvia ácida daña hojas, suelos y edificios. Se reduce quemando menos carbón y petróleo.")]}],
                 [L("hal", "El Último Brote: la tienda más antigua del barrio. Habla con Don Ramiro para comprar.")]),
        interior("moon_bar", "moon", "Bar Cráter · Luna", "w", ".", "B", "lupe", "moon_bar",
                 "Salir a la base", "bar_door",
                 [table(11, 6), stool(10, 6), stool(13, 6), table(5, 7), stool(4, 7), stool(7, 7),
                  {"type": "prop", "sprite": "jukebox", "pos": [14, 4], "solid": [1, 1],
                   "light": light(GOLD, (0, -14), 1.4, 0.8)},
                  {"type": "prop", "sprite": "screen_menu", "pos": [11.5, 1]},
                  {"type": "npc", "id": "amina", "pos": [12, 7], "facing": "left"}],
                 [L("hal", "Bar Cráter. Ambiente: tranquilo. Música: aceptable. Batidos: muy recomendados.")]),
        interior("moon_shop", "moon", "Repuestos Regolito · Luna", "w", ".", "S", "ingrid", "moon_parts",
                 "Salir a la base", "shop_door",
                 [{"type": "prop", "sprite": "crate", "pos": [11, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "barrel_rust", "pos": [13, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "crate", "pos": [12, 8], "solid": [1, 1]},
                  {"type": "prop", "sprite": "screen_news", "pos": [11.5, 1]}],
                 [L("hal", "Repuestos Regolito: baterías, escudos y tornillos. Ingrid puede mejorar ASTRA.")]),
        interior("mars_bar", "mars", "Cantina Polvo Rojo · Marte", "m", ";", "B", "rosa", "mars_cantina",
                 "Salir a la colonia", "bar_door",
                 [table(11, 6), stool(10, 6), stool(13, 6), table(5, 7), stool(7, 7),
                  {"type": "prop", "sprite": "jukebox", "pos": [14, 4], "solid": [1, 1],
                   "light": light(PINK, (0, -14), 1.4, 0.8)},
                  {"type": "prop", "sprite": "screen_menu", "pos": [11.5, 1]},
                  {"type": "npc", "id": "nia", "pos": [4, 7], "facing": "right"}],
                 [L("hal", "Cantina Polvo Rojo. Aquí la gente de la colonia se cuenta las noticias.")]),
        interior("mars_shop", "mars", "Mercado de Jezero · Marte", "m", ";", "S", "chen", "mars_market",
                 "Salir a la colonia", "shop_door",
                 [{"type": "prop", "sprite": "crate", "pos": [11, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "crate", "pos": [12, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "plant_pot", "pos": [13, 8], "solid": [1, 1]},
                  {"type": "prop", "sprite": "screen_news", "pos": [11.5, 1]}],
                 [L("hal", "Mercado de Jezero. Chen vende un motor iónico que haría volar a ASTRA.")]),
    ]


# ------------------------------------------------------------------ LUNA / MARTE
def rocky(W, H, seed):
    gr = Grid(W, H, "0")
    ob = Grid(W, H, " ")
    rng = random.Random(seed)
    for y in range(H):
        for x in range(W):
            r = rng.random()
            gr.set(x, y, "4" if r < 0.04 else "p" if r < 0.1 else rng.choice("0123"))
    for x in range(W):
        ob.set(x, 0, "R")
        ob.set(x, H - 1, "R")
    for y in range(H):
        ob.set(0, y, "R")
        ob.set(W - 1, y, "R")
    return gr, ob, rng


ROCKY_LEGEND = {
    "0": {"tile": 0}, "1": {"tile": 1}, "2": {"tile": 2}, "3": {"tile": 3}, "4": {"tile": 4},
    "p": {"tile": 11}, "~": {"tile": 6}, "i": {"tile": 7}, "=": {"tile": 8}, "|": {"tile": 10},
    "R": {"tile": 5, "solid": True}, "H": {"tile": 9, "solid": True},
}


def moon():
    # 0–35 × 0–23: base de Kai y cráter (historia). Nuevo: distrito Shackleton (y 24–37).
    W, H = 36, 38
    gr, ob, rng = rocky(W, H, 31)
    gr.rect(4, 25, 33, 35, "=")
    gr.rect(17, 22, 18, 24, "|")
    gr.rect(3, 3, 13, 10, "=")
    ob.rect(3, 2, 13, 2, "H")
    for y in range(H):
        for x in range(W):
            d = ((x - 28) / 7.0) ** 2 + ((y - 10) / 6.0) ** 2
            if d <= 1.0:
                gr.set(x, y, "~")
            if ((x - 28) / 3.2) ** 2 + ((y - 10) / 2.6) ** 2 <= 1.0:
                gr.set(x, y, "i")
    gr.rect(14, 16, 20, 20, "|")
    for (x, y) in [(18, 4), (22, 19), (6, 15), (10, 20), (33, 20), (24, 3), (16, 11), (3, 13)]:
        ob.set(x, y, "R")
    entities = [
        {"type": "spawn", "id": "ship", "pos": [17, 21]},
        {"type": "ship", "id": "astra", "pos": [17, 19], "prompt": "Subir a ASTRA y despegar", "radius": 34},
        {"type": "prop", "sprite": "habitat", "pos": [5.5, 6], "solid": [2, 1]},
        {"type": "prop", "sprite": "habitat", "pos": [10.5, 6], "solid": [2, 1]},
        {"type": "prop", "sprite": "antenna", "pos": [13, 5], "solid": [1, 1]},
        {"type": "prop", "sprite": "solar_panel", "pos": [4, 9], "solid": [1, 1]},
        {"type": "prop", "sprite": "solar_panel", "pos": [5, 9], "solid": [1, 1]},
        {"type": "npc", "id": "kai", "pos": [8, 8], "facing": "right"},
        {"type": "scan", "id": "moon_ice_crater", "pos": [28, 10], "sprite": "ice", "radius": 40},
        {"type": "prop", "sprite": "ice", "pos": [26, 11]},
        {"type": "prop", "sprite": "ice", "pos": [30, 9]},
        {"type": "terminal", "id": "drill_terminal", "challenge_id": "ice_drill", "pos": [21, 12], "solid": [1, 1],
         "locked_text": "Terminal del taladro. Kai te dirá cuándo usarla."},
        {"type": "sign", "id": "sign_apollo", "pos": [15, 7], "sprite": "sensor", "solid": [1, 1], "prompt": "Leer la placa",
         "lines": [L("hal", "Placa: «El 20 de julio de 1969, el Apolo 11 llevó a las primeras personas a la Luna»."),
                   L("hal", "Alunizó en el Mar de la Tranquilidad, lejos de aquí. Nosotros estamos en el polo sur lunar.")]},
    ]
    for (x, y) in [(20, 6), (31, 18), (8, 17), (25, 21)]:
        entities.append({"type": "prop", "sprite": "rock_moon", "pos": [x, y], "solid": [1, 1]})
    entities += [
        building("bld_moon_bar", [9.5, 28], 4, 48, PINK, {
            "id": "door_moon_bar", "label": "Bar Cráter", "prompt": "Entrar al Bar Cráter",
            "target": "moon_bar", "spawn": "entrance"}),
        {"type": "spawn", "id": "bar_door", "pos": [9.5, 29]},
        building("bld_moon_shop", [17.5, 28], 4, 48, GOLD, {
            "id": "door_moon_shop", "label": "Repuestos", "prompt": "Entrar en Repuestos Regolito",
            "target": "moon_shop", "spawn": "entrance"}),
        {"type": "spawn", "id": "shop_door", "pos": [17.5, 29]},
        house_door("dorm_a", [25, 28], "bld_moon_dorm", 3, 44, CYAN, "Tanaka",
                   "Kai vive aquí. En la puerta: «Si oyes una explosión pequeña, es un experimento. Si es grande, llama»."),
        house_door("dorm_b", [30, 28], "bld_moon_dorm", 3, 44, PINK, "Diallo",
                   "Dentro se ve un telescopio apuntando a la Tierra."),
        house_door("dorm_c", [8, 35], "bld_moon_dorm", 3, 44, GOLD, "Larsen",
                   "Huele a aceite de máquina. Ingrid duerme poco."),
        house_door("dorm_d", [14, 35], "bld_moon_dorm", 3, 44, CYAN, "Pérez",
                   "Cartel: «Turno de minería. Volvemos con el hielo»."),
        {"type": "sign", "id": "holo_air_moon", "pos": [22, 33], "sprite": "holo_air", "solid": [1, 1],
         "prompt": "Mirar el anuncio", "light": light(CYAN, (0, -30), 2.2, 0.9, True),
         "lines": [L("hal", "Anuncio: «Aire reciclado AgroNet, ahora también en la Luna»."),
                   L("hal", "En las bases espaciales el aire se recicla: se quita el dióxido de carbono y se recupera el oxígeno.")]},
        lamp([6, 31], CYAN), lamp([13, 31], PINK), lamp([21, 31], CYAN), lamp([28, 31], PINK),
        {"type": "prop", "sprite": "crate", "pos": [32, 34], "solid": [1, 1]},
        {"type": "prop", "sprite": "barrel_rust", "pos": [33, 34], "solid": [1, 1]},
        {"type": "npc", "id": "tomas", "pos": [24, 14], "facing": "right", "wander": 2},
        {"type": "light", "id": "light_base", "pos": [8, 6], "light": light(CYAN, (0, -8), 3.4, 0.7)},
        {"type": "light", "id": "light_ship", "pos": [17, 19], "light": light(GOLD, (0, 0), 3.0, 0.6)},
        {"type": "light", "id": "light_ice", "pos": [28, 10], "light": light("#9fd8ff", (0, 0), 4.0, 0.7)},
        {"type": "light", "id": "light_drill", "pos": [21, 12], "light": light(CYAN, (0, -10), 1.5, 0.8)},
    ]
    return {
        "id": "moon", "display_name": "Base Shackleton · Luna", "tileset": "moon",
        "void_color": "#05070d", "ambient": "#7a82aa", "weather": "", "dark": True, "music": "mission",
        "legend": ROCKY_LEGEND, "ground": gr.rows(), "objects": ob.rows(), "entities": entities,
        "arrival_lines": [
            L("hal", "Alunizaje completado. Gravedad: una sexta parte de la terrestre. ¡Cuidado con los saltos!"),
            L("hal", "No hay aire para respirar: tu traje te protege. Kai está en la base, al oeste."),
            L("hal", "Al sur está el distrito de la base: el Bar Cráter y una tienda de repuestos para ASTRA."),
        ],
    }


def mars():
    # 0–37 × 0–23: base de Osei y delta (historia). Nuevo: colonia Jezero (y 24–37).
    W, H = 38, 38
    gr, ob, rng = rocky(W, H, 37)
    gr.rect(3, 26, 35, 35, "=")
    gr.rect(6, 22, 7, 25, "|")
    gr.rect(3, 3, 14, 9, "=")
    ob.rect(3, 2, 14, 2, "H")
    for y in range(H):
        for x in range(W):
            # abanico del delta (sureste)
            dx, dy = x - 22, y - 13
            if dx >= 0 and dy >= 0 and dx * dx + dy * dy <= 110 and x < W - 2 and y < H - 2:
                gr.set(x, y, "i")
    gr.rect(4, 17, 9, 21, "|")
    for (x, y) in [(18, 4), (30, 3), (33, 9), (16, 20), (12, 15), (2, 12)]:
        ob.set(x, y, "R")
    entities = [
        {"type": "spawn", "id": "ship", "pos": [6.5, 21]},
        {"type": "ship", "id": "astra", "pos": [6.5, 20], "prompt": "Subir a ASTRA y despegar", "radius": 34},
        {"type": "prop", "sprite": "habitat", "pos": [5.5, 5], "solid": [2, 1]},
        {"type": "prop", "sprite": "habitat", "pos": [10.5, 5], "solid": [2, 1]},
        {"type": "prop", "sprite": "antenna", "pos": [14, 5], "solid": [1, 1]},
        {"type": "npc", "id": "osei", "pos": [12, 8], "facing": "down"},
        {"type": "object", "id": "mars_greenhouse", "pos": [8, 13], "sprite": "dome_empty", "sprite_done": "dome_alive",
         "done_flag": "mars_planted", "solid": [3, 1], "prompt": "Plantar un brote de La Semilla",
         "locked_text": "El invernadero de la base. Primero termina los estudios que pidió la comandante.",
         "use_lines": [L("andres", "Un poco de suelo tratado, agua de la Luna… y luz. ¡Crece, pequeño!"),
                       L("hal", "Temperatura interior: 21 °C. Presión: como en la Tierra. ¡El brote está vivo!")],
         "done_lines": [L("hal", "El brote sigue creciendo dentro de la cúpula.")]},
        {"type": "scan", "id": "mars_rover", "pos": [25, 7], "sprite": "rover", "solid": [2, 1], "radius": 40},
        {"type": "scan", "id": "mars_delta", "pos": [28, 17], "sprite": "sample", "radius": 40},
        {"type": "terminal", "id": "delta_terminal", "challenge_id": "delta_samples", "pos": [21, 15], "solid": [1, 1],
         "locked_text": "Terminal de muestras. Primero escanea el delta y el rover."},
    ]
    for (x, y) in [(20, 8), (32, 13), (14, 18), (27, 22), (34, 5)]:
        entities.append({"type": "prop", "sprite": "rock_mars", "pos": [x, y], "solid": [1, 1]})
    entities += [
        building("bld_mars_bar", [8.5, 29], 4, 48, PINK, {
            "id": "door_mars_bar", "label": "Cantina", "prompt": "Entrar en la Cantina Polvo Rojo",
            "target": "mars_bar", "spawn": "entrance"}),
        {"type": "spawn", "id": "bar_door", "pos": [8.5, 30]},
        building("bld_mars_shop", [15.5, 29], 4, 48, GREEN, {
            "id": "door_mars_shop", "label": "Mercado", "prompt": "Entrar en el Mercado de Jezero",
            "target": "mars_shop", "spawn": "entrance"}),
        {"type": "spawn", "id": "shop_door", "pos": [15.5, 30]},
        building("bld_mars_school", [22.5, 29], 4, 48, CYAN, {
            "id": "door_school", "label": "Escuela", "prompt": "Mirar por la ventana de la escuela",
            "lines": [L("hal", "En la pizarra: «Marte: 4.º planeta. Día: 24 h 40 min. Año: 687 días terrestres»."),
                      L("hal", "Hoy no hay clase: los alumnos están fuera con el profesor Yusuf.")]}),
        building("bld_mars_garage", [29.5, 29], 4, 44, GOLD, {
            "id": "door_garage", "label": "Taller", "prompt": "Asomarse al taller",
            "lines": [L("hal", "Dentro hay tres rovers desmontados y una radio que suena muy alto."),
                      L("hal", "Bruno suele estar en la puerta, peleándose con una rueda.")]}),
        house_door("mars_house_a", [8, 36], "bld_mars_house", 3, 40, CYAN, "Osei",
                   "La comandante casi nunca está en casa. En la puerta hay una piedra con forma de corazón."),
        house_door("mars_house_b", [14, 36], "bld_mars_house", 3, 40, PINK, "de Nia",
                   "Una nota infantil: «Fui a la cantina. Vuelvo antes del atardecer azul»."),
        house_door("mars_house_c", [33, 36], "bld_mars_house", 3, 40, GOLD, "Wei",
                   "Cajas apiladas hasta el techo: Chen guarda aquí la mercancía."),
        {"type": "sign", "id": "holo_marscorp", "pos": [26, 34], "sprite": "holo_mars", "solid": [1, 1],
         "prompt": "Mirar el anuncio", "light": light(PINK, (0, -30), 2.4, 1.0, True),
         "lines": [L("hal", "Anuncio: «MarsCorp: agua, aire y trabajo. Todo bajo control»."),
                   L("hal", "Hmm. Yo prefiero que cada colonia controle su propia agua.")]},
        lamp([5, 32], PINK), lamp([12, 32], CYAN), lamp([19, 32], PINK), lamp([33, 32], CYAN),
        {"type": "prop", "sprite": "barrel_rust", "pos": [35, 29], "solid": [1, 1]},
        {"type": "prop", "sprite": "crate", "pos": [35, 30], "solid": [1, 1]},
        {"type": "npc", "id": "yusuf", "pos": [22, 32], "facing": "down", "wander": 2},
        {"type": "npc", "id": "bruno", "pos": [29, 31], "facing": "down", "wander": 1},
        {"type": "light", "id": "light_base", "pos": [8, 5], "light": light(GOLD, (0, -8), 3.4, 0.6)},
        {"type": "light", "id": "light_greenhouse", "pos": [8, 13], "light": light(GREEN, (0, -10), 2.6, 0.7)},
        {"type": "light", "id": "light_ship", "pos": [6.5, 20], "light": light(CYAN, (0, 0), 3.0, 0.6)},
        {"type": "light", "id": "light_delta_terminal", "pos": [21, 15], "light": light(CYAN, (0, -10), 1.5, 0.8)},
    ]
    return {
        "id": "mars", "display_name": "Base Jezero · Marte", "tileset": "mars",
        "void_color": "#2a120a", "ambient": "#9a7a80", "weather": "dust", "dark": True, "music": "mission",
        "legend": ROCKY_LEGEND, "ground": gr.rows(), "objects": ob.rows(), "entities": entities,
        "arrival_lines": [
            L("hal", "Aterrizaje en el cráter Jezero. Hay una pequeña tormenta de polvo: visibilidad reducida."),
            L("hal", "Un día en Marte (un «sol») dura unas 24 h y 40 min. La comandante Osei está en la base, al noroeste."),
            L("hal", "Al sur está la colonia: cantina, mercado, escuela y taller. MarsCorp lo controla casi todo."),
        ],
    }


os.makedirs(OUT, exist_ok=True)
for m in (earth(), moon(), mars(), *interiors()):
    with open(os.path.join(OUT, m["id"] + ".json"), "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
print("maps ok")
