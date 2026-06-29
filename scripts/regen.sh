#!/usr/bin/env bash
# Rebuild the converter and regenerate the entire dist/ tree from assets/ + catalog/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo ">> regenerating source pixel art (mascots + emoji/icons/cursors)…"
python3 scripts/gen_sprites.py
python3 scripts/gen_pixel_svgs.py
python3 scripts/gen_lineup.py

echo ">> building kofun-convert (release)…"
cargo build --release --manifest-path tools/converter/Cargo.toml

BIN="$(cargo metadata --no-deps --format-version 1 \
  --manifest-path tools/converter/Cargo.toml \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["target_directory"])')/release/kofun-convert"

echo ">> cleaning dist/ (preserving .gitkeep)…"
find dist -type f ! -name '.gitkeep' -delete 2>/dev/null || true

echo ">> regenerating dist/ from catalog/manifest.json…"
"$BIN" batch --manifest catalog/manifest.json

echo ">> done. dist/ contents:"
find dist -type f | sort
