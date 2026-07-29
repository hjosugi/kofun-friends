# Kofun Snake — Ebitengine + Go

古墳くんの列を伸ばしながら埴輪を15個集めるグリッドゲームです。壁または
自分の列に当たると終了します。

```bash
python3 games/sync_assets.py
cd games/ebitengine-go
go run .
```

WASD／矢印で方向転換、Enterで再開します。画像は`go:embed`で実行ファイルへ
埋め込まれ、WindowsでもCコンパイラは不要です。
