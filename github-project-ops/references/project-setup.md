# Project設定

Projectフィールド、工数、容量、ラベル不使用方針、日付フィールド、Forecast、ビュー、コピー用アセットを扱うときに読む。

# 目次

- コピー用アセット
- Projectフィールド
- 工数と見積り
- 容量とWIP上限
- GitHubラベル
- Milestone
- 日付フィールド
- Forecast変更
- ビュー説明の置き場所
- 標準ビュー
- スプリントを導入するか

# コピー用アセット

`assets/` は、対象リポジトリへコピーして使う設定・サンプルデータを置く場所である。エージェントが読む手順は `references/` に置く。

主なコピー用アセット:

- `assets/.github/`: Issue Forms、PRテンプレート、`merge_group` 対応CIの例。導入時は対象リポジトリの `.github/` へコピーし、固有の文言と検査コマンドだけを調整する。
- `assets/.github/project/views.md`: GitHub Projectsビューの説明をリポジトリ側へ置く例。導入時は対象リポジトリの `.github/project/views.md` へコピーする。
- `assets/project-fields.json`: 推奨Projectフィールドと単一選択肢の色・説明文の定義例。
- `assets/project-views.json`: 標準ビューの名前、レイアウト、フィルターの機械可読な正本。
- `assets/project-items.example.json`: 作成済みIssueとProject項目値を結ぶ割当計画例。

これらは実GitHub Projectやリポジトリ設定を自動移行するものではない。GitHub上の実状態を確認してから、必要な設定だけ手動またはgh CLIで反映する。

# Projectフィールド

標準ProjectのアイテムはIssueを主体とする。PRを別のProjectアイテムとして管理せず、Issueの組み込み列 `Linked pull requests` と `Reviewers` から関連PRとレビュー状況を読む。承認、必須ステータスチェック、マージ可否の詳細はPR自体で確認し、Project独自フィールドに複製しない。

フィールド作成前に、作業対象Issueのリポジトリ所有者を確認する。

- 組織所有リポジトリ: 対象リポジトリで利用できるIssue Typesと、所有組織のIssue Fieldsを読む。同じ意味と値域を持つフィールドがある場合はそれを正本とし、同義のProject独自フィールドを作らない。
- 個人所有リポジトリ: 組織Issue Fieldsを使えないため、Project独自フィールドを正本とする。
- 複数組織や個人所有のIssue、PR、Draft Issueが混在するProject: 組織Issue Fieldsは対象外アイテムで空になる。正本を自動選択せず停止し、対象組織のIssueだけを持つProjectへ分けてから計画を作り直す。
- 公開またはinternal Project: `visibility: all` の組織Issue Fieldだけを使う。組織内限定フィールドはProjectに表示できないため、同義とみなさず停止する。

検出には次の読み取りを使う。得られた名前、型、値域を `assets/project-fields.json` と比較し、同義である場合だけ切り替える。

```bash
gh api repos/OWNER/REPO/issue-types
gh api orgs/ORG/issue-fields
```

参照:

- <https://docs.github.com/en/rest/repos/issue-types?apiVersion=2026-03-10>
- <https://docs.github.com/en/rest/orgs/issue-fields?apiVersion=2026-03-10>
- <https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields>

例えば、組織のIssue Typeがこの運用のType一式を表せる場合はIssue Typeを正本とし、Project独自の `Type` を作らない。一式が揃わない場合はProject Typeを使い、組織Issue FieldをTypeの代用にはしない。組織のIssue Fieldに同義の `Scope` がある場合はフィールド単位で切り替える。名前だけが同じで値域が足りない場合は同義とみなさない。

以下では、組織Issue Type、組織Issue Field、Project独自フィールドから選んだ保存先を「選択した正本」と呼ぶ。フィールド名は共通でも、実際の保存先はリポジトリの所有形態と利用可能な機能によって変わる。

組織のIssue TypesまたはIssue Fieldsに切り替えなかったフィールドの、推奨Project独自定義は次のとおり。

単一選択肢の名前はlower-kebab形式にする。GitHub Projectsの絞り込み式、`gh` 出力後の `jq`、手作業の検索で、空白・大文字小文字・引用符の扱いを減らすためである。フィールド名は人間が読むためTitle Caseのままにする。

