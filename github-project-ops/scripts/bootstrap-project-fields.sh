#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 PROJECT_NUMBER PROJECT_OWNER project-fields.json" >&2
  echo "Example: $0 1 @me examples/project-fields.json" >&2
  exit 2
fi

PROJECT_NUMBER="$1"
PROJECT_OWNER="$2"
FIELDS_JSON="$3"

existing=$(gh project field-list "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --format json)

jq -c '.[]' "$FIELDS_JSON" | while read -r field; do
  name=$(jq -r '.name' <<<"$field")
  type=$(jq -r '.type' <<<"$field")

  if jq -e --arg name "$name" '.fields[] | select(.name == $name)' <<<"$existing" >/dev/null; then
    echo "field exists: $name"
    continue
  fi

  if [ "$type" = "SINGLE_SELECT" ]; then
    mapfile -t options < <(jq -r '.options[]' <<<"$field")
    args=(gh project field-create "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --name "$name" --data-type SINGLE_SELECT)
    for opt in "${options[@]}"; do
      args+=(--single-select-option "$opt")
    done
    "${args[@]}"
  else
    gh project field-create "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --name "$name" --data-type "$type"
  fi
  echo "created field: $name"
done
