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
require '^## Scope' 'Scope section'
require '^## Verification' 'Verification section'
require '^## Risk' 'Risk section'
require '^## Review Focus' 'Review Focus section'

section_has_content() {
  local section="$1"
  local message="$2"
  if ! awk -v section="$section" '
    /^## / {
      in_section = ($0 == section)
      next
    }
    in_section {
      line = $0
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
      if (line != "" && line != "-" && line != "- [ ]") {
        found = 1
      }
    }
    END { exit found ? 0 : 1 }
  ' "$FILE"; then
    echo "placeholder only: $message" >&2
    fail=1
  fi
}

section_has_content '## Summary' 'Summary section'
section_has_content '## Scope' 'Scope section'
section_has_content '## Verification' 'Verification section'
section_has_content '## Risk' 'Risk section'
section_has_content '## Review Focus' 'Review Focus section'

if grep -Eq '^[[:space:]]*-[[:space:]]*(\[ \])?[[:space:]]*$' "$FILE"; then
  echo "placeholder bullet remains in PR body" >&2
  fail=1
fi

if awk '
  /^## / {
    in_verification = ($0 == "## Verification")
    next
  }
  in_verification {
    line = $0
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
    if (line ~ /^-?[[:space:]]*(done|Done|DONE|確認済み|済)$/) {
      found = 1
    }
  }
  END { exit found ? 0 : 1 }
' "$FILE"; then
  echo "verification must contain concrete steps, not only done/確認済み" >&2
  fail=1
fi

if grep -Eiq 'GPT|Claude|Opus|Sonnet|Haiku|Fable|Composer|Agent Model Used|AI Model Used' "$FILE"; then
  echo "model name must not be written in PR body. Use Project fields Agent Harness and Agent Model." >&2
  fail=1
fi

exit "$fail"
