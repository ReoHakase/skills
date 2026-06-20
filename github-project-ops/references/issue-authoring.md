# Issue authoring

Issue作成、WBS分解、sub-issue、blocked by / blocking、Issue bodyを書くときに読む。

# 目次

- WBSと依存関係
- 運用中のIssue追加
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

語彙を混同しない。

- `blocking`: このIssueが後続Issueの前提である。未解決の前段がなければ、このIssue自体は `ready` にできる。
- `blocked by`: このIssueが前段Issueを待っているIssue間関係。未解決で作業開始を止めるなら、このIssueは `ready` ではなく `blocked` にする。

`ready` は「仕様確定済み」ではなく「今すぐ作業開始できる」という意味である。仕様、受け入れ条件、確認手順が確定していても、前段Issueの完了待ちなら `blocked` にする。

Issue dependencyとStatusは自動同期しない。`blocked by` / `blocking` はGitHub Issue同士の順序依存だけに使う。upstream PR、Figma design、権限、外部tracker、設計判断待ちのような外部blockerは、dummy Issueを作ってdependencyへ押し込まず、Statusを `blocked` にしてblocked commentへURL付きで書く。

Forecast Start / Forecast Endは、Project上の計画作業期間である。直列依存では期間を重ねない。

- AがBを `blocked by` で待つなら、AのForecast StartはBのForecast Endより後の日付にする。
- 同じepic配下でも、blocked by / blockingがない子Issue同士は並列化できるため、Forecastを重ねてよい。
- epicのForecastは子Issue群を包む期間にする。epicと子IssueのForecastが重なるのは正常である。

Forecast変更はProject fieldだけで行う。Issue本文にForecastやMilestone期限を書かない。

AI agentを使う前提では、並列実行可能なIssue数は無限に近いと仮定する。最適化目標は、総Issue数を減らすことではなく、完成までの直列Issue数を減らすこと。

分解手順:

1. epicを作る。
2. 共有contractを切る。
3. contract完了後に並列実装Issueを切る。
4. test/docs/observabilityを別Issueにできるなら分ける。
5. c3-complex/r3-dangerousはspikeを先に切る。
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

# 運用中のIssue追加

bootstrap後にIssueを追加する場合も、独自WBS番号は作らない。GitHub Issue number、sub-issue、blocked by / blocking、Project fieldsをSSoTにする。

追加前に親Issue、既存の子Issue、依存関係を読む。

```bash
gh issue view PARENT_NUMBER \
  --repo OWNER/REPO \
  --json number,title,milestone,subIssues,subIssuesSummary,blockedBy,blocking
```

新規Issueを既存epicの子として作る。

```bash
gh issue create \
  --repo OWNER/REPO \
  --parent PARENT_NUMBER \
  --milestone "First Release" \
  --title "自然な日本語のIssue title" \
  --body-file issue.md
```

既存Issueをsub-issueへ追加する。

```bash
gh issue edit PARENT_NUMBER --repo OWNER/REPO --add-sub-issue CHILD_NUMBER
```

依存関係を後から追加する。

```bash
gh issue edit BLOCKED_NUMBER --repo OWNER/REPO --add-blocked-by BLOCKER_NUMBER
```

依存を追加したらForecastを再確認する。`BLOCKED_NUMBER` のForecast Startは、すべての未完了blockerのForecast Endより後にする。`BLOCKER_NUMBER` は後続Issueをblockingしていても、未解決のblocked byがなければreadyにできる。

sub-issue追加はWBS階層の変更であり、実行順序の追加ではない。順序依存が必要なときだけblocked by / blockingを追加する。

# Issue粒度

branchable issueは、1 branchと1 PRを持てるIssueである。次をすべて満たす。

- 1 PRで閉じられる。
- 受け入れ条件が第三者に判定可能。
- titleが自然な日本語で、何が変わるか分かる。
- TypeとScopeはProject fieldに入っている。
- 主componentが1つ、またはinterface境界が1つ。
- 非スコープが明記されている。
- 必要なblocked by / blockingがGitHub上の関係として設定されている。
- テストまたは確認手順がある。
- Issue本文だけでagentが作業できる。

分割すべき兆候:

- 受け入れ条件が8個以上。
- 変更ファイルが12個を超える見込み。
- UI、DB、API、infra、docsを同時に広く変更する。
- 仕様未確定の判断が複数残っている。
- 複数agentが並列実行できる作業を1 Issueに押し込んでいる。
- レビュー観点が3つ以上ある。
- 失敗時の巻き戻しが複数段階になる。

