"""Arte ambiental de The Seed: lo que se mueve por los escenarios.

Uso:  python3 tools/pixelart/ambient_art.py
Salida: game/assets/art/ambient/<kind>.png y game/assets/data/ambient/kinds.json.
Determinista. Autónomo (no importa generate.py): mismos colores y contorno que el resto del arte.

Hojas: filas = direcciones (right, down, up), columnas = cuadros de animación.
Izquierda = derecha volteada (lo hace el código). Sin ruedas en la Tierra: todo flota
(propulsores con brillo animado). Rovers solo en Luna y Marte (máquinas de exploración).
"""
from __future__ import annotations

import json
import math
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, "..", "..", "game"))
OUT = os.path.join(GAME, "assets", "art", "ambient")
MANIFEST = os.path.join(GAME, "assets", "data", "ambient", "kinds.json")
RES = "res://assets/art/ambient/"

OUTLINE = (34, 24, 42, 255)
CLEAR = (0, 0, 0, 0)


def hx(s: str, a: int = 255) -> tuple:
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def shade(c: tuple, f: float) -> tuple:
    return tuple(max(0, min(255, int(c[i] * f))) for i in range(3)) + (c[3],)


def mix(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


CYAN, GOLD, PINK, GREEN = hx("3de7c9"), hx("f4d35e"), hx("ff3ea5"), hx("7dff9a")
RED = hx("ff4a4a")
GLASS, GLASS_L = hx("2b5d7a"), hx("8fd8ef")
STEEL, STEEL_D, STEEL_L = hx("8d97a6"), hx("4f5868"), hx("c9d1db")
DARK = hx("232838")
WINDOW_LIT = hx("ffd98a")


class Canvas:
    def __init__(self, w: int, h: int):
        self.img = Image.new("RGBA", (w, h), CLEAR)
        self.px = self.img.load()
        self.w, self.h = w, h

    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and c[3] > 0:
            if c[3] < 255:
                o = self.px[x, y]
                a = c[3] / 255.0
                if o[3] == 0:
                    self.px[x, y] = c
                else:
                    self.px[x, y] = tuple(int(o[i] * (1 - a) + c[i] * a) for i in range(3)) + (max(o[3], c[3]),)
            else:
                self.px[x, y] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.put(x, y, c)

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x, y1, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.put(x, y, c)

    def rrect(self, x0, y0, x1, y1, r, c):
        """Rectángulo con esquinas redondeadas (r en px)."""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                dx = max(x0 + r - x, 0, x - (x1 - r))
                dy = max(y0 + r - y, 0, y - (y1 - r))
                if dx * dx + dy * dy <= r * r + 0.5:
                    self.put(x, y, c)


def outline(img: Image.Image, color=OUTLINE) -> Image.Image:
    w, h = img.size
    src = img.load()
    out = img.copy()
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] > 160:
                    dst[x, y] = color
                    break
    return out


def glow(cv: Canvas, cx, cy, r, c, strength=0.55):
    """Halo suave (sin contorno: se pinta después de outline)."""
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r
            if d < 1.0:
                a = int(255 * strength * (1 - d) ** 1.6)
                if a > 6:
                    cv.put(x, y, c[:3] + (a,))


def post(cv: Canvas, fn) -> Canvas:
    """Contorno del cuerpo y luego efectos luminosos (fn) encima, sin contorno."""
    img = outline(cv.img)
    out = Canvas(cv.w, cv.h)
    out.img = img
    out.px = img.load()
    if fn:
        fn(out)
    return out


def sheet(rows: list[list[Canvas]]) -> Image.Image:
    fw, fh = rows[0][0].w, rows[0][0].h
    cols = max(len(r) for r in rows)
    img = Image.new("RGBA", (fw * cols, fh * len(rows)), CLEAR)
    for ry, row in enumerate(rows):
        for cx, cv in enumerate(row):
            img.paste(cv.img, (cx * fw, ry * fh))
    return img


# ------------------------------------------------------------------ aerovehículos

def _thruster_side(cv, x, y, w, frame, color=CYAN):
    """Patín de propulsión bajo la carrocería (vista lateral) con chorro animado."""
    cv.rect(x, y, x + w, y + 1, STEEL_D)
    cv.hline(x + 1, x + w - 1, y, STEEL)


def _jets_side(cv, x, y, w, frame, color=CYAN):
    flick = 1 if frame % 2 else 0
    for i in range(x + 1, x + w, 3):
        cv.put(i, y + 2, color)
        cv.put(i, y + 3, color[:3] + (150,))
        if flick:
            cv.put(i, y + 4, color[:3] + (80,))
    glow(cv, x + w / 2, y + 3, w / 2 + 2, color, 0.35 + 0.15 * flick)


