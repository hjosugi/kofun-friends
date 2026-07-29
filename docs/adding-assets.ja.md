<!-- i18n: language-switcher -->
[English](adding-assets.md) | [日本語](adding-assets.ja.md)

# 素材追加

## 手順

1. 原本を `assets/<category>/` に置きます。
2. `catalog/manifest.json` に追加します。
3. `scripts/regen.sh` を実行します。
4. `assets/` と `dist/` を一緒にコミットします。

## ルール

- ファイル名はケバブケース（kebab-case）にします。
- ドット絵の拡大は `"filter": "nearest"` を指定します。
- 新規素材には必ず `license` を記載します。
- 外部素材は元のURLとライセンス情報を同じディレクトリに残します。

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