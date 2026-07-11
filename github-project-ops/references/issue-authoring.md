# Issue authoring

Issue作成、WBS分解、sub-issue、blocked by / blocking、Issue本文を書くときに読む。

# 目次

- WBSと依存関係
- 運用中のIssue追加
- Issue粒度
- Issue本文運用
- Issue本文テンプレート
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

bootstrap用JSONにも独自WBS keyを置かない。初期作成ファイル内ではtitleを一意にする。既存Issueの再利用はtitle照合ではなく、確認済みIssue numberを明示する。

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

実行対象の末端Issueをnode、`blocker -> 後続` をedgeとする依存関係DAGを作る。apply前と依存変更後に次を検証する。

- 自己参照、同じedgeの重複、循環がない。
- sub-issue階層にも自己parent、重複parent、循環がない。
- blocker完了はIssueがclosedかだけで判断せず、Project Statusが `done` で型別done条件を満たすことを確認する。
- 中止した前段Issueを完了扱いしない。辺の置換、依存不要化、下流中止のいずれかを決めるまで推移的な後続Issueを再トリアージする。
- 依存関係の追加・削除・置換後は、影響する後続Issue全体のready可否、クリティカルパス、Forecast、Milestone実現可能性を再計算する。

Issue本文の `変更ファイル` から、同じファイルまたはglobを同時に触るIssue同士の変更競合グラフも作る。変更競合は別の実行Waveへ送る根拠だが、論理的な完了順序がなければ `blocked by` にしない。作業権を取得した各Issueには独立したworktreeを割り当て、同じブランチやworktreeを複数エージェントで共有しない。

Forecast Start / Forecast Endは、Project上の計画作業期間である。直列依存では期間を重ねない。

- AがBを `blocked by` で待つなら、AのForecast StartはBのForecast Endより後の日付にする。
- 同じepic配下でも、依存関係、変更競合、実装/レビュー/CI/マージ容量が許す子IssueだけForecastを重ねてよい。
- epicのForecastは子Issue群を包む期間にする。epicと子IssueのForecastが重なるのは正常である。

Forecast変更はProject fieldだけで行う。Issue本文にForecastやMilestone期限を書かない。

並列実行可能数はエージェント、worktree、レビュアー、重いCI、共有フィクスチャ、マージ待ちの各WIP上限で有限である。最適化目標は直列依存を減らしつつ、後段を詰まらせない範囲で `ready` Issueを投入することにする。

分解手順:

1. epicを作る。
2. 共有インターフェースの契約を切る。
3. 契約完了後に並列実装Issueを切る。
4. テスト、ドキュメント、可観測性は実装末端Issueの完了条件へ残す。単独でマージでき、親の受け入れ条件を弱めず、別のレビュー境界に価値がある場合だけ分ける。
5. c3-complex/r3-dangerousはspikeを先に切る。
6. ブランチ同士の競合が予想される場合は、先にインターフェースを定めるPRを作る。

悪い分解:

```text
Epic: 検索機能を全部作る
  - 検索UI、API、DB、検索順位、テスト、ドキュメントを1Issueで実装する
```

良い分解:

```text
Epic: 検索機能
  - 検索レスポンスのcontractを定義する
  - DB検索repositoryとunit testを追加する
  - 検索結果カード、UIテスト、操作説明を追加する
```

依存:

```text
検索結果カードを表示する blocked by 検索レスポンスのcontractを定義する
DB検索repositoryを追加する blocked by 検索レスポンスのcontractを定義する
```

contract後は変更競合とWIP上限を確認し、DBの末端IssueとUIの末端Issueを別の実行Waveまたは同じ実行Waveへ配置する。

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
  --title "自然な日本語のIssueタイトル" \
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

ブランチ作成型Issue（branchable Issue）は、1 branchと1 PRを持てるIssueである。次をすべて満たす。

- 1 PRで閉じられる。
- 受け入れ条件が第三者に判定可能。
- titleが自然な日本語で、何が変わるか分かる。
- TypeとScopeはProject fieldに入っている。
- 正のEffortとEstimate ConfidenceがProject fieldに入っている。
- 主componentが1つ、またはinterface境界が1つ。
- 非スコープが明記されている。
- 必要なblocked by / blockingがGitHub上の関係として設定されている。
- テストまたは確認手順がある。
- Issue本文だけでagentが作業できる。

