# ライフサイクルコメント

Issueのライフサイクルコメントを書くときに読む。Status判定、実行Wave、作業権取得の規則は
[`issue-lifecycle.md`](issue-lifecycle.md) を先に読む。

# 方針

- GitHubメタデータと選択した構造化項目の値をコメントへ重複させない。
- 具体的なagentモデル名、branch名、Statusなどのfield assignmentは原則書かない。
- 例外として、作業権取得、引き継ぎ、解放では競合判定に必要なAgent Runの実行IDとGitHub上の証跡を書く。
- 外部依存はIssue、PR、CI run、log、design、chat threadなど、後から開けるURLで示す。
- 冒頭の絵文字付き一文でイベントを示し、該当するキーだけを書く。

# テンプレート

## Inbox

```markdown
📥 流入内容を整理した。

流入元: ... (URL)
要約: ...
影響: ...
次に確認すること: ...
```

## Triaged

```markdown
🔎 トリアージした。

判断根拠:

- ...

未確定事項: なし / ...
readyへ進めない理由: なし / ...
```

## Ready

判断が揺れやすいIssue、重要Issue、blocker解消直後だけ残す。

```markdown
🟢 着手条件を確認した。

確認済み:

- 受け入れ条件、非スコープ、確認手順
- 依存DAGと作業外blockerなし
- 参照ドキュメントと見積

補足: なし / ...
```

## 再トリアージ

```markdown
🔄 前提変更を受けて再トリアージした。

きっかけ: 受け入れ条件 / 依存関係 / リスク / 見積 / reopen / その他 ...
変更前: Size ...、Complexity ...、Risk ...、Effort ...、Estimate Confidence ...、Agent Tier ...
変更後: Size ...、Complexity ...、Risk ...、Effort ...、Estimate Confidence ...、Agent Tier ...
依存関係・Forecast・実行Waveへの影響: ...
戻すStatus: triaged / in-progress / blocked
```

## 作業権の取得

`作成時刻` はクライアント時刻を書かず、コメントのGitHub server timestampを参照する。

```markdown
🔐 Agent Runの作業権を取得する。

実行ID: `<harness>:<run-id>`
事前再取得: Project item更新世代または取得時刻 ...
作成時刻: このコメントのGitHub server timestamp
field/branch操作: 最古コメント判定前は未実施
```

競合に負けたagent:

```markdown
↩️ 作業権の競合により開始せず待機列へ戻る。

自分の実行ID: `...`
勝者の実行ID: `...`
判定根拠: 最古のGitHub server timestamp / 同値時のcomment ID
ローカル変更: なし / 扱い ...
```

敗者はAgent Run、Status、Assignee、branchを変更しない。勝者だけがfield更新後の事後再取得を通してからbranchとworktreeを作る。

## 作業中

```markdown
🚧 作業上の補足を記録する。

進捗または判断: ...
受け入れ条件への影響: なし / ...
次の操作: ...
```

## レビュー中

通常はコメントを書かず、PR本文とGitHubメタデータを正とする。外部判断や特殊なCI事情など、そこから分からない情報だけを書く。

```markdown
👀 レビュー中の特記事項を記録する。

PR本文やmetadataから分からないこと: ...
一時的な注意点: ...
次に確認する対象: レビュースレッド / CI実行 / 外部URL
```

## Blocked

`解除できる人` はrepository collaboratorならmention、それ以外はprofileまたは連絡先URLで特定する。

```markdown
⛔ 作業外blockerのため停止する。

理由: ...
解除できる人: @repo-collaborator / profile URL / 氏名
依存: #... / URL
担当内で試したこと: ...
再確認条件: 日時だけでなく、更新、判断、mergeなどの観測条件を書く
```

## 阻害要因の解消 / 再開

```markdown
🔓 Blockerが解消した。

解消内容: ...
戻す候補状態: ready / in-progress / in-review
再確認したこと: ...
作業権: 新規取得が必要 / 現在の実行IDを事後再取得済み
```

## 引き継ぎ

```markdown
🤝 Agent Runを引き継ぐ。

旧実行ID: `...`
新実行ID: `...`
理由: ...
引継ぐbranch/PR: #... / URL
完了済み: ...
未完了: ...
検証状態: ...
新担当の事後再取得: 未確認 / 確認済み
```

