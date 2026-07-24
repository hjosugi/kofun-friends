#!/usr/bin/env python3
"""Copy repository assets into each runnable game project."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / "games"

PROJECT_ASSETS: dict[str, dict[str, str]] = {
    "godot-gdscript": {
        "background.png": "dist/backgrounds/neon-alley.png",
        "kofun.png": "dist/kofun/kofun-kun-idle_96.png",
        "dochicken.png": "dist/dochicken/dochicken-san-idle_96.png",
        "haniwa.png": "dist/emoji/haniwa_64.png",
    },
    "raylib-c": {
        "background.png": "dist/backgrounds/arcade-market.png",
        "kofun.png": "dist/kofun/kofun-kun-smile_96.png",
    },
    "defold-lua": {
        "haniwa.png": "dist/emoji/haniwa_64.png",
        "dochicken.png": "dist/dochicken/dochicken-san-peck_96.png",
    },
    "love2d-lua": {
        "background.png": "dist/backgrounds/rain-skyline.png",
        "kofun.png": "dist/kofun/kofun-kun-idle_96.png",
        "dochicken.png": "dist/dochicken/dochicken-san-idle_96.png",
    },
    "phaser-typescript/public": {
        "background.png": "dist/backgrounds/rooftop-antennas.png",
        "kofun.png": "dist/kofun/kofun-kun-smile_96.png",
        "dochicken.png": "dist/dochicken/dochicken-san-idle_96.png",
    },
    "macroquad-rust": {
        "background.png": "dist/backgrounds/data-shrine.png",
        "kofun.png": "dist/kofun/kofun-kun-idle_96.png",
        "dochicken.png": "dist/dochicken/dochicken-san-idle_96.png",
    },
    "ebitengine-go": {
        "kofun.png": "dist/kofun/kofun-kun-idle_96.png",
        "haniwa.png": "dist/emoji/haniwa_64.png",
    },
}


def main() -> None:
    copied = 0
    for project, files in PROJECT_ASSETS.items():
        destination = GAMES / project / "assets"
        destination.mkdir(parents=True, exist_ok=True)
        for target_name, source_name in files.items():
            source = ROOT / source_name
            if not source.is_file():
                raise FileNotFoundError(f"Missing source asset: {source}")
            shutil.copy2(source, destination / target_name)
            copied += 1
    print(f"Synced {copied} assets into {len(PROJECT_ASSETS)} game projects.")


if __name__ == "__main__":
    main()