実行対象の末端Issueには、ブランチ作成型のほかにspikeとリポジトリ差分なしの作業がある。いずれも受け入れ条件、非スコープ、確認手順、正のEffort、Estimate Confidence、未解決blockerなしを確認してから `ready` にする。リポジトリ差分なしの作業とPRなしspikeもAgent Runで作業権を取得して `in-progress` へ進めるが、branchとworktreeは作らない。

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

デバッグログ、チャット、問い合わせからIssueを起こす場合は、最初はStatusを `inbox` にする。SourceはProject fieldに入れる。Issue本文にはSourceなどのProject field値を書かない。

Issue本文に必ず書く:

- 原文または要約
- 影響している利用者または機能
- 再現性
- 緊急度の仮判定
- 次のトリアージで確認すべきこと

inboxから直接in-progressにしない。必ずtriagedまたはreadyを通す。

# Issue本文運用

Issue本文は最新の信頼できる情報源として随時更新する。受け入れ条件、非スコープ、確認手順、再現条件、成果の境界が変わった場合は、古い情報を放置せず本文を更新する。

Issue本文は常体で書く。論文やレポートと同じく「である」「する」「できる」を使い、丁寧体は使わない。

状態遷移、判断理由、阻害要因、レビュー/CI判断、クローズ/中止理由はコメントへ残す。本文は現在信頼してよい内容、コメントは時系列の判断記録として分ける。

Issue本文に `実装メモ`、`メモ`、`注意点` のような何でも入る欄を作らない。変更予定箇所、調査中の考え、実装中の注意、未確定の案はコメントへ書く。確定した契約、受け入れ条件、非スコープ、確認手順だけを本文へ反映する。

Milestone、sub-issue、blocked by / blocking、Project field、Assignee、紐づくブランチはGitHubメタデータをSSoTにする。Issue本文にMilestone、sub-issue一覧、依存関係の節、Project field値を書かない。

Issue本文やPR本文で既存Issue、PR、コミットを参照するときは、同一リポジトリなら `#123` や短いコミットSHAだけを書く。GitHubが自動リンクとプレビューで参照先を表示するため、`#123 タイトル` のようにタイトルを併記しない。別リポジトリのIssue/PRは `OWNER/REPO#123` と書く。参照: <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls>

Issueの種類ごとに必要な章を固定する。章があっても、プレースホルダーや本文のないチェック項目だけでは不十分である。

| 種類                         | 必須の章                                                                                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 機能追加・通常作業           | 概要または背景、非スコープ、変更ファイル、参照ドキュメント、受け入れ条件、確認手順                                        |
| 不具合（Type `fix`）         | 通常作業の必須章に加え、期待動作、実際の動作、再現手順、ログ・証拠。環境と影響範囲も再現・判断に必要なら含める            |
| 調査（Type `spike`）         | 通常作業の必須章に加え、調査する問い、時間枠、停止条件、判断基準、成果物と証拠、後続Issue。調査手順も再現に必要なら含める |
| 大項目（Type `epic`）        | 目的、成果の境界、完了条件、状態集約の根拠。必要に応じて分割方針も含める                                                  |
| リポジトリ差分なしの通常作業 | 通常作業と同じ。変更ファイルには `なし（リポジトリ差分なし）` と理由を書く                                                |

`変更ファイル` は、並列実行時に人間とエージェントが競合リスクを事前に予測するための章である。変更予定をglobパターンだけで書く。調査Issueでリポジトリを変更しない場合は「なし（リポジトリ差分なし）」と書く。

`参照ドキュメント` は、Issue作成時点で参照した仕様、設計、README、`docs/`を、コミット固定URLと行番号付きで残す章である。参照コミットは必ずSHAで残す。基幹ブランチから起票する場合も、本文にはブランチ名ではなく `git rev-parse origin/<default-branch>` で得たSHAを書く。参照先が見つからない場合は起票を止め、正本または根拠文書を特定する。

