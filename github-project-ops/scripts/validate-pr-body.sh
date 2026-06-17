#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 pr-body.md" >&2
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

require '^## Summary' 'Summary section'
require '^## Linked Issue' 'Linked Issue section'
require '(Closes|Fixes|Resolves) #[0-9]+' 'closing keyword'
require '^## Verification' 'Verification section'
require '^## Risk' 'Risk section'
require '^## Review Focus' 'Review Focus section'

if grep -Eiq 'GPT|Claude|Opus|Sonnet|Haiku|Fable|Composer|Agent Model Used|AI Model Used' "$FILE"; then
  echo "model name must not be written in PR body. Use Project fields Agent Harness and Agent Model." >&2
  fail=1
fi

exit "$fail"
