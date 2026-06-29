# kofun-friends 🏯🐔

**古墳くん (Kofun-kun)** や **ドチキンさん (Dochicken-san)** などのキャラクター素材を一元管理する
アセットリポジトリです。ドット絵スプライト・SVG・PNG・GIF・絵文字セット・マウスカーソルなどを置き、
**Rust製ネイティブ converter** でリサイズ・フォーマット変換・SVGラスタライズ・複数サイズ書き出し・
**Windowsカーソル (.cur/.ani) 書き出し** を行います。

主役キャラ（[本家 hjosugi-hub](https://github.com/hjosugi/hjosugi-hub) に準拠）:

- **古墳くん** 🟢 — 前方後円墳の姿をしたミドリムシ好きの子ども。ドット絵 (idle/blink/smile/munch)
- **ドチキンさん** 🐔 — 鶏の姿をした埴輪。古墳くんの遊び友達。ドット絵 (idle/blink/peck)

> 関連: [hjosugi/hjosugi-hub](https://github.com/hjosugi/hjosugi-hub)

---

## 何ができる？

| やりたいこと | コマンド |
| --- | --- |
| SVG を PNG にラスタライズ | `kofun-convert rasterize foo.svg --width 512` |
| 画像のサイズ変換 | `kofun-convert resize foo.png --width 128` |
| フォーマット変換 (png↔webp↔jpg…) | `kofun-convert convert foo.png --to webp` |
| 絵文字/アイコンセットを一括書き出し | `kofun-convert sizes foo.svg --sizes 16,32,48,128` |
| ドット絵をクリスプに拡大 | `kofun-convert sizes pixel.png --sizes 96,192 --filter nearest` |
| GIFアニメをサイズ変換（フレーム保持） | `kofun-convert resize anim.gif --width 48` |
| Windows静的カーソル (.cur) | `kofun-convert cur pointer.svg --hotspot-x 4 --hotspot-y 2` |
| Windowsアニメカーソル (.ani) | `kofun-convert ani kofun-kun.gif --size 48` |
| カタログから全部生成 | `kofun-convert batch` |

---

## ディレクトリ構成

```
kofun-friends/
├── assets/                 # ★ オリジナル素材（source of truth）のみを置く
│   ├── kofun/              #   古墳くん
│   │   ├── pixel/          #     ドット絵スプライト原本 (PNG, 16x16・本家準拠)
│   │   ├── svg/            #     ベクター原本
│   │   ├── png/            #     SVG由来でないラスタ原本
│   │   ├── gif/            #     アニメGIF原本
│   │   └── raw/            #     .ai/.psd/.kra など編集用ソース
│   ├── dochicken/          #   ドチキンさん（pixel/svg/png/gif/raw）
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
├── scripts/                # 補助スクリプト
│   ├── regen.sh            #   dist/ をまるごと再生成（原本生成→converter）
│   ├── gen_sprites.py      #   マスコットのドット絵生成（16x16グリッド→PNG/GIF）
│   └── gen_pixel_svgs.py   #   emoji/icons/cursors のドット絵SVG生成
├── docs/                   # ドキュメント
└── .github/workflows/      # CI（converterのビルド + dist再現性チェック）
```

設計方針（アセット管理のベストプラクティス）:

1. **ソースと成果物を分離** — 人間が編集する原本は `assets/`、機械生成物は `dist/`。
2. **全素材がドット絵 (ゲーミング/サイバーパンク調)** — マスコットは native解像度PNG
   （`--filter nearest` でクリスプに拡大）、emoji/icons/cursors は `shape-rendering="crispEdges"`
   の矩形ベースSVG。どちらも 16x16 グリッドで、古墳くん/ドチキンさんは本家 hjosugi-hub の
   定義を1:1移植。生成は [scripts/gen_sprites.py](scripts/gen_sprites.py)（マスコット）と
   [scripts/gen_pixel_svgs.py](scripts/gen_pixel_svgs.py)（emoji/icons/cursors）。
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