調査Issueの `判断基準` は、起票時に候補と選定条件を書き、完了時に採用案、棄却案、理由、残った不確実性へ更新する。`後続Issue` は、完了時に「不要」と理由、または作成したIssue番号へ更新する。

不具合Issueのログは、再現に必要な最小限に絞る。秘密情報、認証情報、個人情報は記載せず、編集履歴にも残さない。

PR作成時に実際の変更範囲が `変更ファイル` から大きく外れた場合は、PR本文の `Issueとの差異` に理由を書く。現在の契約そのものが変わった場合は、PRをレビュー可能にする前にIssue本文を更新する。

古いが残さないと混乱する短い記述は取り消し線で残す。

```markdown
~~旧APIだけを対象にする。~~
新旧APIの両方を対象にする。
```

長い経緯は折りたたみ欄へ移す。

```markdown
<details>
<summary>古い経緯</summary>

以前は旧APIだけを対象にしていたが、移行期間中に新旧APIの両方を扱う方針へ変更した。

</details>
```

秘密情報、認証情報、個人情報、公開してはいけないログは取り消し線や折りたたみ欄で残さない。必要ならGitHubの履歴から削除する手順に従う。

GitHub上の確認事項:

- Issue本文は編集でき、編集履歴を参照できる。参照: <https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/editing-an-issue>
- コメントの編集履歴は読み取り権限があれば確認できる。参照: <https://docs.github.com/en/communities/moderating-comments-and-conversations/tracking-changes-in-a-comment>
- コメントの過去版は文章の差分として表示される。参照: <https://github.blog/changelog/2018-05-23-comment-edit-history/>
- 取り消し線と折りたたみ欄はGitHub Markdownで使える。参照: <https://docs.github.com/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax>, <https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/quickstart-for-writing-on-github>

Project fieldにあるメタデータは本文へ書かない。Type、Scope、Status、Priority、Size、Effort、Estimate Confidence、Complexity、Risk、Agent Tier、Agent Harness、Agent Model、Agent Run、Reviewer Owner、Branch、Source、Forecast Start、Forecast End、Actual Start、Actual EndはProject fieldだけに記録する。

# 参照ドキュメントURL

固定URLはGitHubの `blob/<commit_sha>/<path>#Lx-Ly` を使う。

```text
https://github.com/OWNER/REPO/blob/<commit_sha>/SPEC.md#L120-L180
```

更新確認はrepository全体のcompare URLを標準にする。

```text
https://github.com/OWNER/REPO/compare/<commit_sha>...main
```

特定ファイルだけを確認したい場合は、GitHub URLではなくローカル確認コマンドを補助として書く。

```bash
git diff <commit_sha>..main -- SPEC.md
```

GitHub UI上のdiff file anchorは使ってもよいが、生成が安定した仕様として扱いにくいため、skillの必須形式にはしない。

参照:

- <https://docs.github.com/en/pull-requests/committing-changes-to-your-project/viewing-and-comparing-commits/comparing-commits>
- <https://docs.github.com/articles/about-comparing-branches-in-pull-requests>
- <https://git-scm.com/docs/git-diff>

# Issue本文テンプレート

```markdown
# 概要

このIssueで実現することを1〜3文で書く。

# 背景

なぜ必要かを書く。

# 非スコープ

- このIssueでは扱わないこと1
- このIssueでは扱わないこと2

# 変更ファイル

- `src/{session,state,cli}.rs`
- `tests/{conflict_repair,multi_window}.rs`
- `docs/RELEASE_READINESS.md`

# 参照ドキュメント

https://github.com/OWNER/REPO/blob/<commit_sha>/SPEC.md#L120-L180
https://github.com/OWNER/REPO/blob/<commit_sha>/docs/ARCHITECTURE.md#L40-L95

更新確認: https://github.com/OWNER/REPO/compare/<commit_sha>...main

# 受け入れ条件

- [ ] 条件1
- [ ] 条件2
- [ ] 条件3

# 確認手順

- [ ] テストまたは手動確認1
- [ ] テストまたは手動確認2
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

# 完了条件

- [ ] フィクスチャ検索で一致シーンの根拠表示まで確認できる
- [ ] 未取得データのフォールバック表示が確認できる
- [ ] 残作業が別Issueまたは中止として整理されている

# 状態集約の根拠

必須の末端Issueを正とし、`issue-lifecycle.md` の優先順位でStatusを集約する。
```

