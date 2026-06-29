#!/usr/bin/env python3
"""Pixel-art SVG generator for kofun-friends emoji / icons / cursors.

Everything in this repo shares one look: chunky, neon, cyberpunk dot-art on a
dark background — the same aesthetic as the Kofun-kun / Dochicken-san mascots
(see scripts/gen_sprites.py) and the live hjosugi-hub site (mint --accent
#71f6bd on near-black #07110f).

Each glyph is authored as a 16x16 ASCII grid + a palette. We emit crisp,
rect-based SVGs (shape-rendering="crispEdges", run-length merged per row) so the
art is true pixel art at every size — no curves, no gradients, no anti-aliasing.
The Rust converter rasterises these to PNG / .cur / .ani.

Run:  python3 scripts/gen_pixel_svgs.py
Out:  assets/emoji/svg/*.svg, assets/icons/svg/*.svg, assets/cursors/svg/*.svg
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 16  # grid size

# ---- shared neon palette ---------------------------------------------------
BG = "#07110f"        # site background (used for "hollow" pixels on emoji)
ACCENT = "#71f6bd"    # mint
ACCENT2 = "#7dd3fc"   # cyan
CORAL = "#ff5470"
DANGER = "#ff8a8a"
GOLD = "#f6c177"
ORANGE = "#ff9d42"
ORANGE_D = "#ef6f1f"
VIOLET = "#c792ea"
VIOLET_D = "#9d6bd0"
JADE = "#5eead4"
JADE_D = "#14b8a6"
JADE_L = "#bdf5e9"
STEEL = "#cfe9ff"
STEEL_D = "#7fa8c9"
CREAM = "#f5e9d0"
CREAM_D = "#e8d4a8"
INK = "#0a1c17"       # dark outline / cursor outline
WHITE = "#eafff6"
BROWN = "#c17336"
BROWN_D = "#6d4328"
TAN = "#ffe1a3"
STONE = "#9aa7a0"
STONE_D = "#53625d"


def svg(name, grid, palette, label, viewbox=N, px=128, hotspot=None):
    """Emit a crispEdges SVG. palette: char -> hex (omit '.' = transparent)."""
    assert len(grid) == viewbox, f"{name}: {len(grid)} rows != {viewbox}"
    rects = []
    for y, row in enumerate(grid):
        assert len(row) == viewbox, f"{name} row {y}: len {len(row)} != {viewbox}: {row!r}"
        x = 0
        while x < viewbox:
            ch = row[x]
            if ch == ".":
                x += 1
                continue
            run = 1
            while x + run < viewbox and row[x + run] == ch:
                run += 1
            fill = palette[ch]
            rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="{fill}"/>')
            x += run
    hs = f"\n<!-- hotspot grid {hotspot} -->" if hotspot else ""
    body = "\n  ".join(rects)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!-- {label} — kofun-friends pixel art -->{hs}\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {viewbox} {viewbox}" '
        f'width="{px}" height="{px}" shape-rendering="crispEdges" '
        f'role="img" aria-label="{label}">\n  {body}\n</svg>\n'
    )


# ===========================================================================
# EMOJI (16x16) — small friends with strong, readable silhouettes
# ===========================================================================

# 埴輪 haniwa — hat brim, eye holes, mouth, arms, and hollow legs
HANIWA = [
    "................",
    ".....dddddd.....",
    "....dggggggd....",
    "...dggggggggd...",
    "...dggegggegd...",
    "...dgggeeggd....",
    "....dgggggd.....",
    ".....dggd.......",
    "..ddggggggggdd..",
    ".dggggggggggggd.",
    "...dggggggggd...",
    "...dggggggggd...",
    "..dggggggggggd..",
    "..dggg....gggd..",
    ".dgggd....dgggd.",
    "................",
]
HANIWA_PAL = {"g": ORANGE, "d": ORANGE_D, "e": BG}

# うり坊 uribo — side-view striped boar piglet
URIBO = [
    "................",
    "................",
    "....dd.dd.......",
    "...dbbdbbdd.....",
    "..dbttbttbbbd...",
    ".dbbtbbtbbbbbdd.",
    ".dbbbbbbbbbbbeed",
    ".dbbtbbtbbbbnnnd",
    "..dbttbttbbbbd..",
    "...dddddddddd...",
    "...d.d...d.d....",
    "...d.d...d.d....",
    "................",
    "................",
    "................",
    "................",
]
URIBO_PAL = {"b": BROWN, "d": BROWN_D, "t": TAN, "n": "#f59b76", "e": BG}

# ペンギン penguin — dark body, white belly, orange beak and feet
PENGUIN = [
    "................",
    "......kkkk......",
    ".....kkkkkk.....",
    "....kkwkkwkk....",
    "....kkkoookk....",
    "...kkkkkkkkkk...",
    "..kkkkwwwwkkkk..",
    ".kkkkkwwwwkkkkk.",
    ".kkkkkwwwwkkkkk.",
    "..kkkkwwwwkkkk..",
    "...kkkwwwwkkk...",
    "....kkkwwkkk....",
    ".....kkkkkk.....",
    "....oo....oo....",
    "...ooo....ooo...",
    "................",
]
PENGUIN_PAL = {"k": "#163b45", "w": WHITE, "o": ORANGE}

# モアイ moai — stone head with heavy brow, long nose and lips
MOAI = [
    "................",
    "....dddddd......",
    "...dssssssd.....",
    "..dssssssssd....",
    "..dssddddssd....",
    "..dssdeedssd....",
    "..dssssssssd....",
    "..dsssssssssdd..",
    "..dssssddddsssd.",
    "..dssssssssssd..",
    "..dssddddddsd...",
    "..dsssssssssd...",
    "..dssssddddsd...",
    "..dsssssssssd...",
    "...dddddddd.....",
    "................",
]
MOAI_PAL = {"s": STONE, "d": STONE_D, "e": BG}

# ピラミッド pyramid — stepped triangle with brick cuts
PYRAMID = [
    "................",
    ".......d........",
    "......dgd.......",
    ".....dgggd......",
    "....dgggggd.....",
    "...dggdggggd....",
    "..dggggdggggd...",
    ".dggdggggdgggd..",
    "dggggdggggdgggd.",
    "dggdggggdgggggd.",
    "dgggggggggggggd.",
    "dddddddddddddddd",
    "................",
    "................",
    "................",
    "................",
]
PYRAMID_PAL = {"g": GOLD, "d": "#a66f24"}

# すべすべまんじゅうがに subesube-manjugani — round shell, claws and legs
SUBESUBE_MANJUGANI = [
    "................",
    "................",
    ".....cccccc.....",
    "...cccccccccc...",
    "..cccccccccccc..",
    ".occcaccccaccco.",
    "o.cccccccccccc.o",
    ".occcccccccccco.",
    "..ccccaccccacc..",
    "...cccccccccc...",
    "....dccccccd....",
    ".....dddddd.....",
    ".o.o........o.o.",
    "oo..........oo..",
    "................",
    "................",
]
SUBESUBE_MANJUGANI_PAL = {"c": CREAM, "d": CREAM_D, "o": ORANGE, "e": BG, "a": ACCENT}


# ===========================================================================
# ICONS (16x16) — UI glyphs in mint, flat single-tone pixel art
# ===========================================================================
G = ACCENT
C = ACCENT2

SEARCH = [
    "................",
    "....gggg........",
    "...g....g.......",
    "..g......g......",
    "..g......g......",
    "..g......g......",
    "..g......g......",
    "...g....g.......",
    "....gggg........",
    ".....gggg.......",
    "......gggg......",
    ".......gggg.....",
    "........ggg.....",
    ".........gg.....",
    "................",
    "................",
]

HEART = [
    "................",
    "................",
    "...gg....gg.....",
    "..gggg..gggg....",
    ".gggggggggggg...",
    ".gggggggggggg...",
    ".gggggggggggg...",
    ".gggggggggggg...",
    "..gggggggggg....",
    "...gggggggg.....",
    "....gggggg......",
    ".....gggg.......",
    "......gg........",
    "................",
    "................",
    "................",
]

STAR = [
    "................",
    ".......gg.......",
    ".......gg.......",
    "......gggg......",
    "......gggg......",
    "gggggggggggggg..",
    ".gggggggggggg...",
    "..gggggggggg....",
    "...gggggggg.....",
    "...gggggggg.....",
    "..ggggggggg.....",
    "..ggg...ggg.....",
    ".gg.......gg....",
    ".g.........g....",
    "................",
    "................",
]

DOWNLOAD = [
    "................",
    "......gg........",
    "......gg........",
    "......gg........",
    "......gg........",
    "...g..gg..g.....",
    "...gg.gg.gg.....",
    "....gggggg......",
    ".....gggg.......",
    "......gg........",
    "................",
    ".gg........gg...",
    ".gg........gg...",
    ".gggggggggggg...",
    ".gggggggggggg...",
    "................",
]

TAG = [
    "................",
    "....gggggggg....",
    "...gg......gg...",
    "..gg..dd....gg..",
    "..g..dddd....g..",
    "..g..dddd....g..",
    "..g...dd.....g..",
    "..gg........gg..",
    "...gg......gg...",
    "....gg....gg....",
    ".....gg..gg.....",
    "......gggg......",
    ".......gg.......",
    "................",
    "................",
    "................",
]

COPY = [
    "................",
    "...gggggg.......",
    "...g....g.......",
    "...g.cccccc.....",
    "...g.c....c.....",
    "...ggc....c.....",
    ".....c....c.....",
    ".....c....c.....",
    ".....c....c.....",
    ".....c....c.....",
    ".....cccccc.....",
    "................",
    "................",
    "................",
    "................",
    "................",
]

LINK = [
    "................",
    "................",
    "................",
    "...gggg..gggg...",
    "..gg..gggg..gg..",
    "..g....gg....g..",
    "..g..........g..",
    "..g....gg....g..",
    "..gg..gggg..gg..",
    "...gggg..gggg...",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]

FOLDER = [
    "................",
    "..ggggg.........",
    ".gggggggg.......",
    ".gggggggggggg...",
    ".gggggggggggg...",
    ".gggggggggggg...",
    ".gggggggggggg...",
    ".gggggggggggg...",
    ".gggggggggggg...",
    ".gggggggggggg...",
    "..gggggggggg....",
    "................",
    "................",
    "................",
    "................",
    "................",
]

ICON_PAL = {"g": G, "c": C, "d": BG}


# ===========================================================================
# CURSORS (16x16) — near-white fill + dark edge so they read on any background
# ===========================================================================
W = WHITE
O = INK

POINTER = [
    "o...............",
    "oo..............",
    "owo.............",
    "owwo............",
    "owwwo...........",
    "owwwwo..........",
    "owwwwwo.........",
    "owwwwwwo........",
    "owwwwwwwo.......",
    "owwwwwwwwo......",
    "owwwwwoooo......",
    "owwowwo.........",
    "owo.owwo........",
    "oo..owwo........",
    "o....owwo.......",
    "......oo........",
]

HAND = [
    ".....oo.........",
    "....owwo........",
    "....owwo........",
    "....owwo........",
    "....owwo........",
    "....owwooo......",
    "....owwowwoo....",
    "..oowwowwowo....",
    ".owwwwwwwwwwo...",
    ".owwwwwwwwwwo...",
    ".owwwwwwwwwwo...",
    ".owwwwwwwwwo....",
    "..owwwwwwwwo....",
    "..owwwwwwwo.....",
    "..ooooooooo.....",
    "................",
]

TEXT = [
    "................",
    "...ooo.ooo......",
    "....owowo.......",
    "......o.........",
    "......o.........",
    "......o.........",
    "......o.........",
    "......o.........",
    "......o.........",
    "......o.........",
    "......o.........",
    "......o.........",
    "....owowo.......",
    "...ooo.ooo......",
    "................",
    "................",
]

GRAB = [
    "................",
    "...o.o.o........",
    "..owowowo.......",
    "..owowowoo......",
    "..owwwwwwwo.....",
    ".oowwwwwwwwo....",
    ".owowwwwwwwo....",
    ".owwwwwwwwwo....",
    "..owwwwwwwwo....",
    "..owwwwwwwo.....",
    "...owwwwwwo.....",
    "....oooooo......",
    "................",
    "................",
    "................",
    "................",
]

CURSOR_PAL = {"w": W, "o": O}


# ===========================================================================
def main():
    jobs = [
        # (subdir, name, grid, palette, label, hotspot-grid-or-None)
        ("emoji", "haniwa", HANIWA, HANIWA_PAL, "haniwa", None),
        ("emoji", "uribo", URIBO, URIBO_PAL, "uribo", None),
        ("emoji", "penguin", PENGUIN, PENGUIN_PAL, "penguin", None),
        ("emoji", "moai", MOAI, MOAI_PAL, "moai", None),
        ("emoji", "pyramid", PYRAMID, PYRAMID_PAL, "pyramid", None),
        ("emoji", "subesube-manjugani", SUBESUBE_MANJUGANI, SUBESUBE_MANJUGANI_PAL, "subesube-manjugani", None),
        ("icons", "search", SEARCH, ICON_PAL, "search", None),
        ("icons", "heart", HEART, ICON_PAL, "heart", None),
        ("icons", "star", STAR, ICON_PAL, "star", None),
        ("icons", "download", DOWNLOAD, ICON_PAL, "download", None),
        ("icons", "tag", TAG, ICON_PAL, "tag", None),
        ("icons", "copy", COPY, ICON_PAL, "copy", None),
        ("icons", "link", LINK, ICON_PAL, "link", None),
        ("icons", "folder", FOLDER, ICON_PAL, "folder", None),
        ("cursors", "pointer", POINTER, CURSOR_PAL, "pointer cursor", (0, 0)),
        ("cursors", "hand", HAND, CURSOR_PAL, "hand cursor", (5, 0)),
        ("cursors", "text", TEXT, CURSOR_PAL, "text cursor", (6, 7)),
        ("cursors", "grab", GRAB, CURSOR_PAL, "grab cursor", (5, 6)),
    ]
    for sub, name, grid, pal, label, hs in jobs:
        out = os.path.join(ROOT, "assets", sub, "svg", f"{name}.svg")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            f.write(svg(name, grid, pal, label, hotspot=hs))
        print("wrote", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    main()