新担当が事後再取得で新実行IDを確認するまで、旧担当と新担当のどちらも追加変更を始めない。

## 解放 / 強制回収

```markdown
🔓 Agent Runを解放する。

実行ID: `...`
理由: ...
停止を確認した証跡: branch / PR / agent run / owner確認のURL
未push変更: なし / 保存場所と扱い ...
linked branch: 維持 / close / 削除候補
再投入条件: ...
```

強制回収では `理由` に「時間超過」だけを書かず、停止の証跡と確認者を含める。

## 投入見送り

```markdown
📤 作業権未取得のため実行Waveから外す。

元のWave: Wave ...
理由: Priority変更 / 容量 / 変更競合 / 依存変更 / 見積超過
再評価条件: ...
次の候補Wave: 未定 / Wave ...
Statusへの影響: なし / ...
```

## 完了

```markdown
✅ Type別の完了条件を確認した。

完了モード: ブランチ作成型 / spike / リポジトリ差分なし / epic
成果物またはmerge: #... / URL
受け入れ確認: ...
後続Issue: なし / #...
```

## 中止

```markdown
🛑 実行しない判断を記録する。

理由: duplicated / obsolete / out of scope / invalid / replaced
根拠: ...
代替または関連Issue: なし / #...
依存と作業権の整理: 完了 / 要対応 ...
```

## 再開 / 中止の取り消し

```markdown
♻️ 再トリアージする。

再開元: done / canceled
再開理由と新しい証跡: ...
以前のActual Start / Actual End: ... / ...
再確認するもの: 受け入れ条件 / 依存 / 見積 / Agent Tier / Type
以前の成果物への影響: ...
```

# 記入例

## 作業権の競合

最初のagent:

```markdown
🔐 Agent Runの作業権を取得する。

実行ID: `codex:run-01`
事前再取得: Project itemを作業権取得直前に取得済み
作成時刻: このコメントのGitHub server timestamp
field/branch操作: 最古コメント判定前は未実施
```

後から作業権を取得しようとしたagent:

```markdown
↩️ 作業権の競合により開始せず待機列へ戻る。

自分の実行ID: `codex:run-02`
勝者の実行ID: `codex:run-01`
判定根拠: 勝者commentのGitHub server timestampが古い
ローカル変更: なし
```

## Blocked: upstream PR

```markdown
⛔ 作業外blockerのため停止する。

理由: 依存ライブラリの公開APIがupstreamのreview結果で変わる可能性があり、こちらの実装を確定できない。
解除できる人: https://github.com/upstream-maintainer
依存: https://github.com/example/video-sdk/pull/482
担当内で試したこと: 現行版とPR版の差分を確認し、共通部分まで実装済み。
再確認条件: upstream PRがmergeまたはcloseされ、公開APIが確定したとき。
```

## Requested changesで作業再開

```markdown
🚧 作業上の補足を記録する。

進捗または判断: requested changesに対応するため実装を再開した。
受け入れ条件への影響: なし
次の操作: 指摘箇所を修正し、適用対象のcheckを再実行する。
```

この場合は外部blockerではないため `blocked` ではなく `in-progress` にする。

## Handoff

```markdown
🤝 Agent Runを引き継ぐ。

旧実行ID: `codex:run-10`
新実行ID: `codex:run-11`
理由: workspace所有者が交代するため。
引継ぐbranch/PR: #219
完了済み: fallback表示と単体テスト
未完了: 視覚確認とreview指摘1件
検証状態: 単体テスト成功、E2E未実施
新担当の事後再取得: 未確認
```

## Queue eviction

```markdown
📤 作業権未取得のため実行Waveから外す。

元のWave: Wave 3
理由: shared schemaを変更する#310と変更ファイルが競合し、作業環境枠も不足している。
再評価条件: #310のmerge後に参照ドキュメントと見積を再確認する。
次の候補Wave: Wave 4
Statusへの影響: なし
```

## Spike done

```markdown
✅ Type別の完了条件を確認した。

完了モード: spike
成果物またはmerge: 調査結果と採否判断をIssue本文へ反映済み
受け入れ確認: timebox内で3案を比較し、案Bを採用した
後続Issue: #412, #413
```
