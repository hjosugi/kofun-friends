<!-- i18n: language-switcher -->
[English](README.md) | [日本語](README.ja.md)

# kofun-convert

`kofun-friends` 用の素材コンバータです。

## ビルド

```bash
cargo build --release
```

## よく使うコマンド

```bash
# catalog/manifest.json から全部作る
kofun-convert batch

# SVG -> PNG
kofun-convert rasterize in.svg --width 512

# PNG/GIF のリサイズ。GIFは全フレームを保持
kofun-convert resize in.gif --width 96 --filter nearest

# 複数サイズ
kofun-convert sizes in.svg --sizes 32,64,128 --outdir dist/emoji

# Windowsカーソル
kofun-convert cur pointer.svg --sizes 32,48 --hotspot-x 1 --hotspot-y 1
kofun-convert ani anim.gif --size 48 --hotspot-x 24 --hotspot-y 24

# 情報表示
kofun-convert info in.png
```

## テスト

```bash
cargo test
```