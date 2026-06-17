# Project fields / labels / views

# Type field

値:

```text
epic, feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert, spike
```

Issue/PRタイトルにtypeやscopeを入れない。TypeとScopeはProject fieldで見る。

# labels

labelsはProject fieldの補助。GitHub検索、通知、CLIで使いやすくするために残す。

推奨label group:

- `type:*`
- `priority:*`
- `size:*`
- `complexity:*`
- `risk:*`
- `agent:*`
- `source:*`
- `status:*`

Project fieldがSSoTだが、labelはgrepしやすいportable fallbackとして使う。

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

filter:

```text
status:Ready,In Progress,In Review priority:>=P2
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

filter:

```text
agent:frontier status:Ready,In Progress,In Review
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
- P2/P3とblockedを重点監視する。
- Velocityを週次で観察する。

悪い使い方:

- sprint開始時に固定scopeを硬く約束する。
- agent投入量の変化を無視する。
- 期限変更のたびにIssueを大量編集する。