`assets/project-fields.json` の単一選択肢 `options` は、標準では `name`、`color`、`description` を持つオブジェクト形式にする。フィールド値として使うのは `name` だけで、色と説明文は `references/project-api-queries.md` のGraphQL手順で反映する。

| フィールド          | 型       | 値                                                                                  |
| ------------------- | -------- | ----------------------------------------------------------------------------------- |
| Status              | 単一選択 | inbox, triaged, ready, in-progress, in-review, blocked, done, canceled              |
| Type                | 単一選択 | epic, feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert, spike |
| Scope               | テキスト | ui, api, db, infraなど。リポジトリごとに自由定義                                    |
| Priority            | 単一選択 | p0-optional, p1-normal, p2-high, p3-critical                                        |
| Size                | 単一選択 | s0-tiny, s1-small, s2-medium, s3-large                                              |
| Effort              | 数値     | 正の理想作業時間。標準単位はideal-hours                                             |
| Estimate Confidence | 単一選択 | ec0-low, ec1-medium, ec2-high                                                       |
| Complexity          | 単一選択 | c0-none, c1-simple, c2-moderate, c3-complex                                         |
| Risk                | 単一選択 | r0-none, r1-safe, r2-moderate, r3-dangerous                                         |
| Agent Tier          | 単一選択 | agent-fast, agent-standard, agent-frontier                                          |
| Agent Harness       | 単一選択 | codex, claude-code, cursor, human, other                                            |
| Agent Model         | テキスト | 実際に使用したモデル名と推論設定。作業開始時に記録                                  |
| Agent Run           | テキスト | 公開可能なタスクURL、または外部情報を含まない実行ID                                 |
| Reviewer Owner      | テキスト | エージェント実行環境の持ち主、またはレビュー責任者のGitHubログイン名                |
| Branch              | テキスト | 123/feat-ui-example                                                                 |
| Source              | 単一選択 | human, agent, debug-log, chat, inquiry, ci, dependency, security, docs              |
| Forecast Start      | 日付     | 計画開始日。WBS/ロードマップで使う                                                  |
| Forecast End        | 日付     | 計画終了目標日。WBS/ロードマップで使う                                              |
| Actual Start        | 日付     | 実作業開始日                                                                        |
| Actual End          | 日付     | 実終了日                                                                            |

Issue時点では具体的なモデル名まで確定させず、Agent Tierを設定する。作業権取得成功時にAgent Harness、Agent Model、Agent Runをそれぞれの正本へ記録する。

Issue/PRタイトルにTypeやScopeを入れない。TypeとScopeは、選択した正本で見る。

# 工数と見積り

EffortはProject全体で単位を固定した理想作業時間で、標準は `ideal-hours` とする。実装、直接確認、テスト、文書更新、通常見込むレビュー修正を含める。CI待ち、外部待ち、レビュー待ち、マージ待ちは含めない。

- ブランチ作成型Issue、`spike`、リポジトリ差分なしIssueは、`ready` へ進める前に正のEffortとEstimate Confidenceを持つ。
- 運用中に流入した `inbox` / `triaged` Issueは見積欄が空でもよいが、初期構築へ渡すWBSの非`epic` Issueは事前検証のため両方を必須にする。
- `epic` のEffortとEstimate Confidenceは空欄にする。末端Issueだけを合計し、親子で二重計上しない。
- Sizeは差分量とレビュー量の順序尺度である。Sizeを数値へ変換して合計しない。
- `ec0-low` で未知要素が作業境界まで揺らす場合は、`ready` にせず`spike`へ分ける。

Estimate Confidenceの正本は次である。

- `ec0-low`: 未知要素が多く、再見積りの可能性が高い。
- `ec1-medium`: 境界は明確だが、一部未知要素がある。
- `ec2-high`: 類似実績、変更範囲、確認手順が揃っている。

# 容量とWIP上限

リポジトリ側の `.github/project/views.md` に、少なくとも次をProject運用設定として置く。

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

実装WIPは `min(Agent枠上限, 作業環境枠上限)` で導出する。未設定の枠/WIP上限は各1として安全側に扱う。稼働カレンダー、有効Effort、予備日が未設定なら上記標準値を使い、採用値を計画出力に明記する。

