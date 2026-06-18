# Message templates

このfileをIssue/PR bodyとlifecycle comment templateのSSoTにする。

`examples/issue-*.md` と `examples/pr.md` は記入済み具体例であり、generic templateではない。repositoryへコピーする設定例は `examples/.github/` に置く。

# Body update policy

Issue/PR bodyは最新状態の要約として随時更新する。受け入れ条件、非スコープ、確認手順、実装メモ、リスク、レビュー観点が変わった場合は、古い情報を放置せずbodyを更新する。

状態遷移、判断理由、blocker、review/CI判断、close/cancel理由はcommentへ残す。bodyは現在読むべき内容、commentは時系列の判断記録として分ける。

古いが消すと混乱する短い記述はstrikethroughで残す。

```markdown
~~旧APIだけを対象にする。~~
新旧APIの両方を対象にする。
```

長い経緯はcollapsed sectionへ移す。

```markdown
<details>
<summary>古い経緯</summary>

以前は旧APIだけを対象にしていたが、移行期間中に新旧APIの両方を扱う方針へ変更した。

</details>
```

secret、credential、個人情報、公開してはいけないlogはstrikethroughやdetailsで残さない。必要ならGitHubの履歴redaction手順に従う。

GitHub上の確認事項:

- Issue descriptionは編集でき、edit historyは削除されない限り参照できる。参照: <https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/editing-an-issue>
- commentのedit historyはread権限があれば確認できる。参照: <https://docs.github.com/en/communities/moderating-comments-and-conversations/tracking-changes-in-a-comment>
- commentの過去revisionはrendered prose diffとして表示される。参照: <https://github.blog/changelog/2018-05-23-comment-edit-history/>
- PR descriptionは既存PRではopening commentとして編集する。参照: <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/helping-others-review-your-changes>
- strikethroughとcollapsed sectionはGitHub Markdownで使える。参照: <https://docs.github.com/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax>, <https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/quickstart-for-writing-on-github>

# Issue body

Project fieldにあるメタデータは本文へ書かない。Type、Scope、Status、Priority、Size、Complexity、Risk、Agent Tier、Agent Harness、Agent Model、Reviewer Owner、Branch、Source、Forecast Start、Forecast End、Actual Start、Actual EndはProject fieldだけに記録する。

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

# Lifecycle comments

Project field metadata、具体モデル名、branch名はcomment本文へ書かない。必要なら「Project fieldに記録済み」とだけ書く。

`examples/lifecycle-comments.md` と同じく、冒頭の絵文字付き一文で状態を示し、その後に必要なキーだけを書く。

## Inbox comment

```markdown
📥 流入内容を整理した。

流入元: ... (URL)
要約: ...
影響: ...
次に確認すること: ...
```

## Triaged comment

```markdown
🔎 トリアージした。

判断根拠:

- ...

未確定事項: なし / ...
Readyへ進めない理由: なし / ...
```

Readyへ進められる場合は、Ready commentを使う。未確定事項がない場合は `なし` と書く。

## Ready comment

明白な場合は省略してよい。判断が揺れやすいIssue、重要Issue、blocker解消直後のIssueでは残す。

```markdown
🟢 Ready状態になった。

確認済み:

- 受け入れ条件が判定可能
- 非スコープが明確
- 確認手順がある
- 作業開始を止めるblockerがない

補足: なし / ...
```

## In Progress comment

```markdown
🚧 作業中の補足。

担当者、agent情報、branch、実作業開始日はProject fieldに記録済み。

作業前確認:

- blockerを再確認済み
- linked branchを確認済み

メモ: なし / ...
```

## In Review comment

通常は書かない。PR bodyに概要、関連Issue、スコープ、確認手順、リスク、レビュー観点を書き、`Closes #...` / `Fixes #...` / `Resolves #...` による自動追跡に任せる。

PR bodyやGitHub metadataで分かる内容をcommentへ重複させない。reviewerへの一時的な補足、CIの特殊事情、外部判断待ち、通常と違う確認依頼がある場合だけ書く。

```markdown
👀 特筆事項があるため、In Review commentを残す。

PR本文やGitHub metadataでは分からないこと: ...
一時的な注意点: ...
次に見るもの: PR checks / review thread / 外部URL
```

## Blocked comment

`解除できる人` はproject/repository内のGitHub collaboratorならGitHub mentionを書く。upstream maintainerなどproject/repository外のGitHub accountはmentionせず、GitHub profile URLまたは該当Issue/PR URLで書く。GitHub accountがない場合はSlack/TeamsのプロフィールURL、または氏名を書く。

外部依存は必ずURL付きで書く。Issue/PR、CI run、log、Figma frame、Slack/Teams thread、外部trackerなど、後から同じ対象を開ける参照にする。

```markdown
⛔ ブロックに変更した。

理由: ...
解除できる人: @repo-collaborator / GitHub profile URL / Slack profile URL / Teams profile URL / 氏名
依存: #... / 外部依存URL
次の確認タイミング: ...
```

## Unblocked / resume comment

```markdown
🔓 ブロックが解消した。

解消内容: ...
戻す状態: ...
再確認したこと: ...
```

## Done comment

```markdown
✅ 完了確認。

確認済み:

- PRがmainへmerge済み
- linked Issueがclose済み
- required checksが通過済み
- 実終了日はProject fieldに記録済み

残follow-up: なし / #...
```

## Canceled comment

```markdown
🛑 Canceledにします。

理由: duplicated / obsolete / out of scope / invalid / replaced
根拠: ...
代替または関連Issue: なし / #...
```
