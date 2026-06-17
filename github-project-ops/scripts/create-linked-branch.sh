#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 4 ]; then
  echo "Usage: $0 OWNER/REPO ISSUE_NUMBER BRANCH_NAME BASE_BRANCH" >&2
  exit 2
fi

REPO="$1"
ISSUE_NUMBER="$2"
BRANCH_NAME="$3"
BASE_BRANCH="$4"

gh issue develop "$ISSUE_NUMBER" --repo "$REPO" --name "$BRANCH_NAME" --base "$BASE_BRANCH" --checkout
