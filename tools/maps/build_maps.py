"""Genera los mapas JSON de superficie e interiores de The Seed.

Uso:  python3 tools/maps/build_maps.py   (reescribe game/assets/data/maps/*.json)
Vista previa: python3 tools/maps/preview_map.py <id> salida.png

Exteriores (urbanismo con calles, manzanas, mobiliario y vida ambiental): earth_city.py, moon_city.py y
mars_city.py sobre city.py. Aquí quedan los interiores (tiendas, bares y el taller) y la salida a JSON.
Mundo posapocalíptico cyberpunk: noches con neón ("dark": true + entidades con "light").
"""
import json, math, os, random

import earth_city
import mars_city
import moon_city

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


# ------------------------------------------------------------------ DECORACIÓN
# Capa de ambiente: props sólidos (coches, tanques, rocas grandes), props pequeños sin colisión
# y calcas planas (z = -1: charcos, grietas, cráteres). Nunca tapan NPC ni puntos de misión
# (margen de 1 tile) y check_reachable() comprueba que ningún camino queda cortado.

INTERACTIVE = {"npc", "scan", "item", "terminal", "ship", "object", "sign", "door", "enemy", "service", "spawn"}


def footprint(pos, w, h):
    """Celdas que ocupa una caja de w×h tiles anclada abajo-centro en pos (como el spawner)."""
    x0 = pos[0] * 16 + 8 - w * 8
    x1 = pos[0] * 16 + 8 + w * 8
    cols = range(int(math.floor(x0 / 16)), int(math.floor((x1 - 1) / 16)) + 1)
    rows = range(int(pos[1]) - h + 1, int(pos[1]) + 1)
    return {(cx, cy) for cx in cols for cy in rows}


def anchor_cells(pos):
    xs = {int(math.floor(pos[0])), int(math.ceil(pos[0]))}
    return {(x, int(pos[1])) for x in xs}


def solid_cells(ob, legend, entities):
    cells = set()
    for y, row in enumerate(ob.g):
        for x, ch in enumerate(row):
            if ch != " " and legend.get(ch, {}).get("solid"):
                cells.add((x, y))
    for e in entities:
        if isinstance(e.get("solid"), list):
            cells |= footprint(e["pos"], *e["solid"])
    return cells


def reachable(W, H, solid, starts):
    seen = set()
    stack = [c for c in starts if c not in solid]
    while stack:
        c = stack.pop()
        if c in seen:
            continue
        seen.add(c)
        x, y = c
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= n[0] < W and 0 <= n[1] < H and n not in solid and n not in seen:
                stack.append(n)
    return seen


