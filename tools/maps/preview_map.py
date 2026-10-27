"""Renderiza un mapa JSON de superficie a PNG para revisarlo sin abrir Godot.

Uso:  python3 tools/maps/preview_map.py earth [salida.png]
"""
import json
import os
import sys

from PIL import Image, ImageDraw

GAME = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "game"))
ATLAS = {
    "earth": ("assets/art/tiles/earth_tiles.png", 12),
    "moon": ("assets/art/tiles/moon_tiles.png", 8),
    "mars": ("assets/art/tiles/mars_tiles.png", 8),
    "interior": ("assets/art/tiles/interior_tiles.png", 8),
}
T = 16


def tile_img(atlas, cols, idx):
    x, y = (idx % cols) * T, (idx // cols) * T
    return atlas.crop((x, y, x + T, y + T))


def main(map_id, out):
    data = json.load(open(os.path.join(GAME, "assets/data/maps", map_id + ".json")))
    tileset = data["tileset"]
    if tileset in ATLAS:
        path, cols = ATLAS[tileset]
    else:
        manifest = json.load(open(os.path.join(GAME, "assets/art/tiles", tileset + ".json")))
        path, cols = "assets/art/tiles/%s.png" % tileset, manifest["columns"]
    atlas = Image.open(os.path.join(GAME, path)).convert("RGBA")
    legend = data["legend"]
    h = len(data["ground"])
    w = max(len(r) for r in data["ground"])
    img = Image.new("RGBA", (w * T, h * T), (11, 18, 32, 255))
    for layer in ("ground", "objects"):
        for y, row in enumerate(data[layer]):
            for x, ch in enumerate(row):
                if ch == " " or ch not in legend:
                    continue
                t = legend[ch]["tile"]
                opts = t if isinstance(t, list) else [t]
                idx = opts[abs((x * 73856093) ^ (y * 19349663)) % 9973 % len(opts)]
                tile = tile_img(atlas, cols, idx)
                img.alpha_composite(tile, (x * T, y * T))
    d = ImageDraw.Draw(img)
    for e in sorted(data["entities"], key=lambda e: (e.get("z", 0), e["pos"][1])):
        px = int(e["pos"][0] * T + T / 2)
        py = int((e["pos"][1] + 1) * T)
        sprite = e.get("sprite")
        if e["type"] == "ship":
            sprite_path = os.path.join(GAME, "assets/art/ship/astra.png")
        elif e["type"] == "npc":
            sheet = Image.open(os.path.join(GAME, "assets/art/characters", e["id"] + ".png")).convert("RGBA")
            spr = sheet.crop((0, 0, 16, 24))
            img.alpha_composite(spr, (px - 8, py - 24))
            continue
        elif sprite or e["type"] == "terminal":
            sprite_path = os.path.join(GAME, "assets/art/props", (sprite or "terminal") + ".png")
        else:
            sprite_path = None
        if sprite_path and os.path.exists(sprite_path):
            spr = Image.open(sprite_path).convert("RGBA")
            img.alpha_composite(spr, (px - spr.width // 2, py - spr.height))
        color = {"spawn": (61, 231, 201), "scan": (244, 211, 94), "sign": (200, 200, 255),
                 "door": (255, 62, 165)}.get(e["type"])
        if color:
            d.rectangle([px - 2, py - 2, px + 2, py + 2], outline=color)
    scale = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(out)
    print(out)


if __name__ == "__main__":
    mid = sys.argv[1] if len(sys.argv) > 1 else "earth"
    main(mid, sys.argv[2] if len(sys.argv) > 2 else f"{mid}_preview.png")
