# Project設定

Projectフィールド、工数、容量、Forecast、ビューを設計または見直すときに読む。
IssueやPRの作り方ではなく、GitHub Projectsへ保存する管理情報だけを扱う。

# 責務の境界

この資料が変更してよい対象は、Project、Projectアイテム、Projectフィールド、フィールド値、
ビュー、リポジトリとの紐付けである。

次の情報は`github-issue-pr-ops`が管理する。Project側では作成、変更、競合解決を行わず、
必要な事実だけを読む。

- Issue本文、受け入れ条件、確認手順、sub-issue、`blocked by` / `blocking`
- Milestoneの作成、期限変更、Issueへの割り当て
- `Assignee`の決定、linked branchの作成・選択、open PRの関連付け、着手競合の解消
- branch、worktree、PR本文、レビュー契約、CI契約、マージ契約
- Issue Forms、PRテンプレート、CIワークフロー

Projectの`Status`や`Agent Run`を、担当者や作業中branchの正本にしない。
`github-issue-pr-ops`で`Assignee`、linked branch、open PRの整合を確認した後、
確定済みの着手情報を`Status`へ派生同期する。`Agent Run`は、現在の実行環境が公開可能な
一意のIDまたはタスクURLを提示した場合だけ記録する任意の追跡値とする。

# コピー用アセット

Project用の定義だけを対象リポジトリへコピーする。

- `assets/project-fields.json`: Projectフィールドと単一選択肢の定義例
- `assets/project-views.json`: 標準ビューの名前、レイアウト、フィルター
- `assets/project-items.example.json`: 作成済みIssueとProject項目値を結ぶ割当計画例
- `assets/.github/project/views.md`: ビューの目的と運用規則をリポジトリ側へ置く例

これらはGitHub上の状態を自動移行しない。反映前後にProjectを再取得し、差分を確認する。

# Projectフィールド

ProjectアイテムはIssueを主体とする。PRを別アイテムとして重複管理せず、組み込み列
`Linked pull requests`と`Reviewers`から関連PRをたどる。レビュー、必須チェック、マージ可否は
PR自体から読む。

## 正本の選択

フィールド作成前に、Projectへ入れるIssueのリポジトリ所有者と利用可能なIssue Type、
Issue Fieldを確認する。

- 組織所有リポジトリでは、同じ意味、型、値域を持つ組織Issue TypeまたはIssue Fieldを正本にする。
  同義のProject独自フィールドは作らない。
- 個人所有リポジトリでは、Project独自フィールドを正本にする。
- 複数組織や個人所有のIssue、PR、Draft Issueが混在する場合、組織Issue Fieldは一部のアイテムで
  空になる。正本を自動選択せず、対象組織ごとにProjectを分けてから計画を作り直す。
- 公開またはinternal Projectでは、`visibility: all`の組織Issue Fieldだけを使う。
- 名前が同じでも型または値域が違えば同義とみなさない。

保存先は次の順で決める。

- `Status`、`Agent Run`、`Reviewer Owner`、計画日、実績日はProject独自フィールドを正本にする。
- `Type`は、必要な値一式が揃う組織Issue Typeを優先し、揃わなければProject独自フィールドにする。
- Scope、Priority、Size、Effort、Estimate Confidence、Complexity、Risk、Agent Tier、Sourceは、
  同義の組織Issue Fieldがあればそれを使い、なければProject独自フィールドにする。

検出には読み取りAPIを使う。

```bash
gh api repos/OWNER/REPO/issue-types
gh api orgs/ORG/issue-fields
```

各フィールドは個別に判断し、選んだ保存先を割当計画の`field_sources`へ記録する。

参照:

- <https://docs.github.com/en/rest/repos/issue-types?apiVersion=2026-03-10>
- <https://docs.github.com/en/rest/orgs/issue-fields?apiVersion=2026-03-10>
- <https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields/about-issue-fields>

## Project独自フィールド

組織Issue TypeまたはIssue Fieldへ切り替えなかった項目は、次を標準にする。
フィールド名はTitle Case、単一選択肢はlower-kebab形式とする。色と説明文を含む定義は
`assets/project-fields.json`を正本にする。

