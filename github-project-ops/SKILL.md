---
name: github-project-ops
description: Agentで効率的に並列Issue処理することを前提に、GitHub Projects、Issues、sub-issues、blocked by/blocking、merge queue、auto-mergeを使って、WBS作成、アジャイルIssue駆動開発、1 issue = 1 branch = 1 PR運用を行う日本語skill。複数人と複数agentがタスク管理のSSoTとして使う。
---

# 目的

Agentで効率的に並列Issue処理することを前提とした、GitHub Projectsを使ったWBS作成とアジャイルIssue駆動開発のためのskill。

このskillは、複数人と複数agentがタスク管理のSSoTとしてGitHub Projects、Issues、sub-issues、blocked by/blocking、PR、merge queueを使うための運用規約を定義する。

# 適用する場面

- 大型ソフトウェア開発をGitHub ProjectsとIssuesで分解する。
- WBS、Kanban、Roadmap、Current Focus、Review Queue、Blocked Queue、VelocityをGitHub Projectsで管理する。
- 複数agentが並列にIssueを処理できるように、低コンテクストで非属人的なIssueを作る。
- 1 issue = 1 branch = 1 PRを維持する。
- mainを壊さず、merge commit + merge queue + auto-mergeでPRを高速に流す。
- GitHub MCPで対話的に確認し、gh CLIとgh apiで再現可能に操作する。

# 基本原則

## SSoT

SSoTはGitHub上のProject、Issue、PRである。

- 計画構造はGitHub Projectsに置く。
- 作業単位はGitHub Issueに置く。
- 親子階層はsub-issueで表す。
- 実行順序はblocked by / blockingで表す。
- 実装差分はPRで表す。
- main統合はmerge queueで表す。

`.github/` とskill内のexamples/scriptsは初期化、検証、再現、教育のために使う。GitHub上の動的状態を上書きするために使わない。

## 1 issue = 1 branch = 1 PR

- 1つのbranchable issueは1つのbranchを持つ。
- 1つのbranchは1つのPRに対応する。
- PR本文は必ず `Closes #<issue-number>`、`Fixes #<issue-number>`、`Resolves #<issue-number>` のいずれかを含む。
- epic issueは原則branchを持たない。
- spike issueは調査成果物を閉じるPRを持ってよい。

## titleは自然な日本語にする

IssueタイトルとPRタイトルは、Conventional Commits風にしない。

悪い例:

```text
feat(ui): シークバーに章トラックを追加する
fix(db): work_time_msのoffset計算を修正する
```

良い例:

```text
シークバーに章トラックを表示してクリックで移動できるようにする
分割動画の連結時刻から各partのローカル時刻を正しく逆引きする
```

TypeとScopeはProject fieldへ書くため、titleには書かない。titleには、何ができるようになるか、何が直るかを自然な日本語で書く。

## branch名は機械的にする

branch名は読みやすさと自動化を優先し、次の形式にする。

```text
<issue-number>/<type>-<scope>-<short-slug>
```

例:

```text
123/feat-ui-seekbar-chapters
124/fix-db-work-time-offset
125/docs-ops-merge-queue-policy
```

Issue titleとbranch名を一致させる必要はない。

# GitHub MCP / gh CLI / gh apiの使い分け

## GitHub MCP

GitHub MCPは対話的な確認、探索、状況整理、自然言語での操作補助に使う。

- Projectの状態を読む。
- IssueやPRの要約を作る。
- どのIssueを分割するべきか検討する。
- agentに実装対象Issueを読ませる。
- PR reviewやCI失敗の原因を整理する。

## gh CLI

再現可能な操作はgh CLIで行う。

- label同期
- Project field作成
- Issue作成
- sub-issue設定
- blocked by / blocking設定
- linked branch作成
- PR作成
- auto-merge投入

## gh api

gh CLIの高水準コマンドで足りない場合だけ、`gh api` または `gh api graphql` を使う。

生のcurl POSTは使わない。script内でもGitHub API呼び出しは `gh api` に寄せる。

# Project fields

推奨Project fieldsは次。

| Field          | Type          | Values                                                                              |
| -------------- | ------------- | ----------------------------------------------------------------------------------- |
| Status         | Single select | Inbox, Triaged, Ready, In Progress, In Review, Blocked, Done, Canceled              |
| Type           | Single select | epic, feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert, spike |
| Scope          | Text          | ui, api, db, infraなど。repoごとに自由定義                                          |
| Priority       | Single select | P0, P1, P2, P3                                                                      |
| Size           | Single select | S0, S1, S2, S3                                                                      |
| Complexity     | Single select | C0, C1, C2, C3                                                                      |
| Risk           | Single select | R0, R1, R2, R3                                                                      |
| Agent Tier     | Single select | agent:fast, agent:standard, agent:frontier                                          |
| Agent Harness  | Single select | Codex, Claude Code, Cursor, Human, Other                                            |
| Agent Model    | Text          | GPT 5.5 (xhigh), Opus 4.8 (medium), Composer 2.5など。作業開始時に記録              |
| Reviewer Owner | Text          | agent実行環境の持ち主、またはreview責任者のGitHub login                             |
| Branch         | Text          | 123/feat-ui-example                                                                 |
| Source         | Single select | human, agent, debug-log, chat, inquiry, ci, dependency, security, docs              |
| Target Date    | Date          | 期限がある場合だけ                                                                  |
| Started At     | Date          | 作業開始日                                                                          |
| Merged At      | Date          | merge日                                                                             |

