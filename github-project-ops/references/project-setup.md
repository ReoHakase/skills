# Project setup

Project fields、工数、容量、no-label policy、date fields、Forecast、views、copyable assetsを扱うときに読む。

# 目次

- Copyable assets
- Project fields
- 工数と見積り
- 容量とWIP上限
- GitHub labels
- Milestones
- Date fields
- Forecast変更
- View説明の置き場所
- 標準view
- Sprintを導入するか

# Copyable assets

`assets/` は、対象repositoryへコピーして使う設定・サンプルデータを置く場所である。agentが読む手順は `references/` に置く。

主なcopyable assets:

- `assets/.github/`: Issue Forms、PR template、merge_group対応CIの例。導入時は対象repoの `.github/` へコピーし、repo固有の文言とcheck commandだけを調整する。
- `assets/.github/project/views.md`: GitHub Projects viewの説明をrepo側へ置く例。導入時は対象repoの `.github/project/views.md` へコピーする。
- `assets/project-fields.json`: 推奨Project fieldsとsingle select optionの色・説明文の定義例。
- `assets/backlog.flat.json`: 初期backlog作成用のサンプルデータ。

これらはlive GitHub Projectやrepository設定を自動移行するものではない。GitHub上の実状態を確認してから、必要な設定だけ手動またはgh CLIで反映する。

# Project fields

推奨Project fieldsは次。

Single select optionはlower-kebabにする。GitHub Projectsのfilter query、`gh` 出力後の `jq`、手作業の検索で、空白・大文字小文字・quoteの扱いを減らすためである。Field名は人間が読むためTitle Caseのままにする。

`assets/project-fields.json` のsingle select `options` は、標準では `name`、`color`、`description` を持つobject形式にする。Project fieldの値として使うのは `name` だけで、色と説明文は `references/project-bootstrap.md` のGraphQL手順または `assets/project-bootstrap-template.py` で反映する。

| Field               | Type          | Values                                                                              |
| ------------------- | ------------- | ----------------------------------------------------------------------------------- |
| Status              | Single select | inbox, triaged, ready, in-progress, in-review, blocked, done, canceled              |
| Type                | Single select | epic, feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert, spike |
| Scope               | Text          | ui, api, db, infraなど。repoごとに自由定義                                          |
| Priority            | Single select | p0-optional, p1-normal, p2-high, p3-critical                                        |
| Size                | Single select | s0-tiny, s1-small, s2-medium, s3-large                                              |
| Effort              | Number        | 正の理想作業時間。標準単位はideal-hours                                             |
| Estimate Confidence | Single select | ec0-low, ec1-medium, ec2-high                                                       |
| Complexity          | Single select | c0-none, c1-simple, c2-moderate, c3-complex                                         |
| Risk                | Single select | r0-none, r1-safe, r2-moderate, r3-dangerous                                         |
| Agent Tier          | Single select | agent-fast, agent-standard, agent-frontier                                          |
| Agent Harness       | Single select | codex, claude-code, cursor, human, other                                            |
| Agent Model         | Text          | GPT 5.5 (xhigh), Opus 4.8 (medium), Composer 2.5など。作業開始時に記録              |
| Agent Run           | Text          | 公開可能なタスクURL、または外部情報を含まない実行ID                                 |
| Reviewer Owner      | Text          | agent実行環境の持ち主、またはレビュー責任者のGitHub login                           |
| Branch              | Text          | 123/feat-ui-example                                                                 |
| Source              | Single select | human, agent, debug-log, chat, inquiry, ci, dependency, security, docs              |
| Forecast Start      | Date          | 計画開始日。WBS/ロードマップで使う                                                  |
| Forecast End        | Date          | 計画終了目標日。WBS/ロードマップで使う                                              |
| Actual Start        | Date          | 実作業開始日                                                                        |
| Actual End          | Date          | 実終了日                                                                            |

Issue時点では具体的なモデル名まで確定させず、Agent Tierを設定する。作業権取得成功時にAgent Harness、Agent Model、Agent RunをProject fieldへ記録する。

Issue/PRタイトルにTypeやScopeを入れない。TypeとScopeはProject fieldで見る。

# 工数と見積り

