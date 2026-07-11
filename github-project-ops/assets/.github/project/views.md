# Project views の設定例

GitHub Projectsのviewには説明文欄がない前提で運用する。viewの目的、filter、運用ルールは、このfileまたはrepo側の `.github/project/views.md` に保存する。

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

実装WIPは `min(Agent枠上限, 作業環境枠上限)` で導出し、未設定の枠/WIP上限は各1として扱う。Effortは実装、直接確認、テスト、ドキュメント、通常のレビュー修正を含み、待ち時間を含めない。epicはEffortを持たず、末端Issueだけを合計する。Sizeは順序尺度なので合計しない。

# かんばん

目的:

- 全体の進捗をStatus別に見る。
- ready、in-progress、in-review、blockedの詰まりを日次で確認する。
- 作業投入、review待ち、blocker解除の入口にする。

Layout:

- board

Filter:

- Project field: Status = inbox, triaged, ready, in-progress, in-review, blocked

Group:

- Status

Sort:

- Priority desc
- Risk desc
- updated asc

Visible fields:

- Type
- Scope
- Priority
- Size
- Effort
- Estimate Confidence
- Complexity
- Risk
- Agent Tier
- Agent Run
- Assignee
- Reviewer Owner
- Branch
- Actual Start

運用ルール:

- readyに置くのは、受け入れ条件、非スコープ、確認手順、未解決blockerなしを確認済みの実行対象末端Issueだけにする。仕様確定済みでも前段Issue待ちならblockedにする。
- `blocking` はこのIssueが後続Issueの前提であるという意味なのでreadyと両立する。`blocked by` が未解決ならreadyと両立しない。
- Statusは `blocked by` / `blocking` から自動同期しない。upstream PR、Figma design、権限、担当外のCI基盤障害、設計判断待ちなどでblockedになるIssueもあるため、かんばんではStatusとblockedコメントを一緒に読む。
- in-progressへ進める前にblocked byを再確認する。未解決の阻害要因がある場合は作業開始しない。
- 実装WIPが上限なら新しい作業権を取得しない。レビュー、重いCI/共有環境、マージ待ちの下流WIPも確認する。
- 作業権取得の勝者だけがAgent Runを設定し、リポジトリ差分を作る場合は独立worktreeを作る。
- in-reviewではPR本文のclosing keyword、確認手順、リスク、レビュー観点、required checksを見る。
- blockedではcommentに理由、解除者、依存Issue/PR/log、次の確認タイミングがあるか確認する。
- doneとcanceledは通常表示しない。

# WBS/ロードマップ

目的:

- WBS/Gantt相当の計画表示として使う。
- Milestoneの締切目標からIssue/WBSのForecastを確認する。
- 作業の構造と順序を、epic、sub-issue、blocked by / blockingで見る。
- 計画開始日と計画終了目標日を確認する。

Layout:

- roadmap

Filter:

- Project field: Forecast Start is not empty
- Project field: Forecast End is not empty
- Project field: Status = triaged, ready, in-progress, in-review, blocked, done

Group:

- Scope

Sort:

- Forecast Start asc
- Forecast End asc
- Priority desc

Visible fields:

- Type
- Scope
- Priority
- Effort
- Estimate Confidence
- Risk
- Agent Tier
- Forecast Start
- Forecast End
- Milestone
- blocked by
- blocking

運用ルール:

- date fieldsは `Forecast Start` / `Forecast End` を使う。
- Milestone due dateを先に決め、その締切目標からForecast Start / Forecast Endを組む。
- 締切未定MilestoneはForecastの締切制約には使わない。
- 期限変更時はMilestone due dateを先に更新し、ForecastはProject fieldだけを見直す。詳細手順は `github-project-ops` skillのreferenceを読む。
- WBS番号は作らない。構造はepic/sub-issue、順序はblocked by / blockingで表す。
- Statusは依存関係からの自動同期ではなく、運用状態として人間またはagentが確認して更新する。
- epicのForecastは子Issue群を包む期間で、子Issueと重なってよい。
- 直列依存するブランチ作成型Issue同士ではForecastを重ねない。後続IssueのForecast Startは、すべての `blocked by` 先のForecast Endより後の日付にする。
- 依存関係、変更競合グラフ、実装/レビュー/CI/マージ容量が許すIssueだけForecastを重ねてよい。
- Forecastは稼働日で扱い、レビュー、重いCI、マージの予備日を含める。Milestone期限を超える場合はscope、期限、依存関係、容量を見直す。
- 実績はActual Start、Actual Endで見る。

# マージキュー候補

目的:

- auto-mergeまたはmerge queue投入候補のPRを確認する。
- review承認済みでrequired checksが揃ったPRをmainへ流す。

Layout:

- table

Filter:

- Project field: Status = in-review
- GitHub PR: レビュー承認済み
- GitHub checks: required checks passing

Group:

- Risk

Sort:

- Priority desc
- updated asc

Visible fields:

- Type
- Scope
- Priority
- Risk
- Reviewer Owner
- Branch

運用ルール:

- closing keyword、linked Issue、base/head branch、merge queue設定を確認してからauto-mergeを有効化する。
- required checkがrerun中または失敗中なら候補にしない。
- PR作成日、merge状態、merge日はGitHub PR metadataから読む。Project fieldへ複製しない。
- merge後はdone条件を満たしてからActual EndをProject fieldへ記録する。

# Velocity

目的:

- 完了量、サイクルタイム、レビュー時間を週次で観察する。
- agent投入量とmerge queueの詰まりをふりかえる。

Layout:

- table

Filter:

- Project field: Status = done
- Project field: Actual End is not empty

Group:

- Scope

Sort:

- Actual End desc

Visible fields:

- Type
- Scope
- Size
- Effort
- Estimate Confidence
- Complexity
- Risk
- Agent Tier
- Actual Start
- Actual End

運用ルール:

- done件数、末端IssueのEffort合計、Size区分別件数、Scope別完了、Agent Tier別完了を週次で見る。
- Estimate Confidence別にForecast超過率とサイクルタイムを観察する。Actual Start / Actual Endは待ち時間を含むため、実Effortとは扱わない。Sizeは合計しない。
- Cycle timeはActual StartからActual Endまでを見る。
- レビュー時間やマージ待ち時間が必要な場合は、GitHub PRメタデータのcreatedAt、mergedAt、レビュー状態から読む。
- 厳密な見積もり契約ではなく、throughputを観察してready投入量を調整する。
