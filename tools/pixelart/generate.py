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
    "ada": {
        "hair": hx("c8602a"), "skin": hx("b07850"), "cloth": hx("8a7a4a"),
        "accent": hx("3de7c9"), "pants": hx("5a4a30"), "boots": hx("2a2018"),
        "style": "bun", "glasses": hx("3de7c9"),
    },
}

DIRS = ["down", "left", "right", "up"]
GOLD_BUCKLE = hx("f4d35e")


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


def mix_c(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def _hair_shine(cv: Canvas, cfg: dict, x0: int, x1: int, y: int) -> None:
    """Reflejo del pelo: una franja más clara arriba-izquierda (luz de arriba)."""
    h = cfg["hair"]
    hi = tuple(min(255, int(c * 1.28 + 18)) for c in h[:3]) + (255,)
    for x in range(x0, x1 + 1):
        if cv.get(x, y) == h:
            cv.put(x, y, hi)
    if cv.get(x0 + 1, y + 1) == h:
        cv.put(x0 + 1, y + 1, hi)


def _eyes_front(cv: Canvas, cfg: dict, xs=(6, 9), y: int = 7) -> None:
    """Ojos: pupila oscura arriba y el iris de color abajo (brillan con la luz de arriba)."""
    iris = cfg.get("eyes", hx("6a4430"))
    for x in xs:
        cv.put(x, y, OUTLINE)
        cv.put(x, y + 1, iris)


def _hood(cv: Canvas, cfg: dict, side: bool = False, back: bool = False) -> None:
    """Capucha de chubasquero con visera luminosa (peatones de la Tierra lluviosa)."""
    c = cfg.get("hood", cfg["cloth"])
    cd = shade(c, 0.75)
    if back:
        cv.rect(3, 1, 12, 9, c)
        cv.rect(10, 2, 12, 9, cd)
        cv.hline(4, 11, 1, shade(c, 1.2))
        cv.vline(7, 2, 9, shade(c, 0.85))
        cv.hline(4, 11, 10, shade(c, 0.7))
        return
    if side:
        cv.rect(4, 1, 12, 4, c)
        cv.rect(8, 4, 12, 10, c)
        cv.rect(10, 4, 12, 10, cd)
        cv.hline(4, 9, 1, shade(c, 1.2))
        cv.hline(2, 6, 5, cfg.get("accent"))
        return
    cv.rect(3, 1, 12, 4, c)
    cv.vline(3, 4, 10, c)
    cv.vline(12, 4, 10, cd)
    cv.vline(2, 4, 9, c)
    cv.vline(13, 4, 9, cd)
    cv.hline(4, 11, 1, shade(c, 1.2))
    cv.hline(4, 11, 5, cfg.get("accent"))
    cv.put(5, 5, hx("ffffff"))


def _helmet(cv: Canvas, side: bool = False) -> None:
    """Casco de colono: burbuja de cristal tintado con aro, brillo y antena (se ve la cara)."""
    rim, rim_d, glass = hx("e8ecf2"), hx("9aa0ac"), (191, 232, 255)
    cx, cy, rx, ry = 7.5, 6.0, 6.6, 6.8
    for y in range(-1, 14):
        for x in range(0, 16):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d > 1.0:
                continue
            old = cv.get(x, y)
            if d >= 0.78:
                cv.put(x, y, rim if y < cy + 2 else rim_d)
            elif old[3] == 0:
                cv.put(x, y, glass + (110,))
            else:
                cv.put(x, y, mix_c(old, glass + (255,), 0.22))
    for (x, y) in ((4, 2), (3, 3), (5, 1)):
        cv.put(x, y, hx("ffffff"))
    ax = 12 if not side else 10
    cv.vline(ax, -1, 1, hx("8a909c"))
    cv.put(ax, -2, hx("ff4a4a"))


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
    cv.vline(x_left, y_top, bottom - 1 - lift_l, shade(p, 1.12))
    cv.rect(x_left, bottom - lift_l, x_left + 1, bottom - lift_l, b)
    cv.put(x_left, bottom - lift_l, shade(b, 1.5) if b[0] < 200 else b)
    cv.rect(x_right, y_top, x_right + 1, bottom - 1 - lift_r, shade(p, 0.85))
    cv.rect(x_right, bottom - lift_r, x_right + 1, bottom - lift_r, b)
    cv.put(x_right, bottom - lift_r, shade(b, 1.35) if b[0] < 200 else b)
    if cfg.get("coat"):
        c = cfg["cloth"]
        cv.rect(4, 17, 11, 19, c)
        cv.vline(11, 17, 19, shade(c, 0.78))
        cv.vline(4, 17, 19, shade(c, 1.1))
        cv.hline(4, 11, 19, shade(c, 0.7))


def char_front(cfg: dict, frame: int) -> Image.Image:
    cv = Canvas(16, 24)
    s, c, a = cfg["skin"], cfg["cloth"], cfg["accent"]
    cd = shade(c, 0.8)
    _legs(cv, cfg, 5, 9, frame)
    # torso con volumen: luz a la izquierda, sombra a la derecha, cuello y cinturón
    cv.rect(5, 12, 10, 17, c)
    cv.vline(5, 13, 16, shade(c, 1.12))
    cv.vline(10, 12, 17, cd)
    cv.hline(5, 10, 17, shade(c, 0.6))
    cv.hline(6, 9, 12, shade(c, 1.2))
    cv.put(7, 12, shade(s, 0.85))
    cv.put(8, 12, shade(s, 0.85))
    cv.vline(7, 13, 16, a)
    if not cfg.get("coat"):
        cv.hline(5, 10, 16, shade(cfg["pants"], 0.6))
        cv.put(7, 16, GOLD_BUCKLE)
    else:
        cv.put(6, 14, shade(c, 0.7))
        cv.put(9, 14, shade(c, 0.7))
    # brazos (manga sombreada y mano)
    sway_l = -1 if frame == 1 else 0
    sway_r = -1 if frame == 2 else 0
    cv.rect(4, 12, 4, 15 + sway_l, shade(c, 1.05))
    cv.put(4, 16 + sway_l, s)
    cv.rect(11, 12, 11, 15 + sway_r, cd)
    cv.put(11, 16 + sway_r, shade(s, 0.85))
    # cabeza: sombra en el lado derecho y bajo la barbilla
    cv.rect(4, 3, 11, 10, s)
    cv.rect(3, 4, 12, 9, s)
    cv.vline(12, 4, 9, shade(s, 0.88))
    cv.vline(11, 9, 10, shade(s, 0.9))
    cv.hline(5, 10, 10, shade(s, 0.92))
    cv.put(3, 4, shade(s, 1.06))
    _eyes_front(cv, cfg)
    cv.put(5, 9, hx("f08a8a"))
    cv.put(10, 9, hx("e07a7a"))
    if cfg.get("glasses"):
        g = cfg["glasses"]
        cv.hline(5, 7, 6, g)
        cv.hline(8, 10, 6, g)
    if cfg.get("visor"):
        v = cfg["visor"]
        cv.rect(4, 7, 11, 8, v)
        cv.hline(4, 11, 7, shade(v, 1.25))
        cv.put(5, 7, hx("ffffff"))
    if cfg.get("implant"):
        cv.put(12, 6, cfg["implant"])
        cv.put(12, 7, shade(cfg["implant"], 0.7))
    if cfg["style"] == "hood":
        _hood(cv, cfg)
    elif cfg["style"] == "helmet":
        _hair_front(cv, dict(cfg, style="short"), back=False)
        _hair_shine(cv, cfg, 4, 7, 2)
        _helmet(cv)
    else:
        _hair_front(cv, cfg, back=False)
        _hair_shine(cv, cfg, 4, 7, 2)
    return add_outline(cv.img)


def char_back(cfg: dict, frame: int) -> Image.Image:
    cv = Canvas(16, 24)
    s, c = cfg["skin"], cfg["cloth"]
    cd = shade(c, 0.8)
    _legs(cv, cfg, 5, 9, frame)
    cv.rect(5, 12, 10, 17, cd)
    cv.vline(5, 12, 17, c)
    cv.vline(6, 13, 16, shade(c, 0.9))
    cv.hline(5, 10, 12, shade(c, 0.95))
    if not cfg.get("coat"):
        cv.hline(5, 10, 16, shade(cfg["pants"], 0.6))
    sway_l = -1 if frame == 2 else 0
    sway_r = -1 if frame == 1 else 0
    cv.rect(4, 12, 4, 15 + sway_l, c)
    cv.put(4, 16 + sway_l, s)
    cv.rect(11, 12, 11, 15 + sway_r, cd)
    cv.put(11, 16 + sway_r, shade(s, 0.85))
    if "pack" in cfg:
        pk = cfg["pack"]
        cv.rect(5, 11, 10, 16, pk)
        cv.hline(6, 9, 11, shade(pk, 1.2))
        cv.rect(5, 16, 10, 16, shade(pk, 0.7))
        cv.vline(5, 11, 16, shade(pk, 0.85))
        cv.vline(10, 11, 16, shade(pk, 0.7))
        cv.hline(6, 9, 14, shade(pk, 0.8))
        cv.put(7, 13, hx("4caf50"))
        cv.put(8, 13, hx("6ad06a"))
        cv.put(7, 12, hx("2e7d32"))
    cv.rect(4, 3, 11, 10, s)
    cv.rect(3, 4, 12, 9, s)
    if cfg["style"] == "hood":
        _hood(cv, cfg, back=True)
    elif cfg["style"] == "helmet":
        _hair_front(cv, dict(cfg, style="short"), back=True)
        _helmet(cv)
    else:
        _hair_front(cv, cfg, back=True)
        _hair_shine(cv, cfg, 4, 8, 2)
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
    cv.vline(6, 13, 16, shade(c, 1.12))
    cv.vline(9, 12, 17, cd)
    cv.hline(6, 9, 17, shade(c, 0.6))
    cv.hline(6, 8, 12, shade(c, 1.2))
    if cfg.get("coat"):
        cv.rect(5, 17, 10, 19, c)
        cv.vline(10, 17, 19, cd)
        cv.hline(5, 10, 19, shade(c, 0.7))
    else:
        cv.hline(6, 9, 16, shade(cfg["pants"], 0.6))
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
    cv.hline(4, 9, 10, shade(s, 0.92))
    cv.put(4, 7, OUTLINE)
    cv.put(4, 8, cfg.get("eyes", hx("6a4430")))
    cv.put(4, 9, hx("f08a8a"))
    cv.put(3, 10, shade(s, 0.75))
    if cfg["style"] == "hood":
        _hood(cv, cfg, side=True)
        return add_outline(cv.img)
    if cfg["style"] == "helmet":
        cfg = dict(cfg, style="short")
        helmet_after = True
    else:
        helmet_after = False
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
    _hair_shine(cv, cfg, 4, 8, 2)
    if helmet_after:
        _helmet(cv, side=True)
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


# Peatones (no son personajes de historia): chubasqueros en la Tierra, monos y cascos en Luna y Marte.
CROWD = {
    "crowd_e_1": {"hair": hx("2a2230"), "skin": hx("e0a87a"), "cloth": hx("2a6a8a"), "accent": hx("3de7c9"),
                  "pants": hx("2a2a36"), "boots": hx("1a1a22"), "style": "hood", "coat": True, "hood": hx("2a6a8a")},
    "crowd_e_2": {"hair": hx("d8d0c0"), "skin": hx("b07a58"), "cloth": hx("8a4a6a"), "accent": GOLD_BUCKLE,
                  "pants": hx("3a3048"), "boots": hx("2a1a22"), "style": "bun", "coat": True, "eyes": hx("3a5a3a")},
    "crowd_e_3": {"hair": hx("15121a"), "skin": hx("6a4028"), "cloth": hx("e8c040"), "accent": hx("2a2a36"),
                  "pants": hx("2a3048"), "boots": hx("1a1a22"), "style": "hood", "coat": True, "hood": hx("e8c040")},
    "crowd_e_4": {"hair": hx("c86a2a"), "skin": hx("f0c8a0"), "cloth": hx("4a5a4a"), "accent": hx("ff3ea5"),
                  "pants": hx("3a4a5a"), "boots": hx("e8eef5"), "style": "spiky", "eyes": hx("2a6a8a")},
    "crowd_m_1": {"hair": hx("3a2a20"), "skin": hx("d8a07a"), "cloth": hx("e8ecf2"), "accent": hx("f08a2c"),
                  "pants": hx("c8ccd4"), "boots": hx("5a6070"), "style": "helmet"},
    "crowd_m_2": {"hair": hx("f0e0a0"), "skin": hx("f2c8a8"), "cloth": hx("3a7ac8"), "accent": hx("e8ecf2"),
                  "pants": hx("2a4a7a"), "boots": hx("1a2a4a"), "style": "bob", "eyes": hx("2a5a8a")},
    "crowd_m_3": {"hair": hx("15121a"), "skin": hx("8a5a3a"), "cloth": hx("8a909c"), "accent": hx("3de7c9"),
                  "pants": hx("5a606c"), "boots": hx("2a2e36"), "style": "helmet"},
    "crowd_m_4": {"hair": hx("6a3a8a"), "skin": hx("eab98e"), "cloth": hx("2a9a90"), "accent": GOLD_BUCKLE,
                  "pants": hx("1e4a50"), "boots": hx("1a2228"), "style": "long", "glasses": hx("e8eef5")},
    "crowd_r_1": {"hair": hx("2a1a14"), "skin": hx("a86a44"), "cloth": hx("f08a2c"), "accent": hx("e8ecf2"),
                  "pants": hx("8a3a20"), "boots": hx("3a2a22"), "style": "helmet"},
    "crowd_r_2": {"hair": hx("d8402a"), "skin": hx("e8b088"), "cloth": hx("8a5a3a"), "accent": GOLD_BUCKLE,
                  "pants": hx("5a3a2a"), "boots": hx("2a1a18"), "style": "braids"},
    "crowd_r_3": {"hair": hx("e8e8e0"), "skin": hx("c48a64"), "cloth": hx("b0643c"), "accent": hx("3de7c9"),
                  "pants": hx("4a3a3a"), "boots": hx("1a1418"), "style": "short", "visor": hx("f4d35e")},
    "crowd_r_4": {"hair": hx("15121a"), "skin": hx("5a3420"), "cloth": hx("d8c8b8"), "accent": hx("c8302a"),
                  "pants": hx("8a7a6a"), "boots": hx("3a2a22"), "style": "helmet"},
}


def crowd_assets() -> None:
    import json
    by_planet = {"earth": [], "moon": [], "mars": []}
    key = {"e": "earth", "m": "moon", "r": "mars"}
    for name, cfg in CROWD.items():
        save(character_sheet(cfg), "crowd", f"{name}.png")
        by_planet[key[name.split("_")[1]]].append(f"res://assets/art/crowd/{name}.png")
    path = os.path.join(GAME, "assets", "data", "ambient", "crowd.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(by_planet, f, ensure_ascii=False, indent=2)
        f.write("\n")


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
    cv.hline(14, 18, 24, shade(s, 0.7))
    cv.hline(14, 18, 25, shade(s, 0.78))
    # cuello de la ropa con luz
    for x in range(8, 25):
        y = 33 - int(7 * math.sqrt(max(0.0, 1 - ((x - 16) / 13) ** 2)))
        if cv.get(x, y)[3]:
            cv.put(x, y, shade(c, 1.22))
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
    iris = cfg.get("eyes", hx("6a4430"))
    for ex in (11, 19):
        cv.rect(ex, 15, ex + 2, 18, OUTLINE)
        cv.put(ex, 17, iris)
        cv.put(ex + 2, 17, iris)
        cv.put(ex + 1, 18, shade(iris, 1.35))
        cv.put(ex, 15, hx("ffffff"))
        cv.put(ex, 16, mix_c(hx("ffffff"), iris, 0.3))
    # nariz con luz de arriba-izquierda
    cv.put(17, 20, shade(s, 0.8))
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
    hi = tuple(min(255, int(ch * 1.3 + 20)) for ch in h[:3]) + (255,)
    for x in range(9, 16):
        y = 6 - int(1.5 * math.sin((x - 9) / 6 * math.pi))
        for yy in (y, y + 1):
            if cv.get(x, yy) == h:
                cv.put(x, yy, hi)
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
    12 muro con pantalla, 13 mostrador, 14 estante de tienda, 15 estante de bar (jugos).
    Fila 3-4: 16-18 suelo con sombra bajo el muro (metal, madera, baldosa), 19 metal gastado,
    20 rejilla de suelo, 21 suelo con cables, 22 madera rayada, 23 baldosa agrietada,
    24 franjas de peligro, 25 sumidero, 26 muro con tuberías, 27 ventana a las estrellas,
    28 ventana a Marte, 29 muro con cartel, 30 muro con rejilla de ventilación, 31 muro de ladrillo."""
    rng = random.Random(91)
    atlas = Image.new("RGBA", (128, 64), CLEAR)

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

    floors = ((hx("3a4050"), hx("2a2e3a"), False), (hx("6a4a32"), hx("4a3222"), True),
              (hx("8a4a32"), hx("6a3222"), False))
    for i, (base, line, planks) in enumerate(floors):
        cv = floor(base, line, 1, planks)
        for y in range(7):
            for x in range(16):
                k = 0.55 + y * 0.065
                c = cv.get(x, y)
                cv.put(x, y, shade(c, k))
        tile(16 + i, cv)
    cv = floor(hx("3a4050"), hx("2a2e3a"), 1, False)
    for _ in range(18):
        cv.put(rng.randrange(16), rng.randrange(16), rng.choice((hx("4a5060"), hx("2e323e"), hx("5a4a3a"))))
    cv.ellipse(10, 10, 3, 2, hx("2e2a34"))
    tile(19, cv)
    cv = floor(hx("3a4050"), hx("2a2e3a"), 0, False)
    cv.rect(2, 2, 13, 13, hx("1a1c24"))
    for x in range(3, 13, 2):
        cv.vline(x, 2, 13, hx("4a5060"))
    cv.hline(2, 13, 2, hx("5a6070"))
    tile(20, cv)
    cv = floor(hx("3a4050"), hx("2a2e3a"), 2, False)
    for x in range(16):
        y = 7 + int(round(math.sin(x * 0.6) * 2))
        cv.put(x, y, hx("15121e"))
        cv.put(x, y + 1, hx("2a1a2a"))
        cv.put(x, 12 + (x // 5) % 2, hx("1a2a30"))
    cv.put(5, 7, NEON_CYAN)
    tile(21, cv)
    cv = floor(hx("6a4a32"), hx("4a3222"), 2, True)
    for _ in range(3):
        x, y = rng.randrange(1, 12), rng.randrange(1, 14)
        cv.hline(x, x + rng.randrange(2, 5), y, hx("8a6a4a"))
    tile(22, cv)
    cv = floor(hx("8a4a32"), hx("6a3222"), 1, False)
    x, y = 3, 2
    for _ in range(12):
        cv.put(x, y, hx("4a2218"))
        x += rng.choice((0, 1))
        y += 1
    tile(23, cv)
    haz = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            haz.put(x, y, hx("e0b030") if ((x + y) // 4) % 2 == 0 else hx("2a2430"))
    tile(24, haz)
    cv = floor(hx("3a4050"), hx("2a2e3a"), 0, False)
    cv.disc(8, 8, 4, hx("2a2e3a"))
    cv.disc(8, 8, 3, hx("15121e"))
    for x in range(6, 11, 2):
        cv.vline(x, 6, 10, hx("4a5060"))
    tile(25, cv)
    cv = wall(hx("5a606c"), None)
    for y, col in ((4, hx("8a6a4a")), (9, hx("6a7080"))):
        cv.rect(0, y, 15, y + 2, col)
        cv.hline(0, 15, y, shade(col, 1.3))
        cv.hline(0, 15, y + 2, shade(col, 0.6))
    cv.rect(6, 3, 8, 12, hx("4a5060"))
    cv.put(7, 7, NEON_GOLD)
    tile(26, cv)

    def window(sky: tuple, ground_col: tuple | None) -> Canvas:
        cv = wall(hx("5a606c"), None)
        cv.rect(2, 2, 13, 12, hx("2a2e3a"))
        cv.rect(3, 3, 12, 11, sky)
        for _ in range(5):
            cv.put(rng.randrange(3, 13), rng.randrange(3, 9), hx("e8eef5"))
        if ground_col:
            cv.rect(3, 9, 12, 11, ground_col)
            cv.hline(3, 7, 8, shade(ground_col, 0.8))
        cv.vline(7, 3, 11, hx("2a2e3a"))
        cv.hline(3, 12, 3, shade(sky, 1.6))
        return cv

    tile(27, window(hx("0b1230"), None))
    tile(28, window(hx("5a3a4a"), hx("b05a34")))
    cv = wall(hx("6a6460"), None)
    cv.rect(3, 2, 12, 13, hx("e8e0c8"))
    cv.rect(4, 3, 11, 7, hx("3a6aa0"))
    cv.disc(8, 5, 2, NEON_GOLD)
    for y in (9, 11):
        cv.hline(4, 11, y, hx("6a6460"))
    tile(29, cv)
    cv = wall(hx("5a606c"), None)
    cv.rect(3, 4, 12, 11, hx("2a2e3a"))
    for y in range(5, 11, 2):
        cv.hline(4, 11, y, hx("8a90a0"))
    tile(30, cv)
    cv = wall(hx("8a4a36"), None)
    for y in range(0, 16, 4):
        cv.hline(0, 15, y, hx("5a2a20"))
        off = 0 if (y // 4) % 2 == 0 else 4
        for x in range(off, 16, 8):
            cv.vline(x, y, y + 3, hx("5a2a20"))
    tile(31, cv)
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


# ------------------------------------------------- escenarios: decoración y calcas
# Calcas planas (decal_*: charcos con reflejo de neón, grietas, cráteres, hojas) que el
# mapa dibuja bajo todo lo demás (z = -1) y props de ambiente para Tierra, Luna, Marte e interiores.

def decal_puddle(w: int, h: int, seed: int) -> Image.Image:
    """Charco translúcido: refleja el cielo nocturno y manchas de neón; borde húmedo más oscuro."""
    rng = random.Random(seed)
    cv = Canvas(w, h)
    cx, cy = w / 2, h / 2

    def inside(x: int, y: int) -> bool:
        wob = 1 + 0.16 * math.sin(x * 0.7 + seed) + 0.1 * math.cos(y * 1.3 + seed)
        return ((x + 0.5 - cx) / (cx - 0.5)) ** 2 + ((y + 0.5 - cy) / (cy - 0.5)) ** 2 <= wob * 0.82

    for y in range(h):
        for x in range(w):
            if inside(x, y):
                edge = not (inside(x - 1, y) and inside(x + 1, y) and inside(x, y - 1) and inside(x, y + 1))
                cv.put(x, y, (40, 44, 70, 120) if edge else (96, 120, 168, 92))
    for col in (NEON_PINK, NEON_CYAN):
        rx, ry = rng.randrange(3, max(4, w - 5)), rng.randrange(2, max(3, h - 2))
        for dx in range(-2, 3):
            if cv.get(rx + dx, ry)[3]:
                cv.put(rx + dx, ry, (col[0], col[1], col[2], 120 if abs(dx) < 2 else 70))
        if cv.get(rx, ry + 1)[3]:
            cv.put(rx, ry + 1, (col[0], col[1], col[2], 70))
    for x in range(2, w - 2):
        if cv.get(x, 2)[3] and rng.random() < 0.35:
            cv.put(x, 2, (200, 225, 255, 110))
    return cv.img


def decal_crack(seed: int) -> Image.Image:
    rng = random.Random(seed)
    cv = Canvas(24, 16)
    for start in ((2, 8), (12, 3)):
        x, y = start
        for _ in range(12):
            cv.put(x, y, (20, 18, 26, 190))
            x += 1
            y = max(0, min(15, y + rng.choice((-1, 0, 0, 1))))
    return cv.img


def decal_manhole() -> Image.Image:
    cv = Canvas(16, 10)
    cv.ellipse(8, 5, 7, 4.5, (40, 40, 52, 255))
    cv.ellipse(8, 5, 5.5, 3.3, (70, 72, 86, 255))
    for x in range(4, 13, 2):
        cv.vline(x, 3, 7, (46, 48, 60, 255))
    return cv.img


def decal_oil() -> Image.Image:
    cv = Canvas(16, 10)
    cv.ellipse(8, 5, 7, 4, (16, 14, 22, 200))
    cv.ellipse(6, 4, 3, 1.5, (90, 40, 120, 140))
    cv.ellipse(10, 6, 2, 1, (40, 120, 110, 140))
    return cv.img


def decal_leaves(seed: int) -> Image.Image:
    rng = random.Random(seed)
    cv = Canvas(24, 12)
    for _ in range(16):
        x, y = rng.randrange(1, 22), rng.randrange(1, 10)
        col = rng.choice([hx("8a5a2a"), hx("a07038"), hx("6a4a2a"), hx("b88a48")])
        cv.put(x, y, col)
        cv.put(x + 1, y, shade(col, 0.8))
    for _ in range(3):
        x, y = rng.randrange(2, 20), rng.randrange(2, 9)
        cv.rect(x, y, x + 1, y, hx("c8c8d0"))
    return cv.img


def decal_crater(base: str, seed: int) -> Image.Image:
    rng = random.Random(seed)
    c = hx(base)
    cv = Canvas(40, 26)
    cv.ellipse(20, 13, 19, 12, shade(c, 1.12))
    cv.ellipse(20, 13.5, 16.5, 10, shade(c, 0.7))
    cv.ellipse(21, 15, 14, 8, shade(c, 0.82))
    cv.ellipse(23, 17, 9, 5, shade(c, 0.9))
    for _ in range(12):
        a = rng.random() * math.tau
        cv.put(int(20 + math.cos(a) * 18), int(13 + math.sin(a) * 11.5), shade(c, 1.25))
    return cv.img


def decal_drift(base: str, seed: int) -> Image.Image:
    rng = random.Random(seed)
    c = hx(base)
    cv = Canvas(32, 12)
    for y in range(12):
        for x in range(32):
            if ((x - 16) / 15) ** 2 + ((y - 6) / 5) ** 2 <= 1 and rng.random() < 0.7:
                cv.put(x, y, (*shade(c, 1.12)[:3], 200))
    for x in range(4, 28):
        cv.put(x, 6 + int(math.sin(x * 0.5) * 1.5), shade(c, 1.25))
    return cv.img


def decal_trash(seed: int) -> Image.Image:
    rng = random.Random(seed)
    cv = Canvas(20, 12)
    for _ in range(7):
        x, y = rng.randrange(1, 17), rng.randrange(1, 10)
        col = rng.choice([hx("c8c8d0"), hx("8a8a98"), NEON_PINK, hx("6a8a2a"), hx("a05a3a")])
        cv.rect(x, y, x + rng.randrange(0, 3), y, col)
    return cv.img


def prop_boulder(base: str, seed: int) -> Image.Image:
    rng = random.Random(seed)
    c = hx(base)
    cv = Canvas(32, 26)
    cv.ellipse(16, 22, 15, 3.5, (0, 0, 0, 70))
    cv.ellipse(15, 15, 13, 9, shade(c, 0.85))
    cv.ellipse(12, 12, 9, 7, c)
    cv.ellipse(20, 14, 8, 7, shade(c, 0.95))
    cv.ellipse(10, 9, 5, 3.5, shade(c, 1.2))
    cv.ellipse(19, 19, 9, 3.5, shade(c, 0.7))
    for _ in range(10):
        cv.put(rng.randrange(6, 26), rng.randrange(8, 20), shade(c, rng.choice((0.75, 1.25))))
    cv.vline(17, 9, 15, shade(c, 0.65))
    return add_outline(cv.img)


def prop_rocks_small(base: str, seed: int) -> Image.Image:
    c = hx(base)
    cv = Canvas(20, 12)
    for (x, y, rx, ry) in ((5, 7, 4, 3), (12, 8, 3, 2.5), (16, 6, 2, 1.8)):
        cv.ellipse(x, y + 2, rx, ry * 0.5, (0, 0, 0, 60))
        cv.ellipse(x, y, rx, ry, c)
        cv.ellipse(x - 1, y - 1, rx * 0.5, ry * 0.5, shade(c, 1.2))
    return add_outline(cv.img)


def prop_tank_o2() -> Image.Image:
    cv = Canvas(16, 28)
    cv.ellipse(8, 26, 6, 1.5, (0, 0, 0, 80))
    cv.rect(3, 6, 12, 25, hx("dfe6ee"))
    cv.rect(10, 6, 12, 25, hx("a8b0bc"))
    cv.ellipse(7.5, 6, 4.5, 2, hx("f0f4f8"))
    cv.rect(6, 1, 9, 4, hx("6a7080"))
    cv.hline(3, 12, 11, hx("3a8ac8"))
    cv.hline(3, 12, 12, hx("3a8ac8"))
    draw_text3(cv, "O2", 4, 15, hx("2a3a6a"))
    cv.rect(4, 21, 6, 23, hx("2a2e3a"))
    cv.put(5, 22, NEON_GREEN)
    return add_outline(cv.img)


def prop_tanks_pair() -> Image.Image:
    cv = Canvas(34, 32)
    cv.ellipse(17, 30, 15, 2, (0, 0, 0, 80))
    for x0, col in ((2, hx("c8cdd6")), (17, hx("b8a888"))):
        cv.rect(x0, 7, x0 + 13, 29, col)
        cv.rect(x0 + 10, 7, x0 + 13, 29, shade(col, 0.75))
        cv.ellipse(x0 + 6.5, 7, 6.5, 2.5, shade(col, 1.15))
        cv.hline(x0, x0 + 13, 13, shade(col, 0.6))
        cv.hline(x0, x0 + 13, 24, shade(col, 0.6))
    cv.rect(14, 15, 19, 16, hx("6a7080"))
    cv.disc(16.5, 15.5, 2, hx("e04a4a"))
    draw_text3(cv, "CH4", 19, 17, hx("5a2a1a"))
    cv.rect(4, 17, 9, 21, hx("2a2e3a"))
    cv.hline(5, 8, 19, NEON_CYAN)
    return add_outline(cv.img)


def prop_pipe_run() -> Image.Image:
    cv = Canvas(48, 16)
    cv.ellipse(24, 14, 23, 1.5, (0, 0, 0, 70))
    for x0 in (3, 41):
        cv.rect(x0, 8, x0 + 3, 14, hx("4a5060"))
    cv.rect(0, 4, 47, 9, hx("8a90a0"))
    cv.hline(0, 47, 4, hx("c6ced8"))
    cv.hline(0, 47, 9, hx("4a5060"))
    for x in (12, 30):
        cv.rect(x, 3, x + 2, 10, hx("6a7080"))
    cv.rect(21, 0, 24, 3, hx("6a7080"))
    cv.disc(22.5, 1, 2.5, hx("e04a4a"))
    cv.rect(36, 5, 38, 8, hx("f4c430"))
    return add_outline(cv.img)


def prop_sat_dish() -> Image.Image:
    cv = Canvas(26, 30)
    cv.ellipse(13, 28, 9, 2, (0, 0, 0, 80))
    cv.rect(11, 16, 14, 27, hx("5a6478"))
    cv.rect(7, 26, 18, 28, hx("3a4458"))
    img = cv.img
    d = ImageDraw.Draw(img)
    d.ellipse((1, 2, 24, 18), fill=hx("dfe6ee"))
    d.ellipse((4, 4, 22, 15), fill=hx("b8c0cc"))
    d.line((13, 10, 18, 3), fill=hx("6a7080"))
    d.point([(18, 3), (19, 2)], fill=hx("e86a6a"))
    return add_outline(img)


def prop_solar_array() -> Image.Image:
    cv = Canvas(34, 24)
    cv.ellipse(17, 22, 15, 2, (0, 0, 0, 80))
    cv.rect(15, 12, 18, 22, hx("5a6478"))
    img = cv.img
    d = ImageDraw.Draw(img)
    d.polygon([(3, 3), (31, 3), (33, 14), (1, 14)], fill=hx("1e2e5a"))
    for x in range(5, 31, 5):
        d.line((x, 3, x - 1 + (x > 17) * 2, 14), fill=hx("4a6aa8"))
    d.line((2, 8, 32, 8), fill=hx("4a6aa8"))
    d.line((3, 3, 31, 3), fill=hx("8ab0e8"))
    return add_outline(img)


def prop_hydro_rack() -> Image.Image:
    rng = random.Random(41)
    cv = Canvas(32, 26)
    cv.ellipse(16, 24, 15, 2, (0, 0, 0, 80))
    cv.rect(1, 4, 30, 23, hx("2a3040"))
    for y in (10, 17, 23):
        cv.rect(2, y - 1, 29, y, hx("5a6478"))
        cv.hline(2, 29, y - 2, shade(NEON_PINK, 0.8))
        for x in range(3, 29, 3):
            h = rng.randrange(2, 5)
            cv.vline(x, y - 1 - h, y - 2, hx("3fae5a"))
            cv.put(x, y - 1 - h, hx("7fe08a"))
            if rng.random() < 0.3:
                cv.put(x + 1, y - 2 - h // 2, hx("e04a4a"))
    cv.rect(1, 2, 30, 4, hx("4a5060"))
    cv.hline(3, 28, 3, NEON_PINK)
    return add_outline(cv.img)


def prop_cable_spool() -> Image.Image:
    cv = Canvas(18, 16)
    cv.ellipse(9, 14, 8, 1.5, (0, 0, 0, 70))
    cv.ellipse(9, 8, 7, 6.5, hx("8a6a4a"))
    cv.ellipse(9, 8, 5.5, 5, hx("2a2a34"))
    for r in (4.5, 3):
        cv.ellipse(9, 8, r, r * 0.9, hx("e07a2a") if r > 4 else hx("c05a1a"))
    cv.disc(9, 8, 1.5, hx("8a6a4a"))
    cv.hline(14, 17, 13, hx("e07a2a"))
    return add_outline(cv.img)


def prop_beacon() -> Image.Image:
    cv = Canvas(10, 24)
    cv.ellipse(5, 22, 4, 1.2, (0, 0, 0, 80))
    cv.rect(4, 6, 5, 22, hx("5a6478"))
    cv.rect(2, 20, 7, 22, hx("3a4458"))
    for y in range(8, 20, 4):
        cv.rect(4, y, 5, y + 1, hx("f4c430"))
    cv.disc(4.5, 3.5, 2.5, hx("ff4a4a"))
    cv.put(4, 2, hx("ffd0d0"))
    return add_outline(cv.img)


def prop_antenna_mast() -> Image.Image:
    cv = Canvas(18, 52)
    cv.ellipse(9, 50, 7, 1.5, (0, 0, 0, 80))
    for y in range(6, 50):
        half = 1 + (y - 6) * 5 // 44
        cv.put(9 - half, y, hx("7a8494"))
        cv.put(9 + half, y, hx("5a6478"))
        if y % 6 == 0:
            cv.hline(9 - half, 9 + half, y, hx("7a8494"))
            cv.put(9 - half + (y // 6) % (2 * half + 1), y + 3, hx("5a6478"))
    cv.vline(9, 0, 6, hx("8a90a0"))
    cv.disc(9, 1, 1.5, hx("ff4a4a"))
    cv.rect(10, 16, 13, 20, hx("dfe6ee"))
    return add_outline(cv.img)


def prop_engine_block() -> Image.Image:
    cv = Canvas(26, 20)
    cv.ellipse(13, 18, 12, 2, (0, 0, 0, 80))
    cv.rect(3, 5, 22, 16, hx("5a5e6a"))
    cv.rect(3, 5, 22, 7, hx("8a90a0"))
    for x in range(6, 21, 4):
        cv.rect(x, 2, x + 2, 5, hx("6a7080"))
    cv.rect(18, 9, 24, 13, hx("3a3e4a"))
    cv.disc(8, 11, 2.5, hx("2a2e3a"))
    cv.put(8, 11, hx("e07a2a"))
    cv.hline(4, 21, 15, hx("3a2a2a"))
    return add_outline(cv.img)


def prop_tool_board() -> Image.Image:
    cv = Canvas(32, 18)
    cv.rect(0, 0, 31, 17, hx("6a5a48"))
    for y in range(2, 17, 3):
        for x in range(2, 31, 3):
            cv.put(x, y, hx("4a3e30"))
    cv.rect(3, 3, 4, 13, hx("b8bec8"))
    cv.rect(2, 3, 5, 5, hx("b8bec8"))
    cv.rect(9, 4, 10, 14, hx("e07a2a"))
    cv.rect(8, 3, 11, 5, hx("8a90a0"))
    cv.rect(15, 3, 16, 12, hx("8a90a0"))
    cv.disc(15.5, 13, 2, hx("e04a4a"))
    cv.rect(21, 4, 26, 6, hx("f4c430"))
    cv.rect(22, 7, 23, 13, hx("2a2430"))
    cv.disc(28, 11, 2.5, hx("3a3a44"))
    return add_outline(cv.img)


def prop_arcade() -> Image.Image:
    cv = Canvas(18, 32)
    cv.ellipse(9, 30, 8, 1.5, (0, 0, 0, 80))
    cv.rect(2, 3, 15, 29, hx("2a1a4a"))
    cv.rect(13, 3, 15, 29, hx("1a1030"))
    cv.rect(2, 1, 15, 4, NEON_PINK)
    cv.rect(4, 7, 12, 15, hx("0b1220"))
    cv.rect(5, 8, 11, 14, shade(NEON_CYAN, 0.35))
    cv.rect(7, 10, 8, 11, NEON_GOLD)
    cv.put(10, 12, NEON_PINK)
    cv.rect(3, 17, 14, 19, hx("3a2a5a"))
    cv.disc(6, 18, 1, hx("e04a4a"))
    cv.disc(10, 18, 1, NEON_CYAN)
    cv.disc(12, 18, 1, NEON_GOLD)
    cv.vline(2, 4, 28, NEON_CYAN)
    return add_outline(cv.img)


def prop_smoothie_machine() -> Image.Image:
    cv = Canvas(18, 26)
    cv.rect(2, 6, 15, 25, hx("b8bec8"))
    cv.rect(13, 6, 15, 25, hx("8a90a0"))
    for i, col in enumerate((NEON_PINK, hx("f4a030"), NEON_GREEN)):
        x = 3 + i * 4
        cv.rect(x, 1, x + 2, 9, hx("dfe6ee"))
        cv.rect(x, 4, x + 2, 9, col)
    cv.rect(3, 12, 12, 16, hx("2a2e3a"))
    draw_text3(cv, "JUGO", 1, 18, hx("2a3a6a"))
    cv.rect(6, 23, 9, 24, hx("4a5060"))
    return add_outline(cv.img)


def prop_server_rack() -> Image.Image:
    rng = random.Random(23)
    cv = Canvas(16, 30)
    cv.ellipse(8, 28, 7, 1.5, (0, 0, 0, 80))
    cv.rect(2, 2, 13, 27, hx("1e2230"))
    cv.rect(2, 2, 13, 3, hx("4a5060"))
    for y in range(5, 26, 3):
        cv.hline(3, 12, y, hx("3a4050"))
        for x in range(4, 12, 2):
            if rng.random() < 0.5:
                cv.put(x, y + 1, rng.choice((NEON_GREEN, NEON_CYAN, NEON_GOLD, hx("ff4a4a"))))
    return add_outline(cv.img)


def prop_neon_wall(text: str, color: tuple) -> Image.Image:
    w = text_width(text) + 8
    cv = Canvas(w, 11)
    cv.rect(0, 0, w - 1, 10, hx("15121e"))
    glow = shade(color, 0.35)
    cv.rect(1, 1, w - 2, 9, glow)
    draw_text3(cv, text, 4, 3, color)
    cv.hline(1, w - 2, 1, color)
    cv.hline(1, w - 2, 9, color)
    return cv.img


def prop_corp_crate(color: tuple, mark: str) -> Image.Image:
    cv = Canvas(16, 16)
    cv.ellipse(8, 15, 7, 1.2, (0, 0, 0, 80))
    cv.rect(1, 3, 14, 15, hx("4a4e5a"))
    cv.rect(1, 3, 14, 5, hx("6a7080"))
    cv.vline(14, 3, 15, hx("2e323e"))
    cv.rect(3, 8, 12, 12, shade(color, 0.3))
    draw_text3(cv, mark, 8 - text_width(mark) // 2, 8, color)
    return add_outline(cv.img)


def prop_scrap_fence() -> Image.Image:
    rng = random.Random(52)
    cv = Canvas(32, 22)
    cols = [hx("6a6460"), hx("8a5a3a"), hx("5a6478"), hx("7a6a5a")]
    x = 0
    while x < 32:
        w = rng.randrange(4, 8)
        top = rng.randrange(2, 7)
        col = rng.choice(cols)
        cv.rect(x, top, min(31, x + w - 1), 20, col)
        for xx in range(x, min(32, x + w), 2):
            cv.vline(xx, top + 1, 20, shade(col, 0.8))
        if rng.random() < 0.5:
            cv.put(x + 1, top + 3, hx("a05a2a"))
        x += w
    cv.hline(0, 31, 21, hx("2a2430"))
    return add_outline(cv.img)


def prop_dead_bush() -> Image.Image:
    cv = Canvas(16, 14)
    img = cv.img
    d = ImageDraw.Draw(img)
    for (x1, y1) in ((3, 3), (8, 1), (13, 4), (5, 6), (11, 7)):
        d.line((8, 13, x1, y1), fill=hx("6a4a32"))
    d.point([(3, 3), (13, 4), (8, 1)], fill=hx("a07038"))
    return add_outline(img)


def prop_rover_wreck() -> Image.Image:
    cv = Canvas(34, 22)
    cv.ellipse(17, 19, 16, 2.5, (0, 0, 0, 80))
    cv.rect(4, 8, 27, 14, hx("9aa0a8"))
    cv.rect(4, 12, 27, 14, hx("6a7080"))
    cv.rect(8, 5, 18, 8, hx("8a6a3a"))
    cv.rect(20, 4, 23, 7, hx("5a6478"))
    for x in (7, 24):
        cv.disc(x + 0.5, 17, 3, hx("2a2a30"))
        cv.disc(x + 0.5, 17, 1, hx("6a6a74"))
    cv.ellipse(16, 18, 2.5, 1.5, hx("3a3a44"))
    for (x, y) in ((10, 9), (15, 10), (22, 11), (6, 13)):
        cv.put(x, y, hx("a05a2a"))
    cv.rect(28, 10, 32, 11, hx("6a7080"))
    return add_outline(cv.img)


def scenery_assets() -> None:
    props = {
        "decal_puddle": decal_puddle(32, 12, 3),
        "decal_puddle_s": decal_puddle(18, 8, 7),
        "decal_puddle_l": decal_puddle(44, 16, 11),
        "decal_crack": decal_crack(5),
        "decal_crack_b": decal_crack(9),
        "decal_manhole": decal_manhole(),
        "decal_oil": decal_oil(),
        "decal_leaves": decal_leaves(4),
        "decal_trash": decal_trash(6),
        "decal_crater_mars": decal_crater("c45e34", 13),
        "decal_crater_moon": decal_crater("9a9da4", 17),
        "decal_drift_mars": decal_drift("c45e34", 21),
        "decal_drift_moon": decal_drift("9a9da4", 22),
        "boulder_mars": prop_boulder("a4462a", 31),
        "boulder_moon": prop_boulder("8a8d94", 33),
        "rocks_mars": prop_rocks_small("8a3b26", 0),
        "rocks_moon": prop_rocks_small("7a7d84", 0),
        "tank_o2": prop_tank_o2(),
        "tanks_pair": prop_tanks_pair(),
        "pipe_run": prop_pipe_run(),
        "sat_dish": prop_sat_dish(),
        "solar_array": prop_solar_array(),
        "hydro_rack": prop_hydro_rack(),
        "cable_spool": prop_cable_spool(),
        "beacon": prop_beacon(),
        "antenna_mast": prop_antenna_mast(),
        "engine_block": prop_engine_block(),
        "tool_board": prop_tool_board(),
        "arcade": prop_arcade(),
        "smoothie_machine": prop_smoothie_machine(),
        "server_rack": prop_server_rack(),
        "neon_batidos": prop_neon_wall("BATIDOS", NEON_PINK),
        "neon_abierto": prop_neon_wall("ABIERTO", NEON_GREEN),
        "neon_taller": prop_neon_wall("REPARAMOS", NEON_GOLD),
        "crate_marscorp": prop_corp_crate(NEON_PINK, "MC"),
        "crate_agronet": prop_corp_crate(NEON_GREEN, "AG"),
        "scrap_fence": prop_scrap_fence(),
        "dead_bush": prop_dead_bush(),
        "rover_wreck": prop_rover_wreck(),
    }
    for name, img in props.items():
        save(img, "props", f"{name}.png")
    import third_party
    third_party.main()


# ------------------------------------------------------------------- tiles

def noise_tile(rng: random.Random, base: tuple, dark: tuple, light: tuple, density: float = 0.12) -> Canvas:
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            r = rng.random()
            cv.put(x, y, dark if r < density else light if r > 1 - density * 0.6 else base)
    return cv


def tileset(palette: dict, seed: int) -> Image.Image:
    """Atlas 8×4 de 16 px: 0-3 suelo, 4 cráter, 5 roca (sólido), 6 sombra/duna,
    7 hielo/sedimento, 8 suelo metálico, 9 muro metálico (sólido), 10 marca de pista,
    11 piedras pequeñas. Detalle (ver rocky_detail_tiles): 12 ondas de duna, 13 grietas,
    14 microcráter, 15 grava, 16-17 huellas de rover (horizontal/vertical), 18 placa gastada,
    19 rejilla, 20 franjas de peligro, 21 placa con cable, 22-25 borde de placa con polvo
    (arriba/abajo/izquierda/derecha), 26 pisadas, 27 polvo oscuro, 28 borde de hielo,
    29 borde de sombra, 30 piedrecitas sueltas, 31 tira de luz en placa."""
    rng = random.Random(seed)
    atlas = Image.new("RGBA", (16 * 8, 16 * 4), CLEAR)
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
    tiles += rocky_detail_tiles(palette, rng)
    for i, t in enumerate(tiles):
        atlas.paste(t, ((i % 8) * 16, (i // 8) * 16))
    return atlas


METAL = hx("6a7080")
METAL_HI = hx("8a90a0")
METAL_LO = hx("4a5060")


def metal_plate(rng: random.Random, worn: float = 0.0, dust: tuple | None = None) -> Canvas:
    cv = Canvas(16, 16)
    cv.rect(0, 0, 15, 15, METAL)
    cv.hline(0, 15, 0, METAL_HI)
    cv.vline(0, 0, 15, METAL_HI)
    cv.hline(0, 15, 15, METAL_LO)
    cv.vline(15, 0, 15, METAL_LO)
    for (x, y) in ((2, 2), (13, 2), (2, 13), (13, 13)):
        cv.put(x, y, METAL_LO)
    for _ in range(int(worn * 40)):
        x, y = rng.randrange(1, 15), rng.randrange(1, 15)
        cv.put(x, y, dust if dust and rng.random() < 0.6 else shade(METAL, rng.choice((0.85, 1.1))))
    return cv


def rocky_detail_tiles(palette: dict, rng: random.Random) -> list:
    """Tiles 12-31 del atlas rocoso: variaciones del suelo y transiciones."""
    base, dark, light = palette["base"], palette["dark"], palette["light"]
    out = []

    def ground(density: float = 0.1) -> Canvas:
        return noise_tile(rng, base, dark, light, density)

    cv = ground(0.06)  # 12 ondas de duna
    for row in (3, 8, 13):
        for x in range(16):
            y = row + int(round(math.sin((x + row) * 0.55) * 1.2))
            cv.put(x, y, light)
            cv.put(x, y + 1, dark)
    out.append(cv.img)
    cv = ground(0.08)  # 13 grietas
    x, y = 2, 3
    while x < 15 and y < 15:
        cv.put(x, y, shade(dark, 0.7))
        x += 1
        y += rng.choice((0, 1, 1))
        if rng.random() < 0.25:
            cv.put(x, y + 1, shade(dark, 0.8))
    cv.put(9, 4, shade(dark, 0.7))
    cv.put(10, 5, shade(dark, 0.7))
    out.append(cv.img)
    cv = ground(0.08)  # 14 microcráter
    cv.ellipse(8, 9, 4, 3, dark)
    cv.ellipse(8.5, 9.5, 3, 2, shade(base, 0.85))
    cv.hline(5, 11, 12, light)
    cv.hline(6, 10, 6, shade(dark, 0.9))
    out.append(cv.img)
    cv = ground(0.05)  # 15 grava
    for _ in range(14):
        gx, gy = rng.randrange(0, 15), rng.randrange(0, 15)
        cv.put(gx, gy, palette["rock"])
        cv.put(gx, gy + 1, shade(dark, 0.8))
        if rng.random() < 0.4:
            cv.put(gx + 1, gy, shade(palette["rock"], 1.2))
    out.append(cv.img)
    for vertical in (False, True):  # 16-17 huellas de rover
        cv = ground(0.07)
        for lane in (3, 11):
            for t in range(16):
                px, py = (lane, t) if vertical else (t, lane)
                c = shade(dark, 0.85) if t % 3 else shade(dark, 0.7)
                cv.put(px, py, c)
                cv.put(px + (0 if vertical else 0), py + (0 if vertical else 1), shade(base, 0.92))
                if vertical:
                    cv.put(px + 1, py, shade(base, 0.92))
        out.append(cv.img)
    out.append(metal_plate(rng, 0.6, shade(base, 0.9)).img)  # 18 placa gastada
    cv = metal_plate(rng, 0.1)  # 19 rejilla
    cv.rect(3, 3, 12, 12, hx("2a2e3a"))
    for gx in range(4, 12, 2):
        cv.vline(gx, 3, 12, METAL_LO)
    cv.hline(3, 12, 3, METAL_HI)
    out.append(cv.img)
    cv = Canvas(16, 16)  # 20 franjas de peligro
    for y in range(16):
        for x in range(16):
            cv.put(x, y, hx("f4c430") if ((x + y) // 4) % 2 == 0 else hx("2a2430"))
    for _ in range(14):
        cv.put(rng.randrange(16), rng.randrange(16), shade(base, 0.9))
    out.append(cv.img)
    cv = metal_plate(rng, 0.15)  # 21 placa con cable
    for x in range(16):
        y = 9 + int(round(math.sin(x * 0.5) * 1.5))
        cv.put(x, y, hx("1a1a22"))
        cv.put(x, y + 1, hx("3a2a2a"))
    cv.put(6, 9, NEON_PINK)
    out.append(cv.img)
    for side in ("top", "bottom", "left", "right"):  # 22-25 bordes con polvo
        cv = metal_plate(rng, 0.2, base)
        for y in range(16):
            for x in range(16):
                d = {"top": y, "bottom": 15 - y, "left": x, "right": 15 - x}[side]
                if d <= 1 or (d <= 4 and rng.random() < (5 - d) * 0.18):
                    cv.put(x, y, rng.choice((base, base, dark, light)))
        out.append(cv.img)
    cv = ground(0.06)  # 26 pisadas
    for i, (fx, fy) in enumerate(((3, 13), (6, 9), (4, 5), (7, 1))):
        cv.rect(fx, fy, fx + 1, fy + 2, shade(dark, 0.85))
        cv.put(fx, fy + 3, shade(dark, 0.8))
        cv.put(fx + 6 + (i % 2), fy + 1, shade(dark, 0.85))
    out.append(cv.img)
    cv = noise_tile(rng, base, dark, light, 0.1)  # 27 polvo oscuro (motas, sin bloque de color)
    for _ in range(26):
        cv.put(rng.randrange(16), rng.randrange(16), shade(dark, 0.9))
    out.append(cv.img)
    cv = noise_tile(rng, palette["special"], palette["special_dark"], palette["special_light"], 0.15)
    for y in range(16):  # 28 borde de hielo/sedimento salpicado de suelo
        for x in range(16):
            if rng.random() < 0.28:
                cv.put(x, y, rng.choice((base, dark)))
    out.append(cv.img)
    cv = noise_tile(rng, palette["shadow"], shade(palette["shadow"], 0.8), shade(palette["shadow"], 1.2), 0.15)
    for y in range(16):  # 29 borde de sombra
        for x in range(16):
            if rng.random() < 0.3:
                cv.put(x, y, rng.choice((base, dark, shade(palette["shadow"], 1.3))))
    out.append(cv.img)
    cv = ground(0.07)  # 30 piedrecitas sueltas
    for (sx, sy) in ((4, 5), (11, 9), (6, 12)):
        cv.ellipse(sx, sy, 1.8, 1.3, palette["rock"])
        cv.put(int(sx) - 1, int(sy) - 1, shade(palette["rock"], 1.25))
        cv.hline(int(sx) - 1, int(sx) + 1, int(sy) + 2, shade(dark, 0.75))
    out.append(cv.img)
    cv = metal_plate(rng, 0.1)  # 31 tira de luz
    cv.rect(2, 6, 13, 9, hx("1a2a30"))
    cv.hline(3, 12, 7, NEON_CYAN)
    cv.hline(3, 12, 8, shade(NEON_CYAN, 0.6))
    out.append(cv.img)
    return out


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


# ------------------------------------------------- capítulo 4: combate y taller
# Robots de los Antihumanistas (acero oscuro + visor rojo), piezas del taller de Bruno,
# ingredientes del metano, iconos de elemento para las «cerraduras» y fondo de batalla.

AH_RED = hx("e0283c")
AH_STEEL = hx("4a4e5a")
AH_STEEL_L = hx("727888")
AH_STEEL_D = hx("2c2f38")


def _emblem(cv: Canvas, cx: int, cy: int, color: tuple) -> None:
    """Emblema antihumanista: anillo roto atravesado por una barra."""
    for ang in range(0, 360, 20):
        if 200 <= ang <= 250:
            continue
        a = math.radians(ang)
        cv.put(int(round(cx + math.cos(a) * 2.6)), int(round(cy + math.sin(a) * 2.6)), color)
    for i in range(-3, 4):
        cv.put(cx + i, cy - i, color)


def robot_ah7(off: bool = False) -> Image.Image:
    """Centinela AH-7: robot minero reprogramado, puños hidráulicos y visor rojo."""
    cv = Canvas(32, 40)
    steel, light, dark = (shade(AH_STEEL, 0.8), shade(AH_STEEL_L, 0.8), AH_STEEL_D) if off else (AH_STEEL, AH_STEEL_L, AH_STEEL_D)
    eye = hx("3a2a30") if off else AH_RED
    # piernas
    cv.rect(9, 28, 13, 37, dark)
    cv.rect(18, 28, 22, 37, dark)
    cv.rect(7, 36, 14, 39, steel)
    cv.rect(17, 36, 24, 39, steel)
    # torso
    cv.rect(7, 13, 24, 29, steel)
    cv.rect(7, 13, 24, 15, light)
    cv.vline(24, 13, 29, dark)
    cv.rect(10, 18, 21, 26, dark)
    _emblem(cv, 15, 22, shade(AH_RED, 0.5) if off else AH_RED)
    # hombros y brazos
    cv.rect(2, 13, 7, 18, light)
    cv.rect(24, 13, 29, 18, light)
    cv.rect(3, 18, 6, 26, dark)
    cv.rect(25, 18, 28, 26, dark)
    cv.rect(1, 26, 7, 32, steel)
    cv.rect(24, 26, 30, 32, steel)
    cv.hline(1, 7, 29, dark)
    cv.hline(24, 30, 29, dark)
    # cabeza
    cv.rect(10, 3, 21, 12, steel)
    cv.rect(10, 3, 21, 4, light)
    cv.rect(11, 6, 20, 9, hx("15121e"))
    cv.hline(12, 19, 7, eye)
    if not off:
        cv.put(13, 7, hx("ff9a9a"))
    cv.vline(15, 0, 2, dark)
    cv.put(15, 0, eye)
    # óxido
    for (x, y) in ((8, 27), (22, 16), (12, 11), (27, 30), (4, 30)):
        cv.put(x, y, hx("8a4a2a"))
    if off:
        for (x, y) in ((24, 1), (26, 0), (28, 2)):
            cv.put(x, y, hx("b8bec8"))
    return add_outline(cv.img)


def drone_ah(off: bool = False) -> Image.Image:
    """Dron vigía AH-D: esfera con hélices y un ojo rojo."""
    cv = Canvas(20, 16)
    body = shade(AH_STEEL, 0.8) if off else AH_STEEL
    cv.hline(1, 7, 2, AH_STEEL_L)
    cv.hline(12, 18, 2, AH_STEEL_L)
    cv.vline(4, 2, 5, AH_STEEL_D)
    cv.vline(15, 2, 5, AH_STEEL_D)
    cv.disc(10, 9, 5.5, body)
    cv.disc(9, 8, 3.5, AH_STEEL_L if not off else body)
    cv.disc(10, 9.5, 2.2, hx("15121e"))
    cv.disc(10, 9.5, 1.2, hx("3a2a30") if off else AH_RED)
    cv.hline(6, 14, 14, AH_STEEL_D)
    return add_outline(cv.img)


def prop_wreck() -> Image.Image:
    """Carguero de MarsCorp estrellado: casco abollado, aleta rota y franja rosa."""
    cv = Canvas(56, 32)
    cv.ellipse(28, 27, 26, 4, hx("6a3428"))
    cv.ellipse(26, 18, 22, 9, hx("b8c0cc"))
    cv.ellipse(26, 15, 20, 6, hx("dfe6ee"))
    cv.ellipse(26, 22, 20, 4, hx("8a919c"))
    cv.hline(8, 44, 18, NEON_PINK)
    cv.rect(44, 6, 50, 16, hx("8a919c"))
    cv.rect(46, 3, 49, 6, hx("5a606c"))
    for x in range(10, 40, 7):
        cv.rect(x, 13, x + 2, 15, hx("2a7fa0"))
    cv.rect(18, 19, 28, 25, hx("2a2a30"))
    cv.rect(20, 20, 26, 24, hx("4a4e5a"))
    for (x, y) in ((6, 16), (7, 21), (33, 23), (40, 12), (12, 24)):
        cv.put(x, y, hx("8a4a2a"))
    return add_outline(cv.img)


def prop_engine_part() -> Image.Image:
    """Motor de metano tirado en la arena: tobera acampanada y tuberías."""
    cv = Canvas(28, 22)
    cv.rect(3, 5, 13, 16, hx("8a919c"))
    cv.rect(3, 5, 13, 7, hx("b8c0cc"))
    for i in range(10):
        cv.vline(13 + i, 7 - i // 2, 14 + i // 2, hx("c87a3a") if i < 7 else hx("e0a050"))
    cv.ellipse(23, 10.5, 2, 6, hx("3a2a20"))
    cv.hline(4, 12, 11, NEON_CYAN)
    cv.vline(6, 1, 5, hx("5a606c"))
    cv.vline(10, 2, 5, hx("5a606c"))
    cv.ellipse(14, 19, 12, 2, hx("6a3428", 160))
    return add_outline(cv.img)


def prop_workbench() -> Image.Image:
    cv = Canvas(32, 24)
    cv.rect(1, 8, 30, 11, hx("6a5a48"))
    cv.rect(1, 8, 30, 8, hx("8a7a60"))
    cv.rect(2, 12, 4, 23, hx("4a3e30"))
    cv.rect(27, 12, 29, 23, hx("4a3e30"))
    cv.rect(6, 13, 25, 17, hx("3a4458"))
    cv.rect(5, 2, 12, 7, hx("1e2a3e"))
    cv.hline(6, 11, 4, NEON_GOLD)
    cv.put(8, 5, NEON_CYAN)
    cv.rect(17, 4, 19, 7, hx("b8c0cc"))
    cv.rect(21, 5, 26, 7, hx("c87a3a"))
    cv.put(24, 15, NEON_GOLD)
    return add_outline(cv.img)


def prop_distiller(on: bool) -> Image.Image:
    """Reactor Sabatier casero: depósito, serpentín y ventanita (verde cuando funciona)."""
    cv = Canvas(24, 32)
    cv.rect(4, 8, 17, 30, hx("8a919c"))
    cv.ellipse(10.5, 8, 6.5, 3, hx("b8c0cc"))
    cv.vline(17, 8, 30, hx("5a606c"))
    cv.rect(7, 14, 14, 20, hx("15121e"))
    glow = NEON_GREEN if on else hx("3a4458")
    cv.rect(8, 15, 13, 19, glow)
    if on:
        cv.put(9, 16, hx("e0ffe8"))
    for y in range(10, 28, 3):
        cv.hline(18, 21, y, hx("c87a3a"))
        cv.put(22, y + 1, hx("c87a3a"))
    cv.rect(5, 24, 16, 26, hx("5a606c"))
    draw_text3(cv, "CH4", 5, 1, NEON_GREEN if on else hx("8a91a3"))
    return add_outline(cv.img)


def prop_compressor(on: bool) -> Image.Image:
    cv = Canvas(18, 26)
    cv.rect(2, 8, 15, 25, hx("5a6478"))
    cv.rect(2, 8, 15, 10, hx("7a8494"))
    cv.vline(15, 8, 25, hx("3a4458"))
    for y in range(12, 23, 2):
        cv.hline(4, 13, y, hx("3a4458"))
    cv.rect(6, 2, 11, 7, hx("8a919c"))
    cv.put(8, 4, NEON_CYAN if on else hx("3a4458"))
    cv.put(13, 10, NEON_GREEN if on else AH_RED)
    return add_outline(cv.img)


def prop_meteorite() -> Image.Image:
    """Meteorito de hierro y níquel: oscuro, pulido por el viento, con brillos metálicos."""
    cv = Canvas(24, 18)
    cv.ellipse(12, 11, 10, 6, hx("3a3438"))
    cv.ellipse(10, 9, 7, 4.5, hx("5a5458"))
    cv.ellipse(15, 13, 5, 2.5, hx("2a2428"))
    for (x, y) in ((8, 7), (12, 9), (6, 11), (16, 10)):
        cv.put(x, y, hx("d8dce4"))
    cv.put(9, 7, hx("a8b0bc"))
    return add_outline(cv.img)


def prop_drill_rig() -> Image.Image:
    cv = Canvas(16, 30)
    cv.vline(4, 4, 27, hx("7a8494"))
    cv.vline(11, 4, 27, hx("7a8494"))
    for y in range(6, 26, 5):
        cv.hline(4, 11, y, hx("5a6478"))
    cv.rect(2, 1, 13, 4, NEON_GOLD)
    cv.vline(7, 4, 29, hx("b8c0cc"))
    cv.vline(8, 4, 29, hx("9aa2ae"))
    cv.rect(1, 27, 14, 29, hx("3a4458"))
    return add_outline(cv.img)


def prop_service_pump() -> Image.Image:
    cv = Canvas(16, 30)
    cv.rect(2, 4, 12, 29, hx("2a3a6a"))
    cv.vline(12, 4, 29, hx("1e2a4e"))
    cv.rect(4, 8, 10, 13, hx("0b1220"))
    cv.hline(5, 9, 10, NEON_GOLD)
    cv.rect(13, 12, 14, 22, hx("3a3440"))
    cv.put(14, 23, hx("8a91a3"))
    draw_text3(cv, "COMB", 0, 0, NEON_GOLD)
    cv.rect(4, 18, 10, 24, hx("1e2a4e"))
    cv.put(7, 21, NEON_GREEN)
    return add_outline(cv.img)


def icon_engine() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(1, 5, 7, 11, hx("b8c0cc"))
    cv.rect(1, 5, 7, 6, hx("e8eef5"))
    for i in range(6):
        cv.vline(8 + i, 6 - i // 2, 10 + i // 2, hx("c87a3a"))
    cv.vline(14, 2, 14, hx("e0a050"))
    cv.put(3, 8, NEON_CYAN)
    return add_outline(cv.img)


def icon_canister(body: str, cap: str, label: tuple) -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(4, 4, 11, 14, hx(body))
    cv.vline(11, 4, 14, shade(hx(body), 0.7))
    cv.rect(6, 1, 9, 3, hx(cap))
    cv.rect(5, 7, 10, 10, hx("0b1220"))
    cv.hline(6, 9, 8, label)
    return add_outline(cv.img)


def icon_medkit() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(2, 5, 13, 14, hx("e8eef5"))
    cv.rect(2, 12, 13, 14, hx("c6d1dd"))
    cv.rect(6, 2, 9, 4, hx("8a91a3"))
    cv.rect(7, 6, 8, 12, NEON_GREEN)
    cv.rect(5, 8, 10, 9, NEON_GREEN)
    return add_outline(cv.img)


def icon_repair_kit() -> Image.Image:
    cv = Canvas(16, 16)
    cv.rect(2, 8, 13, 14, hx("c87a3a"))
    cv.hline(2, 13, 8, hx("e0a050"))
    for i in range(7):
        cv.put(4 + i, 7 - i, hx("b8c0cc"))
        cv.put(5 + i, 7 - i, hx("8a91a3"))
    cv.disc(11.5, 1.5, 1.6, hx("b8c0cc"))
    cv.put(7, 11, NEON_GOLD)
    return add_outline(cv.img)


def element_icon(kind: str) -> Image.Image:
    cv = Canvas(12, 12)
    if kind == "impacto":
        cv.disc(6, 6, 4.6, hx("c8ccd4"))
        cv.disc(6, 6, 1.8, hx("2a2f38"))
        for (x, y) in ((6, 0), (6, 11), (0, 6), (11, 6), (2, 2), (9, 9), (2, 9), (9, 2)):
            cv.put(x, y, hx("c8ccd4"))
    elif kind == "electricidad":
        for (x, y) in ((7, 0), (6, 1), (5, 2), (4, 3), (3, 4), (4, 5), (5, 5), (6, 5), (7, 5), (6, 6),
                       (5, 7), (4, 8), (3, 9), (2, 10), (8, 1), (7, 2), (6, 3), (5, 4)):
            cv.put(x, y, NEON_GOLD)
    else:
        cv.disc(6, 6, 2.8, hx("ffd98a"))
        for a in range(0, 360, 45):
            r = math.radians(a)
            cv.put(int(round(6 + math.cos(r) * 4.6)), int(round(6 + math.sin(r) * 4.6)), hx("ffb040"))
    return add_outline(cv.img)


def combat_assets() -> None:
    props = {
        "robot_ah7": robot_ah7(),
        "robot_ah7_off": robot_ah7(off=True),
        "drone_ah": drone_ah(),
        "drone_ah_off": drone_ah(off=True),
        "wreck_marscorp": prop_wreck(),
        "engine_part": prop_engine_part(),
        "workbench": prop_workbench(),
        "distiller_off": prop_distiller(False),
        "distiller_on": prop_distiller(True),
        "compressor_off": prop_compressor(False),
        "compressor_on": prop_compressor(True),
        "meteorite": prop_meteorite(),
        "drill_rig": prop_drill_rig(),
        "service_pump": prop_service_pump(),
        "holo_antihuman": prop_holo_ad("ANTIHUMANISTAS", AH_RED),
    }
    for name, img in props.items():
        save(img, "props", f"{name}.png")
    icons = {
        "methane_engine": icon_engine(),
        "mars_ice_core": icon_vial("bfe8ff", "ffffff"),
        "co2_tank": icon_canister("8a91a3", "5a606c", NEON_CYAN),
        "nickel_catalyst": icon_rock("a8b0bc"),
        "orders_chip": icon_chip("ff3ea5"),
        "medkit": icon_medkit(),
        "repair_kit": icon_repair_kit(),
        "aux_tank": icon_canister("c87a3a", "8a91a3", NEON_GOLD),
    }
    for name, img in icons.items():
        save(img, "items", f"{name}.png")
    for kind in ("impacto", "electricidad", "luz"):
        save(element_icon(kind), "ui", f"element_{kind}.png")
    # El fondo de combate lo genera tools/pixelart/battle_art.py (capas + versión plana).


# ------------------------------------------------------------------- main

def main() -> None:
    sprites: dict = {}
    for name, cfg in CHARACTERS.items():
        save(character_sheet(cfg), "characters", f"{name}.png")
        save(portrait(cfg), "portraits", f"{name}.png")
        sprites[f"{name}_front"] = char_front(cfg, 0)
        sprites[f"{name}_back"] = char_back(cfg, 0)
    crowd_assets()
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
    scenery_assets()
    combat_assets()
    illustrations(sprites)
    import city_art  # ciudades vivas: atlas urbanos, edificios 3/4, mobiliario (usa este módulo)
    city_art.main()
    print("OK →", ART)


if __name__ == "__main__":
    main()
