#!/usr/bin/env python3
"""Pixel-art sprite generator for kofun-friends mascots.

The mascots are a faithful, 1:1 port of the originals defined in hjosugi-hub
(`lib/hjosugi_hub/kofun.ex`, `lib/hjosugi_hub/dochicken.ex`). There the artwork
is a 16x16 grid of coloured rectangles that the site scales and animates with
CSS. We reproduce the *exact* same rectangles and palette here so the assets in
this repo stay pixel-identical to the live site ("本家準拠").

  source of truth (16x16 rects) ── this script ──> native-res RGBA PNGs + GIFs

Pixel art must be upscaled with nearest-neighbour, which the converter's
`sizes --filter nearest` (and `resize --filter nearest` for GIFs) handles.

Run:  python3 scripts/gen_sprites.py
Out:  assets/kofun/pixel/*.png, assets/dochicken/pixel/*.png, *.gif
"""
import os
import struct
import tempfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# x10 nearest previews for visual inspection — only when KOFUN_PREVIEW=1.
PREVIEW = os.environ.get("KOFUN_PREVIEW") == "1"
PREVIEW_DIR = os.path.join(tempfile.gettempdir(), "kofun-sprite-preview")

GRID = 16          # the originals are authored on a 16x16 grid
GIF_SCALE = 6      # 16 * 6 = 96px animated GIFs (matches the live assets)
GIF_DELAY_CS = 35  # per-frame delay, centiseconds


# ---- colour helpers --------------------------------------------------------

def hx(s, a=255):
    """'#rrggbb' -> (r, g, b, a)."""
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


TRANSPARENT = (0, 0, 0, 0)


# ---- 16x16 rectangle renderer (mirrors the Elixir <rect> emitters) ---------

def blank():
    return [TRANSPARENT] * (GRID * GRID)


def paint(px, rects, colour):
    """Paint {x, y, w, h} rects (later layers overwrite earlier ones)."""
    for x, y, w, h in rects:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if 0 <= xx < GRID and 0 <= yy < GRID:
                    px[yy * GRID + xx] = colour
    return px


# ---- minimal PNG writer (RGBA, 8-bit) --------------------------------------

def write_png(path, pixels, w=GRID, h=GRID, scale=1):
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


# ---- minimal animated GIF89a writer (indexed, transparent index 0) ---------

def _lzw_encode(indexes, min_code_size):
    """Standard GIF LZW. Returns the packed byte stream (sans block framing)."""
    clear = 1 << min_code_size
    end = clear + 1
    code_size = min_code_size + 1
    table = {}

    def reset():
        nonlocal table, code_size
        table = {(i,): i for i in range(clear)}
        code_size = min_code_size + 1

    out = bytearray()
    buf = 0
    nbits = 0

    def emit(code):
        nonlocal buf, nbits
        buf |= code << nbits
        nbits += code_size
        while nbits >= 8:
            out.append(buf & 0xFF)
            buf >>= 8
            nbits -= 8

    reset()
    emit(clear)
    next_code = end + 1
    cur = (indexes[0],)
    for idx in indexes[1:]:
        nxt = cur + (idx,)
        if nxt in table:
            cur = nxt
        else:
            emit(table[cur])
            table[nxt] = next_code
            next_code += 1
            if next_code > (1 << code_size) and code_size < 12:
                code_size += 1
            if next_code >= 4096:
                emit(clear)
                reset()
                next_code = end + 1
            cur = (idx,)
    emit(table[cur])
    emit(end)
    if nbits > 0:
        out.append(buf & 0xFF)
    return bytes(out)


