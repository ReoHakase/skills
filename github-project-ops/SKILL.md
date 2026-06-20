---
name: github-project-ops
description: Agentで効率的に並列Issue処理することを前提に、GitHub Projects、Milestones、Issues、sub-issues、blocked by/blocking、マージキュー、自動マージを使って、WBS作成、Project/Milestone導入・解除、アジャイルIssue駆動開発、1 issue = 1 branch = 1 PR運用を行う日本語skill。複数人と複数agentがタスク管理のSSoTとして使う。
---

# 目的

Agentで効率的に並列Issue処理することを前提とした、GitHub Projectsを使ったWBS作成とアジャイルIssue駆動開発のためのskill。

このskillは、複数人と複数agentがタスク管理のSSoTとしてGitHub Projects、Issues、sub-issues、blocked by/blocking、PR、マージキューを使うための運用規約を定義する。

# 基本原則

SSoTはGitHub上のProject、Issue、PRである。

- 計画構造はGitHub Projectsに置く。
- 作業単位はGitHub Issueに置く。
- 親子階層はsub-issueで表す。
- 実行順序はblocked by / blockingで表す。
- release/checkpointと締切目標はGitHub Milestoneで表す。
- 実装差分はPRで表す。
- main統合はマージキューで表す。

`assets/` は、対象repositoryへコピーして使う設定・サンプルデータ、または対象repositoryに合わせて編集して使うtemplateを置く。Issue Forms、PR template、merge_group対応CI、Project view説明、Project field JSON、backlog JSON、bulk bootstrap用templateはここに置く。
Project field JSONは `assets/project-fields.json` を正本にし、一括作成テンプレートはこのJSONを読む。

`references/` は、agentが必要に応じて読む手順、判断基準、template、記入済み例を置く。templateと記入済み例はuse-caseごとのreference内で隣接させる。

このskillはそのまま実行するturnkey shell scriptを配らない。GitHubの実操作は、GitHub MCPで実状態を確認してから `gh` / `gh api` の明示コマンドで行う。大量WBS起票では `assets/project-bootstrap-template.py` を対象repository向けに編集して使ってよい。

# Reference routing

必要なreferenceだけを読む。

| Task                                                                                                | Read                                  |
| --------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Project fields、Milestone、期限変更、Forecast運用、no-label、date fields、views、copyable assets    | `references/project-setup.md`         |
| Project作成、Milestone作成、bulk WBS setup、Project item field一括設定、GraphQL fallback、template  | `references/project-bootstrap.md`     |
| WBS分解、Issue粒度、Issue body template、epic/feature/bug起票、sub-issue、dependency、直列Forecast  | `references/issue-authoring.md`       |
| Status遷移、epic status、ready/blocked判断、lifecycle comment template、状態別例                    | `references/issue-lifecycle.md`       |
| Priority / Size / Complexity / Risk / Agent Tier判定                                                | `references/triage-and-agent-tier.md` |
| PR body template、in-review comment方針、マージコミット、マージキュー、自動マージ、`merge_group` CI | `references/pr-and-merge.md`          |
| Project/Milestone解除、Project item削除、repo側copyable assets削除、破壊的削除の確認                | `references/uninstall.md`             |
| skill本文、references、assetsの経験的検証                                                           | `references/empirical-validation.md`  |

# 変更前に発見する値

Issue、PR、Project itemを変更する前に、GitHub上の実状態を読む。推測で埋めてよいのは計画案や下書きだけで、実行コマンドに渡す値は確認済みの値にする。

最低限確認する値:

- `OWNER/REPO`
- Project number / owner
- Project item ID
- Milestone title / number / due date
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
- PRレビューやCI失敗の原因を整理する。

再現可能な操作はgh CLIで行う。

- Issue作成
- Milestone作成
- IssueへのMilestone割当
- sub-issue設定
- blocked by / blocking設定
- 紐づくブランチ作成
- PR作成
- 自動マージ投入

gh CLIの高水準コマンドで足りない場合だけ、`gh api` または `gh api graphql` を使う。生のcurl POSTは使わない。

# Issue / PR invariants

1つのブランチ可能Issueは1つのブランチを持つ。1つのブランチは1つのPRに対応する。PR本文は必ず `Closes #<issue-number>`、`Fixes #<issue-number>`、`Resolves #<issue-number>` のいずれかを含む。

epic issueは原則ブランチを持たない。spike issueは調査成果物を閉じるPRを持ってよい。

