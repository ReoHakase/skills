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

PR本文には構造化項目のメタデータや具体的なエージェントモデル名を書かない。Agent HarnessとAgent Modelは、それぞれ選択した正本へ記録する。

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

`確認結果` には、変更に適用できる自動テストと手動確認だけを書く。単体、結合、E2Eのすべてを一律に要求しない。実行したコマンドまたは操作、結果、対象となる受け入れ条件を示す。適用できるが未実施の確認は、確認名と理由を書く。構造化項目やCIメタデータは複製しない。

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

- `<確認コマンド>` — 結果を書く

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

# マージ方針

既定ブランチを壊さずにPRを流す。方式は固定せず、所有者種別、公開範囲、組織の契約プランを先に読む。

```bash
DEFAULT_BRANCH=$(gh repo view OWNER/REPO --json defaultBranchRef --jq '.defaultBranchRef.name')
gh api --method GET -H "X-GitHub-Api-Version: 2026-03-10" repos/OWNER/REPO
gh api --method GET -H "X-GitHub-Api-Version: 2026-03-10" orgs/ORG
```

| 利用資格                                                    | 推奨する統合方式                                       |
| ----------------------------------------------------------- | ------------------------------------------------------ |
| 組織所有の公開リポジトリ                                    | マージコミット + マージキュー + 自動マージ             |
| GitHub Enterprise Cloud組織所有の非公開・internalリポジトリ | マージコミット + マージキュー + 自動マージ             |
| 個人所有またはマージキュー非対応と確認済みのリポジトリ      | マージコミット + 保護ブランチ + 利用可能なら自動マージ |
| 契約プランや利用資格を確認できないリポジトリ                | 未決定。確認できるまで停止                             |

この表は利用資格から出す推奨値であり、設定済みという証拠ではない。既定ブランチに適用されるruleset、ブランチ保護、リポジトリのマージ設定、CI定義を読む。

```bash
gh api --method GET -H "X-GitHub-Api-Version: 2026-03-10" \
  "repos/OWNER/REPO/rulesets?includes_parents=true"
gh api --method GET -H "X-GitHub-Api-Version: 2026-03-10" \
  "repos/OWNER/REPO/branches/$DEFAULT_BRANCH/protection"
gh api --method GET -H "X-GitHub-Api-Version: 2026-03-10" \
  "repos/OWNER/REPO/contents/.github/workflows?ref=$DEFAULT_BRANCH"
```

一覧に出たrulesetは各IDの詳細も読む。マージキュー方式ではRequire merge queue、自動マージ、PRと `merge_group` の必須検査を確認する。代替方式ではPR必須、必須レビュー、必須検査、会話解決、直接push禁止をrulesetまたはブランチ保護で確認する。設定確認・変更に必要な権限、通常の自動マージの利用可否も別に確認する。必要な保護を強制できない、または権限不足で確認できない場合は、Issue投入前に停止する。

全方式で、既定ブランチへの直接pushを禁止し、PR、必須レビュー、必須検査、会話解決をrulesetまたはbranch protectionで要求する。マージコミットを使い、squash/rebaseマージとRequire linear historyは標準では使わない。

マージキューを利用できる場合だけRequire merge queueを有効化し、全必須検査を次の両方で実行する。

```yaml
on:
  pull_request:
  merge_group:
    types: [checks_requested]
```

- `pull_request`: PR単体の早期フィードバック。
- `merge_group`: マージキュー上で実際に既定ブランチへ入る候補状態の最終確認。

PR単体ではCIが通っていても、先行PRと組み合わせると壊れることがあるため、`merge_group` でも同じ必須検査を走らせる。マージキュー非対応時は `pull_request` の必須検査を合格条件にし、Require merge queueを設定しない。

`Maximum group size = 100` はマージキュー利用時に採用してよい。これはCIを1回にまとめる設定ではなく、必須検査を通過した後に既定ブランチへ一度にマージできるPR数の上限である。

GitHub標準のマージキューだけでは、特定のPR群を明示的に1つのmerge groupへ固定し、CIも1回だけにすることはできない。epicブランチは使わない。

リポジトリ設定は次を標準にする。

```text
allow_merge_commit = true
allow_squash_merge = false
allow_rebase_merge = false
allow_auto_merge = true
```

マージ候補の確認はProject filterへ承認状態や検査結果を書かず、PRごとに次を読む。

```bash
gh pr view PR_NUMBER \
  --repo OWNER/REPO \
  --json baseRefName,headRefName,isDraft,reviewDecision,statusCheckRollup,mergeable,mergeStateStatus,autoMergeRequest
gh pr checks PR_NUMBER --repo OWNER/REPO --required
```

`statusCheckRollup` は検査全体の把握に使い、必須検査だけの合否は `gh pr checks --required` で判定する。

# gh CLI / MCP操作

紐づくブランチの作成:

```bash
DEFAULT_BRANCH=$(gh repo view OWNER/REPO --json defaultBranchRef --jq '.defaultBranchRef.name')
gh issue develop 123 \
  --repo OWNER/REPO \
  --name "123/feat-ui-search-cards" \
  --base "$DEFAULT_BRANCH" \
  --checkout
```

完成済みのPR本文を先に作り、具体的な概要、スコープ、Issueとの差異、振る舞い、確認結果、展開と切り戻し、リスク、レビュー案内、自動クローズキーワードがあることを確認してからPRを作成する。

```bash
gh pr create \
  --repo OWNER/REPO \
  --base "$DEFAULT_BRANCH" \
  --head "123/feat-ui-search-cards" \
  --draft \
  --title "検索結果カードで一致シーンの無音プレビューを表示する" \
  --body-file pr.md
```

実装と適用対象の検査が終わったら、Draftを解除して状態を再確認する。この確認が終わるまではIssueを `in-review` にしない。

```bash
gh pr ready PR_NUMBER --repo OWNER/REPO
gh pr view PR_NUMBER --repo OWNER/REPO --json isDraft,headRefOid,reviewDecision,statusCheckRollup
```

PR本文には必ず次のいずれかを含める。

```text
Closes #123
Fixes #123
Resolves #123
```

能力確認後に自動マージを利用する場合は、条件を満たしたPRで有効化する。マージキュー必須ブランチなら `gh` がキュー投入または自動マージ予約へ切り替える。

```bash
gh pr merge 123 --repo OWNER/REPO --auto --merge
```

保護ブランチ経路で通常の自動マージを利用できない場合だけ、レビュー、最新コミットの必須検査、会話解決、マージ可能状態を再確認した権限保持者が手動マージする。`--admin` で保護を迂回しない。

```bash
gh pr checks 123 --repo OWNER/REPO --required
gh pr view 123 --repo OWNER/REPO \
  --json headRefOid,reviewDecision,mergeable,mergeStateStatus,isDraft
gh pr merge 123 --repo OWNER/REPO --merge
```

MCPはPRレビュー結果の要約、CI失敗原因の整理、Project viewの現状把握に使う。再現可能な操作はgh CLIへ落とす。
