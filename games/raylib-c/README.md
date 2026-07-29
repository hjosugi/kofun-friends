# Mound Breaker — raylib 6.0 + C

古墳くんをパドルにした軽量なブロック崩しです。左右キーまたはA/Dで移動し、
50個のブロックをすべて壊すとクリアです。

```bash
python3 games/sync_assets.py
cmake -S games/raylib-c -B games/raylib-c/build
cmake --build games/raylib-c/build
./games/raylib-c/build/mound_breaker
```

raylib 6.0が未導入なら、CMakeに`-DKOFUN_FETCH_RAYLIB=ON`を追加すると
ソースを取得してビルドできます。再開はSpaceまたはEnterです。
