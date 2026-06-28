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
| `sizes` | 複数サイズ一括 | `sizes` (配列), `format` |
| `resize` | ラスタ/GIFのサイズ変換 | `width` / `height` / `scale` / `exact` / `format` |
| `convert` | フォーマット変換 | `format`, `quality` |

スキーマ: [`catalog/manifest.schema.json`](../catalog/manifest.schema.json)

## 3. 生成 & コミット

```bash
scripts/regen.sh        # dist/ を再生成
git add assets dist catalog
git commit -m "add: wahaha emoji"
```

## マウスカーソルについて

- 編集用ソースは `assets/cursors/svg/`。
- Web 用は `dist/cursors/*.png`（`cursor: url(...)` で使用、ホットスポット小さめに）。
- Windows の `.ani`/`.cur` は専用ツールが必要なため、現状は `assets/cursors/ani/` に手動で置きます
  （converter は静的ラスタ/SVG変換まで担当）。