epic本文には、到達したい成果、成果の境界、分割方針、完了判定を書く。sub-issue一覧はGitHub metadataで見る。

spikeは未確定要素を減らすための調査Issue。調査結果、採用案、棄却案、後続Issue案、実装しない判断の理由を書く。コード変更を含んでもよいが、本番機能を完成させるIssueではない。

bug Issueには必ず再現条件を書く。

- 期待動作
- 実際の動作
- 再現手順
- 環境
- ログ
- 影響範囲
- 修正の受け入れ条件

debug log、chat、inquiryからIssueを起こす場合は、最初はStatusをinboxにする。SourceはProject fieldに入れる。Issue本文にはSourceなどのProject field assignmentを書かない。

Issue本文に必ず書く:

- 原文または要約
- 影響しているユーザーまたは機能
- 再現性
- 緊急度の仮判定
- 次のtriageで確認すべきこと

inboxから直接in-progressにしない。必ずtriagedまたはreadyを通す。

# Issue body運用

Issue bodyは最新の信頼できる情報源として随時更新する。受け入れ条件、非スコープ、確認手順、再現条件、成果の境界が変わった場合は、古い情報を放置せずbodyを更新する。

状態遷移、判断理由、阻害要因、レビュー/CI判断、close/cancel理由はコメントへ残す。bodyは現在信頼してよい内容、コメントは時系列の判断記録として分ける。

Issue bodyに `実装メモ`、`メモ`、`注意点` のような何でも入る欄を作らない。変更予定箇所、調査中の考え、実装中の注意、未確定の案はコメントへ書く。確定した契約、受け入れ条件、非スコープ、確認手順だけをbodyへ反映する。

Milestone、sub-issue、blocked by / blocking、Project field、Assignee、linked branchはGitHub metadataをSSoTにする。Issue bodyにMilestone、sub-issue一覧、依存関係section、field assignmentを書かない。

Issue bodyやPR bodyで既存Issue/PRやcommitを参照するときは、同一repositoryなら `#123` や短いcommit SHAだけを書く。GitHubがautolinkとhover/previewで参照先を表示するため、`#123 タイトル` のようにtitleを併記しない。別repositoryのIssue/PRは `OWNER/REPO#123` と書く。参照: <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls>

古いが残さないと混乱する短い記述はstrikethroughで残す。

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

- Issue descriptionは編集でき、edit historyを参照できる。参照: <https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/editing-an-issue>
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
```

# 記入済み例

## Epic

```markdown
# 目的

検索結果から「なぜこの動画がヒットしたか」を、一覧画面だけで判断できるようにする。

# 成果の境界

対象:

- 検索結果カードに作品情報と一致シーンの根拠を表示する
- 一致シーンの時刻からプレイヤーへ移動できる
- 未取得データがあっても表示が破綻しない

対象外:

- ホバー動画プレビュー
- 検索ランキング
- キャプション生成処理

# 分割方針

- 検索レスポンスの契約を先に固定する
- UI、API、フィクスチャ確認は契約確定後に並列化する
- ランキング変更は別の親Issueで扱う

# 完了判定

- [ ] フィクスチャ検索で一致シーンの根拠表示まで確認できる
- [ ] 未取得データのフォールバック表示が確認できる
- [ ] 残作業が別Issueまたは中止として整理されている
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
gh issue create --repo OWNER/REPO --parent PARENT_NUMBER --title "子Issue" --body-file issue.md
```

既存Issueをsub-issueへ追加:

```bash
gh issue edit PARENT_NUMBER --repo OWNER/REPO --add-sub-issue CHILD_NUMBER
```

blocked by / blocking付きでIssue作成:

```bash
gh issue create \
  --repo OWNER/REPO \
  --blocked-by BLOCKER_NUMBER \
  --blocking BLOCKED_NUMBER \
  --title "Issue" \
  --body-file issue.md
```

既存Issueにdependencyを追加:

```bash
gh issue edit BLOCKED_NUMBER --repo OWNER/REPO --add-blocked-by BLOCKER_NUMBER

gh issue edit BLOCKER_NUMBER --repo OWNER/REPO --add-blocking BLOCKED_NUMBER
```

MCPはIssue本文の不足確認、Project viewの現状把握、並列化可能なIssueの抽出に使う。再現可能な操作はgh CLIへ落とす。