EffortはProject全体で単位を固定した理想作業時間で、標準は `ideal-hours` とする。実装、直接確認、テスト、docs更新、通常見込むreview修正を含める。CI待ち、外部待ち、review待ち、merge待ちは含めない。

- ブランチ作成型Issue、spike、リポジトリ差分なしIssueは、`ready` へ進める前に正のEffortとEstimate Confidenceを持つ。
- 運用中に流入した `inbox` / `triaged` Issueは見積欄が空でもよいが、bootstrapへ渡す初期WBSの非epic Issueは事前検証のため両方を必須にする。
- epicのEffortとEstimate Confidenceは空欄にする。末端Issueだけを合計し、親子で二重計上しない。
- Sizeは差分量とreview量のordinal値である。Sizeを数値へ変換して合計しない。
- `ec0-low` で未知要素が作業境界まで揺らす場合は、readyにせずspikeへ分ける。

Estimate Confidenceの正本は次である。

- `ec0-low`: 未知要素が多く、再見積りの可能性が高い。
- `ec1-medium`: 境界は明確だが、一部未知要素がある。
- `ec2-high`: 類似実績、変更範囲、確認手順が揃っている。

# 容量とWIP上限

repo側の `.github/project/views.md` に、少なくとも次をProject運用設定として置く。

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
- 作業権取得済みIssueにはagentごとに独立worktreeを割り当てる。
- agentまたは作業環境枠が埋まっていれば新しい作業権を取得しない。レビュー、重いCI/共有環境、マージ待ちが上限なら、その下流へ新規投入しない。
- Draft PRとリポジトリ内で修正可能なレビュー/CI対応は実装枠、レビュー依頼後はレビュー枠、重いCIや共有fixture使用中はその専用枠、merge queue待ちはマージ枠を消費する。
- 枠が空いた、Issueがマージ/canceled/blockedになった、Effortや依存関係が変わった時に次の実行Waveを再計算する。

# Milestones

MilestoneはGitHub native milestoneを使う。Project fieldとして複製しない。

Milestoneはrelease/checkpointと締切目標を表す。先にMilestoneとdue dateを決め、その範囲に収まるようにIssue/WBSのForecast Start / Forecast Endを組む。IssueのForecastからMilestone期限を逆算しない。

期限や日付はMilestone名へ入れず、GitHub Milestoneのdue dateにだけ置く。Issue本文、PR本文、Project fieldにもMilestone期限を複製しない。

期限ありが基本のMilestone候補:

- `First Release`: 初回利用可能版。bootstrap既定で作成する。
- `v1 Release`: 安定版として公開・配布できる状態。
- `仕様・デザイン確定`: 主要仕様、UI/UX、非スコープが確定した状態。
- `データセット固定`: 学習・評価・公開対象のデータセットを固定した状態。
- `評価完了`: 評価指標、結果、再現手順が揃った状態。
- `論文投稿準備完了`: 論文、補足資料、artifact、チェックリストが投稿可能な状態。
- `ポスター完成`: 掲示・発表に使えるポスターが完成した状態。
- `投稿完了`: 投稿先への提出、査読用情報、保存先、公開先の準備が完了した状態。
- `一般公開`: docs、demo、artifact、release noteを含めて公開できる状態。

期限未定でも使えるMilestone候補:

- `法人設立`
- `外部審査`
- `共同研究契約`
- `データ利用許諾`

締切未定Milestoneはdue dateなしで作ってよい。ただしForecastの締切制約には使わない。

Milestone一覧を読む。

```bash
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100
```

Milestone due dateを変更する。

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

期限変更はMilestone due dateをSSoTにする。Issue本文、PR本文、Project fieldへMilestone期限を複製しない。Forecast Start / Forecast Endは、その期限に収まるように必要なIssueだけを更新する。

# GitHub labels

このskillではGitHub labelを使わない。

Type、Source、Status、Priority、Size、Effort、Estimate Confidence、Complexity、Risk、Agent TierはProject fieldをSSoTにする。GitHub labelへは複製しない。

分類、状態、起票元、優先度、見積もり、agent割り当てはすべてProject fieldで表す。新しいGitHub labelは定義しない。

