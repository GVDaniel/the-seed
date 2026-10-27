"""Urbanismo para los mapas de superficie: calles, aceras, manzanas, edificios, mobiliario y vida.

Se trabaja con NOMBRES lógicos de tile (`soil`, `pave`, `road`, `hedge_h`…) que se traducen a índices
del atlas `city_<planeta>` con su manifiesto JSON (game/assets/art/tiles/city_<planeta>.json).
Los edificios toman tamaño (w, d) del manifiesto game/assets/art/props/buildings.json.

Convenciones de coordenadas (tiles), las mismas que el spawner de Godot:
- pos [x, y] = el sprite se apoya en el borde inferior de la fila y, centrado en la columna x.
- Un edificio de ancho w y fondo d con pos [cx, by] ocupa las filas by-d+1..by y las columnas centradas en cx.
"""
import json
import math
import os
import random

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TILES = os.path.join(ROOT, "game", "assets", "art", "tiles")
PROPS = os.path.join(ROOT, "game", "assets", "art", "props")

# Variantes de cada nombre lógico (se eligen por posición: patrón estable).
VARIANTS = {
    "soil": ["soil_0", "soil_1", "soil_2", "soil_3"],
    "rough": ["soil_rough_0", "soil_rough_1"],
    "grass": ["grass_0", "grass_1", "grass_2"],
    "pave": ["pave_0", "pave_1", "pave_2", "pave_3"],
    "road": ["road_0", "road_1", "road_2"],
    "plaza": ["plaza_0", "plaza_1"],
    "ice": ["ice_0", "ice_1"],
    "sediment": ["sediment_0", "sediment_1"],
    "cliff": ["cliff_0", "cliff_1", "cliff_2"],
    "rock_solid": ["rock_solid_0", "rock_solid_1"],
}
SOLID = {"hedge_h", "hedge_v", "cliff", "canal", "wall_low_h", "rock_solid"}
GROUND_ROAD = {"road", "road_line_h", "road_line_v", "cross_h", "cross_v", "rail_h"}
PAVED = {"pave", "plaza", "plaza_center", "grate", "hatch", "pad_0", "pad_mark", "pad_line"}

# Tamaños por defecto si aún no existe el manifiesto de edificios (w, d).
def _spec_sizes():
    import re
    out = {}
    names = ["bld_e_apt_4a", "bld_e_apt_4b", "bld_e_apt_5a", "bld_e_apt_5b", "bld_e_apt_6a", "bld_e_house_3a",
             "bld_e_house_3b", "bld_e_house_4a", "bld_e_ruin_4", "bld_e_ruin_3", "bld_e_tower_6", "bld_e_kiosk_2",
             "bld_e_greenhouse_4", "bld_m_hab_3", "bld_m_hab_4", "bld_m_hab_5", "bld_m_dome_6", "bld_m_lab_5",
             "bld_m_hangar_6", "bld_r_block_4", "bld_r_block_5", "bld_r_dome_5", "bld_r_tower_4", "bld_r_silo_2",
             "bld_r_lab_5"]
    for n in names:
        w = int(re.search(r"_(\d)[a-z]?$", n).group(1))
        out[n] = {"w": w, "d": 2 if w <= 2 else (4 if "dome" in n or "tower" in n else 3)}
    out.update({"bld_e_vault": {"w": 10, "d": 3}, "bld_e_shop": {"w": 5, "d": 3}, "bld_e_home_andres": {"w": 4, "d": 3},
                "bld_m_bar": {"w": 5, "d": 3}, "bld_m_shop": {"w": 5, "d": 3}, "bld_m_dorm": {"w": 4, "d": 3},
                "bld_r_bar": {"w": 5, "d": 3}, "bld_r_shop": {"w": 5, "d": 3}, "bld_r_school": {"w": 5, "d": 3},
                "bld_r_garage": {"w": 5, "d": 3}, "bld_r_house": {"w": 4, "d": 3}, "bld_r_greenhouse": {"w": 4, "d": 3},
                "bld_r_greenhouse_alive": {"w": 4, "d": 3}})
    return out


