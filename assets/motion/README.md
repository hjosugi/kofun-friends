# motion — 動き・角度の検討素材

KOFUN/DOCHICKEN本体の正規スプライトとは別枠の、動き検討用アセットです。
`scripts/gen_motion_studies.py` が生成します。

- `gif/`: キャラごとの確認用GIF。
  - `*-motion-pack.gif`: bob / hop / dash / turn / wiggle をまとめて再生。
  - `*-turntable.gif`: front / side / back / side の角度確認。
- `sheets/`: 24x24 native pixel のフレームシート。
  - `*-motion-sheet.png`: 5行 x 6フレーム。行は bob, hop, dash, turn, wiggle。
  - `*-angle-strip.png`: front, right-ish, back-ish, left-ish。
- `board/motion-board.png`: 全キャラ・全モーションを一画面で見るためのコンタクトシート。

ここで作る差分は「候補」です。採用する動きが決まったら、必要なものだけ
`assets/<character>/` やアプリ側のアニメーション定義へ昇格します。
