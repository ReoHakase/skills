# PR、レビュー、マージ

PR本文、Draft解除、レビュー状態、CI、マージ経路を扱うときに読む。stacked PRの作成、同期、再構成は`stacked-prs.md`も参照する。

# PRの段階

| 状態                               | 扱い                                |
| ---------------------------------- | ----------------------------------- |
| Draft PR                           | 実装、自己確認、本文更新を続ける    |
| レビュー可能でレビューまたはCI待ち | 最新head SHAを基準に確認する        |
| 変更要求、修正可能なCI失敗、競合   | 実装へ戻して修正する                |
| 外部判断、権限、上流障害だけで停止 | Issueへ阻害要因を記録する           |
| マージ済み                         | Issueの種類ごとの完了条件を確認する |

PRを作成しただけでレビュー可能扱いにしない。Draft解除、本文、レビュアー、適用できる確認結果が揃った時点を境界にする。

# PR本文

PR本文には次を含める。

- 概要
- 関連Issue
- スコープ
- Issueとの差異
- 振る舞い
- 確認結果
- 展開と切り戻し
- リスク
- レビュー案内
- 対応Issueを正確に1件だけ閉じる自動クローズキーワード

Projectフィールド、組織Issue Field、具体的なエージェントモデル名を本文へ複製しない。既存PRでは説明文を編集し、現在信頼できる情報へ更新する。

Stack内のPRでは、`レビュー案内`に次を加える。

- この段だけが担う責務
- 下段から引き継ぐ前提
- このPR単独で確認できる範囲

Stack番号、Stack内の位置一覧、各PRのbaseは本文へ複製しない。GitHubのStackメタデータを正本として読む。

自動クローズは次のいずれかを使う。

```text
Closes #123
Fixes #123
Resolves #123
```

単なる参照Issueは通常の`#123`として書き、複数Issueを一度に閉じない。Stack内の各PRも対応する末端Issueだけを閉じる。`epic`やPRを成果物にしない調査へ機械的に適用しない。

# 振る舞いと確認結果

- CLI変更: 実行したコマンドと結果を示す。
- UI変更: 主要状態の画像または動画を示す。
- 内部処理: 必要ならMermaidで変更後の流れを示す。
- 実施した確認: コマンドまたは操作、結果、対応する受け入れ条件を書く。
- 未実施の確認: 適用可能だが未実施のものと理由を書く。

単体、結合、E2Eを一律に必須にしない。変更に適用できる確認を選ぶ。

# 通常PRの作成

既定ブランチと既存PRを確認する。

```bash
DEFAULT_BRANCH=$(gh repo view OWNER/REPO --json defaultBranchRef --jq '.defaultBranchRef.name')
gh pr list --repo OWNER/REPO --head BRANCH --state open --json number,url,isDraft
```

完成した本文を用意してDraft PRを作る。

```bash
gh pr create \
  --repo OWNER/REPO \
  --base "$DEFAULT_BRANCH" \
  --head BRANCH \
  --draft \
  --title "自然な言葉のPRタイトル" \
  --body-file pr.md
```

実装と該当確認が終わったらDraftを解除し、最新状態を再取得する。

```bash
gh pr ready PR_NUMBER --repo OWNER/REPO
gh pr view PR_NUMBER \
  --repo OWNER/REPO \
  --json isDraft,headRefOid,reviewDecision,statusCheckRollup,mergeable,mergeStateStatus
```

stacked PRは`gh stack submit`でDraft作成した後、各PRの本文をこのスキルのテンプレートで置き換え、個別にDraftを解除する。通常PRの`gh pr create`経路と混ぜない。具体的なコマンドと失敗時の停止条件は`stacked-prs.md`を参照する。

# Stack下段の変更後

下段branchを修正したら、上段を順番にrebaseしてpushする。影響した全PRについて、GitHub上のbaseとhead SHA、Draft状態、レビュー判断、必須チェックを再取得する。古いhead SHAへの承認や確認結果を、現在も有効とみなさない。

```bash
gh pr view PR_NUMBER \
  --repo OWNER/REPO \
  --json baseRefName,headRefOid,isDraft,reviewDecision,statusCheckRollup,mergeable,mergeStateStatus
gh pr checks PR_NUMBER --repo OWNER/REPO --required
```

# マージ経路

所有者種別や契約プランだけで方式を決めない。既定ブランチへ適用されるruleset、ブランチ保護、必須チェック、リポジトリのマージ設定、CI起動条件を読む。

- マージキューが実際に必須なら、PRと`merge_group`で同じ必須チェックを実行する。
- マージキューが使えない場合は、必須レビューと必須チェックを強制する保護ブランチ経路を使う。
- どちらも確認または強制できない場合は、保護を迂回せず停止する。
- `--admin`で保護を迂回しない。

## 通常PR

必須チェックと最新head SHAを確認する。

```bash
gh pr checks PR_NUMBER --repo OWNER/REPO --required
gh pr view PR_NUMBER \
  --repo OWNER/REPO \
  --json headRefOid,reviewDecision,mergeable,mergeStateStatus,isDraft
```

マージキューまたは自動マージを利用できる場合:

```bash
gh pr merge PR_NUMBER --repo OWNER/REPO --auto --merge
```

通常の自動マージを利用できない保護ブランチ経路では、権限保持者が最新状態を再確認してからマージする。

```bash
gh pr merge PR_NUMBER --repo OWNER/REPO --merge --match-head-commit HEAD_SHA
```

標準はマージコミットとする。既存リポジトリが別方式を明示している場合は、その規約を優先する。

## stacked PR

Stackでは自動マージと`gh pr merge`を使わない。全PRのDraft状態、承認、必須チェック、head SHA、base関係、線形履歴を再取得し、最下段から連続して条件を満たす範囲だけを`gh stack merge`で処理する。マージキュー利用時は方式を指定せず、直接マージ時だけリポジトリ既定の方式を指定する。実行後の確認を含む詳細は`stacked-prs.md`に従う。

# コピー用アセット

- PR本文: `assets/.github/pull_request_template.md`
- マージキュー対応CI例: `assets/.github/workflows/merge-queue-checks.example.yml`

CI例は既存ワークフローを上書きする完成品ではない。マージキューを採用するときだけ、既存の必須チェックへ`merge_group`起動条件を統合する。プレースホルダーを対象リポジトリ固有の確認コマンドへ置き換えるまでは失敗する設定を維持する。
