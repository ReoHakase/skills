# 作業権、引き継ぎ、解放

複数の人やエージェントが同じIssueへ着手する可能性があるときに読む。Projectの有無にかかわらず、この手順を作業権の正本にする。

# 作業開始前

次をGitHubから再取得する。

- Issueがopenであり、受け入れ条件、非スコープ、確認手順が揃っている。
- 未解決のblocked byと外部阻害要因がない。
- 有効な作業権取得コメントがない。
- 競合するAssignee、紐づくbranch、open PRがない。
- 参照ドキュメントが現在も有効である。

Projectの`Status`だけで開始可能と判断しない。Projectがない場合も、Issue本文とGitHubメタデータから同じ条件を確認する。

# 実行ID

実行ごとに一意で、外部情報を含まないIDを使う。

```text
<実行環境>:<一意なID>
```

非公開タスクURL、利用者名、認証情報、プロンプト内容を埋め込まない。同じIDを再利用しない。

# 規約イベント

規約コメントの先頭へ、次のいずれかの固定マーカーを1行で置く。

```text
<!-- github-issue-pr-ops:event=claim;version=1;run=<ID> -->
<!-- github-issue-pr-ops:event=release;version=1;run=<ID> -->
<!-- github-issue-pr-ops:event=handoff;version=1;from=<OLD_ID>;to=<NEW_ID> -->
<!-- github-issue-pr-ops:event=reclaim;version=1;from=<OLD_ID>;to=<NEW_ID> -->
```

マーカー付きコメントは編集・削除せず、訂正も新しいイベントとして追記する。コメント本文の自然文だけからイベント種別を推測しない。

REST APIで全ページを取得し、`created_at`の昇順、同時刻なら数値`id`の昇順に並べる。有効な所有者はイベント列を先頭から適用して決める。

- 所有者がいない区間では、最初の`claim`だけが所有者になる。後続の`claim`は敗者である。
- 現所有者自身の`release`だけが所有を終了する。
- 現所有者または指定された責任者が確認した`handoff`だけが所有者を`to`へ変える。
- 停止証拠と確認者を本文に持つ`reclaim`だけが所有者を`to`へ変える。
- 未知の版、欠落したページ、矛盾するイベント、編集・削除の疑いがある場合は停止する。

```bash
gh api --paginate \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/OWNER/REPO/issues/ISSUE_NUMBER/comments
```

# 取得手順

1. 事前確認後、`claim`マーカーと一意な実行IDを含む作業権取得コメントだけを作る。
2. 同じIssueの有効な取得コメントを再取得する。
3. GitHubサーバー時刻が最古のコメントを勝者にする。同時刻ならコメントIDが小さい方を勝者にする。
4. 敗者はAssignee、branch、PR、Project項目を変更しない。
5. 勝者だけがAssigneeを設定する。
6. コメント、Assignee、紐づくbranch、open PRを再取得し、自分が勝者で競合がないことを確認する。branchは`gh issue develop --list ISSUE_NUMBER`でも確認する。
7. リポジトリ差分を作るIssueだけ、紐づくbranchと独立した`worktree`を作る。

Assigneeの更新成功だけでは取得成功にしない。事後再取得を必須にする。

# 取得コメント

```markdown
<!-- github-issue-pr-ops:event=claim;version=1;run=<実行環境>:<一意なID> -->

🔐 作業権を取得する。

- 実行ID: `<実行環境>:<一意なID>`
- 対象: #123
- 開始前確認: 未解決の前段なし / 既存branchなし / open PRなし
- 予定する変更: `src/**/*.ts`、`tests/**/*.test.ts`
```

コメントの作成時刻とIDはGitHubの返却値を使う。ローカル時刻を競合判定に使わない。

割り当て可能なGitHub利用者がない実行環境では、Assigneeを作業権の代用にしない。リポジトリ規約が許す場合だけコメントを正本として続行し、Assigneeを設定できなかった理由を取得コメントへ追記する。

# 稼働報告

長時間作業では、意味のある区切りで次だけをコメントする。

```markdown
🛠️ 作業を継続している。

- 実行ID: `<実行環境>:<一意なID>`
- 完了したこと: ...
- 残っていること: ...
- 新しい阻害要因: なし / ...
```

経過時間だけで作業権を無効にしない。branch、PR、最新コメント、実行環境の停止証拠を確認する。

# 阻害要因

担当者自身で解消できない権限、外部判断、上流障害などで停止するときにコメントする。

```markdown
⛔ 作業を停止する。

- 実行ID: `<実行環境>:<一意なID>`
- 阻害要因: ...
- 解除できる人または条件: ...
- 証拠: ...
- 次の確認条件: ...
```

通常のレビュー待ち、CI実行中、マージ待ちを阻害要因として扱わない。

# 引き継ぎ

旧担当が最初に変更を止め、次をコメントする。

```markdown
<!-- github-issue-pr-ops:event=handoff;version=1;from=<旧ID>;to=<新ID> -->

🤝 作業を引き継ぐ。

- 旧実行ID: `<旧ID>`
- 新実行ID: `<新ID>`
- 理由: ...
- branch / PR: ...
- 完了したこと: ...
- 未完了作業: ...
- 未push差分の扱い: なし / ...
```

旧担当または明示された責任者が引き継ぎを承認し、新担当がコメントとAssigneeを再取得してから再開する。確認までは双方とも変更しない。

# 解放と強制回収

通常の解放:

```markdown
<!-- github-issue-pr-ops:event=release;version=1;run=<実行環境>:<一意なID> -->

🔓 作業権を解放する。

- 実行ID: `<実行環境>:<一意なID>`
- 理由: ...
- branch / PRの扱い: ...
- 未push差分の扱い: なし / ...
```

コメント後にAssigneeを外す。Projectを併用している場合は、その後に`Agent Run`と`Status`を同期する。

強制回収では、`reclaim`マーカーを使い、旧担当が停止している証拠、branchとPRの状態、確認者、回収理由をコメントする。一定時間が経過したという理由だけで回収しない。
