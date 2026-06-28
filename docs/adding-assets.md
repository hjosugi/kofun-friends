# 新しい素材を追加する

## 1. 原本を置く

ベクター（SVG）を第一級ソースとして扱います。カテゴリ配下の `svg/` に置いてください。

```
assets/kofun/svg/my-kofun.svg
assets/emoji/svg/wahaha.svg
assets/cursors/svg/pointer.svg
```

SVG 化できない素材（写真・手描き）は `png/` `gif/`、編集用ファイル（.psd/.ai/.kra）は `raw/` に。

### 命名規則
- 小文字 + ハイフン区切り（kebab-case）: `kofun-keyhole.svg`
- サイズ違いの生成物は converter が `_<size>` を付けます: `kofun-keyhole_128.png`
- バリアント: `dochicken-wink.svg`, `dochicken-angry.svg`

## 2. カタログに登録

[`catalog/manifest.json`](../catalog/manifest.json) の `assets[]` に追記します（`license` は必須）。

```json
{
  "source": "assets/emoji/svg/wahaha.svg",
  "category": "emoji",
  "tags": ["emoji", "laugh"],
  "license": "CC-BY-4.0",
  "outputs": [
    { "op": "sizes", "sizes": [32, 64, 128], "format": "png", "outdir": "dist/emoji" }
  ]
}
```

利用できる `op`:

| op | 用途 | 主なフィールド |
| --- | --- | --- |
| `rasterize` | SVG→PNG 1枚 | `width` / `height` / `scale` |
| `sizes` | 複数サイズ一括 | `sizes` (配列), `format`, `filter` |
| `resize` | ラスタ/GIFのサイズ変換 | `width` / `height` / `scale` / `exact` / `format` / `filter` |
| `convert` | フォーマット変換 | `format`, `quality` |
| `cur` | Windows静的カーソル | `sizes`, `hotspot_x`, `hotspot_y` |
| `ani` | Windowsアニメカーソル(GIFから) | `size`, `hotspot_x`, `hotspot_y`, `fps` |

`filter` は `nearest`（ドット絵）/ `lanczos3`（既定・高品質）など。

スキーマ: [`catalog/manifest.schema.json`](../catalog/manifest.schema.json)

## ドット絵スプライトを追加する

古墳くん/ドチキンさんのようなドット絵は [scripts/gen_sprites.py](../scripts/gen_sprites.py)
でASCIIグリッド + パレットとして定義し、native解像度PNG（24×24）を
`assets/<char>/pixel/` に生成します。

```bash
python3 scripts/gen_sprites.py          # assets/*/pixel/*.png を生成
KOFUN_PREVIEW=1 python3 scripts/gen_sprites.py   # 拡大プレビューも出力
```

manifest では `nearest` フィルタで整数倍に拡大します:

```json
{ "op": "sizes", "sizes": [24, 48, 96, 192], "format": "png", "filter": "nearest", "outdir": "dist/kofun" }
```

## 3. 生成 & コミット

```bash
scripts/regen.sh        # dist/ を再生成
git add assets dist catalog
git commit -m "add: wahaha emoji"
```

## マウスカーソルについて

- 編集用ソースは `assets/cursors/svg/`。
- Web 用は `dist/cursors/*.png`（`cursor: url(...)` で使用、ホットスポット小さめに）。
- **Windows 静的カーソル `.cur`** は `cur` op で生成（ホットスポット指定可）:
  ```json
  { "op": "cur", "sizes": [32, 48], "hotspot_x": 4, "hotspot_y": 2, "outdir": "dist/cursors" }
  ```
- **Windows アニメカーソル `.ani`** はアニメGIFソースから `ani` op で生成:
  ```json
  { "op": "ani", "size": 48, "hotspot_x": 24, "hotspot_y": 24, "outdir": "dist/cursors" }
  ```
