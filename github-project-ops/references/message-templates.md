# Message templates

# Issue body

```markdown
# 概要

このIssueで実現することを1〜3文で書く。

# 背景

なぜ必要かを書く。

# スコープ

- 実装対象1
- 実装対象2

# 非スコープ

- このIssueでは扱わないこと1
- このIssueでは扱わないこと2

# 受け入れ条件

- [ ] 条件1
- [ ] 条件2
- [ ] 条件3

# 確認手順

- [ ] testまたは手動確認1
- [ ] testまたは手動確認2

# 依存関係

Blocked by:

- #...

Blocking:

- #...

# 実装メモ

変更予定箇所、interface、注意点を書く。

# Agent指定

Agent Tier: agent:standard

作業開始時にProject fieldへ記録するもの:

- Agent Harness
- Agent Model
- Reviewer Owner
- Branch
```

# PR body

PR本文に具体モデル名を書かない。Project fieldへ記録する。

```markdown
## Summary

- 変更点1
- 変更点2

## Linked Issue

Closes #123

## Scope

実装したこと:

- ...

意図的に扱わないこと:

- ...

## Verification

- [ ] テストまたは確認1
- [ ] テストまたは確認2

## Risk

- 既知のリスク
- rollback方針

## Review Focus

- 特に見てほしい点
```

# Work start comment

```markdown
作業開始。

- Assignee: @owner
- Agent Tier: agent:standard
- Agent Harness: Codex
- Branch: 123/feat-ui-search-cards
```

# Blocked comment

```markdown
Blockedに変更。

理由:

- ...

解除条件:

- ...

依存:

- #...
```