| フィールド          | 型       | 値または用途                                                                                |
| ------------------- | -------- | ------------------------------------------------------------------------------------------- |
| Status              | 単一選択 | inbox, triaged, ready, in-progress, in-review, blocked, done, canceled                      |
| Type                | 単一選択 | epic, feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert, spike         |
| Scope               | テキスト | ui, api, db, infraなど。リポジトリごとに定義                                                |
| Priority            | 単一選択 | p0-optional, p1-normal, p2-high, p3-critical                                                |
| Size                | 単一選択 | s0-tiny, s1-small, s2-medium, s3-large                                                      |
| Effort              | 数値     | 正の理想作業時間。標準単位はideal-hours                                                     |
| Estimate Confidence | 単一選択 | ec0-low, ec1-medium, ec2-high                                                               |
| Complexity          | 単一選択 | c0-none, c1-simple, c2-moderate, c3-complex                                                 |
| Risk                | 単一選択 | r0-none, r1-safe, r2-moderate, r3-dangerous                                                 |
| Agent Tier          | 単一選択 | agent-fast, agent-standard, agent-frontier                                                  |
| Agent Run           | テキスト | 現在の実行環境が明示した公開可能なタスクURLまたは外部情報を含まない一意のID。未提示なら空欄 |
| Reviewer Owner      | テキスト | レビュー責任者のGitHubログイン名                                                            |
| Source              | 単一選択 | human, agent, debug-log, chat, inquiry, ci, dependency, security, docs                      |
| Forecast Start      | 日付     | 計画開始日                                                                                  |
| Forecast End        | 日付     | 計画終了目標日                                                                              |
| Actual Start        | 日付     | 確定した作業開始日                                                                          |
| Actual End          | 日付     | 確定した終了日                                                                              |

Status、Type、工数、優先度などをGitHubラベルへ複製しない。このスキルは新しいラベルを
定義せず、既存ラベルも自動削除しない。

# Issue/PR側からの同期

作業開始前にProjectの容量を判定し、その結果をIssue/PR側へ返す。

1. Projectの実装枠、作業環境枠、下流WIP、依存関係を読む。
2. 容量がなければ`投入不可`、埋まっている枠、再確認条件を返す。Project側では着手を確定せず、
   `Agent Run`や`Status: in-progress`も設定しない。
3. 容量があれば`投入可能`を返す。`Assignee`、linked branch、open PRの整合確認と競合解消は
   `github-issue-pr-ops`へ任せる。
4. Issue/PR側で整合した着手情報が確定したことを再取得してから`Status: in-progress`を同期する。
   現在の実行環境が追跡値を明示した場合だけ`Agent Run`も同期し、未提示なら空欄のままにする。

Projectの値が先に書かれていても着手済みとはみなさない。確定済み着手情報を取得できない、
現在の`Assignee`、linked branch、open PRが確定内容と一致しない、候補を一意に特定できない、
提示された`Agent Run`が既存値と衝突する、または容量判定後に枠が埋まった場合は同期を止める。
確認済みの担当変更では新しい追跡値へ更新できるが、それ以外はProject側で候補や値を選ばず、
差異を`github-issue-pr-ops`へ返して整合確認からやり直す。

`Status`のその後の変更も、Issue、sub-issue、依存関係、PRの確定状態を読み取った後に行う。
ProjectビューやProjectフィールドだけから、レビュー完了、CI成功、マージ完了を推測しない。

# 工数と見積り

EffortはProject全体で単位を固定した理想作業時間で、標準は`ideal-hours`とする。実装、直接確認、
テスト、文書更新、通常見込むレビュー修正を含める。CI待ち、外部待ち、レビュー待ち、
マージ待ちは含めない。

- `ready`へ進める末端Issueは、正のEffortとEstimate Confidenceを持つ。
- 運用中の`inbox` / `triaged`は未見積りでもよい。
- `epic`のEffortとEstimate Confidenceは空欄にし、末端Issueだけを合計する。
- Sizeは差分量とレビュー量の順序尺度であり、数値へ変換して合計しない。
- `ec0-low`で作業境界が揺れる場合は、開始可能と判定しない。Issueの再分割判断は
  `github-issue-pr-ops`へ返す。

Estimate Confidenceの意味は次で固定する。

- `ec0-low`: 未知要素が多く、再見積りの可能性が高い。
- `ec1-medium`: 境界は明確だが、一部に未知要素がある。
- `ec2-high`: 類似実績、変更範囲、確認手順が揃っている。

# 容量とWIP上限

リポジトリ側の`.github/project/views.md`に、少なくとも次をProject運用設定として置く。

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

実装WIPは`min(Agent枠上限, 作業環境枠上限)`で導出する。設定と関連項目を読めて、値が存在しないことを確認できた場合に限り、未設定の枠とWIP上限は1、未設定の稼働カレンダー、有効Effort、予備日は上記の標準値を使い、採用値を計画出力に明記する。権限不足、取得失敗、対象不明で未設定か確認できない場合は初期値で補わず停止する。

- 1 Issueは各段階で1枠を消費する。Effortと同時処理数を混同しない。
- 実装中は実装枠、レビュー依頼後はレビュー枠、重いCIや共有試験環境の使用中は専用枠、
  マージ待ちはマージ枠を消費する。
- いずれかの必要枠が上限なら新規投入を止める。Issue/PR側へ不足している枠と再確認条件を返す。
- 枠が空いた、Issueが終了または阻害された、Effortや依存関係が変わった時に実行Waveを再計算する。

# Forecast

Forecastの入力として、Projectフィールドに加えて次のGitHub上の事実を読み取る。
これらをProject独自フィールドやIssue本文へ複製しない。

