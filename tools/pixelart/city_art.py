"""Ciudades vivas de The Seed: atlas de suelo urbano, edificios en 3/4, mobiliario y peatones.

Uso:  python3 tools/pixelart/city_art.py   (también lo llama generate.py al final)
Salida:
  game/assets/art/tiles/city_{earth,moon,mars}.png + .json   (mismos nombres de tile, distinto material)
  game/assets/art/props/bld_{e,m,r}_*.png + buildings.json   (edificios: tejado d×16 px + fachada «wall» px)
  game/assets/art/props/<mobiliario>.png y calcas decal_*
  game/assets/art/crowd/crowd_{e,m,r}_N.png + game/assets/data/ambient/crowd.json
Determinista (semillas fijas). Luz desde arriba-izquierda, contorno oscuro de 1 px.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate as G  # noqa: E402
from generate import Canvas, hx, shade, add_outline, OUTLINE, CLEAR, FONT_3X5  # noqa: E402

ART = G.ART
DATA = os.path.join(G.GAME, "assets", "data")
CYAN, GOLD, PINK, GREEN = hx("3de7c9"), hx("f4d35e"), hx("ff3ea5"), hx("7dff9a")
WARM = hx("ffd27a")
NIGHT = hx("15121e")


def mix(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (int(a[3] + (b[3] - a[3]) * t),)


def alpha(c: tuple, a: int) -> tuple:
    return (c[0], c[1], c[2], a)


def blend_put(cv: Canvas, x: int, y: int, c: tuple, t: float) -> None:
    """Mezcla c sobre el píxel existente (para brillos y sombras suaves)."""
    old = cv.get(x, y)
    if old[3] == 0:
        return
    cv.put(x, y, mix(old, (c[0], c[1], c[2], old[3]), t))


def save_json(obj, *parts: str) -> None:
    path = os.path.join(*parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ------------------------------------------------------------------ texto con tildes

ACCENTS = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N"}


def draw_text(cv: Canvas, text: str, x: int, y: int, color: tuple) -> None:
    for ch in text.upper():
        base = ACCENTS.get(ch, ch)
        bits = FONT_3X5.get(base, FONT_3X5[" "])
        for i, b in enumerate(bits):
            if b == "1":
                cv.put(x + i % 3, y + i // 3, color)
        if ch in ACCENTS:
            if ch == "Ñ":
                cv.hline(x, x + 2, y - 2, color)
            else:
                cv.put(x + 2, y - 2, color)
        x += 4


def text_w(text: str) -> int:
    return len(text) * 4 - 1


def neon_sign(cv: Canvas, text: str, cx: int, y: int, color: tuple, panel: tuple = NIGHT) -> None:
    """Letrero luminoso: caja oscura con marco, letras de neón con halo y brillos."""
    w = text_w(text)
    x0 = cx - w // 2
    cv.rect(x0 - 3, y - 3, x0 + w + 2, y + 7, panel)
    cv.hline(x0 - 3, x0 + w + 2, y - 3, shade(color, 0.6))
    cv.hline(x0 - 3, x0 + w + 2, y + 7, shade(color, 0.45))
    cv.vline(x0 - 3, y - 3, y + 7, shade(color, 0.5))
    cv.vline(x0 + w + 2, y - 3, y + 7, shade(color, 0.4))
    halo = Canvas(cv.w, cv.h)
    draw_text(halo, text, x0, y, color)
    for yy in range(max(0, y - 3), min(cv.h, y + 8)):
        for xx in range(max(0, x0 - 2), min(cv.w, x0 + w + 2)):
            if halo.get(xx, yy)[3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if halo.get(xx + dx, yy + dy)[3]:
                    cv.put(xx, yy, mix(panel, color, 0.35))
                    break
    draw_text(cv, text, x0, y, color)
    for xx in range(x0, x0 + w):
        if cv.get(xx, y + 1) == color and xx % 3 == 0:
            cv.put(xx, y + 1, hx("ffffff"))


# ================================================================== 1. ATLAS DE SUELO

PALETTES = {
    "earth": {
        "soil": hx("7e705c"), "soil_d": hx("665a4a"), "soil_l": hx("948468"),
        "grass": hx("8c8a4a"), "grass_d": hx("6c6a3a"), "grass_l": hx("a8a25e"),
        "pave": hx("8e929c"), "pave_d": hx("70747e"), "pave_l": hx("a6aab4"),
        "curb": hx("b6bac4"), "curb_d": hx("5a5e68"),
        "road": hx("3a3c48"), "road_d": hx("2e3039"), "road_l": hx("474a57"),
        "line": CYAN, "cross": hx("c6cad4"),
        "plaza": hx("9a8c80"), "plaza_d": hx("7a6e64"), "plaza_l": hx("b0a294"), "emblem": GOLD,
        "bed": hx("4a3a2e"), "bed_l": hx("5e4a38"),
        "metal": hx("6a7080"), "metal_l": hx("8a90a0"), "metal_d": hx("4a505e"),
        "hedge": hx("6a6638"), "hedge_d": hx("4e4a2a"), "hedge_l": hx("8a8450"),
        "cliff": hx("5a5650"), "cliff_d": hx("3e3a36"), "cliff_l": hx("78726a"),
        "canal": hx("2e5a58"), "canal_l": hx("4a8a80"), "canal_d": hx("1e3e40"),
        "wall": hx("8a8478"), "wall_d": hx("625c52"),
        "rubble": True,
        "ice": hx("8ab8c0"), "ice_l": hx("c8e8ee"), "ice_d": hx("5a8890"),
        "sed": hx("a49a86"), "sed_l": hx("bab09a"), "sed_d": hx("8a806c"),
    },
    "moon": {
        "soil": hx("9a9da4"), "soil_d": hx("80838b"), "soil_l": hx("b2b5bc"),
        "grass": hx("767982"), "grass_d": hx("62656e"), "grass_l": hx("8c8f98"),
        "pave": hx("b4bac6"), "pave_d": hx("8c929e"), "pave_l": hx("ccd2dc"),
        "curb": hx("dfe4ec"), "curb_d": hx("5e6470"),
        "road": hx("4a4e5c"), "road_d": hx("3c404c"), "road_l": hx("5a5e6c"),
        "line": hx("8ad8ff"), "cross": hx("e8ecf2"),
        "plaza": hx("a6aebc"), "plaza_d": hx("848c9a"), "plaza_l": hx("c0c8d4"), "emblem": CYAN,
        "bed": hx("5a5048"), "bed_l": hx("6e6258"),
        "metal": hx("7a8294"), "metal_l": hx("9aa2b4"), "metal_d": hx("586070"),
        "hedge": hx("d8dce4"), "hedge_d": hx("9aa0ac"), "hedge_l": hx("f0f2f6"),
        "cliff": hx("6e7178"), "cliff_d": hx("4e5158"), "cliff_l": hx("8e9198"),
        "canal": hx("3a3e48"), "canal_l": hx("50545e"), "canal_d": hx("2a2d36"),
        "wall": hx("c8ced8"), "wall_d": hx("8e94a0"),
        "rubble": False,
        "ice": hx("bfe8ff"), "ice_l": hx("eaf8ff"), "ice_d": hx("86b4d0"),
        "sed": hx("bcc0c8"), "sed_l": hx("d4d8de"), "sed_d": hx("a0a4ac"),
    },
    "mars": {
        "soil": hx("c05c34"), "soil_d": hx("a2482a"), "soil_l": hx("d4764a"),
        "grass": hx("d08a58"), "grass_d": hx("b4703e"), "grass_l": hx("e4a676"),
        "pave": hx("c88a62"), "pave_d": hx("a46c4a"), "pave_l": hx("dca47c"),
        "curb": hx("e8bc94"), "curb_d": hx("7a4630"),
        "road": hx("5c3a32"), "road_d": hx("4a2e28"), "road_l": hx("6e4a3e"),
        "line": GOLD, "cross": hx("f0dcc0"),
        "plaza": hx("b47454"), "plaza_d": hx("945a40"), "plaza_l": hx("cc9068"), "emblem": GOLD,
        "bed": hx("5a3426"), "bed_l": hx("6e4230"),
        "metal": hx("7a7480"), "metal_l": hx("9a94a0"), "metal_d": hx("5a5460"),
        "hedge": hx("9a5a3a"), "hedge_d": hx("74422a"), "hedge_l": hx("b8744c"),
        "cliff": hx("8a3b26"), "cliff_d": hx("6a2c1c"), "cliff_l": hx("a84e32"),
        "canal": hx("5a2a20"), "canal_l": hx("7a3e2e"), "canal_d": hx("441e18"),
        "wall": hx("c8865c"), "wall_d": hx("9a6040"),
        "rubble": False,
        "ice": hx("d8eef8"), "ice_l": hx("f4fbff"), "ice_d": hx("a8c8dc"),
        "sed": hx("d8b48a"), "sed_l": hx("ecd0a8"), "sed_d": hx("b8946a"),
    },
}


def _noise_fill(cv, rng, base, dark, light, density=0.14):
    for y in range(16):
        for x in range(16):
            r = rng.random()
            cv.put(x, y, dark if r < density else light if r > 1 - density * 0.7 else base)


def t_soil(P, rng, variant):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["soil"], P["soil_d"], P["soil_l"], 0.10)
    # manchas suaves y alguna piedrecita
    for _ in range(2 + variant):
        x, y = rng.randrange(1, 15), rng.randrange(1, 15)
        cv.put(x, y, P["soil_d"])
        cv.put(x + 1, y, P["soil_d"])
        if rng.random() < 0.5:
            cv.put(x, y - 1, P["soil_l"])
    if variant == 3:
        x, y = rng.randrange(3, 12), rng.randrange(3, 12)
        cv.rect(x, y, x + 1, y, shade(P["soil_d"], 0.9))
        cv.put(x, y - 1, P["soil_l"])
    return cv


def t_soil_rough(P, rng, variant):
    cv = t_soil(P, rng, 1)
    if variant == 0:  # grietas
        x, y = rng.randrange(2, 6), rng.randrange(2, 6)
        for k in range(10):
            cv.put(x, y, shade(P["soil_d"], 0.8))
            x += 1
            y += rng.choice((0, 1, 1))
            if x > 14 or y > 14:
                break
    else:  # guijarros
        for _ in range(5):
            x, y = rng.randrange(1, 14), rng.randrange(1, 14)
            cv.rect(x, y, x + 1, y + 1, P["cliff_l"] if "cliff_l" in P else P["soil_l"])
            cv.put(x + 1, y + 1, P["cliff_d"])
    return cv


def t_grass(P, rng, variant):
    if not P.get("rubble"):
        return t_dust(P, rng, variant)
    cv = t_soil(P, rng, 0)
    for _ in range(9 + variant * 3):
        x, y = rng.randrange(0, 15), rng.randrange(2, 16)
        h = rng.randrange(2, 4)
        cv.vline(x, y - h, y, P["grass"])
        cv.put(x, y - h, P["grass_l"])
        cv.put(x + 1, y, P["grass_d"])
    return cv


def t_dust(P, rng, variant):
    """Luna/Marte: ondas de polvo (Marte) o regolito oscuro con piedrecitas (Luna)."""
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["grass"], P["grass_d"], P["grass_l"], 0.1)
    for k in range(3):
        y0 = 2 + k * 5 + variant
        for x in range(16):
            y = y0 + int(1.2 * math.sin((x + k * 4 + variant * 3) * 0.45))
            cv.put(x, y % 16, P["grass_l"])
            cv.put(x, (y + 1) % 16, P["grass_d"])
    for _ in range(2 + variant):
        x, y = rng.randrange(1, 14), rng.randrange(1, 14)
        cv.put(x, y, P["cliff_d"])
        cv.put(x, y - 1, P["cliff_l"])
    return cv


def _slab_joints(cv, P, rng, size=8):
    """Losas de acera: juntas oscuras con borde de luz arriba-izquierda."""
    for y in range(16):
        for x in range(16):
            if x % size == 0 or y % size == 0:
                cv.put(x, y, P["pave_d"])
            elif x % size == 1 or y % size == 1:
                blend_put(cv, x, y, P["pave_l"], 0.6)


def t_pave(P, rng, variant):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["pave"], shade(P["pave"], 0.94), shade(P["pave"], 1.05), 0.12)
    _slab_joints(cv, P, rng)
    if variant == 1:  # mancha / desgaste
        x, y = rng.randrange(3, 10), rng.randrange(3, 10)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (2, 1), (1, 2)):
            blend_put(cv, x + dx, y + dy, P["pave_d"], 0.45)
    elif variant == 2:  # grieta fina
        x = rng.randrange(2, 6)
        for y in range(2, 7):
            cv.put(x + (y % 2), y, P["pave_d"])
    elif variant == 3:  # tapa pequeña
        cv.rect(10, 10, 13, 13, P["metal_d"])
        cv.rect(11, 11, 12, 12, P["metal"])
    return cv


def _curb(cv, P, side):
    c, d = P["curb"], P["curb_d"]
    if side == "n":
        cv.hline(0, 15, 0, d)
        cv.hline(0, 15, 1, c)
        cv.hline(0, 15, 2, shade(c, 0.9))
    elif side == "s":
        cv.hline(0, 15, 12, c)
        cv.hline(0, 15, 13, shade(c, 0.8))
        cv.hline(0, 15, 14, shade(c, 0.66))
        cv.hline(0, 15, 15, d)
    elif side == "w":
        cv.vline(0, 0, 15, d)
        cv.vline(1, 0, 15, c)
        cv.vline(2, 0, 15, shade(c, 0.92))
    elif side == "e":
        cv.vline(13, 0, 15, shade(c, 0.9))
        cv.vline(14, 0, 15, shade(c, 0.75))
        cv.vline(15, 0, 15, d)


def t_pave_edge(P, rng, sides):
    cv = t_pave(P, rng, 0)
    for s in sides:
        _curb(cv, P, s)
    if "n" in sides and "w" in sides:
        cv.put(0, 0, CLEAR)
    if "n" in sides and "e" in sides:
        cv.put(15, 0, CLEAR)
    return cv


def t_road(P, rng, variant):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["road"], P["road_d"], P["road_l"], 0.12)
    if variant == 1:  # parche
        x, y = rng.randrange(2, 8), rng.randrange(2, 8)
        cv.rect(x, y, x + 5, y + 4, shade(P["road"], 0.9))
        cv.hline(x, x + 5, y, P["road_l"])
    elif variant == 2:  # fisura
        x, y = rng.randrange(1, 5), rng.randrange(4, 12)
        for k in range(9):
            cv.put(x + k, y + (k // 3) % 2, P["road_d"])
    return cv


def _guide(cv, P, horizontal):
    line, glow = P["line"], mix(P["road"], P["line"], 0.35)
    for i in range(16):
        on = (i % 8) < 5
        if horizontal:
            if on:
                cv.put(i, 7, line)
                cv.put(i, 8, shade(line, 0.8))
                cv.put(i, 6, glow)
                cv.put(i, 9, glow)
        else:
            if on:
                cv.put(7, i, line)
                cv.put(8, i, shade(line, 0.8))
                cv.put(6, i, glow)
                cv.put(9, i, glow)


def t_road_line(P, rng, horizontal):
    cv = t_road(P, rng, 0)
    _guide(cv, P, horizontal)
    return cv


def t_cross(P, rng, horizontal):
    """Franjas para cruzar una calle horizontal (cross_h: franjas verticales) o vertical."""
    cv = t_road(P, rng, 0)
    c = P["cross"]
    for i in range(16):
        for j in range(16):
            k = i if horizontal else j
            if 2 <= (k % 8) <= 5:
                x, y = (i, j)
                if 1 <= (j if horizontal else i) <= 14:
                    cv.put(x, y, c if rng.random() > 0.08 else shade(c, 0.8))
    return cv


def t_rail(P, rng):
    cv = t_road(P, rng, 0)
    for x in range(0, 16, 4):
        cv.rect(x, 4, x + 2, 11, shade(P["road_d"], 0.85))
    for y, c in ((5, P["metal_l"]), (6, P["metal_d"]), (10, P["metal_l"]), (11, P["metal_d"])):
        cv.hline(0, 15, y, c)
    for x in (2, 10):
        cv.put(x, 8, P["line"])
        cv.put(x + 1, 8, shade(P["line"], 0.7))
    return cv


def t_plaza(P, rng, variant):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["plaza"], shade(P["plaza"], 0.94), shade(P["plaza"], 1.05), 0.1)
    # adoquín en espiga
    for y in range(16):
        for x in range(16):
            u = (x + (y // 4) * 2 * (1 if variant == 0 else -1)) % 8
            if y % 4 == 0 or u == 0:
                cv.put(x, y, P["plaza_d"])
            elif y % 4 == 1 or u == 1:
                blend_put(cv, x, y, P["plaza_l"], 0.5)
    return cv


def t_plaza_center(P, rng):
    cv = t_plaza(P, rng, 0)
    e = P["emblem"]
    cv.disc(8, 8, 7, shade(P["plaza_d"], 0.9))
    cv.disc(8, 8, 6, P["plaza_l"])
    cv.disc(8, 8, 5, shade(e, 0.55))
    # semilla con brote
    cv.ellipse(8, 10, 2.5, 2, e)
    cv.vline(8, 4, 8, mix(e, GREEN, 0.6))
    cv.put(7, 5, GREEN)
    cv.put(9, 4, GREEN)
    cv.put(10, 5, GREEN)
    cv.put(7, 9, hx("ffffff"))
    return cv


def t_soil_bed(P, rng):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["bed"], shade(P["bed"], 0.85), P["bed_l"], 0.18)
    for y in (3, 8, 13):
        cv.hline(0, 15, y, shade(P["bed"], 0.7))
        cv.hline(0, 15, y - 1, P["bed_l"])
    return cv


def t_grate(P, rng):
    cv = t_pave(P, rng, 0)
    cv.rect(2, 3, 13, 12, P["metal_d"])
    cv.rect(3, 4, 12, 11, NIGHT)
    for x in range(3, 13, 2):
        cv.vline(x, 4, 11, P["metal"])
    cv.hline(2, 13, 3, P["metal_l"])
    return cv


def t_hatch(P, rng):
    cv = t_pave(P, rng, 0)
    cv.rect(2, 2, 13, 13, P["metal_d"])
    cv.rect(3, 3, 12, 12, P["metal"])
    cv.hline(3, 12, 3, P["metal_l"])
    for x in range(4, 12, 2):
        cv.put(x, 7, P["metal_d"])
        cv.put(x + 1, 8, P["metal_d"])
    cv.rect(10, 10, 11, 11, GOLD)
    return cv


def t_pad(P, rng, mark):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["metal"], shade(P["metal"], 0.92), shade(P["metal"], 1.06), 0.1)
    for y in range(16):
        for x in range(16):
            if x % 16 == 0 or y % 16 == 0:
                cv.put(x, y, P["metal_d"])
            elif x == 1 or y == 1:
                cv.put(x, y, P["metal_l"])
    for (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)):
        cv.put(x, y, P["metal_d"])
    if mark == "mark":
        for y in range(16):
            for x in range(16):
                if ((x + y) // 4) % 2 == 0:
                    cv.put(x, y, hx("e8c03a"))
                else:
                    cv.put(x, y, hx("2a2830"))
    elif mark == "line":
        cv.rect(0, 6, 15, 9, hx("e8e4d8"))
        cv.hline(0, 15, 6, hx("ffffff"))
    return cv


def t_hedge(P, rng, horizontal, planet):
    cv = Canvas(16, 16)
    if planet == "earth":
        # seto seco: masa de ramas con brillos
        for y in range(16):
            for x in range(16):
                inside = (2 <= y <= 15) if horizontal else (1 <= x <= 14)
                if inside:
                    r = rng.random()
                    cv.put(x, y, P["hedge_d"] if r < 0.3 else P["hedge_l"] if r > 0.85 else P["hedge"])
        if horizontal:
            for x in range(0, 16, 3):
                cv.put(x + rng.randrange(0, 2), 1, P["hedge"])
            cv.hline(0, 15, 15, shade(P["hedge_d"], 0.8))
        for _ in range(4):
            cv.put(rng.randrange(1, 15), rng.randrange(4, 14), hx("a06a3a"))
    else:
        # barrera de módulos (Luna) / muro de sacos de regolito (Marte)
        if horizontal:
            cv.rect(0, 4, 15, 14, P["hedge"])
            cv.hline(0, 15, 4, P["hedge_l"])
            cv.rect(0, 12, 15, 14, P["hedge_d"])
            cv.vline(7, 5, 14, P["hedge_d"])
            cv.vline(15, 5, 14, P["hedge_d"])
            cv.hline(0, 15, 15, shade(P["hedge_d"], 0.7))
            if planet == "moon":
                cv.rect(2, 8, 5, 9, hx("f08a2c"))
                cv.rect(10, 8, 13, 9, hx("f08a2c"))
        else:
            cv.rect(3, 0, 12, 15, P["hedge"])
            cv.vline(3, 0, 15, P["hedge_l"])
            cv.vline(11, 0, 15, P["hedge_d"])
            cv.vline(12, 0, 15, shade(P["hedge_d"], 0.8))
            cv.hline(3, 12, 7, P["hedge_d"])
            if planet == "moon":
                cv.rect(6, 2, 8, 4, hx("f08a2c"))
    return cv


def t_cliff(P, rng, variant, planet):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["cliff"], P["cliff_d"], P["cliff_l"], 0.18)
    # bloques/rocas con luz arriba-izquierda
    for _ in range(3 + variant):
        x, y = rng.randrange(0, 12), rng.randrange(0, 12)
        w, h = rng.randrange(3, 7), rng.randrange(3, 6)
        cv.rect(x, y, x + w, y + h, P["cliff"])
        cv.hline(x, x + w, y, P["cliff_l"])
        cv.vline(x, y, y + h, P["cliff_l"])
        cv.hline(x, x + w, y + h, P["cliff_d"])
        cv.vline(x + w, y, y + h, P["cliff_d"])
    if planet == "earth" and variant == 2:  # escombro con hierros
        cv.vline(5, 2, 9, hx("7a4a32"))
        cv.vline(11, 4, 12, hx("7a4a32"))
        cv.put(5, 2, hx("a06a4a"))
    return cv


def t_canal(P, rng):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["canal"], P["canal_d"], P["canal_l"], 0.08)
    for _ in range(3):
        x, y = rng.randrange(1, 11), rng.randrange(2, 14)
        cv.hline(x, x + rng.randrange(2, 5), y, P["canal_l"])
    cv.hline(0, 15, 0, P["curb_d"])
    cv.hline(0, 15, 1, shade(P["canal"], 0.7))
    return cv


def t_wall_low(P, rng):
    cv = Canvas(16, 16)
    cv.rect(0, 5, 15, 13, P["wall"])
    cv.hline(0, 15, 5, mix(P["wall"], hx("ffffff"), 0.25))
    cv.hline(0, 15, 6, mix(P["wall"], hx("ffffff"), 0.1))
    cv.rect(0, 10, 15, 13, P["wall_d"])
    for x in (0, 8):
        cv.vline(x, 7, 13, P["wall_d"])
    cv.hline(0, 15, 14, shade(P["wall_d"], 0.6))
    for _ in range(3):
        cv.put(rng.randrange(1, 15), rng.randrange(7, 10), shade(P["wall"], 0.9))
    return cv


def t_ice(P, rng, variant):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["ice"], P["ice_d"], P["ice_l"], 0.06)
    # grietas del hielo y reflejos
    x, y = rng.randrange(1, 6), rng.randrange(2, 8)
    for k in range(8):
        cv.put(x + k, y + (k * (1 + variant)) // 4, P["ice_d"])
    for _ in range(3):
        x, y = rng.randrange(2, 13), rng.randrange(2, 13)
        cv.put(x, y, hx("ffffff"))
        cv.put(x + 1, y, P["ice_l"])
    return cv


def t_ice_edge(P, rng):
    """Orilla: el hielo arriba, el suelo natural asoma abajo con borde irregular."""
    cv = t_soil(P, rng, 0)
    ice = t_ice(P, random.Random(rng.random()), 0)
    for x in range(16):
        edge = 9 + int(2 * math.sin(x * 0.9)) + rng.randrange(0, 2)
        for y in range(edge):
            cv.put(x, y, ice.get(x, y))
        cv.put(x, edge, P["ice_l"])
        cv.put(x, edge + 1, shade(P["soil_d"], 0.85))
    return cv


def t_sediment(P, rng, variant):
    cv = Canvas(16, 16)
    _noise_fill(cv, rng, P["sed"], P["sed_d"], P["sed_l"], 0.1)
    # vetas onduladas del abanico
    for k in range(3):
        y0 = 3 + k * 5 + variant
        for x in range(16):
            y = y0 + int(1.5 * math.sin((x + k * 3) * 0.5))
            cv.put(x, y % 16, P["sed_d"])
            cv.put(x, (y - 1) % 16, P["sed_l"])
    return cv


def t_track(P, rng, horizontal):
    cv = t_soil(P, rng, 0)
    d, l = shade(P["soil_d"], 0.85), P["soil_l"]
    for lane in (4, 11):
        for i in range(16):
            if i % 3 == 0:
                continue
            if horizontal:
                cv.put(i, lane, d)
                cv.put(i, lane + 1, d)
                cv.put(i, lane - 1, l)
            else:
                cv.put(lane, i, d)
                cv.put(lane + 1, i, d)
                cv.put(lane - 1, i, l)
    return cv


def t_crater(P, rng):
    cv = t_soil(P, rng, 0)
    cv.ellipse(8, 9, 6.5, 5, P["soil_l"])
    cv.ellipse(8, 9.5, 5.5, 4, shade(P["soil_d"], 0.85))
    cv.ellipse(8.5, 10, 4, 3, P["soil_d"])
    cv.ellipse(9, 10.5, 2.5, 1.8, P["soil"])
    return cv


def t_rock_solid(P, rng, variant):
    cv = t_soil(P, rng, 1)
    rock = Canvas(16, 16)
    rock.ellipse(8, 9, 7 - variant, 6, P["cliff"])
    rock.ellipse(6.5, 7, 4.5 - variant * 0.5, 3.5, P["cliff_l"])
    rock.ellipse(10, 11.5, 4, 2.5, P["cliff_d"])
    rock.put(5, 6, mix(P["cliff_l"], hx("ffffff"), 0.4))
    out = add_outline(rock.img)
    shadow = Canvas(16, 16)
    shadow.ellipse(9, 14, 6, 1.6, alpha(shade(P["soil_d"], 0.6), 160))
    base = cv.img
    base.alpha_composite(shadow.img)
    base.alpha_composite(out)
    c = Canvas(16, 16)
    c.img = base
    c.px = base.load()
    return c


def city_tileset(planet: str, seed: int):
    P = PALETTES[planet]
    rng = random.Random(seed)
    tiles: list[tuple[str, Canvas]] = []

    def add(name, cv):
        tiles.append((name, cv))

    for v in range(4):
        add(f"soil_{v}", t_soil(P, random.Random(seed + v), v))
    for v in range(2):
        add(f"soil_rough_{v}", t_soil_rough(P, random.Random(seed + 10 + v), v))
    for v in range(3):
        add(f"grass_{v}", t_grass(P, random.Random(seed + 20 + v), v))
    for v in range(4):
        add(f"pave_{v}", t_pave(P, random.Random(seed + 30 + v), v))
    for s in "nsew":
        add(f"pave_edge_{s}", t_pave_edge(P, random.Random(seed + 40), s))
    for c in ("ne", "nw", "se", "sw"):
        add(f"pave_corner_{c}", t_pave_edge(P, random.Random(seed + 41), c))
    for v in range(3):
        add(f"road_{v}", t_road(P, random.Random(seed + 50 + v), v))
    add("road_line_h", t_road_line(P, random.Random(seed + 55), True))
    add("road_line_v", t_road_line(P, random.Random(seed + 56), False))
    add("cross_h", t_cross(P, random.Random(seed + 57), True))
    add("cross_v", t_cross(P, random.Random(seed + 58), False))
    add("rail_h", t_rail(P, random.Random(seed + 59)))
    for v in range(2):
        add(f"plaza_{v}", t_plaza(P, random.Random(seed + 60 + v), v))
    add("plaza_center", t_plaza_center(P, random.Random(seed + 62)))
    add("soil_bed", t_soil_bed(P, random.Random(seed + 63)))
    add("grate", t_grate(P, random.Random(seed + 64)))
    add("hatch", t_hatch(P, random.Random(seed + 65)))
    add("pad_0", t_pad(P, random.Random(seed + 66), ""))
    add("pad_mark", t_pad(P, random.Random(seed + 67), "mark"))
    add("pad_line", t_pad(P, random.Random(seed + 68), "line"))
    add("hedge_h", t_hedge(P, random.Random(seed + 70), True, planet))
    add("hedge_v", t_hedge(P, random.Random(seed + 71), False, planet))
    for v in range(3):
        add(f"cliff_{v}", t_cliff(P, random.Random(seed + 80 + v), v, planet))
    add("canal", t_canal(P, random.Random(seed + 90)))
    add("wall_low_h", t_wall_low(P, random.Random(seed + 91)))
    for v in range(2):
        add(f"ice_{v}", t_ice(P, random.Random(seed + 100 + v), v))
    add("ice_edge", t_ice_edge(P, random.Random(seed + 102)))
    for v in range(2):
        add(f"sediment_{v}", t_sediment(P, random.Random(seed + 103 + v), v))
    add("track_h", t_track(P, random.Random(seed + 105), True))
    add("track_v", t_track(P, random.Random(seed + 106), False))
    add("crater_s", t_crater(P, random.Random(seed + 107)))
    for v in range(2):
        add(f"rock_solid_{v}", t_rock_solid(P, random.Random(seed + 108 + v), v))

    cols = 16
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 16, rows * 16), CLEAR)
    index = {}
    for i, (name, cv) in enumerate(tiles):
        # los tiles transparentes en esquinas (bordillo) se apoyan sobre calzada
        img = cv.img
        if name.startswith("pave_corner") or name.startswith("pave_edge"):
            base = t_road(P, random.Random(seed + 52), 0).img
            base.alpha_composite(img)
            img = base
        sheet.paste(img, ((i % cols) * 16, (i // cols) * 16))
        index[name] = i
    G.save(sheet, "tiles", f"city_{planet}.png")
    save_json({"columns": cols, "rows": rows, "tiles": index}, ART, "tiles", f"city_{planet}.json")
    return sheet, index



# ================================================================== 2. EDIFICIOS (vista 3/4)
# Sprite = tejado (d×16 px, arriba) + fachada (wall px, abajo). Ancho w×16. Anclaje abajo-centro.

BUILDINGS: dict = {}


def reg(name: str, img: Image.Image, w: int, d: int, wall: int, planet: str, kind: str, door_dx: int = 0) -> None:
    assert img.size == (w * 16, d * 16 + wall), (name, img.size, (w * 16, d * 16 + wall))
    G.save(img, "props", f"{name}.png")
    BUILDINGS[name] = {"w": w, "d": d, "wall": wall, "planet": planet, "kind": kind, "door_dx": door_dx}


def tex_fill(cv, x0, y0, x1, y1, base, rng, amount=0.08, dark=0.9, light=1.07):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            r = rng.random()
            cv.put(x, y, shade(base, dark) if r < amount else shade(base, light) if r > 1 - amount else base)


# ------------------------------------------------------------ tejados

def roof_flat(cv, x0, y0, x1, y1, mat, rng, extras=(), rim=None):
    """Azotea plana con pretil: luz arriba-izquierda, sombra abajo-derecha, grava y equipos."""
    rim = rim or shade(mat, 1.18)
    tex_fill(cv, x0, y0, x1, y1, mat, rng, 0.12)
    cv.rect(x0, y0, x1, y0 + 1, rim)
    cv.rect(x0, y0, x0 + 1, y1, rim)
    cv.vline(x1, y0, y1, shade(mat, 0.7))
    cv.vline(x1 - 1, y0 + 2, y1, shade(mat, 0.82))
    cv.hline(x0, x1, y1, shade(mat, 0.62))
    # juntas de la tela asfáltica / placas
    for y in range(y0 + 7, y1 - 1, 8):
        for x in range(x0 + 3, x1 - 1):
            blend_put(cv, x, y, shade(mat, 0.7), 0.35)
            blend_put(cv, x, y + 1, shade(mat, 1.3), 0.15)
    for x in range(x0 + 13, x1 - 1, 16):
        for y in range(y0 + 3, y1 - 1):
            blend_put(cv, x, y, shade(mat, 0.75), 0.25)
    cv.hline(x0 + 2, x1 - 2, y0 + 2, shade(mat, 0.82))  # sombra interior del pretil
    cv.vline(x0 + 2, y0 + 2, y1 - 1, shade(mat, 0.88))
    W = x1 - x0
    free = [x0 + 4, x1 - 4]
    for kind in extras:
        if free[1] - free[0] < 6:
            break
        if kind == "ac":
            x = rng.randrange(free[0], max(free[0] + 1, free[1] - 8))
            y = rng.randrange(y0 + 4, max(y0 + 5, y1 - 8))
            ac_box(cv, x, y)
        elif kind == "tank":
            x = free[1] - 9
            water_tank(cv, x, y0 + 3, rng)
            free[1] -= 12
        elif kind == "solar":
            x = free[0]
            ny = max(1, (y1 - y0 - 6) // 6)
            for k in range(min(2, ny)):
                solar_panel(cv, x, y0 + 4 + k * 7, min(14, W // 2 - 4))
            free[0] += min(14, W // 2 - 4) + 3
        elif kind == "antenna":
            x = rng.randrange(x0 + 4, x1 - 4)
            antenna(cv, x, y0 + 1)
        elif kind == "dish":
            dish(cv, free[1] - 8, y0 + 4)
            free[1] -= 11
        elif kind == "skylight":
            x = rng.randrange(free[0], max(free[0] + 1, free[1] - 10))
            cv.rect(x, y1 - 9, x + 9, y1 - 5, shade(mat, 0.6))
            cv.rect(x + 1, y1 - 8, x + 8, y1 - 6, hx("6ad8e8"))
            cv.hline(x + 1, x + 4, y1 - 8, hx("d8fbff"))
        elif kind == "vents":
            for k in range(3):
                x = rng.randrange(x0 + 4, x1 - 4)
                y = rng.randrange(y0 + 4, y1 - 3)
                cv.rect(x, y, x + 1, y + 1, shade(mat, 0.55))
                cv.put(x, y, shade(mat, 1.3))
        elif kind == "garden":
            x = rng.randrange(free[0], max(free[0] + 1, free[1] - 12))
            y = y1 - 7
            cv.rect(x, y, x + 11, y + 4, hx("5a3e2c"))
            cv.hline(x, x + 11, y, hx("7a5a3e"))
            for k in range(0, 11, 2):
                cv.put(x + k, y - 1, hx("8a8a3a"))
                cv.put(x + k + 1, y - 2, hx("6a7a3a"))
        elif kind == "stairs":
            x = rng.randrange(free[0], max(free[0] + 1, free[1] - 12))
            y = y0 + 3
            cv.rect(x, y, x + 11, y + 6, shade(mat, 1.12))
            cv.hline(x, x + 11, y, shade(mat, 1.35))
            cv.rect(x, y + 7, x + 11, y + 12, shade(mat, 0.78))
            cv.rect(x + 4, y + 8, x + 7, y + 12, hx("3a3040"))
            cv.put(x + 6, y + 10, GOLD)
            cv.hline(x, x + 11, y + 13, hx("1e1a24"))
            free[0] = max(free[0], x + 14) if x - free[0] < 6 else free[0]
        elif kind == "puddles":
            for _ in range(3):
                px, py = rng.randrange(x0 + 5, x1 - 10), rng.randrange(y0 + 5, y1 - 4)
                for yy in range(py, py + 3):
                    for xx in range(px + (yy == py), px + rng.randrange(5, 9) - (yy == py + 2)):
                        blend_put(cv, xx, yy, hx("4a6a8a"), 0.55)
                cv.put(px + 2, py + 1, mix(CYAN, hx("ffffff"), 0.5))
        elif kind == "pipes":
            yy = rng.randrange(y0 + 5, y1 - 4)
            cv.hline(x0 + 3, x1 - 3, yy, hx("8a8a92"))
            cv.hline(x0 + 3, x1 - 3, yy + 1, hx("5a5a62"))
            for x in range(x0 + 6, x1 - 3, 12):
                cv.rect(x, yy - 1, x + 1, yy + 2, hx("4a4a52"))
        elif kind == "cables":
            yy = rng.randrange(y0 + 5, y1 - 3)
            for x in range(x0 + 3, x1 - 3):
                if (x * 7 + yy) % 13 != 0:
                    cv.put(x, yy + int(1.5 * math.sin(x * 0.3)), hx("1e1a24"))


def ac_box(cv, x, y):
    cv.rect(x, y, x + 6, y + 4, hx("9aa0aa"))
    cv.hline(x, x + 6, y, hx("c8ccd4"))
    cv.vline(x + 6, y, y + 4, hx("6a707a"))
    cv.hline(x, x + 6, y + 5, hx("2a2830"))
    cv.disc(x + 3, y + 2.5, 1.6, hx("4a505a"))
    cv.put(x + 3, y + 2, hx("8a909a"))


def water_tank(cv, x, y, rng):
    cv.rect(x + 1, y + 7, x + 7, y + 11, hx("2a2830"))
    cv.vline(x + 1, y + 7, y + 11, hx("4a4650"))
    cv.vline(x + 7, y + 7, y + 11, hx("4a4650"))
    cv.ellipse(x + 4, y + 4, 4, 2.5, hx("7a8a9a"))
    cv.rect(x, y + 4, x + 8, y + 8, hx("6a7a8a"))
    cv.vline(x, y + 4, y + 8, hx("8a9aaa"))
    cv.vline(x + 8, y + 4, y + 8, hx("4a5a6a"))
    cv.ellipse(x + 4, y + 3.5, 3.5, 2, hx("9aaaba"))
    cv.hline(x, x + 8, y + 6, hx("5a6a7a"))


def solar_panel(cv, x, y, w):
    cv.rect(x, y, x + w, y + 5, hx("2a3a6a"))
    for xx in range(x, x + w + 1, 3):
        cv.vline(xx, y, y + 5, hx("4a5a8a"))
    cv.hline(x, x + w, y + 2, hx("4a5a8a"))
    cv.hline(x, x + w, y, hx("8aa8e0"))
    cv.hline(x, x + w, y + 6, hx("1e1a24"))


def antenna(cv, x, y):
    cv.vline(x, y, y + 9, hx("4a4650"))
    cv.hline(x - 2, x + 2, y + 3, hx("4a4650"))
    cv.hline(x - 1, x + 1, y + 6, hx("4a4650"))
    cv.put(x, y, hx("ff4a4a"))


def dish(cv, x, y):
    cv.ellipse(x + 3, y + 3, 4, 3.5, hx("d8dce4"))
    cv.ellipse(x + 4, y + 4, 2.5, 2, hx("a8aeb8"))
    cv.vline(x + 4, y + 6, y + 9, hx("4a4650"))
    cv.put(x + 3, y + 2, hx("ffffff"))


def roof_gable(cv, x0, y0, x1, y1, color, rng):
    """Tejado a dos aguas visto en 3/4: faldón trasero estrecho, cumbrera y faldón delantero de tejas."""
    ridge = y0 + (y1 - y0) * 2 // 5
    light, dark = shade(color, 1.18), shade(color, 0.72)
    for y in range(y0, y1 + 1):
        back = y < ridge
        base = shade(color, 1.1) if back else color
        row = (y - (ridge if not back else y0)) // 3
        for x in range(x0, x1 + 1):
            c = base
            if not back:
                off = 0 if row % 2 == 0 else 2
                if (y - ridge) % 3 == 2:
                    c = shade(color, 0.8)
                elif (x + off) % 4 == 0:
                    c = shade(color, 0.86)
                elif (y - ridge) % 3 == 0:
                    c = shade(color, 1.06)
            else:
                if (y - y0) % 2 == 1:
                    c = shade(base, 0.92)
            cv.put(x, y, c)
    cv.hline(x0, x1, ridge, light)
    cv.hline(x0, x1, ridge + 1, shade(color, 0.9))
    cv.hline(x0, x1, ridge - 1, shade(color, 1.25))
    cv.hline(x0, x1, y1, dark)
    cv.hline(x0, x1, y1 - 1, shade(color, 0.82))
    cv.vline(x0, y0, y1, shade(color, 1.0))
    cv.vline(x1, y0, y1, dark)
    for _ in range(4):  # tejas sueltas / musgo seco
        x, y = rng.randrange(x0 + 2, x1 - 2), rng.randrange(ridge + 2, y1 - 2)
        cv.put(x, y, shade(color, 0.65))


# ------------------------------------------------------------ fachadas

def facade(cv, x0, y0, x1, y1, mat, rng, panels=False, bricks=False, layered=False):
    tex_fill(cv, x0, y0, x1, y1, mat, rng, 0.07)
    if bricks:
        for y in range(y0, y1 + 1):
            if (y - y0) % 4 == 3:
                cv.hline(x0, x1, y, shade(mat, 0.86))
            else:
                off = 0 if ((y - y0) // 4) % 2 == 0 else 4
                for x in range(x0 + off, x1 + 1, 8):
                    cv.put(x, y, shade(mat, 0.86))
    if layered:
        for y in range(y0, y1 + 1):
            if (y - y0) % 3 == 0:
                cv.hline(x0, x1, y, shade(mat, 0.92))
            elif (y - y0) % 3 == 1:
                cv.hline(x0, x1, y, shade(mat, 1.04))
    if panels:
        for x in range(x0, x1 + 1, 12):
            cv.vline(x, y0, y1, shade(mat, 0.86))
    # sombra bajo el alero y en el lado derecho, suciedad abajo
    cv.hline(x0, x1, y0, shade(mat, 0.55))
    cv.hline(x0, x1, y0 + 1, shade(mat, 0.75))
    cv.vline(x1, y0, y1, shade(mat, 0.72))
    cv.vline(x0, y0, y1, shade(mat, 1.08))
    for y in range(y1 - 2, y1 + 1):
        for x in range(x0, x1 + 1):
            blend_put(cv, x, y, hx("1e1a24"), 0.18 + 0.1 * (y - y1 + 2))


def window(cv, x, y, w, h, lit, rng, frame=hx("2a2632"), tint=WARM, curtain=True, sill=True):
    cv.rect(x - 1, y - 1, x + w, y + h, frame)
    if lit:
        for yy in range(y, y + h):
            t = (yy - y) / max(1, h - 1)
            cv.hline(x, x + w - 1, yy, mix(shade(tint, 1.05), shade(tint, 0.78), t))
        if curtain and w >= 4:
            side = rng.random() < 0.5
            cx = x if side else x + w - 2
            cv.rect(cx, y, cx + 1, y + h - 1, shade(tint, 0.6) if rng.random() < 0.5 else mix(tint, PINK, 0.4))
        if rng.random() < 0.35 and w >= 4 and h >= 4:  # maceta o silueta
            px = x + w // 2
            cv.rect(px - 1, y + h - 2, px, y + h - 1, hx("3a2a30"))
            cv.put(px - 1, y + h - 3, hx("4a8a3a"))
            cv.put(px, y + h - 4, hx("5aa04a"))
        cv.put(x, y, hx("ffffff"))
    else:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                cv.put(xx, yy, hx("1c2436") if (xx - x + yy - y) % 5 else hx("2e3a52"))
        cv.put(x + w - 1, y, hx("4a5a78"))
    if w >= 5:
        cv.vline(x + w // 2, y, y + h - 1, frame)
    if sill:
        cv.hline(x - 1, x + w, y + h + 1, hx("b8b4ac"))
        cv.hline(x - 1, x + w, y + h + 2, hx("4a4650"))


def round_window(cv, cx, cy, r, lit, tint=CYAN):
    cv.disc(cx, cy, r + 1, hx("5a6070"))
    cv.disc(cx, cy, r, mix(tint, hx("ffffff"), 0.15) if lit else hx("1c2436"))
    if lit:
        cv.disc(cx + 0.5, cy + 0.5, r - 1, shade(tint, 0.8))
    cv.put(int(cx - r / 2), int(cy - r / 2), hx("ffffff"))


def arch_window(cv, x, y, w, h, lit, rng, frame, tint=WARM):
    window(cv, x, y + 2, w, h - 2, lit, rng, frame, tint, curtain=lit, sill=False)
    cv.hline(x, x + w - 1, y + 1, frame)
    cv.hline(x + 1, x + w - 2, y, frame)
    cv.hline(x + 1, x + w - 2, y + 1, shade(tint, 0.95) if lit else hx("1c2436"))


def door(cv, cx, bottom, color, frame=hx("2a2632"), w=8, h=13, glass=True, step=hx("8a8680"), lamp=GOLD):
    x0 = cx - w // 2
    cv.rect(x0 - 2, bottom - h - 2, x0 + w + 1, bottom, frame)
    cv.rect(x0, bottom - h, x0 + w - 1, bottom, color)
    cv.vline(x0, bottom - h, bottom, shade(color, 1.2))
    cv.vline(x0 + w - 1, bottom - h, bottom, shade(color, 0.7))
    if glass:
        cv.rect(x0 + 2, bottom - h + 2, x0 + w - 3, bottom - h + 5, mix(WARM, color, 0.3))
        cv.put(x0 + 2, bottom - h + 2, hx("ffffff"))
    cv.put(x0 + w - 3, bottom - h // 2, GOLD)
    cv.hline(x0 - 3, x0 + w + 2, bottom, step)
    if lamp:
        cv.rect(x0 + w + 2, bottom - h - 1, x0 + w + 3, bottom - h + 1, hx("2a2632"))
        cv.put(x0 + w + 3, bottom - h, lamp)


def awning(cv, x0, x1, y, c1, c2, depth=4):
    for yy in range(y, y + depth):
        for x in range(x0, x1 + 1):
            c = c1 if ((x - x0) // 3) % 2 == 0 else c2
            cv.put(x, yy, shade(c, 1.1 - 0.06 * (yy - y)))
    for x in range(x0, x1 + 1, 3):
        cv.put(x, y + depth, c1 if ((x - x0) // 3) % 2 == 0 else c2)
    cv.hline(x0, x1, y - 1, shade(c1, 0.6))
    for x in range(x0, x1 + 1):
        blend_put(cv, x, y + depth + 1, hx("1e1a24"), 0.35)


def balcony(cv, x0, x1, y, metal=hx("3a3640"), plants=True, rng=None):
    cv.rect(x0, y + 4, x1, y + 5, hx("8a8680"))
    cv.hline(x0, x1, y + 6, hx("4a4650"))
    cv.hline(x0, x1, y, metal)
    for x in range(x0, x1 + 1, 2):
        cv.vline(x, y, y + 3, metal)
    if plants and rng is not None and rng.random() < 0.6:
        x = rng.randrange(x0 + 1, max(x0 + 2, x1 - 2))
        cv.rect(x, y + 1, x + 2, y + 3, hx("8a4a32"))
        cv.put(x, y, hx("6a9a3a"))
        cv.put(x + 1, y - 1, hx("8aba4a"))
        cv.put(x + 2, y, hx("5a8a3a"))


def drain_pipe(cv, x, y0, y1, color=hx("6a6670")):
    cv.vline(x, y0, y1, color)
    cv.vline(x + 1, y0, y1, shade(color, 0.7))
    for y in range(y0 + 4, y1, 10):
        cv.hline(x - 1, x + 2, y, shade(color, 0.6))


def wall_ac(cv, x, y):
    cv.rect(x, y, x + 5, y + 3, hx("b8bcc4"))
    cv.hline(x, x + 5, y, hx("dfe2e8"))
    cv.rect(x + 1, y + 1, x + 4, y + 2, hx("6a707a"))
    cv.hline(x, x + 5, y + 4, hx("2a2830"))
    cv.put(x + 5, y + 5, hx("5a8aa0"))  # goteo


def graffiti(cv, x, y, rng):
    cols = [PINK, CYAN, GOLD, GREEN]
    c = rng.choice(cols)
    for k in range(rng.randrange(5, 9)):
        cv.put(x + k, y + int(1.5 * math.sin(k * 1.3 + rng.random())), c)
    cv.put(x + 2, y - 2, rng.choice(cols))
    cv.put(x + 5, y + 2, rng.choice(cols))


def neon_strip(cv, x0, x1, y, color):
    cv.hline(x0, x1, y, color)
    for x in range(x0, x1 + 1):
        blend_put(cv, x, y - 1, color, 0.3)
        blend_put(cv, x, y + 1, color, 0.3)


def shopfront(cv, x0, x1, y0, bottom, color, rng, goods="plants"):
    """Escaparate: cristal ancho iluminado con productos y marco."""
    cv.rect(x0 - 1, y0 - 1, x1 + 1, bottom, hx("2a2632"))
    for yy in range(y0, bottom - 2):
        cv.hline(x0, x1, yy, mix(WARM, color, 0.25 + 0.3 * (yy - y0) / max(1, bottom - y0)))
    cv.hline(x0, x1, bottom - 2, hx("4a4650"))
    cv.hline(x0, x1, bottom - 1, hx("8a8680"))
    for x in range(x0 + 1, x1, 3):
        if goods == "plants":
            h = rng.randrange(2, 5)
            cv.rect(x, bottom - 4, x + 1, bottom - 3, hx("8a4a32"))
            cv.vline(x, bottom - 4 - h, bottom - 5, hx("5aa04a"))
            cv.put(x + 1, bottom - 5 - h // 2, hx("8ad04a"))
        elif goods == "tech":
            cv.rect(x, bottom - 6, x + 1, bottom - 3, rng.choice([CYAN, PINK, hx("8a90a0")]))
        elif goods == "food":
            cv.rect(x, bottom - 4, x + 1, bottom - 3, rng.choice([hx("e86a3a"), GOLD, hx("8ad04a")]))
    cv.hline(x0, x1 - 3, y0, hx("ffffff"))
    cv.put(x0, y0 + 1, hx("ffffff"))


# ------------------------------------------------------------ Tierra

def earth_apartment(w, d, wall, palette, seed, floors=None, sign=None, shop=None):
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    mat, roof, accent = palette
    R = d * 16
    roof_flat(cv, 1, 1, W - 2, R + 1, roof, rng,
              extras=["stairs"] + rng.sample(["ac", "tank", "solar", "antenna", "vents", "garden", "dish", "pipes"], 4)
              + ["ac", "puddles"])
    facade(cv, 1, R + 2, W - 2, H - 1, mat, rng, panels=rng.random() < 0.5, bricks=rng.random() < 0.3)
    # cornisa
    cv.hline(1, W - 2, R + 2, shade(mat, 1.25))
    cv.hline(1, W - 2, R + 3, shade(mat, 0.6))
    floor_h = 16
    n = floors or max(1, (wall - 18) // floor_h)
    ground_top = H - 18
    cols = max(2, (W - 8) // 12)
    step = (W - 10) / cols
    for f in range(n):
        y = ground_top - (f + 1) * floor_h + 4
        if y < R + 5:
            break
        cv.hline(2, W - 3, y + floor_h - 3, shade(mat, 0.82))  # forjado
        for c in range(cols):
            x = int(6 + c * step)
            window(cv, x, y, 6, 7, rng.random() < 0.55, rng,
                   tint=rng.choice([WARM, WARM, hx("ffe6b0"), mix(CYAN, WARM, 0.5), mix(PINK, WARM, 0.5)]))
            if rng.random() < 0.18:
                wall_ac(cv, x + 7, y + 2)
        if f % 2 == 1 and rng.random() < 0.7:
            bx = int(5 + rng.randrange(cols) * step)
            balcony(cv, bx - 2, bx + 10, y + 5, rng=rng)
    # planta baja
    cv.hline(1, W - 2, ground_top - 1, shade(mat, 1.2))
    tex_fill(cv, 1, ground_top, W - 2, H - 2, shade(mat, 0.86), rng, 0.06)
    cv.vline(W - 2, ground_top, H - 1, shade(mat, 0.64))
    if shop:
        color, goods = shop
        shopfront(cv, 4, W // 2 - 8, ground_top + 4, H - 2, color, rng, goods)
        shopfront(cv, W // 2 + 7, W - 6, ground_top + 4, H - 2, color, rng, goods)
        awning(cv, 3, W - 4, ground_top + 1, color, hx("e8e4dc"))
        door(cv, W // 2, H - 2, shade(color, 0.6), lamp=None)
    else:
        door(cv, W // 2, H - 2, accent)
        for x in (5, W - 13):
            if abs(x + 4 - W // 2) > 10:
                window(cv, x, ground_top + 5, 7, 6, rng.random() < 0.6, rng, sill=False)
        cv.rect(W // 2 - 9, H - 7, W // 2 - 7, H - 3, hx("6a6670"))  # buzones
        cv.put(W // 2 - 8, H - 6, GOLD)
    drain_pipe(cv, W - 6 if rng.random() < 0.5 else 3, R + 4, H - 3)
    if rng.random() < 0.6:
        graffiti(cv, rng.randrange(4, W - 14), H - 6, rng)
    for k in range(2):  # cables de fachada
        y = R + 6 + k * 9
        if rng.random() < 0.6:
            for x in range(1, W - 1):
                cv.put(x, y + int(2 * math.sin(math.pi * x / W)), hx("1e1a24"))
    if sign:
        text, color = sign
        neon_sign(cv, text, W // 2, ground_top - 9, color)
    return add_outline(cv.img)


def earth_house(w, d, wall, roof_color, wall_color, seed, porch=True, warm=True, extras=()):
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    R = d * 16
    roof_gable(cv, 1, 1, W - 2, R + 3, roof_color, rng)
    # chimenea / placa solar sobre el tejado
    if "chimney" in extras:
        cx = W - 14
        cv.rect(cx, 2, cx + 4, 9, hx("8a5a4a"))
        cv.hline(cx, cx + 4, 2, hx("aa7a6a"))
        cv.rect(cx - 1, 1, cx + 5, 2, hx("5a3a32"))
    if "solar" in extras:
        solar_panel(cv, 5, R - 9, 12)
    facade(cv, 1, R + 4, W - 2, H - 1, wall_color, rng, bricks="bricks" in extras)
    for x in range(1, W - 1):  # alero
        cv.put(x, R + 4, shade(roof_color, 0.5))
    door(cv, W // 2, H - 2, hx("6a3a2a") if warm else hx("3a4a5a"))
    wy = R + 9
    for x in (5, W - 12):
        window(cv, x, wy, 7, 7, warm or rng.random() < 0.5, rng)
        # contraventanas
        cv.rect(x - 3, wy - 1, x - 2, wy + 7, shade(roof_color, 0.75))
        cv.rect(x + 8, wy - 1, x + 9, wy + 7, shade(roof_color, 0.75))
    if porch:
        cv.hline(1, W - 2, H - 1, hx("6a5a4a"))
        for x in (W // 2 - 9, W // 2 + 8):
            cv.vline(x, H - 15, H - 2, hx("d8d0c0"))
            cv.vline(x + 1, H - 15, H - 2, hx("a8a090"))
        cv.hline(W // 2 - 10, W // 2 + 10, H - 16, shade(roof_color, 0.8))
        cv.hline(W // 2 - 10, W // 2 + 10, H - 15, shade(roof_color, 0.55))
    # macetas en la entrada
    for x in (W // 2 - 13, W // 2 + 11):
        cv.rect(x, H - 5, x + 2, H - 2, hx("9a5a3a"))
        cv.put(x + 1, H - 6, hx("6a9a3a") if warm else hx("8a7a4a"))
        cv.put(x, H - 7, hx("8aba4a") if warm else hx("6a5a3a"))
    return add_outline(cv.img)


def earth_ruin(w, d, wall, seed):
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    R = d * 16
    mat = hx("6e6862")
    roof_flat(cv, 1, 1, W - 2, R + 1, hx("4e4a46"), rng, extras=["vents", "puddles", "cables"])
    # agujeros en el tejado
    for _ in range(2):
        x, y = rng.randrange(4, W - 12), rng.randrange(4, R - 6)
        cv.rect(x, y, x + rng.randrange(4, 9), y + rng.randrange(3, 5), hx("1a1620"))
        cv.vline(x + 2, y, y + 3, hx("7a4a32"))
    facade(cv, 1, R + 2, W - 2, H - 1, mat, rng, panels=True)
    for _ in range(5):  # grietas
        x, y = rng.randrange(2, W - 6), rng.randrange(R + 4, H - 8)
        for k in range(rng.randrange(4, 9)):
            cv.put(x + (k % 3 == 0), y + k, shade(mat, 0.55))
    cols = max(2, (W - 8) // 12)
    step = (W - 10) / cols
    floors = max(1, (wall - 18) // 16)
    for f in range(floors):
        y = H - 18 - (f + 1) * 16 + 4
        if y < R + 5:
            break
        for c in range(cols):
            x = int(6 + c * step)
            cv.rect(x - 1, y - 1, x + 6, y + 7, hx("2a2632"))
            cv.rect(x, y, x + 5, y + 6, hx("14101a"))
            if rng.random() < 0.6:  # tablones
                for k in range(2):
                    yy = y + 1 + k * 3
                    cv.hline(x - 1, x + 6, yy, hx("8a6a4a"))
                    cv.hline(x - 1, x + 6, yy + 1, hx("6a4a32"))
            else:
                cv.put(x + 1, y + 2, hx("4a5a78"))
    # entrada tapiada
    cv.rect(W // 2 - 6, H - 14, W // 2 + 5, H - 2, hx("4a4440"))
    for x in range(W // 2 - 6, W // 2 + 6, 3):
        cv.vline(x, H - 14, H - 2, hx("5a544e"))
    cv.hline(W // 2 - 7, W // 2 + 6, H - 10, hx("8a6a4a"))
    cv.hline(W // 2 - 7, W // 2 + 6, H - 6, hx("8a6a4a"))
    for _ in range(3):
        graffiti(cv, rng.randrange(3, W - 12), rng.randrange(H - 14, H - 3), rng)
    # enredadera seca
    x = rng.choice((3, W - 6))
    for y in range(R + 3, H - 4):
        if rng.random() < 0.7:
            cv.put(x + int(1.5 * math.sin(y * 0.4)), y, hx("6a6a3a"))
    return add_outline(cv.img)


def earth_tower(w, d, wall, seed):
    """Torre de AgroNet: muro cortina de cristal, logotipo verde, azotea con antenas."""
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    R = d * 16
    roof_flat(cv, 1, 1, W - 2, R + 1, hx("4a5258"), rng, extras=["dish", "antenna", "ac", "ac", "vents"])
    # helipuerto (aeropuerto de drones)
    cv.disc(W // 2 - 8, R // 2 + 2, 8, hx("3a4248"))
    cv.disc(W // 2 - 8, R // 2 + 2, 7, hx("5a646a"))
    draw_text(cv, "D", W // 2 - 9, R // 2, GREEN)
    facade(cv, 1, R + 2, W - 2, H - 1, hx("2e3a44"), rng)
    for y in range(R + 6, H - 22, 6):
        for x in range(4, W - 4, 5):
            lit = rng.random() < 0.45
            c = mix(GREEN, CYAN, rng.random() * 0.5) if lit else hx("1c2a36")
            cv.rect(x, y, x + 3, y + 3, shade(c, 0.85) if lit else c)
            if lit:
                cv.put(x, y, mix(c, hx("ffffff"), 0.5))
        cv.hline(2, W - 3, y + 5, hx("5a6a74"))
    for x in range(4, W - 4, 5):
        cv.vline(x - 1, R + 4, H - 22, hx("4a5a64"))
    # reflejo diagonal del cristal
    for k in range(0, wall - 30, 1):
        x = 6 + k // 2
        if x < W - 8:
            blend_put(cv, x, R + 6 + k, hx("ffffff"), 0.15)
    neon_sign(cv, "AGRONET", W // 2, R + 12, GREEN)
    # vestíbulo
    gt = H - 20
    cv.rect(2, gt, W - 3, H - 2, hx("3a464e"))
    shopfront(cv, 6, W - 7, gt + 4, H - 2, GREEN, rng, "food")
    door(cv, W // 2, H - 2, hx("2a4a3a"), lamp=GREEN)
    cv.hline(2, W - 3, gt, GREEN)
    return add_outline(cv.img)


def earth_kiosk(seed):
    rng = random.Random(seed)
    W, H = 32, 16 + 24
    cv = Canvas(W, H)
    roof_flat(cv, 1, 1, W - 2, 15, hx("5a6a74"), rng, extras=["antenna"])
    facade(cv, 1, 16, W - 2, H - 1, hx("3a5a6a"), rng)
    awning(cv, 1, W - 2, 17, CYAN, hx("1e3a44"), 3)
    cv.rect(4, 23, W - 5, 31, hx("1e2a34"))
    cv.rect(5, 24, W - 6, 30, mix(CYAN, hx("1e2a34"), 0.5))
    draw_text(cv, "INFO", 8, 25, hx("ffffff"))
    cv.rect(3, 33, W - 4, H - 2, hx("6a7a84"))
    cv.hline(3, W - 4, 33, hx("a8b8c0"))
    return add_outline(cv.img)


def earth_vault(seed):
    """Bóveda Semillera: búnker de hormigón con puerta acorazada redonda y letrero."""
    rng = random.Random(seed)
    w, d, wall = 10, 3, 48
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    R = d * 16
    roof_flat(cv, 1, 1, W - 2, R + 1, hx("6a6e74"), rng,
              extras=["stairs", "solar", "dish", "ac", "garden", "pipes", "vents", "ac", "puddles", "antenna"])
    facade(cv, 1, R + 2, W - 2, H - 1, hx("7e8288"), rng, bricks=True)
    # contrafuertes
    for x in (12, W - 20, 40, W - 48):
        cv.rect(x, R + 4, x + 7, H - 1, hx("8e9298"))
        cv.vline(x, R + 4, H - 1, hx("a8acb2"))
        cv.vline(x + 7, R + 4, H - 1, hx("5e6268"))
    # puerta acorazada
    cx, cy = W // 2, H - 17
    cv.rect(cx - 18, cy - 16, cx + 17, H - 1, hx("4a4e56"))
    cv.disc(cx, cy, 15, hx("2e3238"))
    cv.disc(cx, cy, 13, hx("9aa0aa"))
    cv.disc(cx, cy, 11, hx("7a8088"))
    cv.disc(cx - 1, cy - 1, 9, hx("b0b6c0"))
    cv.disc(cx, cy, 4, GOLD)
    cv.disc(cx, cy, 2, shade(GOLD, 0.7))
    for a in range(8):
        ang = a * math.pi / 4
        cv.put(int(cx + 12 * math.cos(ang)), int(cy + 12 * math.sin(ang)), hx("4a4e56"))
        cv.rect(int(cx + 7 * math.cos(ang)), int(cy + 7 * math.sin(ang)),
                int(cx + 7 * math.cos(ang)) + 1, int(cy + 7 * math.sin(ang)) + 1, hx("5a6068"))
    # brote pintado
    cv.vline(cx, cy - 4, cy - 1, GREEN)
    cv.put(cx - 1, cy - 3, GREEN)
    cv.put(cx + 1, cy - 4, GREEN)
    neon_sign(cv, "BÓVEDA SEMILLERA", cx, R + 8, GOLD)
    # ventanucos de búnker
    for x in (24, 54, W - 61, W - 31):
        cv.rect(x, R + 20, x + 7, R + 22, hx("1a1620"))
        cv.hline(x, x + 7, R + 20, mix(WARM, hx("1a1620"), 0.4))
    for x in (8, W - 10):
        drain_pipe(cv, x, R + 4, H - 3)
    return add_outline(cv.img)


def greenhouse(w, d, wall, alive, seed, frame=hx("c8ccd4"), base=hx("6a6e74")):
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    R = d * 16
    # bóveda de cristal en arco (tejado) + muro bajo
    for y in range(1, H - 6):
        for x in range(1, W - 1):
            u = (x - W / 2) / (W / 2 - 1)
            top = 1 + (R + 4) * (1 - math.sqrt(max(0.0, 1 - u * u))) * 0.9
            if y >= top:
                t = (y - top) / max(1, H - top)
                glass = mix(hx("8ac8d0"), hx("4a7a88"), t)
                cv.put(x, y, alpha(glass, 230))
    # plantas dentro
    for x in range(4, W - 4, 3):
        h = rng.randrange(6, 14) if alive else rng.randrange(3, 7)
        g1 = hx("4aa04a") if alive else hx("8a7a3a")
        g2 = hx("8ad05a") if alive else hx("a08a4a")
        for k in range(h):
            cv.put(x + int(math.sin(k * 0.8) * (1 if alive else 0.4)), H - 8 - k, g1 if k % 2 else g2)
        if alive and rng.random() < 0.4:
            cv.put(x + 1, H - 8 - h, rng.choice([hx("ff6a5a"), GOLD, PINK]))
    # costillas del armazón
    for x in range(1, W - 1, 8):
        for y in range(1, H - 6):
            u = (x - W / 2) / (W / 2 - 1)
            top = 1 + (R + 4) * (1 - math.sqrt(max(0.0, 1 - u * u))) * 0.9
            if y >= top:
                cv.put(x, y, frame)
    for k, y in enumerate(range(R // 2, H - 6, 9)):
        for x in range(1, W - 1):
            if cv.get(x, y)[3]:
                cv.put(x, y, shade(frame, 0.9))
    # brillo
    for k in range(10):
        blend_put(cv, 6 + k, 8 + k * 2, hx("ffffff"), 0.5)
    cv.rect(1, H - 6, W - 2, H - 1, base)
    cv.hline(1, W - 2, H - 6, shade(base, 1.3))
    door(cv, W // 2, H - 2, hx("4a6a5a"), w=8, h=12, lamp=None)
    return add_outline(cv.img)


# ------------------------------------------------------------ Luna

def moon_module(w, d, wall, seed, sign=None, accent=hx("f08a2c"), kind="hab", lit=0.7):
    """Módulo presurizado: tejado de cilindro (bandas de luz), ojos de buey, esclusa."""
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    R = d * 16
    body, dark = hx("dfe3ea"), hx("9aa0ac")
    tint = rng.choice([hx("e6eaf0"), hx("d8dee8"), hx("e2e0dc"), hx("d4dce4")])
    for y in range(1, R + 3):
        t = (y - 1) / (R + 2)
        c = mix(tint, hx("8a92a0"), 0.25 + 0.55 * t * t)
        for x in range(2, W - 2):
            cv.put(x, y, c)
    for x in range(2, W - 2, 12):  # costillas
        cv.vline(x, 2, R + 2, shade(mix(body, dark, 0.5), 1.0))
        cv.vline(x + 1, 2, R + 2, hx("ffffff"))
    for y in range(6, R, 7):  # remaches
        for x in range(6, W - 4, 12):
            cv.put(x, y, hx("8a909c"))
    # escotilla y conductos en el techo
    hx0 = W - 22 if kind != "lab" else 22
    cv.rect(hx0, R // 2, hx0 + 8, R // 2 + 6, hx("9aa0ac"))
    cv.rect(hx0 + 1, R // 2 + 1, hx0 + 7, R // 2 + 5, hx("c8ccd4"))
    cv.put(hx0 + 6, R // 2 + 4, hx("4aff7a"))
    cv.hline(4, W - 5, R - 3, hx("8a8f9a"))
    cv.hline(4, W - 5, R - 2, hx("6a707c"))
    cv.hline(3, W - 4, 2, hx("ffffff"))
    cv.put(2, 1, CLEAR)
    cv.put(W - 3, 1, CLEAR)
    if kind == "lab":
        dish(cv, W - 14, 4)
        antenna(cv, 10, 2)
        antenna(cv, 16, 3)
    else:
        solar_panel(cv, 6, R // 2 - 2, min(16, W // 3))
        if rng.random() < 0.6:
            antenna(cv, W - 8, 2)
    # radiadores (aletas blancas que tiran el calor al espacio) y tanque
    rx0 = rng.randrange(W // 2 - 6, W // 2 + 2)
    for k in range(4):
        cv.rect(rx0 + k * 3, 4, rx0 + k * 3 + 1, 11, hx("f8f8fa"))
        cv.vline(rx0 + k * 3 + 1, 4, 11, hx("b8bec8"))
    cv.hline(rx0 - 1, rx0 + 11, 12, hx("6a707c"))
    if W >= 64:
        water_tank(cv, 4, 3, rng)
    # sombra del borde delantero (cilindro)
    for x in range(2, W - 2):
        blend_put(cv, x, R + 1, hx("4a505c"), 0.5)
        blend_put(cv, x, R + 2, hx("4a505c"), 0.35)
    # banda de color
    for y in range(R + 3, H - 1):
        t = (y - R - 3) / max(1, wall - 4)
        c = mix(body, dark, 0.15 + 0.45 * t)
        for x in range(1, W - 1):
            cv.put(x, y, c)
    cv.hline(1, W - 2, R + 3, hx("5a6070"))
    cv.hline(1, W - 2, R + 6, accent)
    cv.hline(1, W - 2, R + 7, shade(accent, 0.7))
    for x in range(1, W - 1, 8):
        cv.put(x, R + 10, hx("8a909c"))
    cv.vline(1, R + 3, H - 1, hx("eef0f4"))
    cv.vline(W - 2, R + 3, H - 1, hx("7a808c"))
    cy = R + 4 + (wall - 4) // 2 - 2 if not sign else H - 10
    for x in range(8, W - 6, 11):
        if abs(x - W // 2) < 9:
            continue
        round_window(cv, x, cy, 3, rng.random() < lit, rng.choice([CYAN, WARM, hx("bfe8ff")]))
    # esclusa
    cx = W // 2
    cv.rect(cx - 7, H - 16, cx + 6, H - 1, hx("5a6070"))
    cv.rect(cx - 6, H - 15, cx + 5, H - 1, hx("8a929e"))
    cv.rect(cx - 4, H - 13, cx + 3, H - 1, hx("3a404c"))
    cv.vline(cx, H - 13, H - 1, hx("5a6070"))
    cv.rect(cx - 3, H - 11, cx - 1, H - 9, mix(CYAN, hx("3a404c"), 0.3))
    cv.put(cx + 4, H - 9, hx("4aff7a"))
    for x in range(cx - 7, cx + 7):
        cv.put(x, H - 17, accent if (x // 2) % 2 == 0 else hx("2a2830"))
    if sign:
        text, color = sign
        neon_sign(cv, text, cx, R + 12 if wall >= 40 else R + 10, color)
    return add_outline(cv.img)


def dome(w, d, wall, seed, planet="moon", alive=True):
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    cx, base_y = W / 2, H - 7
    rx, ry = W / 2 - 1.5, H - 9
    plants = hx("4aa04a"), hx("8ad05a"), hx("2a7a3a")
    for y in range(0, H):
        for x in range(W):
            u, v = (x + 0.5 - cx) / rx, (base_y - y) / ry
            if v >= 0 and u * u + v * v <= 1.0:
                t = y / H
                glass = mix(hx("bfe8ff") if planet == "moon" else hx("f0c8a0"), hx("3a5a70"), t * 0.8)
                cv.put(x, y, alpha(glass, 210))
    # vegetación interior
    for x in range(int(cx - rx + 4), int(cx + rx - 4), 2):
        u = (x - cx) / rx
        top = base_y - ry * math.sqrt(max(0.0, 1 - u * u))
        hmax = int(min(base_y - top - 4, 22))
        if hmax <= 2:
            continue
        h = rng.randrange(max(2, hmax // 3), hmax)
        for k in range(h):
            cv.put(x + int(math.sin(k * 0.6 + x) * 1.2), base_y - 1 - k, plants[k % 3] if alive else hx("8a7a4a"))
        if alive and rng.random() < 0.3:
            cv.disc(x, base_y - h, 1.6, plants[1])
            cv.put(x, base_y - h - 1, rng.choice([hx("ff6a5a"), GOLD]))
    # armazón geodésico
    for k in range(1, 6):
        a = math.pi * k / 6
        for t in range(0, 100):
            r = t / 100
            x = cx + rx * math.cos(a) * math.sqrt(1 - (1 - r) ** 2) * (1 if k < 3 else 1)
            y = base_y - ry * r
            x = cx + rx * math.cos(a) * math.sin(math.acos(r)) if r <= 1 else x
            cv.put(int(x), int(y), hx("dfe3ea"))
    for k in range(1, 4):
        y = int(base_y - ry * k / 4)
        for x in range(W):
            if cv.get(x, y)[3]:
                cv.put(x, y, hx("dfe3ea"))
    for k in range(12):
        blend_put(cv, int(cx - rx * 0.55) + k // 3, int(base_y - ry * 0.75) + k, hx("ffffff"), 0.55)
    # anillo de base y esclusa
    ring = hx("c8ccd4") if planet == "moon" else hx("b0643c")
    cv.rect(1, H - 7, W - 2, H - 1, ring)
    cv.hline(1, W - 2, H - 7, shade(ring, 1.25))
    cv.hline(1, W - 2, H - 1, shade(ring, 0.6))
    door(cv, W // 2, H - 2, hx("5a6070"), w=10, h=12, lamp=CYAN if planet == "moon" else GOLD)
    return add_outline(cv.img)


def hangar(w, d, wall, seed):
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    R = d * 16
    for y in range(1, R + 3):  # techo abovedado
        t = (y - 1) / (R + 2)
        c = mix(hx("c8ced8"), hx("7a8090"), t)
        for x in range(1, W - 1):
            cv.put(x, y, c if (x // 4) % 2 else shade(c, 0.94))
    cv.hline(2, W - 3, 1, hx("f0f2f6"))
    facade(cv, 1, R + 3, W - 2, H - 1, hx("9aa2b0"), rng, panels=True)
    cx = W // 2
    cv.rect(cx - 30, R + 10, cx + 29, H - 1, hx("3a404c"))
    for y in range(R + 11, H - 1, 3):
        cv.hline(cx - 29, cx + 28, y, hx("5a6070"))
    for x in range(cx - 31, cx + 31):
        cv.put(x, R + 9, hx("e8c03a") if (x // 3) % 2 else hx("2a2830"))
    for x in (6, W - 8):
        cv.rect(x, R + 8, x + 2, R + 10, hx("2a2830"))
        cv.put(x + 1, R + 9, hx("ff4a4a"))
    draw_text(cv, "H-2", cx - 5, R + 14, hx("e8c03a"))
    return add_outline(cv.img)


# ------------------------------------------------------------ Marte

def mars_block(w, d, wall, seed, sign=None, color=hx("c8865c"), accent=GOLD, kind="block", shop=None):
    """Regolito impreso en 3D: capas horizontales, esquinas redondeadas, ventanas en arco."""
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    R = d * 16
    roof = shade(color, 0.92)
    roof_flat(cv, 1, 2, W - 2, R + 1, roof, rng,
              extras=["stairs"] + rng.sample(["ac", "solar", "antenna", "vents", "dish", "skylight", "garden", "pipes"], 4))
    # bordes redondeados del tejado
    for (x, y) in ((1, 2), (2, 2), (1, 3), (W - 2, 2), (W - 3, 2), (W - 2, 3)):
        cv.put(x, y, CLEAR)
    facade(cv, 1, R + 2, W - 2, H - 1, color, rng, layered=True)
    cv.hline(1, W - 2, R + 2, shade(color, 1.3))
    cv.hline(1, W - 2, R + 3, shade(color, 0.6))
    floors = max(1, (wall - 20) // 16)
    cols = max(2, (W - 8) // 13)
    step = (W - 12) / cols
    for f in range(floors):
        y = H - 20 - (f + 1) * 16 + 4
        if y < R + 6:
            break
        for c in range(cols):
            x = int(7 + c * step)
            arch_window(cv, x, y, 6, 9, rng.random() < 0.6, rng, hx("4a2a22"),
                        rng.choice([WARM, hx("ffe0a0"), mix(CYAN, WARM, 0.6)]))
    gt = H - 20
    cv.hline(1, W - 2, gt - 1, shade(color, 1.2))
    if shop:
        scol, goods = shop
        shopfront(cv, 4, W // 2 - 9, gt + 5, H - 2, scol, rng, goods)
        shopfront(cv, W // 2 + 8, W - 6, gt + 5, H - 2, scol, rng, goods)
        awning(cv, 3, W - 4, gt + 1, scol, hx("e8d0b0"))
    elif kind == "garage":
        cv.rect(W // 2 - 20, gt + 3, W // 2 + 19, H - 1, hx("3a2a26"))
        for y in range(gt + 4, H - 1, 3):
            cv.hline(W // 2 - 19, W // 2 + 18, y, hx("6a4a3a"))
        for x in range(W // 2 - 21, W // 2 + 21):
            cv.put(x, gt + 2, hx("e8c03a") if (x // 3) % 2 else hx("2a2830"))
    else:
        for x in (6, W - 14):
            arch_window(cv, x, gt + 4, 7, 10, rng.random() < 0.7, rng, hx("4a2a22"))
    # puerta en arco
    cx = W // 2
    if kind != "garage":
        cv.rect(cx - 6, H - 16, cx + 5, H - 1, hx("4a2a22"))
        cv.hline(cx - 5, cx + 4, H - 17, hx("4a2a22"))
        cv.rect(cx - 5, H - 15, cx + 4, H - 1, shade(accent, 0.55))
        cv.hline(cx - 4, cx + 3, H - 16, shade(accent, 0.55))
        cv.rect(cx - 3, H - 13, cx + 2, H - 9, mix(WARM, accent, 0.3))
        cv.put(cx - 3, H - 13, hx("ffffff"))
        cv.put(cx + 3, H - 8, GOLD)
        cv.hline(cx - 8, cx + 7, H - 1, shade(color, 0.7))
    # tubería de aire y luces
    drain_pipe(cv, W - 7, R + 5, H - 3, hx("8a7a80"))
    cv.rect(cx + 8, H - 18, cx + 9, H - 16, hx("2a2632"))
    cv.put(cx + 9, H - 17, accent)
    if sign:
        text, scolor = sign
        neon_sign(cv, text, cx, gt - 8, scolor)
    return add_outline(cv.img)


def mars_tower(w, d, wall, seed):
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    R = d * 16
    roof_flat(cv, 1, 1, W - 2, R + 1, hx("5a5460"), rng, extras=["antenna", "dish", "vents"])
    facade(cv, 1, R + 2, W - 2, H - 1, hx("4a4652"), rng)
    for y in range(R + 6, H - 22, 7):
        for x in range(4, W - 4, 6):
            lit = rng.random() < 0.5
            c = mix(hx("ff8a4a"), GOLD, rng.random()) if lit else hx("2a2632")
            cv.rect(x, y, x + 4, y + 4, c)
            if lit:
                cv.put(x, y, hx("ffffff"))
    for x in (2, W - 4):
        neon_strip(cv, x, x + 1, R + 4, PINK)
        for y in range(R + 4, H - 4):
            cv.put(x, y, mix(PINK, hx("4a4652"), 0.4))
    neon_sign(cv, "MARSCORP", W // 2, R + 10, PINK)
    gt = H - 20
    shopfront(cv, 5, W - 6, gt + 4, H - 2, PINK, rng, "tech")
    door(cv, W // 2, H - 2, hx("4a2a3a"), lamp=PINK)
    return add_outline(cv.img)


def mars_silo(w, d, wall, seed):
    rng = random.Random(seed)
    W, H = w * 16, d * 16 + wall
    cv = Canvas(W, H)
    cx = W / 2
    cv.ellipse(cx, 9, W / 2 - 1, 8, hx("d8dce4"))
    cv.ellipse(cx - 2, 7, W / 2 - 6, 5, hx("f0f2f6"))
    for y in range(9, H - 1):
        for x in range(1, W - 1):
            u = (x + 0.5 - cx) / (W / 2 - 1)
            cv.put(x, y, mix(hx("f0f2f6"), hx("8a909c"), (u + 1) / 2))
    for y in range(14, H - 2, 8):
        cv.hline(1, W - 2, y, hx("9aa0ac"))
    cv.vline(W - 6, 12, H - 2, hx("5a6070"))
    for y in range(12, H - 2, 3):
        cv.hline(W - 7, W - 5, y, hx("5a6070"))
    draw_text(cv, "CH4", int(cx) - 6, H // 2, hx("c8302a"))
    cv.ellipse(cx, H - 2, W / 2 - 1, 1.5, hx("6a707a"))
    return add_outline(cv.img)


# ------------------------------------------------------------ catálogo

def buildings() -> None:
    # Tierra
    reg("bld_e_apt_4a", earth_apartment(4, 3, 64, (hx("8a9a9a"), hx("5a6468"), hx("4a7a8a")), 11), 4, 3, 64, "earth", "apt")
    reg("bld_e_apt_4b", earth_apartment(4, 3, 48, (hx("b08a7a"), hx("6a5a58"), hx("8a4a3a")), 12), 4, 3, 48, "earth", "apt")
    reg("bld_e_apt_5a", earth_apartment(5, 3, 80, (hx("a49a7a"), hx("5e5a50"), hx("6a5a2a")), 13), 5, 3, 80, "earth", "apt")
    reg("bld_e_apt_5b", earth_apartment(5, 3, 64, (hx("7a8aa4"), hx("4e5662"), hx("3a4a7a")), 14,
                                         shop=(PINK, "tech")), 5, 3, 64, "earth", "apt")
    reg("bld_e_apt_6a", earth_apartment(6, 4, 80, (hx("9a8a9e"), hx("56505e"), hx("5a3a6a")), 15,
                                         shop=(hx("e8a03a"), "food")), 6, 4, 80, "earth", "apt")
    reg("bld_e_house_3a", earth_house(3, 2, 32, hx("b4553a"), hx("d8c8a8"), 21), 3, 2, 32, "earth", "house")
    reg("bld_e_house_3b", earth_house(3, 2, 32, hx("4a6a8a"), hx("c8c0b0"), 22, warm=False), 3, 2, 32, "earth", "house")
    reg("bld_e_house_4a", earth_house(4, 3, 32, hx("5a7a4a"), hx("d0c4a4"), 23, extras=("chimney", "solar", "bricks")),
        4, 3, 32, "earth", "house")
    reg("bld_e_home_andres", earth_house(4, 3, 32, hx("c0442e"), hx("e8d8b8"), 24, extras=("chimney", "solar")),
        4, 3, 32, "earth", "house")
    reg("bld_e_ruin_4", earth_ruin(4, 3, 48, 31), 4, 3, 48, "earth", "ruin")
    reg("bld_e_ruin_3", earth_ruin(3, 2, 40, 32), 3, 2, 40, "earth", "ruin")
    reg("bld_e_tower_6", earth_tower(6, 4, 112, 33), 6, 4, 112, "earth", "tower")
    reg("bld_e_kiosk_2", earth_kiosk(34), 2, 1, 24, "earth", "kiosk")
    reg("bld_e_vault", earth_vault(35), 10, 3, 48, "earth", "vault")
    reg("bld_e_greenhouse_4", greenhouse(4, 3, 24, False, 36), 4, 3, 24, "earth", "greenhouse")
    reg("bld_e_shop", earth_apartment(5, 3, 48, (hx("6a8a74"), hx("4a5650"), hx("2a5a3a")), 37,
                                      floors=1, sign=("EL ÚLTIMO BROTE", GREEN), shop=(GREEN, "plants")),
        5, 3, 48, "earth", "shop")
    # Luna
    reg("bld_m_hab_3", moon_module(3, 2, 32, 41), 3, 2, 32, "moon", "hab")
    reg("bld_m_hab_4", moon_module(4, 3, 32, 42, accent=hx("3a7ac8")), 4, 3, 32, "moon", "hab")
    reg("bld_m_hab_5", moon_module(5, 3, 40, 43, accent=hx("e8c03a")), 5, 3, 40, "moon", "hab")
    reg("bld_m_dome_6", dome(6, 4, 24, 44, "moon"), 6, 4, 24, "moon", "dome")
    reg("bld_m_lab_5", moon_module(5, 3, 40, 45, accent=CYAN, kind="lab"), 5, 3, 40, "moon", "lab")
    reg("bld_m_hangar_6", hangar(6, 4, 48, 46), 6, 4, 48, "moon", "hangar")
    reg("bld_m_bar", moon_module(5, 3, 40, 47, sign=("BAR CRÁTER", PINK), accent=PINK), 5, 3, 40, "moon", "bar")
    reg("bld_m_shop", moon_module(5, 3, 40, 48, sign=("REPUESTOS", GOLD), accent=GOLD), 5, 3, 40, "moon", "shop")
    reg("bld_m_dorm", moon_module(4, 3, 32, 49, sign=("HOGAR", CYAN), accent=CYAN), 4, 3, 32, "moon", "dorm")
    # Marte
    reg("bld_r_block_4", mars_block(4, 3, 48, 51), 4, 3, 48, "mars", "block")
    reg("bld_r_block_5", mars_block(5, 3, 56, 52, color=hx("b87452")), 5, 3, 56, "mars", "block")
    reg("bld_r_dome_5", dome(5, 4, 24, 53, "mars"), 5, 4, 24, "mars", "dome")
    reg("bld_r_tower_4", mars_tower(4, 3, 96, 54), 4, 3, 96, "mars", "tower")
    reg("bld_r_silo_2", mars_silo(2, 2, 48, 55), 2, 2, 48, "mars", "silo")
    reg("bld_r_lab_5", mars_block(5, 3, 40, 56, color=hx("d8c8b8"), accent=CYAN), 5, 3, 40, "mars", "lab")
    reg("bld_r_bar", mars_block(5, 3, 48, 57, sign=("CANTINA", PINK), accent=PINK, shop=(PINK, "food")), 5, 3, 48, "mars", "bar")
    reg("bld_r_shop", mars_block(5, 3, 48, 58, sign=("MERCADO", GREEN), accent=GREEN, shop=(GREEN, "food")), 5, 3, 48, "mars", "shop")
    reg("bld_r_school", mars_block(5, 3, 48, 59, sign=("ESCUELA", CYAN), accent=CYAN, color=hx("d0946a")), 5, 3, 48, "mars", "school")
    reg("bld_r_garage", mars_block(5, 3, 48, 60, sign=("TALLER", GOLD), accent=GOLD, kind="garage", color=hx("a8704e")),
        5, 3, 48, "mars", "garage")
    reg("bld_r_house", mars_block(4, 3, 32, 61, color=hx("c47a54")), 4, 3, 32, "mars", "house")
    reg("bld_r_greenhouse", greenhouse(4, 3, 24, False, 62, base=hx("a46a4a")), 4, 3, 24, "mars", "greenhouse")
    reg("bld_r_greenhouse_alive", greenhouse(4, 3, 24, True, 62, base=hx("a46a4a")), 4, 3, 24, "mars", "greenhouse")
    save_json(BUILDINGS, ART, "props", "buildings.json")



# ================================================================== 3. MOBILIARIO URBANO

METALS = {"e": (hx("3a3e4a"), hx("5a6070"), CYAN), "m": (hx("c8ccd4"), hx("eef0f4"), hx("8ad8ff")),
          "r": (hx("6a4a3e"), hx("8a6a5a"), GOLD)}


def shadow_ellipse(cv, cx, cy, rx, ry, a=110):
    cv.ellipse(cx, cy, rx, ry, (20, 16, 30, a))


def lamp_smart(kind):
    dark, light, glow = METALS[kind]
    cv = Canvas(16, 40)
    shadow_ellipse(cv, 8, 38, 5, 1.5)
    cv.rect(5, 35, 10, 38, dark)
    cv.hline(5, 10, 35, light)
    cv.rect(7, 8, 8, 35, dark)
    cv.vline(7, 8, 35, light)
    cv.rect(6, 22, 9, 24, shade(dark, 0.8))  # panel con QR/luz
    cv.put(8, 23, glow)
    # brazo curvo y cabezal
    for k, (x, y) in enumerate(((8, 7), (9, 6), (10, 5), (11, 5), (12, 5))):
        cv.put(x, y, dark)
    cv.rect(9, 3, 15, 5, dark)
    cv.hline(9, 15, 3, light)
    cv.hline(10, 14, 6, glow)
    cv.hline(11, 13, 7, mix(glow, hx("ffffff"), 0.5))
    img = add_outline(cv.img)
    return img


def bench_holo():
    cv = Canvas(32, 16)
    shadow_ellipse(cv, 16, 14, 14, 2)
    cv.rect(3, 10, 4, 14, hx("3a3e4a"))
    cv.rect(27, 10, 28, 14, hx("3a3e4a"))
    cv.rect(1, 7, 30, 10, hx("8a6a4a"))  # asiento de madera reciclada
    cv.hline(1, 30, 7, hx("b08a64"))
    for x in range(1, 31, 5):
        cv.vline(x, 7, 10, hx("6a4e36"))
    cv.rect(1, 2, 30, 5, hx("7a5e42"))  # respaldo
    cv.hline(1, 30, 2, hx("a07c58"))
    cv.hline(1, 30, 11, CYAN)  # tira de luz
    cv.hline(1, 30, 12, mix(CYAN, hx("1e1a24"), 0.5))
    return add_outline(cv.img)


def bin_smart():
    cv = Canvas(12, 16)
    shadow_ellipse(cv, 6, 15, 5, 1.2)
    cv.rect(1, 4, 10, 14, hx("3a6a5a"))
    cv.vline(1, 4, 14, hx("5a9a7a"))
    cv.vline(10, 4, 14, hx("2a4a40"))
    cv.rect(0, 2, 11, 4, hx("4a4e5a"))
    cv.hline(0, 11, 2, hx("8a909c"))
    cv.rect(4, 3, 7, 3, hx("1e1a24"))
    cv.rect(3, 7, 8, 9, hx("2a4a40"))
    cv.put(5, 8, GREEN)  # símbolo de reciclaje
    cv.put(6, 7, GREEN)
    cv.put(7, 8, GREEN)
    return add_outline(cv.img)


def kiosk_info():
    cv = Canvas(14, 28)
    shadow_ellipse(cv, 7, 26, 6, 1.5)
    cv.rect(5, 18, 8, 26, hx("3a3e4a"))
    cv.rect(1, 2, 12, 18, hx("2a2e3a"))
    cv.hline(1, 12, 2, hx("6a7080"))
    cv.rect(2, 4, 11, 16, hx("10303a"))
    for y in range(4, 17):
        cv.hline(2, 11, y, mix(hx("10303a"), CYAN, 0.25 + 0.2 * ((y - 4) % 4 == 0)))
    cv.rect(3, 5, 10, 7, CYAN)  # mapa
    cv.put(4, 10, GOLD)
    cv.hline(3, 9, 12, hx("8ad8ff"))
    cv.hline(3, 7, 14, hx("8ad8ff"))
    cv.put(2, 4, hx("ffffff"))
    return add_outline(cv.img)


def charge_post():
    cv = Canvas(10, 22)
    shadow_ellipse(cv, 5, 20, 4, 1.2)
    cv.rect(2, 4, 7, 20, hx("4a5060"))
    cv.vline(2, 4, 20, hx("7a8090"))
    cv.rect(1, 2, 8, 4, hx("2a2e3a"))
    cv.rect(3, 7, 6, 10, hx("10303a"))
    cv.hline(3, 6, 8, GREEN)
    cv.put(4, 12, GOLD)
    cv.vline(7, 12, 18, hx("1e1a24"))  # cable
    cv.put(8, 18, hx("1e1a24"))
    return add_outline(cv.img)


def planter(alive):
    cv = Canvas(32, 18)
    shadow_ellipse(cv, 16, 16, 15, 2)
    cv.rect(1, 9, 30, 16, hx("5a6070") if alive else hx("6a6058"))
    cv.hline(1, 30, 9, hx("8a90a0") if alive else hx("8a8076"))
    cv.rect(2, 10, 29, 11, hx("3a2a22"))
    if alive:
        cv.hline(1, 30, 14, GREEN)
        rng = random.Random(7)
        for x in range(2, 30, 2):
            h = rng.randrange(3, 8)
            for k in range(h):
                cv.put(x + (k % 2), 10 - k, hx("4aa04a") if k % 2 else hx("7ad05a"))
            if rng.random() < 0.3:
                cv.put(x, 10 - h, rng.choice([hx("ff6a5a"), GOLD]))
    else:
        rng = random.Random(8)
        for x in range(3, 29, 4):
            for k in range(rng.randrange(2, 6)):
                cv.put(x + (k % 2), 10 - k, hx("8a7a4a"))
        cv.hline(4, 9, 13, hx("4a4038"))
    return add_outline(cv.img)


def tree_dead_big():
    cv = Canvas(40, 48)
    shadow_ellipse(cv, 20, 45, 13, 3)
    rng = random.Random(9)
    bark, bl = hx("5a4a3e"), hx("7a6656")

    def branch(x, y, ang, length, width):
        for k in range(int(length)):
            xx = x + math.cos(ang) * k
            yy = y - math.sin(ang) * k
            for w in range(width):
                cv.put(int(xx) + w, int(yy), bark if w else bl)
        ex, ey = x + math.cos(ang) * length, y - math.sin(ang) * length
        if length > 5:
            branch(ex, ey, ang + rng.uniform(0.3, 0.6), length * 0.65, max(1, width - 1))
            branch(ex, ey, ang - rng.uniform(0.3, 0.6), length * 0.6, max(1, width - 1))
    cv.rect(17, 30, 21, 45, bark)
    cv.vline(17, 30, 45, bl)
    cv.hline(15, 23, 45, bark)
    branch(19, 31, math.pi / 2, 12, 3)
    branch(19, 33, math.pi / 2 + 0.7, 9, 2)
    branch(20, 34, math.pi / 2 - 0.8, 9, 2)
    for _ in range(6):  # hojas secas colgando
        x, y = rng.randrange(6, 34), rng.randrange(4, 22)
        if cv.get(x, y)[3]:
            cv.put(x, y + 1, hx("b08a3a"))
    # anillo de protección
    cv.hline(13, 25, 46, hx("6a6670"))
    return add_outline(cv.img)


def fountain_dry():
    cv = Canvas(32, 32)
    shadow_ellipse(cv, 16, 28, 15, 3)
    cv.ellipse(16, 22, 15, 8, hx("8a8e98"))
    cv.ellipse(16, 21, 13, 6.5, hx("b0b4bc"))
    cv.ellipse(16, 22, 11, 5, hx("5a5048"))
    cv.ellipse(16, 23, 9, 3.5, hx("6a6058"))
    for _ in range(5):
        x, y = random.Random(_).randrange(9, 23), random.Random(_ + 9).randrange(20, 25)
        cv.put(x, y, hx("8a7a4a"))
    cv.rect(14, 6, 17, 21, hx("9a9ea8"))
    cv.vline(14, 6, 21, hx("c8ccd4"))
    cv.ellipse(15.5, 7, 5, 2.5, hx("b0b4bc"))
    cv.ellipse(15.5, 6.5, 3.5, 1.5, hx("6a6058"))
    cv.disc(16, 3, 2.2, GREEN)  # brote de metal (escultura)
    cv.put(15, 2, hx("bfffcf"))
    return add_outline(cv.img)


def hover_stop():
    cv = Canvas(48, 36)
    shadow_ellipse(cv, 24, 33, 22, 2.5)
    cv.rect(2, 4, 45, 9, hx("3a3e4a"))
    cv.hline(2, 45, 4, hx("6a7080"))
    cv.rect(3, 6, 44, 8, mix(CYAN, hx("3a3e4a"), 0.5))
    draw_text(cv, "AEROBUS", 10, 5, hx("ffffff"))
    for x in (4, 43):
        cv.rect(x, 10, x + 1, 33, hx("4a4e5a"))
    cv.rect(6, 10, 30, 28, alpha(hx("8ad8ff"), 120))  # mampara
    cv.hline(6, 30, 10, hx("bfe8ff"))
    for k in range(6):
        blend_put(cv, 8 + k, 12 + k * 2, hx("ffffff"), 0.4)
    cv.rect(32, 12, 41, 24, hx("10303a"))  # pantalla de horarios
    for y in (14, 17, 20):
        cv.hline(33, 40, y, CYAN)
        cv.put(40, y, GOLD)
    cv.rect(8, 26, 28, 28, hx("8a6a4a"))  # banco
    cv.hline(8, 28, 26, hx("b08a64"))
    cv.hline(2, 45, 34, hx("e8c03a"))
    return add_outline(cv.img)


def tram_stop():
    cv = Canvas(48, 30)
    shadow_ellipse(cv, 24, 27, 22, 2)
    cv.rect(1, 22, 46, 27, hx("8a90a0"))
    cv.hline(1, 46, 22, hx("c8ccd4"))
    for x in range(1, 47):
        cv.put(x, 27, hx("e8c03a") if (x // 3) % 2 else hx("2a2830"))
    cv.rect(3, 2, 44, 6, hx("2a2e3a"))
    cv.hline(3, 44, 2, hx("6a7080"))
    cv.hline(3, 44, 6, PINK)
    draw_text(cv, "MAGLEV", 12, 3, PINK)
    for x in (6, 41):
        cv.rect(x, 7, x + 1, 22, hx("4a4e5a"))
    cv.rect(18, 10, 29, 18, hx("10303a"))
    cv.hline(19, 28, 12, CYAN)
    cv.hline(19, 25, 15, GOLD)
    return add_outline(cv.img)


def stall(kind):
    cv = Canvas(32, 30)
    shadow_ellipse(cv, 16, 28, 15, 2)
    c1, c2, goods = {"food": (hx("e86a3a"), hx("f4e0c0"), "food"), "tech": (CYAN, hx("1e3a44"), "tech"),
                     "plants": (GREEN, hx("2e5a3a"), "plants")}[kind]
    for x in (2, 29):
        cv.rect(x, 6, x + 1, 27, hx("5a4a3e"))
    for y in range(2, 9):  # toldo
        for x in range(0, 32):
            c = c1 if (x // 4) % 2 == 0 else c2
            cv.put(x, y, shade(c, 1.12 - 0.04 * (y - 2)))
    for x in range(0, 32, 4):
        cv.put(x + 1, 9, c1)
        cv.put(x + 2, 9, c1)
    cv.rect(1, 17, 30, 27, hx("7a5a40"))
    cv.hline(1, 30, 17, hx("a07c58"))
    cv.vline(30, 17, 27, hx("5a4030"))
    rng = random.Random(len(kind))
    for x in range(3, 29, 3):
        if goods == "food":
            cv.rect(x, 14, x + 1, 16, rng.choice([hx("ff6a3a"), GOLD, hx("8ad04a"), hx("e83a5a")]))
            cv.put(x, 14, hx("ffffff"))
        elif goods == "tech":
            cv.rect(x, 13, x + 1, 16, rng.choice([hx("4a5060"), hx("8a90a0")]))
            cv.put(x, 13, rng.choice([CYAN, PINK, GOLD]))
        else:
            cv.rect(x, 15, x + 1, 16, hx("9a5a3a"))
            cv.vline(x, 11, 14, hx("4aa04a"))
            cv.put(x + 1, 12, hx("8ad05a"))
    cv.rect(10, 20, 21, 24, hx("2a2632"))  # cartel de precio
    draw_text(cv, "3CR", 11, 20, GOLD)
    return add_outline(cv.img)


def vendor_cart():
    cv = Canvas(28, 26)
    cv.ellipse(14, 24, 10, 1.5, alpha(CYAN, 120))  # flota
    cv.rect(3, 12, 24, 20, hx("c8ccd4"))
    cv.hline(3, 24, 12, hx("eef0f4"))
    cv.rect(3, 18, 24, 20, hx("8a909c"))
    cv.hline(4, 23, 21, CYAN)
    cv.rect(6, 14, 12, 16, hx("e86a3a"))
    draw_text(cv, "JUGO", 13, 14, PINK)
    cv.vline(13, 2, 12, hx("4a4e5a"))
    for y in range(0, 5):  # sombrilla
        cv.hline(13 - (y * 3), 13 + (y * 3), y + 1, PINK if (y % 2) else hx("ff8ac5"))
    return add_outline(cv.img)


def ac_unit():
    cv = Canvas(14, 12)
    cv.rect(1, 1, 12, 9, hx("b8bcc4"))
    cv.hline(1, 12, 1, hx("e2e5ea"))
    cv.vline(12, 1, 9, hx("7a808a"))
    cv.disc(6, 5, 3, hx("4a505a"))
    for a in range(4):
        cv.put(int(6 + 2 * math.cos(a * 1.57)), int(5 + 2 * math.sin(a * 1.57)), hx("8a909a"))
    cv.hline(1, 12, 10, hx("4a4650"))
    return add_outline(cv.img)


def crate_stack():
    cv = Canvas(18, 22)
    shadow_ellipse(cv, 9, 20, 8, 1.5)

    def crate(x, y, w, h, c):
        cv.rect(x, y, x + w, y + h, c)
        cv.hline(x, x + w, y, shade(c, 1.25))
        cv.vline(x + w, y, y + h, shade(c, 0.7))
        cv.hline(x, x + w, y + h // 2, shade(c, 0.8))
        cv.put(x + 1, y + 1, shade(c, 1.4))
    crate(1, 11, 15, 8, hx("8a6a4a"))
    crate(3, 3, 11, 7, hx("5a7a8a"))
    cv.rect(5, 5, 8, 6, GOLD)
    return add_outline(cv.img)


def barrel_water():
    cv = Canvas(12, 16)
    shadow_ellipse(cv, 6, 15, 5, 1.2)
    cv.rect(1, 3, 10, 14, hx("3a6ab0"))
    cv.vline(1, 3, 14, hx("6a9ad8"))
    cv.vline(10, 3, 14, hx("2a4a80"))
    cv.ellipse(5.5, 3, 4.5, 1.5, hx("8abaf0"))
    cv.hline(1, 10, 7, hx("2a4a80"))
    cv.hline(1, 10, 11, hx("2a4a80"))
    cv.put(4, 9, hx("ffffff"))
    cv.put(5, 9, hx("ffffff"))
    return add_outline(cv.img)


def solar_tree():
    cv = Canvas(28, 44)
    shadow_ellipse(cv, 14, 42, 9, 2)
    cv.rect(13, 14, 15, 41, hx("4a5060"))
    cv.vline(13, 14, 41, hx("7a8090"))
    cv.hline(10, 18, 41, hx("4a5060"))
    for (x, y, w) in ((2, 10, 9), (17, 8, 9), (8, 2, 11), (4, 18, 7), (17, 18, 7)):
        cx = x + w // 2
        cv.vline(cx, y + 3, 16, hx("4a5060"))
        solar_panel(cv, x, y, w)
    cv.put(14, 30, GREEN)
    cv.put(14, 31, shade(GREEN, 0.7))
    return add_outline(cv.img)


def antenna_small():
    cv = Canvas(12, 26)
    shadow_ellipse(cv, 6, 24, 4, 1)
    cv.vline(6, 4, 24, hx("5a6070"))
    cv.vline(5, 10, 24, hx("8a909c"))
    for y, w in ((8, 4), (12, 3), (16, 2)):
        cv.hline(6 - w, 6 + w, y, hx("5a6070"))
    cv.disc(6, 3, 1.5, hx("ff4a4a"))
    cv.rect(3, 22, 9, 24, hx("4a4e5a"))
    return add_outline(cv.img)


def sign_arrow():
    cv = Canvas(16, 24)
    shadow_ellipse(cv, 8, 22, 4, 1)
    cv.vline(7, 6, 22, hx("4a4e5a"))
    cv.vline(8, 6, 22, hx("7a8090"))
    pts = [(1, 2), (12, 2), (15, 5), (12, 8), (1, 8)]
    cv.rect(1, 2, 12, 8, hx("1e5a54"))
    for k in range(3):
        cv.vline(13 + k, 3 + k, 7 - k, hx("1e5a54"))
    cv.hline(1, 12, 2, CYAN)
    cv.hline(3, 10, 5, hx("eef0f4"))
    cv.put(11, 4, hx("eef0f4"))
    cv.put(11, 6, hx("eef0f4"))
    return add_outline(cv.img)


def hydrant_water():
    cv = Canvas(10, 14)
    shadow_ellipse(cv, 5, 13, 4, 1)
    cv.rect(2, 4, 7, 12, hx("3a7ac8"))
    cv.vline(2, 4, 12, hx("6aa0e8"))
    cv.rect(1, 6, 8, 7, hx("2a5a9a"))
    cv.ellipse(4.5, 3.5, 2.5, 1.5, hx("8abaf0"))
    cv.put(4, 9, hx("ffffff"))
    cv.hline(1, 8, 12, hx("2a5a9a"))
    return add_outline(cv.img)


def bollard_light():
    cv = Canvas(8, 14)
    shadow_ellipse(cv, 4, 13, 3, 1)
    cv.rect(2, 3, 5, 12, hx("4a4e5a"))
    cv.vline(2, 3, 12, hx("7a8090"))
    cv.rect(2, 2, 5, 4, CYAN)
    cv.hline(2, 5, 2, hx("bfffff"))
    return add_outline(cv.img)


def cable_post():
    cv = Canvas(16, 44)
    shadow_ellipse(cv, 8, 42, 4, 1)
    cv.rect(7, 4, 8, 42, hx("5a4a40"))
    cv.vline(7, 4, 42, hx("7a6656"))
    cv.hline(1, 14, 7, hx("4a3e36"))
    cv.hline(3, 12, 12, hx("4a3e36"))
    for x in (1, 4, 11, 14):
        cv.put(x, 6, hx("c8ccd4"))
    cv.rect(9, 18, 12, 22, hx("6a7080"))  # transformador
    cv.put(11, 19, GREEN)
    for x in range(0, 16):  # cables que salen hacia los lados
        cv.put(x, 8 + int(abs(x - 7.5) / 3), hx("1e1a24"))
    return add_outline(cv.img)


def trash_robot_dock():
    cv = Canvas(18, 18)
    shadow_ellipse(cv, 9, 16, 8, 1.5)
    cv.rect(2, 4, 15, 15, hx("4a5060"))
    cv.hline(2, 15, 4, hx("8a909c"))
    cv.rect(4, 8, 13, 15, hx("1e1a24"))
    cv.hline(4, 13, 8, GOLD)
    cv.rect(6, 5, 11, 6, hx("10303a"))
    cv.hline(7, 9, 5, GREEN)
    for x in range(2, 16):
        cv.put(x, 16, hx("e8c03a") if (x // 2) % 2 else hx("2a2830"))
    return add_outline(cv.img)


def mural_wall():
    cv = Canvas(48, 32)
    rng = random.Random(77)
    cv.rect(0, 4, 47, 30, hx("8a8478"))
    cv.hline(0, 47, 4, hx("aaa498"))
    for y in range(6, 30, 4):
        cv.hline(0, 47, y, hx("7a7468"))
    # mural: planeta verde, brote y sol
    cv.disc(14, 18, 9, hx("2a6aa0"))
    cv.disc(12, 16, 6, hx("4aa04a"))
    cv.disc(17, 21, 3, hx("4aa04a"))
    cv.disc(36, 11, 4, GOLD)
    for a in range(8):
        cv.put(int(36 + 6 * math.cos(a * 0.785)), int(11 + 6 * math.sin(a * 0.785)), GOLD)
    cv.vline(32, 18, 27, hx("4aa04a"))
    cv.put(31, 19, GREEN)
    cv.put(33, 20, GREEN)
    cv.put(30, 21, GREEN)
    draw_text(cv, "VIDA", 26, 24, PINK)
    cv.rect(0, 30, 47, 31, hx("5a5448"))
    return add_outline(cv.img)


def decal_arrow():
    cv = Canvas(16, 16)
    c = alpha(hx("d8dce4"), 170)
    cv.rect(7, 6, 8, 13, c)
    for k in range(4):
        cv.hline(7 - k, 8 + k, 2 + k, c)
    return cv.img


def decal_logo(text, color):
    w = max(32, text_w(text) + 8)
    cv = Canvas(w, 12)
    c = alpha(color, 120)
    cv.rect(1, 1, w - 2, 10, alpha(shade(color, 0.4), 90))
    draw_text(cv, text, (w - text_w(text)) // 2, 4, c)
    return cv.img


def decal_logo_seed():
    cv = Canvas(24, 16)
    c = alpha(GOLD, 120)
    cv.ellipse(12, 10, 6, 4, c)
    cv.vline(12, 2, 8, alpha(GREEN, 140))
    cv.put(11, 3, alpha(GREEN, 140))
    cv.put(13, 4, alpha(GREEN, 140))
    return cv.img


def furniture() -> None:
    out = {
        "lamp_smart_e": lamp_smart("e"), "lamp_smart_m": lamp_smart("m"), "lamp_smart_r": lamp_smart("r"),
        "bench_holo": bench_holo(), "bin_smart": bin_smart(), "kiosk_info": kiosk_info(),
        "charge_post": charge_post(), "planter_hydro": planter(True), "planter_dead": planter(False),
        "tree_dead_big": tree_dead_big(), "fountain_dry": fountain_dry(), "hover_stop": hover_stop(),
        "tram_stop": tram_stop(), "stall_food": stall("food"), "stall_tech": stall("tech"),
        "stall_plants": stall("plants"), "vendor_cart": vendor_cart(), "ac_unit": ac_unit(),
        "crate_stack": crate_stack(), "barrel_water": barrel_water(), "solar_tree": solar_tree(),
        "antenna_small": antenna_small(), "sign_arrow": sign_arrow(), "hydrant_water": hydrant_water(),
        "bollard_light": bollard_light(), "cable_post": cable_post(), "trash_robot_dock": trash_robot_dock(),
        "mural_wall": mural_wall(),
        "decal_arrow": decal_arrow(), "decal_logo_agronet": decal_logo("AGRONET", GREEN),
        "decal_logo_marscorp": decal_logo("MARSCORP", PINK), "decal_logo_seed": decal_logo_seed(),
    }
    for name, img in out.items():
        G.save(img, "props", f"{name}.png")


def main() -> None:
    for i, pl in enumerate(("earth", "moon", "mars")):
        city_tileset(pl, 500 + i * 37)
    buildings()
    furniture()
    G.crowd_assets()


if __name__ == "__main__" and len(sys.argv) == 1:
    main()
if __name__ == "__main__" and "--tiles" in sys.argv:
    for i, pl in enumerate(("earth", "moon", "mars")):
        city_tileset(pl, 500 + i * 37)
if __name__ == "__main__" and "--buildings" in sys.argv:
    buildings()
if __name__ == "__main__" and "--furniture" in sys.argv:
    furniture()
