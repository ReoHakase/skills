# Project運用の解除

Project/Milestone運用を外すときに読む。標準は可逆優先とし、目的に応じて `detach`、`disable`、`hide`、`destroy` を選ぶ。IssueやPRは閉じず、本文も原則編集しない。

# モード

| モード    | 操作                                                      | Projectアイテムのフィールド値 | 戻し方                           |
| --------- | --------------------------------------------------------- | ----------------------------- | -------------------------------- |
| `detach`  | リポジトリとProjectの紐づけだけを外す                     | 保持                          | `gh project link`                |
| `disable` | Projectを閉じる                                           | 保持                          | `gh project close --undo`        |
| `hide`    | 対象アイテムをアーカイブする                              | 保持                          | `gh project item-archive --undo` |
| `destroy` | Projectアイテム、フィールド、Milestone、Projectを削除する | 失われる                      | 書き出しから手動再構築           |

`item-delete` は可逆操作ではない。フィールド値を保持したい場合は `hide` を使う。

# 事前確認

GitHub上の実状態を先に読む。推測したProject番号、ProjectアイテムID、Milestone番号で操作しない。

```bash
gh repo view OWNER/REPO --json id,nameWithOwner,url,defaultBranchRef,owner,isPrivate
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 1000
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 100
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100
```

Milestoneに属するIssueを読む。

```bash
gh issue list \
  --repo OWNER/REPO \
  --milestone "First Release" \
  --state all \
  --limit 1000 \
  --json number,title,state,url,milestone
```

解除対象のProject URL、リポジトリURL、ProjectアイテムID、Issue番号を一覧化し、依頼されたモードを記録してから実行する。

# `detach`: リポジトリとの紐づけを外す

Projectとアイテムを残したまま、リポジトリからの紐づけだけを外す。

```bash
gh project unlink PROJECT_NUMBER --owner OWNER --repo REPO_NAME
```

戻す場合:

```bash
gh project link PROJECT_NUMBER --owner OWNER --repo REPO_NAME
```

# `disable`: Projectを閉じる

Projectを読み取り専用の履歴として残し、通常運用から外す。

```bash
gh project close PROJECT_NUMBER --owner OWNER
```

戻す場合:

```bash
gh project close PROJECT_NUMBER --owner OWNER --undo
```

# `hide`: アイテムをアーカイブする

Project内の対象アイテムを非表示にする。Issue/PR本体と、選択した構造化フィールドの値は保持される。

```bash
gh project item-archive PROJECT_NUMBER --owner OWNER --id PROJECT_ITEM_ID
```

戻す場合:

```bash
gh project item-archive PROJECT_NUMBER --owner OWNER --id PROJECT_ITEM_ID --undo
```

IssueからMilestone割当だけを外す場合は、Milestone本体を残す。

```bash
gh issue edit ISSUE_NUMBER --repo OWNER/REPO --remove-milestone
```

必要な場合だけsub-issueや依存関係も解除する。Project/Milestoneだけを外す場合はWBS構造を残してよい。

```bash
gh issue edit CHILD_NUMBER --repo OWNER/REPO --remove-parent
gh issue edit PARENT_NUMBER --repo OWNER/REPO --remove-sub-issue CHILD_NUMBER
gh issue edit BLOCKED_NUMBER --repo OWNER/REPO --remove-blocked-by BLOCKER_NUMBER
gh issue edit BLOCKER_NUMBER --repo OWNER/REPO --remove-blocking BLOCKED_NUMBER
```

# リポジトリへコピーしたアセットの削除

対象リポジトリへコピーしたファイルだけを消す。他の用途へ編集済みの`.github`ファイルは削除しない。

候補:

- `.github/project/views.md`
- `.github/ISSUE_TEMPLATE/feature.yml`
- `.github/ISSUE_TEMPLATE/spike.yml`
- `.github/ISSUE_TEMPLATE/bug.yml`
- `.github/ISSUE_TEMPLATE/config.yml`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`

Git管理下で、このスキル導入専用のファイルだと確認できたものだけ削除する。

```bash
git rm .github/project/views.md
```

# `destroy`: 破壊的な削除

`detach`、`disable`、`hide` で目的を満たせない場合だけ使う。削除前に復元用JSONを作り、対象を再表示し、確認文字列を要求する。

```bash
set -euo pipefail

mkdir -p github-project-ops-export
gh project view PROJECT_NUMBER --owner OWNER --format json \
  > github-project-ops-export/project.json
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 1000 \
  > github-project-ops-export/items.json
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 100 \
  > github-project-ops-export/fields.json
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100 \
  > github-project-ops-export/milestones.json
gh issue list --repo OWNER/REPO --state all --limit 1000 \
  --json number,title,url,state,milestone \
  > github-project-ops-export/issues.json
```

書き出したファイルを開き、Projectの所有者、タイトル、URL、番号、リポジトリ、全アイテム数を確認する。確認文字列はProjectのタイトルと番号を含める。

```bash
set -euo pipefail

EXPECTED="OWNER/REPO#destroy-project:PROJECT_OWNER:PROJECT_TITLE#PROJECT_NUMBER"
printf '破壊的削除の確認文字列 (%s): ' "$EXPECTED"
read -r CONFIRM
test "$CONFIRM" = "$EXPECTED" || exit 1
```

確認後に、依頼された対象だけを削除する。Projectアイテムを削除すると、そのアイテムの独自フィールド値は失われる。

```bash
set -euo pipefail

gh project item-delete PROJECT_NUMBER --owner OWNER --id PROJECT_ITEM_ID
gh project field-delete --id FIELD_ID
gh api repos/OWNER/REPO/milestones/MILESTONE_NUMBER --method DELETE
gh project delete PROJECT_NUMBER --owner OWNER
```

GitHub既定フィールドや他用途のフィールドは削除しない。Milestoneは配下Issueが空であることを確認してから削除する。Projectを削除する場合は個別のProjectアイテム・フィールド削除を先に行う必要はない。

# 検証

選んだモードに応じて、期待する状態を読み取り専用コマンドで確認する。

```bash
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 1000
gh issue list --repo OWNER/REPO --state all --limit 1000 \
  --json number,title,state,url,milestone
```

- `detach`: リポジトリの紐づくProject一覧に対象がない。Projectとアイテムは残る。
- `disable`: Projectが閉じており、アイテムは残る。
- `hide`: 対象アイテムがアーカイブされ、元に戻せる。
- `destroy`: 削除対象が見つからず、書き出した一式が手元に残る。

リポジトリへコピーしたアセットを削除した場合は差分も確認する。

```bash
git status --short
git diff -- .github
```
