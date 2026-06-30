# Contributing

## 素材

1. 原本を `assets/` に置く。
2. `catalog/manifest.json` に登録する。
3. `scripts/regen.sh` を実行する。
4. `assets/` と `dist/` を一緒にコミットする。

詳しくは [docs/adding-assets.md](docs/adding-assets.md)。

## converter

```bash
cargo fmt --manifest-path tools/converter/Cargo.toml
cargo test --manifest-path tools/converter/Cargo.toml
```
