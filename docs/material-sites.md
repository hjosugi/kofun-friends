# 素材サイト・参照元メモ

サイバーパンク背景・ドット絵キャラの色や雰囲気を決めるための参照元です。
素材をそのまま入れる場合は、必ず配布元ページと同梱ライセンスを保存してから使います。

## 現在使っているもの

| サイト | 用途 | ライセンス確認 | このリポジトリでの扱い |
| --- | --- | --- | --- |
| [OpenGameArt: Warped City](https://opengameart.org/content/warped-city) | サイバーパンク背景・看板・小物のCC0参照素材 | 同梱 `LICENSE.txt` に public domain / commercial OK / credit not required と記載 | `assets/backgrounds/cc0/warped-city/` にPNGのみ保存 |
| [OpenGameArt: Skyline Background](https://opengameart.org/content/skyline-background) | 夜景・水面・空気感のCC0参照素材 | 同梱 `LICENSE.txt` に public domain (CC0) と記載 | `assets/backgrounds/cc0/skyline-background/` にPNGレイヤーとプレビューのみ保存 |
| [Lospec: Cyberpunk Neon City](https://lospec.com/palette-list/cyberpunk-neon-city) | 色作りの参照パレット | パレットページのライセンス表示を確認して使う | 絵はコピーせず、黒紫/濃紺/シアン/マゼンタ/酸性ライム/黄色の配色方針として使う |

## 探索に使うもの

| サイト | 使い方 | 注意 |
| --- | --- | --- |
| Google 画像検索 | 方向性、シルエット、色の傾向を見る | 検索結果画像は素材として使わない。必ず元サイトへ行き、ライセンスを確認する |
| OpenGameArt | `cyberpunk`, `pixel art`, `city`, `character`, `CC0` などで素材を探す | OGA内でもライセンスは作品ごとに違う。CC0以外は条件を読んで `catalog/manifest.json` に明記する |
| Lospec Palette List | パレット候補を探す | パレット名・作者・ライセンスをメモする。キャラ絵やサンプル画像はコピーしない |
| itch.io asset packs | 候補探し | free と書かれていても商用可/改変可/再配布可は別。LICENSEがないものは入れない |
| sprite sheet / animation packs | 歩き・待機・ジャンプなどの差分発想を見る | フレーム構成の参考に留める。素材を入れる場合はCC0または再配布可が明記されたものだけにする |

## 入れる前のチェックリスト

1. 配布元URLを `SOURCE.md` に保存する。
2. ライセンス本文を `LICENSE.txt` などで同じディレクトリに保存する。
3. `catalog/manifest.json` の `license` を実際のライセンス名に合わせる。
4. CC0以外は、クレジット表記・再配布・改変・商用利用の条件をREADMEかSOURCEに書く。
5. Google画像検索、Pinterest、SNS投稿、個人ブログのスクリーンショットは直接素材にしない。
6. 使わない音声、PSD、デモコード、OSメタデータは取り込まない。

## 色方針

今回のサイバーパンク寄せでは、自然色をそのまま置くのをやめて、次の役割で色を使います。

| 役割 | 色 |
| --- | --- |
| 背景の黒 | `#0a0a14` |
| 影・建物 | `#12101e`, `#1c1830`, `#0d2240` |
| 発光シアン | `#00ffff`, `#00ccff` |
| 発光マゼンタ | `#ff0090`, `#ff44cc` |
| アクセント | `#ccff00`, `#ffe040`, `#ff6600` |

キャラや背景を追加するときも、まず暗いベースで形を作り、発光色は輪郭・目・看板・小さい面積に絞ります。
