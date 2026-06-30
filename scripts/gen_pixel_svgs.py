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
BG = "#0a0a14"        # near-black violet from cyberpunk/neon palettes
ACCENT = "#00ffff"    # electric cyan
ACCENT2 = "#00ccff"   # saturated blue-cyan
CORAL = "#ff0090"     # hot magenta
DANGER = "#ff44cc"    # pink glow
GOLD = "#ffe040"
ORANGE = "#ff6600"
ORANGE_D = "#7a2f20"
ACID = "#ccff00"
VIOLET = "#7c4dff"
VIOLET_D = "#2a2445"
JADE = "#00ffff"
JADE_D = "#1870a8"
JADE_L = "#e8e8ff"
STEEL = "#e8e8ff"
STEEL_D = "#105080"
CREAM = "#e8e8ff"
CREAM_D = "#9aa8c8"
INK = "#0a0a14"       # dark outline / cursor outline
WHITE = "#e8e8ff"
BROWN = "#9a5a3d"
BROWN_D = "#1c1830"
TAN = "#ffe040"
STONE = "#9aa8c8"
STONE_D = "#2a2445"

# Muted small-RPG palette for the side characters. Kofun-kun / Dochicken-san
# stay in gen_sprites.py; these colours only affect the emoji friends.
PIXEL_INK = "#241a24"
PIXEL_HOLE = "#08070d"
CLAY = "#b97854"
CLAY_L = "#d99572"
CLAY_D = "#7a4a34"
BOAR = "#8e5f3c"
BOAR_D = "#5f382b"
BOAR_STRIPE = "#e1b36b"
PINK = "#f28b93"
NEON_CYAN = "#00d7ff"
NEON_PINK = "#ff4fa3"
NAVY = "#2f7de1"
NAVY_D = "#12345d"
SNOW = "#f0f2ee"
STONE_M = "#8d93a6"
STONE_L = "#b6bccb"
STONE_S = "#5d6172"
SAND = "#d5a24c"
SAND_L = "#f0c86b"
SAND_S = "#8f6130"
CRAB = "#d84a35"
CRAB_L = "#ff8060"
GREEN = "#4aa35f"
GREEN_L = "#73c779"
GREEN_S = "#2d7048"


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

# 埴輪 haniwa — broad clay idol with only the readable features kept
HANIWA = [
    "................",
    "......dddd......",
    "....ddccccdd....",
    "...dccccccccd...",
    "...dcceddcecd...",
    "...dccccccccd...",
    "....ddccccdd....",
    "..ddccccccccdd..",
    ".dccccccccccccd.",
    "..dccccccccccd..",
    "...dcccclcccd...",
    "...dccccccccd...",
    "...dccd..dccd...",
    "...dcd....dcd...",
    "....d......d....",
    "................",
]
HANIWA_PAL = {"c": CLAY, "l": CLAY_L, "d": PIXEL_INK, "e": PIXEL_HOLE}

# うり坊 uribo — side-view striped boar piglet
URIBO = [
    "................",
    "................",
    "....dd..........",
    "...dttd.........",
    "..dccccdddd.....",
    ".dctcctccccdd...",
    "dctcctccccccnd..",
    "dcccccccccend...",
    ".dccctccccccd...",
    "..dccccccccd....",
    "...ddddd.dd.....",
    "...d..d.d.......",
    "................",
    "................",
    "................",
    "................",
]
URIBO_PAL = {"c": BOAR, "d": PIXEL_INK, "t": BOAR_STRIPE, "n": PINK, "e": PIXEL_HOLE}

# ペンギン penguin — blue neon body, small feet, and a clean white belly
PENGUIN = [
    "................",
    "......dddd......",
    ".....dkkkkd.....",
    "....dkkkkkkd....",
    "....dkeakked....",
    "...dkkkoakkkd...",
    "...dkkwwwwkkd...",
    "..dkkkwwwwkkkd..",
    "..dkkkwwwwkkkd..",
    "...dkkwwwwkkd...",
    "....dkkwwkkd....",
    ".....dkkkkd.....",
    "......dddd......",
    "......o..o......",
    "................",
    "................",
]
PENGUIN_PAL = {"k": NAVY, "a": NEON_CYAN, "w": SNOW, "o": ORANGE, "d": NAVY_D, "e": PIXEL_HOLE}

# モアイ moai — stone head with heavy brow, long nose and lips
MOAI = [
    "................",
    "....ddddddd.....",
    "...dssssssdd....",
    "..dssssssssdd...",
    "..dssddddsssd...",
    "..dsseesssssd...",
    "..dssssddsssd...",
    "..dssssdssssd...",
    "..dssssdssssd...",
    "..dssddddsssd...",
    "..dsssssssssd...",
    "..dssddddsssd...",
    "...dsssssssd....",
    "....ddddddd.....",
    "................",
    "................",
]
MOAI_PAL = {"s": STONE_M, "l": STONE_L, "d": PIXEL_INK, "e": PIXEL_HOLE}

# すべすべまんじゅうがに subesube-manjugani — round shell, claws and legs
SUBESUBE_MANJUGANI = [
    "................",
    "...dd......dd...",
    "..dcld....dlcd..",
    "..dcld....dlcd..",
    "...dddccccddd...",
    "..dccccccccd....",
    ".dccecccccecd...",
    ".dccccccccccd...",
    "..dcccllcccd....",
    "...dccccccd.....",
    "..d.d....d.d....",
    ".d.d......d.d...",
    "................",
    "................",
    "................",
    "................",
]
SUBESUBE_MANJUGANI_PAL = {"c": CRAB, "l": CRAB_L, "d": PIXEL_INK, "e": PIXEL_HOLE}

# さぼてん cactus — saguaro silhouette, neon flower, chunky arms
CACTUS = [
    "................",
    ".......ff.......",
    "......dggd......",
    "......dggd......",
    "..dd..dggd..dd..",
    ".dggd.dggd.dggd.",
    ".dggddggggddggd.",
    "..dggdggggdggd..",
    "...ddggggggdd...",
    ".....dglggd.....",
    ".....dggggd.....",
    ".....dggggd.....",
    ".....dggggd.....",
    "....dggggggd....",
    "....dddddddd....",
    "................",
]
CACTUS_PAL = {"g": GREEN, "l": GREEN_L, "d": PIXEL_INK, "f": CORAL}


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
        ("emoji", "subesube-manjugani", SUBESUBE_MANJUGANI, SUBESUBE_MANJUGANI_PAL, "subesube-manjugani", None),
        ("emoji", "cactus", CACTUS, CACTUS_PAL, "cactus", None),
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
