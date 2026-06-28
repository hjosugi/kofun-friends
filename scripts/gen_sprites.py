#!/usr/bin/env python3
"""Pixel-art sprite generator for kofun-friends mascots.

Sprites are authored as ASCII grids + a colour palette (the source of truth),
and emitted as native-resolution RGBA PNGs. Pixel art must be upscaled with
nearest-neighbour, which the converter's `sizes --filter nearest` handles.

Run:  python3 scripts/gen_sprites.py
Out:  assets/kofun/pixel/*.png, assets/dochicken/pixel/*.png
"""
import os
import struct
import tempfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# x10 nearest previews for visual inspection — only when KOFUN_PREVIEW=1.
PREVIEW = os.environ.get("KOFUN_PREVIEW") == "1"
PREVIEW_DIR = os.path.join(tempfile.gettempdir(), "kofun-sprite-preview")

# ---- minimal PNG writer (RGBA, 8-bit) --------------------------------------

def write_png(path, w, h, pixels, scale=1):
    """pixels: list of (r,g,b,a), row-major, length w*h. scale: nearest upscale."""
    W, H = w * scale, h * scale
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        sy = y // scale
        for x in range(W):
            r, g, b, a = pixels[sy * w + (x // scale)]
            raw += bytes((r, g, b, a))

    def chunk(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


def render(grid, palette):
    """grid: list of equal-length strings. palette: char -> (r,g,b,a)."""
    h = len(grid)
    w = len(grid[0])
    px = []
    for row in grid:
        assert len(row) == w, f"ragged row: {row!r} ({len(row)} != {w})"
        for ch in row:
            px.append(palette.get(ch, (0, 0, 0, 0)))
    return w, h, px


def T(rgb):  # opaque helper
    return (rgb[0], rgb[1], rgb[2], 255)


# ===========================================================================
# Kofun-kun — mint-green keyhole-tomb child (前方後円墳の子ども)
# 24x24. Round head/body + flared 前方部 skirt with two little feet.
# ===========================================================================
K = {
    ".": (0, 0, 0, 0),
    "o": T((26, 110, 78)),    # outline
    "d": T((45, 170, 120)),   # shadow
    "g": T((78, 222, 158)),   # main
    "l": T((150, 240, 200)),  # highlight
    "e": T((18, 56, 42)),     # eyes / mouth
    "p": T((120, 235, 180)),  # cheek
}

# Base body (eyes/mouth filled per-variant via markers: 1/2 eyes, m mouth area)
KOFUN_BASE = [
    "........oooooo..........",
    "......oolllllloo........",
    ".....ollllllllldo.......",
    "....ollllgggggggdo......",
    "...olllggggggggggdo.....",
    "...olgggggggggggggdo....",
    "..olggggggggggggggddo...",
    "..olgggg11gggg22ggddo...",
    "..olgggg11gggg22ggddo...",
    "..olggggggggggggggddo...",
    "..olggggggmmmmggggddo...",
    "..olgggggggggggggdddo...",
    "..oolggggggggggggdddo...",
    "...olggggggggggggddo....",
    "...oolgggggggggggddo....",
    "....olggggggggggddo.....",
    "....olgggggggggdddo.....",
    "...olllgggggggggdddo....",
    "..olllgggggggggggdddo...",
    "..oldggggggggggggggdo...",
    "..oodggggddoooddggggdo..",
    "..oodddddoo..oodddddoo..",
    "...oooooo......oooooo...",
    "........................",
]


def kofun(eyes, mouth):
    grid = [row for row in KOFUN_BASE]
    grid = [list(r) for r in grid]
    # eye columns: '1' left eye cells, '2' right eye cells, 'm' mouth cells
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == "1":
                row[x] = eyes.get("L", "g")
            elif ch == "2":
                row[x] = eyes.get("R", "g")
            elif ch == "m":
                row[x] = mouth.get((x, y), "g")
    return ["".join(r) for r in grid]


# eyes: dict L/R char to place in the 2x2 eye region (rows 7-8).
EYES_OPEN = {"L": "e", "R": "e"}
# For mouth we map specific cells (row 10, cols 10..13) -> char
def mouth_cells(pattern):
    # pattern: 4 chars for cols 10,11,12,13 at row 10
    return {(10 + i, 10): c for i, c in enumerate(pattern)}


def kofun_variant(name):
    if name == "idle":
        g = kofun(EYES_OPEN, mouth_cells("geeg"))
    elif name == "blink":
        # closed eyes: only bottom row of the 2x2 has 'e' -> emulate by half
        g = kofun({"L": "g", "R": "g"}, mouth_cells("geeg"))
        g = [list(r) for r in g]
        # draw thin closed-eye lines at row 8
        for x in (8, 9):
            g[8][x] = "e"
        for x in (14, 15):
            g[8][x] = "e"
        g = ["".join(r) for r in g]
    elif name == "smile":
        g = kofun(EYES_OPEN, mouth_cells("geeg"))
        g = [list(r) for r in g]
        # upturned smile + cheeks
        g[10][9] = "g"; g[10][10] = "e"; g[10][13] = "e"; g[10][14] = "g"
        g[9][10] = "g"; g[9][13] = "g"
        g[11][11] = "e"; g[11][12] = "e"
        g[9][6] = "p"; g[9][17] = "p"
        g = ["".join(r) for r in g]
    elif name == "munch":
        g = kofun(EYES_OPEN, mouth_cells("eeee"))
        g = [list(r) for r in g]
        # open mouth block
        for x in range(10, 14):
            g[9][x] = "e"
            g[11][x] = "e"
        g[10][11] = "p"; g[10][12] = "p"
        g = ["".join(r) for r in g]
    else:
        raise ValueError(name)
    return render(g, K)


# ===========================================================================
# Dochicken-san — orange chicken haniwa (鶏の姿をした埴輪)
# 24x24. Red comb, round terracotta body, beak, eye, wing, two legs.
# ===========================================================================
C = {
    ".": (0, 0, 0, 0),
    "o": T((120, 60, 20)),    # outline
    "d": T((205, 110, 28)),   # shadow
    "g": T((242, 150, 45)),   # body main
    "l": T((250, 205, 120)),  # belly / highlight
    "r": T((235, 80, 75)),    # comb
    "R": T((190, 45, 40)),    # comb shadow
    "b": T((250, 140, 0)),    # beak
    "B": T((215, 95, 0)),     # beak shadow
    "e": T((40, 28, 18)),     # eye
    "w": T((250, 215, 140)),  # wing
}

DOCHI_BASE = [
    "............rr..........",
    "..........rrRr..........",
    ".........rRrrRr.........",
    "........oorRRroo........",
    ".......ooggggggoo.......",
    "......oggggggggggo......",
    ".....ogglllllllllgo.....",
    ".....oglll1lll2llgo.....",
    ".....oglll1lll2llgo.....",
    ".....ogllllbbblllgo.....",
    ".....oglllbbBBblllo.....",
    "....oglllllllllllgo.....",
    "....owwlllllllllllgo....",
    "....owwlllllllllllgo....",
    "....oggllllllllllggo....",
    ".....ogggllllllgggo.....",
    ".....ooggggggggggoo.....",
    "......ooggggggggoo......",
    "........oooooooo........",
    ".........bb..bb.........",
    ".........bb..bb.........",
    ".........bb..bb.........",
    ".......bbbb..bbbb.......",
    "........................",
]


def dochi(eye, peck=False):
    grid = [list(r) for r in DOCHI_BASE]
    for row in grid:
        for x, ch in enumerate(row):
            if ch in ("1", "2"):
                row[x] = eye
    g = [list(r) for r in grid]
    if peck:
        # extend beak downward (pecking) + ground mark
        g[11][9] = "b"; g[11][10] = "B"; g[11][11] = "b"
        g[12][10] = "B"
        g[20][3] = "o"; g[21][4] = "o"
    return render(["".join(r) for r in g], C)


def dochi_variant(name):
    if name == "idle":
        return dochi("e")
    if name == "blink":
        grid = [list(r) for r in DOCHI_BASE]
        for row in grid:
            for x, ch in enumerate(row):
                if ch in ("1", "2"):
                    row[x] = "l"
        # short closed-eye lines
        grid[8][9] = "e"; grid[8][10] = "e"
        grid[8][13] = "e"; grid[8][14] = "e"
        return render(["".join(r) for r in grid], C)
    if name == "peck":
        return dochi("e", peck=True)
    raise ValueError(name)


# ===========================================================================
def main():
    jobs = [
        ("kofun/pixel/kofun-kun", ["idle", "blink", "smile", "munch"], kofun_variant),
        ("dochicken/pixel/dochicken-san", ["idle", "blink", "peck"], dochi_variant),
    ]
    previews = []
    for base, variants, fn in jobs:
        for v in variants:
            w, h, px = fn(v)
            out = os.path.join(ROOT, "assets", f"{base}-{v}.png")
            write_png(out, w, h, px)
            prev = os.path.join(PREVIEW_DIR, f"{os.path.basename(base)}-{v}.png")
            previews.append((prev, w, h, px))
            print("wrote", os.path.relpath(out, ROOT))
    if PREVIEW:
        for prev, w, h, px in previews:
            write_png(prev, w, h, px, scale=10)
        print("previews:", PREVIEW_DIR)


if __name__ == "__main__":
    main()
