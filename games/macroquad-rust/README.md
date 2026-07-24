# Kofun Orbit — Macroquad + Rust

古墳くんを操作し、四方から近づくドチキンさんを自動照準弾で退けながら
30秒間生存するアリーナゲームです。

```bash
python3 games/sync_assets.py
cd games/macroquad-rust
cargo run --release
```

WASD／矢印で移動、Space長押しで最も近い敵へ射撃、Enterで再開します。
依存はMacroquadだけです。
