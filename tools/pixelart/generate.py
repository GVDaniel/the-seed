"""Generador de pixel art propio de The Seed.

Uso:  python3 tools/pixelart/generate.py
Salida: game/assets/art/** (PNG). Determinista (semillas fijas).

Estilo: 16 px por tile, contorno oscuro de 1 px, paleta limitada,
luz desde arriba-izquierda. Coherente con Kenney Tiny Town (CC0).
"""
from __future__ import annotations

import colorsys
import math
import os
import random

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.normpath(os.path.join(HERE, "..", "..", "game"))
ART = os.path.join(GAME, "assets", "art")

OUTLINE = (34, 24, 42, 255)
CLEAR = (0, 0, 0, 0)

BAYER4 = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]


def hx(s: str, a: int = 255) -> tuple:
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def shade(c: tuple, f: float) -> tuple:
    return (
        max(0, min(255, int(c[0] * f))),
        max(0, min(255, int(c[1] * f))),
        max(0, min(255, int(c[2] * f))),
        c[3],
    )


def save(img: Image.Image, *parts: str) -> None:
    path = os.path.join(ART, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def add_outline(img: Image.Image, color: tuple = OUTLINE) -> Image.Image:
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
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3] != 0 and src[nx, ny] != color:
                    dst[x, y] = color
                    break
    return out


class Canvas:
    def __init__(self, w: int, h: int):
        self.img = Image.new("RGBA", (w, h), CLEAR)
        self.px = self.img.load()
        self.w, self.h = w, h

    def put(self, x: int, y: int, c: tuple) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = c

    def rect(self, x0: int, y0: int, x1: int, y1: int, c: tuple) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def hline(self, x0: int, x1: int, y: int, c: tuple) -> None:
        self.rect(x0, y, x1, y, c)

    def vline(self, x: int, y0: int, y1: int, c: tuple) -> None:
        self.rect(x, y0, x, y1, c)

    def disc(self, cx: float, cy: float, r: float, c: tuple) -> None:
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    self.put(x, y, c)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, c: tuple) -> None:
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.put(x, y, c)

    def get(self, x: int, y: int) -> tuple:
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return CLEAR


# ---------------------------------------------------------------- personajes

CHARACTERS = {
    "andres": {
        "hair": hx("6b3f2a"), "skin": hx("e3a878"), "cloth": hx("e8eef5"),
        "accent": hx("3de7c9"), "pants": hx("3a4a6b"), "boots": hx("2a3048"),
        "style": "short", "pack": hx("f4d35e"),
    },
    "lucia": {
        "hair": hx("ece8e0"), "skin": hx("d39a72"), "cloth": hx("6f9a4c"),
        "accent": hx("f4d35e"), "pants": hx("7a5a8c"), "boots": hx("4a3040"),
        "style": "bun", "skirt": True,
    },
    "vega": {
        "hair": hx("2a2230"), "skin": hx("b9825e"), "cloth": hx("7e5cb8"),
        "accent": hx("3de7c9"), "pants": hx("3b3350"), "boots": hx("221c30"),
        "style": "bob", "glasses": hx("3de7c9"),
    },
    "kai": {
        "hair": hx("1f1a24"), "skin": hx("eab98e"), "cloth": hx("f08a2c"),
        "accent": hx("3de7c9"), "pants": hx("c06a20"), "boots": hx("3a3030"),
        "style": "spiky",
    },
    "osei": {
        "hair": hx("1a1418"), "skin": hx("7c4b30"), "cloth": hx("b5532f"),
        "accent": hx("f4d35e"), "pants": hx("7a3420"), "boots": hx("2a1a18"),
        "style": "braids",
    },
    # --- Vecinos (mundo posapocalíptico cyberpunk) ---
    "ramiro": {
        "hair": hx("b8b8c0"), "skin": hx("c48a64"), "cloth": hx("2f5a48"),
        "accent": hx("7dff9a"), "pants": hx("2a2a36"), "boots": hx("1a1a22"),
        "style": "short", "implant": hx("7dff9a"),
    },
    "mateo": {
        "hair": hx("2a62c8"), "skin": hx("e0a070"), "cloth": hx("ff3ea5"),
        "accent": hx("3de7c9"), "pants": hx("2a3048"), "boots": hx("e8eef5"),
        "style": "spiky",
    },
    "amaru": {
        "hair": hx("15121a"), "skin": hx("a86a44"), "cloth": hx("e8c040"),
        "accent": hx("2a2a36"), "pants": hx("6a5a20"), "boots": hx("2a2a22"),
        "style": "braids", "visor": hx("3de7c9"),
    },
    "zoe": {
        "hair": hx("ff3ea5"), "skin": hx("f0c090"), "cloth": hx("6a4a32"),
        "accent": hx("f4d35e"), "pants": hx("3a3040"), "boots": hx("201820"),
        "style": "mohawk", "implant": hx("ff3ea5"),
    },
    "lupe": {
        "hair": hx("9a4ae0"), "skin": hx("d8a07a"), "cloth": hx("1e1a2a"),
        "accent": hx("ff3ea5"), "pants": hx("2a2240"), "boots": hx("15121e"),
        "style": "long", "implant": hx("3de7c9"),
    },
    "ingrid": {
        "hair": hx("f0f0e8"), "skin": hx("f2c8a8"), "cloth": hx("e07a2a"),
        "accent": hx("2a2a36"), "pants": hx("b05a1a"), "boots": hx("2a2020"),
        "style": "bob", "visor": hx("f4d35e"),
    },
    "tomas": {
        "hair": hx("3a2a20"), "skin": hx("c89070"), "cloth": hx("8a909c"),
        "accent": hx("3de7c9"), "pants": hx("5a606c"), "boots": hx("2a2e36"),
        "style": "short", "implant": hx("3de7c9"),
    },
    "amina": {
        "hair": hx("15121a"), "skin": hx("6a4028"), "cloth": hx("2a9a90"),
        "accent": hx("f4d35e"), "pants": hx("1e4a50"), "boots": hx("1a2228"),
        "style": "bun", "glasses": hx("f4d35e"),
    },
    "chen": {
        "hair": hx("15121a"), "skin": hx("eac498"), "cloth": hx("c8302a"),
        "accent": hx("f4d35e"), "pants": hx("2a2a36"), "boots": hx("1a1a20"),
        "style": "short", "implant": hx("f4d35e"),
    },
    "rosa": {
        "hair": hx("d8402a"), "skin": hx("e8b088"), "cloth": hx("3a5a8a"),
        "accent": hx("ff3ea5"), "pants": hx("2a3a5a"), "boots": hx("2a1a18"),
        "style": "long",
    },
    "yusuf": {
        "hair": hx("6a6a70"), "skin": hx("8a5a3a"), "cloth": hx("3a6ac8"),
        "accent": hx("f4d35e"), "pants": hx("2a3048"), "boots": hx("1a1a22"),
        "style": "short", "glasses": hx("e8eef5"),
    },
    "nia": {
        "hair": hx("3de7c9"), "skin": hx("7a4a30"), "cloth": hx("f08a2c"),
        "accent": hx("e8eef5"), "pants": hx("8a3a20"), "boots": hx("e8eef5"),
        "style": "braids",
    },
    "bruno": {
        "hair": hx("4ae070"), "skin": hx("d0a080"), "cloth": hx("5a5e68"),
        "accent": hx("f08a2c"), "pants": hx("3a3e48"), "boots": hx("1a1c22"),
        "style": "mohawk", "visor": hx("f08a2c"),
    },
}

DIRS = ["down", "left", "right", "up"]


def _hair_front(cv: Canvas, cfg: dict, back: bool) -> None:
    h = cfg["hair"]
    hd = shade(h, 0.78)
    style = cfg["style"]
    if style == "mohawk":
        stubble = shade(cfg["skin"], 0.72)
        cv.rect(4, 2, 11, 3, stubble)
        if back:
            cv.rect(4, 4, 11, 6, stubble)
        cv.rect(6, -1, 9, 4 if not back else 9, h)
        cv.vline(9, -1, 4 if not back else 9, hd)
        return
    cv.rect(4, 1, 11, 1, h)
    cv.rect(3, 2, 12, 4, h)
    cv.hline(10, 12, 4, hd)
    if back:
        cv.rect(3, 5, 12, 9, h)
        cv.rect(9, 5, 12, 9, hd)
        cv.hline(4, 11, 10, hd)
    if style == "short":
        if not back:
            cv.vline(3, 5, 6, h)
            cv.vline(12, 5, 6, hd)
            for x in (4, 5, 7, 10, 11):
                cv.put(x, 5, h)
    elif style == "bun":
        cv.rect(6, 0, 9, 0, h)
        cv.rect(5, -1, 10, 0, h)
        if not back:
            cv.vline(3, 5, 8, h)
            cv.vline(12, 5, 8, hd)
            cv.hline(4, 11, 5, h)
            cv.put(7, 5, cfg["skin"])
            cv.put(8, 5, cfg["skin"])
    elif style == "bob":
        cv.vline(2, 4, 10, h)
        cv.vline(13, 4, 10, hd)
        cv.vline(3, 5, 10, h)
        cv.vline(12, 5, 10, hd)
        if not back:
            cv.hline(4, 11, 5, h)
            cv.put(8, 5, cfg["skin"])
        else:
            cv.rect(2, 5, 13, 10, h)
            cv.rect(9, 5, 13, 10, hd)
    elif style == "spiky":
        for x in (4, 7, 10):
            cv.put(x, 0, h)
            cv.put(x + 1, 0, h)
        cv.hline(3, 12, 5, cfg["accent"])
        if not back:
            cv.vline(3, 6, 6, h)
            cv.vline(12, 6, 6, hd)
    elif style == "long":
        cv.vline(2, 4, 14, h)
        cv.vline(13, 4, 14, hd)
        cv.vline(3, 5, 13, h)
        cv.vline(12, 5, 13, hd)
        if not back:
            cv.hline(4, 11, 5, h)
            cv.put(6, 5, cfg["skin"])
            cv.put(7, 5, cfg["skin"])
        else:
            cv.rect(2, 5, 13, 14, h)
            cv.rect(9, 5, 13, 14, hd)
    elif style == "braids":
        if not back:
            cv.hline(4, 11, 5, h)
            cv.put(7, 5, cfg["skin"])
        for i, y in enumerate(range(5, 15)):
            c = h if i % 2 == 0 else cfg["accent"] if i == 9 else hd
            cv.put(2, y, c)
            cv.put(13, y, c)


def _legs(cv: Canvas, cfg: dict, x_left: int, x_right: int, frame: int, y_top: int = 18) -> None:
    p, b = cfg["pants"], cfg["boots"]
    if cfg.get("skirt"):
        cv.rect(4, 16, 11, 19, p)
        cv.hline(4, 11, 19, shade(p, 0.8))
        y_top = 20
    lift_l = 1 if frame == 1 else 0
    lift_r = 1 if frame == 2 else 0
    bottom = 21
    cv.rect(x_left, y_top, x_left + 1, bottom - 1 - lift_l, p)
    cv.rect(x_left, bottom - lift_l, x_left + 1, bottom - lift_l, b)
    cv.rect(x_right, y_top, x_right + 1, bottom - 1 - lift_r, shade(p, 0.85))
    cv.rect(x_right, bottom - lift_r, x_right + 1, bottom - lift_r, b)


