#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 PROJECT_NUMBER PROJECT_OWNER" >&2
  exit 2
fi

PROJECT_NUMBER="$1"
PROJECT_OWNER="$2"

gh project item-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --limit 1000 --format json > /tmp/project-items.json

echo "Items by status:"
jq -r '.items[] | (.status // "No Status")' /tmp/project-items.json | sort | uniq -c | sort -nr

echo
echo "Open issues by agent tier if field is present in item output:"
jq -r '.items[] | select(.content.type == "Issue") | (."Agent Tier" // "No Agent Tier")' /tmp/project-items.json 2>/dev/null | sort | uniq -c | sort -nr || true

echo
echo "Recently updated review/blocker candidates:"
jq -r '.items[] | select((.status // "") == "Blocked" or (.status // "") == "In Review") | [.content.number, .status, .content.title] | @tsv' /tmp/project-items.json 2>/dev/null || true
