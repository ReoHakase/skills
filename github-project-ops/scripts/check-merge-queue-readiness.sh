#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 OWNER/REPO" >&2
  exit 2
fi

REPO="$1"

echo "Repository merge settings:"
gh api "repos/$REPO" --jq '{allow_merge_commit, allow_squash_merge, allow_rebase_merge, allow_auto_merge, default_branch}'

echo
echo "Rulesets:"
gh ruleset list --repo "$REPO" || true

echo
echo "Workflow files mentioning merge_group:"
gh api "repos/$REPO/contents/.github/workflows" --jq '.[].path' 2>/dev/null | while read -r path; do
  if gh api "repos/$REPO/contents/$path" --jq '.content' 2>/dev/null | base64 --decode | grep -q 'merge_group'; then
    echo "  $path"
  fi
done || true

cat <<'EOF'
Checklist:
  [ ] allow_merge_commit = true
  [ ] allow_squash_merge = false for standard operation
  [ ] allow_rebase_merge = false for standard operation
  [ ] allow_auto_merge = true
  [ ] main is protected by branch protection or ruleset
  [ ] Require merge queue is enabled
  [ ] Require linear history is disabled
  [ ] Required CI workflows run on pull_request and merge_group
EOF