## Feature

```markdown
# 概要

検索結果カードに、一致シーンの情報を日本語で表示できるようにする。

# 背景

検索結果一覧で動画全体の情報だけでは、なぜヒットしたか判断しづらい。一致した部分の説明とセリフをカード上で確認できるようにする。

# 非スコープ

- ホバー動画プレビューの実装
- 独自HTMLタイムラインの実装
- 検索順位の変更

# 変更ファイル

- `web/components/search-result.*`
- `web/components/search-result.test.*`

# 参照ドキュメント

https://github.com/OWNER/REPO/blob/0123456789abcdef0123456789abcdef01234567/docs/spec.md#L120-L180

# 受け入れ条件

- [ ] 検索結果カードに品番、長さ、容量、解像度、商品名が表示される
- [ ] 一致シーンの時刻、説明、タグ、セリフ抜粋が表示される
- [ ] データがない項目は空白ではなく未取得と表示される
- [ ] カードクリックに必要な `video_id` と `scene_id` を保持する

# 確認手順

- [ ] フィクスチャデータでカードが表示される
- [ ] 長い商品名でもレイアウトが崩れない
```

## Bug

```markdown
# 概要

分割動画の連結時刻からパート内のローカル時刻を逆引きする処理が、パート境界で1秒ずれる。

# 背景

検索結果からプレイヤーへ移動したとき、境界上の一致場面とは異なる位置が開かれる。

# 非スコープ

- 境界以外の時刻変換方式
- プレイヤー画面の表示

# 期待動作

`work_time_ms` がパート境界上にある場合、次のパートの `local_time_ms=0` として解決される。

# 実際の動作

パート境界上の時刻が前のパートの末尾として扱われることがある。

# 再現手順

1. 2パート構成のフィクスチャを使う
2. パート1の長さと同じ `work_time_ms` を指定する
3. `work_time_to_video_time` を実行する

# 環境

- フィクスチャ: 2パート構成
- 対象処理: work_time_to_video_time

# ログ・証拠

秘密情報、認証情報、個人情報を除いた失敗ログを貼る。

# 影響範囲

パート境界に一致する検索結果で、プレイヤー遷移先が1秒ずれる可能性がある。

# 変更ファイル

- `src/time-conversion.*`
- `tests/time-conversion.*`

# 参照ドキュメント

https://github.com/OWNER/REPO/blob/0123456789abcdef0123456789abcdef01234567/docs/time-model.md#L40-L95

# 修正の受け入れ条件

- [ ] 境界時刻が次のパートの `local_time_ms=0` になる
- [ ] 境界直前は前のパートの末尾になる
- [ ] 単体テストが追加される

# 確認手順

- [ ] 該当する単体テストが通る
```

## Spike

```markdown
# 背景

検索APIのレスポンス契約が未確定で、画面とAPIを安全に並列実装できない。

# 非スコープ

- 検索APIと画面の本実装

# 変更ファイル

- なし（リポジトリ差分なし）

# 参照ドキュメント

https://github.com/OWNER/REPO/blob/0123456789abcdef0123456789abcdef01234567/docs/spec.md#L10-L40

# 受け入れ条件

- [ ] 候補方式の比較結果と採否を第三者が確認できる
- [ ] 後続Issueの要否を判断できる

# 確認手順

- [ ] 記録した入力とコマンドで比較結果を再現する

# 調査する問い

検索結果を場面単位と動画単位のどちらで返すべきか。

# 時間枠

上限4時間。2時間経過時に証拠と残りの問いを整理する。

# 停止条件

- 判断に必要な証拠が揃ったら終了する
- 上限時間に達したら未解決点を明示して打ち切る

# 判断基準

画面側の変換量、API互換性、追加問い合わせ回数で比較する。

# 成果物と証拠

候補ごとのレスポンス例、再現コマンド、比較表を残す。

# 後続Issue

採用案の実装Issueを作る。採用を見送る場合は理由を明記して不要とする。
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