def write_gif(path, frames, scale=1, delay_cs=GIF_DELAY_CS, w=GRID, h=GRID):
    """frames: list of pixel buffers (each (r,g,b,a) list of len w*h)."""
    # Build a shared palette: index 0 reserved for transparent.
    colours = []
    seen = {}
    for fr in frames:
        for r, g, b, a in fr:
            if a == 0:
                continue
            key = (r, g, b)
            if key not in seen:
                seen[key] = len(colours) + 1  # +1: index 0 is transparent
                colours.append(key)
    size = max(2, (len(colours) + 1 - 1).bit_length())  # bits for table
    table_len = 1 << size
    min_code_size = max(2, size)

    gct = bytearray()
    gct += bytes((0, 0, 0))  # index 0 (transparent placeholder)
    for r, g, b in colours:
        gct += bytes((r, g, b))
    while len(gct) < table_len * 3:
        gct += bytes((0, 0, 0))

    W, H = w * scale, h * scale
    out = bytearray()
    out += b"GIF89a"
    out += struct.pack("<HH", W, H)
    out += bytes((0xF0 | (size - 1), 0, 0))  # GCT flag, colour resolution, bg, aspect
    out += gct
    # NETSCAPE2.0 loop-forever extension
    out += b"\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00"

    for fr in frames:
        idx = bytearray()
        for y in range(H):
            sy = y // scale
            for x in range(W):
                r, g, b, a = fr[sy * w + (x // scale)]
                idx.append(0 if a == 0 else seen[(r, g, b)])
        # Graphic Control Extension: transparent index 0, restore-to-bg.
        out += b"\x21\xf9\x04" + bytes((0x09,)) + struct.pack("<H", delay_cs) + bytes((0, 0))
        out += b"\x2c" + struct.pack("<HHHH", 0, 0, W, H) + bytes((0,))
        out += bytes((min_code_size,))
        data = _lzw_encode(idx, min_code_size)
        for i in range(0, len(data), 255):
            block = data[i:i + 255]
            out += bytes((len(block),)) + block
        out += bytes((0,))  # block terminator
    out += b"\x3b"  # trailer
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(out)


# ===========================================================================
# Kofun-kun — 前方後円墳 (keyhole-tomb) child. Port of HjosugiHub.Kofun.
# Flat body (site uses currentColor = --accent) + dark face. munch adds the
# euglena (midorimushi) blob he is nibbling.
# ===========================================================================
KOFUN_BODY = hx("#71f6bd")   # --accent (the site themes the body with this)
KOFUN_FACE = hx("#0a1c17")
KOFUN_EUGLENA = hx("#7bf0a6")

# {x, y, w} rows, each one pixel tall — copied verbatim from kofun.ex @body.
KOFUN_BODY_RECTS = [
    (6, 0, 4, 1), (5, 1, 6, 1), (4, 2, 8, 1), (3, 3, 10, 1), (3, 4, 10, 1),
    (3, 5, 10, 1), (3, 6, 10, 1), (4, 7, 8, 1), (5, 8, 6, 1), (5, 9, 6, 1),
    (4, 10, 8, 1), (4, 11, 8, 1), (3, 12, 10, 1), (2, 13, 12, 1),
    (2, 14, 12, 1), (4, 15, 3, 1), (9, 15, 3, 1),
]

# @faces from kofun.ex (eyes + mouth as {x, y, w, h}).
KOFUN_FACES = {
    "idle":  [(5, 4, 1, 2), (10, 4, 1, 2), (7, 6, 2, 1)],
    "blink": [(5, 5, 1, 1), (10, 5, 1, 1), (7, 6, 2, 1)],
    "smile": [(5, 4, 1, 2), (10, 4, 1, 2), (6, 6, 1, 1), (7, 7, 2, 1), (9, 6, 1, 1)],
    "munch": [(5, 4, 1, 2), (10, 4, 1, 2), (7, 6, 2, 2)],
}


def kofun_variant(name):
    px = blank()
    paint(px, KOFUN_BODY_RECTS, KOFUN_BODY)
    paint(px, KOFUN_FACES[name], KOFUN_FACE)
    if name == "munch":  # pose_extra(:munch): euglena blob with a flagellum tail
        paint(px, [(1, 6, 2, 2), (0, 8, 1, 1)], KOFUN_EUGLENA)
    return px


# ===========================================================================
# Dochicken-san — chicken-shaped 埴輪 (haniwa). Port of HjosugiHub.Dochicken.
# ===========================================================================
DOCHI_COMB = hx("#ff5470")   # @comb_fill (also @wattle)
DOCHI_BODY = hx("#ff9d42")   # @body_fill
DOCHI_SHADE = hx("#ef6f1f")  # @body_shade (wing)
DOCHI_LEG = hx("#ff8a1f")    # @leg_fill
DOCHI_BEAK = hx("#ffd24a")   # @beak_fill
DOCHI_EYE = hx("#2a1008")    # @eye_fill

DOCHI_COMB_RECTS = [(6, 0, 1, 1), (8, 0, 1, 1), (10, 0, 1, 1), (6, 1, 5, 1)]
DOCHI_BODY_RECTS = [
    (6, 2, 4, 1), (5, 3, 6, 1), (5, 4, 6, 1), (5, 5, 6, 1), (4, 6, 8, 1),
    (3, 7, 10, 1), (3, 8, 10, 1), (3, 9, 10, 1), (3, 10, 10, 1), (3, 11, 10, 1),
    (4, 12, 8, 1), (4, 13, 8, 1),
]
DOCHI_WING = [(4, 9, 3, 1), (4, 10, 2, 1)]
DOCHI_WATTLE = [(7, 7, 2, 1)]
DOCHI_LEGS = [(6, 14, 1, 1), (9, 14, 1, 1), (5, 15, 2, 1), (9, 15, 2, 1)]
DOCHI_EYES = {
    "idle":  [(6, 3, 1, 2), (9, 3, 1, 2)],
    "blink": [(6, 4, 1, 1), (9, 4, 1, 1)],
    "peck":  [(6, 3, 1, 2), (9, 3, 1, 2)],
}
DOCHI_BEAK_RECTS = {
    "idle":  [(7, 5, 2, 2)],
    "blink": [(7, 5, 2, 2)],
    "peck":  [(7, 6, 2, 2)],
}


def dochi_variant(name):
    # z-order from dochicken.ex pose_svg/1: comb, body, wing, legs, beak, wattle, eyes
    px = blank()
    paint(px, DOCHI_COMB_RECTS, DOCHI_COMB)
    paint(px, DOCHI_BODY_RECTS, DOCHI_BODY)
    paint(px, DOCHI_WING, DOCHI_SHADE)
    paint(px, DOCHI_LEGS, DOCHI_LEG)
    paint(px, DOCHI_BEAK_RECTS[name], DOCHI_BEAK)
    paint(px, DOCHI_WATTLE, DOCHI_COMB)
    paint(px, DOCHI_EYES[name], DOCHI_EYE)
    return px


# ===========================================================================
def main():
    jobs = [
        ("kofun/pixel/kofun-kun", ["idle", "blink", "smile", "munch"], kofun_variant),
        ("dochicken/pixel/dochicken-san", ["idle", "blink", "peck"], dochi_variant),
    ]
    rendered = {}
    previews = []
    for base, variants, fn in jobs:
        for v in variants:
            px = fn(v)
            rendered[(base, v)] = px
            out = os.path.join(ROOT, "assets", f"{base}-{v}.png")
            write_png(out, px)
            previews.append((os.path.basename(base) + "-" + v, px))
            print("wrote", os.path.relpath(out, ROOT))

    # Animated GIFs (96x96, looping) — the same poses the site cycles through.
    gifs = [
        ("kofun/gif/kofun-kun.gif",
         [rendered[("kofun/pixel/kofun-kun", p)] for p in ("idle", "blink", "munch")]),
        ("dochicken/gif/dochicken-san.gif",
         [rendered[("dochicken/pixel/dochicken-san", p)] for p in ("idle", "blink", "peck")]),
    ]
    for rel, frames in gifs:
        out = os.path.join(ROOT, "assets", rel)
        write_gif(out, frames, scale=GIF_SCALE)
        print("wrote", os.path.relpath(out, ROOT))

    if PREVIEW:
        for name, px in previews:
            write_png(os.path.join(PREVIEW_DIR, name + ".png"), px, scale=10)
        print("previews:", PREVIEW_DIR)


if __name__ == "__main__":
    main()