Project fieldのfilterでIssueは絞り込めるため、labelをportable fallbackとして持たない。比較やsortでは `p2-high` の `2` のようにProject field optionの数値prefixを読む。

既存Project fieldのoption名は自動移行しない。Project側で必要なoption移行を手動で行う。

既存repositoryに残っているlabelは自動削除しない。不要なlabelはrepository側で手動整理する。

# Date fields

計画日と実績日は別fieldにする。

- `Forecast Start`: 計画開始日。`WBS/ロードマップ` viewで使う。
- `Forecast End`: 計画終了目標日。`WBS/ロードマップ` viewで使う。
- `Actual Start`: 実作業開始日。Issueをin-progressへ進める時に記録する。
- `Actual End`: 実終了日。doneまたはcanceledで終了を確認した時に記録する。

PR作成日、マージ日、Issue/PR close日はGitHub metadataをSSoTにする。Project fieldへ複製しない。

本文、PR本文、作業開始commentにはdate field assignmentを書かない。計画/実績の期間はProject fieldで見る。

Forecast Start / Forecast Endは計画上の作業期間であり、実績ではない。

日付はProject運用設定のタイムゾーンで解釈し、StartとEndを含む稼働日とする。休日は作業日数へ数えない。Date fieldは時刻を持たないため、直列Issueの同日引き継ぎは行わず、後続は次の稼働日以降に開始する。

- 期限付きMilestoneでは、Milestone due dateを先に決めてからIssue/WBSのForecastを組む。
- epicのForecastは子Issue群を包む期間にする。epicと子IssueのForecastが重なるのは正常である。
- ブランチ作成型Issue同士が直列依存する場合、後続IssueのForecast Startは、すべての `blocked by` 先のForecast Endより後の日付にする。
- GitHub ProjectsのDate fieldは時刻を持たないため、同日引き継ぎを前提にして直列IssueのForecastを同じ日に重ねない。必要ならIssueをさらに分けるか、前段のForecast Endを短くする。
- 依存関係がなくても、変更ファイル競合または実装/レビュー/CI/マージの容量競合があるIssueは同じ期間へ詰め込まない。

# Forecast変更

Forecast変更では、先にMilestone due date、Issue間の依存関係、sub-issue構造、変更競合グラフ、Effort、Estimate Confidence、稼働カレンダー、各WIP上限を読む。Issue本文のメタデータ行ではなく、Project fieldだけを更新する。

```bash
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 100
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 100
gh issue view ISSUE_NUMBER \
  --repo OWNER/REPO \
  --json number,title,milestone,parent,subIssuesSummary,blockedBy,blocking
```

Project itemのDate fieldを更新する。

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
2. canceled blockerを完了扱いせず、transitive downstreamを再トリアージする。
3. `ceil(Effort / 実装1枠・1稼働日あたりの有効Effort)` を実装作業日の初期値にする。
4. 依存関係、変更競合、実装WIPを満たすよう末端Issueを稼働日へ配置する。
5. レビュー、重いCI/共有環境、マージ待ちのWIPと予備日を加える。
6. epicのForecastを必要な末端Issue全体を包む期間へ集約する。epic Effortは合計しない。

Milestone実現可能性の確認では、必要な末端IssueがMilestone due dateまでに型別doneへ到達できるかを見る。超過する場合は日付だけを圧縮せず、scope削減、期限変更、依存関係の解消、容量追加の選択肢と影響を出す。選択が決まるまで計画を実現可能と報告しない。

期限変更で全Issueを機械的に同じ幅でずらさない。依存関係、競合、容量が許すIssueだけForecastを重ねる。epicのForecastは子Issue群を包む期間に直す。

# View説明の置き場所

GitHub Projectsのviewには説明文欄がない前提で運用する。viewの目的、filter、運用ルールは、このfileとcopyableな `assets/.github/project/views.md` に置く。

repo固有に公開したい場合は、対象repoの `.github/project/views.md` に同じ形式で保存する。Project本体にはview名とfield設定だけを置く。

# 標準view

標準viewは次の4つだけにする。

- `かんばん`
- `WBS/ロードマップ`
- `マージキュー候補`
- `Velocity`

ready、レビュー、blocked、高難度agent向けの専用viewは作らない。必要な確認は `かんばん` のStatus、filter、sort、visible fieldsで行う。