def hover_car_side(fw, fh, body, accent, length, frame, kind="taxi"):
    cv = Canvas(fw, fh)
    bob = frame % 2
    x0 = (fw - length) // 2
    x1 = x0 + length - 1
    base = fh - 7 - bob
    roof = base - (11 if kind != "van" else 12)
    # carrocería baja
    cv.rrect(x0, base - 5, x1, base, 2, body)
    cv.hline(x0 + 2, x1 - 2, base - 5, shade(body, 1.25))
    cv.hline(x0 + 1, x1 - 1, base, shade(body, 0.7))
    # cabina
    if kind == "van":
        cv.rrect(x0 + 2, roof, x1 - 3, base - 5, 2, body)
        cv.hline(x0 + 3, x1 - 4, roof, shade(body, 1.3))
        cv.rect(x1 - 8, roof + 2, x1 - 4, base - 6, GLASS)
        cv.put(x1 - 7, roof + 2, GLASS_L)
        # rótulo de reparto
        cv.rect(x0 + 5, roof + 3, x1 - 12, base - 7, shade(accent, 0.9))
        cv.hline(x0 + 6, x1 - 13, roof + 4, shade(accent, 1.3))
    else:
        # cabina de burbuja: techo del color del coche y cristal a los lados
        cv.rrect(x0 + 5, roof, x1 - 4, base - 4, 4, shade(body, 0.95))
        cv.hline(x0 + 8, x1 - 7, roof, shade(body, 1.3))
        cv.rrect(x0 + 7, roof + 2, x1 - 5, base - 6, 2, GLASS)
        cv.hline(x1 - 9, x1 - 7, roof + 2, GLASS_L)
        cv.put(x1 - 6, roof + 3, GLASS_L)
        cv.vline((x0 + x1) // 2, roof + 2, base - 6, shade(body, 0.8))
        # pasajero
        cv.rect((x0 + x1) // 2 - 4, base - 8, (x0 + x1) // 2 - 3, base - 6, hx("c08a60"))
        cv.put((x0 + x1) // 2 - 4, base - 9, hx("3a2a1a"))
        cv.rect((x0 + x1) // 2 + 3, base - 8, (x0 + x1) // 2 + 4, base - 6, hx("f0c8a0"))
        cv.put((x0 + x1) // 2 + 3, base - 9, hx("d8b060"))
    # franja lateral luminosa
    cv.hline(x0 + 2, x1 - 2, base - 3, accent)
    # patín de propulsión
    _thruster_side(cv, x0 + 3, base + 1, length - 7, frame)
    if kind == "taxi":
        cv.rect((x0 + x1) // 2 - 2, roof - 2, (x0 + x1) // 2 + 2, roof - 1, hx("2a2f40"))

    def lights(c):
        c.put(x1, base - 3, hx("fff6c8"))
        c.put(x1 + 1, base - 3, hx("fff6c8", 160))
        glow(c, x1 + 2, base - 3, 4, hx("fff6c8"), 0.5)
        c.put(x0, base - 3, RED)
        glow(c, x0 - 1, base - 3, 3, RED, 0.4)
        _jets_side(c, x0 + 3, base + 1, length - 7, frame)
        if kind == "taxi":
            c.hline((x0 + x1) // 2 - 1, (x0 + x1) // 2 + 1, roof - 2, hx("fff3a0"))
            glow(c, (x0 + x1) / 2, roof - 2, 3, GOLD, 0.4)
    return post(cv, lights)


def hover_car_front(fw, fh, body, accent, width, frame, kind="taxi", rear=False):
    """Vista de frente (down) o de espaldas (up): techo arriba, frontal abajo."""
    cv = Canvas(fw, fh)
    bob = frame % 2
    cx = fw // 2
    x0, x1 = cx - width // 2, cx + width // 2 - 1
    base = fh - 5 - bob
    top = base - (13 if kind != "van" else 15)
    # techo (visto desde arriba en 3/4), estrecho como una burbuja
    inset = 3 if kind == "taxi" else 1
    cv.rrect(x0 + inset, top, x1 - inset, top + 4, 2, shade(body, 1.15))
    cv.hline(x0 + inset + 2, x1 - inset - 2, top, shade(body, 1.35))
    if kind == "taxi":
        cv.rect(cx - 2, top - 2, cx + 1, top - 1, hx("2a2f40"))
    if kind == "van":
        cv.rect(x0 + 3, top + 1, x1 - 3, top + 3, shade(accent, 0.9))
    # parabrisas / luneta (cristal amplio con reflejo)
    cv.rrect(x0 + 1, top + 5, x1 - 1, top + 8, 1, GLASS if not rear else shade(GLASS, 0.75))
    cv.hline(x0 + 2, x0 + 4, top + 5, GLASS_L)
    cv.put(x0 + 2, top + 6, GLASS_L)
    if not rear:
        cv.rect(cx - 3, top + 7, cx - 2, top + 8, hx("c08a60"))
        cv.put(cx - 3, top + 6, hx("3a2a1a"))
    # frontal: capó y parrilla luminosa
    cv.rrect(x0, top + 9, x1, base, 2, body)
    cv.hline(x0 + 1, x1 - 1, top + 9, shade(body, 1.2))
    cv.hline(x0 + 1, x1 - 1, base, shade(body, 0.7))
    cv.hline(x0 + 3, x1 - 3, base - 2, shade(body, 0.6))
    cv.hline(x0 + 2, x1 - 2, top + 11, accent)
    _thruster_side(cv, x0 + 2, base + 1, width - 5, frame)
    lamp = RED if rear else hx("fff6c8")

    def lights(c):
        for lx in (x0 + 1, x1 - 1):
            c.put(lx, top + 10, lamp)
            c.put(lx + (1 if lx > cx else -1), top + 10, lamp[:3] + (150,))
            glow(c, lx, top + 10, 4, lamp, 0.45)
        if kind == "taxi":
            c.hline(cx - 1, cx, top - 2, hx("fff3a0"))
        _jets_side(c, x0 + 2, base + 1, width - 5, frame)
    return post(cv, lights)


def hover_vehicle(kind, body, accent, fw, fh, length, width):
    rows = [[hover_car_side(fw, fh, body, accent, length, f, kind) for f in range(2)],
            [hover_car_front(fw, fh, body, accent, width, f, kind) for f in range(2)],
            [hover_car_front(fw, fh, body, accent, width, f, kind, rear=True) for f in range(2)]]
    return sheet(rows)


def hover_bus_side(fw, fh, frame):
    cv = Canvas(fw, fh)
    bob = frame % 2
    x0, x1 = 3, fw - 4
    base = fh - 6 - bob
    top = base - 15
    body, trim = hx("3a6ea5"), hx("2a4b78")
    cv.rrect(x0, top, x1, base, 3, body)
    cv.hline(x0 + 3, x1 - 3, top, shade(body, 1.3))
    cv.rect(x0, base - 3, x1, base, trim)
    # ventanas con pasajeros
    rng = random.Random(7)
    for wx in range(x0 + 6, x1 - 8, 7):
        cv.rect(wx, top + 3, wx + 4, top + 8, WINDOW_LIT)
        if rng.random() < 0.7:
            skin = rng.choice([hx("f0c8a0"), hx("c08a60"), hx("7a4e30")])
            cv.rect(wx + 1, top + 6, wx + 2, top + 8, skin)
            cv.put(wx + 1, top + 5, rng.choice([hx("3a2a1a"), hx("d8b060"), hx("202020")]))
    # parabrisas delantero
    cv.rect(x1 - 5, top + 3, x1 - 2, top + 9, GLASS)
    cv.put(x1 - 4, top + 3, GLASS_L)
    cv.hline(x0 + 2, x1 - 2, base - 5, CYAN)
    _thruster_side(cv, x0 + 6, base + 1, 14, frame)
    _thruster_side(cv, x1 - 22, base + 1, 14, frame)

    def lights(c):
        # rótulo de línea
        for i, col in enumerate([GOLD, GOLD, GOLD]):
            c.put(x1 - 12 + i * 2, top + 1, col)
        c.put(x1, base - 4, hx("fff6c8"))
        glow(c, x1 + 2, base - 4, 4, hx("fff6c8"), 0.5)
        c.put(x0, base - 4, RED)
        _jets_side(c, x0 + 6, base + 1, 14, frame)
        _jets_side(c, x1 - 22, base + 1, 14, frame)
    return post(cv, lights)


def hover_bus():
    fw, fh = 64, 24
    body, accent = hx("3a6ea5"), CYAN
    rows = [[hover_bus_side(fw, fh, f) for f in range(2)],
            [hover_car_front(fw, fh, body, accent, 26, f, "van") for f in range(2)],
            [hover_car_front(fw, fh, body, accent, 26, f, "van", rear=True) for f in range(2)]]
    return sheet(rows)


# ------------------------------------------------------------------ drones

def quad_drone(fw, fh, frame, body, light_c, payload=None):
    cv = Canvas(fw, fh)
    cx = fw // 2
    bob = (0, 1, 1, 0)[frame % 4]
    cy = fh // 2 - 1 + bob
    # brazos
    cv.hline(cx - fw // 2 + 3, cx + fw // 2 - 4, cy - 2, STEEL_D)
    # cuerpo
    cv.rrect(cx - 4, cy - 3, cx + 3, cy + 2, 2, body)
    cv.hline(cx - 3, cx + 2, cy - 3, shade(body, 1.3))
    if payload:
        cv.rect(cx - 3, cy + 3, cx + 2, cy + 7, payload)
        cv.hline(cx - 3, cx + 2, cy + 3, shade(payload, 1.25))
        cv.vline(cx, cy + 3, cy + 7, shade(payload, 0.75))
    # hélices animadas
    span = [fw // 2 - 3, fw // 2 - 4]
    for side in (-1, 1):
        px = cx + side * span[0] - (1 if side > 0 else 0)
        blade = (frame % 2 == 0)
        if blade:
            cv.hline(px - 3, px + 3, cy - 4, hx("c9d1db", 200))
        else:
            cv.hline(px - 1, px + 1, cy - 4, hx("c9d1db", 200))
            cv.put(px, cy - 5, hx("c9d1db", 120))
        cv.rect(px, cy - 3, px, cy - 2, STEEL_D)

    def lights(c):
        c.put(cx, cy - 1, light_c)
        glow(c, cx, cy - 1, 4, light_c, 0.5 if frame % 2 else 0.3)
        c.put(cx - fw // 2 + 3, cy - 2, RED)
        c.put(cx + fw // 2 - 4, cy - 2, GREEN)
    return post(cv, lights)


def drone_sheet(fw, fh, body, light_c, payload=None):
    return sheet([[quad_drone(fw, fh, f, body, light_c, payload) for f in range(4)]])


def patrol_drone(frame):
    """Dron de mantenimiento: esfera con lente cian y aro de luz (sin armas)."""
    fw, fh = 20, 16
    cv = Canvas(fw, fh)
    bob = (0, 1, 1, 0)[frame % 4]
    cx, cy = 10, 7 + bob
    cv.ellipse(cx, cy, 5, 4.5, STEEL)
    cv.ellipse(cx - 1, cy - 1, 3, 2.5, STEEL_L)
    cv.hline(cx - 7, cx + 6, cy, STEEL_D)
    cv.rect(cx - 8, cy - 1, cx - 7, cy + 1, STEEL_D)
    cv.rect(cx + 6, cy - 1, cx + 7, cy + 1, STEEL_D)
    cv.rect(cx + 1, cy - 1, cx + 3, cy + 1, DARK)

    def lights(c):
        c.put(cx + 2, cy, CYAN)
        glow(c, cx + 2, cy, 4, CYAN, 0.6)
        ring = GOLD if frame in (1, 2) else shade(GOLD, 0.6)
        c.put(cx - 7, cy + 2, ring)
        c.put(cx + 6, cy + 2, ring)
        glow(c, cx, cy + 6, 4, CYAN, 0.25)
    return post(cv, lights)


# ------------------------------------------------------------------ robots de calle

def bot_cleaner(direction, frame):
    """Robot barrendero: chasis bajo blanco con franja de aviso, depósito, cepillos que giran."""
    fw, fh = 16, 16
    cv = Canvas(fw, fh)
    body, stripe, tank = hx("e9eef5"), hx("f4a23a"), hx("5aa88a")
    cx = 8
    spin = frame % 2
    brush, brush_d = hx("f4d35e"), hx("a07a30")
    if direction == "right":
        cv.rrect(2, 7, 12, 13, 2, body)
        cv.hline(3, 11, 7, hx("ffffff"))
        cv.hline(2, 12, 11, stripe)
        cv.rect(3, 3, 7, 7, tank)
        cv.hline(4, 6, 3, shade(tank, 1.3))
        cv.rect(9, 8, 11, 9, DARK)
        cv.ellipse(13, 13, 2, 1.5, brush_d)
        cv.put(12 + spin, 13, brush)
        cv.put(14 - spin, 12, brush)
        cv.hline(3, 11, 14, STEEL_D)
    elif direction == "down":
        cv.rrect(3, 5, 12, 13, 2, body)
        cv.rect(5, 2, 10, 6, tank)
        cv.hline(6, 9, 2, shade(tank, 1.3))
        cv.hline(3, 12, 11, stripe)
        cv.rect(6, 8, 9, 9, DARK)
        for bx in (2, 13):
            cv.ellipse(bx, 13, 2, 1.5, brush_d)
            cv.put(bx - 1 + spin, 13, brush)
            cv.put(bx + 1 - spin, 12, brush)
    else:
        cv.rrect(3, 5, 12, 13, 2, body)
        cv.rect(5, 3, 10, 9, tank)
        cv.hline(6, 9, 3, shade(tank, 1.3))
        cv.vline(7, 4, 8, shade(tank, 0.75))
        cv.hline(3, 12, 11, stripe)
        cv.hline(4, 11, 13, STEEL_D)

    def lights(c):
        beacon = (5, 2) if direction == "right" else (7, 1) if direction == "down" else (7, 2)
        c.put(beacon[0], beacon[1], GOLD if frame else shade(GOLD, 0.5))
        glow(c, beacon[0], beacon[1], 3, GOLD, 0.5 if frame else 0.15)
        if direction == "right":
            c.put(10, 8, CYAN)
            glow(c, 12, 9, 3, CYAN, 0.4)
        elif direction == "down":
            c.put(6, 8, CYAN)
            c.put(9, 8, CYAN)
        else:
            c.put(4, 12, RED)
            c.put(11, 12, RED)
    return post(cv, lights)


def bot_courier(direction, frame):
    """Robot mensajero flotante: cuerpo de cápsula, pantalla con cara amable, maletín."""
    fw, fh = 16, 20
    cv = Canvas(fw, fh)
    bob = frame % 2
    cx, top = 8, 2 + bob
    body = hx("e9eef5")
    cv.rrect(cx - 5, top, cx + 4, top + 12, 3, body)
    cv.hline(cx - 4, cx + 3, top, hx("ffffff"))
    cv.rect(cx - 5, top + 9, cx + 4, top + 12, shade(body, 0.82))
    if direction == "up":
        cv.rect(cx - 3, top + 3, cx + 2, top + 8, hx("2a4b78"))
        cv.rect(cx - 2, top + 4, cx + 1, top + 7, hx("3a6ea5"))
    else:
        face_x = cx - 4 if direction == "down" else cx - 1
        cv.rect(face_x, top + 3, face_x + 6 if direction == "down" else face_x + 4, top + 7, DARK)
        cv.rect(cx - 2, top + 13, cx + 1, top + 15, hx("b07a3a"))
    cv.ellipse(cx, fh - 2, 3, 1, hx("3de7c9", 90))

    def lights(c):
        if direction == "down":
            c.put(cx - 2, top + 5, CYAN)
            c.put(cx + 1, top + 5, CYAN)
            c.hline(cx - 1, cx, top + 6, CYAN)
        elif direction == "right":
            c.put(cx + 1, top + 5, CYAN)
            c.put(cx + 2, top + 6, CYAN)
        glow(c, cx, fh - 3, 4, CYAN, 0.45 if frame else 0.3)
    return post(cv, lights)


def bot_worker(direction, frame):
    """Robot de carga bípedo (Luna/Marte): torso amarillo de obra, piernas articuladas, caja."""
    fw, fh = 20, 24
    cv = Canvas(fw, fh)
    body, dark = hx("e0b23a"), hx("8a6420")
    cx = 10
    step = frame % 2
    # piernas
    for side, off in ((-1, step), (1, 1 - step)):
        lx = cx + side * 3 - (1 if side < 0 else 0)
        cv.rect(lx, 15, lx + 1, 21 - off, STEEL_D)
        cv.rect(lx - 1, 21 - off, lx + 2, 22 - off, DARK)
    # torso
    cv.rrect(cx - 6, 6, cx + 5, 15, 2, body)
    cv.hline(cx - 5, cx + 4, 6, shade(body, 1.25))
    for i in range(cx - 5, cx + 5, 3):
        cv.put(i, 14, DARK)
        cv.put(i + 1, 14, body)
    # cabeza
    cv.rect(cx - 3, 2, cx + 2, 6, STEEL)
    cv.hline(cx - 2, cx + 1, 2, STEEL_L)
    if direction != "up":
        cv.rect(cx - 2 if direction == "down" else cx, 3, cx + 1 if direction == "down" else cx + 2, 4, DARK)
    # caja en brazos
    if direction == "right":
        cv.rect(cx + 3, 9, cx + 8, 13, hx("b07a3a"))
        cv.hline(cx + 3, cx + 8, 9, hx("d49a50"))
    elif direction == "down":
        cv.rect(cx - 4, 10, cx + 3, 14, hx("b07a3a"))
        cv.hline(cx - 4, cx + 3, 10, hx("d49a50"))

    def lights(c):
        if direction == "down":
            c.put(cx - 1, 3, CYAN)
            c.put(cx, 3, CYAN)
        elif direction == "right":
            c.put(cx + 1, 3, CYAN)
        c.put(cx - 5, 8, hx("ff9a3a") if frame else shade(hx("ff9a3a"), 0.6))
        glow(c, cx - 5, 8, 3, hx("ff9a3a"), 0.4 if frame else 0.15)
    return post(cv, lights)


def bot_sheet(fn):
    return sheet([[fn(d, f) for f in range(2)] for d in ("right", "down", "up")])


# ------------------------------------------------------------------ rovers (Luna y Marte)

def rover_side(fw, fh, frame, mars):
    cv = Canvas(fw, fh)
    body = hx("e9eef5") if mars else hx("d8dde4")
    cx = fw // 2
    base = fh - 6
    # ruedas (rover científico)
    wheel = hx("3a3f4c")
    for wx in ((cx - 10, cx, cx + 9) if mars else (cx - 9, cx + 8)):
        cv.ellipse(wx, base + 2, 3, 3, wheel)
        cv.put(wx + (frame % 2) - 1, base + 1, hx("8a8f9c"))
    # suspensión
    cv.hline(cx - 11, cx + 10, base - 1, STEEL_D)
    # chasis
    cv.rrect(cx - 11, base - 7, cx + 10, base - 2, 1, body)
    cv.hline(cx - 10, cx + 9, base - 7, hx("ffffff"))
    if mars:
        # mástil con cámara (Perseverance)
        cv.vline(cx + 6, base - 16, base - 8, STEEL)
        cv.rect(cx + 4, base - 19, cx + 9, base - 16, STEEL_L)
        cv.rect(cx + 7, base - 18, cx + 8, base - 17, DARK)
        # generador
        cv.rect(cx - 13, base - 8, cx - 10, base - 4, hx("5a5f6c"))
        # brazo
        cv.hline(cx + 10, cx + 13, base - 4, STEEL)
    else:
        # rover lunar tripulado: asientos y antena de paraguas
        cv.rect(cx - 6, base - 11, cx - 3, base - 8, hx("8d6a4a"))
        cv.rect(cx + 1, base - 11, cx + 4, base - 8, hx("8d6a4a"))
        cv.vline(cx + 8, base - 16, base - 8, STEEL)
        cv.hline(cx + 6, cx + 10, base - 17, STEEL_L)
        cv.rect(cx - 10, base - 9, cx - 8, base - 8, GOLD)

    def lights(c):
        col = CYAN if mars else GOLD
        c.put(cx + 10, base - 5, col)
        glow(c, cx + 12, base - 5, 3, col, 0.4)
        if frame % 2:
            c.put(cx - 9, base - 9, RED)
    return post(cv, lights)


def rover_front(fw, fh, frame, mars, rear=False):
    cv = Canvas(fw, fh)
    body = hx("e9eef5") if mars else hx("d8dde4")
    cx = fw // 2
    base = fh - 6
    wheel = hx("3a3f4c")
    for wx in (cx - 8, cx + 7):
        cv.rect(wx - 1, base - 1, wx + 1, base + 4, wheel)
    cv.rect(cx - 8, base - 12, cx + 7, base - 9, shade(body, 1.05))
    cv.hline(cx - 7, cx + 6, base - 12, hx("ffffff"))
    for gx in range(cx - 6, cx + 6, 3):
        cv.vline(gx, base - 11, base - 10, hx("3a6ea5") if not mars else hx("6a7484"))
    cv.rect(cx - 8, base - 9, cx + 7, base - 1, body)
    cv.hline(cx - 7, cx + 6, base - 9, shade(body, 0.92))
    cv.rect(cx - 6, base - 6, cx + 5, base - 3, shade(body, 0.8))
    if mars:
        cv.vline(cx + 4, base - 17, base - 9, STEEL)
        cv.rect(cx + 2, base - 20, cx + 6, base - 17, STEEL_L)
    else:
        cv.vline(cx + 5, base - 15, base - 9, STEEL)
        cv.hline(cx + 3, cx + 7, base - 16, STEEL_L)

    def lights(c):
        col = RED if rear else (CYAN if mars else GOLD)
        for lx in (cx - 6, cx + 5):
            c.put(lx, base - 5, col)
            glow(c, lx, base - 5, 3, col, 0.4)
    return post(cv, lights)


def rover(mars):
    fw, fh = 32, 24 if mars else 20
    return sheet([[rover_side(fw, fh, f, mars) for f in range(2)],
                  [rover_front(fw, fh, f, mars) for f in range(2)],
                  [rover_front(fw, fh, f, mars, rear=True) for f in range(2)]])


# ------------------------------------------------------------------ tranvía maglev

def maglev_tram(frame):
    fw, fh = 112, 28
    cv = Canvas(fw, fh)
    base = fh - 6
    top = base - 15
    body, trim = hx("e9eef5"), hx("2a4b78")
    rng = random.Random(11)
    cars = [(2, 54), (57, 109)]
    for i, (x0, x1) in enumerate(cars):
        nose = i == 1
        cv.rrect(x0, top, x1, base, 3, body)
        if nose:
            # morro aerodinámico
            for k in range(6):
                cv.vline(x1 - k, top + 6 - k if k < 6 else top, base, CLEAR)
            for k in range(6):
                cv.vline(x1 - 5 + k, top + k + 1, base, body)
            cv.rect(x1 - 9, top + 3, x1 - 4, top + 7, GLASS)
            cv.put(x1 - 8, top + 3, GLASS_L)
        cv.hline(x0 + 3, x1 - 3, top, hx("ffffff"))
        cv.rect(x0, base - 3, x1, base, trim)
        cv.hline(x0 + 1, x1 - 1, base - 4, CYAN)
        for wx in range(x0 + 4, x1 - (12 if nose else 5), 6):
            cv.rect(wx, top + 3, wx + 3, top + 8, WINDOW_LIT)
            if rng.random() < 0.65:
                skin = rng.choice([hx("f0c8a0"), hx("c08a60"), hx("7a4e30"), hx("e0b080")])
                cv.rect(wx + 1, top + 6, wx + 2, top + 8, skin)
                cv.put(wx + 1, top + 5, rng.choice([hx("3a2a1a"), hx("d8b060"), hx("202020"), hx("a03030")]))
        # puerta
        dx = (x0 + x1) // 2 - 6
        cv.rect(dx, top + 3, dx + 3, base - 4, shade(body, 0.75))
        cv.vline(dx + 1, top + 3, base - 4, shade(body, 0.6))
    # enganche
    cv.rect(54, base - 6, 57, base - 3, STEEL_D)

    def lights(c):
        flick = frame % 2
        for x0, x1 in cars:
            for gx in range(x0 + 4, x1 - 3, 4):
                c.put(gx, base + 2, CYAN)
                if flick:
                    c.put(gx, base + 3, CYAN[:3] + (120,))
            glow(c, (x0 + x1) / 2, base + 3, (x1 - x0) / 2, CYAN, 0.18)
        c.put(108, base - 5, hx("fff6c8"))
        glow(c, 110, base - 5, 5, hx("fff6c8"), 0.55)
        c.put(3, base - 5, RED)
        # logo de la línea
        c.rect(20, top + 1, 26, top + 1, GOLD)
    return post(cv, lights)


# ------------------------------------------------------------------ naves del cielo

def _engine_flame(c, x, y, length, frame, col=CYAN):
    ln = length + (2 if frame % 2 else 0)
    for i in range(ln):
        a = int(255 * (1 - i / ln))
        c.put(x - i, y, col[:3] + (a,))
        if i < ln - 2:
            c.put(x - i, y - 1, col[:3] + (a // 2,))
            c.put(x - i, y + 1, col[:3] + (a // 2,))
    glow(c, x - 1, y, 4, col, 0.55)


def sky_hopper(frame):
    fw, fh = 48, 24
    cv = Canvas(fw, fh)
    body = hx("d8dde4")
    cy = 12
    cv.rrect(10, cy - 4, 40, cy + 3, 3, body)
    for k in range(6):
        cv.vline(40 + k, cy - 3 + k // 2, cy + 3 - k // 3, body)
    cv.hline(11, 39, cy - 4, hx("ffffff"))
    cv.rect(10, cy + 1, 40, cy + 3, shade(body, 0.75))
    cv.rect(30, cy - 3, 38, cy - 1, GLASS)
    cv.hline(31, 33, cy - 3, GLASS_L)
    # alas
    for k in range(6):
        cv.hline(16 + k, 28, cy + 4 + k // 2, shade(body, 0.85 - k * 0.03))
    cv.rect(8, cy - 2, 11, cy + 2, STEEL_D)
    cv.hline(12, 38, cy, PINK)

    def lights(c):
        _engine_flame(c, 8, cy, 6, frame)
        c.put(46, cy, hx("fff6c8"))
        c.put(17, cy + 7, RED if frame else shade(RED, 0.5))
        for wx in range(14, 28, 3):
            c.put(wx, cy - 2, WINDOW_LIT)
    return post(cv, lights)


def sky_shuttle(frame):
    fw, fh = 96, 36
    cv = Canvas(fw, fh)
    body, dark = hx("e9eef5"), hx("8d97a6")
    cy = 17
    # fuselaje
    cv.rrect(14, cy - 7, 78, cy + 6, 5, body)
    for k in range(12):
        cv.vline(78 + k, cy - 6 + k // 2, cy + 6 - k // 3, body)
    cv.hline(16, 76, cy - 7, hx("ffffff"))
    cv.rect(14, cy + 3, 80, cy + 6, dark)
    # cabina
    cv.rect(76, cy - 5, 85, cy - 2, GLASS)
    cv.hline(77, 80, cy - 5, GLASS_L)
    # ventanillas
    for wx in range(22, 72, 5):
        cv.rect(wx, cy - 3, wx + 2, cy - 1, WINDOW_LIT)
    # franjas y logotipo
    cv.hline(16, 76, cy + 1, CYAN)
    cv.hline(16, 76, cy + 2, shade(CYAN, 0.6))
    # aletas y alas
    for k in range(9):
        cv.hline(18 + k, 30, cy - 8 - k, shade(body, 0.9))
    for k in range(7):
        cv.hline(30 + k, 58, cy + 7 + k // 2, shade(dark, 1.0 - k * 0.05))
    # motores
    cv.rect(8, cy - 5, 15, cy - 1, dark)
    cv.rect(8, cy + 1, 15, cy + 5, dark)

    def lights(c):
        _engine_flame(c, 7, cy - 3, 9, frame)
        _engine_flame(c, 7, cy + 3, 9, frame)
        c.put(27, cy - 17, RED if frame else shade(RED, 0.4))
        glow(c, 27, cy - 17, 3, RED, 0.5 if frame else 0.1)
        c.put(89, cy, hx("fff6c8"))
        glow(c, 91, cy, 5, hx("fff6c8"), 0.5)
        c.put(56, cy + 10, GREEN)
    return post(cv, lights)


def sky_freighter(frame):
    fw, fh = 160, 52
    cv = Canvas(fw, fh)
    hull, dark, panel = hx("8d97a6"), hx("4f5868"), hx("6a7484")
    cy = 26
    # casco principal (bloque industrial)
    cv.rrect(20, cy - 12, 130, cy + 10, 3, hull)
    cv.hline(22, 128, cy - 12, hx("c9d1db"))
    cv.rect(20, cy + 6, 130, cy + 10, dark)
    # módulos de carga (contenedores de colores)
    rng = random.Random(5)
    for i, x in enumerate(range(28, 118, 15)):
        col = rng.choice([hx("c0603a"), hx("3a6ea5"), hx("6aa04a"), hx("e0b23a"), hx("8a4aa0")])
        cv.rect(x, cy - 9, x + 12, cy + 3, col)
        cv.hline(x, x + 12, cy - 9, shade(col, 1.3))
        cv.vline(x + 6, cy - 9, cy + 3, shade(col, 0.7))
        cv.rect(x + 2, cy - 7, x + 4, cy - 6, shade(col, 0.6))
    # puente de mando
    cv.rrect(128, cy - 10, 148, cy + 6, 4, panel)
    for k in range(6):
        cv.vline(148 + k, cy - 7 + k, cy + 5 - k // 2, panel)
    cv.rect(138, cy - 7, 150, cy - 3, GLASS)
    cv.hline(139, 143, cy - 7, GLASS_L)
    # torre y antenas
    cv.rect(118, cy - 20, 126, cy - 12, panel)
    cv.vline(122, cy - 25, cy - 20, STEEL)
    cv.hline(120, 124, cy - 25, STEEL_L)
    # motores
    for ey in (cy - 8, cy, cy + 7):
        cv.rect(10, ey - 2, 21, ey + 2, dark)
        cv.hline(10, 21, ey - 2, panel)
    cv.hline(22, 128, cy + 4, GOLD)

    def lights(c):
        for ey in (cy - 8, cy, cy + 7):
            _engine_flame(c, 9, ey, 12, frame, hx("ffb070"))
        c.put(122, cy - 26, RED if frame else shade(RED, 0.4))
        glow(c, 122, cy - 26, 4, RED, 0.6 if frame else 0.1)
        for wx in range(130, 136, 2):
            c.put(wx, cy - 4, WINDOW_LIT)
        c.put(154, cy, hx("fff6c8"))
        glow(c, 156, cy, 6, hx("fff6c8"), 0.5)
    return post(cv, lights)


def single_row(fn, n):
    return sheet([[fn(f) for f in range(n)]])


# ------------------------------------------------------------------ manifiesto

def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    dirs3 = {"right": 0, "down": 1, "up": 2}
    beam = lambda c, s=1.2, e=0.7: {"color": c, "offset": [0, -8], "scale": s, "energy": e}
    kinds = {}

    def emit(kind, img, frame, frames, fps, rows=None, shadow=None, light=None):
        img.save(os.path.join(OUT, kind + ".png"))
        d = {"texture": RES + kind + ".png", "frame": list(frame), "frames": frames, "fps": fps,
             "rows": rows or {"right": 0}}
        if shadow:
            d["shadow"] = list(shadow)
        if light:
            d["light"] = light
        kinds[kind] = d

    emit("hover_taxi", hover_vehicle("taxi", hx("f4c430"), CYAN, 32, 20, 28, 18), (32, 20), 2, 6,
         dirs3, (24, 6), beam("#3de7c9"))
    emit("hover_van", hover_vehicle("van", hx("dfe4ea"), PINK, 36, 22, 32, 20), (36, 22), 2, 6,
         dirs3, (28, 6), beam("#ff3ea5"))
    emit("hover_bus", hover_bus(), (64, 24), 2, 5, dirs3, (52, 8), beam("#3de7c9", 1.8, 0.8))
    emit("patrol_drone", single_row(patrol_drone, 4), (20, 16), 4, 8, None, (12, 4), beam("#3de7c9", 0.9, 0.7))
    emit("cargo_drone", drone_sheet(24, 20, hx("dfe4ea"), GOLD, hx("b07a3a")), (24, 20), 4, 14, None, (16, 5),
         beam("#f4d35e", 0.8, 0.6))
    emit("delivery_drone", drone_sheet(16, 14, hx("3de7c9"), PINK, hx("d49a50")), (16, 14), 4, 14, None, (10, 3),
         beam("#ff3ea5", 0.6, 0.5))
    emit("bot_cleaner", bot_sheet(bot_cleaner), (16, 16), 2, 6, dirs3, None, beam("#3de7c9", 0.7, 0.5))
    emit("bot_courier", bot_sheet(bot_courier), (16, 20), 2, 4, dirs3, (10, 3), beam("#3de7c9", 0.7, 0.5))
    emit("bot_worker", bot_sheet(bot_worker), (20, 24), 2, 4, dirs3, None, beam("#ffb070", 0.7, 0.5))
    emit("rover_moon", rover(False), (32, 20), 2, 4, dirs3, None, beam("#f4d35e", 1.0, 0.6))
    emit("rover_mars", rover(True), (32, 24), 2, 4, dirs3, None, beam("#3de7c9", 1.0, 0.6))
    emit("maglev_tram", single_row(maglev_tram, 2), (112, 28), 2, 6, None, None,
         {"color": "#3de7c9", "offset": [0, -4], "scale": 3.0, "energy": 0.7})
    emit("sky_hopper", single_row(sky_hopper, 2), (48, 24), 2, 8, None, (30, 6))
    emit("sky_shuttle", single_row(sky_shuttle, 2), (96, 36), 2, 8, None, (64, 10))
    emit("sky_freighter", single_row(sky_freighter, 2), (160, 52), 2, 6, None, (110, 14))

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(kinds, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"ambient_art: {len(kinds)} kinds → {OUT}")


if __name__ == "__main__":
    main()
