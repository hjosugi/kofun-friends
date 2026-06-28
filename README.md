# kofun-friends 🏯🐔

古墳（kofun）や **ドチキンさん** などのキャラクター素材を一元管理するアセットリポジトリです。
SVG / PNG / GIF・絵文字セット・マウスカーソルなどを置き、**Rust製ネイティブ converter** で
リサイズ・フォーマット変換・SVGラスタライズ・複数サイズ書き出しを行います。

> 関連: [hjosugi/hjosugi-hub](https://github.com/hjosugi/hjosugi-hub)

---

## 何ができる？

| やりたいこと | コマンド |
| --- | --- |
| SVG を PNG にラスタライズ | `kofun-convert rasterize foo.svg --width 512` |
| 画像のサイズ変換 | `kofun-convert resize foo.png --width 128` |
| フォーマット変換 (png↔webp↔jpg…) | `kofun-convert convert foo.png --to webp` |
| 絵文字/アイコンセットを一括書き出し | `kofun-convert sizes foo.svg --sizes 16,32,48,128` |
| GIFアニメをサイズ変換（フレーム保持） | `kofun-convert resize anim.gif --width 48` |
| カタログから全部生成 | `kofun-convert batch` |

---

## ディレクトリ構成

```
kofun-friends/
├── assets/                 # ★ オリジナル素材（source of truth）のみを置く
│   ├── kofun/              #   カテゴリごと
│   │   ├── svg/            #     ← まずここに SVG を置くのが基本
│   │   ├── png/            #     手描き/撮影など SVG 由来でないラスタ原本
│   │   ├── gif/            #     アニメGIF原本
│   │   └── raw/            #     .ai/.psd/.kra など編集用ソース
│   ├── dochicken/          #   ドチキンさん
│   ├── emoji/              #   絵文字セット (svg/png/gif)
│   ├── cursors/            #   マウスカーソル (svg/png/ani)
│   └── icons/              #   汎用アイコン (svg/png)
│
├── dist/                   # ★ converter が生成した配布用の成果物（再生成可能）
│   ├── kofun/  dochicken/  emoji/  cursors/  icons/
│
├── catalog/                # 素材カタログ（メタデータ・生成定義）
│   ├── manifest.json       #   どの素材をどう書き出すかの宣言
│   └── manifest.schema.json
│
├── tools/converter/        # ★ Rust製ネイティブ converter (kofun-convert)
│   ├── src/  Cargo.toml  README.md
│
├── scripts/                # 補助スクリプト（再生成・新規素材追加など）
├── docs/                   # ドキュメント
└── .github/workflows/      # CI（converterのビルド + dist再現性チェック）
```

設計方針（アセット管理のベストプラクティス）:

1. **ソースと成果物を分離** — 人間が編集する原本は `assets/`、機械生成物は `dist/`。
2. **SVG を第一級ソースに** — ベクターで持ち、必要なサイズ/形式は都度生成。
3. **カタログ駆動** — 何をどう書き出すかを `catalog/manifest.json` に集約し再現可能に。
4. **ライセンス明記** — 各素材に `license` を付与（未指定は CI が警告）。
5. **dist は再生成可能** — `scripts/regen.sh` でいつでも `assets/` から作り直せる。

---

## クイックスタート

```bash
# 1. converter をビルド
cd tools/converter
cargo build --release        # → target/release/kofun-convert

# 2. リポジトリ直下でカタログから一括生成
cd ../..
./tools/converter/target/release/kofun-convert batch

# あるいは個別に
kofun-convert rasterize assets/kofun/svg/kofun-keyhole.svg --width 512
kofun-convert sizes     assets/dochicken/svg/dochicken.svg --sizes 16,32,64,128 --outdir dist/dochicken
```

再生成はワンコマンド:

```bash
scripts/regen.sh           # build → dist/ をまるごと作り直す
```

---

## 新しい素材を追加する流れ

1. 原本（SVG推奨）を `assets/<カテゴリ>/svg/` に置く。
2. `catalog/manifest.json` の `assets[]` にエントリを追加（`license` 必須）。
3. `scripts/regen.sh` を実行して `dist/` を更新。
4. コミット（`assets/` と `dist/` の両方）。

詳細は [docs/adding-assets.md](docs/adding-assets.md) と
[tools/converter/README.md](tools/converter/README.md) を参照。

---

## ライセンス

- **素材 (`assets/`, `dist/`)**: 既定で [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)（各素材の `catalog/manifest.json` の `license` が正）。
- **converter のコード (`tools/`)**: [MIT](tools/converter/LICENSE)。