- 1 Issueは各段階で1枠を消費する。Effortは作業量、WIPは同時処理数であり混同しない。
- 作業権取得済みIssueにはエージェントごとに独立した`worktree`を割り当てる。
- エージェントまたは作業環境枠が埋まっていれば新しい作業権を取得しない。レビュー、重いCI・共有環境、マージ待ちが上限なら、その下流へ新規投入しない。
- Draft PRとリポジトリ内で修正可能なレビュー・CI対応は実装枠、レビュー依頼後はレビュー枠、重いCIや共用試験環境の使用中はその専用枠、設定済み経路でのマージ待ちはマージ枠を消費する。
- 枠が空いた、Issueがマージ・`canceled`・`blocked`になった、Effortや依存関係が変わった時に次の実行Waveを再計算する。

# Milestone

MilestoneはGitHub標準のMilestoneを使う。Project独自フィールドとして複製しない。

Milestoneはリリースや節目と締切目標を表す。先にMilestoneと期限を決め、その範囲に収まるようにIssue/WBSのForecast Start / Forecast Endを組む。IssueのForecastからMilestone期限を逆算しない。

期限や日付はMilestone名へ入れず、GitHub Milestoneの期限にだけ置く。Issue本文、PR本文、ProjectフィールドにもMilestone期限を複製しない。

期限ありが基本のMilestone候補:

- `First Release`: 初回利用可能版。bootstrap既定で作成する。
- `v1 Release`: 安定版として公開・配布できる状態。
- `仕様・デザイン確定`: 主要仕様、UI/UX、非スコープが確定した状態。
- `データセット固定`: 学習・評価・公開対象のデータセットを固定した状態。
- `評価完了`: 評価指標、結果、再現手順が揃った状態。
- `論文投稿準備完了`: 論文、補足資料、artifact、チェックリストが投稿可能な状態。
- `ポスター完成`: 掲示・発表に使えるポスターが完成した状態。
- `投稿完了`: 投稿先への提出、査読用情報、保存先、公開先の準備が完了した状態。
- `一般公開`: 文書、デモ、成果物、リリースノートを含めて公開できる状態。

期限未定でも使えるMilestone候補:

- `法人設立`
- `外部審査`
- `共同研究契約`
- `データ利用許諾`

締切未定Milestoneは期限なしで作ってよい。ただしForecastの締切制約には使わない。

Milestone一覧を読む。

```bash
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100
```

Milestoneの期限を変更する。

```bash
gh api repos/OWNER/REPO/milestones/MILESTONE_NUMBER \
  --method PATCH \
  -f due_on="2026-07-31T23:59:59Z"
```

締切未定へ戻す。

```bash
gh api repos/OWNER/REPO/milestones/MILESTONE_NUMBER \
  --method PATCH \
  -F due_on=null
```

既存IssueへMilestoneを割り当てる。

```bash
gh issue edit ISSUE_NUMBER --repo OWNER/REPO --milestone "First Release"
```

Milestone期限を変更した後は、そのMilestoneに属するIssueだけを見直す。

```bash
gh issue list \
  --repo OWNER/REPO \
  --milestone "First Release" \
  --state all \
  --json number,title,state,milestone
```

期限変更はGitHub Milestoneの期限を正本にする。Issue本文、PR本文、ProjectフィールドへMilestone期限を複製しない。Forecast Start / Forecast Endは、その期限に収まるように必要なIssueだけを更新する。

# GitHubラベル

このスキルではGitHubラベルを使わない。

StatusはProject独自フィールドを正本にする。Typeは組織Issue Type一式またはProject Typeを正本にする。Source、Priority、Size、Effort、Estimate Confidence、Complexity、Risk、Agent Tierは、導入時にフィールドごとに選択した組織Issue FieldまたはProject独自フィールドを正本にする。GitHubラベルへは複製しない。

分類、状態、起票元、優先度、見積もり、エージェント割り当ては、すべて選択した正本で表す。新しいGitHubラベルは定義しない。

Projectでは選択した正本の値でIssueを絞り込めるため、ラベルを移植用の代替手段として持たない。比較や並び替えでは、`p2-high` の `2` のように選択肢名の数値接頭辞を読む。