IssueタイトルとPRタイトルは、Conventional Commits風にしない。TypeとScopeはProject fieldへ書くため、titleには書かない。titleには、何ができるようになるか、何が直るかを自然な日本語で書く。

Issue本文やPR本文で既存Issue/PRやコミットを参照するときは、同一repositoryなら `#123` や短いコミットSHAだけを書く。GitHubが自動リンクとホバー表示/プレビューで参照先を表示するため、titleを併記しない。

ブランチ名は読みやすさと自動化を優先し、次の形式にする。

```text
<issue-number>/<type>-<scope>-<short-slug>
```

例:

```text
123/feat-ui-seekbar-chapters
124/fix-db-work-time-offset
125/docs-ops-ci-rules
```

Issue titleとブランチ名を一致させる必要はない。

# Project metadata policy

このskillではGitHub labelを使わない。Type、Source、Status、Priority、Size、Complexity、Risk、Agent TierはProject fieldをSSoTにする。

Project fieldにあるmetadataはIssue本文、PR本文、作業開始コメントへ書かない。sub-issue、blocked by / blockingもGitHub metadataをSSoTにし、Issue本文にsub-issue一覧や依存関係sectionとして重複させない。Issue本文には検証可能な最新情報だけを書く。変更予定、注意点、未確定メモのような一時情報はコメントへ残す。

Issue時点では具体的なモデル名まで確定させない。backlog/triaged/readyではAgent Tierだけでよい。作業開始時にAgent HarnessとAgent ModelをProject fieldへ記録する。

# Milestone policy

MilestoneはProject fieldではなく、GitHub native milestoneを使う。Milestone due dateを先に決め、その締切目標からIssue/WBSのForecast Start / Forecast Endを組む。IssueのForecastからMilestone期限を逆算しない。

締切未定のMilestoneは必要に応じてdue dateなしで作ってよい。Issue本文、PR本文、Project fieldにはMilestone期限を複製しない。

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
- `ci`: CI/CD、ブランチ保護、マージキュー、ワークフロー。
- `chore`: 開発補助、掃除、非機能的メンテナンス。
- `revert`: 既存変更のrevert。
- `spike`: 実装前調査、設計検証、技術検証。成果物と次Issueを作る。

# Issue lifecycle

`ready` は「仕様が確定している」ではなく「今すぐ作業開始できる」という意味で使う。未解決の `blocked by` が作業開始を止めるIssueは `ready` にしない。

`blocking` は「このIssueが後続Issueの前提である」という関係であり、`ready` と両立する。`blocked by` は「このIssueが前段Issueを待っている」というIssue間関係であり、未解決なら `blocked` にする。

Statusは `blocked by` / `blocking` から自動同期しない。`blocked` にはupstream PR、Figma design、権限、CI障害、設計判断待ちなど、GitHub Issue dependencyでは表せない阻害要因も含む。Issue dependencyは構造化されたIssue間依存、Statusはかんばん上の運用状態として扱う。

epic issueは原則ブランチを持たないため、`ready` にしない。epicのStatusは子Issue群の進行状態を要約するroll-upとして扱う。

標準Status:

```text
inbox -> triaged -> ready -> in-progress -> in-review -> done
          triaged -> blocked -> ready
                     ready -> blocked -> ready
                        in-progress -> blocked -> in-progress
                        in-review -> blocked -> in-review
inbox/triaged/ready/in-progress/in-review -> canceled
```

`needs-info` と `ready-to-merge` は使わない。更新負荷が高く、agent運用で状態が細かくなりすぎるため。

作業開始時の必須操作:

1. `blocked by` を確認する。未解決の阻害要因がある場合は作業を開始せず、Statusをblockedにする。
2. Issueをin-progressにする。
3. Assigneeを必ず設定する。
4. agent自律作業でも、開発環境の持ち主またはレビュー責任者の人間をAssigneeにする。
5. Agent Tier、Agent Harness、Agent ModelをProject fieldへ記録する。
6. linked branchを作る。

# Merge policy

採用するmain統合方式は、マージコミット + マージキュー + 自動マージ。

- マージコミットを使う。
- squashマージとrebaseマージは標準運用では使わない。
- Require linear historyは使わない。
- mainへ直接pushしない。
- PR単体CIとmerge_group CIを両方走らせる。
- 承認済みPRは自動マージを有効化してマージキューへ流す。
- マージキューのMaximum group sizeは100を許容する。ただしCIを1回にまとめる設定ではない。