def char_front(cfg: dict, frame: int) -> Image.Image:
    cv = Canvas(16, 24)
    s, c, a = cfg["skin"], cfg["cloth"], cfg["accent"]
    cd = shade(c, 0.8)
    _legs(cv, cfg, 5, 9, frame)
    # torso
    cv.rect(5, 12, 10, 17, c)
    cv.vline(10, 12, 17, cd)
    cv.hline(5, 10, 17, shade(c, 0.6))
    cv.vline(7, 12, 16, a)
    # brazos
    sway_l = -1 if frame == 1 else 0
    sway_r = -1 if frame == 2 else 0
    cv.rect(4, 12, 4, 15 + sway_l, c)
    cv.put(4, 16 + sway_l, s)
    cv.rect(11, 12, 11, 15 + sway_r, cd)
    cv.put(11, 16 + sway_r, shade(s, 0.85))
    # cabeza
    cv.rect(4, 3, 11, 10, s)
    cv.rect(3, 4, 12, 9, s)
    cv.vline(12, 4, 9, shade(s, 0.88))
    cv.put(6, 7, OUTLINE)
    cv.put(6, 8, OUTLINE)
    cv.put(9, 7, OUTLINE)
    cv.put(9, 8, OUTLINE)
    cv.put(5, 9, shade(hx("e86a6a"), 1.0))
    cv.put(10, 9, shade(hx("e86a6a"), 0.9))
    if cfg.get("glasses"):
        g = cfg["glasses"]
        cv.hline(5, 7, 6, g)
        cv.hline(8, 10, 6, g)
    if cfg.get("visor"):
        v = cfg["visor"]
        cv.rect(4, 7, 11, 8, v)
        cv.put(5, 7, hx("ffffff"))
    if cfg.get("implant"):
        cv.put(11, 6, cfg["implant"])
        cv.put(11, 7, shade(cfg["implant"], 0.7))
    _hair_front(cv, cfg, back=False)
    return add_outline(cv.img)


def char_back(cfg: dict, frame: int) -> Image.Image:
    cv = Canvas(16, 24)
    s, c = cfg["skin"], cfg["cloth"]
    cd = shade(c, 0.8)
    _legs(cv, cfg, 5, 9, frame)
    cv.rect(5, 12, 10, 17, cd)
    cv.vline(5, 12, 17, c)
    sway_l = -1 if frame == 2 else 0
    sway_r = -1 if frame == 1 else 0
    cv.rect(4, 12, 4, 15 + sway_l, c)
    cv.put(4, 16 + sway_l, s)
    cv.rect(11, 12, 11, 15 + sway_r, cd)
    cv.put(11, 16 + sway_r, shade(s, 0.85))
    if "pack" in cfg:
        pk = cfg["pack"]
        cv.rect(5, 11, 10, 16, pk)
        cv.rect(5, 11, 10, 11, shade(pk, 0.7))
        cv.rect(5, 16, 10, 16, shade(pk, 0.7))
        cv.vline(5, 11, 16, shade(pk, 0.7))
        cv.vline(10, 11, 16, shade(pk, 0.7))
        cv.put(7, 13, hx("4caf50"))
        cv.put(8, 13, hx("4caf50"))
        cv.put(7, 14, hx("2e7d32"))
    cv.rect(4, 3, 11, 10, s)
    cv.rect(3, 4, 12, 9, s)
    _hair_front(cv, cfg, back=True)
    return add_outline(cv.img)


def char_side(cfg: dict, frame: int) -> Image.Image:
    """Mirando a la izquierda."""
    cv = Canvas(16, 24)
    s, c, a = cfg["skin"], cfg["cloth"], cfg["accent"]
    cd = shade(c, 0.8)
    p, b = cfg["pants"], cfg["boots"]
    if cfg.get("skirt"):
        cv.rect(5, 16, 10, 19, p)
        cv.hline(5, 10, 19, shade(p, 0.8))
        legs_top = 20
    else:
        legs_top = 18
    if frame == 0:
        cv.rect(6, legs_top, 9, 20, p)
        cv.rect(6, 21, 9, 21, b)
        cv.put(5, 21, b)
    else:
        front_x, back_x = (5, 9) if frame == 1 else (6, 8)
        cv.rect(back_x, legs_top, back_x + 1, 20, shade(p, 0.8))
        cv.rect(back_x, 21, back_x + 1, 21, b)
        cv.rect(front_x, legs_top, front_x + 1, 20, p)
        cv.rect(front_x - 1, 21, front_x + 1, 21, b)
    cv.rect(6, 12, 9, 17, c)
    cv.vline(9, 12, 17, cd)
    cv.hline(6, 9, 17, shade(c, 0.6))
    if "pack" in cfg:
        pk = cfg["pack"]
        cv.rect(10, 11, 11, 16, pk)
        cv.vline(11, 11, 16, shade(pk, 0.7))
    arm_dx = {0: 0, 1: -1, 2: 1}[frame]
    cv.rect(7 + arm_dx, 12, 8 + arm_dx, 15, cd)
    cv.vline(7 + arm_dx, 12, 15, a)
    cv.rect(7 + arm_dx, 16, 8 + arm_dx, 16, s)
    # cabeza
    cv.rect(4, 3, 11, 10, s)
    cv.rect(3, 4, 11, 9, s)
    cv.put(4, 7, OUTLINE)
    cv.put(4, 8, OUTLINE)
    cv.put(3, 9, shade(hx("e86a6a"), 1.0))
    if cfg.get("glasses"):
        cv.hline(3, 5, 6, cfg["glasses"])
    if cfg.get("visor"):
        cv.rect(3, 7, 6, 8, cfg["visor"])
    h = cfg["hair"]
    hd = shade(h, 0.78)
    style = cfg["style"]
    if style == "mohawk":
        cv.rect(4, 2, 11, 4, shade(s, 0.72))
        cv.rect(5, -1, 11, 2, h)
        cv.rect(9, 0, 11, 3, hd)
        if cfg.get("implant"):
            cv.put(9, 6, cfg["implant"])
        return add_outline(cv.img)
    cv.rect(4, 1, 11, 1, h)
    cv.rect(3, 2, 12, 4, h)
    cv.rect(7, 4, 12, 9, h)
    cv.rect(9, 5, 12, 9, hd)
    cv.put(6, 5, h)
    cv.put(7, 6, s)
    if cfg.get("implant"):
        cv.put(6, 6, cfg["implant"])
    if style == "long":
        cv.rect(7, 4, 12, 14, h)
        cv.rect(10, 5, 12, 14, hd)
    if style == "bun":
        cv.rect(10, 0, 13, 2, h)
    elif style == "bob":
        cv.rect(7, 5, 12, 10, h)
        cv.rect(10, 5, 12, 10, hd)
    elif style == "spiky":
        for x in (5, 8, 11):
            cv.put(x, 0, h)
        cv.hline(3, 12, 5, cfg["accent"])
    elif style == "braids":
        for i, y in enumerate(range(5, 15)):
            cv.put(12, y, h if i % 2 == 0 else hd)
    return add_outline(cv.img)


def character_sheet(cfg: dict) -> Image.Image:
    """4 filas (abajo, izquierda, derecha, arriba) × 3 columnas (quieto, paso A, paso B)."""
    sheet = Image.new("RGBA", (16 * 3, 24 * 4), CLEAR)
    for f in range(3):
        sheet.paste(char_front(cfg, f), (f * 16, 0))
        left = char_side(cfg, f)
        sheet.paste(left, (f * 16, 24))
        sheet.paste(left.transpose(Image.FLIP_LEFT_RIGHT), (f * 16, 48))
        sheet.paste(char_back(cfg, f), (f * 16, 72))
    return sheet


# ------------------------------------------------------------------ retratos

