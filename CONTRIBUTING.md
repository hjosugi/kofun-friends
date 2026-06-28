# Contributing to kofun-friends

## 素材を追加・変更する

[docs/adding-assets.md](docs/adding-assets.md) を参照。要点:

1. 原本は `assets/`（SVG優先）。生成物は触らず `dist/` は `scripts/regen.sh` で作る。
2. `catalog/manifest.json` に `license` 付きで登録する。
3. PR 前に `scripts/regen.sh` を実行し、`assets/` と `dist/` を揃えてコミット。

## converter を変更する

```bash
cd tools/converter
cargo fmt
cargo clippy --all-targets -- -D warnings
cargo build --release
```

## チェックリスト

- [ ] 新規素材に `license` を付けた
- [ ] `scripts/regen.sh` を実行し `dist/` が最新
- [ ] ファイル名は kebab-case
- [ ] 大きなバイナリ原本（>5MB）は必要性を検討（`raw/` 行き、または別途LFS）

## コミットメッセージ

`add:` / `update:` / `fix:` / `tool:` などの接頭辞を推奨。
