# Issue authoring

Issue作成、WBS分解、sub-issue、blocked by / blocking、Issue bodyを書くときに読む。

# 目次

- WBSと依存関係
- Issue粒度
- Issue body運用
- Issue body template
- 記入済み例
- gh CLI / MCP操作

# WBSと依存関係

`SJ-1.2.3` のような独自WBS番号は使わない。

理由:

- 動的な分割・統合で番号が壊れる。
- GitHub Issue numberと二重管理になる。
- sub-issueで親子関係を表せる。
- blocked by / blockingで順序依存を表せる。
- Project viewでgrouping、filtering、sortができる。

bootstrap用JSONにも独自keyを置かない。タイトルを一時的な照合キーとして使うため、初期作成ファイル内ではtitleを一意にする。

sub-issue:

- WBS階層を表す。
- あるepicや親featureを構成する子Issueを示す。
- 実行順序は表さない。

blocked by / blocking:

- 実行順序を表す。
- あるIssueが別Issue完了まで開始できないことを示す。
- critical pathを短くするために最小限にする。

AI agentを使う前提では、並列実行可能なIssue数は無限に近いと仮定する。最適化目標は、総Issue数を減らすことではなく、完成までの直列Issue数を減らすこと。

分解手順:

1. epicを作る。
2. 共有contractを切る。
3. contract完了後に並列実装Issueを切る。
4. test/docs/observabilityを別Issueにできるなら分ける。
5. C3-complex/R3-dangerousはspikeを先に切る。
6. branch同士の競合が予想される場合は、先にinterface PRを作る。

悪い分解:

```text
Epic: 検索機能を全部作る
  - 検索UI、API、DB、ranking、test、docsを1Issueで実装する
```

良い分解:

```text
Epic: 検索機能
  - 検索レスポンスのcontractを定義する
  - DB検索repositoryを追加する
  - 検索結果カードを表示する
  - 検索rankingのunit testを追加する
  - 検索UIの操作説明を追加する
```

依存:

```text
検索結果カードを表示する blocked by 検索レスポンスのcontractを定義する
DB検索repositoryを追加する blocked by 検索レスポンスのcontractを定義する
```

contract後はUI、DB、test、docsを並列化できる。

# Issue粒度

branchable issueは、1 branchと1 PRを持てるIssueである。次をすべて満たす。

- 1 PRで閉じられる。
- 受け入れ条件が第三者に判定可能。
- titleが自然な日本語で、何が変わるか分かる。
- TypeとScopeはProject fieldに入っている。
- 主componentが1つ、またはinterface境界が1つ。
- 非スコープが明記されている。
- blocked by / blockingが明記されている。
- テストまたは確認手順がある。
- Issue本文だけでagentが作業できる。

分割すべき兆候:

- 受け入れ条件が8個以上。
- 変更ファイルが12個を超える見込み。
- UI、DB、API、infra、docsを同時に広く変更する。
- 仕様未確定の判断が複数残っている。
- 複数agentが並列実行できる作業を1 Issueに押し込んでいる。
- review focusが3つ以上ある。
- 失敗時のrollbackが複数段階になる。

epicは親Issue。実装branchを持たない。目的、成功条件、sub-issue一覧、主要依存関係、完了条件を書く。

spikeは未確定要素を減らすための調査Issue。調査結果、採用案、棄却案、後続Issue案、実装しない判断の理由を書く。コード変更を含んでもよいが、本番機能を完成させるIssueではない。

bug Issueには必ず再現条件を書く。

- 期待動作
- 実際の動作
- 再現手順
- 環境
- ログ
- 影響範囲
- 修正の受け入れ条件

debug log、chat、inquiryからIssueを起こす場合は、最初はStatusをInboxにする。SourceはProject fieldに入れる。Issue本文にはSourceなどのProject field assignmentを書かない。

Issue本文に必ず書く:

- 原文または要約
- 影響しているユーザーまたは機能
- 再現性
- 緊急度の仮判定
- 次のtriageで確認すべきこと

Inboxから直接In Progressにしない。必ずTriagedまたはReadyを通す。

# Issue body運用