def portrait(cfg: dict) -> Image.Image:
    cv = Canvas(32, 32)
    s, c, a, h = cfg["skin"], cfg["cloth"], cfg["accent"], cfg["hair"]
    sd = shade(s, 0.85)
    hd = shade(h, 0.75)
    style = cfg["style"]
    # hombros
    cv.ellipse(16, 33, 13, 7, c)
    cv.ellipse(20, 34, 9, 6, shade(c, 0.82))
    cv.rect(14, 24, 18, 27, sd)
    cv.vline(16, 27, 31, a)
    if style == "braids":
        for y in range(12, 30):
            col = h if (y // 2) % 2 == 0 else hd
            cv.rect(4, y, 5, y, col)
            cv.rect(26, y, 27, y, col)
    if style == "bob":
        cv.rect(5, 10, 26, 25, h)
        cv.rect(20, 10, 26, 25, hd)
    if style == "long":
        cv.rect(5, 10, 26, 31, h)
        cv.rect(20, 10, 26, 31, hd)
    # cara
    cv.ellipse(16, 16, 9, 10, s)
    cv.ellipse(19, 17, 6, 8.5, s)
    for y in range(8, 27):
        for x in range(20, 26):
            if cv.get(x, y) == s and (x - 16) ** 2 / 81 + (y - 16) ** 2 / 100 > 0.55:
                cv.put(x, y, sd)
    # ojos
    for ex in (11, 19):
        cv.rect(ex, 15, ex + 2, 18, OUTLINE)
        cv.put(ex, 15, hx("ffffff"))
        cv.put(ex + 1, 18, hx("4a5a8a"))
    cv.hline(10, 13, 13, shade(h, 0.6))
    cv.hline(19, 22, 13, shade(h, 0.6))
    # boca / mejillas
    cv.hline(15, 18, 22, shade(s, 0.6))
    cv.put(14, 21, shade(s, 0.6))
    cv.put(19, 21, shade(s, 0.6))
    cv.rect(9, 19, 10, 20, hx("e88080"))
    cv.rect(22, 19, 23, 20, hx("d07070"))
    if cfg.get("glasses"):
        g = cfg["glasses"]
        for ex in (10, 18):
            cv.hline(ex, ex + 4, 14, g)
            cv.hline(ex, ex + 4, 19, g)
            cv.vline(ex, 14, 19, g)
            cv.vline(ex + 4, 14, 19, g)
        cv.hline(15, 17, 15, g)
    if cfg.get("visor"):
        v = cfg["visor"]
        cv.rect(8, 14, 24, 18, v)
        cv.hline(8, 24, 14, shade(v, 1.3))
        cv.rect(10, 15, 12, 15, hx("ffffff"))
    if cfg.get("implant"):
        im = cfg["implant"]
        cv.rect(23, 11, 24, 13, shade(im, 0.6))
        cv.put(24, 12, im)
        cv.put(22, 14, im)
    # pelo
    if style == "mohawk":
        cv.ellipse(16, 9, 9.5, 4.5, shade(s, 0.72))
        for x in range(13, 20):
            top = 0 if x in (15, 16, 17) else 2
            cv.vline(x, top, 9, h if x < 17 else hd)
        return add_outline(cv.img)
    cv.ellipse(16, 9, 10, 5.5, h)
    cv.ellipse(19, 9, 7, 4.5, hd)
    cv.ellipse(15, 8, 6, 3, h)
    if style == "short":
        for x in range(8, 25, 3):
            cv.rect(x, 11, x + 1, 12, h)
        cv.rect(6, 9, 7, 16, h)
        cv.rect(25, 9, 26, 15, hd)
    elif style == "bun":
        cv.disc(16, 2.5, 3.5, h)
        cv.disc(17, 3, 2, hd)
        cv.rect(6, 9, 7, 18, h)
        cv.rect(25, 9, 26, 18, hd)
        cv.put(6, 25, cfg["accent"])
    elif style in ("bob", "long"):
        cv.rect(7, 10, 13, 12, h)
        cv.rect(18, 10, 25, 12, hd)
    elif style == "spiky":
        for x, tip in ((8, 1), (12, 0), (16, 1), (20, 0), (24, 2)):
            for y in range(tip, 6):
                w = (y - tip) // 2
                cv.hline(x - w, x + w, y, h)
        cv.rect(6, 11, 26, 12, a)
        cv.rect(6, 9, 7, 15, h)
    elif style == "braids":
        cv.rect(6, 9, 8, 13, h)
        cv.rect(24, 9, 26, 13, hd)
        cv.put(4, 29, a)
        cv.put(26, 29, a)
    if "pack" in cfg:
        cv.rect(26, 24, 29, 31, cfg["pack"])
        cv.vline(29, 24, 31, shade(cfg["pack"], 0.7))
    return add_outline(cv.img)


# HAL: homenaje a HAL 9000 (2001: Una odisea del espacio). Panel plateado flotante,
# cara negra y una lente roja con el centro dorado. Amable, no siniestra.
HAL_SILVER = hx("c9ced8")
HAL_SILVER_D = hx("8a91a3")
HAL_FACE = hx("10141c")
HAL_LENS = [hx("3a0a10"), hx("7a1018"), hx("c8202a"), hx("ff4a32"), hx("ff9a4a")]


def _lens(cv: Canvas, cx: float, cy: float, r: float, glow: float) -> None:
    """Lente concéntrica: borde oscuro → rojo → naranja; punto dorado y brillo."""
    steps = len(HAL_LENS)
    for i, col in enumerate(HAL_LENS):
        rr = r * (1 - i / (steps + 0.6))
        cv.disc(cx, cy, rr, shade(col, 0.75 + 0.25 * glow) if i > 0 else col)
    cv.disc(cx, cy, max(0.6, r * 0.16), hx("f4d35e"))
    cv.put(int(cx - r * 0.45), int(cy - r * 0.5), hx("ffffff", 200))


def hal_sheet() -> Image.Image:
    """4 cuadros de 16×16: la lente late suavemente; el propulsor parpadea."""
    sheet = Image.new("RGBA", (64, 16), CLEAR)
    for f, glow in enumerate((0.55, 0.8, 1.0, 0.8)):
        cv = Canvas(16, 16)
        cv.rect(4, 0, 11, 13, HAL_SILVER)
        cv.vline(11, 1, 13, HAL_SILVER_D)
        cv.hline(4, 11, 13, HAL_SILVER_D)
        cv.rect(5, 3, 10, 12, HAL_FACE)
        cv.hline(5, 10, 1, hx("3de7c9"))       # placa con el nombre
        _lens(cv, 8, 7, 2.6, glow)
        for x in (6, 8, 10):                   # rejilla del altavoz
            cv.put(x, 11, hx("3a4252"))
        cv.put(7, 14, hx("3de7c9", 220 if f % 2 == 0 else 120))
        cv.put(8, 14, hx("3de7c9", 220 if f % 2 == 1 else 120))
        cv.put(7 + f % 2, 15, hx("3de7c9", 90))
        sheet.paste(add_outline(cv.img), (f * 16, 0))
    return sheet


def hal_portrait() -> Image.Image:
    cv = Canvas(32, 32)
    cv.rect(7, 1, 24, 31, HAL_SILVER)
    cv.vline(24, 2, 31, HAL_SILVER_D)
    cv.vline(7, 1, 31, hx("e6eaf0"))
    cv.rect(9, 8, 22, 30, HAL_FACE)
    cv.rect(8, 2, 23, 6, HAL_FACE)            # placa con el nombre
    draw_text3(cv, "HAL", 10, 2, hx("3de7c9"))
    _lens(cv, 15.5, 16.5, 6.6, 1.0)
    for y in (26, 28):
        for x in range(11, 21, 2):
            cv.put(x, y, hx("3a4252"))
    return add_outline(cv.img)


def hal_eye(size: int = 64) -> Image.Image:
    """Ojo grande para la interfaz de HAL (se escala ×4 en pantalla)."""
    cv = Canvas(size, size)
    c = size / 2
    cv.disc(c, c, c - 1, hx("2a3040"))
    cv.disc(c, c, c - 3, hx("10141c"))
    r = c - 6
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c) / r
            if d > 1:
                continue
            t = 1 - d
            dither = (BAYER4[y % 4][x % 4] / 16 - 0.5) * 0.12
            k = max(0.0, min(0.999, t ** 0.8 + dither)) * (len(HAL_LENS) - 1)
            a, b = HAL_LENS[int(k)], HAL_LENS[min(int(k) + 1, len(HAL_LENS) - 1)]
            col = a if (k - int(k)) < 0.5 else b
            cv.put(x, y, col)
    cv.disc(c, c, r * 0.13, hx("f4d35e"))
    cv.disc(c, c, r * 0.06, hx("fff3b0"))
    cv.ellipse(c - r * 0.38, c - r * 0.42, r * 0.17, r * 0.11, hx("ff9a8a"))
    cv.ellipse(c - r * 0.4, c - r * 0.44, r * 0.09, r * 0.05, hx("ffe0d8"))
    cv.disc(c + r * 0.3, c + r * 0.36, r * 0.05, hx("ff7a5a"))
    return cv.img


def hal_glow(size: int = 32) -> Image.Image:
    """Halo rojo (se dibuja con mezcla aditiva)."""
    img = Image.new("RGBA", (size, size), CLEAR)
    px = img.load()
    c = size / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c) / c
            a = max(0.0, 1 - d) ** 2
            px[x, y] = (255, 70, 50, int(a * 160))
    return img


# --------------------------------------------------------------------- nave

def astra_ship() -> Image.Image:
    img = Image.new("RGBA", (32, 32), CLEAR)
    d = ImageDraw.Draw(img)
    hull = hx("e4ebf2")
    hull_d = hx("a9b6c6")
    d.polygon([(11, 15), (3, 25), (3, 28), (11, 26)], fill=hx("c6d1dd"))
    d.polygon([(20, 15), (28, 25), (28, 28), (20, 26)], fill=hull_d)
    d.polygon([(15, 2), (16, 2), (21, 13), (22, 25), (19, 28), (12, 28), (9, 25), (10, 13)], fill=hull)
    d.polygon([(16, 2), (21, 13), (22, 25), (19, 28), (16, 28)], fill=hull_d)
    d.line([(4, 27), (10, 25)], fill=hx("3de7c9"))
    d.line([(21, 25), (27, 27)], fill=hx("3de7c9"))
    d.rectangle([3, 26, 4, 28], fill=hx("f4d35e"))
    d.rectangle([27, 26, 28, 28], fill=hx("f4d35e"))
    d.rectangle([13, 18, 18, 19], fill=hx("3de7c9"))
    d.ellipse([13, 7, 18, 14], fill=hx("2a7fa0"))
    d.ellipse([14, 8, 16, 10], fill=hx("c9fff4"))
    d.rectangle([12, 28, 14, 29], fill=hx("4a5060"))
    d.rectangle([17, 28, 19, 29], fill=hx("4a5060"))
    return add_outline(img)


