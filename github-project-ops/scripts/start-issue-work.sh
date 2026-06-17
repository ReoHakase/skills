#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 7 ]; then
  cat >&2 <<'USAGE'
Usage: start-issue-work.sh OWNER/REPO ISSUE_NUMBER HUMAN_ASSIGNEE AGENT_TIER AGENT_HARNESS AGENT_MODEL BRANCH_NAME [BASE_BRANCH] [PROJECT_NUMBER] [PROJECT_OWNER]

Example:
  start-issue-work.sh OWNER/REPO 123 reohakuta agent:standard Codex 'GPT 5.5 (xhigh)' 123/feat-ui-search-cards main 1 @me
USAGE
  exit 2
fi

REPO="$1"
ISSUE_NUMBER="$2"
HUMAN_ASSIGNEE="$3"
AGENT_TIER="$4"
AGENT_HARNESS="$5"
AGENT_MODEL="$6"
BRANCH_NAME="$7"
BASE_BRANCH="${8:-main}"
PROJECT_NUMBER="${9:-}"
PROJECT_OWNER="${10:-}"

gh issue edit "$ISSUE_NUMBER" --repo "$REPO" --add-assignee "$HUMAN_ASSIGNEE"

gh issue comment "$ISSUE_NUMBER" --repo "$REPO" --body "$(cat <<EOF
作業開始。

- Assignee: @$HUMAN_ASSIGNEE
- Agent Tier: $AGENT_TIER
- Agent Harness: $AGENT_HARNESS
- Branch: $BRANCH_NAME

Agent ModelはProject fieldに記録する。Issue本文とPR本文には書かない。
EOF
)"

gh issue develop "$ISSUE_NUMBER" --repo "$REPO" --name "$BRANCH_NAME" --base "$BASE_BRANCH" --checkout

if [ -n "$PROJECT_NUMBER" ] && [ -n "$PROJECT_OWNER" ]; then
  ISSUE_URL=$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json url --jq '.url')
  SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
  "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$ISSUE_URL" "Status" "In Progress"
  "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$ISSUE_URL" "Agent Tier" "$AGENT_TIER"
  "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$ISSUE_URL" "Agent Harness" "$AGENT_HARNESS"
  "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$ISSUE_URL" "Agent Model" "$AGENT_MODEL"
  "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$ISSUE_URL" "Reviewer Owner" "$HUMAN_ASSIGNEE"
  "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$ISSUE_URL" "Branch" "$BRANCH_NAME"
  "$SCRIPT_DIR/set-project-field-by-url.sh" "$PROJECT_NUMBER" "$PROJECT_OWNER" "$ISSUE_URL" "Started At" "$(date +%F)" || true
else
  cat <<EOF
Project fieldsを手動で設定してください。
  - Status = In Progress
  - Agent Tier = $AGENT_TIER
  - Agent Harness = $AGENT_HARNESS
  - Agent Model = <concrete model with effort in parentheses>
  - Reviewer Owner = $HUMAN_ASSIGNEE
  - Branch = $BRANCH_NAME
EOF
fi
