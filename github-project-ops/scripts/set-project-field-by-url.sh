#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 5 ]; then
  cat >&2 <<'USAGE'
Usage: set-project-field-by-url.sh PROJECT_NUMBER PROJECT_OWNER ITEM_URL FIELD_NAME FIELD_VALUE

Examples:
  set-project-field-by-url.sh 1 @me https://github.com/OWNER/REPO/issues/123 'Agent Model' 'GPT 5.5 (xhigh)'
  set-project-field-by-url.sh 1 @me https://github.com/OWNER/REPO/pull/456 'Agent Harness' Codex
USAGE
  exit 2
fi

PROJECT_NUMBER="$1"
PROJECT_OWNER="$2"
ITEM_URL="$3"
FIELD_NAME="$4"
FIELD_VALUE="$5"

PROJECT_ID=$(gh project view "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --format json --jq '.id')
FIELDS_JSON=$(gh project field-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --limit 100 --format json)
FIELD_JSON=$(jq -c --arg name "$FIELD_NAME" '.fields[] | select(.name == $name)' <<<"$FIELDS_JSON")
if [ -z "$FIELD_JSON" ]; then
  echo "field not found: $FIELD_NAME" >&2
  exit 1
fi
FIELD_ID=$(jq -r '.id' <<<"$FIELD_JSON")
FIELD_TYPE=$(jq -r '.dataType // .type // empty' <<<"$FIELD_JSON")

ITEMS_JSON=$(gh project item-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --limit 1000 --format json)
ITEM_ID=$(jq -r --arg url "$ITEM_URL" '.items[] | select(.content.url == $url) | .id' <<<"$ITEMS_JSON" | head -n1)

if [ -z "$ITEM_ID" ]; then
  ITEM_ID=$(gh project item-add "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --url "$ITEM_URL" --format json --jq '.id')
fi

case "$FIELD_TYPE" in
  SINGLE_SELECT|ProjectV2SingleSelectField)
    OPTION_ID=$(jq -r --arg name "$FIELD_VALUE" '.options[]? | select(.name == $name) | .id' <<<"$FIELD_JSON" | head -n1)
    if [ -z "$OPTION_ID" ]; then
      echo "single select option not found for $FIELD_NAME: $FIELD_VALUE" >&2
      exit 1
    fi
    gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$FIELD_ID" --single-select-option-id "$OPTION_ID" >/dev/null
    ;;
  TEXT|ProjectV2Field)
    gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$FIELD_ID" --text "$FIELD_VALUE" >/dev/null
    ;;
  DATE)
    gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$FIELD_ID" --date "$FIELD_VALUE" >/dev/null
    ;;
  NUMBER)
    gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$FIELD_ID" --number "$FIELD_VALUE" >/dev/null
    ;;
  *)
    # gh field-list may report generic ProjectV2Field for text/number/date. Try text fallback.
    gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" --field-id "$FIELD_ID" --text "$FIELD_VALUE" >/dev/null
    ;;
esac

echo "set $FIELD_NAME = $FIELD_VALUE"
