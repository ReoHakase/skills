# Projectビューの設定例

GitHub Projectsのビューには説明文欄がないため、ビューの目的、フィルター、運用規則をこのファイルに保存する。

ビュー名、レイアウト、フィルターの機械可読な正本は `../../project-views.json` である。対象リポジトリへコピーした後は、この文書を人間向けの正本として残し、作成時のJSONとの不一致を作らない。

# Project運用設定

```text
タイムゾーン: UTC
稼働曜日: 月-金
休日: なし
Effort単位: ideal-hours
実装1枠・1稼働日あたりの有効Effort: 4
Agent枠上限: 1
作業環境枠上限: 1
レビューWIP上限: 1
重いCI・共有環境WIP上限: 1
マージ待ちWIP上限: 1
レビュー予備日: 1稼働日
重いCI予備日: 1稼働日
マージ予備日: 1稼働日
```

実装WIPは `min(Agent枠上限, 作業環境枠上限)` で導出し、未設定の枠とWIP上限は各1として扱う。Effortは実装、直接確認、テスト、ドキュメント、通常のレビュー修正を含み、待ち時間を含めない。`epic` はEffortを持たず、末端Issueだけを合計する。Sizeは順序尺度なので合計しない。

# Projectアイテムとフィールドの正本

標準ビューのProjectアイテムはIssueを主体とする。PRを別のProjectアイテムとして管理せず、Issueの組み込み列 `Linked pull requests` と `Reviewers` から関連PRとレビュー状況を読む。承認、必須ステータスチェック、マージ可否の詳細はPR自体で確認する。

組織所有リポジトリでは、導入前に組織のIssue TypesとIssue Fieldsを検出する。同じ意味と値域を持つフィールドがある場合はそれを正本とし、同義のProject独自フィールドを作らない。個人所有ProjectではProject独自フィールドを正本とする。

# 作成APIとUIの分担

API版 `2026-03-10` のREST APIによるProjectビュー作成で設定するのは、ビュー名、`layout`、`filter`、`visible_fields` である。`visible_fields` は `table` と `board` でのみ指定でき、`roadmap` では指定できない。表示フィールドは名前ではなくフィールドIDを渡す。

グループ化、並び替え、ボードの列、ロードマップの日付フィールドと表示フィールドは、作成後にGitHubのUIで設定する。REST APIの作成要求にグループ化や並び替えを混ぜない。

参照: <https://docs.github.com/en/rest/projects/views?apiVersion=2026-03-10>

# かんばん

目的:

- 全体の進捗と、`ready`、`in-progress`、`in-review`、`blocked` の詰まりを日次で確認する。
- 作業投入、レビュー待ち、阻害要因解除の入口にする。

REST APIで設定:

- `layout`: `board`
- `filter`: `is:issue is:open status:inbox,triaged,ready,in-progress,in-review,blocked`
- `visible_fields`: Typeの正本、Scopeの正本、Priority、Size、Effort、Estimate Confidence、Complexity、Risk、Agent Tier、Agent Run、Assignees、Reviewer Owner、Branch、Actual Start、Linked pull requests、Reviewers

UIで後設定:

- 列: Status
- 並び替え: Priorityの降順、Riskの降順、更新日時の昇順

運用規則:

- `ready` に置くのは、受け入れ条件、非スコープ、確認手順、未解決の阻害要因がないことを確認済みの実行対象末端Issueだけにする。
- Issue間の依存関係はIssue自体で確認する。`blocked by` と `blocking` を表示フィールドやフィルターとして扱わない。
- 実装WIPが上限なら新しい作業権を取得しない。レビュー、重いCI・共有環境、マージ待ちの下流WIPも確認する。
- `in-review` では `Linked pull requests` と `Reviewers` からPRを開き、本文、レビュー、チェックを確認する。
- `done` と `canceled` は通常表示しない。

# WBS/ロードマップ

目的:

- WBS/Gantt相当の計画表示として使う。
- 計画開始日と計画終了目標日を確認する。
- 構造と順序はIssueの親子関係と依存関係から読む。

REST APIで設定:

- `layout`: `roadmap`
- `filter`: `is:issue -no:"Forecast Start" -no:"Forecast End" status:triaged,ready,in-progress,in-review,blocked,done`
- `visible_fields`: 指定しない。`roadmap` は作成APIの `visible_fields` 対象外

UIで後設定:

- 日付フィールド: Forecast Start、Forecast End
- グループ化: Scopeの正本
- 並び替え: Forecast Startの昇順、Forecast Endの昇順、Priorityの降順
- 表示フィールド: Typeの正本、Scopeの正本、Priority、Effort、Estimate Confidence、Risk、Agent Tier、Forecast Start、Forecast End、Milestone、Linked pull requests

運用規則:

- Milestoneの期日を先に決め、その期限目標からForecast StartとForecast Endを組む。
- 親IssueのForecastは子Issue群を包む期間とし、子Issueと重なってよい。
- 直列依存する末端Issue同士ではForecastを重ねない。後続Issueはすべての前段IssueのForecast Endより後の稼働日に開始する。
- Issue間の親子関係と依存関係はIssue自体で確認し、ビューの表示フィールドに擬似列を追加しない。

# マージ候補

目的:

- `in-review` のIssueのうち、マージ候補を絞り込むための一覧にする。マージキュー対応時も非対応時も同じビューを使う。
- ビュー上の表示だけでマージ可能と判定しない。

REST APIで設定:

- `layout`: `table`
- `filter`: `is:issue is:open status:in-review`
- `visible_fields`: Typeの正本、Scopeの正本、Priority、Risk、Reviewer Owner、Branch、Linked pull requests、Reviewers

UIで後設定:

- グループ化: Risk
- 並び替え: Priorityの降順、更新日時の昇順

運用規則:

- `Linked pull requests` から対象PRを開く。`Reviewers` は入口として使い、承認状況の最終判定はPR自体で行う。
- レビュー承認、必須ステータスチェック、マージ可否、Draft状態、基点・作業ブランチは `gh pr view` で別に確認する。

```bash
gh pr view PR_NUMBER \
  --repo OWNER/REPO \
  --json reviewDecision,statusCheckRollup,mergeable,mergeStateStatus,isDraft,baseRefName,headRefName
gh pr checks PR_NUMBER --repo OWNER/REPO --required
```

- `statusCheckRollup` はチェック全体の把握に使い、必須ステータスチェックだけの合否は `gh pr checks --required` で判定する。必須ステータスチェックが実行中または失敗中なら候補から外す。マージ後は型別完了条件を満たしてからActual Endを記録する。

# Velocity

目的:

- 完了量、サイクルタイム、レビュー時間を週次で観察する。
- エージェント投入量とマージ待ちの詰まりを振り返る。

REST APIで設定:

- `layout`: `table`
- `filter`: `is:issue status:done -no:"Actual End"`
- `visible_fields`: Typeの正本、Scopeの正本、Size、Effort、Estimate Confidence、Complexity、Risk、Agent Tier、Actual Start、Actual End、Linked pull requests、Reviewers

UIで後設定:

- グループ化: Scopeの正本
- 並び替え: Actual Endの降順

運用規則:

- `done` 件数、末端IssueのEffort合計、Size区分別件数、Scope別完了、Agent Tier別完了を週次で見る。
- Sizeは合計しない。Actual Start / Actual Endは待ち時間を含むため、実Effortとは扱わない。
- レビュー時間やマージ待ち時間は、`Linked pull requests` からPRを開き、作成日時、マージ日時、レビュー状態を読む。
