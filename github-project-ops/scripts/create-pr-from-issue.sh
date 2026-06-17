#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 5 ]; then
  cat >&2 <<'USAGE'
Usage: create-pr-from-issue.sh OWNER/REPO ISSUE_NUMBER HEAD_BRANCH BASE_BRANCH PR_TITLE [PROJECT_NUMBER] [PROJECT_OWNER] [AGENT_HARNESS] [AGENT_MODEL]

The PR body must not include concrete model names. If project arguments are supplied, Agent Harness and Agent Model are written to Project fields.
USAGE
  exit 2
fi

REPO="$1"
ISSUE_NUMBER="$2"
HEAD_BRANCH="$3"
BASE_BRANCH="$4"
PR_TITLE="$5"
PROJECT_NUMBER="${6:-}"
PROJECT_OWNER="${7:-}"
AGENT_HARNESS="${8:-}"
AGENT_MODEL="${9:-}"

body_file=$(mktemp)
cat > "$body_file" <<EOF
## Summary

-

## Linked Issue

Closes #$ISSUE_NUMBER

## Scope

実装したこと:

-

意図的に扱わないこと:

-

## Verification

- [ ]

## Risk

-

## Review Focus

-
EOF

PR_URL=$(gh pr create --repo "$REPO" --base "$BASE_BRANCH" --head "$HEAD_BRANCH" --title "$PR_TITLE" --body-file "$body_file")
rm -f "$body_file"
echo "$PR_URL"

if [ -n "$PROJECT_NUMBER" ] && [ -n "$PROJECT_OWNER" ]; then
  SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
  "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$PR_URL" "Status" "In Review" || true
  if [ -n "$AGENT_HARNESS" ]; then
    "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$PR_URL" "Agent Harness" "$AGENT_HARNESS" || true
  fi
  if [ -n "$AGENT_MODEL" ]; then
    "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$PR_URL" "Agent Model" "$AGENT_MODEL" || true
  fi
fi
