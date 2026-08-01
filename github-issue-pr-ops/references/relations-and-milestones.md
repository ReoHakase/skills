# 親子関係、依存、Milestone

sub-issue、blocked by / blocking、Milestoneを設計・変更するとき、または複数Issueを一括起票するときに読む。

# 関係の意味

| 関係                  | 意味                                    | 正本                    |
| --------------------- | --------------------------------------- | ----------------------- |
| `epic` / sub-issue    | 成果の階層。実行順序は表さない          | GitHubのIssue関係       |
| blocked by / blocking | 前段Issueが完了するまで着手できない依存 | GitHubのIssue依存関係   |
| Stackのbase関係       | branch、レビュー、マージの直列順序      | GitHubのStackメタデータ |

Stackの上段PRは、下段PRのマージ前でも実装、確認、レビューできる。Stackの隣接関係だけを理由にblocked byを追加しない。実際に前段Issueの完了まで着手できない場合は、Stackのbase関係とは別にblocked byを設定する。Stack固有の設計と操作は`stacked-prs.md`を参照する。

外部判断、権限、Figma、上流PRなどIssueではない阻害要因を、ダミーIssueで依存関係へ押し込まない。

作業開始可能性とIssue関係は自動同期しない。関係を変更した後、影響するIssueを再取得して開始可能性を再判定する。

# 検証

書き込み前と関係変更後に確認する。

- 親子関係に自己参照、複数の親、循環がない。
- 依存関係に自己参照、重複、循環がない。
- 中止した前段Issueを自動的に完了扱いしない。
- 変更競合だけを理由にblocked byを追加していない。
- Stackの隣接関係を、着手不能という根拠なしにblocked byへ複製していない。
- 1つのStackが複数の`epic`へまたがっていない。
- 親Issueと前段Issueの番号・URLを、タイトル検索ではなく明示的に確定している。

# Milestone

MilestoneはGitHub標準のMilestoneを使う。Projectフィールドへ複製しない。

- リリース、確認点、締切目標をまとめる場合に使う。
- 期限未定なら期限なしで作ってよい。
- Issue作成前に、同名Milestoneの番号、状態、期限を確認する。
- 同名で意味や期限が異なる場合は自動再利用せず停止する。
- 期限変更は影響するIssueと外部の公開予定を確認してから行う。

# 一括起票の段階

配布スクリプトは使わず、次の単位で計画、適用、再取得を繰り返す。

1. 変更しない計画としてIssue一覧を作る。
2. 一時キー、タイトル、本文ファイル、種類、Milestone、親キー、前段キーを確定する。
3. Milestoneを作成または明示的に再利用する。
4. 親Issueから順にIssueを作成し、返された番号とURLを一時キーへ記録する。
5. Issue番号を使ってsub-issueと依存関係を設定する。
6. 全Issueと関係を再取得し、計画との差分を検証する。

可変なタイトルを作成済みIssueとの結合キーにしない。作成時のURLを保存し、以後はIssue番号またはURLを使う。

書き込みは、対象リポジトリ、件数、Milestone、作成するIssueの一時キーを含む確認文字列に利用者が同意した後だけ開始する。途中で1件でも失敗した場合は残りを止め、作成済みの番号と未実行項目を報告する。自動削除で巻き戻さない。

一時的な計画データの例は`assets/issue-plan.example.json`を参照する。このJSONは作成結果の正本ではなく、書き込み前の計画と返却された識別子を結ぶためだけに使う。

# 高水準コマンド

親付きIssueを作る。

```bash
gh issue create \
  --repo OWNER/REPO \
  --parent PARENT_NUMBER \
  --milestone "MILESTONE_TITLE" \
  --title "Issueタイトル" \
  --body-file issue.md
```

既存Issueを親へ追加する。

```bash
gh issue edit PARENT_NUMBER \
  --repo OWNER/REPO \
  --add-sub-issue CHILD_NUMBER
```

依存を追加する。

```bash
gh issue edit BLOCKED_NUMBER \
  --repo OWNER/REPO \
  --add-blocked-by BLOCKER_NUMBER
```

変更後は`gh issue view ... --json`またはGitHub MCPで親子・依存関係を再取得する。高水準コマンドが対象環境で使えないことを確認した場合だけ`gh api`または`gh api graphql`へ切り替える。
