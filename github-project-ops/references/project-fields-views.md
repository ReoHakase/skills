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

分類、状態、起票元、優先度、見積もり、agent割り当てはすべてProject fieldで表す。新しいGitHub labelは定義せず、Issue作成scriptもlabelを付けない。

Project fieldのfilterでIssueは絞り込めるため、labelをportable fallbackとして持たない。比較やsortでは `P2-high` の `2` のようにProject field optionの数値prefixを読む。

既存Project fieldのoption名は自動移行しない。`bootstrap-project-fields.sh` は既存fieldをskipするため、形容詞なしの旧optionから `P2-high` のような新optionへの変更はProject側で手動移行する。

既存repositoryに残っているlabelは自動削除しない。不要なlabelはrepository側で手動整理する。

# Kanban view

目的:

- 人間が全体進捗を把握する。
- agent作業中、review中、blockedを一目で見る。

設定:

- layout: board
- group by: Status
- slice by: ScopeまたはAgent Tier
- sort: Priority desc, Risk desc

# Ready Pool view

目的:

- すぐagentへ投入できるIssueを見る。

filter:

```text
status:Ready -is:blocked
```

group:

```text
Agent Tier
```

# Current Focus view

Sprintの代替。固定コミットメントではなく、現在注力する観察窓として使う。

Project field filter:

```text
Status = Ready, In Progress, In Review
Priority = P2-high, P3-critical
```

またはProjectのIteration fieldを使う。

# Review Queue view

filter:

```text
status:In Review
```

sort:

```text
Risk desc, Priority desc, updated asc
```

# Blocked view

filter:

```text
status:Blocked
```

表示field:

- blocked by
- blocking
- assignee
- risk
- updated

# Frontier Queue view

Project field filter:

```text
Agent Tier = agent:frontier
Status = Ready, In Progress, In Review
```

目的:

- 高性能agentまたは人間reviewが必要な作業を分ける。

# Merge Queue Candidate view

filter:

```text
status:In Review is:pr review:approved
```

目的:

- auto-merge対象候補を確認する。

# Velocity view

GitHub Projects単体では厳密なVelocity chartは弱い。次の近似を使う。

- Done count per week
- Done Size sum per week
- Done by Scope
- Done by Agent Tier
- Cycle time: Started AtからMerged Atまで
- Review time: PR作成からmergeまで

`report-project-health.sh` で簡易集計する。

# Sprintを導入するか

固定sprint commitmentは必須にしない。

理由:

- agent並列開発では投入可能量が動的に変わる。
- CI、review、merge queueの詰まりでthroughputが変わる。
- 割り込みIssueを柔軟に流す必要がある。

使うならIterationは観察窓として使う。

良い使い方:

- 今週見る範囲をCurrent Focusに置く。
- P2-high/P3-criticalとblockedを重点監視する。
- Velocityを週次で観察する。

悪い使い方:

- sprint開始時に固定scopeを硬く約束する。
- agent投入量の変化を無視する。
- 期限変更のたびにIssueを大量編集する。