- Milestoneの期限
- sub-issue階層
- `blocked by` / `blocking`
- 関連PRのDraft、レビュー、必須チェック、マージ可否、状態

```bash
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 100
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 100

gh issue view ISSUE_NUMBER \
  --repo OWNER/REPO \
  --json number,title,milestone,parent,subIssues,subIssuesSummary,blockedBy,blocking

gh pr view PR_NUMBER \
  --repo OWNER/REPO \
  --json reviewDecision,statusCheckRollup,mergeable,mergeStateStatus,isDraft,baseRefName,headRefName

gh pr checks PR_NUMBER --repo OWNER/REPO --required
```

Milestone期限はIssueに割り当て済みの値だけを読み、Forecastの上限制約として使う。期限を作成、変更、
削除したり、Issueへ割り当てたりしない。期限なしMilestoneは締切制約へ使わない。

Forecastは次の順で組む。

1. 依存関係DAGとsub-issue階層の循環を拒否する。
2. `canceled`になった阻害Issueを完了扱いせず、推移的な後続Issueを再評価する。
3. `ceil(Effort / 実装1枠・1稼働日あたりの有効Effort)`を実装作業日の初期値にする。
4. 依存関係、変更競合、実装WIPを満たすよう末端Issueを稼働日へ配置する。
5. レビュー、重いCI・共有環境、マージ待ちのWIPと予備日を加える。
6. `epic`のForecastを末端Issue全体を包む期間へ集約する。`epic`のEffortは合計しない。

期限までに必要な末端Issueが`done`へ到達できない場合、日付だけを圧縮しない。範囲削減、
期限変更、依存関係の解消、容量追加の選択肢と影響を返し、選択が決まるまで実現可能と報告しない。
Milestone期限の変更自体はIssue/PR側の運用へ委ねる。

日付はProject運用設定のタイムゾーンで解釈し、開始日と終了日を含む稼働日とする。
休日を作業日数へ含めない。直列Issueの後続は、すべての依存先の`Forecast End`より後の
稼働日に開始する。変更競合または容量競合があるIssueも同じ期間へ詰め込まない。

# 実績日の同期

計画日と実績日は分ける。

- `Forecast Start` / `Forecast End`: Projectで作る計画期間
- `Actual Start`: Issue/PR側で作業開始が確定したイベントのGitHubサーバー時刻から同期
- `Actual End`: Issue/PR側で完了または取消が確定したイベントのGitHubサーバー時刻から同期

同期時刻をProject運用設定のタイムゾーンへ変換し、日付だけを保存する。既存の実績日を
推測値で上書きしない。PR作成日、マージ日、Issue終了日はGitHubのメタデータとして読み、
`Actual Start` / `Actual End`の代用にしない。

# ビュー説明の置き場所

GitHub Projectsのビューには説明文欄がない前提で運用する。ビューの目的、絞り込み条件、
運用規則は、この資料と`assets/.github/project/views.md`に置く。Project本体にはビュー名、
レイアウト、フィルター、表示フィールドだけを置く。

# 標準ビュー

標準ビューは次の4つとする。

- `かんばん`
- `WBS/ロードマップ`
- `マージ候補`
- `Velocity`

API版`2026-03-10`のREST APIで作成時に指定できるのは、ビュー名、`layout`、`filter`、
`visible_fields`である。`visible_fields`は`table`と`board`だけで指定できる。グループ化、
並び替え、ボードの列、ロードマップの日付フィールドは作成後にGitHub UIで設定する。

参照: <https://docs.github.com/en/rest/projects/views?apiVersion=2026-03-10>

| ビュー           | `layout` / `filter`                                                                                                    | 用途                                                       |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| かんばん         | `board` / `is:issue is:open status:inbox,triaged,ready,in-progress,in-review,blocked`                                  | Status、優先度、工数、担当実行、詰まりを見る               |
| WBS/ロードマップ | `roadmap` / `is:issue -no:"Forecast Start" -no:"Forecast End" status:triaged,ready,in-progress,in-review,blocked,done` | Forecast、依存関係、Milestone期限との整合を見る            |
| マージ候補       | `table` / `is:issue is:open status:in-review`                                                                          | 関連PRを確認する入口。レビューやマージ可否はPR自体から読む |
| Velocity         | `table` / `is:issue status:done -no:"Actual End"`                                                                      | Effort、Estimate Confidence、実績期間を週次で振り返る      |

`blocked by`と`blocking`はIssue自体から、レビュー、必須チェック、マージ可否はPR自体から読む。
ビューの所属や`Status`だけでこれらを判定しない。表示フィールドの正本は
`assets/.github/project/views.md`とする。

# Iterationを導入するか

Iterationを使う場合は、固定した作業範囲への確約ではなく観察窓として使う。投入可能量は実装、
レビュー、重いCI、共有環境、マージ待ちの空きで変わるため、Iterationの所属だけを理由に
容量を超えて作業を開始しない。期限変更のたびにIssueを一括編集せず、Forecastと実行Waveを
再計算する。
