---
name: github-project-ops
description: Agentで効率的に並列Issue処理することを前提に、GitHub Projects、Issues、sub-issues、blocked by/blocking、merge queue、auto-mergeを使って、WBS作成、アジャイルIssue駆動開発、1 issue = 1 branch = 1 PR運用を行う日本語skill。複数人と複数agentがタスク管理のSSoTとして使う。
---

# 目的

Agentで効率的に並列Issue処理することを前提とした、GitHub Projectsを使ったWBS作成とアジャイルIssue駆動開発のためのskill。

このskillは、複数人と複数agentがタスク管理のSSoTとしてGitHub Projects、Issues、sub-issues、blocked by/blocking、PR、merge queueを使うための運用規約を定義する。

# 基本原則

SSoTはGitHub上のProject、Issue、PRである。

- 計画構造はGitHub Projectsに置く。
- 作業単位はGitHub Issueに置く。
- 親子階層はsub-issueで表す。
- 実行順序はblocked by / blockingで表す。
- 実装差分はPRで表す。
- main統合はmerge queueで表す。

`assets/` は、対象repositoryへコピーして使う設定・サンプルデータを置く。Issue Forms、PR template、merge_group対応CI、Project view説明、Project field JSON、backlog JSONはここに置く。

`references/` は、agentが必要に応じて読む手順、判断基準、template、記入済み例を置く。templateと記入済み例はuse-caseごとのreference内で隣接させる。

このskillはshell scriptを配らない。GitHubの実操作は、GitHub MCPで実状態を確認してから `gh` / `gh api` の明示コマンドで行う。

# Reference routing

必要なreferenceだけを読む。

| Task                                                                                             | Read                                  |
| ------------------------------------------------------------------------------------------------ | ------------------------------------- |
| Project fields、no-label、date fields、views、copyable assets                                    | `references/project-setup.md`         |
| WBS分解、Issue粒度、Issue body template、epic/feature/bug起票、sub-issue、dependency             | `references/issue-authoring.md`       |
| Status遷移、Ready/In Progress/In Review/Blocked判断、lifecycle comment template、状態別例        | `references/issue-lifecycle.md`       |
| Priority / Size / Complexity / Risk / Agent Tier判定                                             | `references/triage-and-agent-tier.md` |
| PR body template、In Review comment方針、merge commit、merge queue、auto-merge、`merge_group` CI | `references/pr-and-merge.md`          |
| skill本文、references、assetsの経験的検証                                                        | `references/empirical-validation.md`  |

# 変更前に発見する値

Issue、PR、Project itemを変更する前に、GitHub上の実状態を読む。推測で埋めてよいのは計画案や下書きだけで、実行コマンドに渡す値は確認済みの値にする。

最低限確認する値:

- `OWNER/REPO`
- Project number / owner
- Issue number、PR number、Issue/PR URL
- parent / sub-issue / blocked by / blocking
- Status、Type、Scope、Priority、Size、Complexity、Risk、Agent Tier
- Assignee、Reviewer Owner、Agent Harness、Agent Model、Branch

不明な値は `<PROJECT_NUMBER>` のようなplaceholderとして明示し、実行前にGitHub MCP、`gh issue view`、`gh pr view`、`gh project item-list`、`gh api` のいずれかで確認する。Issue本文やPR本文の具体化に必要な受け入れ条件、非スコープ、確認手順が足りない場合は、推測で確定せず、draftとして分けるか追加確認する。

# GitHub MCP / gh CLI / gh apiの使い分け

GitHub MCPは対話的な確認、探索、状況整理、自然言語での操作補助に使う。

- Projectの状態を読む。
- IssueやPRの要約を作る。
- どのIssueを分割するべきか検討する。
- agentに実装対象Issueを読ませる。
- PR reviewやCI失敗の原因を整理する。

再現可能な操作はgh CLIで行う。

- Issue作成
- sub-issue設定
- blocked by / blocking設定
- linked branch作成
- PR作成
- auto-merge投入

gh CLIの高水準コマンドで足りない場合だけ、`gh api` または `gh api graphql` を使う。生のcurl POSTは使わない。

# Issue / PR invariants

1つのbranchable issueは1つのbranchを持つ。1つのbranchは1つのPRに対応する。PR本文は必ず `Closes #<issue-number>`、`Fixes #<issue-number>`、`Resolves #<issue-number>` のいずれかを含む。

epic issueは原則branchを持たない。spike issueは調査成果物を閉じるPRを持ってよい。

IssueタイトルとPRタイトルは、Conventional Commits風にしない。TypeとScopeはProject fieldへ書くため、titleには書かない。titleには、何ができるようになるか、何が直るかを自然な日本語で書く。

branch名は読みやすさと自動化を優先し、次の形式にする。

```text
<issue-number>/<type>-<scope>-<short-slug>
```

例:

```text
123/feat-ui-seekbar-chapters
124/fix-db-work-time-offset
125/docs-ops-queue-rules
```

Issue titleとbranch名を一致させる必要はない。

# Project metadata policy

このskillではGitHub labelを使わない。Type、Source、Status、Priority、Size、Complexity、Risk、Agent TierはProject fieldをSSoTにする。

Project fieldにあるmetadataはIssue本文、PR本文、作業開始コメントへ書かない。本文には実現内容、背景、受け入れ条件、確認手順、実装メモだけを書く。

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

# Issue lifecycle

標準Status:

```text
Inbox -> Triaged -> Ready -> In Progress -> In Review -> Done
                        In Progress -> Blocked -> In Progress
                        In Review -> Blocked -> In Review
Inbox/Triaged/Ready/In Progress/In Review -> Canceled
```

`Needs Info` と `Ready to Merge` は使わない。更新負荷が高く、agent運用で状態が細かくなりすぎるため。

作業開始時の必須操作:

1. `blocked by` を確認する。未解決のblockerがある場合は作業を開始せず、StatusをBlockedに戻すか、blocker解消を開始条件にする。
2. IssueをIn Progressにする。
3. Assigneeを必ず設定する。
4. agent自律作業でも、開発環境の持ち主またはreview責任者の人間をAssigneeにする。
5. Agent Tier、Agent Harness、Agent ModelをProject fieldへ記録する。
6. linked branchを作る。

# Merge policy

採用するmain統合方式は、merge commit + merge queue + auto-merge。

- merge commitを使う。
- squash mergeとrebase mergeは標準運用では使わない。
- Require linear historyは使わない。
- mainへ直接pushしない。
- PR単体CIとmerge_group CIを両方走らせる。
- 承認済みPRはauto-mergeを有効化してmerge queueへ流す。
- merge queueのMaximum group sizeは100を許容する。ただしCIを1回にまとめる設定ではない。
