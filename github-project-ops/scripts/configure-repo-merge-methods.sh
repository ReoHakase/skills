#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 OWNER/REPO" >&2
  exit 2
fi

REPO="$1"

gh api -X PATCH "repos/$REPO" \
  -F allow_merge_commit=true \
  -F allow_squash_merge=false \
  -F allow_rebase_merge=false \
  -F allow_auto_merge=true \
  -F delete_branch_on_merge=true \
  --jq '{allow_merge_commit, allow_squash_merge, allow_rebase_merge, allow_auto_merge, delete_branch_on_merge}'

cat <<'EOF'
Repository merge methods configured.

Next manual/ruleset step:
  - Protect main.
  - Require pull request reviews.
  - Require status checks.
  - Require merge queue.
  - Do not enable Require linear history.
  - Set merge queue merge method to merge.
  - Set maximum group size as desired, e.g. 100.
EOF
