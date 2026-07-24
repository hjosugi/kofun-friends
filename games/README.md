# Kofun Friends Game Lab

同じ素材を使い、7種類の軽量ゲームエンジン／フレームワークで
それぞれ違うミニゲームを実装した比較用ワークスペースです。

## 最初に1回だけ

リポジトリのルートで次を実行し、`dist/` の素材を各プロジェクトへ
コピーします。Pythonの標準ライブラリだけを使用します。

```bash
python3 games/sync_assets.py
```

生成された `assets/*.png` はGit管理されません。素材を更新した場合も
同じコマンドで上書きできます。

## ゲーム一覧

| 目的／技術 | ゲーム | 操作 | 起動 |
|---|---|---|---|
| Godot + GDScript | Kofun Courier | 矢印/WASD、Enter | Godot 4で `godot-gdscript/project.godot` を開く |
| raylib 6.0 + C | Mound Breaker | 左右/A・D、Space | `cmake -S raylib-c -B raylib-c/build && cmake --build raylib-c/build` |
| Defold + Lua | Haniwa Tap Patrol | クリック／タップ | Defoldで `defold-lua/game.project` を開く |
| LÖVE + Lua | Dochicken Sky Dodge | Space/↑、Enter | `love love2d-lua` |
| Phaser + TypeScript | Neon Kofun Dash | Space/↑/クリック | `cd phaser-typescript && npm install && npm run dev` |
| Macroquad + Rust | Kofun Orbit | WASD/矢印、Space、Enter | `cd macroquad-rust && cargo run --release` |
| Ebitengine + Go | Kofun Snake | WASD/矢印、Enter | `cd ebitengine-go && go run .` |

すべて1画面で完結し、スコア、失敗条件、リスタートを備えています。
高解像度3D、動画、音源は使わず、統合GPUや少ないメモリでも編集しやすい
小さな構成にしています。

## 推奨順

まず完成までの流れを体験するならGodot、PC負荷と構成の小ささを最優先する
ならraylib、ブラウザですぐ共有するならPhaserがおすすめです。その後、
使いたい言語に合わせてLua、Rust、Goのプロジェクトを比較できます。

## 素材ライセンス

同期される画像のライセンスは、リポジトリ直下の
[`LICENSE-ASSETS.md`](../LICENSE-ASSETS.md) と
[`catalog/manifest.json`](../catalog/manifest.json) に従います。
