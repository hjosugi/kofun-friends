# GitHub Issue → Daimon 自動投稿

`.github/workflows/post-issue-to-daimon.yml` は、対象となるGitHub Issueを
Daimonの投稿へ変換します。Issue本文は `$GITHUB_EVENT_PATH` のJSONからPythonで
読み取るため、タイトルや本文がシェルコマンドとして評価されることはありません。

## 投稿対象

次のどれかを満たすIssueだけを投稿します。

- 作成者の `author_association` が `OWNER`、`MEMBER`、`COLLABORATOR`
- Issue作成後、メンテナーが `daimon-post` ラベルを付けた
- メンテナーがActions画面からIssue番号を指定して手動実行した

Pull Request、Issue編集、コメント追加は投稿対象外です。外部ユーザーのIssueは、
内容を確認してから `daimon-post` ラベルを付けてください。ラベル名はRepository
Variable `DAIMON_POST_LABEL` で変更できます。

Issue作成時からラベルが存在しても、外部ユーザーの `opened` イベントでは投稿しません。
メンテナーによる `labeled` イベントか手動実行が必要です。

## Environment設定

Settings → Environments で `daimon-production` を作成し、deployment branchを
default branch（`main`）だけに制限します。Daimon credentialはRepository Secretではなく、
このEnvironmentのSecretとして設定してください。これにより、別branchから変更した
`workflow_dispatch` でcredentialを読み出す経路を閉じます。

EnvironmentのSecrets and variablesに次を設定します。

| 種類 | 名前 | 値 |
| --- | --- | --- |
| Environment Variable | `DAIMON_API_URL` | Daimon APIのHTTPS base URL |
| Environment Secret | `DAIMON_ACCOUNT` | 自動投稿専用Daimonアカウントのemailまたはusername |
| Environment Secret | `DAIMON_PASSWORD` | 自動投稿専用アカウントのpassword |
| Environment Variable | `DAIMON_POST_LABEL` | 任意。既定は `daimon-post` |
| Environment Variable | `DAIMON_IDEMPOTENCY_SUPPORTED` | Daimonが冪等キーを保証した後だけ `true` |

固定セッショントークンは保存しません。実行ごとに `/auth/login` で短期セッションを
作り、`/posts/` の完了後に `/auth/logout` します。専用アカウントには自動投稿以外の
用途を持たせず、passwordを定期的にローテーションしてください。

## 重複防止

投稿には次の `Idempotency-Key` を送ります。

```text
github:<owner>/<repository>:issue:<GitHub issue id>
```

成功後、GitHub Actions botが同じキーを含む配送記録コメントをIssueへ追加します。
workflow再実行、`opened` と `labeled` の競合、手動再送では、この記録を確認して
既送信ならスキップします。他ユーザーが同じ文字列をコメントしても配送記録として
扱いません。

現在のDaimon APIが `Idempotency-Key` をDBのunique制約で保証していない間は、投稿
POSTを自動再試行しません。APIが投稿を保存した直後、配送記録コメントより前に実行
環境が停止した場合だけは重複の可能性が残ります。Daimon側で次を実装・deployした後、
`DAIMON_IDEMPOTENCY_SUPPORTED=true` にしてください。

- `source=github` と `external_id`（または同等の冪等キー）を投稿と一緒に保存する
- キーにunique制約を置く
- 同じキーの再要求には既存post IDを返す

`true` のときだけ、一時的な接続エラー、HTTP 429、HTTP 5xxに対して投稿POSTも指数
バックオフで再試行します。

## 手動確認・再送

Actions → **Post issue to Daimon** → **Run workflow** からIssue番号を指定します。

1. 最初は `dry_run=true` で対象判定と整形だけを確認する
2. Actions summaryにIssue、文字数、POV数が表示されることを確認する
3. `dry_run=false` で実行する

すでに配送記録があるIssueは安全にスキップされます。前回がDaimon投稿前に失敗した
場合は記録がないため再送されます。

## 障害対応

- `Missing required live configuration`: Variable / Secretの未設定を確認する
- Daimon loginが401/4xx: 専用アカウントとpasswordを確認・更新する
- Daimon postが429/5xx: 冪等保証が有効なら自動再試行される。無効ならDaimon側の
  投稿有無を確認してから手動実行する
- `receipt failed`: Actions summaryのpost IDを確認する。Daimon側で同じ投稿が存在する
  場合、冪等保証なしで安易に再実行しない

ローカルテスト:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.12
```
