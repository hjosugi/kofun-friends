#!/usr/bin/env python3
"""Group "cast" art for kofun-friends — see everyone at a glance.

Inspired by the vscode-pets group photo (github.com/tonybaloney/vscode-pets):
all the characters clustered together in one friendly shot. We emit two
self-contained, font-free pixel-art SVGs (so they rasterise identically on any
machine — CI included; no system fonts, no blur filters):

  kofun-friends-group.svg  — transparent cluster (hero / marketplace-style icon)
  kofun-friends-cast.svg   — titled dark "slide" with name labels + item strip

The mascots reuse the exact 16x16 grids from gen_sprites.py and the emoji from
gen_pixel_svgs.py, so this art can never drift from the real assets. Labels are
drawn with a tiny built-in 5x7 pixel font (романизированный) — no fonts needed.

Run:  python3 scripts/gen_lineup.py
Out:  assets/lineup/*.svg
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_sprites as S          # noqa: E402  (mascot grids)
import gen_pixel_svgs as P       # noqa: E402  (emoji grids + palette)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# palette echoes the site / gen_pixel_svgs
BG = P.BG
ACCENT = P.ACCENT
ACCENT2 = P.ACCENT2
ORANGE = P.ORANGE
MUTED = "#86a99c"
LINE = "#24443a"
TEXT = "#d9f7ea"


# ---- rect emitters ---------------------------------------------------------

def _rects_from_rgba(px, ox, oy, s, w=S.GRID, h=S.GRID):
    """Mascot pixel buffer (list of rgba) -> list of (x,y,w,h,fill)."""
    out = []
    for y in range(h):
        x = 0
        while x < w:
            r, g, b, a = px[y * w + x]
            if a == 0:
                x += 1
                continue
            fill = "#%02x%02x%02x" % (r, g, b)
            run = 1
            while x + run < w:
                r2, g2, b2, a2 = px[y * w + x + run]
                if a2 == 0 or "#%02x%02x%02x" % (r2, g2, b2) != fill:
                    break
                run += 1
            out.append((ox + x * s, oy + y * s, run * s, s, fill))
            x += run
    return out


def _rects_from_ascii(grid, pal, ox, oy, s):
    """ASCII emoji grid + palette -> list of (x,y,w,h,fill)."""
    out = []
    for y, row in enumerate(grid):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == ".":
                x += 1
                continue
            run = 1
            while x + run < len(row) and row[x + run] == ch:
                run += 1
            out.append((ox + x * s, oy + y * s, run * s, s, pal[ch]))
            x += run
    return out


def mascot_rects(kind, pose, ox, oy, s):
    px = S.kofun_variant(pose) if kind == "kofun" else S.dochi_variant(pose)
    return _rects_from_rgba(px, ox, oy, s)


def mascot_size(s):
    return S.GRID * s


def emoji_rects(name, ox, oy, s):
    key = name.upper().replace("-", "_")
    grid = getattr(P, key)
    pal = getattr(P, key + "_PAL")
    return _rects_from_ascii(grid, pal, ox, oy, s)


# ---- tiny 5x7 pixel font (uppercase subset we actually use) ----------------
FONT = {
    " ": ["     "] * 7,
    "-": ["     ", "     ", "     ", "XXXXX", "     ", "     ", "     "],
    "A": [".XXX.", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    "B": ["XXXX.", "X...X", "X...X", "XXXX.", "X...X", "X...X", "XXXX."],
    "C": [".XXXX", "X....", "X....", "X....", "X....", "X....", ".XXXX"],
    "G": [".XXXX", "X....", "X....", "X.XXX", "X...X", "X...X", ".XXXX"],
    "W": ["X...X", "X...X", "X...X", "X.X.X", "X.X.X", "XX.XX", "X...X"],
    "D": ["XXXX.", "X...X", "X...X", "X...X", "X...X", "X...X", "XXXX."],
    "E": ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "XXXXX"],
    "F": ["XXXXX", "X....", "X....", "XXXX.", "X....", "X....", "X...."],
    "H": ["X...X", "X...X", "X...X", "XXXXX", "X...X", "X...X", "X...X"],
    "I": ["XXXXX", "..X..", "..X..", "..X..", "..X..", "..X..", "XXXXX"],
    "K": ["X...X", "X..X.", "X.X..", "XX...", "X.X..", "X..X.", "X...X"],
    "L": ["X....", "X....", "X....", "X....", "X....", "X....", "XXXXX"],
    "M": ["X...X", "XX.XX", "X.X.X", "X.X.X", "X...X", "X...X", "X...X"],
    "N": ["X...X", "XX..X", "XX..X", "X.X.X", "X..XX", "X..XX", "X...X"],
    "O": [".XXX.", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    "P": ["XXXX.", "X...X", "X...X", "XXXX.", "X....", "X....", "X...."],
    "R": ["XXXX.", "X...X", "X...X", "XXXX.", "X.X..", "X..X.", "X...X"],
    "S": [".XXXX", "X....", "X....", ".XXX.", "....X", "....X", "XXXX."],
    "T": ["XXXXX", "..X..", "..X..", "..X..", "..X..", "..X..", "..X.."],
    "U": ["X...X", "X...X", "X...X", "X...X", "X...X", "X...X", ".XXX."],
    "X": ["X...X", "X...X", ".X.X.", "..X..", ".X.X.", "X...X", "X...X"],
    "Y": ["X...X", "X...X", ".X.X.", "..X..", "..X..", "..X..", "..X.."],
}


def text_width(text, scale):
    return (len(text) * 6 - 1) * scale if text else 0


def text_rects(text, ox, oy, scale, fill):
    out = []
    cx = ox
    for ch in text:
        glyph = FONT.get(ch.upper())
        if glyph:
            for y, row in enumerate(glyph):
                x = 0
                while x < 5:
                    if row[x] == "X":
                        run = 1
                        while x + run < 5 and row[x + run] == "X":
                            run += 1
                        out.append((cx + x * scale, oy + y * scale, run * scale, scale, fill))
                        x += run
                    else:
                        x += 1
        cx += 6 * scale
    return out


def text_centered(text, cx, oy, scale, fill):
    return text_rects(text, cx - text_width(text, scale) // 2, oy, scale, fill)


# ---- SVG assembly ----------------------------------------------------------

def rect_svg(r):
    x, y, w, h, fill = r
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'


def build_svg(w, h, defs, bg_markup, pixel_rects, label, overlay=""):
    px = "\n    ".join(rect_svg(r) for r in pixel_rects)
    defs_block = f"<defs>{defs}</defs>\n  " if defs else ""
    overlay_block = f"\n  {overlay}" if overlay else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!-- {label} — kofun-friends cast art (generated; do not edit by hand) -->\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label="{label}">\n  '
        f'{defs_block}{bg_markup}'
        f'<g shape-rendering="crispEdges">\n    {px}\n  </g>{overlay_block}\n</svg>\n'
    )


# ===========================================================================
# 1) transparent group cluster — the "group photo"
# ===========================================================================
def group_svg():
    # Square, tight 2x2 cluster like the vscode-pets icon: each mascot appears
    # twice (different pose), corners slightly overlapping, with a haniwa badge
    # in the middle. Transparent — drops onto any bg.
    W = H = 256
    s = 7  # 112px per mascot
    r = []
    r += mascot_rects("kofun", "smile", 12, 14, s)        # top-left
    r += mascot_rects("dochicken", "idle", 132, 10, s)    # top-right
    r += mascot_rects("dochicken", "peck", 10, 132, s)    # bottom-left
    r += mascot_rects("kofun", "munch", 134, 134, s)      # bottom-right
    r += emoji_rects("haniwa", 96, 92, 4)                 # centre badge
    return build_svg(W, H, "", "", r, "Kofun-kun and friends — group")


# ===========================================================================
# 2) titled dark "slide" — characters + name labels + item strip
# ===========================================================================
def cast_svg():
    W, H = 1280, 720
    MAGENTA = P.CORAL
    defs = (
        '<linearGradient id="bgwash" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#081a18"/><stop offset="0.6" stop-color="{BG}"/>'
        f'<stop offset="1" stop-color="#0b0712"/></linearGradient>'
        '<linearGradient id="panel" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#10211d"/><stop offset="1" stop-color="#081310"/>'
        "</linearGradient>"
        '<radialGradient id="glowK" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{ACCENT}" stop-opacity="0.45"/>'
        f'<stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="glowD" cx="0.5" cy="0.5" r="0.5">'
        f'<stop offset="0" stop-color="{ORANGE}" stop-opacity="0.45"/>'
        f'<stop offset="1" stop-color="{ORANGE}" stop-opacity="0"/></radialGradient>'
        # neon dot-grid + CRT scanlines — the cyberpunk dot-art texture
        '<pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<rect width="2" height="2" fill="{ACCENT2}" opacity="0.10"/></pattern>'
        '<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#000000" opacity="0.22"/></pattern>'
    )
    # background + frame + stages (smooth, AA — drawn before the crispEdges g)
    bg = [
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#bgwash)"/>',
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#grid)"/>',
        # neon double frame
        f'<rect x="14" y="14" width="{W-28}" height="{H-28}" rx="18" '
        f'fill="none" stroke="{LINE}" stroke-width="3"/>',
        f'<rect x="20" y="20" width="{W-40}" height="{H-40}" rx="14" '
        f'fill="none" stroke="{ACCENT}" stroke-width="1" opacity="0.35"/>',
    ]
    # two stages
    stage_w = 340
    gap = 100
    total = stage_w * 2 + gap
    sx0 = (W - total) // 2
    stages = [("kofun", "smile", sx0, ACCENT, "glowK", "KOFUN-KUN"),
              ("dochicken", "idle", sx0 + stage_w + gap, ORANGE, "glowD", "DOCHICKEN-SAN")]
    stage_y = 178
    for kind, pose, sx, color, glow, name in stages:
        bg.append(f'<rect x="{sx}" y="{stage_y}" width="{stage_w}" height="{stage_w}" '
                  f'rx="20" fill="url(#panel)" stroke="{LINE}" stroke-width="3"/>')
        bg.append(f'<rect x="{sx+20}" y="{stage_y+20}" width="{stage_w-40}" '
                  f'height="{stage_w-40}" fill="url(#{glow})"/>')
    bg_markup = "\n  ".join(bg) + "\n  "

    r = []
    # title with chromatic-aberration glitch (magenta + cyan offsets + mint core)
    title = "KOFUN-FRIENDS"
    tscale = 10
    cx = W // 2
    r += text_centered(title, cx - 5, 48 + 3, tscale, MAGENTA)
    r += text_centered(title, cx + 5, 48 - 3, tscale, ACCENT2)
    r += text_centered(title, cx, 48, tscale, ACCENT)
    r += text_centered("PIXEL MASCOTS", cx, 132, 4, MUTED)

    # mascots inside stages + name labels
    mscale = 18
    msz = mascot_size(mscale)
    for kind, pose, sx, color, glow, name in stages:
        mx = sx + (stage_w - msz) // 2
        my = stage_y + (stage_w - msz) // 2
        r += mascot_rects(kind, pose, mx, my, mscale)
        r += text_centered(name, sx + stage_w // 2, stage_y + stage_w + 22, 6, color)

    # item strip along the bottom
    items = ["haniwa", "uribo", "penguin", "moai", "pyramid", "subesube-manjugani"]
    iscale = 5
    isz = P.N * iscale
    igap = 26
    iwidth = len(items) * isz + (len(items) - 1) * igap
    ix = (W - iwidth) // 2
    iy = 612
    for i, name in enumerate(items):
        r += emoji_rects(name, ix + i * (isz + igap), iy, iscale)

    overlay = f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#scan)"/>'
    return build_svg(W, H, defs, bg_markup, r, "Kofun-kun and friends — cast", overlay)


# ===========================================================================
# 3) roster grid — every sprite + label at a glance (cf. vscode-pets pet-grid)
# ===========================================================================
def grid_svg():
    W, H = 1280, 720
    defs = (
        '<linearGradient id="bgwash2" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#081a18"/><stop offset="0.6" stop-color="{BG}"/>'
        f'<stop offset="1" stop-color="#0b0712"/></linearGradient>'
        '<linearGradient id="cell" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#10211d"/><stop offset="1" stop-color="#081310"/>'
        "</linearGradient>"
        '<pattern id="grid2" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<rect width="2" height="2" fill="{ACCENT2}" opacity="0.10"/></pattern>'
        '<pattern id="scan2" width="4" height="3" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#000000" opacity="0.20"/></pattern>'
    )
    bg = [
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#bgwash2)"/>',
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#grid2)"/>',
        f'<rect x="14" y="14" width="{W-28}" height="{H-28}" rx="18" '
        f'fill="none" stroke="{LINE}" stroke-width="3"/>',
    ]
    r = []
    # title
    cx = W // 2
    r += text_centered("KOFUN-FRIENDS", cx - 4, 30 + 2, 6, P.CORAL)
    r += text_centered("KOFUN-FRIENDS", cx + 4, 30 - 2, 6, ACCENT2)
    r += text_centered("KOFUN-FRIENDS", cx, 30, 6, ACCENT)
    r += text_centered("CHARACTER ROSTER", cx, 96, 3, MUTED)

    # rows: (header, color, [(rect-fn, label, scale), ...])
    def km(pose):
        return lambda ox, oy, s: mascot_rects("kofun", pose, ox, oy, s)

    def dm(pose):
        return lambda ox, oy, s: mascot_rects("dochicken", pose, ox, oy, s)

    def em(name):
        return lambda ox, oy, s: emoji_rects(name, ox, oy, s)

    rows = [
        ("KOFUN-KUN", ACCENT, 6, [(km("idle"), "IDLE"), (km("blink"), "BLINK"),
                                  (km("smile"), "SMILE"), (km("munch"), "MUNCH")]),
        ("DOCHICKEN-SAN", ORANGE, 6, [(dm("idle"), "IDLE"), (dm("blink"), "BLINK"),
                                      (dm("peck"), "PECK")]),
        ("FRIENDS", ACCENT2, 5, [(em("haniwa"), "HANIWA"), (em("uribo"), "URIBO"),
                                  (em("penguin"), "PENGUIN"), (em("moai"), "MOAI"),
                                  (em("pyramid"), "PYRAMID"),
                                  (em("subesube-manjugani"), "CRAB")]),
    ]

    y = 148
    box = 110            # cell panel size
    pitch = 168          # horizontal step between cells
    for header, color, scale, cells in rows:
        row_w = (len(cells) - 1) * pitch + box
        x0 = (W - row_w) // 2
        r += text_rects(header, x0, y, 4, color)
        cy = y + 32
        sprite = P.N * scale  # 16*scale
        for i, (fn, label) in enumerate(cells):
            bx = x0 + i * pitch
            bg.append(f'<rect x="{bx}" y="{cy}" width="{box}" height="{box}" rx="14" '
                      f'fill="url(#cell)" stroke="{LINE}" stroke-width="2"/>')
            off = (box - sprite) // 2
            r += fn(bx + off, cy + off, scale)
            r += text_centered(label, bx + box // 2, cy + box + 10, 3, MUTED)
        y = cy + box + 44

    overlay = f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#scan2)"/>'
    bg_markup = "\n  ".join(bg) + "\n  "
    return build_svg(W, H, defs, bg_markup, r, "Kofun-kun and friends — roster", overlay)


def main():
    outdir = os.path.join(ROOT, "assets", "lineup")
    os.makedirs(outdir, exist_ok=True)
    for name, svg in (("kofun-friends-group", group_svg()),
                      ("kofun-friends-cast", cast_svg()),
                      ("kofun-friends-grid", grid_svg())):
        out = os.path.join(outdir, name + ".svg")
        with open(out, "w") as f:
            f.write(svg)
        print("wrote", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    main()