class Decor:
    def __init__(self, gr, ob, legend, entities, seed, keep_free=""):
        self.gr, self.ob, self.legend = gr, ob, legend
        self.W, self.H = gr.w, gr.h
        self.rng = random.Random(seed)
        self.keep_free = keep_free  # símbolos de suelo (caminos) donde no se ponen sólidos
        self.base_entities = list(entities)
        self.solid = solid_cells(ob, legend, entities)
        self.blocked = set(self.solid)
        self.flat = set()
        for e in entities:
            if e.get("type") in INTERACTIVE:
                for (ax, ay) in anchor_cells(e["pos"]):
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            self.blocked.add((ax + dx, ay + dy))
                    if e["type"] in ("door", "ship"):
                        self.blocked |= {(ax, ay + 2), (ax - 1, ay + 2), (ax + 1, ay + 2)}
            elif e.get("type") == "prop":
                self.blocked |= anchor_cells(e["pos"])
        self.out = []
        self.misses = []

    def ground_at(self, x, y):
        return self.gr.g[y][x] if 0 <= x < self.W and 0 <= y < self.H else " "

    def add(self, sprite, pos, solid=None, z=None, light=None, must=False, wall=False):
        if wall:
            e = {"type": "prop", "sprite": sprite, "pos": [pos[0], pos[1]]}
            if light:
                e["light"] = light
            self.out.append(e)
            return True
        if solid:
            cells = footprint(pos, *solid)
        else:
            cells = anchor_cells(pos)
        ok = all(1 <= x < self.W - 1 and 1 <= y < self.H - 1 for (x, y) in cells)
        if z is not None:
            ok = ok and not (cells & self.flat) and not (cells & self.solid)
        else:
            ok = ok and not (cells & self.blocked)
            if solid:
                ok = ok and not any(self.ground_at(x, y) in self.keep_free for (x, y) in cells)
        if not ok:
            if must:
                self.misses.append((sprite, pos))
            return False
        e = {"type": "prop", "sprite": sprite, "pos": [pos[0], pos[1]]}
        if solid:
            e["solid"] = list(solid)
            self.solid |= cells
            self.blocked |= cells
        if z is not None:
            e["z"] = z
            self.flat |= cells
        else:
            self.blocked |= cells
        if light:
            e["light"] = light
        self.out.append(e)
        return True

    def place(self, sprite, positions, solid=None, z=None, light=None, wall=False):
        """Piezas fijas; wall=True cuelga la pieza de la fila del muro (sin comprobar huecos)."""
        for pos in positions:
            self.add(sprite, pos, solid, z, light, must=True, wall=wall)

    def scatter(self, sprites, rect, count, solid=None, z=None, on="", light=None):
        """count piezas al azar dentro de rect=(x0, y0, x1, y1); on = símbolos de suelo admitidos."""
        x0, y0, x1, y1 = rect
        placed = tries = 0
        while placed < count and tries < count * 40:
            tries += 1
            x, y = self.rng.randint(x0, x1), self.rng.randint(y0, y1)
            if on and self.ground_at(x, y) not in on:
                continue
            if self.add(self.rng.choice(sprites), [x, y], solid, z, light):
                placed += 1
        return placed

    def finish(self, label, starts):
        """Devuelve las entidades de decoración tras comprobar que no cortan ningún camino."""
        if self.misses:
            print(f"  {label}: {len(self.misses)} piezas fijas no caben: {self.misses[:6]}")
        start_cells = set()
        for st in starts:
            start_cells |= anchor_cells(st)
        before = reachable(self.W, self.H, solid_cells(self.ob, self.legend, self.base_entities), start_cells)
        after = reachable(self.W, self.H, self.solid, start_cells)
        lost = (before - self.solid) - after
        if lost:
            raise SystemExit(f"{label}: la decoración corta el paso a {len(lost)} celdas, p. ej. {sorted(lost)[:8]}")
        return self.out


SHADOW_OF = {".": "a", ",": "b", ";": "e"}
WORN_OF = {".": "u", ",": "y", ";": "z"}


