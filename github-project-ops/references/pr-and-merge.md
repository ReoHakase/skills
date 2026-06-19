# PR and merge

PR本文、in-review判断、merge commit、merge queue、auto-mergeを扱うときに読む。

# 目次

- PR body運用
- PR body template
- PR body example
- in-review comment方針
- Merge policy
- gh CLI / MCP操作

# PR body運用

PR本文にはProject fieldのメタデータや具体的なagentモデル名を書かない。Agent HarnessとAgent ModelはProject fieldへ記録する。

PR本文に必須の要素:

- 概要
- 関連Issue
- スコープ
- 確認手順
- リスク
- レビュー観点
- `Closes #<issue-number>` または同等のclosing keyword

必須sectionが存在していても、`-`、`- [ ]`、`done`、`確認済み` のようなplaceholderだけなら不十分。PR作成前に、第三者が確認できる具体的な変更点、確認手順、リスク、レビュー観点が書かれているか確認する。

PR bodyは最新状態の要約として随時更新する。確認手順、リスク、レビュー観点が変わった場合は、古い情報を放置せずbodyを更新する。

PR descriptionは既存PRではopening commentとして編集する。参照: <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/helping-others-review-your-changes>

Issue/PRやcommitの参照は、同一repositoryなら `#123` や短いcommit SHAだけを書く。GitHubがautolinkとhover/previewで参照先を表示するため、titleを併記しない。別repositoryのIssue/PRは `OWNER/REPO#123` と書く。参照: <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls>

古いが消すと混乱する短い記述はstrikethroughで残す。長い経緯はcollapsed sectionへ移す。secret、credential、個人情報、公開してはいけないlogはstrikethroughやdetailsで残さない。

# PR body template

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
- 巻き戻し方針

## レビュー観点

- 特に見てほしい点
```

# PR body example

```markdown
## Summary

- 検索結果カードに品番、長さ、容量、解像度、商品名を表示しました
- 一致シーンの時刻、説明、タグ、セリフ抜粋を表示しました
- 未取得項目のfallback表示を追加しました

## Linked Issue

Closes #123

## Scope

実装したこと:

- 検索結果カードの表示項目追加
- fixtureデータでの表示確認

意図的に扱わないこと:

- ホバー動画プレビュー
- 検索ranking変更

## Verification

- [ ] fixtureで検索結果カードを表示確認
- [ ] 長い商品名でも崩れないことを確認

## Risk

- UI表示だけの変更で、DB schemaと検索rankingには影響しない

## Review Focus

- 情報量が多すぎてカードが読みにくくなっていないか
- 未取得項目の表示が分かりやすいか
```

# in-review comment方針

通常はcommentを書かない。PR bodyに概要、関連Issue、スコープ、確認手順、リスク、レビュー観点を書き、`Closes #...` / `Fixes #...` / `Resolves #...` による自動追跡に任せる。

PR bodyやGitHub metadataで分かる内容をcommentへ重複させない。reviewerへの一時的な補足、CIの特殊事情、外部判断待ち、通常と違う確認依頼がある場合だけ、`issue-lifecycle.md` のin-review commentを使う。

# Merge policy

mainを壊さずに、複数PRを自動で高速に流す。PR単体のCIだけでなく、実際にmainへ入る直前の合成状態でもCIを通すことで、mainの安定性を保つ。

採用する運用は、merge commit + merge queue + auto-merge。

merge commit:

- PRの統合点をmain履歴に残す方式。
- squashやrebaseではなく、PRブランチをmerge commitで取り込む。

merge queue:

- 承認済みPRをすぐmainへ入れず、順番にキューへ入れる。
- 最新mainと先行PR込みの状態でCIを通してからマージする。

auto-merge:

- 条件を満たしたPRを人間が手動でマージせず、自動的にmerge queueへ流す。

main保護:

- mainには直接pushしない。
- PR経由にする。
- required checksを必須にする。
- reviewを必須にする。
- conversation解決を必須にする。
- merge queueを必須にする。
- Require linear historyは使わない。

merge commit運用ではlinear historyと衝突するため、Require linear historyを有効にしない。

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

`Maximum group size = 100`は採用してよい。これはPR単位の厳密な切り分けより、queue throughputを優先する設定。ただし、CIを1回にまとめる設定ではない。required checksを通過した後に、base branchへ一度にmergeできるPR数の上限を決める設定である。

GitHub nativeのmerge queueだけでは、特定のPR群を明示的に1つのmerge groupへ固定し、CIも1回だけにすることはできない。epic branchは使わない。

通常運用:

- 各PRをmain向けに出す。
- merge queueに任せる。
- CIはPRごと、merge_groupごとに走る。

CI 1回を厳密に優先したい場合は、最初から1つの大きめPRにまとめる。

概念整理:

| 段階                   | 目的                                       |
| ---------------------- | ------------------------------------------ |
| PR CI                  | そのPR単体が壊れていないか早めに確認する   |
| merge queue            | mainへ入れる順序を管理する                 |
| merge_group CI         | 最新mainと先行PR込みでも壊れないか確認する |
| Maximum group size 100 | CI削減ではなく、merge throughputを上げる   |
| merge commit           | main履歴にPRの統合点を残す                 |

repository設定は次を標準にする。

```text
allow_merge_commit = true
allow_squash_merge = false
allow_rebase_merge = false
allow_auto_merge = true
```

branch protectionまたはrulesetでRequire merge queueを有効化する。GitHub UIまたはruleset APIで設定する。

# gh CLI / MCP操作

linked branch作成:

```bash
gh issue develop 123 \
  --repo OWNER/REPO \
  --name "123/feat-ui-search-cards" \
  --base main \
  --checkout
```

完成済みのPR本文を先に作り、具体的な概要、スコープ、確認手順、リスク、レビュー観点、closing keywordがあることを確認してからPRを作成する。

```bash
gh pr create \
  --repo OWNER/REPO \
  --base main \
  --head "123/feat-ui-search-cards" \
  --title "検索結果カードで一致シーンの無音プレビューを表示する" \
  --body-file pr.md
```

PR本文には必ず次のいずれかを含める。

```text
Closes #123
Fixes #123
Resolves #123
```

merge queue運用では、条件を満たしたPRにauto-mergeを有効化する。

```bash
gh pr merge 123 --repo OWNER/REPO --auto --merge
```

MCPはPR review結果の要約、CI失敗原因の整理、Project viewの現状把握に使う。再現可能な操作はgh CLIへ落とす。