既存フィールドの選択肢名は自動移行しない。必要な選択肢の移行は、正本側で手動実施する。

既存リポジトリに残っているラベルは自動削除しない。不要なラベルはリポジトリ側で手動整理する。

# 日付フィールド

計画日と実績日は別フィールドにする。

- `Forecast Start`: 計画開始日。`WBS/ロードマップ`ビューで使う。
- `Forecast End`: 計画終了目標日。`WBS/ロードマップ`ビューで使う。
- `Actual Start`: 実作業開始日。Issueをin-progressへ進める時に記録する。
- `Actual End`: 実終了日。doneまたはcanceledで終了を確認した時に記録する。

PR作成日、マージ日、Issue/PRの終了日はGitHubのメタデータを正本にする。運用フィールドへ複製しない。

Issue本文、PR本文、作業開始コメントには日付フィールドの値を書かない。計画・実績の期間は選択した正本で見る。

Forecast Start / Forecast Endは計画上の作業期間であり、実績ではない。

日付はProject運用設定のタイムゾーンで解釈し、開始日と終了日を含む稼働日とする。休日は作業日数へ数えない。日付フィールドは時刻を持たないため、直列Issueの同日引き継ぎは行わず、後続は次の稼働日以降に開始する。

- 期限付きMilestoneでは、Milestone due dateを先に決めてからIssue/WBSのForecastを組む。
- epicのForecastは子Issue群を包む期間にする。epicと子IssueのForecastが重なるのは正常である。
- ブランチ作成型Issue同士が直列依存する場合、後続IssueのForecast Startは、すべての `blocked by` 先のForecast Endより後の日付にする。
- GitHub Projectsの日付フィールドは時刻を持たないため、同日引き継ぎを前提にして直列IssueのForecastを同じ日に重ねない。必要ならIssueをさらに分けるか、前段のForecast Endを短くする。
- 依存関係がなくても、変更ファイル競合または実装/レビュー/CI/マージの容量競合があるIssueは同じ期間へ詰め込まない。

# Forecast変更

Forecast変更では、先にMilestoneの期限、Issue間の依存関係、sub-issue構造、変更競合グラフ、Effort、Estimate Confidence、稼働カレンダー、各WIP上限を読む。Issue本文のメタデータ行ではなく、選択した正本だけを更新する。

```bash
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 100
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 100
gh issue view ISSUE_NUMBER \
  --repo OWNER/REPO \
  --json number,title,milestone,parent,subIssuesSummary,blockedBy,blocking
```

Projectフィールドを正本にしている場合の日付更新例を示す。

```bash
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(input:{
    projectId:"PROJECT_ID",
    itemId:"PROJECT_ITEM_ID",
    fieldId:"FORECAST_END_FIELD_ID",
    value:{date:"2026-07-31"}
  }) {
    projectV2Item { id }
  }
}'
```

Forecastは次の順で組む。

1. 依存関係DAGとsub-issue階層の循環を拒否する。
2. `canceled`になった阻害Issueを完了扱いせず、推移的な後続Issueを再トリアージする。
3. `ceil(Effort / 実装1枠・1稼働日あたりの有効Effort)` を実装作業日の初期値にする。
4. 依存関係、変更競合、実装WIPを満たすよう末端Issueを稼働日へ配置する。
5. レビュー、重いCI/共有環境、マージ待ちのWIPと予備日を加える。
6. `epic` のForecastを必要な末端Issue全体を包む期間へ集約する。`epic` のEffortは合計しない。

Milestone実現可能性の確認では、必要な末端IssueがMilestone期限までに型別`done`へ到達できるかを見る。超過する場合は日付だけを圧縮せず、範囲削減、期限変更、依存関係の解消、容量追加の選択肢と影響を出す。選択が決まるまで計画を実現可能と報告しない。

期限変更で全Issueを機械的に同じ幅でずらさない。依存関係、競合、容量が許すIssueだけForecastを重ねる。epicのForecastは子Issue群を包む期間に直す。

# ビュー説明の置き場所

GitHub Projectsのビューには説明文欄がない前提で運用する。ビューの目的、絞り込み条件、運用規則は、このファイルとコピー用の `assets/.github/project/views.md` に置く。