## かんばん

目的:

- 全体の進捗をStatus別に見る。
- ready、in-progress、in-review、blockedの詰まりを日次で確認する。
- 作業投入、レビュー待ち、阻害要因解除の入口にする。

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
- in-progressへ進める前に実装WIPと作業権取得結果を確認する。勝者のAgent Runだけを設定し、リポジトリ差分を作る場合は独立worktreeを作る。
- レビュー、重いCI/共有環境、マージ待ちの下流WIPが上限なら、新しいready Issueの作業権を取得せず、上流への投入を抑える。
- in-reviewではPR本文のclosing keyword、振る舞い、テストケース、確認手順、リスク、レビュー観点、required checksを見る。
- blockedではコメントに理由、解除者、依存Issue/PR/log、次の確認タイミングがあるか確認する。
- `c3-complex` または `r3-dangerous` を含む作業は人間のレビュー責任者を明確にする。
- doneとcanceledは通常表示しない。完了後の観察は `Velocity` で行う。

## WBS/ロードマップ

目的:

- WBS/Gantt相当の計画表示として使う。
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
- Milestone due dateを変更したら、そのMilestone配下のIssueだけForecastを見直す。
- WBS番号は作らない。構造はepic/sub-issue、順序はblocked by / blockingで表す。
- Statusは依存関係からの自動同期ではなく、運用状態として人間またはagentが確認して更新する。
- epicのForecastは子Issue群を包む期間で、子Issueと重なってよい。
- 直列依存するブランチ作成型Issue同士ではForecastを重ねない。後続IssueのForecast Startは、すべての `blocked by` 先のForecast Endより後の日付にする。
- 同じepic配下でも、依存関係、変更競合グラフ、実装/レビュー/CI/マージ容量が許す子IssueだけForecastを重ねてよい。
- 実績はActual Start、Actual Endで見る。ロードマップ上の計画日と混ぜない。
- 日付変更は計画の変更として扱い、Issue本文のmetadata行ではなくProject fieldだけを更新する。

## マージキュー候補

目的:

- 自動マージまたはマージキュー投入候補のPRを確認する。
- レビュー承認済みでrequired checksが揃ったPRをmainへ流す。

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

- closing keyword、linked Issue、base/head branch、マージキュー設定を確認してから自動マージを有効化する。
- required checkがrerun中または失敗中なら候補にしない。
- PR作成日、マージ状態、マージ日はGitHub PR metadataから読む。Project fieldへ複製しない。
- マージ後はdone条件を満たしてからActual EndをProject fieldへ記録する。
- Project field metadataや具体モデル名はPR本文へ書かない。

## Velocity

目的:

- 完了量、サイクルタイム、レビュー時間を週次で観察する。
- agent投入量とマージキューの詰まりをふりかえる。

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

- done件数、末端IssueのEffort合計、Size区分別件数、Scope別完了、Agent Tier別完了を週次で見る。epic Effortは集計しない。
- Sizeは順序尺度なので合計しない。Estimate Confidence別にForecast超過率とサイクルタイムを観察する。Actual Start / Actual Endは待ち時間を含むため、実Effortとは扱わない。
- Cycle timeはActual StartからActual Endまでを見る。
- レビュー時間やマージ待ち時間が必要な場合は、GitHub PR metadataのcreatedAt、mergedAt、レビュー状態から読む。
- 厳密な見積もり契約ではなく、throughputを観察してready投入量を調整するために使う。

# Sprintを導入するか

固定sprint commitmentは必須にしない。

理由:

- agent並列開発では投入可能量が動的に変わる。
- CI、レビュー、マージキューの詰まりで処理量が変わる。
- 割り込みIssueを柔軟に流す必要がある。

使うならIterationは観察窓として使う。

良い使い方:

- `かんばん` で現在のStatusと詰まりを見る。
- `WBS/ロードマップ` で計画日と依存関係を見る。
- `マージキュー候補` でmain統合前のPRだけを見る。
- `Velocity` を週次で観察する。

悪い使い方:

- sprint開始時に固定scopeを硬く約束する。
- agent投入量の変化を無視する。
- 期限変更のたびにIssueを大量編集する。
