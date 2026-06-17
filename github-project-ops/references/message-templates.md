# Message templates

# Issue body

Project fieldにあるメタデータは本文へ書かない。Type、Scope、Status、Priority、Size、Complexity、Risk、Agent Tier、Agent Harness、Agent Model、Reviewer Owner、Branch、Source、Target Date、Started At、Merged AtはProject fieldだけに記録する。

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
```

# PR body

PR本文にProject fieldのメタデータや具体モデル名を書かない。Project fieldへ記録する。

```markdown
## 概要

- 変更点1
- 変更点2

## 関連Issue

Closes #123

## スコープ

実装したこと:

- ...

意図的に扱わないこと:

- ...

## 確認手順

- [ ] テストまたは確認1
- [ ] テストまたは確認2

## リスク

- 既知のリスク
- rollback方針

## レビュー観点

- 特に見てほしい点
```

# Work start comment

```markdown
作業開始。

担当者、agent情報、branchはProject fieldに記録済み。
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