リポジトリ固有に公開したい場合は、対象リポジトリの `.github/project/views.md` に同じ形式で保存する。Project本体にはビュー名とフィールド設定だけを置く。

# 標準ビュー

標準ビューは次の4つだけにする。

- `かんばん`
- `WBS/ロードマップ`
- `マージ候補`
- `Velocity`

`ready`、レビュー、`blocked`、高難度エージェント向けの専用ビューは作らない。

API版 `2026-03-10` のREST APIによるProjectビュー作成で指定できるのは、ビュー名、`layout`、`filter`、`visible_fields` である。`visible_fields` は `table` と `board` でのみ指定でき、`roadmap` では指定できない。グループ化、並び替え、ボードの列、ロードマップの日付フィールドと表示フィールドは、作成後にGitHubのUIで設定する。

参照: <https://docs.github.com/en/rest/projects/views?apiVersion=2026-03-10>

| ビュー           | REST APIで設定する `layout` / `filter`                                                                                 | REST APIで設定する `visible_fields`                                                                                                                                                             | UIで後設定                                                                                   |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| かんばん         | `board` / `is:issue is:open status:inbox,triaged,ready,in-progress,in-review,blocked`                                  | Typeの正本、Scopeの正本、Priority、Size、Effort、Estimate Confidence、Complexity、Risk、Agent Tier、Agent Run、Assignees、Reviewer Owner、Branch、Actual Start、Linked pull requests、Reviewers | Statusの列。Priority降順、Risk降順、更新日時昇順                                             |
| WBS/ロードマップ | `roadmap` / `is:issue -no:"Forecast Start" -no:"Forecast End" status:triaged,ready,in-progress,in-review,blocked,done` | 指定しない                                                                                                                                                                                      | Forecast Start / Forecast End、Scopeの正本でグループ化、計画日昇順、Typeなどの表示フィールド |
| マージ候補       | `table` / `is:issue is:open status:in-review`                                                                          | Typeの正本、Scopeの正本、Priority、Risk、Reviewer Owner、Branch、Linked pull requests、Reviewers                                                                                                | Riskでグループ化、Priority降順、更新日時昇順                                                 |
| Velocity         | `table` / `is:issue status:done -no:"Actual End"`                                                                      | Typeの正本、Scopeの正本、Size、Effort、Estimate Confidence、Complexity、Risk、Agent Tier、Actual Start、Actual End、Linked pull requests、Reviewers                                             | Scopeの正本でグループ化、Actual End降順                                                      |

`blocked by` と `blocking` はIssue自体で読む。Projectで使える表示フィールドやフィルターとして定義しない。

`Linked pull requests` と `Reviewers` はPRへ進む入口であり、レビュー承認、必須ステータスチェック、マージ可否の正本ではない。`マージ候補` は `in-review` の候補一覧に限定し、ビューのフィルターに「レビュー承認済み」や「必須ステータスチェック成功」を書かない。各PRを次で別確認する。

```bash
gh pr view PR_NUMBER \
  --repo OWNER/REPO \
  --json reviewDecision,statusCheckRollup,mergeable,mergeStateStatus,isDraft,baseRefName,headRefName
gh pr checks PR_NUMBER --repo OWNER/REPO --required
```

`statusCheckRollup` はチェック全体の把握に使う。必須ステータスチェックだけの合否は `gh pr checks --required` で判定する。

その他の運用規則とビューごとの表示フィールドは `assets/.github/project/views.md` を正本とする。

# スプリントを導入するか

スプリント開始時の固定した作業範囲への確約は必須にしない。

理由:

- エージェント並列開発では投入可能量が動的に変わる。
- CI、レビュー、マージ待ちの詰まりで処理量が変わる。
- 割り込みIssueを柔軟に流す必要がある。

使うならIterationは観察窓として使う。

良い使い方:

- `かんばん` で現在のStatusと詰まりを見る。
- `WBS/ロードマップ` で計画日と依存関係を見る。
- `マージ候補` で既定ブランチ統合前のPRだけを見る。
- `Velocity` を週次で観察する。

悪い使い方:

- スプリント開始時に固定範囲を硬く約束する。
- エージェント投入量の変化を無視する。
- 期限変更のたびにIssueを大量編集する。
