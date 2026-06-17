#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 6 ]; then
  cat >&2 <<'USAGE'
Usage: create-pr-from-issue.sh OWNER/REPO ISSUE_NUMBER HEAD_BRANCH BASE_BRANCH PR_TITLE PR_BODY_FILE [PROJECT_NUMBER] [PROJECT_OWNER] [AGENT_HARNESS] [AGENT_MODEL]

The PR body must not include concrete model names. If project arguments are supplied, Agent Harness and Agent Model are written to Project fields.
USAGE
  exit 2
fi

REPO="$1"
ISSUE_NUMBER="$2"
HEAD_BRANCH="$3"
BASE_BRANCH="$4"
PR_TITLE="$5"
PR_BODY_FILE="$6"
PROJECT_NUMBER="${7:-}"
PROJECT_OWNER="${8:-}"
AGENT_HARNESS="${9:-}"
AGENT_MODEL="${10:-}"

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
"$SCRIPT_DIR/validate-pr-body.sh" "$PR_BODY_FILE"

PR_URL=$(gh pr create --repo "$REPO" --base "$BASE_BRANCH" --head "$HEAD_BRANCH" --title "$PR_TITLE" --body-file "$PR_BODY_FILE")
echo "$PR_URL"

if [ -n "$PROJECT_NUMBER" ] && [ -n "$PROJECT_OWNER" ]; then
  "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$PR_URL" "Status" "In Review" || true
  if [ -n "$AGENT_HARNESS" ]; then
    "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$PR_URL" "Agent Harness" "$AGENT_HARNESS" || true
  fi
  if [ -n "$AGENT_MODEL" ]; then
    "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$PR_URL" "Agent Model" "$AGENT_MODEL" || true
  fi
fi
