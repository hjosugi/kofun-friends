#!/usr/bin/env python3
"""Generate motion-study GIFs and sprite sheets for kofun-friends.

These are exploration assets, separate from the canonical Kofun-kun /
Dochicken-san sprites in assets/kofun and assets/dochicken. The goal is to
quickly compare many tiny animation deltas: bob, hop, dash, turn, and wiggle.

Run:  python3 scripts/gen_motion_studies.py
Out:  assets/motion/gif/*.gif, assets/motion/sheets/*.png, assets/motion/board/*.png
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_pixel_svgs as P  # noqa: E402
import gen_sprites as S     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANVAS = 24
MOTION_FRAMES = 6
GIF_SCALE = 4  # 24 * 4 = 96px
GIF_DELAY_CS = 12

OUT_GIF = os.path.join(ROOT, "assets", "motion", "gif")
OUT_SHEETS = os.path.join(ROOT, "assets", "motion", "sheets")
OUT_BOARD = os.path.join(ROOT, "assets", "motion", "board")

TRANSPARENT = (0, 0, 0, 0)
SHADOW = S.hx("#1c1830")
CYAN = S.hx("#00ffff")
MAGENTA = S.hx("#ff0090")
ACID = S.hx("#ccff00")


CHARACTERS = [
    ("kofun-kun", lambda: S.kofun_variant("smile")),
    ("dochicken-san", lambda: S.dochi_variant("idle")),
    ("haniwa", lambda: emoji_pixels("haniwa")),
    ("uribo", lambda: emoji_pixels("uribo")),
    ("penguin", lambda: emoji_pixels("penguin")),
    ("moai", lambda: emoji_pixels("moai")),
    ("subesube-manjugani", lambda: emoji_pixels("subesube-manjugani")),
    ("cactus", lambda: emoji_pixels("cactus")),
]


def emoji_pixels(name):
    grid = getattr(P, name.upper().replace("-", "_"))
    pal = {k: S.hx(v) for k, v in getattr(P, name.upper().replace("-", "_") + "_PAL").items()}
    px = [TRANSPARENT] * (P.N * P.N)
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch != ".":
                px[y * P.N + x] = pal[ch]
    return px


def rect(px, x, y, w, h, colour):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if 0 <= xx < CANVAS and 0 <= yy < CANVAS:
                px[yy * CANVAS + xx] = colour


def dominant_colour(src):
    colours = Counter((r, g, b, a) for r, g, b, a in src if a)
    bright = Counter(c for c, n in colours.items() if sum(c[:3]) > 150 for _ in range(n))
    return bright.most_common(1)[0][0] if bright else colours.most_common(1)[0][0]


def back_source(src):
    body = dominant_colour(src)
    out = []
    for r, g, b, a in src:
        if not a:
            out.append(TRANSPARENT)
        elif r + g + b < 110:
            out.append(body)
        else:
            out.append((max(0, body[0] - 24), max(0, body[1] - 24), max(0, body[2] - 24), body[3]))
    return out


def canvas(src, ox=4, oy=4, flip=False, lean=0, shadow=True, trail=0, back=False):
    out = [TRANSPARENT] * (CANVAS * CANVAS)
    if shadow:
        rect(out, ox + 3, oy + 17, 10, 2, SHADOW)
        rect(out, ox + 5, oy + 19, 6, 1, SHADOW)
    if trail:
        colour = MAGENTA if trail < 0 else CYAN
        tx = ox - 2 if trail < 0 else ox + 15
        rect(out, tx, oy + 6, 3, 1, colour)
        rect(out, tx - trail, oy + 9, 5, 1, colour)
        rect(out, tx - trail * 2, oy + 12, 4, 1, ACID)
    source = back_source(src) if back else src
    for sy in range(16):
        row_shift = int(round(((sy - 8) / 8) * lean))
        for sx in range(16):
            px = source[sy * 16 + sx]
            if px[3] == 0:
                continue
            x = 15 - sx if flip else sx
            dx = ox + x + row_shift
            dy = oy + sy
            if 0 <= dx < CANVAS and 0 <= dy < CANVAS:
                out[dy * CANVAS + dx] = px
    return out


def motion_rows(src):
    bob = [canvas(src, 4, 4 + y) for y in [0, -1, 0, 1, 0, -1]]
    hop = [canvas(src, 4, 5), canvas(src, 4, 4), canvas(src, 4, 2), canvas(src, 4, 1),
           canvas(src, 4, 3), canvas(src, 4, 4)]
    dash = [canvas(src, x, 4, trail=-1) for x in [1, 3, 6, 9, 12, 7]]
    turn = [
        canvas(src, 4, 4),
        canvas(src, 5, 4, lean=1),
        canvas(src, 4, 4, back=True),
        canvas(src, 3, 4, flip=True, lean=-1),
        canvas(src, 4, 4, flip=True),
        canvas(src, 4, 4),
    ]
    wiggle = [canvas(src, 4, 4, lean=v) for v in [-1, 1, -1, 1, 0, -1]]
    return [("bob", bob), ("hop", hop), ("dash", dash), ("turn", turn), ("wiggle", wiggle)]


def paste(dst, dw, frame, ox, oy):
    for y in range(CANVAS):
        for x in range(CANVAS):
            px = frame[y * CANVAS + x]
            if px[3] != 0:
                dst[(oy + y) * dw + ox + x] = px


def sheet(rows):
    w = CANVAS * MOTION_FRAMES
    h = CANVAS * len(rows)
    out = [TRANSPARENT] * (w * h)
    for row_idx, (_, frames) in enumerate(rows):
        for col_idx, frame in enumerate(frames):
            paste(out, w, frame, col_idx * CANVAS, row_idx * CANVAS)
    return out, w, h


def angle_strip(src):
    frames = [
        canvas(src, 4, 4),
        canvas(src, 5, 4, lean=1),
        canvas(src, 4, 4, back=True),
        canvas(src, 3, 4, flip=True, lean=-1),
    ]
    w = CANVAS * len(frames)
    h = CANVAS
    out = [TRANSPARENT] * (w * h)
    for i, frame in enumerate(frames):
        paste(out, w, frame, i * CANVAS, 0)
    return frames, out, w, h


def board(character_rows):
    cols = len(character_rows)
    rows = 5
    gap = 4
    w = cols * CANVAS + (cols - 1) * gap
    h = rows * CANVAS + (rows - 1) * gap
    out = [S.hx("#0a0a14")] * (w * h)
    for col, (_, motions) in enumerate(character_rows):
        for row, (_, frames) in enumerate(motions):
            paste(out, w, frames[2], col * (CANVAS + gap), row * (CANVAS + gap))
    return out, w, h


def main():
    os.makedirs(OUT_GIF, exist_ok=True)
    os.makedirs(OUT_SHEETS, exist_ok=True)
    os.makedirs(OUT_BOARD, exist_ok=True)

    board_rows = []
    for slug, make_src in CHARACTERS:
        src = make_src()
        rows = motion_rows(src)
        board_rows.append((slug, rows))

        motion_frames = [frame for _, frames in rows for frame in frames]
        gif = os.path.join(OUT_GIF, f"{slug}-motion-pack.gif")
        S.write_gif(gif, motion_frames, scale=GIF_SCALE, delay_cs=GIF_DELAY_CS, w=CANVAS, h=CANVAS)
        print("wrote", os.path.relpath(gif, ROOT))

        turn_frames, angles, aw, ah = angle_strip(src)
        turn_gif = os.path.join(OUT_GIF, f"{slug}-turntable.gif")
        S.write_gif(turn_gif, turn_frames + turn_frames[::-1], scale=GIF_SCALE,
                    delay_cs=GIF_DELAY_CS + 6, w=CANVAS, h=CANVAS)
        print("wrote", os.path.relpath(turn_gif, ROOT))

        pixels, sw, sh = sheet(rows)
        sheet_path = os.path.join(OUT_SHEETS, f"{slug}-motion-sheet.png")
        S.write_png(sheet_path, pixels, w=sw, h=sh)
        print("wrote", os.path.relpath(sheet_path, ROOT))

        angle_path = os.path.join(OUT_SHEETS, f"{slug}-angle-strip.png")
        S.write_png(angle_path, angles, w=aw, h=ah)
        print("wrote", os.path.relpath(angle_path, ROOT))

    pixels, bw, bh = board(board_rows)
    board_path = os.path.join(OUT_BOARD, "motion-board.png")
    S.write_png(board_path, pixels, w=bw, h=bh)
    print("wrote", os.path.relpath(board_path, ROOT))


if __name__ == "__main__":
    main()
