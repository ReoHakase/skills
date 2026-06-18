# Project fields / views

# Type field

値:

```text
epic, feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert, spike
```

Issue/PRタイトルにtypeやscopeを入れない。TypeとScopeはProject fieldで見る。

# GitHub labels

このskillではGitHub labelを使わない。

Type、Source、Status、Priority、Size、Complexity、Risk、Agent TierはProject fieldをSSoTにする。GitHub labelへは複製しない。

分類、状態、起票元、優先度、見積もり、agent割り当てはすべてProject fieldで表す。新しいGitHub labelは定義しない。

Project fieldのfilterでIssueは絞り込めるため、labelをportable fallbackとして持たない。比較やsortでは `P2-high` の `2` のようにProject field optionの数値prefixを読む。

既存Project fieldのoption名は自動移行しない。Project側で必要なoption移行を手動で行う。

既存repositoryに残っているlabelは自動削除しない。不要なlabelはrepository側で手動整理する。

# Date fields

計画日と実績日は別fieldにする。

- `Forecast Start`: 計画開始日。`WBS/ロードマップ` viewで使う。
- `Forecast End`: 計画終了目標日。`WBS/ロードマップ` viewで使う。
- `Actual Start`: 実作業開始日。IssueをIn Progressへ進める時に記録する。
- `Actual End`: 実終了日。DoneまたはCanceledで終了を確認した時に記録する。

PR作成日、merge日、Issue/PR close日はGitHub metadataをSSoTにする。Project fieldへ複製しない。

本文、PR body、作業開始commentにはdate field assignmentを書かない。計画/実績の期間はProject fieldで見る。

# View説明の置き場所

GitHub Projectsのviewには説明文欄がない前提で運用する。viewの目的、filter、運用ルールは、この `references/project-fields-views.md` とcopyableな `examples/project-views.md` に置く。

repo固有に公開したい場合は、対象repoの `.github/project/views.md` に同じ形式で保存する。Project本体にはview名とfield設定だけを置く。

# 標準view

標準viewは次の4つだけにする。

- `かんばん`
- `WBS/ロードマップ`
- `マージキュー候補`
- `Velocity`

Ready、review、blocked、高難度agent向けの専用viewは作らない。必要な確認は `かんばん` のStatus、filter、sort、visible fieldsで行う。

# かんばん

目的:

- 全体の進捗をStatus別に見る。
- Ready、In Progress、In Review、Blockedの詰まりを日次で確認する。
- 作業投入、review待ち、blocker解除の入口にする。

Layout:

- board

Filter:

- Project field: Status = Inbox, Triaged, Ready, In Progress, In Review, Blocked

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

- Readyに置くのは、受け入れ条件、非スコープ、確認手順、blocker解消を確認済みのIssueだけにする。
- In Progressへ進める前にblocked byを再確認する。未解決blockerがある場合は作業開始しない。
- In ReviewではPR本文のclosing keyword、確認手順、リスク、レビュー観点、required checksを見る。
- Blockedではcommentに理由、解除者、依存Issue/PR/log、次の確認タイミングがあるか確認する。
- `C3-complex` または `R3-dangerous` を含む作業は人間review責任者を明確にする。
- DoneとCanceledは通常表示しない。完了後の観察は `Velocity` で行う。

# WBS/ロードマップ

目的:

- WBS/Gantt相当の計画表示として使う。
- 作業の構造と順序を、epic、sub-issue、blocked by / blockingで見る。
- 計画開始日と計画終了目標日を確認する。

Layout:

- roadmap

Filter:

- Project field: Forecast Start is not empty
- Project field: Forecast End is not empty
- Project field: Status = Triaged, Ready, In Progress, In Review, Blocked, Done

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
- 実績はActual Start、Actual Endで見る。ロードマップ上の計画日と混ぜない。
- 日付変更は計画の変更として扱い、Issue本文のmetadata行ではなくProject fieldだけを更新する。

# マージキュー候補

目的:

- auto-mergeまたはmerge queue投入候補のPRを確認する。
- review承認済みでrequired checksが揃ったPRをmainへ流す。

Layout:

- table

Filter:

- Project field: Status = In Review
- GitHub PR: review approved
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
- merge後はDone条件を満たしてからActual EndをProject fieldへ記録する。
- Project field metadataや具体モデル名はPR本文へ書かない。

# Velocity

目的:

- 完了量、cycle time、review timeを週次で観察する。
- agent投入量とmerge queueの詰まりをふりかえる。

Layout:

- table

Filter:

- Project field: Status = Done
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

- Done count、Size合計、Scope別完了、Agent Tier別完了を週次で見る。
- Cycle timeはActual StartからActual Endまでを見る。
- review timeやmerge待ち時間が必要な場合は、GitHub PR metadataのcreatedAt、mergedAt、review状態から読む。
- 厳密な見積もり契約ではなく、throughputを観察してReady投入量を調整するために使う。

# Sprintを導入するか

固定sprint commitmentは必須にしない。

理由:

- agent並列開発では投入可能量が動的に変わる。
- CI、review、merge queueの詰まりでthroughputが変わる。
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
