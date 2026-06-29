#!/usr/bin/env python3
"""Generate cyberpunk background studies for placing kofun-friends characters.

These are original, repo-native SVG concepts. The downloaded CC0 references in
assets/backgrounds/cc0/ are mood/source material; this script creates our own
stage-sized backgrounds so the mascots can be tested in many lighting worlds.

Run:  python3 scripts/gen_backgrounds.py
Out:  assets/backgrounds/svg/*.svg
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_sprites as S  # noqa: E402

OUT = os.path.join(ROOT, "assets", "backgrounds", "svg")
W = 320
H = 180

# Original neon palette for high-contrast pixel backgrounds.
C = {
    "void": "#0b001b",
    "night": "#08173d",
    "blue": "#03274c",
    "cyan": "#53ebe4",
    "cyan_d": "#0f9595",
    "violet": "#7c4dff",
    "purple": "#4d004f",
    "magenta": "#e13a6a",
    "magenta_d": "#c1115a",
    "pink": "#eca6c0",
    "acid": "#c8ff2b",
    "yellow": "#ffea00",
    "orange": "#ff7a00",
    "ice": "#eaffff",
    "ink": "#050915",
}

SCENES = [
    ("neon-alley", "Neon Alley"),
    ("rain-skyline", "Rain Skyline"),
    ("maglev-platform", "Maglev Platform"),
    ("arcade-market", "Arcade Market"),
    ("rooftop-antennas", "Rooftop Antennas"),
    ("data-shrine", "Data Shrine"),
    ("underpass", "Underpass"),
    ("holo-billboards", "Holo Billboards"),
    ("canal-reflections", "Canal Reflections"),
    ("pyramid-terminal", "Pyramid Terminal"),
    ("moai-plaza", "Moai Plaza"),
    ("crab-dock", "Crab Dock"),
]


def rect(x, y, w, h, fill, opacity=None):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{op}/>'


def poly(points, fill, opacity=None):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    pts = " ".join(f"{x},{y}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}"{op}/>'


def line(x1, y1, x2, y2, stroke, width=1, opacity=None):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{stroke}" stroke-width="{width}"{op}/>'
    )


def stars(seed, count=34):
    out = []
    for i in range(count):
        x = (seed * 31 + i * 47) % W
        y = 8 + ((seed * 19 + i * 23) % 78)
        col = C["cyan"] if i % 5 else C["magenta"]
        out.append(rect(x, y, 1, 1, col, 0.45 if i % 3 else 0.75))
    return out


def base(seed, floor=138):
    out = [
        rect(0, 0, W, H, C["void"]),
        rect(0, 0, W, 84, C["night"], 0.72),
        rect(0, 80, W, floor - 80, C["blue"], 0.48),
        rect(0, floor, W, H - floor, C["ink"]),
    ]
    out += stars(seed)
    for y in range(0, H, 4):
        out.append(rect(0, y, W, 1, "#000000", 0.16))
    return out


def skyline(y, heights, fill, edge):
    out = []
    x = 0
    widths = [18, 12, 24, 16, 26, 14, 21, 11, 19, 28, 13, 17, 22]
    for i, h in enumerate(heights):
        w = widths[i % len(widths)]
        out.append(rect(x, y - h, w, h, fill, 0.95))
        if i % 2 == 0:
            out.append(rect(x + w - 2, y - h - 8, 2, 8, edge, 0.55))
        for wy in range(y - h + 8, y - 4, 14):
            wx = x + 4 + ((i + wy) % max(4, w - 7))
            out.append(rect(wx, wy, 2, 3, edge, 0.8 if (i + wy) % 3 == 0 else 0.35))
        x += w + 4
    return out


def floor_grid(y=140, color=None):
    color = color or C["cyan_d"]
    out = [rect(0, y, W, 2, color, 0.8), rect(0, H - 20, W, 2, C["magenta_d"], 0.55)]
    for yy in [148, 156, 165, 174]:
        out.append(line(0, yy, W, yy, color, 1, 0.34))
    for x in range(-160, W + 180, 32):
        out.append(line(W // 2, y, x, H, color, 1, 0.28))
    return out


def sign(x, y, w, h, fill, edge, slats=3):
    out = [rect(x, y, w, h, fill, 0.9), rect(x, y, w, 2, edge), rect(x, y + h - 2, w, 2, edge)]
    for i in range(slats):
        out.append(rect(x + 4 + i * 8, y + 5, 4, h - 10, edge, 0.78))
    return out


def scene_neon_alley():
    out = base(1, 136)
    out += skyline(104, [54, 72, 44, 62, 84, 38, 68, 55, 76], C["purple"], C["magenta"])
    out += [poly([(0, 42), (58, 24), (58, 150), (0, 180)], C["ink"], 0.82)]
    out += [poly([(320, 28), (258, 42), (258, 152), (320, 180)], C["blue"], 0.9)]
    out += sign(14, 58, 22, 70, C["magenta_d"], C["cyan"], 2)
    out += sign(268, 52, 30, 58, C["cyan_d"], C["acid"], 3)
    out += [rect(86, 118, 146, 16, C["violet"], 0.28)]
    out += floor_grid(136, C["cyan"])
    return out


def scene_rain_skyline():
    out = base(2, 128)
    out += skyline(118, [28, 48, 74, 39, 60, 90, 44, 66, 34, 58, 82], C["blue"], C["cyan"])
    out += skyline(132, [46, 32, 62, 86, 52, 72, 28, 44, 68, 50], C["purple"], C["magenta"])
    for x in range(4, W, 11):
        out.append(line(x, 14 + (x % 9), x - 4, 80 + (x % 33), C["cyan"], 1, 0.42))
    for y in range(140, 178, 8):
        out.append(rect(18, y, 280, 1, C["cyan"], 0.20))
        out.append(rect(50, y + 3, 210, 1, C["magenta"], 0.18))
    return out


def scene_maglev_platform():
    out = base(3, 126)
    out += skyline(102, [36, 58, 48, 73, 41, 64, 54, 38, 70], C["purple"], C["cyan"])
    out += [rect(0, 104, W, 20, C["ink"]), rect(28, 92, 258, 22, C["blue"])]
    out += [rect(36, 96, 226, 4, C["cyan"]), rect(55, 105, 164, 5, C["magenta"])]
    out += [rect(70, 92, 14, 22, C["yellow"]), rect(236, 92, 8, 22, C["acid"])]
    out += [rect(0, 128, W, 10, C["violet"], 0.45), rect(0, 142, W, 4, C["cyan_d"])]
    out += floor_grid(146, C["cyan"])
    return out


def scene_arcade_market():
    out = base(4, 132)
    out += skyline(94, [60, 44, 78, 38, 88, 52, 70], C["blue"], C["magenta"])
    for x, col in [(24, C["magenta"]), (72, C["cyan"]), (122, C["yellow"]), (178, C["violet"]), (238, C["acid"])]:
        out += [rect(x, 72, 34, 46, C["ink"]), rect(x + 2, 74, 30, 14, col), rect(x + 6, 94, 22, 20, col, 0.30)]
    out += [rect(0, 122, W, 12, C["purple"], 0.76)]
    for x in range(10, W, 28):
        out.append(rect(x, 126, 14, 2, C["cyan"] if x % 3 else C["magenta"]))
    out += floor_grid(134, C["magenta"])
    return out


def scene_rooftop_antennas():
    out = base(5, 130)
    out += skyline(128, [32, 52, 28, 74, 44, 60, 36, 80, 50, 26], C["purple"], C["cyan"])
    out += [rect(0, 130, W, 18, C["ink"]), rect(28, 116, 264, 16, C["blue"])]
    for x, h, col in [(38, 50, C["cyan"]), (96, 70, C["magenta"]), (170, 58, C["acid"]), (248, 76, C["cyan"])]:
        out += [rect(x, 58, 2, h, col), rect(x - 5, 58, 12, 2, col), line(x, 72, x - 20, 118, col, 1, 0.45), line(x, 74, x + 20, 118, col, 1, 0.45)]
    out += [rect(28, 144, 264, 6, C["cyan_d"], 0.8)]
    return out


def scene_data_shrine():
    out = base(6, 134)
    out += skyline(110, [44, 34, 58, 72, 40, 62, 52, 36, 66], C["blue"], C["cyan"])
    out += [rect(82, 60, 156, 8, C["magenta"]), rect(94, 68, 10, 62, C["magenta"]), rect(216, 68, 10, 62, C["magenta"])]
    out += [rect(104, 82, 112, 6, C["cyan"]), rect(114, 88, 8, 38, C["cyan"]), rect(198, 88, 8, 38, C["cyan"])]
    out += [rect(138, 92, 44, 28, C["ink"]), rect(146, 100, 28, 4, C["acid"]), rect(150, 108, 20, 3, C["cyan"])]
    out += floor_grid(134, C["magenta"])
    return out


def scene_underpass():
    out = base(7, 126)
    out += [poly([(0, 44), (122, 76), (122, 126), (0, 158)], C["blue"], 0.84)]
    out += [poly([(320, 44), (198, 76), (198, 126), (320, 158)], C["purple"], 0.88)]
    out += [rect(122, 76, 76, 50, C["ink"]), rect(136, 88, 48, 24, C["violet"], 0.45)]
    for x in [16, 44, 74, 232, 260, 290]:
        out += sign(x, 72 + (x % 3) * 8, 12, 44, C["cyan_d"] if x < 160 else C["magenta_d"], C["acid"], 1)
    out += floor_grid(126, C["cyan"])
    return out


def scene_holo_billboards():
    out = base(8, 136)
    out += skyline(132, [64, 92, 48, 76, 60, 104, 46, 84], C["ink"], C["cyan"])
    out += [rect(24, 38, 92, 42, C["cyan"], 0.82), rect(32, 46, 76, 26, C["blue"], 0.9)]
    out += [rect(198, 46, 86, 54, C["magenta"], 0.78), rect(208, 58, 66, 28, C["purple"], 0.92)]
    out += [rect(134, 64, 42, 28, C["acid"], 0.7), rect(142, 72, 26, 12, C["ink"], 0.85)]
    out += floor_grid(136, C["violet"])
    return out


def scene_canal_reflections():
    out = base(9, 112)
    out += skyline(108, [38, 56, 72, 44, 68, 52, 88, 34, 60], C["purple"], C["magenta"])
    out += [rect(0, 112, W, 12, C["ink"]), rect(0, 124, W, 56, C["blue"], 0.72)]
    for y in range(130, 176, 7):
        out.append(rect((y * 3) % 42, y, 74, 1, C["cyan"], 0.44))
        out.append(rect(126 + (y * 5) % 28, y + 2, 98, 1, C["magenta"], 0.36))
        out.append(rect(238 - (y * 2) % 36, y + 4, 48, 1, C["acid"], 0.26))
    return out


def scene_pyramid_terminal():
    out = base(10, 138)
    out += skyline(108, [46, 34, 58, 40, 74, 52, 36, 64], C["blue"], C["cyan"])
    out += [poly([(160, 38), (88, 134), (232, 134)], C["purple"], 0.9)]
    out += [poly([(160, 38), (160, 134), (232, 134)], C["magenta_d"], 0.42)]
    for y in [58, 76, 94, 112, 128]:
        out.append(line(104 + (y - 58) // 2, y, 216 - (y - 58) // 2, y, C["yellow"], 1, 0.82))
    out += [rect(144, 106, 32, 18, C["cyan"], 0.65)]
    out += floor_grid(138, C["yellow"])
    return out


def scene_moai_plaza():
    out = base(11, 138)
    out += skyline(102, [36, 74, 46, 58, 82, 40, 66, 54], C["blue"], C["cyan"])
    out += [rect(126, 52, 68, 82, C["violet"], 0.82), rect(136, 62, 48, 10, C["cyan"], 0.72)]
    out += [rect(142, 76, 8, 10, C["ink"]), rect(170, 76, 8, 10, C["ink"])]
    out += [rect(154, 78, 12, 36, C["magenta"]), rect(146, 114, 32, 5, C["cyan"]), rect(150, 124, 24, 4, C["pink"])]
    out += [rect(112, 134, 96, 8, C["ink"]), rect(96, 142, 128, 6, C["cyan_d"])]
    out += floor_grid(148, C["magenta"])
    return out


def scene_crab_dock():
    out = base(12, 126)
    out += skyline(100, [42, 58, 36, 78, 48, 62, 34, 72, 44], C["purple"], C["cyan"])
    out += [rect(0, 126, W, 16, C["ink"]), rect(0, 142, W, 38, C["blue"], 0.74)]
    out += [rect(44, 82, 54, 28, C["magenta_d"]), rect(54, 90, 34, 12, C["yellow"]), rect(64, 84, 14, 4, C["cyan"])]
    out += [rect(218, 78, 50, 34, C["cyan_d"]), rect(226, 86, 34, 16, C["pink"]), rect(236, 92, 14, 4, C["ink"])]
    for x in range(18, W, 42):
        out += [rect(x, 132, 4, 26, C["violet"]), rect(x - 8, 132, 32, 2, C["cyan"], 0.72)]
    for y in range(148, 178, 8):
        out.append(rect(14 + y % 30, y, 86, 1, C["cyan"], 0.34))
        out.append(rect(176 - y % 24, y + 3, 94, 1, C["magenta"], 0.28))
    return out


BUILDERS = {
    "neon-alley": scene_neon_alley,
    "rain-skyline": scene_rain_skyline,
    "maglev-platform": scene_maglev_platform,
    "arcade-market": scene_arcade_market,
    "rooftop-antennas": scene_rooftop_antennas,
    "data-shrine": scene_data_shrine,
    "underpass": scene_underpass,
    "holo-billboards": scene_holo_billboards,
    "canal-reflections": scene_canal_reflections,
    "pyramid-terminal": scene_pyramid_terminal,
    "moai-plaza": scene_moai_plaza,
    "crab-dock": scene_crab_dock,
}


def content_for(name):
    return "\n    ".join(BUILDERS[name]())


def svg_doc(name, label, content, w=W, h=H):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!-- {label} — kofun-friends cyberpunk background study -->\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img" aria-label="{label}">\n'
        f'  <g shape-rendering="crispEdges">\n    {content}\n  </g>\n</svg>\n'
    )


def board_svg():
    cells = []
    for idx, (name, label) in enumerate(SCENES):
        x = (idx % 4) * W
        y = (idx // 4) * H
        cells.append(f'<g transform="translate({x} {y})">\n    {content_for(name)}\n  </g>')
        cells.append(rect(x + 6, y + 6, 96, 12, C["ink"], 0.62))
        cells.append(
            f'<text x="{x + 10}" y="{y + 16}" fill="{C["ice"]}" '
            f'font-family="monospace" font-size="8">{label}</text>'
        )
    return svg_doc(
        "background-board",
        "Kofun Friends cyberpunk background board",
        "\n  ".join(cells),
        W * 4,
        H * 3,
    )


def mascot_rects(px, ox, oy, scale):
    out = []
    for y in range(S.GRID):
        x = 0
        while x < S.GRID:
            r, g, b, a = px[y * S.GRID + x]
            if a == 0:
                x += 1
                continue
            fill = "#%02x%02x%02x" % (r, g, b)
            run = 1
            while x + run < S.GRID:
                r2, g2, b2, a2 = px[y * S.GRID + x + run]
                if a2 == 0 or "#%02x%02x%02x" % (r2, g2, b2) != fill:
                    break
                run += 1
            out.append(rect(ox + x * scale, oy + y * scale, run * scale, scale, fill))
            x += run
    return out


def board_mascots_svg():
    cells = []
    kofun = S.kofun_variant("smile")
    dochi = S.dochi_variant("idle")
    scale = 6
    for idx, (name, label) in enumerate(SCENES):
        x = (idx % 4) * W
        y = (idx // 4) * H
        cells.append(f'<g transform="translate({x} {y})">\n    {content_for(name)}\n  </g>')
        cells.append(rect(x + 6, y + 6, 126, 12, C["ink"], 0.62))
        cells.append(
            f'<text x="{x + 10}" y="{y + 16}" fill="{C["ice"]}" '
            f'font-family="monospace" font-size="8">{label}</text>'
        )
        cells += mascot_rects(kofun, x + 118, y + 86, scale)
        cells += mascot_rects(dochi, x + 178, y + 86, scale)
    return svg_doc(
        "background-board-mascots",
        "Kofun Friends cyberpunk background board with mascots",
        "\n  ".join(cells),
        W * 4,
        H * 3,
    )


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, label in SCENES:
        path = os.path.join(OUT, f"{name}.svg")
        with open(path, "w") as f:
            f.write(svg_doc(name, label, content_for(name)))
        print("wrote", os.path.relpath(path, ROOT))

    board = os.path.join(OUT, "background-board.svg")
    with open(board, "w") as f:
        f.write(board_svg())
    print("wrote", os.path.relpath(board, ROOT))

    board_mascots = os.path.join(OUT, "background-board-mascots.svg")
    with open(board_mascots, "w") as f:
        f.write(board_mascots_svg())
    print("wrote", os.path.relpath(board_mascots, ROOT))


if __name__ == "__main__":
    main()