def astra_flame() -> Image.Image:
    sheet = Image.new("RGBA", (24, 12), CLEAR)
    for f in range(3):
        cv = Canvas(8, 12)
        length = [8, 11, 6][f]
        for y in range(length):
            w = max(0, 3 - (y * 3) // length)
            col = hx("fffbe0") if y < length * 0.3 else hx("f4d35e") if y < length * 0.65 else hx("f08a2c")
            cv.hline(4 - w - 1, 3 + w, y, col)
        sheet.paste(cv.img, (f * 8, 0))
    return sheet


# ---------------------------------------------------------------- planetas

class Noise:
    def __init__(self, seed: int, grid: int = 64):
        rng = random.Random(seed)
        self.g = grid
        self.v = [[rng.random() for _ in range(grid)] for _ in range(grid)]

    def _smooth(self, x: float, y: float) -> float:
        g = self.g
        x0, y0 = int(math.floor(x)) % g, int(math.floor(y)) % g
        x1, y1 = (x0 + 1) % g, (y0 + 1) % g
        fx, fy = x - math.floor(x), y - math.floor(y)
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        a = self.v[y0][x0] * (1 - fx) + self.v[y0][x1] * fx
        b = self.v[y1][x0] * (1 - fx) + self.v[y1][x1] * fx
        return a * (1 - fy) + b * fy

    def fbm(self, x: float, y: float, octaves: int = 4) -> float:
        total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
        for _ in range(octaves):
            total += self._smooth(x * freq, y * freq) * amp
            norm += amp
            amp *= 0.5
            freq *= 2.0
        return total / norm


def planet(size: int, seed: int, surface, rim: tuple | None = None, clouds=None, rot: float = 0.0) -> Image.Image:
    img = Image.new("RGBA", (size, size), CLEAR)
    px = img.load()
    n = Noise(seed)
    cn = Noise(seed + 99)
    r = size / 2 - 1.5
    c = size / 2
    lx, ly, lz = -0.55, -0.6, 0.58
    for y in range(size):
        for x in range(size):
            dx = (x + 0.5 - c) / r
            dy = (y + 0.5 - c) / r
            d2 = dx * dx + dy * dy
            if d2 > 1.0:
                continue
            dz = math.sqrt(1.0 - d2)
            lon = math.atan2(dx, dz) + rot
            lat = math.asin(dy)
            u = (lon / math.pi + 1.0) * 6.0
            v = (lat / math.pi + 0.5) * 6.0
            h = n.fbm(u, v)
            col = surface(h, lat, u, v)
            if clouds is not None:
                cv = cn.fbm(u * 1.4 + 3, v * 2.2)
                cc = clouds(cv, lat)
                if cc is not None:
                    col = cc
            light = max(0.0, dx * lx + dy * ly + dz * lz)
            level = light * 4.0 + (BAYER4[y % 4][x % 4] / 16.0 - 0.5) * 0.9
            f = [0.32, 0.55, 0.78, 0.93, 1.06][max(0, min(4, int(level)))]
            col = shade(col, f)
            if rim is not None and d2 > 0.86:
                t = (d2 - 0.86) / 0.14
                if (t > 0.55 or BAYER4[y % 4][x % 4] < 8 * t) and light > 0.05:
                    col = rim
            px[x, y] = col
    return add_outline(img, hx("0b1220"))


def earth_withered(h: float, lat: float, u: float, v: float) -> tuple:
    if abs(lat) > 1.32:
        return hx("d8d2c0")
    if h < 0.53:
        return hx("23404f") if h < 0.46 else hx("2f5a66")
    if h < 0.56:
        return hx("a08048")
    if h < 0.63:
        return hx("8c6a3c") if (u * 7) % 2 > 0.6 else hx("6e6a3a")
    return hx("b08c58")


def earth_clouds(cv: float, lat: float):
    if cv > 0.62:
        return hx("d9b97a")
    if cv > 0.58:
        return hx("b89a62")
    return None


def moon_surface(h: float, lat: float, u: float, v: float) -> tuple:
    if h < 0.42:
        return hx("6a6d74")
    if h < 0.55:
        return hx("9a9da4")
    return hx("b8bac0")


def mars_surface(h: float, lat: float, u: float, v: float) -> tuple:
    if lat < -1.3:
        return hx("eee6dc")
    if h < 0.42:
        return hx("7a3424")
    if h < 0.5:
        return hx("a4462a")
    if h < 0.62:
        return hx("c45e34")
    return hx("d98a52")


def trappist_surface(h: float, lat: float, u: float, v: float) -> tuple:
    if abs(lat) > 1.25:
        return hx("e8d8e0")
    if h < 0.5:
        return hx("24406e") if h < 0.43 else hx("2f5c8c")
    if h < 0.56:
        return hx("6a4a6a")
    return hx("4a3456")


def trappist_clouds(cv: float, lat: float):
    return hx("f0dce0") if cv > 0.63 else None


def add_craters(img: Image.Image, seed: int, count: int) -> Image.Image:
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    c = w / 2
    for _ in range(count):
        cx, cy = rng.uniform(w * 0.2, w * 0.8), rng.uniform(h * 0.2, h * 0.8)
        if (cx - c) ** 2 + (cy - c) ** 2 > (w * 0.38) ** 2:
            continue
        r = rng.uniform(2, w * 0.06)
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if not (0 <= x < w and 0 <= y < h) or px[x, y][3] == 0 or px[x, y] == hx("0b1220"):
                    continue
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= r:
                    base = px[x, y]
                    if d > r - 1.2 and (x - cx) + (y - cy) > 0:
                        px[x, y] = shade(base, 1.18)
                    elif d <= r - 1.0:
                        px[x, y] = shade(base, 0.8)
    return img


def station_aurora() -> Image.Image:
    cv = Canvas(64, 64)
    grey, grey_d = hx("d6dde6"), hx("8f9bab")
    for x0 in (2, 50):
        cv.rect(x0, 26, x0 + 11, 37, hx("2a4a8a"))
        for gx in range(x0, x0 + 12, 3):
            cv.vline(gx, 26, 37, hx("3d6ab8"))
        cv.hline(x0, x0 + 11, 31, hx("8fb0e8"))
    cv.rect(13, 31, 50, 32, grey_d)
    for y in range(64):
        for x in range(64):
            d = math.hypot(x + 0.5 - 32, y + 0.5 - 32)
            if 17 <= d <= 22:
                cv.put(x, y, grey if (x + y) < 66 else grey_d)
    for ang in range(0, 360, 90):
        a = math.radians(ang + 45)
        for t in range(8, 18):
            cv.put(int(32 + math.cos(a) * t), int(32 + math.sin(a) * t), grey_d)
    cv.disc(32, 32, 8, grey)
    cv.disc(34, 34, 6, grey_d)
    cv.disc(32, 32, 3, hx("3de7c9"))
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        cv.put(int(32 + math.cos(a) * 19.5), int(32 + math.sin(a) * 19.5), hx("f4d35e"))
    return add_outline(cv.img, hx("0b1220"))


def beacon_sheet() -> Image.Image:
    sheet = Image.new("RGBA", (32, 16), CLEAR)
    for f in range(2):
        cv = Canvas(16, 16)
        cv.rect(5, 8, 10, 12, hx("b8c0cc"))
        cv.rect(8, 8, 10, 12, hx("8a94a4"))
        cv.rect(2, 9, 4, 11, hx("2a4a8a"))
        cv.rect(11, 9, 13, 11, hx("2a4a8a"))
        cv.vline(7, 3, 7, hx("8a94a4"))
        light = hx("66ffb3") if f == 0 else hx("2a8a5a")
        cv.disc(7.5, 2.5, 1.6, light)
        sheet.paste(add_outline(cv.img), (f * 16, 0))
    return sheet


def debris() -> Image.Image:
    sheet = Image.new("RGBA", (36, 12), CLEAR)
    rng = random.Random(7)
    for i in range(3):
        cv = Canvas(12, 12)
        pts = [(rng.randint(2, 9), rng.randint(2, 9)) for _ in range(5)]
        img = cv.img
        d = ImageDraw.Draw(img)
        d.polygon(pts, fill=hx("8f96a0"))
        d.line(pts[:2], fill=hx("c8ccd2"))
        if i == 1:
            d.point((pts[2]), fill=hx("f08a2c"))
        sheet.paste(add_outline(img), (i * 12, 0))
    return sheet


# ------------------------------------------------------------------- props

def prop_terminal() -> Image.Image:
    cv = Canvas(16, 24)
    cv.rect(3, 10, 12, 22, hx("5a6478"))
    cv.rect(10, 10, 12, 22, hx("444c5e"))
    cv.rect(2, 3, 13, 11, hx("5a6478"))
    cv.rect(3, 4, 12, 10, hx("0b1220"))
    cv.hline(4, 9, 5, hx("3de7c9"))
    cv.hline(4, 7, 7, hx("3de7c9"))
    cv.hline(4, 10, 9, hx("2bb8a0"))
    cv.rect(5, 13, 6, 14, hx("f4d35e"))
    cv.rect(8, 13, 9, 14, hx("e86a6a"))
    return add_outline(cv.img)


def prop_sensor() -> Image.Image:
    cv = Canvas(16, 24)
    cv.vline(7, 8, 22, hx("7a8494"))
    cv.vline(8, 8, 22, hx("5a6478"))
    cv.rect(4, 2, 11, 8, hx("c8d0dc"))
    cv.rect(9, 2, 11, 8, hx("9aa4b4"))
    cv.disc(7, 5, 2.2, hx("0b1220"))
    cv.put(7, 4, hx("e86a6a"))
    cv.put(8, 5, hx("e86a6a"))
    cv.hline(5, 10, 22, hx("5a6478"))
    return add_outline(cv.img)


def prop_solar_panel() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(1, 3, 14, 10, hx("2a4a8a"))
    for x in range(1, 15, 3):
        cv.vline(x, 3, 10, hx("3d6ab8"))
    cv.hline(1, 14, 6, hx("8fb0e8"))
    cv.vline(7, 11, 14, hx("7a8494"))
    cv.hline(5, 10, 14, hx("5a6478"))
    return add_outline(cv.img)


def prop_plant(alive: bool) -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(4, 10, 11, 14, hx("b5532f"))
    cv.rect(9, 10, 11, 14, hx("8a3b26"))
    cv.hline(3, 12, 10, hx("c8683a"))
    cv.rect(5, 10, 10, 10, hx("4a3020"))
    if alive:
        g, gd = hx("5cc85c"), hx("2e8a3e")
        cv.vline(7, 4, 9, gd)
        cv.ellipse(5, 5, 2.5, 1.5, g)
        cv.ellipse(10, 4, 2.5, 1.5, g)
        cv.put(9, 4, hx("a8f0a0"))
    else:
        b = hx("8a6a3c")
        cv.vline(7, 5, 9, b)
        cv.put(6, 5, b)
        cv.put(5, 6, b)
        cv.put(4, 7, hx("6e5a30"))
        cv.put(8, 6, b)
        cv.put(9, 7, b)
        cv.put(10, 8, hx("6e5a30"))
    return add_outline(cv.img)


def prop_seed_chest() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(2, 5, 13, 13, hx("f4d35e"))
    cv.rect(2, 5, 13, 7, hx("ffe98a"))
    cv.rect(11, 5, 13, 13, hx("c8a43c"))
    cv.hline(2, 13, 8, hx("a8862c"))
    cv.disc(7.5, 10.5, 2, hx("4caf50"))
    cv.put(7, 10, hx("a8f0a0"))
    return add_outline(cv.img)


def prop_vault_door() -> Image.Image:
    cv = Canvas(32, 32)
    cv.rect(0, 2, 31, 31, hx("6a7280"))
    cv.rect(0, 2, 31, 4, hx("8a92a0"))
    cv.disc(16, 18, 12, hx("9aa4b4"))
    cv.disc(17, 19, 10, hx("7a8494"))
    cv.disc(16, 18, 9, hx("b8c0cc"))
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        cv.disc(16 + math.cos(a) * 10.5, 18 + math.sin(a) * 10.5, 1, hx("4a5260"))
    cv.disc(16, 18, 4, hx("f4d35e"))
    cv.put(16, 16, hx("4caf50"))
    cv.put(15, 17, hx("4caf50"))
    cv.put(17, 17, hx("4caf50"))
    cv.vline(16, 18, 20, hx("2e7d32"))
    return add_outline(cv.img)


def prop_greenhouse(alive: bool, empty: bool = False) -> Image.Image:
    cv = Canvas(48, 32)
    glass = hx("9fe8f0", 170) if alive or empty else hx("b8c4b0", 150)
    cv.rect(2, 26, 45, 31, hx("6a7280"))
    cv.ellipse(24, 26, 21, 20, glass)
    for x in range(4, 45, 7):
        for y in range(6, 26):
            if cv.get(x, y)[3]:
                cv.put(x, y, hx("dfe8f0"))
    if empty:
        cv.rect(6, 24, 41, 25, hx("8a3b26"))
    elif alive:
        for x in range(8, 41, 6):
            cv.ellipse(x, 23, 2.5, 3, hx("4caf50"))
            cv.put(x, 21, hx("a8f0a0"))
    else:
        for x in range(8, 41, 6):
            cv.vline(x, 20, 25, hx("8a6a3c"))
            cv.put(x - 1, 21, hx("8a6a3c"))
        for (x, y) in ((14, 9), (15, 10), (16, 11), (16, 12), (30, 14), (31, 15)):
            cv.put(x, y, hx("2a2a30"))
    cv.rect(21, 22, 26, 31, hx("4a5260"))
    return add_outline(cv.img)


def prop_habitat() -> Image.Image:
    cv = Canvas(32, 24)
    cv.rect(1, 6, 30, 21, hx("e4ebf2"))
    cv.ellipse(16, 7, 15, 5, hx("e4ebf2"))
    cv.rect(1, 15, 30, 21, hx("c6d1dd"))
    cv.hline(1, 30, 12, hx("f08a2c"))
    cv.rect(5, 8, 9, 11, hx("2a7fa0"))
    cv.put(6, 9, hx("c9fff4"))
    cv.rect(22, 8, 26, 11, hx("2a7fa0"))
    cv.rect(13, 13, 18, 21, hx("5a6478"))
    cv.put(17, 17, hx("3de7c9"))
    return add_outline(cv.img)


def prop_rover() -> Image.Image:
    cv = Canvas(32, 24)
    cv.rect(5, 9, 26, 15, hx("e4ebf2"))
    cv.rect(5, 13, 26, 15, hx("b8c0cc"))
    cv.rect(8, 6, 22, 9, hx("c8a45c"))
    cv.vline(22, 0, 8, hx("7a8494"))
    cv.rect(20, 0, 25, 3, hx("dfe6ee"))
    cv.put(24, 1, hx("3de7c9"))
    for x in (6, 15, 24):
        cv.disc(x + 0.5, 19, 3, hx("3a3a44"))
        cv.disc(x + 0.5, 19, 1.2, hx("8a8a94"))
    cv.hline(6, 25, 16, hx("5a6478"))
    return add_outline(cv.img)


def prop_antenna() -> Image.Image:
    cv = Canvas(16, 32)
    cv.vline(7, 10, 30, hx("7a8494"))
    cv.vline(8, 10, 30, hx("5a6478"))
    cv.hline(4, 11, 30, hx("5a6478"))
    cv.ellipse(8, 7, 7, 4, hx("dfe6ee"))
    cv.ellipse(8, 6, 5.5, 2.5, hx("b8c0cc"))
    cv.vline(8, 1, 6, hx("7a8494"))
    cv.put(8, 0, hx("e86a6a"))
    return add_outline(cv.img)


def prop_ice() -> Image.Image:
    cv = Canvas(16, 16)
    pts = [((3, 14), (5, 4), (7, 14)), ((6, 14), (9, 2), (12, 14)), ((10, 14), (13, 7), (15, 14))]
    img = cv.img
    d = ImageDraw.Draw(img)
    for tri in pts:
        d.polygon(tri, fill=hx("bfe8ff"))
        d.line([tri[1], tri[2]], fill=hx("7ab8e0"))
    d.point((9, 5), fill=hx("ffffff"))
    return add_outline(img)


def prop_rock(base) -> Image.Image:
    cv = Canvas(16, 16)
    c = hx(base) if isinstance(base, str) else base
    cv.ellipse(8, 10, 6.5, 4.5, c)
    cv.ellipse(6, 8, 4, 3.5, shade(c, 1.15))
    cv.ellipse(10, 12, 4, 2.5, shade(c, 0.75))
    return add_outline(cv.img)


def prop_sample() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(3, 6, 12, 13, hx("c8a072"))
    cv.hline(3, 12, 8, hx("a07848"))
    cv.hline(3, 12, 11, hx("8a6038"))
    cv.rect(10, 6, 12, 13, hx("8a6038"))
    cv.put(6, 9, hx("6ad0ff"))
    cv.put(7, 9, hx("bfefff"))
    return add_outline(cv.img)


def prop_launch_pad() -> Image.Image:
    cv = Canvas(48, 48)
    cv.disc(24, 24, 23, hx("5a6070"))
    cv.disc(24, 24, 21, hx("7a8090"))
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        col = hx("f4d35e") if (ang // 30) % 2 == 0 else hx("2a2a30")
        for t in range(17, 21):
            cv.put(int(24 + math.cos(a) * t), int(24 + math.sin(a) * t), col)
            cv.put(int(24 + math.cos(a + 0.12) * t), int(24 + math.sin(a + 0.12) * t), col)
    cv.disc(24, 24, 9, hx("6a7080"))
    cv.hline(19, 29, 24, hx("3de7c9"))
    cv.vline(24, 19, 29, hx("3de7c9"))
    return add_outline(cv.img)


def prop_dead_tree() -> Image.Image:
    cv = Canvas(16, 24)
    b, bd = hx("7a5a3a"), hx("5a3e26")
    cv.rect(7, 10, 8, 22, b)
    cv.vline(8, 10, 22, bd)
    for (x, y) in ((6, 9), (5, 8), (4, 7), (4, 6), (9, 8), (10, 7), (11, 6), (11, 5), (12, 4), (7, 6), (7, 5), (8, 4), (8, 3), (6, 12), (5, 11), (9, 13), (10, 12)):
        cv.put(x, y, b)
    cv.hline(5, 10, 22, bd)
    return add_outline(cv.img)


def icon_scanner() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(4, 3, 11, 13, hx("3a4458"))
    cv.rect(5, 4, 10, 8, hx("0b1220"))
    cv.hline(6, 9, 6, hx("3de7c9"))
    cv.put(7, 5, hx("3de7c9"))
    cv.put(8, 7, hx("3de7c9"))
    cv.rect(5, 10, 6, 11, hx("f4d35e"))
    cv.rect(9, 10, 10, 11, hx("c8202a"))
    cv.vline(7, 0, 2, hx("8a91a3"))
    cv.put(7, 0, hx("3de7c9"))
    return add_outline(cv.img)


def icon_suit() -> Image.Image:
    cv = Canvas(16, 16)
    cv.disc(8, 4.5, 3.5, hx("e8edf5"))
    cv.ellipse(8, 4.8, 2.4, 1.8, hx("3de7c9"))
    cv.put(7, 4, hx("c9fff4"))
    cv.rect(4, 8, 11, 14, hx("e8edf5"))
    cv.rect(2, 9, 3, 13, hx("d0d6e0"))
    cv.rect(12, 9, 13, 13, hx("d0d6e0"))
    cv.vline(8, 8, 14, hx("3de7c9"))
    cv.rect(5, 10, 6, 11, hx("f4d35e"))
    return add_outline(cv.img)


def icon_chip(accent: str) -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(3, 3, 12, 12, hx("1e2a3e"))
    cv.rect(5, 5, 10, 10, hx(accent))
    cv.rect(6, 6, 9, 9, shade(hx(accent), 0.7))
    for i in (4, 7, 10):
        cv.put(i, 1, hx("f4d35e"))
        cv.put(i, 2, hx("f4d35e"))
        cv.put(i, 13, hx("f4d35e"))
        cv.put(i, 14, hx("f4d35e"))
        cv.put(1, i, hx("f4d35e"))
        cv.put(2, i, hx("f4d35e"))
        cv.put(13, i, hx("f4d35e"))
        cv.put(14, i, hx("f4d35e"))
    return add_outline(cv.img)


def icon_vial(liquid: str, light: str) -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(6, 1, 9, 2, hx("8a91a3"))
    cv.rect(5, 3, 10, 14, hx("d8f0ff", 120))
    cv.rect(6, 7, 9, 13, hx(liquid))
    cv.vline(6, 7, 13, hx(light))
    cv.put(8, 9, hx(light))
    return add_outline(cv.img)


def icon_samples() -> Image.Image:
    cv = Canvas(16, 16)
    for i, x in enumerate((3, 7, 11)):
        cv.rect(x, 2, x + 2, 13, hx("d0d6e0"))
        cv.rect(x, 2, x + 2, 3, hx("8a91a3"))
        cv.rect(x, 8 - i, x + 2, 13, hx(("a4462a", "c45e34", "c8a072")[i]))
    return add_outline(cv.img)


def icon_battery() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(2, 4, 12, 13, hx("2a3048"))
    cv.rect(13, 7, 14, 10, hx("8a91a3"))
    for i, x in enumerate((4, 7, 10)):
        cv.rect(x, 6, x + 1, 11, NEON_GREEN if i < 2 else hx("3a4458"))
    return add_outline(cv.img)


def icon_shield() -> Image.Image:
    cv = Canvas(16, 16)
    for i, c in enumerate((hx("8a91a3"), hx("b8bec8"), hx("e8eef5"))):
        cv.rect(3 + i * 3, 2 + i, 4 + i * 3, 14 - i, c)
    cv.put(2, 6, NEON_GOLD)
    cv.put(1, 6, NEON_GOLD)
    cv.put(0, 6, shade(NEON_GOLD, 0.6))
    return add_outline(cv.img)


def icon_thruster() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(2, 5, 9, 11, hx("8a91a3"))
    cv.rect(9, 4, 11, 12, hx("5a606c"))
    for x, a in ((12, 255), (13, 180), (14, 110)):
        cv.vline(x, 6, 10, (95, 160, 255, a))
    cv.put(4, 7, NEON_CYAN)
    return add_outline(cv.img)


def icon_telescope() -> Image.Image:
    cv = Canvas(16, 16)
    for i in range(9):
        cv.rect(3 + i, 9 - i // 2, 4 + i, 10 - i // 2, hx("c8a43c") if i < 7 else hx("e8eef5"))
    cv.vline(7, 10, 14, hx("5a4030"))
    cv.put(5, 14, hx("5a4030"))
    cv.put(9, 14, hx("5a4030"))
    cv.put(13, 3, NEON_CYAN)
    return add_outline(cv.img)


def icon_star_map() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(2, 3, 13, 13, hx("1e2a4e"))
    for x, y in ((4, 5), (7, 8), (10, 6), (11, 11), (5, 11)):
        cv.put(x, y, hx("ffffff"))
    cv.put(8, 8, NEON_GOLD)
    cv.hline(4, 7, 5, shade(NEON_CYAN, 0.5))
    return add_outline(cv.img)


def icon_hydro() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(3, 9, 12, 14, hx("3a4458"))
    cv.hline(3, 12, 10, NEON_CYAN)
    cv.disc(8, 6, 3, hx("3fae5a"))
    cv.disc(5, 7, 2, hx("3fae5a"))
    cv.disc(11, 7, 2, hx("7fe08a"))
    return add_outline(cv.img)


def icon_rock(base: str) -> Image.Image:
    cv = Canvas(16, 16)
    cv.ellipse(8, 9, 6, 4.5, hx(base))
    cv.ellipse(6, 7.5, 2.5, 1.5, shade(hx(base), 1.25))
    cv.put(10, 10, shade(hx(base), 0.6))
    cv.put(5, 11, shade(hx(base), 0.6))
    return add_outline(cv.img)


def icon_cup(color: tuple) -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(4, 4, 11, 14, hx("e8eef5", 200))
    cv.rect(5, 6, 10, 13, color)
    cv.vline(9, 1, 6, NEON_CYAN)
    cv.hline(9, 11, 1, NEON_CYAN)
    return add_outline(cv.img)


def icon_tortilla() -> Image.Image:
    cv = Canvas(16, 16)
    cv.ellipse(8, 9, 6.5, 4, hx("e8c890"))
    for x, y in ((5, 8), (9, 10), (11, 8)):
        cv.put(x, y, hx("b08850"))
    cv.ellipse(8, 7, 3, 1.2, hx("3fae5a"))
    return add_outline(cv.img)


def icon_fries() -> Image.Image:
    cv = Canvas(16, 16)
    for x in (5, 7, 9, 11):
        cv.vline(x, 2 + (x % 3), 9, hx("f4d35e"))
    cv.rect(4, 8, 12, 14, NEON_PINK)
    cv.hline(4, 12, 8, hx("ffffff"))
    return add_outline(cv.img)


def item_icons() -> None:
    icons = {
        "the_seed": prop_seed_chest(),
        "scanner": icon_scanner(),
        "suit": icon_suit(),
        "launch_program": icon_chip("3de7c9"),
        "probe_data": icon_chip("f4d35e"),
        "lunar_ice": icon_vial("9fd8ff", "e8f8ff"),
        "delta_samples": icon_samples(),
        "battery_pack": icon_battery(),
        "whipple_shield": icon_shield(),
        "ion_thruster": icon_thruster(),
        "pocket_telescope": icon_telescope(),
        "star_map": icon_star_map(),
        "hydro_kit": icon_hydro(),
        "moon_rock_replica": icon_rock("9a9da4"),
        "meteorite_replica": icon_rock("6a3a2a"),
        "freeze_dried_shake": icon_cup(hx("ff7aa8")),
        "polar_ice_water": icon_cup(hx("9fd8ff")),
        "space_tortilla": icon_tortilla(),
        "mars_fries": icon_fries(),
    }
    for name, img in icons.items():
        save(img, "items", f"{name}.png")


# ------------------------------------------------------------ ciudad cyberpunk
# Mundo posapocalíptico: fachadas gastadas, cables, carteles de neón y anuncios
# holográficos de corporaciones inventadas. Los letreros usan una fuente de 3×5 px.

NEON_PINK = hx("ff3ea5")
NEON_CYAN = hx("3de7c9")
NEON_GOLD = hx("f4d35e")
NEON_GREEN = hx("7dff9a")

FONT_3X5 = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011", "D": "110101101101110",
    "E": "111100110100111", "F": "111100110100100", "G": "011100101101011", "H": "101101111101101",
    "I": "111010010010111", "J": "001001001101010", "K": "101101110101101", "L": "100100100100111",
    "M": "101111111101101", "N": "110101101101101", "O": "010101101101010", "P": "110101110100100",
    "Q": "010101101110011", "R": "110101110101101", "S": "011100010001110", "T": "111010010010010",
    "U": "101101101101111", "V": "101101101101010", "W": "101101111111101", "X": "101101010101101",
    "Y": "101101010010010", "Z": "111001010100111", "-": "000000111000000", " ": "000000000000000",
    "0": "111101101101111", "1": "010110010010111", "2": "110001010100111", "3": "110001010001110",
    "4": "101101111001001", "5": "111100110001110", "9": "111101111001110", "!": "010010010000010",
}


def text_width(text: str) -> int:
    return len(text) * 4 - 1


def draw_text3(cv: Canvas, text: str, x: int, y: int, color: tuple) -> None:
    for ch in text.upper():
        bits = FONT_3X5.get(ch, FONT_3X5[" "])
        for i, b in enumerate(bits):
            if b == "1":
                cv.put(x + i % 3, y + i // 3, color)
        x += 4


def neon_sign(cv: Canvas, text: str, cx: int, y: int, color: tuple) -> None:
    """Letrero: panel oscuro, letras de neón y un halo de 1 px."""
    w = text_width(text)
    x0 = cx - w // 2
    cv.rect(x0 - 3, y - 2, x0 + w + 2, y + 6, hx("120e1c"))
    cv.hline(x0 - 3, x0 + w + 2, y - 2, shade(color, 0.55))
    cv.hline(x0 - 3, x0 + w + 2, y + 6, shade(color, 0.55))
    halo = Canvas(cv.w, cv.h)
    draw_text3(halo, text, x0, y, color)
    for yy in range(cv.h):
        for xx in range(cv.w):
            if halo.get(xx, yy)[3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if halo.get(xx + dx, yy + dy)[3] == 0 and cv.get(xx + dx, yy + dy) == hx("120e1c"):
                    cv.put(xx + dx, yy + dy, shade(color, 0.45))
    draw_text3(cv, text, x0, y, color)
    for xx in range(x0, x0 + w):
        if cv.get(xx, y + 2) == color and (xx % 3 == 0):
            cv.put(xx, y + 2, hx("ffffff"))


BUILDING_STYLES = {
    # pared, sombra, detalle, techo
    "concrete": (hx("6a6460"), hx("4a4440"), hx("8a5a3a"), hx("3a3430")),
    "module": (hx("b8bec8"), hx("8a909c"), NEON_CYAN, hx("5a606c")),
    "regolith": (hx("b0643c"), hx("8a4a2c"), NEON_GOLD, hx("6a3420")),
}


def building(w_tiles: int, h: int, style: str, sign: str, neon: tuple, seed: int,
             door: bool = True, lit: float = 0.5) -> Image.Image:
    """Fachada genérica: pared con paneles, ventanas (algunas encendidas), puerta y letrero."""
    w = w_tiles * 16
    cv = Canvas(w, h)
    wall, dark, detail, roof = BUILDING_STYLES[style]
    rng = random.Random(seed)
    top = 4
    if style == "regolith":
        for x in range(w):
            dy = int(4 - 4 * math.sin(math.pi * x / (w - 1)))
            cv.vline(x, dy, h - 1, wall)
        top = 4
    else:
        cv.rect(0, top, w - 1, h - 1, wall)
        cv.rect(0, top, w - 1, top + 2, roof)
    cv.rect(w - 4, top + 3, w - 1, h - 1, dark)
    # paneles / grietas / óxido
    for y in range(top + 6, h - 2, 7):
        cv.hline(1, w - 5, y, shade(wall, 0.88))
    if style == "module":
        for x in range(4, w - 4, 8):
            for y in range(top + 5, h - 2, 7):
                cv.put(x, y, shade(wall, 0.7))
        cv.hline(0, w - 1, top + 3, detail)
    if style == "concrete":
        for _ in range(4):
            x, y = rng.randrange(2, w - 6), rng.randrange(top + 6, h - 6)
            for k in range(rng.randrange(3, 7)):
                cv.put(x + (k % 2), y + k, shade(wall, 0.6))
        for _ in range(3):
            x = rng.randrange(2, w - 6)
            cv.vline(x, top + 3, top + 3 + rng.randrange(4, 10), detail)
    # ventanas
    win_y = top + 13
    for x in range(4, w - 8, 10):
        if door and abs(x + 3 - w // 2) < 8:
            continue
        on = rng.random() < lit
        glass = shade(neon, 0.85) if on else hx("1a2030")
        cv.rect(x, win_y, x + 5, win_y + 5, hx("15121e"))
        cv.rect(x + 1, win_y + 1, x + 4, win_y + 4, glass)
        if on:
            cv.put(x + 1, win_y + 1, hx("ffffff"))
        else:
            cv.put(x + 4, win_y + 1, hx("3a4458"))
    if door:
        dx = w // 2 - 4
        cv.rect(dx - 1, h - 14, dx + 8, h - 1, hx("15121e"))
        cv.rect(dx, h - 13, dx + 7, h - 1, hx("2a2240"))
        cv.rect(dx + 1, h - 12, dx + 6, h - 1, shade(neon, 0.35))
        cv.hline(dx - 1, dx + 8, h - 15, neon)
        cv.put(dx + 6, h - 6, NEON_GOLD)
    # cables colgando del techo
    cv.hline(0, w - 1, top - 1, hx("15121e"))
    for x in range(2, w - 2, 5):
        if rng.random() < 0.3:
            cv.vline(x, top - 1, top + 1, hx("15121e"))
    if sign:
        neon_sign(cv, sign, w // 2, top + 5, neon)
    return add_outline(cv.img)


def prop_holo_ad(text: str, color: tuple) -> Image.Image:
    """Poste con anuncio holográfico translúcido (el ancho se ajusta al texto)."""
    w = max(32, text_width(text) + 10)
    cv = Canvas(w, 40)
    cx = w // 2
    cv.rect(cx - 1, 18, cx, 39, hx("3a3440"))
    cv.rect(cx - 4, 36, cx + 3, 39, hx("2a2430"))
    cv.rect(cx - 3, 17, cx + 2, 18, hx("5a5460"))
    glow = shade(color, 0.6)
    for y in range(1, 16):
        for x in range(1, w - 1):
            if (y + x) % 2 == 0 or y % 3 == 0:
                cv.put(x, y, (glow[0], glow[1], glow[2], 140))
    cv.hline(1, w - 2, 1, color)
    cv.hline(1, w - 2, 15, color)
    draw_text3(cv, text, cx - text_width(text) // 2, 6, hx("ffffff"))
    return add_outline(cv.img)


def prop_vending() -> Image.Image:
    cv = Canvas(16, 26)
    cv.rect(1, 2, 14, 25, hx("2a3a6a"))
    cv.rect(12, 2, 14, 25, hx("1e2a4e"))
    cv.rect(3, 4, 10, 15, hx("0b1220"))
    for row, col in enumerate((NEON_CYAN, NEON_PINK, NEON_GOLD)):
        cv.hline(4, 9, 6 + row * 3, col)
    cv.rect(3, 18, 10, 21, hx("15121e"))
    draw_text3(cv, "AIRE", 1, 0, hx("ffffff"))
    cv.rect(11, 8, 11, 10, NEON_GREEN)
    return add_outline(cv.img)


def prop_scrap() -> Image.Image:
    cv = Canvas(32, 20)
    rng = random.Random(77)
    cv.ellipse(16, 16, 15, 5, hx("4a4440"))
    for _ in range(14):
        x, y = rng.randrange(4, 28), rng.randrange(6, 16)
        col = rng.choice([hx("8a5a3a"), hx("6a6460"), hx("a07040"), hx("3a4458"), hx("b8bec8")])
        cv.rect(x, y, x + rng.randrange(2, 6), y + rng.randrange(1, 3), col)
    cv.disc(10, 9, 3, hx("2a2a30"))
    cv.disc(10, 9, 1.5, hx("6a6a70"))
    cv.put(22, 7, NEON_PINK)
    return add_outline(cv.img)


def prop_lamp(color: tuple) -> Image.Image:
    cv = Canvas(16, 36)
    cv.rect(7, 6, 8, 35, hx("3a3440"))
    cv.rect(5, 33, 10, 35, hx("2a2430"))
    cv.rect(4, 3, 12, 5, hx("2a2430"))
    cv.rect(5, 6, 11, 6, color)
    cv.hline(9, 14, 3, hx("2a2430"))
    return add_outline(cv.img)


def prop_cable_pole() -> Image.Image:
    cv = Canvas(16, 44)
    cv.rect(7, 2, 8, 43, hx("5a4030"))
    cv.rect(2, 5, 13, 6, hx("5a4030"))
    for x in (2, 13):
        cv.put(x, 4, hx("8a8a90"))
    cv.vline(0, 6, 12, hx("15121e"))
    cv.vline(15, 6, 10, hx("15121e"))
    cv.rect(9, 18, 12, 22, hx("3a4458"))
    cv.put(11, 19, NEON_GREEN)
    return add_outline(cv.img)


def prop_barrel(color: tuple) -> Image.Image:
    cv = Canvas(16, 18)
    cv.rect(3, 3, 12, 17, color)
    cv.rect(10, 3, 12, 17, shade(color, 0.75))
    cv.hline(3, 12, 6, shade(color, 0.6))
    cv.hline(3, 12, 14, shade(color, 0.6))
    cv.ellipse(7.5, 3, 4.5, 1.5, shade(color, 1.2))
    return add_outline(cv.img)


def prop_crate() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(2, 4, 13, 15, hx("6a5a48"))
    cv.rect(2, 4, 13, 5, hx("8a7a60"))
    cv.vline(13, 4, 15, hx("4a3e30"))
    cv.hline(2, 13, 10, hx("4a3e30"))
    cv.put(4, 7, NEON_CYAN)
    return add_outline(cv.img)


def prop_table() -> Image.Image:
    cv = Canvas(24, 18)
    cv.ellipse(12, 7, 11, 4, hx("3a3050"))
    cv.ellipse(12, 6, 10, 3, hx("5a4a7a"))
    cv.rect(11, 9, 12, 16, hx("2a2430"))
    cv.rect(7, 16, 16, 17, hx("2a2430"))
    cv.disc(8, 5, 1.2, NEON_CYAN)
    cv.disc(15, 6, 1.2, NEON_PINK)
    return add_outline(cv.img)


def prop_stool() -> Image.Image:
    cv = Canvas(10, 14)
    cv.ellipse(5, 3, 4, 1.5, NEON_PINK)
    cv.rect(4, 4, 5, 12, hx("8a8a90"))
    cv.hline(2, 7, 13, hx("5a5a60"))
    return add_outline(cv.img)


def prop_jukebox() -> Image.Image:
    cv = Canvas(16, 26)
    cv.rect(2, 6, 13, 25, hx("3a2a4a"))
    cv.ellipse(7.5, 6, 5.5, 5, hx("3a2a4a"))
    cv.ellipse(7.5, 6, 4, 3.5, NEON_GOLD)
    cv.ellipse(7.5, 6, 2.5, 2, NEON_PINK)
    for y in range(12, 22, 3):
        cv.hline(4, 11, y, NEON_CYAN)
    return add_outline(cv.img)


def prop_plant_pot() -> Image.Image:
    cv = Canvas(16, 22)
    cv.rect(4, 14, 11, 21, hx("3a4458"))
    cv.hline(4, 11, 15, NEON_CYAN)
    for (x, y, r) in ((8, 8, 4), (5, 10, 3), (11, 10, 3), (8, 4, 2.5)):
        cv.disc(x, y, r, hx("3fae5a"))
    cv.disc(7, 7, 1.5, hx("7fe08a"))
    return add_outline(cv.img)


def prop_screen(text: str, color: tuple) -> Image.Image:
    cv = Canvas(32, 18)
    cv.rect(0, 0, 31, 17, hx("15121e"))
    cv.rect(1, 1, 30, 16, shade(color, 0.3))
    for y in range(2, 16, 2):
        cv.hline(1, 30, y, shade(color, 0.22))
    draw_text3(cv, text, 16 - text_width(text) // 2, 6, color)
    return add_outline(cv.img)


def interior_tiles() -> Image.Image:
    """Atlas 8×2 de interiores: 0-1 metal, 2-3 madera, 4-5 baldosa roja, 6 alfombra neón,
    7 felpudo de salida, 8 muro alto, 9 muro metal con neón, 10 muro de hormigón, 11 muro marciano,
    12 muro con pantalla, 13 mostrador, 14 estante de tienda, 15 estante de bar (jugos)."""
    rng = random.Random(91)
    atlas = Image.new("RGBA", (128, 32), CLEAR)

    def tile(i: int, cv: Canvas) -> None:
        atlas.paste(cv.img, ((i % 8) * 16, (i // 8) * 16))

    def floor(base: tuple, line: tuple, seed_off: int, planks: bool) -> Canvas:
        cv = Canvas(16, 16)
        cv.rect(0, 0, 15, 15, base)
        if planks:
            for y in (0, 5, 10, 15):
                cv.hline(0, 15, y, line)
            for y, x in ((1, 6 + seed_off), (6, 11 - seed_off), (11, 3 + seed_off)):
                cv.vline(x, y, y + 3, line)
        else:
            cv.hline(0, 15, 0, line)
            cv.vline(0, 0, 15, line)
            cv.put(3 + seed_off, 3, shade(base, 1.2))
            cv.put(12 - seed_off, 11, shade(base, 1.2))
        for _ in range(4):
            cv.put(rng.randrange(16), rng.randrange(16), shade(base, 0.9))
        return cv

    tile(0, floor(hx("3a4050"), hx("2a2e3a"), 0, False))
    tile(1, floor(hx("3a4050"), hx("2a2e3a"), 2, False))
    tile(2, floor(hx("6a4a32"), hx("4a3222"), 0, True))
    tile(3, floor(hx("6a4a32"), hx("4a3222"), 2, True))
    tile(4, floor(hx("8a4a32"), hx("6a3222"), 0, False))
    tile(5, floor(hx("8a4a32"), hx("6a3222"), 3, False))
    rug = Canvas(16, 16)
    rug.rect(0, 0, 15, 15, hx("4a1a40"))
    rug.hline(0, 15, 1, NEON_PINK)
    rug.hline(0, 15, 14, NEON_PINK)
    for x in range(2, 16, 4):
        rug.put(x, 7, NEON_CYAN)
    tile(6, rug)
    mat = Canvas(16, 16)
    mat.rect(0, 0, 15, 15, hx("3a4050"))
    mat.rect(2, 3, 13, 13, hx("1a3a3a"))
    mat.hline(2, 13, 3, NEON_CYAN)
    for x in range(4, 12, 2):
        mat.vline(x, 6, 11, shade(NEON_CYAN, 0.5))
    tile(7, mat)
    top = Canvas(16, 16)
    top.rect(0, 0, 15, 15, hx("15121e"))
    top.hline(0, 15, 15, hx("2a2430"))
    tile(8, top)

    def wall(base: tuple, accent: tuple | None) -> Canvas:
        cv = Canvas(16, 16)
        cv.rect(0, 0, 15, 15, base)
        cv.hline(0, 15, 15, shade(base, 0.6))
        cv.hline(0, 15, 0, shade(base, 1.2))
        for _ in range(3):
            cv.put(rng.randrange(16), rng.randrange(2, 14), shade(base, 0.85))
        if accent:
            cv.hline(0, 15, 9, accent)
        return cv

    tile(9, wall(hx("5a606c"), NEON_CYAN))
    tile(10, wall(hx("6a6460"), None))
    tile(11, wall(hx("9a5434"), NEON_GOLD))
    scr = wall(hx("5a606c"), None)
    scr.rect(2, 3, 13, 11, hx("15121e"))
    scr.rect(3, 4, 12, 10, shade(NEON_CYAN, 0.35))
    scr.hline(4, 9, 6, NEON_CYAN)
    scr.hline(4, 11, 8, NEON_PINK)
    tile(12, scr)
    counter = Canvas(16, 16)
    counter.rect(0, 3, 15, 15, hx("3a2a4a"))
    counter.rect(0, 3, 15, 5, hx("8a8a98"))
    counter.hline(0, 15, 10, NEON_PINK)
    tile(13, counter)
    shelf = Canvas(16, 16)
    shelf.rect(0, 0, 15, 15, hx("4a3e30"))
    for y in (4, 9, 14):
        shelf.hline(0, 15, y, hx("2a2218"))
    for i, (x, y) in enumerate([(1, 1), (5, 1), (10, 1), (2, 6), (7, 6), (12, 6), (1, 11), (8, 11)]):
        col = [NEON_CYAN, NEON_GOLD, hx("e07a2a"), NEON_GREEN, NEON_PINK, hx("b8bec8")][i % 6]
        shelf.rect(x, y, x + 2, y + 2, col)
    tile(14, shelf)
    bar = Canvas(16, 16)
    bar.rect(0, 0, 15, 15, hx("2a2240"))
    for y in (6, 13):
        bar.hline(0, 15, y, hx("8a8a98"))
    for i, x in enumerate(range(1, 15, 3)):
        col = [NEON_PINK, NEON_GOLD, NEON_GREEN, NEON_CYAN, hx("e07a2a")][i % 5]
        bar.rect(x, 2, x + 1, 5, col)
        bar.put(x, 1, hx("e8eef5"))
        bar.rect(x, 9, x + 1, 12, shade(col, 0.8))
    tile(15, bar)
    return atlas


def light_radial(size: int = 64) -> Image.Image:
    """Textura de luz suave (blanca) para PointLight2D."""
    img = Image.new("RGBA", (size, size), CLEAR)
    px = img.load()
    c = size / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c) / c
            a = max(0.0, 1 - d) ** 1.6
            px[x, y] = (255, 255, 255, int(a * 255))
    return img


def rain_drop() -> Image.Image:
    img = Image.new("RGBA", (1, 6), CLEAR)
    for y in range(6):
        img.putpixel((0, y), (200, 240, 255, 60 + y * 30))
    return img


def city_assets() -> None:
    buildings = {
        "bld_earth_shop": building(4, 56, "concrete", "TIENDA", NEON_GREEN, 1, lit=0.8),
        "bld_earth_house_a": building(3, 52, "concrete", "", NEON_GOLD, 2, door=True, lit=0.5),
        "bld_earth_house_b": building(3, 60, "concrete", "", NEON_PINK, 3, door=True, lit=0.4),
        "bld_earth_ruin": building(3, 44, "concrete", "", NEON_CYAN, 4, door=False, lit=0.1),
        "bld_moon_bar": building(4, 48, "module", "BAR CRATER", NEON_PINK, 5, lit=0.9),
        "bld_moon_shop": building(4, 48, "module", "REPUESTOS", NEON_GOLD, 6, lit=0.8),
        "bld_moon_dorm": building(3, 44, "module", "HOGAR", NEON_CYAN, 7, lit=0.6),
        "bld_mars_bar": building(4, 48, "regolith", "CANTINA", NEON_PINK, 8, lit=0.9),
        "bld_mars_shop": building(4, 48, "regolith", "MERCADO", NEON_GREEN, 9, lit=0.8),
        "bld_mars_school": building(4, 48, "regolith", "ESCUELA", NEON_CYAN, 10, lit=0.7),
        "bld_mars_garage": building(4, 44, "regolith", "TALLER", NEON_GOLD, 11, lit=0.5),
        "bld_mars_house": building(3, 40, "regolith", "", NEON_CYAN, 12, lit=0.6),
    }
    for name, img in buildings.items():
        save(img, "props", f"{name}.png")
    props = {
        "holo_agronet": prop_holo_ad("AGRONET", NEON_GREEN),
        "holo_air": prop_holo_ad("AIRE 5 CR", NEON_CYAN),
        "holo_mars": prop_holo_ad("MARS CORP", NEON_PINK),
        "vending_air": prop_vending(),
        "scrap_pile": prop_scrap(),
        "lamp_pink": prop_lamp(NEON_PINK),
        "lamp_cyan": prop_lamp(NEON_CYAN),
        "cable_pole": prop_cable_pole(),
        "barrel_rust": prop_barrel(hx("8a4a2a")),
        "barrel_toxic": prop_barrel(hx("6a8a2a")),
        "crate": prop_crate(),
        "table": prop_table(),
        "stool": prop_stool(),
        "jukebox": prop_jukebox(),
        "plant_pot": prop_plant_pot(),
        "screen_menu": prop_screen("MENU", NEON_GOLD),
        "screen_news": prop_screen("NOTICIAS", NEON_CYAN),
    }
    for name, img in props.items():
        save(img, "props", f"{name}.png")
    save(interior_tiles(), "tiles", "interior_tiles.png")
    save(light_radial(), "fx", "light_radial.png")
    save(rain_drop(), "fx", "rain_drop.png")


# ------------------------------------------------------------------- tiles

def noise_tile(rng: random.Random, base: tuple, dark: tuple, light: tuple, density: float = 0.12) -> Canvas:
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            r = rng.random()
            cv.put(x, y, dark if r < density else light if r > 1 - density * 0.6 else base)
    return cv


def tileset(palette: dict, seed: int) -> Image.Image:
    """Atlas 8×2 de 16 px: 0-3 suelo, 4 cráter, 5 roca (sólido), 6 sombra/duna,
    7 hielo/sedimento, 8 suelo metálico, 9 muro metálico (sólido), 10 marca de pista,
    11 piedras pequeñas."""
    rng = random.Random(seed)
    atlas = Image.new("RGBA", (16 * 8, 16 * 2), CLEAR)
    base, dark, light = palette["base"], palette["dark"], palette["light"]
    tiles = []
    for i in range(4):
        cv = noise_tile(rng, base, dark, light, 0.08 + i * 0.03)
        tiles.append(cv.img)
    cv = noise_tile(rng, base, dark, light)
    cv.ellipse(8, 8, 5, 4, dark)
    cv.ellipse(9, 9, 4, 3, shade(base, 0.9))
    for x in range(5, 13):
        cv.put(x, 12, light)
    tiles.append(cv.img)
    cv = noise_tile(rng, base, dark, light)
    rock = prop_rock(palette["rock"])
    cv.img.alpha_composite(rock)
    tiles.append(cv.img)
    tiles.append(noise_tile(rng, palette["shadow"], shade(palette["shadow"], 0.8), shade(palette["shadow"], 1.2), 0.15).img)
    cv = noise_tile(rng, palette["special"], palette["special_dark"], palette["special_light"], 0.15)
    tiles.append(cv.img)
    cv = Canvas(16, 16)
    cv.rect(0, 0, 15, 15, hx("6a7080"))
    cv.hline(0, 15, 0, hx("8a90a0"))
    cv.vline(0, 0, 15, hx("8a90a0"))
    cv.hline(0, 15, 15, hx("4a5060"))
    cv.vline(15, 0, 15, hx("4a5060"))
    cv.put(2, 2, hx("4a5060"))
    cv.put(13, 13, hx("4a5060"))
    tiles.append(cv.img)
    cv = Canvas(16, 16)
    cv.rect(0, 0, 15, 15, hx("8a92a0"))
    cv.rect(0, 0, 15, 4, hx("c6ced8"))
    cv.rect(0, 12, 15, 15, hx("5a6270"))
    cv.hline(0, 15, 8, hx("3de7c9"))
    tiles.append(cv.img)
    cv = Canvas(16, 16)
    cv.rect(0, 0, 15, 15, hx("6a7080"))
    for x in range(0, 16, 4):
        cv.rect(x, 6, x + 1, 9, hx("f4d35e"))
    tiles.append(cv.img)
    cv = noise_tile(rng, base, dark, light)
    for _ in range(4):
        x, y = rng.randint(2, 13), rng.randint(2, 13)
        cv.rect(x, y, x + 1, y, palette["rock"])
        cv.put(x, y + 1, dark)
    tiles.append(cv.img)
    for i, t in enumerate(tiles):
        atlas.paste(t, ((i % 8) * 16, (i // 8) * 16))
    return atlas


def withered_earth_tiles() -> Image.Image:
    src = Image.open(os.path.join(ART, "third_party", "kenney_tiny_town", "tilemap_packed.png")).convert("RGBA")
    px = src.load()
    out = src.copy()
    opx = out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            deg = h * 360
            if 70 <= deg <= 170 and s > 0.2:
                # verde → pasto seco
                t = (deg - 70) / 100
                h = (42 + 14 * t) / 360
                s *= 0.62
                v *= 0.86
            elif 20 <= deg < 70:
                s *= 0.85
                v *= 0.95
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            opx[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    return out


# ------------------------------------------------------------ ilustraciones

def starfield(cv: Image.Image, seed: int, count: int = 140) -> None:
    rng = random.Random(seed)
    px = cv.load()
    for _ in range(count):
        x, y = rng.randrange(cv.width), rng.randrange(cv.height)
        b = rng.choice([120, 170, 220, 255])
        px[x, y] = (b, b, min(255, b + 20), 255)


def sky_gradient(w: int, h: int, top: tuple, bottom: tuple, horizon: int) -> Image.Image:
    img = Image.new("RGBA", (w, h), top)
    px = img.load()
    for y in range(h):
        t = min(1.0, y / max(1, horizon))
        for x in range(w):
            tt = t + (BAYER4[y % 4][x % 4] / 16.0 - 0.5) * 0.12
            steps = 6
            q = max(0.0, min(1.0, round(tt * steps) / steps))
            px[x, y] = tuple(int(top[i] * (1 - q) + bottom[i] * q) for i in range(3)) + (255,)
    return img


def paste_scaled(dst: Image.Image, src: Image.Image, pos: tuple, scale: int) -> None:
    s = src.resize((src.width * scale, src.height * scale), Image.NEAREST)
    dst.alpha_composite(s, pos)


def illustrations(sprites: dict) -> None:
    W, H = 320, 180
    # 1 — La Tierra desde el espacio
    img = Image.new("RGBA", (W, H), hx("0b1220"))
    starfield(img, 1)
    paste_scaled(img, sprites["earth"], (96, 26), 1)
    save(img, "story", "intro_01_earth.png")

    # 2 — La Marchitez: ciudad nocturna bajo una cúpula, neón y lluvia ácida
    img = sky_gradient(W, H, hx("120c22"), hx("4a2a4a"), 120)
    starfield(img, 3, 25)
    cv = Canvas(W, H)
    cv.img = img
    cv.px = img.load()
    rng = random.Random(4)
    neons = [NEON_PINK, NEON_CYAN, NEON_GOLD, NEON_GREEN]
    # rascacielos de fondo y de frente
    for layer, (base, y0, wmin, wmax) in enumerate(((hx("2a1e3a"), 50, 14, 24), (hx("1a1428"), 80, 18, 30))):
        x = -6
        while x < W:
            w = rng.randrange(wmin, wmax)
            top = y0 + rng.randrange(0, 40)
            cv.rect(x, top, x + w, 140, base)
            for wy in range(top + 4, 136, 5):
                for wx in range(x + 2, x + w - 2, 4):
                    if rng.random() < 0.35:
                        cv.put(wx, wy, shade(rng.choice(neons), 0.7 if layer == 0 else 1.0))
            if layer == 1 and rng.random() < 0.6:
                cv.rect(x + 2, top - 3, x + w - 2, top - 1, rng.choice(neons))
            x += w + rng.randrange(1, 6)
    # anuncio holográfico gigante (capa translúcida que se mezcla al final)
    fx = Canvas(W, H)
    ImageDraw.Draw(fx.img).arc([30, 30, 290, 250], 180, 360, fill=hx("3de7c9", 110), width=1)  # cúpula de aire
    fx.rect(196, 58, 262, 76, (125, 255, 154, 70))
    fx.hline(196, 262, 58, NEON_GREEN)
    fx.hline(196, 262, 76, NEON_GREEN)
    draw_text3(fx, "AGRONET", 216, 61, hx("ffffff"))
    draw_text3(fx, "AIRE 5 CR", 212, 68, NEON_GREEN)
    # calle mojada con reflejos
    cv.rect(0, 140, W - 1, H - 1, hx("15101e"))
    for _ in range(70):
        x, y = rng.randrange(W), rng.randrange(142, H)
        col = rng.choice(neons)
        fx.hline(x, x + rng.randrange(2, 8), y, (col[0], col[1], col[2], 120))
    tree = sprites["dead_tree"]
    for x in (24, 132, 270):
        paste_scaled(img, tree, (x, 110), 2)
    # lluvia ácida
    for _ in range(260):
        x, y = rng.randrange(W + 20), rng.randrange(H)
        for k in range(4):
            fx.put(x - k // 2, y + k, (190, 240, 255, 90))
    img.alpha_composite(fx.img)
    save(img, "story", "intro_02_withered.png")

    # 3 — La Bóveda Semillera
    img = sky_gradient(W, H, hx("2a3a5a"), hx("a0b0c8"), 110)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 140), (90, 30), (170, 120), (240, 50), (320, 130), (320, 180), (0, 180)], fill=hx("5a6478"))
    d.polygon([(90, 30), (70, 55), (85, 50), (100, 60), (110, 50)], fill=hx("eef2f8"))
    d.polygon([(240, 50), (222, 72), (238, 66), (252, 74), (262, 64)], fill=hx("eef2f8"))
    d.rectangle([0, 150, W, H], fill=hx("dfe6ee"))
    paste_scaled(img, sprites["vault_door"], (128, 78), 2)
    paste_scaled(img, sprites["lucia_front"], (196, 118), 2)
    save(img, "story", "intro_03_vault.png")

    # 4 — Andrés y ASTRA
    img = sky_gradient(W, H, hx("0b1220"), hx("c87840"), 150)
    starfield(img, 9, 60)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 150, W, H], fill=hx("5a4a3a"))
    pad = sprites["launch_pad"].resize((96, 36), Image.NEAREST)
    img.alpha_composite(pad, (174, 132))
    paste_scaled(img, sprites["astra"], (174, 52), 3)
    paste_scaled(img, sprites["andres_back"], (92, 110), 2)
    paste_scaled(img, sprites["hal"], (132, 96), 2)
    save(img, "story", "intro_04_launch.png")

    # 5 — Marte no basta
    img = sky_gradient(W, H, hx("c8906a"), hx("e8c8a0"), 120)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 120), (60, 96), (130, 112), (210, 88), (320, 116), (320, 180), (0, 180)], fill=hx("a4462a"))
    d.rectangle([0, 140, W, H], fill=hx("c45e34"))
    paste_scaled(img, sprites["dome_alive"], (112, 76), 2)
    paste_scaled(img, sprites["andres_back"], (64, 120), 2)
    paste_scaled(img, sprites["osei_front"], (232, 120), 2)
    save(img, "story", "ending_01_mars.png")

    # 6 — TRAPPIST-1: siete planetas
    img = Image.new("RGBA", (W, H), hx("0b1220"))
    starfield(img, 12, 120)
    d = ImageDraw.Draw(img)
    for r, a in ((46, 40), (36, 90), (26, 160), (18, 255)):
        d.ellipse([-r + 20, 90 - r, r + 20, 90 + r], fill=(255, 110, 70, a))
    xs = [70, 98, 124, 168, 214, 246, 282]
    sizes = [9, 9, 6, 12, 8, 9, 6]
    for i, (x, s) in enumerate(zip(xs, sizes)):
        if i == 3:
            p = sprites["trappist"].resize((40, 40), Image.NEAREST)
            img.alpha_composite(p, (x - 20, 70))
            d.ellipse([x - 24, 66, x + 24, 114], outline=hx("3de7c9"))
        else:
            c = [hx("b07a6a"), hx("c08a6a"), hx("a08070"), None, hx("7a8aa8"), hx("8a9ab8"), hx("9aa8c0")][i]
            d.ellipse([x - s // 2, 90 - s // 2, x + s // 2, 90 + s // 2], fill=c)
    save(img, "story", "ending_02_trappist.png")

    # Fondo de título
    img = Image.new("RGBA", (W, H), hx("0b1220"))
    starfield(img, 21, 180)
    earth_big = sprites["earth"]
    img.alpha_composite(earth_big, (196, 70))
    paste_scaled(img, sprites["astra"], (120, 96), 2)
    save(img, "story", "title_bg.png")


# ------------------------------------------------------------------- main

def main() -> None:
    sprites: dict = {}
    for name, cfg in CHARACTERS.items():
        save(character_sheet(cfg), "characters", f"{name}.png")
        save(portrait(cfg), "portraits", f"{name}.png")
        sprites[f"{name}_front"] = char_front(cfg, 0)
        sprites[f"{name}_back"] = char_back(cfg, 0)
    hal = hal_sheet()
    save(hal, "characters", "hal.png")
    save(hal_portrait(), "portraits", "hal.png")
    save(hal_eye(), "ui", "hal_eye.png")
    save(hal_glow(), "ui", "hal_glow.png")
    sprites["hal"] = hal.crop((32, 0, 48, 16))
    item_icons()

    sprites["astra"] = astra_ship()
    save(sprites["astra"], "ship", "astra.png")
    save(astra_flame(), "ship", "astra_flame.png")

    sprites["earth"] = planet(128, 3, earth_withered, rim=hx("e0b060"), clouds=earth_clouds)
    save(sprites["earth"], "planets", "earth_withered.png")
    moon = add_craters(planet(96, 5, moon_surface), 11, 26)
    save(moon, "planets", "moon.png")
    save(planet(112, 8, mars_surface, rim=hx("f0b088")), "planets", "mars.png")
    sprites["trappist"] = planet(128, 14, trappist_surface, rim=hx("ff9a7a"), clouds=trappist_clouds)
    save(sprites["trappist"], "planets", "trappist1e.png")
    save(station_aurora(), "planets", "station_aurora.png")
    save(beacon_sheet(), "planets", "beacon.png")
    save(debris(), "planets", "debris.png")

    props = {
        "terminal": prop_terminal(),
        "sensor": prop_sensor(),
        "solar_panel": prop_solar_panel(),
        "plant_dead": prop_plant(False),
        "plant_alive": prop_plant(True),
        "seed_chest": prop_seed_chest(),
        "vault_door": prop_vault_door(),
        "greenhouse_dead": prop_greenhouse(False),
        "dome_alive": prop_greenhouse(True),
        "dome_empty": prop_greenhouse(False, empty=True),
        "habitat": prop_habitat(),
        "rover": prop_rover(),
        "antenna": prop_antenna(),
        "ice": prop_ice(),
        "rock_moon": prop_rock("9a9da4"),
        "rock_mars": prop_rock("a4462a"),
        "sample": prop_sample(),
        "launch_pad": prop_launch_pad(),
        "dead_tree": prop_dead_tree(),
    }
    for name, img in props.items():
        save(img, "props", f"{name}.png")
    sprites.update(props)

    save(tileset({
        "base": hx("9a9da4"), "dark": hx("7a7d84"), "light": hx("b8bac0"), "rock": hx("8a8d94"),
        "shadow": hx("2a3040"), "special": hx("3a4458"), "special_dark": hx("2a3040"), "special_light": hx("bfe8ff"),
    }, 31), "tiles", "moon_tiles.png")
    save(tileset({
        "base": hx("c45e34"), "dark": hx("a4462a"), "light": hx("d98a52"), "rock": hx("8a3b26"),
        "shadow": hx("6a3428"), "special": hx("c8a072"), "special_dark": hx("a07848"), "special_light": hx("e0c098"),
    }, 37), "tiles", "mars_tiles.png")
    save(withered_earth_tiles(), "tiles", "earth_tiles.png")

    city_assets()
    illustrations(sprites)
    print("OK →", ART)


if __name__ == "__main__":
    main()
