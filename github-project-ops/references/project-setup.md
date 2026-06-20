# Project setup

Project fields、no-label policy、date fields、views、copyable assetsを扱うときに読む。

# 目次

- Copyable assets
- Project fields
- GitHub labels
- Date fields
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

| Field          | Type          | Values                                                                              |
| -------------- | ------------- | ----------------------------------------------------------------------------------- |
| Status         | Single select | inbox, triaged, ready, in-progress, in-review, blocked, done, canceled              |
| Type           | Single select | epic, feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert, spike |
| Scope          | Text          | ui, api, db, infraなど。repoごとに自由定義                                          |
| Priority       | Single select | p0-optional, p1-normal, p2-high, p3-critical                                        |
| Size           | Single select | s0-tiny, s1-small, s2-medium, s3-large                                              |
| Complexity     | Single select | c0-none, c1-simple, c2-moderate, c3-complex                                         |
| Risk           | Single select | r0-none, r1-safe, r2-moderate, r3-dangerous                                         |
| Agent Tier     | Single select | agent-fast, agent-standard, agent-frontier                                          |
| Agent Harness  | Single select | codex, claude-code, cursor, human, other                                            |
| Agent Model    | Text          | GPT 5.5 (xhigh), Opus 4.8 (medium), Composer 2.5など。作業開始時に記録              |
| Reviewer Owner | Text          | agent実行環境の持ち主、またはレビュー責任者のGitHub login                           |
| Branch         | Text          | 123/feat-ui-example                                                                 |
| Source         | Single select | human, agent, debug-log, chat, inquiry, ci, dependency, security, docs              |
| Forecast Start | Date          | 計画開始日。WBS/ロードマップで使う                                                  |
| Forecast End   | Date          | 計画終了目標日。WBS/ロードマップで使う                                              |
| Actual Start   | Date          | 実作業開始日                                                                        |
| Actual End     | Date          | 実終了日                                                                            |

Issue時点では具体的なモデル名まで確定させない。backlog/triaged/readyではAgent Tierだけでよい。作業開始時にAgent HarnessとAgent ModelをProject fieldへ記録する。

Issue/PRタイトルにTypeやScopeを入れない。TypeとScopeはProject fieldで見る。

# GitHub labels

このskillではGitHub labelを使わない。

Type、Source、Status、Priority、Size、Complexity、Risk、Agent TierはProject fieldをSSoTにする。GitHub labelへは複製しない。

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

本文、PR body、作業開始commentにはdate field assignmentを書かない。計画/実績の期間はProject fieldで見る。

Forecast Start / Forecast Endは計画上の作業期間であり、実績ではない。

- epicのForecastは子Issue群を包む期間にする。epicと子IssueのForecastが重なるのは正常である。
- branchable Issue同士が直列依存する場合、後続IssueのForecast Startは、すべての `blocked by` 先のForecast Endより後の日付にする。
- GitHub ProjectsのDate fieldは時刻を持たないため、同日引き継ぎを前提にして直列IssueのForecastを同じ日に重ねない。必要ならIssueをさらに分けるか、前段のForecast Endを短くする。
- blocked by / blockingがない子Issue同士は並列化できるため、Forecastを重ねてよい。

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
- Complexity
- Risk
- Agent Tier
- Assignee
- Reviewer Owner
- Branch
- Actual Start

運用ルール:

- readyに置くのは、受け入れ条件、非スコープ、確認手順、未解決blockerなしを確認済みのbranchable Issueだけにする。仕様確定済みでも前段Issue待ちならblockedにする。
- `blocking` はこのIssueが後続Issueの前提であるという意味なのでreadyと両立する。`blocked by` が未解決ならreadyと両立しない。
- Statusは `blocked by` / `blocking` から自動同期しない。upstream PR、Figma design、権限、CI障害、設計判断待ちなどでblockedになるIssueもあるため、かんばんではStatusとblocked commentを一緒に読む。
- in-progressへ進める前にblocked byを再確認する。未解決の阻害要因がある場合は作業開始しない。
- in-reviewではPR本文のclosing keyword、確認手順、リスク、レビュー観点、required checksを見る。
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
- Risk
- Agent Tier
- Forecast Start
- Forecast End
- blocked by
- blocking

運用ルール:

- date fieldsは `Forecast Start` / `Forecast End` を使う。
- WBS番号は作らない。構造はepic/sub-issue、順序はblocked by / blockingで表す。
- Statusは依存関係からの自動同期ではなく、運用状態として人間またはagentが確認して更新する。
- epicのForecastは子Issue群を包む期間で、子Issueと重なってよい。
- 直列依存するbranchable Issue同士ではForecastを重ねない。後続IssueのForecast Startは、すべての `blocked by` 先のForecast Endより後の日付にする。
- 同じepic配下でもblocked by / blockingがない子Issue同士は並列化できるため、Forecastを重ねてよい。
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
- Complexity
- Risk
- Agent Tier
- Actual Start
- Actual End

運用ルール:

- done count、Size合計、Scope別完了、Agent Tier別完了を週次で見る。
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