Issue bodyは最新状態の要約として随時更新する。受け入れ条件、非スコープ、確認手順、実装メモ、依存関係が変わった場合は、古い情報を放置せずbodyを更新する。

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
- strikethroughとcollapsed sectionはGitHub Markdownで使える。参照: <https://docs.github.com/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax>, <https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/quickstart-for-writing-on-github>

Project fieldにあるメタデータは本文へ書かない。Type、Scope、Status、Priority、Size、Complexity、Risk、Agent Tier、Agent Harness、Agent Model、Reviewer Owner、Branch、Source、Forecast Start、Forecast End、Actual Start、Actual EndはProject fieldだけに記録する。

# Issue body template

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

# 記入済み例

## Epic

```markdown
# 概要

このIssueは関連する複数Issueを束ねる親Issueである。実装branchは持たない。

# 成功条件

- [ ] 主要sub-issueが作成されている
- [ ] 実行順序が必要なものはblocked by / blockingで表現されている
- [ ] 完了条件が明確である

# sub-issues

- #...

# 完了条件

- [ ] 子Issueが完了している
- [ ] 残Issueが別epicへ移動済み、またはCanceledになっている
```

## Feature

```markdown
# 概要

検索結果カードに、一致シーンの情報を日本語で表示できるようにする。

# 背景

検索結果一覧で動画全体の情報だけでは、なぜヒットしたか判断しづらい。一致した部分の説明とセリフをカード上で確認できるようにする。

# スコープ

- 品番、長さ、容量、解像度、商品名を表示する
- 一致シーンの時刻、シーン説明、タグ、セリフ抜粋を表示する
- カードクリックでプレイヤーへ遷移するためのvideo_idとscene_idを保持する

# 非スコープ

- ホバー動画プレビューの実装
- 独自HTMLタイムラインの実装
- 検索rankingの変更

# 受け入れ条件

- [ ] 検索結果カードに品番、長さ、容量、解像度、商品名が表示される
- [ ] 一致シーンの時刻、説明、タグ、セリフ抜粋が表示される
- [ ] データがない項目は空白ではなく未取得と表示される

# 確認手順

- [ ] fixtureデータでカードが表示される
- [ ] 長い商品名でもレイアウトが崩れない

# 依存関係

Blocked by:

- #...

Blocking:

- #...
```

## Bug

```markdown
# 概要

分割動画の連結時刻からpart内のローカル時刻を逆引きする処理が、part境界で1秒ずれる。

# 期待動作

work_time_msがpart境界上にある場合、次partのlocal_time_ms=0として解決される。

# 実際の動作

part境界上の時刻が前partの末尾として扱われることがある。

# 再現手順

1. 2part構成のfixtureを使う
2. part1のdurationと同じwork_time_msを指定する
3. work_time_to_video_timeを実行する

# 環境

- fixture: 2part構成
- 対象処理: work_time_to_video_time

# ログ

関連logまたは失敗test outputを貼る。secretや個人情報は含めない。

# 影響範囲

part境界に一致する検索結果で、プレイヤー遷移先が1秒ずれる可能性がある。

# 修正の受け入れ条件

- [ ] 境界時刻が次partのlocal_time_ms=0になる
- [ ] 境界直前は前partの末尾になる
- [ ] unit testが追加される

# 確認手順

- [ ] 該当unit testが通る
```

# gh CLI / MCP操作

Project操作にはproject scopeが必要。

```bash
gh auth refresh -s project
```

Issue作成:

```bash
gh issue create \
  --repo OWNER/REPO \
  --title "検索結果カードで一致シーンの無音プレビューを表示する" \
  --body-file issue.md
```

新規sub-issue作成:

```bash
gh issue create --repo OWNER/REPO --parent 100 --title "子Issue" --body-file issue.md
```

既存Issueをsub-issueへ追加:

```bash
gh issue edit 100 --repo OWNER/REPO --add-sub-issue 123
```

blocked by / blocking付きでIssue作成:

```bash
gh issue create --repo OWNER/REPO --blocked-by 120 --blocking 140 --title "Issue" --body-file issue.md
```

既存Issueにdependencyを追加:

```bash
gh issue edit 123 --repo OWNER/REPO --add-blocked-by 120

gh issue edit 120 --repo OWNER/REPO --add-blocking 123
```

MCPはIssue本文の不足確認、Project viewの現状把握、並列化可能なIssueの抽出に使う。再現可能な操作はgh CLIへ落とす。
