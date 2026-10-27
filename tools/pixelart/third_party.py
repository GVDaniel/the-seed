"""Recortes recoloreados de los packs CC0 de Kenney (Roguelike Modern City y Roguelike Indoors).

Uso:  python3 tools/pixelart/third_party.py   (también lo llama generate.py)
Lee las hojas originales de game/assets/art/third_party/ y guarda props sueltos en
game/assets/art/props/ (prefijos city_ e in_), recoloreados a la paleta del juego:
noche de neón en la Tierra, coches abandonados oxidados, polvo rojo en Marte, gris en la Luna.
Tiles de 16 px con 1 px de separación; los objetos de varios tiles se cosen sin la separación.
"""
from __future__ import annotations

import colorsys
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.normpath(os.path.join(HERE, "..", "..", "game", "assets", "art"))
CITY = os.path.join(ART, "third_party", "kenney_roguelike_modern_city", "roguelikeCity_magenta.png")
INDOOR = os.path.join(ART, "third_party", "kenney_roguelike_indoors", "roguelikeIndoor_transparent.png")

# nombre: (columna, fila, ancho, alto, recoloreado)
CITY_PROPS = {
    "tree_tall": (32, 10, 1, 2, "dead"),
    "tree_pine": (33, 10, 1, 2, "dead"),
    "shrub": (33, 13, 1, 1, "dead"),
    "trash_bags": (12, 13, 1, 1, "night"),
    "trash_bag": (13, 13, 1, 1, "night"),
    "bin": (15, 13, 1, 1, "night"),
    "bucket": (16, 13, 1, 1, "night"),
    "hydrant": (15, 14, 1, 1, "night"),
    "mailbox": (12, 15, 1, 1, "night"),
    "postbox": (12, 16, 1, 1, "night"),
    "box_open": (13, 15, 1, 1, "night"),
    "box": (13, 16, 1, 1, "night"),
    "boxes": (13, 17, 1, 1, "night"),
    "boxes_b": (14, 17, 1, 1, "night"),
    "bench": (17, 15, 2, 1, "night"),
    "cone": (14, 18, 1, 1, "night"),
    "planter": (13, 18, 1, 1, "night"),
    "fruit_crate": (12, 18, 1, 1, "night"),
    "barrier": (24, 5, 1, 1, "night"),
    "barrier_lit": (25, 6, 1, 1, "night"),
    "vending": (24, 8, 1, 1, "night"),
    "atm": (26, 8, 1, 1, "night"),
    "news_box": (28, 7, 1, 1, "night"),
    "news_box_b": (29, 7, 1, 1, "night"),
    "ac_unit": (25, 14, 1, 1, "night"),
    "ac_unit_b": (27, 14, 1, 1, "night"),
    "meter": (19, 13, 1, 1, "night"),
    # versiones polvorientas para Marte y la Luna
    "box_mars": (13, 16, 1, 1, "mars"),
    "boxes_mars": (13, 17, 1, 1, "mars"),
    "barrier_mars": (24, 5, 1, 1, "mars"),
    "barrier_moon": (25, 6, 1, 1, "moon"),
    "cone_moon": (14, 18, 1, 1, "moon"),
    "boxes_moon": (14, 17, 1, 1, "moon"),
}

INDOOR_PROPS = {
    "chair_metal": (0, 8, 1, 1, "keep"),
    "chair_metal_side": (2, 8, 1, 1, "keep"),
    "chair_metal_side_b": (3, 8, 1, 1, "keep"),
    "chair_wood": (0, 2, 1, 1, "keep"),
    "table_round": (7, 0, 1, 1, "keep"),
    "table_small": (4, 3, 1, 1, "keep"),
    "sofa": (4, 7, 4, 1, "keep"),
    "counter_sink": (8, 12, 1, 1, "keep"),
    "counter_juice": (5, 12, 1, 1, "keep"),
    "counter_tea": (6, 12, 1, 1, "keep"),
    "counter_plates": (7, 12, 1, 1, "keep"),
    "counter_drawers": (1, 13, 1, 1, "keep"),
    "stove": (14, 14, 1, 2, "keep"),
    "shelf_bottles": (19, 17, 1, 1, "keep"),
    "shelf_bottles_b": (20, 17, 1, 1, "keep"),
    "shelf_bottles_c": (21, 17, 1, 1, "keep"),
    "painting": (19, 12, 1, 1, "keep"),
    "painting_b": (19, 13, 1, 1, "keep"),
    "map_wall": (20, 12, 2, 1, "keep"),
    "rug_teal": (16, 14, 3, 1, "keep"),
    "rug_orange": (16, 15, 3, 1, "keep"),
    "rug_green": (16, 16, 3, 1, "keep"),
    "mirror": (22, 14, 1, 2, "keep"),
    "plant": (16, 0, 1, 1, "keep"),
    "plant_b": (17, 0, 1, 1, "keep"),
}


def load_sheet(path: str) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][:3] == (255, 0, 255):
                px[x, y] = (0, 0, 0, 0)
    return im


def stitch(sheet: Image.Image, c: int, r: int, w: int, h: int) -> Image.Image:
    out = Image.new("RGBA", (w * 16, h * 16), (0, 0, 0, 0))
    for j in range(h):
        for i in range(w):
            x, y = (c + i) * 17, (r + j) * 17
            out.paste(sheet.crop((x, y, x + 16, y + 16)), (i * 16, j * 16))
    return out


def _mix(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def recolor(img: Image.Image, mode: str, seed: int) -> Image.Image:
    if mode == "keep":
        mode = "indoor"
    rng = random.Random(seed)
    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            deg = h * 360
            if mode == "dead" and 50 <= deg <= 170:
                h, s, v = (30 + (deg - 50) * 0.12) / 360, s * 0.45, v * 0.72
            elif mode == "wreck":
                s *= 0.5
                v *= 0.78
            elif mode == "night":
                s *= 0.82
                v *= 0.9
            elif mode == "indoor":
                s *= 0.9
            nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
            c = (int(nr * 255), int(ng * 255), int(nb * 255))
            if mode == "night":
                c = _mix(c, (70, 80, 130), 0.1)
            elif mode == "wreck":
                c = _mix(c, (60, 55, 80), 0.15)
                if v > 0.25 and rng.random() < 0.09:
                    c = _mix(c, (140, 70, 40), 0.7)
            elif mode == "mars":
                c = _mix(c, (176, 84, 52), 0.38)
            elif mode == "moon":
                grey = int(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])
                c = _mix(c, (grey, grey, min(255, grey + 12)), 0.65)
            px[x, y] = (*c, a)
    return out


def main() -> None:
    out_dir = os.path.join(ART, "props")
    os.makedirs(out_dir, exist_ok=True)
    for prefix, path, table in (("city_", CITY, CITY_PROPS), ("in_", INDOOR, INDOOR_PROPS)):
        sheet = load_sheet(path)
        for i, (name, (c, r, w, h, mode)) in enumerate(table.items()):
            img = recolor(stitch(sheet, c, r, w, h), mode, 500 + i)
            bbox = img.getbbox()
            if bbox is None:
                raise SystemExit(f"third_party: {name} está vacío")
            # recorta el aire de abajo para que el sprite se apoye en el suelo
            img = img.crop((0, 0, img.width, bbox[3]))
            img.save(os.path.join(out_dir, f"{prefix}{name}.png"))
    print("third_party OK")


if __name__ == "__main__":
    main()
