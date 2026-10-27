"""Arte de combate de The Seed (campo 428×240 dibujado a ×3).

Uso:  python3 tools/pixelart/battle_art.py
Salida: game/assets/art/battle/*.png y game/assets/data/combat/sheets.json.
Determinista (semillas fijas). Reutiliza la paleta y los helpers de generate.py.

- Fondos en capas por escenario: <id>_sky (opaco), <id>_far (parallax lento),
  <id>_ground (suelo jugable), <id>_fg (primer plano) y <id>.png plano de respaldo.
- Hojas de animación: filas = animaciones, columnas = cuadros (ver ANIMS).
- Efectos: impacto, chispa eléctrica, destello de luz, curación, orbe solar, sombra.
Robots de los Antihumanistas: se desactivan (pose «off»), nunca se rompen.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate import (  # noqa: E402
    AH_RED, AH_STEEL, AH_STEEL_D, AH_STEEL_L, BAYER4, CHARACTERS, CLEAR, GAME, HAL_FACE,
    HAL_SILVER, HAL_SILVER_D, NEON_CYAN, NEON_GOLD, NEON_GREEN, NEON_PINK, OUTLINE, Canvas,
    _emblem, _lens, add_outline, hx, shade,
)

OUT = os.path.join(GAME, "assets", "art", "battle")
MANIFEST = os.path.join(GAME, "assets", "data", "combat", "sheets.json")
RES = "res://assets/art/battle/"
W, H = 428, 240


def lerp_c(a: tuple, b: tuple, t: float) -> tuple:
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (a[3] if len(a) > 3 else 255,)


def with_alpha(c: tuple, a: int) -> tuple:
    return (c[0], c[1], c[2], a)


def dith(x: int, y: int) -> float:
    return BAYER4[y % 4][x % 4] / 16.0


def canvas_of(img: Image.Image) -> Canvas:
    cv = Canvas(img.width, img.height)
    cv.img = img
    cv.px = img.load()
    return cv


def line(cv: Canvas, x0: float, y0: float, x1: float, y1: float, c: tuple, width: int = 1) -> None:
    steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(steps + 1):
        t = i / steps
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        if width <= 1:
            cv.put(int(round(x)), int(round(y)), c)
        else:
            r = width / 2.0
            cv.disc(x, y, r, c)


def noise1d(rng: random.Random, n: int, octaves: list[tuple[int, float]]) -> list[float]:
    """Ruido de valor 1D suave (suma de octavas interpoladas con coseno)."""
    out = [0.0] * n
    for period, amp in octaves:
        pts = [rng.uniform(-1, 1) for _ in range(n // period + 3)]
        for x in range(n):
            i, f = divmod(x / period, 1.0)
            i = int(i)
            f = (1 - math.cos(f * math.pi)) * 0.5
            out[x] += (pts[i] * (1 - f) + pts[i + 1] * f) * amp
    return out


# ================================================================ fondos

def sky(top: tuple, mid: tuple, horizon_c: tuple, horizon: int, seed: int, glow: tuple | None,
        glow_x: int, stars: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), top)
    px = img.load()
    for y in range(H):
        t = min(1.0, y / horizon)
        for x in range(W):
            tt = t + (dith(x, y) - 0.5) * 0.09
            q = round(max(0.0, min(1.0, tt)) * 10) / 10
            c = lerp_c(top, mid, q / 0.6) if q < 0.6 else lerp_c(mid, horizon_c, (q - 0.6) / 0.4)
            if glow is not None:
                d = math.hypot((x - glow_x) / 150.0, (y - horizon) / 46.0)
                g = max(0.0, 1.0 - d)
                g = round((g + (dith(x, y) - 0.5) * 0.12) * 6) / 6
                if g > 0:
                    c = lerp_c(c, glow, g * 0.75)
            px[x, y] = c
    rng = random.Random(seed)
    for _ in range(stars):
        x, y = rng.randrange(W), rng.randrange(int(horizon * 0.75))
        b = rng.choice([110, 150, 190, 235])
        fade = 1.0 - y / horizon
        px[x, y] = lerp_c(px[x, y], (b, b, min(255, b + 25), 255), fade)
    for _ in range(5):  # estrellas brillantes en cruz
        x, y = rng.randrange(8, W - 8), rng.randrange(6, int(horizon * 0.45))
        px[x, y] = (255, 250, 235, 255)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px[x + dx, y + dy] = lerp_c(px[x + dx, y + dy], (200, 210, 255, 255), 0.55)
    return img


def moon_body(cv: Canvas, cx: int, cy: int, rx: float, ry: float, base: tuple, seed: int) -> None:
    """Luna irregular (Fobos/Deimos) con luz desde la izquierda y cráteres."""
    rng = random.Random(seed)
    bumps = [rng.uniform(-0.12, 0.12) for _ in range(12)]
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            ang = math.atan2(dy, dx)
            k = 1.0 + bumps[int((ang + math.pi) / (2 * math.pi) * 12) % 12]
            r = math.hypot(dx, dy)
            if r <= k:
                lit = -dx * 0.7 - dy * 0.4 + 0.25
                f = 0.55 + 0.5 * max(0.0, min(1.0, lit + (dith(x, y) - 0.5) * 0.3))
                cv.put(x, y, shade(base, f))
    for _ in range(3):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.1, 0.5)
        cv.disc(cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d, max(0.8, rx * 0.22), shade(base, 0.6))


def ridge_layer(img: Image.Image, rng: random.Random, base_y: int, amp: float, col: tuple, top_col: tuple,
                octaves: list, strata: tuple | None = None, gullies: bool = False, mesa: bool = False) -> list[int]:
    """Cordillera: cima con ruido, bandas de estratos y cárcavas verticales. Devuelve la altura por x."""
    cv = canvas_of(img)
    n = noise1d(rng, W, octaves)
    if mesa:  # mesetas de cima plana
        n = [round(v * 2.2) / 2.2 for v in n]
    tops = [int(base_y + v * amp) for v in n]
    gully_x = [rng.randrange(W) for _ in range(28)] if gullies else []
    for x in range(W):
        t0 = tops[x]
        for y in range(t0, H):
            depth = y - t0
            c = col
            if strata is not None:
                band = (y + int(n[x] * 3)) % 9
                if band in (0, 1):
                    c = strata
                elif band == 5 and (x + y) % 3 == 0:
                    c = shade(col, 1.08)
            for gx in gully_x:
                if abs(x - gx) <= 1 and depth > 2 and ((y + gx) % 7) < 5:
                    c = shade(c, 0.78)
            if depth == 0:
                c = top_col
            elif depth == 1 and dith(x, y) < 0.5:
                c = top_col
            # luz del ocaso por la izquierda en las caras
            if x > 0 and tops[x - 1] > t0 + 1 and depth < 4:
                c = shade(c, 1.15)
            cv.put(x, y, c)
    return tops


def haze(img: Image.Image, y0: int, y1: int, color: tuple, strength: float) -> None:
    px = img.load()
    for y in range(y0, min(H, y1)):
        t = 1.0 - (y - y0) / max(1, y1 - y0)
        for x in range(W):
            c = px[x, y]
            if c[3] == 0:
                continue
            k = strength * t
            if dith(x, y) < k * 1.4:
                px[x, y] = lerp_c(c, color, 0.35)[:3] + (c[3],)


def rock(cv: Canvas, cx: int, cy: int, rx: int, ry: int, base: tuple, seed: int, cast: tuple | None = None) -> None:
    rng = random.Random(seed)
    if cast is not None:
        cv.ellipse(cx + rx * 0.5, cy + ry * 0.75, rx * 1.15, max(1.5, ry * 0.45), cast)
    bumps = [rng.uniform(-0.18, 0.12) for _ in range(10)]
    for y in range(cy - ry - 2, cy + ry + 2):
        for x in range(cx - rx - 2, cx + rx + 2):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if dy > 0.55:
                continue
            ang = math.atan2(dy, dx)
            k = 1.0 + bumps[int((ang + math.pi) / math.tau * 10) % 10]
            if math.hypot(dx, dy) <= k:
                lit = -dx * 0.6 - dy * 0.8
                f = 0.7 + 0.45 * max(-0.4, min(1.0, lit))
                if dith(x, y) < 0.25 and lit > 0.3:
                    f += 0.1
                cv.put(x, y, shade(base, f))
    # contorno superior oscuro discreto
    cv.hline(cx - rx + 2, cx + rx - 2, int(cy + ry * 0.55), shade(base, 0.5))


def pebble_field(cv: Canvas, rng: random.Random, y0: int, y1: int, base: tuple, n: int,
                 avoid: tuple | None = None) -> None:
    for _ in range(n):
        x, y = rng.randrange(W), rng.randrange(y0, y1)
        if avoid and avoid[0] < x < avoid[2] and avoid[1] < y < avoid[3] and rng.random() < 0.7:
            continue
        near = (y - y0) / max(1, y1 - y0)
        size = 1 if near < 0.4 else rng.choice([1, 1, 2])
        cv.rect(x, y, x + size - 1, y, shade(base, 0.62))
        cv.put(x, y - 1, shade(base, 1.25))


def crack(cv: Canvas, rng: random.Random, x: int, y: int, length: int, col: tuple, hi: tuple) -> None:
    for _ in range(length):
        cv.put(x, y, col)
        cv.put(x, y - 1, hi) if rng.random() < 0.3 else None
        x += rng.choice([1, 1, 2, -1])
        y += rng.choice([0, 0, 1, -1]) if rng.random() < 0.5 else 0
        if rng.random() < 0.08:
            crack(cv, rng, x, y, length // 3, col, hi)


def ground(base_far: tuple, base_near: tuple, accent: tuple, horizon: int, seed: int) -> Image.Image:
    """Suelo en perspectiva: más claro y brumoso al fondo, más saturado y oscuro delante."""
    img = Image.new("RGBA", (W, H), CLEAR)
    px = img.load()
    rng = random.Random(seed)
    edge = noise1d(rng, W, [(40, 2.0), (9, 0.8)])
    ripple = noise1d(rng, W, [(23, 1.0)])
    for y in range(horizon - 4, H):
        t = max(0.0, (y - horizon) / (H - horizon))
        for x in range(W):
            if y < horizon + edge[x]:
                continue
            c = lerp_c(base_far, base_near, t ** 0.8)
            # bandas de polvo (ripples) que se ensanchan con la cercanía
            period = 3 + int(t * 9)
            phase = (y + int(ripple[x] * (2 + t * 4))) % max(3, period)
            if phase == 0:
                c = shade(c, 0.88)
            elif phase == 1 and dith(x, y) < 0.5:
                c = shade(c, 1.07)
            if dith(x, y) < 0.08 + 0.05 * (1 - t):
                c = lerp_c(c, accent, 0.5)
            px[x, y] = c
    return img


def shadow_band(img: Image.Image, cx: int, cy: int, rx: int, ry: int, color: tuple, k: float = 0.4) -> None:
    px = img.load()
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if 0 <= x < W and 0 <= y < H and ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                c = px[x, y]
                if c[3] and dith(x, y) < 0.75:
                    px[x, y] = lerp_c(c, color, k)[:3] + (c[3],)


def wreck_marscorp(cv: Canvas, x0: int, y0: int) -> None:
    """Carguero de MarsCorp medio enterrado, a media distancia (silueta con detalle)."""
    hull, hull_l, hull_d = hx("6c5a66"), hx("8a7884"), hx("3e3240")
    # casco alargado inclinado
    for i in range(70):
        top = y0 + int(i * 0.18) - int(6 * math.sin(i / 70 * math.pi))
        bot = y0 + 18 + int(i * 0.1)
        for y in range(top, bot):
            c = hull_l if y == top else (hull_d if y > bot - 4 else hull)
            if (i % 11 == 0) and y > top + 2:
                c = hull_d
            cv.put(x0 + i, y, c)
    # cabina rota con ventanillas apagadas
    cv.rect(x0 + 60, y0 + 2, x0 + 74, y0 + 14, hull)
    cv.hline(x0 + 60, x0 + 74, y0 + 2, hull_l)
    for wx in range(x0 + 62, x0 + 73, 4):
        cv.rect(wx, y0 + 5, wx + 1, y0 + 7, hx("1e1a28"))
    # aleta de cola
    for i in range(12):
        cv.vline(x0 + 2 + i // 2, y0 - 10 + i, y0 + 2, hull_d if i % 3 else hull)
    # franja de neón de la empresa (rota, algunos tramos encendidos)
    for i in range(6, 58):
        if (i // 5) % 3 != 2:
            cv.put(x0 + i, y0 + 8 + int(i * 0.16), shade(NEON_PINK, 0.95 if (i // 5) % 2 else 0.7))
    # costillas expuestas y cables
    for rx in range(x0 + 20, x0 + 44, 5):
        cv.vline(rx, y0 + 1, y0 + 6, hx("2a2230"))
    line(cv, x0 + 30, y0 + 17, x0 + 38, y0 + 25, hx("2a2230"))
    line(cv, x0 + 33, y0 + 17, x0 + 44, y0 + 24, NEON_CYAN)
    # luz de baliza aún viva
    cv.disc(x0 + 72, y0 + 1, 1.2, NEON_GOLD)


def mars_canyon_layers() -> dict:
    rng = random.Random(1201)
    horizon = 132
    sky_img = sky(hx("120914"), hx("4a2238"), hx("b8705a"), horizon, 77, hx("7fa4d8"), 96, 120)
    scv = canvas_of(sky_img)
    moon_body(scv, 330, 34, 7, 5, hx("d8ccbc"), 5)        # Fobos
    moon_body(scv, 120, 22, 2.5, 2.2, hx("bcb0a0"), 9)    # Deimos
    far = Image.new("RGBA", (W, H), CLEAR)
    ridge_layer(far, rng, 92, 12, hx("6a3a4a"), hx("8a5060"), [(60, 1.0), (17, 0.4)], mesa=True)
    haze(far, 80, 130, hx("b8705a"), 0.5)
    ridge_layer(far, rng, 106, 16, hx("7a3426"), hx("b85a3c"), [(48, 1.0), (13, 0.35), (5, 0.12)],
                strata=hx("5e2a22"), gullies=True)
    fcv = canvas_of(far)
    wreck_marscorp(fcv, 300, 112)
    # torre de comunicaciones caída a la izquierda
    line(fcv, 28, 128, 58, 98, hx("3e3240"), 2)
    for i in range(0, 30, 5):
        line(fcv, 28 + i, 128 - i, 32 + i, 126 - i, hx("5a4a58"))
    fcv.disc(58, 98, 1.2, NEON_CYAN)

    gnd = ground(hx("b0603c"), hx("6e2a1c"), hx("d98a52"), horizon, 88)
    gcv = canvas_of(gnd)
    # zonas de combate: sombras suaves donde se plantan grupo y enemigos
    shadow_band(gnd, 118, 192, 70, 18, hx("4a1c18"), 0.25)
    shadow_band(gnd, 322, 190, 80, 20, hx("4a1c18"), 0.25)
    pebble_field(gcv, rng, horizon + 2, H, hx("a4462a"), 520, avoid=(70, 160, 380, 215))
    for _ in range(10):
        crack(gcv, rng, rng.randrange(W), rng.randrange(150, 236), rng.randrange(8, 22), hx("4a1c18"), hx("d98a52"))
    for (x, y, rx, ry, s) in ((14, 150, 12, 7, 1), (196, 140, 6, 3, 2), (402, 156, 14, 8, 3), (240, 226, 9, 5, 4),
                              (40, 214, 7, 4, 5), (262, 146, 4, 2, 6), (160, 230, 5, 3, 7), (378, 228, 8, 4, 8)):
        rock(gcv, x, y, rx, ry, hx("94402a"), s, cast=hx("5a2018", 200))
    # placa de chatarra con un led cian (cyberpunk sutil)
    gcv.rect(210, 204, 224, 208, hx("4a4e5a"))
    gcv.hline(210, 224, 204, hx("727888"))
    gcv.put(221, 206, NEON_CYAN)
    gcv.put(213, 206, hx("2c2f38"))
    # huellas del carguero (surcos) hacia el fondo
    for i in range(40):
        y = 138 + i
        x = 300 - i * 2
        gcv.put(x, y, hx("7a3020"))
        gcv.put(x + 6, y, hx("7a3020"))

    fg = Image.new("RGBA", (W, H), CLEAR)
    fcg = canvas_of(fg)
    dark = hx("2a1016")
    for (x, y, rx, ry) in ((-6, 236, 40, 22), (30, 242, 22, 12), (430, 232, 46, 26), (396, 244, 26, 12)):
        fcg.ellipse(x, y, rx, ry, dark)
    for x in range(W):  # borde de luz del ocaso en las rocas de primer plano
        for y in range(H):
            if fg.getpixel((x, y))[3] and (y == 0 or fg.getpixel((x, y - 1))[3] == 0):
                fg.putpixel((x, y), hx("6a2a28"))
    line(fcg, 0, 200, 22, 214, hx("1a0c12"), 2)   # cable colgante
    line(fcg, 22, 214, 46, 240, hx("1a0c12"), 2)
    return {"sky": sky_img, "far": far, "ground": gnd, "fg": fg}


def meteorite(cv: Canvas, cx: int, cy: int, rx: int, ry: int) -> None:
    """Meteorito metálico (hierro-níquel): regmaglyptos y reflejos fríos."""
    rng = random.Random(55)
    base = hx("5a5c66")
    pits = [(rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.2), rng.uniform(0.12, 0.22)) for _ in range(9)]
    for y in range(cy - ry - 2, cy + ry + 2):
        for x in range(cx - rx - 2, cx + rx + 2):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            k = 1.0 + 0.08 * math.sin(math.atan2(dy, dx) * 5)
            if math.hypot(dx, dy) <= k and dy < 0.6:
                lit = -dx * 0.5 - dy * 0.85
                f = 0.6 + 0.5 * max(-0.3, min(1.0, lit))
                for px_, py_, pr in pits:
                    if math.hypot(dx - px_, dy - py_) < pr:
                        f *= 0.72
                c = shade(base, f)
                if lit > 0.75 and dith(x, y) < 0.12:
                    c = hx("a8b4c4")
                cv.put(x, y, c)
    for i in range(-rx // 2, rx // 3, 5):  # brillo frío en el filo superior
        cv.put(cx + i, cy - ry + 2 + abs(i) // 5, hx("d0dce8"))


def dish(cv: Canvas, x: int, y: int) -> None:
    """Antena parabólica abandonada, inclinada."""
    for i in range(12):
        cv.hline(x - 6 + i // 2, x + 6 - i // 3, y - 12 + i, hx("8a8e9a") if i < 10 else hx("5a5e6a"))
    cv.put(x - 6, y - 12, hx("c9ced8"))
    line(cv, x, y - 6, x + 6, y - 14, hx("3a3e4a"))
    cv.disc(x + 6, y - 14, 1, NEON_GOLD)
    cv.vline(x, y - 1, y + 10, hx("3a3e4a"))
    cv.vline(x + 1, y - 1, y + 10, hx("2a2e38"))


def mars_crater_layers() -> dict:
    rng = random.Random(3301)
    horizon = 128
    sky_img = sky(hx("0a0814"), hx("2a1838"), hx("8a4a52"), horizon, 91, hx("4a7ab0"), 330, 190)
    scv = canvas_of(sky_img)
    moon_body(scv, 64, 38, 6, 4.5, hx("d0c4b4"), 13)  # Fobos
    # la Tierra vista desde Marte: un lucero azul con su Luna
    scv.disc(352, 30, 1.4, hx("8ac8ff"))
    scv.put(352, 30, hx("ffffff"))
    scv.put(355, 29, hx("c8c8c8"))
    far = Image.new("RGBA", (W, H), CLEAR)
    ridge_layer(far, rng, 104, 10, hx("4e2c40"), hx("6e4256"), [(70, 1.0), (19, 0.3)])
    haze(far, 90, 126, hx("8a4a52"), 0.55)
    fcv = canvas_of(far)
    # borde del cráter: arco elevado con eyecta
    for x in range(W):
        rim = 112 - int(22 * math.exp(-((x - 214) / 150.0) ** 2)) + int(3 * math.sin(x / 9.0))
        for y in range(rim, H):
            d = y - rim
            c = hx("8a3c2c") if d > 1 else hx("c86a48")
            if (y + x // 6) % 8 == 0:
                c = hx("6a2c22")
            if d > 10 and dith(x, y) < 0.12:
                c = hx("a24a32")
            fcv.put(x, y, c)
    meteorite(fcv, 300, 118, 26, 16)
    for i in range(8):  # vapor/humo frío
        fcv.put(300 - 10 + i * 3, 98 - (i % 3), hx("c8b8c8", 120))
    dish(fcv, 70, 116)
    # sonda de aterrizaje vieja
    fcv.rect(132, 106, 146, 112, hx("8a8e9a"))
    fcv.hline(132, 146, 106, hx("c9ced8"))
    for lx in (130, 148):
        line(fcv, lx + (2 if lx < 140 else -2), 112, lx, 120, hx("3a3e4a"))
    fcv.rect(136, 100, 142, 105, hx("c48a30"))   # lámina dorada
    fcv.put(139, 99, NEON_GREEN)
    # baliza antihumanista que vigila la roca
    fcv.vline(254, 92, 114, hx("2c2f38"))
    fcv.disc(254, 91, 1.4, AH_RED)

    gnd = ground(hx("8a4232"), hx("3e1c20"), hx("b05a3c"), horizon + 4, 97)
    gcv = canvas_of(gnd)
    shadow_band(gnd, 118, 192, 70, 18, hx("200c14"), 0.3)
    shadow_band(gnd, 322, 188, 80, 20, hx("200c14"), 0.3)
    # anillos concéntricos del fondo del cráter
    for r in (150, 190, 236):
        for a in range(0, 3600, 3):
            t = math.radians(a / 10)
            x = int(214 + math.cos(t) * r)
            y = int(250 + math.sin(t) * r * 0.32)
            if 0 <= x < W and horizon + 6 < y < H and dith(x, y) < 0.6:
                gcv.put(x, y, hx("5a2a28"))
    pebble_field(gcv, rng, horizon + 6, H, hx("7a3a2c"), 460, avoid=(70, 160, 380, 215))
    # fragmentos metálicos que brillan (parientes del meteorito)
    for _ in range(18):
        x, y = rng.randrange(W), rng.randrange(150, 236)
        gcv.put(x, y, hx("a8b0bc"))
        gcv.put(x + 1, y, hx("5a5c66"))
    for (x, y, rx, ry, s) in ((22, 158, 13, 7, 21), (408, 150, 12, 7, 22), (200, 232, 10, 5, 23), (52, 226, 6, 3, 24),
                              (372, 230, 9, 4, 25)):
        rock(gcv, x, y, rx, ry, hx("6a3028"), s, cast=hx("2a1018", 200))
    fg = Image.new("RGBA", (W, H), CLEAR)
    fcg = canvas_of(fg)
    for (x, y, rx, ry) in ((-10, 238, 44, 20), (436, 236, 44, 24)):
        fcg.ellipse(x, y, rx, ry, hx("180a12"))
    for x in range(W):
        for y in range(H):
            if fg.getpixel((x, y))[3] and (y == 0 or fg.getpixel((x, y - 1))[3] == 0):
                fg.putpixel((x, y), hx("3e1a24"))
    dish_small = Canvas(16, 30)
    dish(dish_small, 8, 18)
    fg.alpha_composite(dish_small.img, (402, 196))
    return {"sky": sky_img, "far": far, "ground": gnd, "fg": fg}


def flatten(layers: dict) -> Image.Image:
    img = layers["sky"].copy()
    for k in ("far", "ground", "fg"):
        img.alpha_composite(layers[k])
    return img


# ================================================================ personajes

ANDRES = CHARACTERS["andres"]
WRENCH = hx("8a91a3")
WRENCH_L = hx("c9ced8")


def _limb(cv: Canvas, a: tuple, b: tuple, c: tuple, w: int = 3) -> None:
    line(cv, a[0], a[1], b[0], b[1], c, w)


def andres_pose(p: dict) -> Image.Image:
    """Andrés de combate (40×48, mira a la derecha). p: desplazamientos y posiciones de manos/pies.

    Claves: bx, by (cuerpo), lean (inclinación de cabeza), ff/bf (pies delante/detrás),
    fh/bh (manos delante/detrás), wrench (ángulo en grados o None), glow (traje), sit, blink.
    """
    cv = Canvas(40, 48)
    s, cl, ac = ANDRES["skin"], ANDRES["cloth"], ANDRES["accent"]
    pants, boots, hair, pack = ANDRES["pants"], ANDRES["boots"], ANDRES["hair"], ANDRES["pack"]
    bx, by = p.get("bx", 0), p.get("by", 0)
    hip = (19 + bx, 32 + by)
    sh_f = (22 + bx, 23 + by)      # hombro delantero
    sh_b = (17 + bx, 23 + by)
    ff, bf = p.get("ff", (23, 45)), p.get("bf", (15, 45))
    fh, bh = p.get("fh", (25, 31)), p.get("bh", (14, 30))
    sit = p.get("sit", False)

    # brazo trasero y pierna trasera (más oscuros)
    _limb(cv, sh_b, (bh[0] + bx, bh[1] + by), shade(cl, 0.62))
    cv.disc(bh[0] + bx, bh[1] + by, 1.3, shade(s, 0.8))
    if sit:
        _limb(cv, (hip[0] - 2, hip[1] + 2), (hip[0] + 6, hip[1] + 4), shade(pants, 0.7))
        _limb(cv, (hip[0] + 6, hip[1] + 4), (hip[0] + 7, 45), shade(pants, 0.7))
        cv.rect(hip[0] + 6, 44, hip[0] + 10, 45, shade(boots, 0.8))
    else:
        knee_b = ((hip[0] - 1 + bf[0]) / 2 - 1, (hip[1] + bf[1]) / 2)
        _limb(cv, (hip[0] - 1, hip[1]), knee_b, shade(pants, 0.7))
        _limb(cv, knee_b, (bf[0], bf[1] - 2), shade(pants, 0.7))
        cv.rect(bf[0] - 2, bf[1] - 2, bf[0] + 2, bf[1], shade(boots, 0.8))
    # mochila (la Semilla va a cuestas)
    cv.rect(10 + bx, 21 + by, 15 + bx, 31 + by, pack)
    cv.vline(10 + bx, 21 + by, 31 + by, shade(pack, 0.7))
    cv.hline(10 + bx, 15 + bx, 31 + by, shade(pack, 0.6))
    cv.rect(11 + bx, 24 + by, 13 + bx, 26 + by, shade(pack, 1.15))
    cv.put(12 + bx, 25 + by, NEON_GREEN)          # brote dentro de la cápsula
    # torso (chaqueta con franja cian)
    cv.rect(15 + bx, 21 + by, 24 + bx, 33 + by, cl)
    cv.vline(15 + bx, 21 + by, 33 + by, shade(cl, 0.82))
    cv.vline(24 + bx, 22 + by, 33 + by, shade(cl, 0.9))
    cv.hline(15 + bx, 24 + bx, 33 + by, shade(cl, 0.7))
    cv.vline(21 + bx, 21 + by, 33 + by, ac)
    cv.hline(16 + bx, 23 + bx, 29 + by, shade(cl, 0.75))  # cinturón
    cv.put(19 + bx, 29 + by, NEON_GOLD)
    glow = p.get("glow", 0)
    if glow:
        for (x, y) in ((17, 24), (23, 26), (16, 31), (22, 32)):
            cv.put(x + bx, y + by, NEON_CYAN if glow > 1 else shade(NEON_CYAN, 0.8))
    # pierna delantera
    if sit:
        _limb(cv, (hip[0] + 1, hip[1] + 2), (hip[0] + 10, hip[1] + 6), pants)
        _limb(cv, (hip[0] + 10, hip[1] + 6), (hip[0] + 11, 45), pants)
        cv.rect(hip[0] + 10, 44, hip[0] + 14, 45, boots)
    else:
        knee_f = ((hip[0] + 2 + ff[0]) / 2 + 1, (hip[1] + ff[1]) / 2)
        _limb(cv, (hip[0] + 2, hip[1]), knee_f, pants)
        _limb(cv, knee_f, (ff[0], ff[1] - 2), pants)
        cv.rect(ff[0] - 2, ff[1] - 2, ff[0] + 3, ff[1], boots)
        cv.put(ff[0] + 3, ff[1] - 2, shade(boots, 1.4))
    # cabeza (14×13) — mira a la derecha
    hx0, hy0 = 13 + bx + p.get("lean", 0), 7 + by + p.get("head_dy", 0)
    cv.rect(hx0 + 1, hy0 + 2, hx0 + 13, hy0 + 13, s)
    cv.rect(hx0 + 2, hy0 + 1, hx0 + 12, hy0 + 14, s)
    cv.vline(hx0 + 1, hy0 + 4, hy0 + 12, shade(s, 0.85))
    # pelo corto, flequillo hacia delante
    cv.rect(hx0 + 1, hy0, hx0 + 12, hy0 + 3, hair)
    cv.rect(hx0, hy0 + 2, hx0 + 6, hy0 + 9, hair)
    cv.rect(hx0 + 7, hy0 + 3, hx0 + 13, hy0 + 4, hair)
    cv.put(hx0 + 13, hy0 + 5, hair)
    cv.hline(hx0 + 2, hx0 + 10, hy0, shade(hair, 1.3))
    cv.rect(hx0, hy0 + 6, hx0 + 3, hy0 + 9, shade(hair, 0.8))
    cv.put(hx0 + 6, hy0 + 8, shade(s, 0.8))       # oreja
    cv.put(hx0 + 5, hy0 + 8, shade(s, 0.7))
    # ojo y cara
    if p.get("blink"):
        cv.hline(hx0 + 10, hx0 + 11, hy0 + 8, OUTLINE)
    elif p.get("tired"):
        cv.hline(hx0 + 10, hx0 + 11, hy0 + 8, OUTLINE)
        cv.put(hx0 + 11, hy0 + 7, OUTLINE)
    else:
        cv.rect(hx0 + 10, hy0 + 7, hx0 + 11, hy0 + 8, OUTLINE)
        cv.put(hx0 + 11, hy0 + 7, hx("ffffff"))
    cv.hline(hx0 + 9, hx0 + 12, hy0 + 5, shade(hair, 0.9))  # ceja
    cv.put(hx0 + 13, hy0 + 9, shade(s, 0.85))     # nariz
    if p.get("shout"):
        cv.rect(hx0 + 11, hy0 + 11, hx0 + 12, hy0 + 12, hx("7a2a30"))
    elif p.get("smile"):
        cv.hline(hx0 + 10, hx0 + 12, hy0 + 11, hx("7a2a30"))
        cv.put(hx0 + 12, hy0 + 10, hx("7a2a30"))
    else:
        cv.hline(hx0 + 11, hx0 + 12, hy0 + 11, shade(s, 0.65))
    cv.put(hx0 + 9, hy0 + 10, hx("e88a7a"))       # mejilla
    # brazo delantero y la llave magnética
    hand = (fh[0] + bx, fh[1] + by)
    elbow = ((sh_f[0] + hand[0]) / 2 + p.get("elbow_dx", 0), (sh_f[1] + hand[1]) / 2 + p.get("elbow_dy", 1))
    _limb(cv, sh_f, elbow, shade(cl, 0.9))
    _limb(cv, elbow, hand, shade(cl, 0.9))
    cv.put(int(elbow[0]), int(elbow[1]) - 1, ac)
    ang = p.get("wrench")
    if ang is not None:
        a = math.radians(ang)
        tip = (hand[0] + math.cos(a) * 11, hand[1] - math.sin(a) * 11)
        line(cv, hand[0], hand[1], tip[0], tip[1], WRENCH, 2)
        line(cv, hand[0] + 0.5, hand[1] - 0.5, tip[0] + 0.5, tip[1] - 0.5, WRENCH_L, 1)
        # cabeza de la llave: imán en «U» con puntas cian
        n = (math.cos(a + math.pi / 2), -math.sin(a + math.pi / 2))
        line(cv, tip[0] - n[0] * 2.5, tip[1] - n[1] * 2.5, tip[0] + n[0] * 2.5, tip[1] + n[1] * 2.5, hx("c8202a"), 1)
        for k in (-2.5, 2.5):
            px_, py_ = tip[0] + n[0] * k, tip[1] + n[1] * k
            line(cv, px_, py_, px_ + math.cos(a) * 3, py_ - math.sin(a) * 3, hx("c8202a"), 1)
            cv.put(int(round(px_ + math.cos(a) * 4)), int(round(py_ - math.sin(a) * 4)), hx("e8eef5"))
        if p.get("spark"):
            for i in range(6):
                t = math.radians(i * 60 + 15)
                cv.put(int(tip[0] + math.cos(t) * 5 + math.cos(a) * 3), int(tip[1] - math.sin(t) * 5 - math.sin(a) * 3),
                       NEON_CYAN if i % 2 else hx("ffffff"))
    cv.disc(hand[0], hand[1], 1.6, s)
    if p.get("mirror"):
        mx, my = hand[0] + 3, hand[1] - 3
        cv.rect(mx - 1, my - 3, mx + 2, my + 2, hx("bfe8ff"))
        cv.vline(mx + 2, my - 3, my + 2, hx("6a8aa8"))
        cv.put(mx, my - 2, hx("ffffff"))
        if p.get("mirror") > 1:
            for i in range(1, 5):
                cv.put(mx + 2 + i, my - i, NEON_GOLD)
                cv.put(mx + 3 + i, my, hx("ffd98a"))
                cv.put(mx + 2 + i, my + i, NEON_GOLD)
    return add_outline(cv.img)


def andres_sheet() -> tuple[Image.Image, dict]:
    rows = []
    # idle: respira (cuerpo sube 1 px, la llave baja)
    rows.append([andres_pose({"by": dy, "wrench": -55, "fh": (26, 31), "blink": i == 3})
                 for i, dy in enumerate((0, 0, 1, 1))])
    # run
    run = []
    for i in range(4):
        cyc = [(28, 44, 12, 42), (24, 45, 16, 45), (12, 42, 28, 44), (16, 45, 24, 45)][i]
        run.append(andres_pose({"bx": 1, "by": -1 if i % 2 == 0 else 0, "lean": 1, "ff": (cyc[0], cyc[1]),
                                "bf": (cyc[2], cyc[3]), "fh": (27 - i % 2 * 4, 29), "bh": (13 + i % 2 * 4, 29),
                                "wrench": 35}))
    rows.append(run)
    # attack: preparación → golpe → seguimiento → recuperación
    rows.append([
        andres_pose({"bx": -2, "by": 1, "ff": (24, 45), "bf": (12, 45), "fh": (16, 18), "elbow_dx": -3,
                     "wrench": 120, "lean": -1, "shout": True}),
        andres_pose({"bx": 2, "ff": (30, 45), "bf": (13, 45), "fh": (28, 25), "wrench": 35, "lean": 2,
                     "shout": True, "spark": True}),
        andres_pose({"bx": 2, "by": 1, "ff": (30, 45), "bf": (13, 45), "fh": (28, 33), "wrench": -50, "lean": 2}),
        andres_pose({"bx": 1, "ff": (26, 45), "bf": (14, 45), "fh": (26, 31), "wrench": -30}),
    ])
    # cast: activa el espejo del traje
    rows.append([
        andres_pose({"by": 1, "fh": (24, 26), "wrench": None, "glow": 1, "mirror": 1}),
        andres_pose({"fh": (27, 20), "wrench": None, "glow": 2, "mirror": 1, "lean": 1}),
        andres_pose({"fh": (28, 18), "wrench": None, "glow": 2, "mirror": 2, "lean": 1, "shout": True}),
    ])
    # hurt: retrocede
    rows.append([
        andres_pose({"bx": -2, "lean": -2, "head_dy": 1, "fh": (23, 33), "wrench": -70, "blink": True,
                     "ff": (22, 45), "bf": (13, 45)}),
        andres_pose({"bx": -1, "lean": -1, "fh": (24, 32), "wrench": -62, "ff": (23, 45), "bf": (14, 45)}),
    ])
    # block: brazos en guardia, llave cruzada
    rows.append([andres_pose({"bx": -1, "by": 1, "ff": (25, 45), "bf": (12, 45), "fh": (26, 22), "bh": (24, 24),
                              "wrench": 95, "lean": -1})])
    # ko: sentado, agotado
    rows.append([andres_pose({"sit": True, "by": 8, "fh": (26, 28), "bh": (16, 30), "wrench": -82, "tired": True,
                              "head_dy": 1, "lean": 1})])
    # victory: levanta la llave
    rows.append([
        andres_pose({"fh": (25, 24), "wrench": 75, "smile": True}),
        andres_pose({"by": -2, "fh": (24, 14), "wrench": 90, "smile": True, "ff": (23, 43), "bf": (15, 43),
                     "spark": True}),
        andres_pose({"by": -1, "fh": (24, 15), "wrench": 90, "smile": True}),
    ])
    names = [("idle", 6, True), ("run", 10, True), ("attack", 12, False), ("cast", 8, False),
             ("hurt", 8, False), ("block", 1, False), ("ko", 1, False), ("victory", 6, True)]
    return pack_sheet(rows, (40, 48), names)


def hal_pose(f: dict) -> Image.Image:
    """HAL de combate (32×40, flota y mira a la derecha). f: dy, glow, tilt, off, beam, flash, shield."""
    cv = Canvas(32, 40)
    dy, off = f.get("dy", 0), f.get("off", False)
    silver = shade(HAL_SILVER, 0.7) if off else HAL_SILVER
    silver_d = shade(HAL_SILVER_D, 0.7) if off else HAL_SILVER_D
    x0, y0 = 7 + f.get("dx", 0), 3 + dy
    # cuerpo con perspectiva: lateral trasero visible
    cv.rect(x0 - 2, y0 + 2, x0, y0 + 26, silver_d)
    cv.rect(x0, y0, x0 + 15, y0 + 27, silver)
    cv.hline(x0, x0 + 15, y0, shade(silver, 1.12))
    cv.vline(x0 + 15, y0 + 1, y0 + 27, silver_d)
    cv.hline(x0, x0 + 15, y0 + 27, silver_d)
    for (x, y) in ((x0 + 1, y0 + 1), (x0 + 14, y0 + 1), (x0 + 1, y0 + 26), (x0 + 14, y0 + 26)):
        cv.put(x, y, shade(silver, 0.8))  # tornillos
    cv.rect(x0 + 2, y0 + 5, x0 + 13, y0 + 24, HAL_FACE)
    cv.hline(x0 + 3, x0 + 12, y0 + 2, shade(NEON_CYAN, 0.5) if off else NEON_CYAN)   # placa del nombre
    cv.hline(x0 + 3, x0 + 12, y0 + 3, shade(NEON_CYAN, 0.3) if off else shade(NEON_CYAN, 0.6))
    if off:
        cv.disc(x0 + 8, y0 + 12, 4.6, hx("3a3e4a"))
        cv.disc(x0 + 8, y0 + 12, 3, hx("22262e"))
        cv.put(x0 + 6, y0 + 10, hx("6a6e7a"))
    else:
        _lens(cv, x0 + 8, y0 + 12, 4.8, f.get("glow", 0.8))
    for x in range(x0 + 4, x0 + 13, 2):  # rejilla
        cv.put(x, y0 + 20, hx("3a4252"))
        cv.put(x, y0 + 22, hx("3a4252"))
    # propulsor
    if not off:
        fl = f.get("flame", 0)
        cv.rect(x0 + 6, y0 + 28, x0 + 10, y0 + 29, silver_d)
        cv.put(x0 + 7, y0 + 30 + fl % 2, NEON_CYAN)
        cv.put(x0 + 9, y0 + 30 + (fl + 1) % 2, NEON_CYAN)
        cv.put(x0 + 8, y0 + 31 + fl % 2, with_alpha(NEON_CYAN, 140))
    img = add_outline(cv.img)
    cv = canvas_of(img)
    if f.get("beam"):
        n = f["beam"]
        cx, cy = x0 + 13, y0 + 12
        for i in range(n * 4):
            cv.put(cx + i, cy, hx("ffffff"))
            cv.put(cx + i, cy - 1, hx("ff6a4a"))
            cv.put(cx + i, cy + 1, hx("ff6a4a"))
        cv.disc(cx + 1, cy, 2.2 if n > 1 else 1.4, hx("ffd0a0"))
    if f.get("flash"):
        r = f["flash"]
        for a in range(0, 360, 30):
            t = math.radians(a)
            cv.put(int(x0 + 8 + math.cos(t) * (5 + r * 2)), int(y0 + 12 + math.sin(t) * (5 + r * 2)),
                   NEON_GOLD if a % 60 else NEON_CYAN)
    if f.get("shield"):
        for y in range(y0 - 1, y0 + 30):
            cv.put(x0 + 19, y, with_alpha(NEON_CYAN, 200 if y % 3 else 90))
        cv.vline(x0 + 20, y0 + 4, y0 + 24, with_alpha(NEON_CYAN, 110))
    if f.get("spark"):
        for (x, y) in ((x0 - 2, y0 + 4), (x0 + 17, y0 + 8), (x0 + 3, y0 - 1)):
            cv.put(x, y, NEON_GOLD)
    return img


def hal_sheet_battle() -> tuple[Image.Image, dict]:
    rows = [
        [hal_pose({"dy": d, "glow": g, "flame": i}) for i, (d, g) in enumerate(((0, 0.6), (1, 0.8), (2, 1.0), (1, 0.8)))],
        [hal_pose({"dy": 0, "glow": 1.0, "dx": -1}), hal_pose({"dy": 0, "glow": 1.0, "beam": 1}),
         hal_pose({"dy": 0, "glow": 1.0, "beam": 4, "dx": -1})],
        [hal_pose({"dy": 1, "glow": 0.7, "flash": 1}), hal_pose({"dy": 0, "glow": 1.0, "flash": 2}),
         hal_pose({"dy": -1, "glow": 1.0, "flash": 3, "spark": True})],
        [hal_pose({"dy": 1, "dx": -2, "glow": 0.4, "spark": True}), hal_pose({"dy": 1, "dx": -1, "glow": 0.6})],
        [hal_pose({"dy": 0, "glow": 0.9, "shield": True})],
        [hal_pose({"dy": 8, "off": True})],
        [hal_pose({"dy": -2, "glow": 1.0, "flash": 2}), hal_pose({"dy": -3, "glow": 1.0, "flash": 3})],
    ]
    names = [("idle", 6, True), ("attack", 10, False), ("cast", 8, False), ("hurt", 8, False),
             ("block", 1, False), ("ko", 1, False), ("victory", 5, True)]
    return pack_sheet(rows, (32, 40), names)


def big_emblem(cv: Canvas, cx: int, cy: int, color: tuple) -> None:
    """Emblema antihumanista grande: anillo roto (hueco abajo-izquierda) atravesado por una barra."""
    for y in range(cy - 8, cy + 9):
        for x in range(cx - 8, cx + 9):
            r = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            ang = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx)) % 360
            if 5.2 <= r <= 7.0 and not (100 <= ang <= 170):
                cv.put(x, y, color)
    for i in range(-6, 7):
        cv.put(cx + i, cy - i, color)
        cv.put(cx + i + 1, cy - i, color)


def ah7_pose(f: dict) -> Image.Image:
    """Centinela AH-7 (72×80, mira a la izquierda). f: dy, punch (0–3), windup, glow, off, flinch."""
    cv = Canvas(72, 80)
    off = f.get("off", False)
    steel = shade(AH_STEEL, 0.75) if off else AH_STEEL
    light = shade(AH_STEEL_L, 0.75) if off else AH_STEEL_L
    dark = AH_STEEL_D
    eye = hx("3a2a30") if off else AH_RED
    glow = f.get("glow", 0)
    if glow:
        steel = lerp_c(steel, hx("a03040"), 0.18 * glow)
        light = lerp_c(light, hx("ff8080"), 0.22 * glow)
    dy, dx = f.get("dy", 0), f.get("dx", 0)
    slump = 6 if off else 0
    # piernas (pistones) y pies
    for lx in (24, 44):
        cv.rect(lx, 56, lx + 7, 74, dark)
        cv.vline(lx + 1, 57, 73, shade(dark, 1.4))
        cv.rect(lx - 3, 72, lx + 10, 78, steel)
        cv.hline(lx - 3, lx + 10, 72, light)
        cv.hline(lx - 3, lx + 10, 78, shade(steel, 0.7))
        cv.rect(lx + 2, 62, lx + 5, 66, hx("8a7a3a"))   # pistón dorado
    bx, by = dx, dy + slump
    # brazo trasero (derecho, al fondo)
    cv.rect(52 + bx, 26 + by, 62 + bx, 36 + by, shade(light, 0.8))
    cv.rect(55 + bx, 36 + by, 61 + bx, 50 + by, shade(dark, 0.9))
    cv.rect(53 + bx, 50 + by, 64 + bx, 60 + by, shade(steel, 0.8))
    # torso
    cv.rect(18 + bx, 24 + by, 56 + bx, 58 + by, steel)
    cv.rect(18 + bx, 24 + by, 56 + bx, 28 + by, light)
    cv.vline(56 + bx, 24 + by, 58 + by, dark)
    cv.hline(18 + bx, 56 + bx, 58 + by, dark)
    cv.rect(24 + bx, 34 + by, 48 + bx, 52 + by, dark)
    cv.rect(25 + bx, 35 + by, 47 + bx, 51 + by, hx("1c1a24"))
    big_emblem(cv, 36 + bx, 43 + by, shade(AH_RED, 0.45) if off else (hx("ff6a6a") if glow > 1 else AH_RED))
    for (x, y) in ((20, 30), (54, 30), (20, 56), (54, 56)):
        cv.put(x + bx, y + by, light)
    # rejillas laterales de ventilación
    for y in range(36, 52, 3):
        cv.hline(19 + bx, 22 + bx, y + by, shade(dark, 1.2))
        cv.hline(50 + bx, 54 + bx, y + by, shade(dark, 1.2))
    # cabeza
    hy = 8 + by + (2 if f.get("flinch") else 0)
    hxo = 26 + bx + (2 if f.get("flinch") else 0)
    cv.rect(hxo, hy, hxo + 22, hy + 16, steel)
    cv.rect(hxo, hy, hxo + 22, hy + 2, light)
    cv.vline(hxo + 22, hy, hy + 16, dark)
    cv.rect(hxo + 1, hy + 5, hxo + 17, hy + 10, hx("15121e"))
    cv.hline(hxo + 2, hxo + 15, hy + 7, eye)
    cv.hline(hxo + 3, hxo + 12, hy + 8, shade(eye, 0.6))
    if not off:
        cv.rect(hxo + 2, hy + 7, hxo + 4, hy + 7, hx("ff9a9a"))   # el visor mira a la izquierda
    cv.vline(hxo + 11, hy - 6, hy - 1, dark)
    cv.disc(hxo + 11, hy - 7, 1.5, eye)
    cv.rect(hxo + 6, hy + 12, hxo + 16, hy + 14, shade(dark, 1.3))   # rejilla de boca
    for x in range(hxo + 7, hxo + 16, 2):
        cv.put(x, hy + 13, dark)
    # óxido y arañazos
    for (x, y) in ((22, 46), (50, 28), (30, 56), (44, 26), (38, 12)):
        cv.put(x + bx, y + by, hx("8a4a2a"))
        cv.put(x + bx + 1, y + by, hx("6a3a22"))
    # brazo delantero (izquierdo) con puño hidráulico: punch 0 = reposo, 1 atrás, 2 extendido, 3 retorno
    punch = f.get("punch", 0)
    shoulder = (16 + bx, 30 + by)
    if punch == 1:
        fist = (22 + bx, 40 + by)
    elif punch == 2:
        fist = (6 + bx, 40 + by)
    elif punch == 3:
        fist = (6 + bx, 44 + by)
    else:
        fist = (12 + bx, 52 + by + (1 if f.get("breath") else 0))
    cv.rect(shoulder[0] - 6, shoulder[1] - 6, shoulder[0] + 6, shoulder[1] + 5, light)
    cv.hline(shoulder[0] - 6, shoulder[0] + 6, shoulder[1] - 6, shade(light, 1.15))
    line(cv, shoulder[0], shoulder[1] + 4, fist[0] + 2, fist[1] - 4, dark, 5)
    line(cv, shoulder[0] - 1, shoulder[1] + 4, fist[0] + 1, fist[1] - 4, shade(dark, 1.4), 1)
    cv.rect(fist[0] - 5, fist[1] - 5, fist[0] + 6, fist[1] + 5, steel)
    cv.hline(fist[0] - 5, fist[0] + 6, fist[1] - 5, light)
    cv.vline(fist[0] - 5, fist[1] - 4, fist[1] + 5, shade(steel, 0.75))
    for k in (-2, 1, 4):
        cv.hline(fist[0] - 5, fist[0] - 3, fist[1] + k, dark)   # nudillos
    img = add_outline(cv.img)
    cv = canvas_of(img)
    if punch == 2:
        for i in range(5):
            cv.hline(fist[0] + 8, fist[0] + 16 - i * 2, fist[1] - 4 + i * 2, with_alpha(hx("ffffff"), 140))
    if f.get("windup"):
        for (x, y) in ((8, 20), (14, 14), (62, 18), (4, 32)):
            cv.put(x + bx, y + by, NEON_GOLD)
            cv.put(x + bx + 1, y + by, with_alpha(NEON_GOLD, 120))
    if glow:
        for a in range(0, 360, 24 if glow > 1 else 40):
            t = math.radians(a + glow * 12)
            r = 30 + glow * 3
            cv.put(int(37 + bx + math.cos(t) * r), int(40 + by + math.sin(t) * r * 1.1),
                   with_alpha(hx("ff6a6a"), 220) if a % 48 else with_alpha(NEON_GOLD, 220))
    if off:
        for (x, y) in ((44, 6), (47, 3), (50, 1)):
            cv.put(x, y + slump, hx("b8bec8"))   # humito de apagado
    return img


def ah7_sheet() -> tuple[Image.Image, dict]:
    rows = [
        [ah7_pose({"dy": d, "breath": d}) for d in (0, 0, 1, 1)],
        [ah7_pose({"punch": 1, "dx": 3, "windup": True}), ah7_pose({"punch": 1, "dx": 4, "dy": 1, "windup": True})],
        [ah7_pose({"punch": 2, "dx": -2}), ah7_pose({"punch": 2, "dx": -3}), ah7_pose({"punch": 3, "dx": -1})],
        [ah7_pose({"glow": 1, "dy": 1}), ah7_pose({"glow": 2, "dy": 0})],
        [ah7_pose({"dx": 5, "dy": 1, "flinch": True}), ah7_pose({"dx": 2, "flinch": True})],
        [ah7_pose({"off": True})],
    ]
    names = [("idle", 5, True), ("windup", 6, False), ("attack", 12, False), ("charge", 6, True),
             ("hurt", 8, False), ("off", 1, False)]
    return pack_sheet(rows, (72, 80), names)


def drone_pose(f: dict) -> Image.Image:
    """Dron vigía AH-D (40×32, mira a la izquierda). f: dy, rotor (0–3), glow, beam, off, flinch."""
    cv = Canvas(40, 32)
    off = f.get("off", False)
    body = shade(AH_STEEL, 0.75) if off else AH_STEEL
    light = shade(AH_STEEL_L, 0.75) if off else AH_STEEL_L
    glow = f.get("glow", 0)
    if glow:
        body = lerp_c(body, hx("a03040"), 0.2 * glow)
    dy = f.get("dy", 0) + (5 if off else 0)
    dx = f.get("dx", 0)
    cx, cy = 20 + dx, 16 + dy
    # brazos de rotor
    cv.hline(cx - 14, cx - 6, cy - 7, AH_STEEL_D)
    cv.hline(cx + 6, cx + 14, cy - 7, AH_STEEL_D)
    cv.vline(cx - 10, cy - 7, cy - 4, AH_STEEL_D)
    cv.vline(cx + 10, cy - 7, cy - 4, AH_STEEL_D)
    # cuerpo esférico con luz arriba-izquierda
    for y in range(cy - 8, cy + 9):
        for x in range(cx - 9, cx + 10):
            ddx, ddy = (x + 0.5 - cx) / 8.6, (y + 0.5 - cy) / 8.0
            r = math.hypot(ddx, ddy)
            if r <= 1.0:
                lit = -ddx * 0.6 - ddy * 0.8
                f2 = 0.72 + 0.5 * max(-0.4, min(1.0, lit))
                cv.put(x, y, shade(body, f2) if lit < 0.5 else (light if dith(x, y) < 0.7 else shade(body, 1.2)))
    cv.hline(cx - 8, cx + 8, cy + 1, AH_STEEL_D)   # junta ecuatorial
    cv.hline(cx - 6, cx + 6, cy + 7, shade(AH_STEEL_D, 0.8))
    # ojo hacia la izquierda
    ex = cx - 3
    cv.disc(ex, cy - 1, 3.6, hx("15121e"))
    cv.disc(ex, cy - 1, 2.2, hx("3a2a30") if off else AH_RED)
    if not off:
        cv.disc(ex, cy - 1, 1.0, hx("ffb0b0") if glow or f.get("beam") else hx("ff6a6a"))
        cv.put(ex - 1, cy - 3, hx("ffffff"))
    for (ox, oy) in ((4, 3), (5, 3), (6, 3)):   # franja roja del clan
        cv.put(cx + ox, cy + oy, shade(AH_RED, 0.7) if not off else shade(AH_RED, 0.35))
    # antena
    cv.vline(cx + 4, cy - 11, cy - 8, AH_STEEL_D)
    cv.put(cx + 4, cy - 12, hx("3a2a30") if off else AH_RED)
    # patas de aterrizaje
    cv.put(cx - 5, cy + 9, AH_STEEL_D)
    cv.put(cx + 5, cy + 9, AH_STEEL_D)
    img = add_outline(cv.img)
    cv = canvas_of(img)
    # hélices: borrosas al girar (se dibujan tras el contorno para que sean ligeras)
    if not off:
        rot = f.get("rotor", 0)
        for rx in (cx - 10, cx + 10):
            span = (6, 3, 6, 2)[rot]
            col = with_alpha(hx("c9ced8"), (230, 150, 230, 110)[rot])
            cv.hline(rx - span, rx + span, cy - 8, col)
            if rot in (1, 3):
                cv.hline(rx - 5, rx + 5, cy - 9, with_alpha(hx("c9ced8"), 60))
    else:
        cv.hline(cx - 13, cx - 7, cy - 8, hx("8a8e9a"))
        cv.hline(cx + 7, cx + 13, cy - 8, hx("8a8e9a"))
    if f.get("beam"):
        n = f["beam"]
        for i in range(n * 5):
            cv.put(ex - 4 - i, cy - 1, hx("ffffff"))
            cv.put(ex - 4 - i, cy - 2, AH_RED)
            cv.put(ex - 4 - i, cy, AH_RED)
    if f.get("windup"):
        for a in range(0, 360, 30):
            t = math.radians(a)
            cv.put(int(round(ex + math.cos(t) * 5)), int(round(cy - 1 + math.sin(t) * 5)), with_alpha(hx("ff8a8a"), 200))
    if glow:
        for a in range(0, 360, 45):
            t = math.radians(a + glow * 20)
            cv.put(int(cx + math.cos(t) * (12 + glow)), int(cy + math.sin(t) * (10 + glow)), with_alpha(NEON_GOLD, 220))
    return img


def drone_sheet() -> tuple[Image.Image, dict]:
    rows = [
        [drone_pose({"dy": d, "rotor": i}) for i, d in enumerate((0, -1, -1, 0))],
        [drone_pose({"rotor": 0, "dx": 2, "dy": -1, "windup": True}), drone_pose({"rotor": 2, "dx": 3, "dy": -2, "windup": True})],
        [drone_pose({"rotor": 1, "beam": 1, "dx": -1}), drone_pose({"rotor": 3, "beam": 3, "dx": -1}),
         drone_pose({"rotor": 1, "dx": 0})],
        [drone_pose({"rotor": 1, "glow": 1}), drone_pose({"rotor": 3, "glow": 2, "dy": -1})],
        [drone_pose({"rotor": 2, "dx": 3, "dy": -2}), drone_pose({"rotor": 0, "dx": 1})],
        [drone_pose({"off": True})],
    ]
    names = [("idle", 10, True), ("windup", 6, False), ("attack", 12, False), ("charge", 8, True),
             ("hurt", 8, False), ("off", 1, False)]
    return pack_sheet(rows, (40, 32), names)


def pack_sheet(rows: list, frame: tuple, names: list) -> tuple[Image.Image, dict]:
    fw, fh = frame
    cols = max(len(r) for r in rows)
    sheet = Image.new("RGBA", (cols * fw, len(rows) * fh), CLEAR)
    anims = {}
    for r, frames in enumerate(rows):
        for c, img in enumerate(frames):
            sheet.alpha_composite(img, (c * fw, r * fh))
        name, fps, loop = names[r]
        anims[name] = {"row": r, "frames": len(frames), "fps": fps, "loop": loop}
    return sheet, anims


# ================================================================ efectos

def fx_strip(draw, n: int = 5, size: int = 32) -> Image.Image:
    strip = Image.new("RGBA", (n * size, size), CLEAR)
    for i in range(n):
        cv = Canvas(size, size)
        draw(cv, i, n)
        strip.alpha_composite(cv.img, (i * size, 0))
    return strip


def fx_hit(cv: Canvas, i: int, n: int) -> None:
    r = [3, 7, 10, 12, 13][i]
    c = 16
    if i < 3:
        cv.disc(c, c, [3, 4, 2][i], hx("ffffff"))
    for a in range(0, 360, 45):
        t = math.radians(a + 22)
        inner = r * (0.3 if i < 2 else 0.6)
        col = hx("ffffff") if i < 2 else (NEON_GOLD if i < 4 else with_alpha(NEON_GOLD, 120))
        line(cv, c + math.cos(t) * inner, c + math.sin(t) * inner, c + math.cos(t) * r, c + math.sin(t) * r, col)
    if 1 <= i <= 3:
        for a in range(0, 360, 20):
            t = math.radians(a)
            if (a // 20 + i) % 2 == 0:
                cv.put(int(c + math.cos(t) * (r - 2)), int(c + math.sin(t) * (r - 2)), hx("ffd98a"))


def fx_zap(cv: Canvas, i: int, n: int) -> None:
    rng = random.Random(70 + i)
    c = 16
    for k in range(3 if i < 4 else 1):
        x, y = c + rng.randint(-2, 2), 2
        col = hx("ffffff") if k == 0 and i < 3 else (NEON_CYAN if k % 2 == 0 else NEON_GOLD)
        while y < 30:
            nx, ny = x + rng.randint(-4, 4), y + rng.randint(3, 6)
            line(cv, x, y, nx, ny, col)
            if i < 3 and rng.random() < 0.3:
                line(cv, nx, ny, nx + rng.choice([-5, 5]), ny + 3, NEON_CYAN)
            x, y = nx, ny
    if i in (1, 2):
        cv.disc(c, c, 3, with_alpha(NEON_CYAN, 140))
        cv.disc(c, c, 1.5, hx("ffffff"))


def fx_light(cv: Canvas, i: int, n: int) -> None:
    c = 16
    r = [3, 6, 9, 11, 12][i]
    a_core = [255, 255, 200, 120, 60][i]
    if i < 3:
        cv.disc(c, c, r * 0.8, with_alpha(hx("ffd98a"), 150))
        cv.disc(c, c, r * 0.45, hx("ffffff"))
    else:
        for a in range(0, 360, 20):
            t = math.radians(a)
            cv.put(int(c + math.cos(t) * r * 0.7), int(c + math.sin(t) * r * 0.7), with_alpha(hx("ffd98a"), a_core))
    for a in range(0, 360, 30):
        t = math.radians(a)
        ln = r + (4 if a % 60 == 0 else 1)
        line(cv, c + math.cos(t) * r * 0.6, c + math.sin(t) * r * 0.6, c + math.cos(t) * ln, c + math.sin(t) * ln,
             with_alpha(NEON_GOLD, a_core))


def fx_heal(cv: Canvas, i: int, n: int) -> None:
    c = 16
    ring = 4 + i * 2.5
    alpha = [255, 230, 190, 140, 80][i]
    for a in range(0, 360, 15):
        t = math.radians(a)
        cv.put(int(c + math.cos(t) * ring), int(c + 6 + math.sin(t) * ring * 0.35), with_alpha(NEON_GREEN, alpha))
    for k, (ox, oy) in enumerate(((-7, 4), (6, 0), (0, -3), (-3, -8))):
        y = c + oy - i * 3 + k
        if 0 < y < 30:
            col = with_alpha(NEON_GREEN if k % 2 == 0 else NEON_CYAN, alpha)
            cv.hline(c + ox - 1, c + ox + 1, y, col)
            cv.vline(c + ox, y - 1, y + 1, col)


def fx_orb(cv: Canvas, i: int, n: int) -> None:
    c = 6
    r = [3.2, 3.8, 4.2, 3.8][i]
    cv.disc(c, c, r + 1.4, with_alpha(NEON_CYAN, 90))
    cv.disc(c, c, r, NEON_GOLD)
    cv.disc(c, c, r * 0.55, hx("fff4c0"))
    cv.put(c - 1, c - 2, hx("ffffff"))
    for (dx, dy) in ((0, -1), (1, 0), (0, 1), (-1, 0))[i:i + 1]:
        cv.put(c + dx * 6 - (1 if dx > 0 else 0), c + dy * 6 - (1 if dy > 0 else 0), NEON_CYAN)


def shadow_img() -> Image.Image:
    cv = Canvas(32, 8)
    cv.ellipse(16, 4, 15.5, 3.6, (12, 6, 14, 70))
    cv.ellipse(16, 4, 11, 2.6, (12, 6, 14, 110))
    return cv.img


# ================================================================ salida

def save(img: Image.Image, name: str) -> None:
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, name))


def main() -> None:
    manifest = {"sheets": {}, "fx": {}, "backdrops": {}}
    sheets = {
        "andres": (andres_sheet, "andres_battle.png", (20, 46)),
        "hal": (hal_sheet_battle, "hal_battle.png", (16, 39)),
        "ah7": (ah7_sheet, "ah7_battle.png", (37, 78)),
        "drone": (drone_sheet, "drone_battle.png", (20, 31)),
    }
    for key, (fn, fname, feet) in sheets.items():
        img, anims = fn()
        save(img, fname)
        size = {"andres": [40, 48], "hal": [32, 40], "ah7": [72, 80], "drone": [40, 32]}[key]
        manifest["sheets"][key] = {"texture": RES + fname, "frame": size, "feet": list(feet), "anims": anims}

    fx = {"hit": (fx_hit, 5, 32, 18), "zap": (fx_zap, 5, 32, 18), "light": (fx_light, 5, 32, 16),
          "heal": (fx_heal, 5, 32, 12), "orb": (fx_orb, 4, 12, 8)}
    for key, (fn, n, size, fps) in fx.items():
        save(fx_strip(fn, n, size), f"fx_{key}.png")
        manifest["fx"][key] = {"texture": RES + f"fx_{key}.png", "frame": [size, size], "frames": n, "fps": fps}
    save(shadow_img(), "shadow.png")
    manifest["fx"]["shadow"] = {"texture": RES + "shadow.png", "frame": [32, 8], "frames": 1, "fps": 1}

    for bid, fn in (("mars_canyon", mars_canyon_layers), ("mars_crater", mars_crater_layers)):
        layers = fn()
        entry = {}
        for k, img in layers.items():
            save(img, f"{bid}_{k}.png")
            entry[k] = RES + f"{bid}_{k}.png"
        save(flatten(layers), f"{bid}.png")
        entry["flat"] = RES + f"{bid}.png"
        manifest["backdrops"][bid] = entry

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("OK →", OUT)


if __name__ == "__main__":
    main()