def interior(id, region, name, wall, floor, shelf, keeper, shop, label_out, back_spawn, extras, arrival,
             music="cantina", walls=None, decor=None, floor_marks=None):
    """Interior de 16×11: muro con estantes, mostrador, salida abajo. shop=None: el dueño solo conversa.
    walls: {x: símbolo} para la fila del muro (ventanas, tuberías, carteles); decor(d) coloca muebles;
    floor_marks: {(x, y): símbolo} detalles del suelo (rejillas, cables, franjas)."""
    W, H = 16, 11
    gr = Grid(W, H, floor)
    ob = Grid(W, H, " ")
    ob.rect(0, 0, W - 1, 0, "#")
    ob.rect(0, 0, 0, H - 1, "#")
    ob.rect(W - 1, 0, W - 1, H - 1, "#")
    ob.rect(0, H - 1, W - 1, H - 1, "#")
    ob.rect(1, 1, W - 2, 1, wall)
    ob.rect(1, 1, 8, 1, shelf)
    for x, ch in (walls or {10: "s", 13: "s"}).items():
        ob.set(x, 1, ch)
    ob.rect(1, 3, 8, 3, "C")
    rng = random.Random(len(id) * 31 + ord(id[0]))
    for y in range(2, H - 1):
        for x in range(1, W - 1):
            if rng.random() < 0.13:
                gr.set(x, y, WORN_OF[floor])
    gr.rect(1, 2, 14, 2, SHADOW_OF[floor])
    for (x, y), ch in (floor_marks or {}).items():
        gr.set(x, y, ch)
    gr.rect(7, 9, 8, 9, "x")
    gr.rect(10, 5, 13, 7, "r")
    legend = {
        ".": {"tile": [0, 1]}, ",": {"tile": [2, 3]}, ";": {"tile": [4, 5]}, "r": {"tile": 6}, "x": {"tile": 7},
        "#": {"tile": 8, "solid": True}, "w": {"tile": 9, "solid": True}, "c": {"tile": 10, "solid": True},
        "m": {"tile": 11, "solid": True}, "s": {"tile": 12, "solid": True}, "C": {"tile": 13, "solid": True},
        "S": {"tile": 14, "solid": True}, "B": {"tile": 15, "solid": True},
        "a": {"tile": 16}, "b": {"tile": 17}, "e": {"tile": 18}, "u": {"tile": 19}, "g": {"tile": 20},
        "l": {"tile": 21}, "y": {"tile": 22}, "z": {"tile": 23}, "h": {"tile": 24}, "d": {"tile": 25},
        "P": {"tile": 26, "solid": True}, "N": {"tile": 27, "solid": True}, "O": {"tile": 28, "solid": True},
        "Q": {"tile": 29, "solid": True}, "V": {"tile": 30, "solid": True}, "K": {"tile": 31, "solid": True},
    }
    entities = [
        {"type": "spawn", "id": "entrance", "pos": [7.5, 7]},
        {"type": "door", "id": "exit", "pos": [7.5, 9], "label": "Salida", "prompt": label_out,
         "target": region, "spawn": back_spawn, "radius": 18},
        dict({"type": "npc", "id": keeper, "pos": [4, 2], "facing": "down", "radius": 46}, **({"shop": shop} if shop else {})),
        {"type": "prop", "sprite": "plant_pot", "pos": [14, 2], "solid": [1, 1]},
        {"type": "light", "id": "light_counter", "pos": [4.5, 3], "light": light(WARM, (0, -6), 3.0, 0.9)},
        {"type": "light", "id": "light_room", "pos": [11.5, 6], "light": light(PINK, (0, 0), 3.2, 0.6, True)},
        {"type": "light", "id": "light_exit", "pos": [7.5, 9], "light": light(CYAN, (0, -4), 1.6, 0.8)},
    ] + extras
    if decor:
        d = Decor(gr, ob, legend, entities, len(id), keep_free="x")
        decor(d)
        entities += d.finish(id, [[7.5, 7]])
    return {
        "id": id, "region": region, "display_name": name, "tileset": "interior",
        "void_color": "#0b0812", "ambient": "#8a84a8", "weather": "", "dark": True, "music": music,
        "legend": legend, "ground": gr.rows(), "objects": ob.rows(), "entities": entities,
        "arrival_lines": arrival,
    }


def earth_shop_decor(d):
    d.place("city_fruit_crate", [[11, 6], [12, 6]], solid=[1, 1])
    d.place("city_planter", [[13, 6]], solid=[1, 1])
    d.place("crate_agronet", [[14, 4]], solid=[1, 1])
    d.place("in_counter_juice", [[9, 3]], solid=[1, 1])
    d.place("in_plant", [[1, 8]], solid=[1, 1])
    d.place("city_boxes", [[14, 8]], solid=[1, 1])
    d.place("in_rug_green", [[4, 8]], z=-1)
    d.place("decal_leaves", [[11, 8]], z=-1)


def bar_decor(window, rug, machine_light):
    def f(d):
        d.place("arcade", [[1, 5]], solid=[1, 1], light=light(CYAN, (0, -18), 1.0, 0.7, True))
        d.place("arcade", [[1, 6]], solid=[1, 1])
        d.place("smoothie_machine", [[9, 3]], solid=[1, 1], light=light(machine_light, (0, -16), 1.0, 0.7))
        d.place("in_plant_b", [[14, 8]], solid=[1, 1])
        d.place("in_chair_metal_side", [[3, 9]], solid=[1, 1])
        d.place(rug, [[11, 8]], z=-1)
        d.place("decal_trash", [[2, 8]], z=-1)
    return f


def moon_shop_decor(d):
    d.place("server_rack", [[1, 5], [1, 6]], solid=[1, 1], light=light(GREEN, (0, -16), 0.9, 0.5, True))
    d.place("tank_o2", [[14, 7]], solid=[1, 1])
    d.place("cable_spool", [[10, 8]], solid=[1, 1])
    d.place("city_boxes_moon", [[14, 6]], solid=[1, 1])
    d.place("decal_oil", [[5, 7]], z=-1)


