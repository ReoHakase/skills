# Merge commit + merge queue + auto-merge policy

# 目的

mainを壊さずに、複数PRを自動で高速に流す。

PR単体のCIだけでなく、実際にmainへ入る直前の合成状態でもCIを通すことで、mainの安定性を保つ。

# 基本方針

採用する運用は、merge commit + merge queue + auto-merge。

## merge commit

PRの統合点をmain履歴に残す方式。squashやrebaseではなく、PRブランチをmerge commitで取り込む。

## merge queue

承認済みPRをすぐmainへ入れず、順番にキューへ入れて、最新mainと先行PR込みの状態でCIを通してからマージする仕組み。

## auto-merge

条件を満たしたPRを人間が手動でマージせず、自動的にmerge queueへ流す運用。

# main保護

- mainには直接pushしない。
- PR経由にする。
- required checksを必須にする。
- reviewを必須にする。
- conversation解決を必須にする。
- merge queueを必須にする。
- Require linear historyは使わない。

merge commit運用ではlinear historyと衝突するため、Require linear historyを有効にしない。

# CI

全checkを次の両方で実行する。

```yaml
on:
  pull_request:
  merge_group:
    types: [checks_requested]
```

- `pull_request`: PR単体の早期フィードバック。
- `merge_group`: merge queue上で実際にmainへ入る候補状態の最終確認。

PR単体ではCIが通っていても、先行PRと組み合わせると壊れることがあるため、merge_groupでも同じcheckを走らせる。

# Maximum group size = 100

`Maximum group size = 100`は採用してよい。

これはPR単位の厳密な切り分けより、queue throughputを優先する設定。

ただし、Maximum group sizeはCIを1回にまとめる設定ではない。required checksを通過した後に、base branchへ一度にmergeできるPR数の上限を決める設定。

したがって、100にしても特定のPR群のCIが必ず1回に圧縮されるわけではない。

# 特定PR群を1つのmerge groupへ固定しない

GitHub nativeのmerge queueだけでは、特定のPR群を明示的に1つのmerge groupへ固定し、CIも1回だけにすることはできない。

epic branchは使わない。

通常運用:

- 各PRをmain向けに出す。
- merge queueに任せる。
- CIはPRごと、merge_groupごとに走る。

CI 1回を厳密に優先したい場合:

- 最初から1つの大きめPRにまとめる。

並列分割された複数PRを維持したまま、merge queue上でCIだけ1回にする運用はGitHub標準機能ではできない。

# 概念整理

| 段階                   | 目的                                       |
| ---------------------- | ------------------------------------------ |
| PR CI                  | そのPR単体が壊れていないか早めに確認する   |
| merge queue            | mainへ入れる順序を管理する                 |
| merge_group CI         | 最新mainと先行PR込みでも壊れないか確認する |
| Maximum group size 100 | CI削減ではなく、merge throughputを上げる   |
| merge commit           | main履歴にPRの統合点を残す                 |

# gh CLI

auto-mergeを有効化し、merge queueへ流す。

```bash
gh pr merge <pr-number> --auto --merge
```

repository設定は次を標準にする。

```text
allow_merge_commit = true
allow_squash_merge = false
allow_rebase_merge = false
allow_auto_merge = true
```

branch protectionまたはrulesetでRequire merge queueを有効化する。GitHub UIまたはruleset APIで設定する。
