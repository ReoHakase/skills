# GitHub CLI / MCP recipes

# 認証

Project操作にはproject scopeが必要。

```bash
gh auth refresh -s project
```

# Issue作成

```bash
gh issue create \
  --repo OWNER/REPO \
  --title "検索結果カードで一致シーンの無音プレビューを表示する" \
  --body-file issue.md \
  --label "type:feat" \
  --label "priority:2" \
  --label "agent:standard"
```

# sub-issue作成

新規作成時:

```bash
gh issue create --repo OWNER/REPO --parent 100 --title "子Issue" --body-file issue.md
```

既存Issueを追加:

```bash
gh issue edit 100 --repo OWNER/REPO --add-sub-issue 123
```

# blocked by / blocking

```bash
gh issue create --repo OWNER/REPO --blocked-by 120 --blocking 140 --title "Issue" --body-file issue.md
```

既存Issue:

```bash
gh issue edit 123 --repo OWNER/REPO --add-blocked-by 120

gh issue edit 120 --repo OWNER/REPO --add-blocking 123
```

# linked branch作成

```bash
gh issue develop 123 \
  --repo OWNER/REPO \
  --name "123/feat-ui-search-cards" \
  --base main \
  --checkout
```

# PR作成

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

# auto-merge

merge queue運用では、条件を満たしたPRにauto-mergeを有効化する。

```bash
gh pr merge 123 --repo OWNER/REPO --auto --merge
```

# GitHub MCPの使い所

MCPは次に使う。

- Issue本文の不足確認。
- Project viewの現状把握。
- 並列化可能なIssueの抽出。
- PR review結果の要約。
- CI失敗原因の整理。

再現可能な操作はscriptまたはgh CLIへ落とす。
