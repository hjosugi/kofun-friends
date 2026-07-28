<!-- i18n: language-switcher -->
[English](adding-assets.md) | [日本語](adding-assets.ja.md)

# Adding assets

## Steps

1. Put the original in `assets/<category>/`.
2. Add it to `catalog/manifest.json`.
3. Run `scripts/regen.sh`.
4. Commit `assets/` and `dist/` together.

## Rules

- File names are kebab-case.
- Scale pixel art with `"filter": "nearest"`.
- Always record a `license` for a new asset.
- For external material, keep the source URL and licence in the same directory.

## Example

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