Issue時点では具体的なモデル名まで確定させない。Backlog/Triaged/ReadyではAgent Tierだけでよい。作業開始時にAgent HarnessとAgent ModelをProject fieldへ記録する。

# Typeの定義

TypeはConventional Commitsのtype集合に `epic` と `spike` を足す。

- `epic`: 複数Issueの親。原則PRを持たない。
- `feat`: ユーザー価値または運用価値を追加する。
- `fix`: 期待動作から外れた不具合を直す。
- `docs`: ドキュメントだけを変更する。
- `style`: 挙動を変えない整形、フォーマット、命名微修正。
- `refactor`: 挙動を変えず構造を改善する。
- `perf`: 性能改善。
- `test`: テスト追加・修正。
- `build`: build system、依存解決、packaging。
- `ci`: CI/CD、branch protection、merge queue、workflow。
- `chore`: 開発補助、掃除、非機能的メンテナンス。
- `revert`: 既存変更のrevert。
- `spike`: 実装前調査、設計検証、技術検証。成果物と次Issueを作る。

# Priority / Size / Complexity / Risk / Agent Tier

詳細基準は `references/estimation-and-agent-tier.md` を参照する。

要点:

- Priorityは0が最低、3が最高。P1とP2が通常作業の大半を占める。
- Sizeは変更量とレビュー量。
- Complexityは設計・未知性・推論量。
- Riskはmain、データ、セキュリティ、運用、利用者影響の危険度。
- Agent Tierは `max(Complexity, Risk)` を基準に決める。

# Issue lifecycle

詳細は `references/issue-lifecycle.md` を参照する。

標準Status:

```text
Inbox -> Triaged -> Ready -> In Progress -> In Review -> Done
                        In Progress -> Blocked -> In Progress
                        In Review -> Blocked -> In Review
Inbox/Triaged/Ready/In Progress/In Review -> Canceled
```

`Needs Info` と `Ready to Merge` は使わない。更新負荷が高く、agent運用で状態が細かくなりすぎるため。

作業開始時の必須操作:

1. IssueをIn Progressにする。
2. Assigneeを必ず設定する。
3. agent自律作業でも、開発環境の持ち主またはreview責任者の人間をAssigneeにする。
4. Agent Tier、Agent Harness、Agent ModelをProject fieldへ記録する。
5. linked branchを作る。

# WBS分解

WBS番号や独自keyは使わない。

GitHub上のIssue number、sub-issue、blocked by / blockingで十分に構造を表せるため、独自の `SJ-1.2.3` のような番号を持ち込まない。

分解の目的は総Issue数を減らすことではなく、完成までの直列Issue数を減らすこと。並列実行可能なIssueは複数人・複数agentが同時に処理できる前提で分ける。

WBS作成時の手順:

1. まずepicを作る。
2. epic配下にcontract、spike、feature、test、docsをsub-issueとして作る。
3. 親子関係はsub-issueで表す。
4. 実行順序はblocked by / blockingで表す。
5. 先にinterface、schema、contractを切り、後続実装を並列化する。
6. C3/R3はfeature化前にspikeを切る。

# Issue粒度

branchable issueは次を満たす。

- 1 PRで閉じられる。
- 受け入れ条件が第三者に判定可能。
- 主componentが1つ、または明確なinterface境界が1つ。
- 非スコープが明記されている。
- 依存Issueがblocked by / blockingで表されている。
- Issue本文だけで作業できる。
- テストまたは確認手順がある。

# Merge policy

採用するmain統合方式は、merge commit + merge queue + auto-merge。

- merge commitを使う。
- squash mergeとrebase mergeは標準運用では使わない。
- Require linear historyは使わない。
- mainへ直接pushしない。
- PR単体CIとmerge_group CIを両方走らせる。
- 承認済みPRはauto-mergeを有効化してmerge queueへ流す。
- merge queueのMaximum group sizeは100を許容する。ただしCIを1回にまとめる設定ではない。

詳細は `references/merge-queue-policy.md` を参照する。

# PR body

PR本文には具体的なagentモデル名を書かない。Agent HarnessとAgent ModelはProject fieldへ記録する。

PR本文に必須の要素:

- Summary
- Linked Issue
- Scope
- Verification
- Risk
- Review Focus
- `Closes #<issue-number>` または同等のclosing keyword

# 使用するscript

再現可能な操作には `scripts/` を使う。

- `bootstrap-labels.sh`
- `bootstrap-project-fields.sh`
- `create-issues-from-backlog.sh`
- `start-issue-work.sh`
- `set-project-field-by-url.sh`
- `create-linked-branch.sh`
- `create-pr-from-issue.sh`
- `configure-repo-merge-methods.sh`
- `check-merge-queue-readiness.sh`
- `validate-issue-body.sh`
- `validate-pr-body.sh`
- `report-project-health.sh`

scriptはshellで書き、gh CLI、gh api、jq、curlだけを前提にする。
