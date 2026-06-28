# kofun-convert

`kofun-friends` 用のネイティブ素材コンバータ。Rust 製・依存ライブラリも純Rust
（[`image`](https://crates.io/crates/image) + [`resvg`](https://crates.io/crates/resvg)）
なので、ImageMagick 等の外部バイナリ無しで単体動作します。

## ビルド

```bash
cargo build --release        # → target/release/kofun-convert
# 任意: PATH に入れる
cargo install --path .
```

## サブコマンド

### `rasterize` — SVG → PNG
```bash
kofun-convert rasterize in.svg --width 512            # 幅512、高さは比率維持
kofun-convert rasterize in.svg --width 256 --height 256
kofun-convert rasterize in.svg --scale 2.0 -o out.png
```

### `resize` — ラスタ画像のサイズ変換（GIFアニメ対応）
```bash
kofun-convert resize in.png --width 128               # 比率維持
kofun-convert resize in.png --width 128 --height 128 --exact   # 引き伸ばし
kofun-convert resize in.png --scale 0.5
kofun-convert resize anim.gif --width 48              # 全フレームをリサイズして再エンコード
kofun-convert resize in.png --width 64 --filter nearest        # ドット絵向け
```

### `convert` — フォーマット変換
```bash
kofun-convert convert in.png --to webp
kofun-convert convert in.png --to jpeg --quality 85
kofun-convert convert in.png --to ico                 # 256px以下に自動縮小
```
対応出力: `png` `jpeg` `webp` `gif` `bmp` `tiff` `ico`

### `sizes` — 複数サイズ一括書き出し（絵文字/アイコン/カーソルセット）
```bash
kofun-convert sizes in.svg  --sizes 16,32,48,128 --outdir dist/emoji
kofun-convert sizes in.png  --sizes 16,32,48     --to png --filter lanczos3
```
SVG入力なら各サイズを**ベクターから直接レンダリング**するので、拡大時もくっきり。

### `info` — メタデータ表示
```bash
kofun-convert info in.png    # format / size / bytes / frames(GIF)
kofun-convert info in.svg    # intrinsic size
```

### `batch` — カタログ駆動で一括生成
```bash
kofun-convert batch                          # catalog/manifest.json を実行
kofun-convert batch --manifest other.json
kofun-convert batch --dry-run                # 生成計画だけ表示
```

## リサンプリングフィルタ

`--filter` で指定: `nearest`（ドット絵）, `triangle`, `catmull-rom`, `gaussian`,
`lanczos3`（既定・高品質）。

## マニフェスト形式

`catalog/manifest.json` のスキーマは [`catalog/manifest.schema.json`](../../catalog/manifest.schema.json) を参照。
各 `op` は `resize` / `convert` / `rasterize` / `sizes` のいずれか。

## 設計メモ

- SVGは `usvg` でパース → `resvg`/`tiny-skia` でレンダリング。テキスト要素はシステムフォントを読み込んで描画。
- GIFアニメは `image` の `GifDecoder`/`GifEncoder` で全フレームを処理（1フレームなら静止画として扱う）。
- `batch` は `rayon` で素材を並列処理。
