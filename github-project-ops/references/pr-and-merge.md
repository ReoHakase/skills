# PRとマージ

PR本文、`in-review` 判断、マージコミット、マージキュー、自動マージを扱うときに読む。

# PR状態とIssue Status

| PRの状態                                             | Issue Status  | 操作                                                   |
| ---------------------------------------------------- | ------------- | ------------------------------------------------------ |
| Draft PR                                             | `in-progress` | 実装、自己確認、PR本文の更新を続ける                   |
| レビュー可能状態で通常のレビューまたはCI待ち         | `in-review`   | レビュアーと最新コミットSHAの検査を監視する            |
| 対応が必要な変更要求                                 | `in-progress` | 指摘へ対応し、再確認後にレビュー可能状態へ戻す         |
| 修正可能なCI失敗またはマージ競合                     | `in-progress` | 修正または競合解消を行う                               |
| 当該担当では解除できない外部判断、権限、上流障害待ち | `blocked`     | 阻害要因、解除者、依存URL、再確認条件をIssueへ記録する |
| マージ済み                                           | `done`候補    | Issue Type別の完了条件を確認してから `done` にする     |

PRを作成しただけでは `in-review` にしない。Draft解除とレビュー依頼を境界にする。通常の待ち時間を `blocked` として扱わない。

# 目次

- PR状態とIssue Status
- PR本文運用
- PR本文テンプレート
- PR本文例
- `in-review` コメント方針
- Merge policy
- gh CLI / MCP操作

# PR本文運用

PR本文にはProject fieldのメタデータや具体的なエージェントモデル名を書かない。Agent HarnessとAgent ModelはProject fieldへ記録する。

PR本文は常体で書く。論文やレポートと同じく「である」「する」「できる」を使い、丁寧体は使わない。

PR本文に必須の要素:

- 概要
- 関連Issue
- スコープ
- Issueとの差異
- 振る舞い
- 確認結果
- 展開と切り戻し
- リスク
- レビュー案内
- ブランチ作成型Issueを正確に1件だけ閉じる `Closes #<issue-number>` または同等の自動クローズキーワード

必須の節が存在していても、`-`、`- [ ]`、`done`、`確認済み` のような仮記入だけなら不十分である。PR作成前に、第三者が確認できる具体的な変更点、振る舞い、確認結果、未実施理由、展開と切り戻し、リスク、レビュー案内が書かれているか確認する。

PR本文は最新状態の要約として随時更新する。振る舞い、確認結果、展開と切り戻し、リスク、レビュー案内が変わった場合は、古い情報を放置せず本文を更新する。

ブランチ作成型のPRは自動クローズキーワードで対応Issueを正確に1件だけ閉じる。単なる関連Issueは通常の `#123` 参照にし、複数Issueを同時に閉じない。epic、リポジトリ差分なしの作業、PRを成果物にしないspikeにはこの規則を機械的に当てはめない。

既存PRでは説明文を先頭コメントとして編集する。参照: <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/getting-started/helping-others-review-your-changes>

Issue、PR、コミットの参照は、同一リポジトリなら `#123` や短いコミットSHAだけを書く。GitHubが自動リンクとプレビューで参照先を表示するため、タイトルを併記しない。別リポジトリのIssue/PRは `OWNER/REPO#123` と書く。参照: <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls>

古いが消すと混乱する短い記述は取り消し線で残す。長い経緯は折りたたみ欄へ移す。秘密情報、認証情報、個人情報、公開してはいけないログはどちらにも残さない。

# 振る舞い

`振る舞い` には、実装したものの動作確認結果を書く。

- CLI変更: 実行したコマンドと出力をコードブロックで書く。
- 対話型CLI変更: asciinema、termsvgなどで色付きアニメーション画像または記録リンクを残す。
- UI変更: 画面部品、ページ、主要状態のスクリーンショットまたは動画を貼る。
- UIや視覚的な出力がない内部ロジック変更: Mermaidフロー図で変更後の流れを書く。

# 確認結果

`確認結果` には、変更に適用できる自動テストと手動確認だけを書く。単体、結合、E2Eのすべてを一律に要求しない。実行したコマンドまたは操作、結果、対象となる受け入れ条件を示す。適用できるが未実施の確認は、確認名と理由を書く。Project fieldやCIメタデータは複製しない。

# PR本文テンプレート

```markdown
## 概要

- 変更内容を書く

## 関連Issue

Closes #123

## スコープ

実装したこと:

- ...

意図的に扱わないこと:

- ...

## Issueとの差異

- なし / Issue本文から外れた点と理由を書く

## 振る舞い

- 動作確認結果を書く

## 確認結果

実施した確認:

- `command` — 結果を書く

未実施の確認と理由:

- なし / 未実施の確認と理由を書く

## 展開と切り戻し

展開:

- 不要 / 手順と事前条件を書く

切り戻し:

- 不要 / 判定基準と手順を書く

## リスク

- 既知のリスクと緩和策を書く

## レビュー案内

読む順序:

1. 最初に見るファイルまたはコミットを書く

重点:

- 境界条件や設計判断を書く
```

# PR本文例

```markdown
## 概要

- 検索結果カードに品番、長さ、容量、解像度、商品名を表示した
- 一致シーンの時刻、説明、タグ、セリフ抜粋を表示した
- 未取得項目のfallback表示を追加した

## 関連Issue

Closes #123

## スコープ

実装したこと:

- 検索結果カードの表示項目追加
- フィクスチャデータでの表示確認

意図的に扱わないこと:

- ホバー動画プレビュー
- 検索順位変更

## Issueとの差異

- なし

## 振る舞い

検索結果フィクスチャでカードを表示し、品番、商品名、一致場面、未取得時の代替表示を同じカード内で確認できる。

![検索結果カードの確認](https://github.com/OWNER/REPO/assets/000000/search-card.png)

## 確認結果

実施した確認:

- `bun test search-result` — 作品情報、一致場面、欠損値の代替表示を確認した
- 検索結果画面の手動確認 — 長い商品名でも主要情報が崩れないことを確認した

未実施の確認と理由:

- E2Eテスト — この変更では利用可能な試験環境がなく、同じ経路を画面部品テストと手動確認で検証した

## 展開と切り戻し

展開:

- 通常のWebアプリケーション展開だけで、追加手順は不要

切り戻し:

- 情報が読めない、またはカード配置が崩れる場合は、このPRのマージコミットをrevertする

## リスク

- UI表示だけの変更で、DBスキーマと検索順位には影響しない

## レビュー案内

読む順序:

1. `web/components/search-result.*`
2. `web/components/search-result.test.*`

重点:

- 情報量が多すぎてカードが読みにくくなっていないか
- 未取得項目の表示が分かりやすいか
```

# `in-review` コメント方針

通常はコメントを書かない。PR本文に概要、関連Issue、スコープ、Issueとの差異、振る舞い、確認結果、展開と切り戻し、リスク、レビュー案内を書き、`Closes #...` / `Fixes #...` / `Resolves #...` による自動追跡に任せる。

PR本文やGitHubメタデータで分かる内容をコメントへ重複させない。レビュアーへの一時的な補足、CIの特殊事情、外部判断待ち、通常と違う確認依頼がある場合だけ、`lifecycle-comments.md` のレビュー中コメントを使う。

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

完成済みのPR本文を先に作り、具体的な概要、スコープ、Issueとの差異、振る舞い、確認結果、展開と切り戻し、リスク、レビュー案内、自動クローズキーワードがあることを確認してからPRを作成する。

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