DEFAULT_BUILDINGS = _spec_sizes()


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def footprint(pos, w, h):
    x0 = pos[0] * 16 + 8 - w * 8
    x1 = pos[0] * 16 + 8 + w * 8
    cols = range(int(math.floor(x0 / 16)), int(math.floor((x1 - 1) / 16)) + 1)
    rows = range(int(pos[1]) - h + 1, int(pos[1]) + 1)
    return {(cx, cy) for cx in cols for cy in rows}


def L(who, text):
    return {"who": who, "text": text}


def light(color, offset=(0, -30), scale=2.0, energy=1.0, flicker=False):
    d = {"color": color, "offset": list(offset), "scale": scale, "energy": energy}
    if flicker:
        d["flicker"] = True
    return d


class City:
    def __init__(self, planet, W, H, seed, base="soil"):
        self.planet = planet
        self.W, self.H = W, H
        self.rng = random.Random(seed)
        self.ground = [[base] * W for _ in range(H)]
        self.objects = [[None] * W for _ in range(H)]
        self.entities = []
        self.blocked = set()      # celdas sólidas (edificios, props, tiles sólidos)
        self.reserved = set()     # celdas que deben quedar libres (frente de puertas, historia)
        self.used = set()         # celdas con algún prop (aunque no sea sólido)
        self.movers = []
        self.crowd = []
        self.sky = None
        self.h_roads = []         # rectángulos de calzada de calles horizontales (x0, y0, x1, y1)
        self.v_roads = []
        manifest = _load(os.path.join(TILES, f"city_{planet}.json"))
        self.tiles = manifest.get("tiles", {})
        self.buildings = dict(DEFAULT_BUILDINGS)
        self.buildings.update(_load(os.path.join(PROPS, "buildings.json")))

    # ------------------------------------------------------------ suelo
    def inside(self, x, y):
        return 0 <= x < self.W and 0 <= y < self.H

    def set(self, x, y, name):
        if self.inside(x, y):
            self.ground[y][x] = name

    def get(self, x, y):
        return self.ground[y][x] if self.inside(x, y) else None

    def fill(self, x0, y0, x1, y1, name):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, name)

    def solid_tile(self, x, y, name):
        if self.inside(x, y):
            self.objects[y][x] = name
            self.blocked.add((x, y))

    def solid_rect(self, x0, y0, x1, y1, name):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.solid_tile(x, y, name)

    def border(self, name="cliff", gaps=()):
        for x in range(self.W):
            for y in (0, self.H - 1):
                if (x, y) not in gaps:
                    self.solid_tile(x, y, name)
        for y in range(self.H):
            for x in (0, self.W - 1):
                if (x, y) not in gaps:
                    self.solid_tile(x, y, name)

    def noise_patches(self, name, x0, y0, x1, y1, amount, scale=5.0, over=("soil",), seed=0):
        """Manchas orgánicas (ruido suave) de `name` sobre el suelo natural."""
        noise = value_noise(seed or self.rng.randint(1, 99999), scale)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.get(x, y) in over and noise(x, y) > 1.0 - amount:
                    self.set(x, y, name)

    def sprinkle(self, name, x0, y0, x1, y1, chance, over=("soil",)):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.get(x, y) in over and self.rng.random() < chance:
                    self.set(x, y, name)

    def ellipse(self, cx, cy, rx, ry, name, over=None):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    if over is None or self.get(x, y) in over:
                        self.set(x, y, name)

    # ------------------------------------------------------------ calles
    def street_h(self, y, x0, x1, lanes=3, walk=2, line=True, rail=False, traffic=None):
        """Calle horizontal: calzada en las filas y..y+lanes-1 y aceras de `walk` filas a cada lado.
        lanes=0 = paseo peatonal (solo acera). traffic = dict de mover para los carriles."""
        self._pave(x0, y - walk, x1, y - 1)
        self._pave(x0, y + lanes, x1, y + lanes + walk - 1)
        if lanes == 0:
            return
        self.fill(x0, y, x1, y + lanes - 1, "road")
        self.h_roads.append((x0, y, x1, y + lanes - 1))
        mid = y + lanes // 2
        if rail:
            self.fill(x0, mid, x1, mid, "rail_h")
        elif line and lanes % 2 == 1:
            self.fill(x0, mid, x1, mid, "road_line_h")
        if traffic:
            top, bottom = y, y + lanes - 1
            self.movers.append(dict(traffic, path=[[x1 + 3, top], [x0 - 3, top]]))
            self.movers.append(dict(traffic, path=[[x0 - 3, bottom], [x1 + 3, bottom]]))
        if rail:
            self.movers.append({"kinds": ["maglev_tram"], "path": [[x0 - 9, mid], [x1 + 9, mid]],
                                "interval": [14, 24], "speed": 95, "altitude": 2, "two_way": False})

    def street_v(self, x, y0, y1, lanes=3, walk=2, line=True, traffic=None):
        self._pave(x - walk, y0, x - 1, y1)
        self._pave(x + lanes, y0, x + lanes + walk - 1, y1)
        if lanes == 0:
            return
        self.fill(x, y0, x + lanes - 1, y1, "road")
        self.v_roads.append((x, y0, x + lanes - 1, y1))
        mid = x + lanes // 2
        if line and lanes % 2 == 1:
            self.fill(mid, y0, mid, y1, "road_line_v")
        if traffic:
            left, right = x, x + lanes - 1
            self.movers.append(dict(traffic, path=[[left, y0 - 3], [left, y1 + 3]]))
            self.movers.append(dict(traffic, path=[[right, y1 + 3], [right, y0 - 3]]))

    def _pave(self, x0, y0, x1, y1):
        """Acera sin pisar calzadas ya trazadas (los cruces se respetan)."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.get(x, y) not in GROUND_ROAD:
                    self.set(x, y, "pave")

    def crosswalks(self):
        """Cruces limpios (sin líneas ni raíles dentro) y pasos de peatones en cada boca del cruce."""
        def cells(rects):
            out = set()
            for (x0, y0, x1, y1) in rects:
                out |= {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
            return out
        hc, vc = cells(self.h_roads), cells(self.v_roads)
        inter = {c for c in hc & vc if self.get(*c) in GROUND_ROAD}
        for (x, y) in inter:
            self.set(x, y, "road")
        for (x, y) in inter:
            for dx in (1, -1):
                n = (x + dx, y)
                if n in hc and n not in inter and self.get(*n) in GROUND_ROAD:
                    self.set(*n, "cross_h")
            for dy in (1, -1):
                n = (x, y + dy)
                if n in vc and n not in inter and self.get(*n) in GROUND_ROAD:
                    self.set(*n, "cross_v")

    def curbs(self):
        """Bordillos: la acera que toca la calzada recibe pave_edge_<lado> o esquina."""
        src = [row[:] for row in self.ground]
        road = lambda x, y: (src[y][x] in GROUND_ROAD) if self.inside(x, y) else False
        for y in range(self.H):
            for x in range(self.W):
                if src[y][x] != "pave":
                    continue
                n, s, w, e = road(x, y - 1), road(x, y + 1), road(x - 1, y), road(x + 1, y)
                if n:
                    self.set(x, y, "pave_edge_n")
                elif s:
                    self.set(x, y, "pave_edge_s")
                elif w:
                    self.set(x, y, "pave_edge_w")
                elif e:
                    self.set(x, y, "pave_edge_e")
                elif road(x + 1, y + 1):
                    self.set(x, y, "pave_corner_se")
                elif road(x - 1, y + 1):
                    self.set(x, y, "pave_corner_sw")
                elif road(x + 1, y - 1):
                    self.set(x, y, "pave_corner_ne")
                elif road(x - 1, y - 1):
                    self.set(x, y, "pave_corner_nw")

    # ------------------------------------------------------------ edificios y props
    def size_of(self, sprite):
        """(ancho, filas que ocupa la silueta entera: tejado + fachada). Todo es sólido: nadie
        queda escondido detrás de un tejado."""
        b = self.buildings.get(sprite, {})
        wall = int(b.get("wall", 48))
        return int(b.get("w", 4)), int(b.get("d", 3)) + int(math.ceil(wall / 16.0))

    def building(self, sprite, cx, by, door=None, lit=None, extra=None):
        """Edificio con su sombra de suelo. door = dict de puerta (id, target/spawn o lines…)."""
        w, d = self.size_of(sprite)
        e = {"type": "door" if door else "prop", "sprite": sprite, "pos": [cx, by], "solid": [w, d]}
        if lit:
            e["light"] = lit
        if door:
            e.update(door)
            e.setdefault("radius", 26)
        if extra:
            e.update(extra)
        cells = footprint([cx, by], w, d)
        # Un edificio alto puede apoyar el tejado sobre el borde del mapa (se quita el borde de ahí).
        for (x, y) in cells:
            if self.inside(x, y) and self.objects[y][x] == "cliff":
                self.objects[y][x] = None
                self.blocked.discard((x, y))
        cells = {(x, y) for (x, y) in cells if y >= 0}
        clash = cells & (self.blocked | self.reserved)
        if clash:
            raise SystemExit(f"{self.planet}: {sprite} en {cx},{by} choca con {sorted(clash)[:4]}")
        self.blocked |= cells
        self.used |= cells
        if door:
            dx = float(self.buildings.get(sprite, {}).get("door_dx", 0))
            fx = int(round(cx + dx))
            self.reserved |= {(fx, by + 1), (fx - 1, by + 1), (fx + 1, by + 1), (fx, by + 2)}
        self.entities.append(e)
        return e

    def row(self, x0, by, sprites, gap=1, doors=None, lights=None):
        """Fila de edificios contiguos (fachada continua) de izquierda a derecha desde x0.
        doors/lights: {índice: dict}. Devuelve la x siguiente libre."""
        x = x0
        for i, sprite in enumerate(sprites):
            if sprite is None:
                x += gap
                continue
            w, _ = self.size_of(sprite)
            cx = x + (w - 1) / 2.0
            self.building(sprite, cx, by, (doors or {}).get(i), (lights or {}).get(i))
            x += w + gap
        return x

    def add(self, entity, solid_cells=True, reserve=0):
        """Entidad de historia o interactiva. reserve = radio (tiles) de celdas que quedan libres."""
        self.entities.append(entity)
        x, y = entity["pos"]
        if isinstance(entity.get("solid"), list):
            cells = footprint(entity["pos"], *entity["solid"])
            self.blocked |= cells
            self.used |= cells
        if reserve:
            for yy in range(int(y) - reserve, int(y) + reserve + 1):
                for xx in range(int(math.floor(x)) - reserve, int(math.ceil(x)) + reserve + 1):
                    self.reserved.add((xx, yy))
        return entity

    def can_place(self, pos, solid=None):
        cells = footprint(pos, *solid) if solid else {(int(math.floor(pos[0])), int(pos[1])),
                                                      (int(math.ceil(pos[0])), int(pos[1]))}
        for (x, y) in cells:
            if not (1 <= x < self.W - 1 and 1 <= y < self.H - 1):
                return False
            if self.get(x, y) in GROUND_ROAD:
                return False
        return not (cells & (self.blocked | self.reserved | self.used))

    def prop(self, sprite, pos, solid=(1, 1), z=None, lit=None, force=False):
        """Prop decorativo; si no cabe (y no es force) se omite. Devuelve si se colocó."""
        if not os.path.exists(os.path.join(PROPS, sprite + ".png")):
            print(f"  {self.planet}: falta el sprite {sprite}, se omite")
            return False
        solid = list(solid) if solid else None
        if z is not None:
            solid = None
        if not force and z is None and not self.can_place(pos, solid):
            return False
        e = {"type": "prop", "sprite": sprite, "pos": [pos[0], pos[1]]}
        if solid:
            e["solid"] = solid
            cells = footprint(pos, *solid)
            self.blocked |= cells
            self.used |= cells
        elif z is None:
            self.used.add((int(round(pos[0])), int(pos[1])))
        if z is not None:
            e["z"] = z
        if lit:
            e["light"] = lit
        self.entities.append(e)
        return True

    def along_h(self, y, x0, x1, every, sprites, solid=(1, 1), lit=None, offset=0, z=None):
        """Mobiliario a intervalos regulares en la fila y (alternando la lista de sprites)."""
        i = 0
        for x in range(x0 + offset, x1 + 1, every):
            sprite = sprites[i % len(sprites)]
            lt = lit(sprite) if callable(lit) else lit
            self.prop(sprite, [x, y], solid, z, lt)
            i += 1

    def along_v(self, x, y0, y1, every, sprites, solid=(1, 1), lit=None, offset=0, z=None):
        i = 0
        for y in range(y0 + offset, y1 + 1, every):
            sprite = sprites[i % len(sprites)]
            lt = lit(sprite) if callable(lit) else lit
            self.prop(sprite, [x, y], solid, z, lt)
            i += 1

    def scatter(self, sprites, rect, count, solid=(1, 1), z=None, on=None, lit=None, tries=40):
        x0, y0, x1, y1 = rect
        placed = n = 0
        while placed < count and n < count * tries:
            n += 1
            x, y = self.rng.randint(x0, x1), self.rng.randint(y0, y1)
            if on and self.get(x, y) not in on:
                continue
            if z is not None and ((x, y) in self.blocked or (x, y) in self.reserved):
                continue
            if self.prop(self.rng.choice(sprites), [x, y], solid, z, lit):
                placed += 1
        return placed

    # ------------------------------------------------------------ vida
    def walkers(self, path, count, barks, speed=(16, 26), pause=(0.6, 4.0)):
        self.crowd.append({"path": path, "count": count, "speed": list(speed), "pause": list(pause),
                           "barks": barks})

    def mover(self, kinds, path, **kw):
        self.movers.append(dict({"kinds": kinds, "path": path}, **kw))

    # ------------------------------------------------------------ salida
    def check_paths(self, starts, targets):
        """Todos los objetivos (pos de entidades interactivas) deben ser alcanzables desde el inicio."""
        seen = set()
        stack = [s for s in starts]
        while stack:
            c = stack.pop()
            if c in seen or c in self.blocked or not self.inside(*c):
                continue
            seen.add(c)
            x, y = c
            stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        missing = []
        for label, cell in targets:
            x, y = cell
            near = {(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1, 2)}
            if not (near & seen):
                missing.append(label)
        if missing:
            raise SystemExit(f"{self.planet}: inalcanzables {missing}")

    def legend_and_rows(self):
        """Traduce los nombres a símbolos ASCII + leyenda con índices del atlas."""
        symbols = {}
        pool = [c for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!$%&()*+,-./:;<=>?@[]^_{|}~"]
        legend = {}

        def sym(name):
            if name not in symbols:
                symbols[name] = pool.pop(0)
                names = VARIANTS.get(name, [name])
                idx = [self.tiles[n] for n in names if n in self.tiles]
                if not idx:
                    idx = [self.tiles.get(VARIANTS["soil"][0], 0)]
                entry = {"tile": idx if len(idx) > 1 else idx[0]}
                if name in SOLID:
                    entry["solid"] = True
                legend[symbols[name]] = entry
            return symbols[name]

        ground = ["".join(sym(n) for n in row) for row in self.ground]
        objects = ["".join(sym(n) if n else " " for n in row) for row in self.objects]
        return legend, ground, objects

    def ambient(self):
        out = {}
        if self.movers:
            out["movers"] = self.movers
        if self.crowd:
            out["crowd"] = self.crowd
        if self.sky:
            out["sky"] = self.sky
        return out


def value_noise(seed, scale):
    cache = {}

    def lattice(ix, iy):
        key = (ix, iy)
        if key not in cache:
            cache[key] = random.Random(seed * 100003 + ix * 7919 + iy * 104729).random()
        return cache[key]

    def f(x, y):
        fx, fy = x / scale, y / scale
        ix, iy = int(math.floor(fx)), int(math.floor(fy))
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = lattice(ix, iy) + (lattice(ix + 1, iy) - lattice(ix, iy)) * tx
        b = lattice(ix, iy + 1) + (lattice(ix + 1, iy + 1) - lattice(ix, iy + 1)) * tx
        return a + (b - a) * ty

    return f
