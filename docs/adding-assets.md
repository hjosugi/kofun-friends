# 素材追加

## 手順

1. 原本を `assets/<category>/` に置く。
2. `catalog/manifest.json` に追加する。
3. `scripts/regen.sh` を実行する。
4. `assets/` と `dist/` を一緒にコミットする。

## ルール

- ファイル名は kebab-case。
- ドット絵の拡大は `"filter": "nearest"`。
- 新規素材は `license` を必ず書く。
- 外部素材は元URLとライセンスを同じディレクトリに残す。

## 例

```json
{
  "source": "assets/emoji/svg/example.svg",
  "category": "emoji",
  "tags": ["emoji"],
  "license": "CC-BY-4.0",
  "outputs": [
    { "op": "sizes", "sizes": [32, 64, 128, 256], "format": "png", "outdir": "dist/emoji" }
  ]
}
```
