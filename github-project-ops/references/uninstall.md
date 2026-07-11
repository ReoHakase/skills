# Uninstall

Project/Milestone運用を外すときに読む。標準は可逆優先とし、目的に応じて `detach`、`disable`、`hide`、`destroy` を選ぶ。IssueやPRは閉じず、本文も原則編集しない。

# モード

| モード    | 操作                                      | Project itemのfield値 | 戻し方                           |
| --------- | ----------------------------------------- | --------------------- | -------------------------------- |
| `detach`  | repositoryとProjectのlinkだけを外す       | 保持                  | `gh project link`                |
| `disable` | Projectをcloseする                        | 保持                  | `gh project close --undo`        |
| `hide`    | 対象itemをarchiveする                     | 保持                  | `gh project item-archive --undo` |
| `destroy` | item、field、Milestone、Projectを削除する | 失われる              | exportを使った手動再構築         |

`item-delete` は可逆操作ではない。field値を保持したい場合は `hide` を使う。

# 事前確認

GitHub上の実状態を先に読む。推測したProject number、Project item ID、Milestone numberで操作しない。

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

解除対象のProject URL、repository URL、Project item ID、Issue numberを一覧化し、依頼されたモードを記録してから実行する。

# detach: repository linkを外す

Projectとitemを残したまま、repositoryからのlinkだけを外す。

```bash
gh project unlink PROJECT_NUMBER --owner OWNER --repo REPO_NAME
```

戻す場合:

```bash
gh project link PROJECT_NUMBER --owner OWNER --repo REPO_NAME
```

# disable: Projectを閉じる

Projectをread-onlyの履歴として残し、通常運用から外す。

```bash
gh project close PROJECT_NUMBER --owner OWNER
```

戻す場合:

```bash
gh project close PROJECT_NUMBER --owner OWNER --undo
```

# hide: itemをarchiveする

Project内の対象itemを非表示にする。Issue/PR本体とProject field値は保持される。

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

必要な場合だけsub-issueやdependencyも解除する。Project/Milestoneだけを外す場合はWBS構造を残してよい。

```bash
gh issue edit CHILD_NUMBER --repo OWNER/REPO --remove-parent
gh issue edit PARENT_NUMBER --repo OWNER/REPO --remove-sub-issue CHILD_NUMBER
gh issue edit BLOCKED_NUMBER --repo OWNER/REPO --remove-blocked-by BLOCKER_NUMBER
gh issue edit BLOCKER_NUMBER --repo OWNER/REPO --remove-blocking BLOCKED_NUMBER
```

# repo側copyable assetsの削除

対象repoへコピーしたファイルだけを消す。他の用途へ編集済みの`.github`ファイルは削除しない。

候補:

- `.github/project/views.md`
- `.github/ISSUE_TEMPLATE/feature.yml`
- `.github/ISSUE_TEMPLATE/spike.yml`
- `.github/ISSUE_TEMPLATE/bug.yml`
- `.github/ISSUE_TEMPLATE/config.yml`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`

Git管理下で、このskill導入専用のファイルだと確認できたものだけ削除する。

```bash
git rm .github/project/views.md
```

# destroy: 破壊的な削除

`detach`、`disable`、`hide` で目的を満たせない場合だけ使う。削除前に復元用JSONを作り、対象を再表示し、typed confirmationを通す。

```bash
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

exportファイルを開き、Project owner、title、URL、number、repository、全item数を確認する。確認文字列はProject titleとnumberを含める。

```bash
EXPECTED="OWNER/PROJECT_TITLE#PROJECT_NUMBER"
printf 'destroy confirmation (%s): ' "$EXPECTED"
read -r CONFIRM
test "$CONFIRM" = "$EXPECTED" || exit 1
```

確認後に、依頼された対象だけを削除する。Project itemを削除するとそのitemのcustom field値は失われる。

```bash
gh project item-delete PROJECT_NUMBER --owner OWNER --id PROJECT_ITEM_ID
gh project field-delete --id FIELD_ID
gh api repos/OWNER/REPO/milestones/MILESTONE_NUMBER --method DELETE
gh project delete PROJECT_NUMBER --owner OWNER
```

GitHub既定fieldや他用途のfieldは削除しない。Milestoneは配下Issueが空であることを確認してから削除する。Projectを削除する場合は個別item/field削除を先に行う必要はない。

# 検証

選んだモードに応じて、期待する状態をread-only commandで確認する。

```bash
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 1000
gh issue list --repo OWNER/REPO --state all --limit 1000 \
  --json number,title,state,url,milestone
```

- `detach`: repositoryのlinked Project一覧に対象がない。Projectとitemは残る。
- `disable`: Projectがclosedで、itemは残る。
- `hide`: 対象itemがarchiveされ、unarchive可能である。
- `destroy`: 削除対象が見つからず、export一式が手元に残る。

repo側copyable assetsを削除した場合は差分も確認する。

```bash
git status --short
git diff -- .github
```