def mars_shop_decor(d):
    d.place("hydro_rack", [[1.5, 6]], solid=[2, 1], light=light(PINK, (0, -12), 1.4, 0.6))
    d.place("crate_marscorp", [[13, 4]], solid=[1, 1])
    d.place("city_boxes_mars", [[14, 4]], solid=[1, 1])
    d.place("city_fruit_crate", [[10, 7]], solid=[1, 1])
    d.place("tank_o2", [[14, 6]], solid=[1, 1])
    d.place("in_rug_orange", [[4, 8]], z=-1)


def garage_decor(d):
    d.place("tool_board", [[9.5, 1]], wall=True)
    d.place("neon_taller", [[13, 1]], light=light(GOLD, (0, -6), 1.2, 0.8, True), wall=True)
    d.place("engine_block", [[4.5, 6]], solid=[2, 1])
    d.place("crate_marscorp", [[1, 8]], solid=[1, 1])
    d.place("barrel_water", [[14, 9]], solid=[1, 1])
    d.place("cable_spool", [[5, 8]], solid=[1, 1])
    d.place("tank_o2", [[14, 4]], solid=[1, 1])
    d.place("decal_oil", [[9, 5], [4, 4]], z=-1)


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
                 [L("hal", "El Último Brote: la tienda más antigua del barrio. Habla con Don Ramiro para comprar.")],
                 walls={9: "Q", 10: "K", 13: "V", 14: "K"}, decor=earth_shop_decor,
                 floor_marks={(5, 6): "d"}),
        interior("moon_bar", "moon", "Bar Cráter · Luna", "w", ".", "B", "lupe", "moon_bar",
                 "Salir a la base", "bar_door",
                 [table(11, 6), stool(10, 6), stool(13, 6), table(5, 7), stool(4, 7), stool(7, 7),
                  {"type": "prop", "sprite": "jukebox", "pos": [14, 4], "solid": [1, 1],
                   "light": light(GOLD, (0, -14), 1.4, 0.8)},
                  {"type": "prop", "sprite": "screen_menu", "pos": [11.5, 1]},
                  {"type": "npc", "id": "amina", "pos": [12, 7], "facing": "left"}],
                 [L("hal", "Bar Cráter. Ambiente: tranquilo. Música: aceptable. Batidos: muy recomendados.")],
                 walls={9: "N", 10: "s", 13: "P", 14: "N"}, decor=bar_decor("N", "in_rug_teal", CYAN)),
        interior("moon_shop", "moon", "Repuestos Regolito · Luna", "w", ".", "S", "ingrid", "moon_parts",
                 "Salir a la base", "shop_door",
                 [{"type": "prop", "sprite": "crate", "pos": [11, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "barrel_rust", "pos": [13, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "crate", "pos": [12, 8], "solid": [1, 1]},
                  {"type": "prop", "sprite": "screen_news", "pos": [11.5, 1]}],
                 [L("hal", "Repuestos Regolito: baterías, escudos y tornillos. Ingrid puede mejorar ASTRA.")],
                 walls={9: "P", 10: "s", 13: "V", 14: "N"}, decor=moon_shop_decor,
                 floor_marks={(3, 5): "g", (4, 5): "g", (6, 6): "l", (9, 6): "l"}),
        interior("mars_bar", "mars", "Cantina Polvo Rojo · Marte", "m", ";", "B", "rosa", "mars_cantina",
                 "Salir a la colonia", "bar_door",
                 [table(11, 6), stool(10, 6), stool(13, 6), table(5, 7), stool(7, 7),
                  {"type": "prop", "sprite": "jukebox", "pos": [14, 4], "solid": [1, 1],
                   "light": light(PINK, (0, -14), 1.4, 0.8)},
                  {"type": "prop", "sprite": "screen_menu", "pos": [11.5, 1]},
                  {"type": "npc", "id": "nia", "pos": [4, 7], "facing": "right"}],
                 [L("hal", "Cantina Polvo Rojo. Aquí la gente de la colonia se cuenta las noticias.")],
                 walls={9: "O", 10: "s", 13: "K", 14: "O"}, decor=bar_decor("O", "in_rug_orange", PINK)),
        interior("mars_shop", "mars", "Mercado de Jezero · Marte", "m", ";", "S", "chen", "mars_market",
                 "Salir a la colonia", "shop_door",
                 [{"type": "prop", "sprite": "crate", "pos": [11, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "crate", "pos": [12, 4], "solid": [1, 1]},
                  {"type": "prop", "sprite": "plant_pot", "pos": [13, 8], "solid": [1, 1]},
                  {"type": "prop", "sprite": "screen_news", "pos": [11.5, 1]}],
                 [L("hal", "Mercado de Jezero. Chen vende un propulsor iónico que ahorra combustible y botiquines.")],
                 walls={9: "O", 10: "s", 13: "Q", 14: "K"}, decor=mars_shop_decor),
        interior("mars_garage", "mars", "Taller de Bruno · Marte", "m", ";", "S", "bruno", None,
                 "Salir a la colonia", "garage_door", garage_extras(),
                 [L("hal", "El Taller de Bruno: rovers desmontados, herramientas por todas partes y una radio demasiado alta.")],
                 music="mission", walls={9: "K", 10: "K", 11: "P", 12: "P", 13: "K", 14: "V"}, decor=garage_decor,
                 floor_marks={(x, 9): "h" for x in (10, 11, 12, 13, 14)} | {(6, 5): "l", (9, 7): "d"}),
    ]


def garage_extras():
    """Banco donde se monta el motor de metano y destilador Sabatier del capítulo 4."""
    return [
        {"type": "object", "id": "mars_workbench", "pos": [11.5, 3], "sprite": "workbench", "solid": [2, 1],
         "done_flag": "engine_installed", "prompt": "Instalar el motor de metano",
         "locked_text": "El banco de trabajo de Bruno. Primero hace falta un motor que instalar.",
         "use_lines": [L("bruno", "¡Allá vamos! Quito el CX-50, ajusto los anclajes y conecto las tuberías de metano y oxígeno."),
                       L("bruno", "Listo. El Corazón Rojo está montado… pero el tanque de metano está vacío."),
                       L("hal", "Para fabricar metano necesitamos tres ingredientes: hidrógeno (del hielo), carbono (del CO₂) y un catalizador de níquel."),
                       L("hal", "Pregunta en la colonia: Yusuf, Nia y Ada pueden ayudarnos. Son misiones secundarias, haz las que quieras primero.")],
         "done_lines": [L("bruno", "El Corazón Rojo está bien sujeto. Ni una tuerca floja.")]},
        {"type": "object", "id": "methane_distiller", "pos": [13.5, 7], "sprite": "distiller_off", "sprite_done": "distiller_on",
         "solid": [1, 1], "done_flag": "methane_distilled", "prompt": "Destilar metano",
         "locked_text": "El destilador Sabatier de Bruno. Faltan ingredientes: hielo, CO₂ y níquel.",
         "use_lines": [L("hal", "Paso 1: electrólisis. El hielo derretido se separa en hidrógeno y oxígeno."),
                       L("hal", "Paso 2: reacción de Sabatier. CO₂ + 4 H₂ → CH₄ + 2 H₂O, con el níquel como catalizador."),
                       L("bruno", "¡Y el agua que sale vuelve al paso 1! Así no se desperdicia nada."),
                       L("hal", "Tanque de metano y oxígeno: lleno. Casco revisado. ASTRA está lista.")],
         "done_lines": [L("hal", "El destilador sigue goteando metano para la colonia. Ya no dependen de MarsCorp.")]},
        {"type": "prop", "sprite": "rover", "pos": [11.5, 7], "solid": [2, 1]},
        {"type": "prop", "sprite": "crate", "pos": [2, 6], "solid": [1, 1]},
        {"type": "prop", "sprite": "barrel_rust", "pos": [2, 7], "solid": [1, 1]},
        {"type": "prop", "sprite": "screen_news", "pos": [11.5, 1]},
    ]


os.makedirs(OUT, exist_ok=True)
for m in (earth_city.build()[0], moon_city.build()[0], mars_city.build()[0], *interiors()):
    with open(os.path.join(OUT, m["id"] + ".json"), "w") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
print("maps ok")
