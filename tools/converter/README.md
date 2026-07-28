<!-- i18n: language-switcher -->
[English](README.md) | [日本語](README.ja.md)

# kofun-convert

The asset converter for `kofun-friends`.

## Build

```bash
cargo build --release
```

## Commands you will use often

```bash
# build everything from catalog/manifest.json
kofun-convert batch

# SVG -> PNG
kofun-convert rasterize in.svg --width 512

# resize a PNG/GIF. Every frame of a GIF is kept
kofun-convert resize in.gif --width 96 --filter nearest

# several sizes at once
kofun-convert sizes in.svg --sizes 32,64,128 --outdir dist/emoji

# Windows cursor
kofun-convert cur pointer.svg --sizes 32,48 --hotspot-x 1 --hotspot-y 1
kofun-convert ani anim.gif --size 48 --hotspot-x 24 --hotspot-y 24

# show information
kofun-convert info in.png
```

## Test

```bash
cargo test
```
