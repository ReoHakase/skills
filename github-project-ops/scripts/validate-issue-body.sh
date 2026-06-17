#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 issue-body.md" >&2
  exit 2
fi

FILE="$1"
fail=0

require() {
  local pattern="$1"
  local message="$2"
  if ! grep -Eiq "$pattern" "$FILE"; then
    echo "missing: $message" >&2
    fail=1
  fi
}

require '^# 概要' '概要 section'
require '^# スコープ' 'スコープ section'
require '^# 非スコープ' '非スコープ section'
require '^# 受け入れ条件' '受け入れ条件 section'
require '^# 確認手順' '確認手順 section'
require 'Agent Tier: agent:(fast|standard|frontier)' 'Agent Tier'

if grep -Eiq 'GPT|Claude|Opus|Sonnet|Haiku|Fable|Composer' "$FILE"; then
  echo "warning: issue body contains a concrete model name. Prefer Agent Tier before work starts." >&2
fi

exit "$fail"
