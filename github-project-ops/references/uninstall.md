# Uninstall

Project/Milestoneを剥がすときに読む。標準は可逆優先にする。IssueやPRは閉じず、本文も原則編集しない。

# 目次

- 事前確認
- 可逆な解除
- repo側copyable assetsの削除
- 破壊的な削除
- 検証

# 事前確認

GitHub上の実状態を先に読む。推測したProject number、Project item ID、Milestone numberで削除しない。

```bash
gh repo view OWNER/REPO --json nameWithOwner,url,owner,isPrivate
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 100
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 100
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100
```

Milestoneに属するIssueを読む。

```bash
gh issue list \
  --repo OWNER/REPO \
  --milestone "First Release" \
  --state all \
  --json number,title,state,milestone
```

解除対象のProject item IDとIssue numberを一覧化してから実行する。Issue本文、PR本文、Project fieldへmetadataを複製しない設計なので、剥がしもGitHub metadata中心で完結させる。

# 可逆な解除

ProjectからIssue/PRを外す。これはIssue/PR本体を削除しない。

```bash
gh project item-delete PROJECT_NUMBER --owner OWNER --id PROJECT_ITEM_ID
```

IssueのMilestoneを解除する。これはMilestone本体を削除しない。

```bash
gh issue edit ISSUE_NUMBER --repo OWNER/REPO --remove-milestone
```

必要ならsub-issueやdependencyも解除する。Project/Milestoneだけを剥がす場合は、WBS構造を残してよい。

```bash
gh issue edit CHILD_NUMBER --repo OWNER/REPO --remove-parent
gh issue edit PARENT_NUMBER --repo OWNER/REPO --remove-sub-issue CHILD_NUMBER
gh issue edit BLOCKED_NUMBER --repo OWNER/REPO --remove-blocked-by BLOCKER_NUMBER
gh issue edit BLOCKER_NUMBER --repo OWNER/REPO --remove-blocking BLOCKED_NUMBER
```

Project field、Milestone、sub-issue、blocked by / blockingの値をIssue本文へ退避しない。残す必要がある判断理由は、現在有効な内容だけIssue本文へ反映し、履歴はGitHub metadataとコメントで読む。

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

# 破壊的な削除

このセクションは、可逆な解除で足りない場合だけ使う。実行前に対象一覧を出力し、Project itemやMilestoneに残っているIssue/PRがないことを確認する。

Projectを削除する。

```bash
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project delete PROJECT_NUMBER --owner OWNER
```

Milestoneを削除する。先にMilestone配下のIssueが空であることを確認する。

```bash
gh issue list \
  --repo OWNER/REPO \
  --milestone "First Release" \
  --state all \
  --json number,title,state

gh api repos/OWNER/REPO/milestones/MILESTONE_NUMBER --method DELETE
```

Projectを残してfieldだけ消す場合は、field IDを確認してから削除する。GitHub既定fieldや他用途で使うfieldは消さない。

```bash
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 100
gh project field-delete --id FIELD_ID
```

# 検証

Project itemが残っていないことを確認する。

```bash
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 100
```

Milestone割当が残っていないことを確認する。

```bash
gh issue list \
  --repo OWNER/REPO \
  --milestone "First Release" \
  --state all \
  --json number,title,state,milestone
```

repo側copyable assetsを削除した場合は、差分を確認する。

```bash
git status --short
git diff -- .github
```
