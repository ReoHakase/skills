#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 OWNER/REPO backlog.flat.json [state-dir]" >&2
  exit 2
fi

REPO="$1"
BACKLOG_JSON="$2"
STATE_DIR="${3:-.github/project/state}"
mkdir -p "$STATE_DIR"
MAP_FILE="$STATE_DIR/issue-map.tsv"
: > "$MAP_FILE"

# このscriptでは独自keyを使わない。titleをbootstrap中だけの照合名として使う。
# backlog.flat.json内のtitleは一意でなければならない。
duplicates=$(jq -r '.[].title' "$BACKLOG_JSON" | sort | uniq -d)
if [ -n "$duplicates" ]; then
  echo "Duplicate titles are not allowed in bootstrap input:" >&2
  echo "$duplicates" >&2
  exit 1
fi

count=$(jq length "$BACKLOG_JSON")

for i in $(seq 0 $((count - 1))); do
  issue=$(jq ".[$i]" "$BACKLOG_JSON")
  title=$(jq -r '.title' <<<"$issue")
  body=$(jq -r '.body // ""' <<<"$issue")
  type=$(jq -r '.type // empty' <<<"$issue")

  body_file=$(mktemp)
  {
    echo "# 概要"
    echo
    echo "$body"
    echo
    echo "# Agent指定"
    echo
    echo "Agent Tier: $(jq -r '.agent_tier // "agent:standard"' <<<"$issue")"
  } > "$body_file"

  args=(gh issue create --repo "$REPO" --title "$title" --body-file "$body_file")

  if [ -n "$type" ]; then
    args+=(--type "$type")
  fi

  while IFS= read -r label; do
    [ -n "$label" ] && args+=(--label "$label")
  done < <(jq -r '.labels[]? // empty' <<<"$issue")

  url=$("${args[@]}")
  number=$(basename "$url")
  printf '%s\t%s\t%s\n' "$title" "$number" "$url" >> "$MAP_FILE"
  rm -f "$body_file"
  echo "created #$number $title"
done

lookup_number() {
  local title="$1"
  awk -F '\t' -v t="$title" '$1 == t { print $2 }' "$MAP_FILE"
}

for i in $(seq 0 $((count - 1))); do
  issue=$(jq ".[$i]" "$BACKLOG_JSON")
  title=$(jq -r '.title' <<<"$issue")
  number=$(lookup_number "$title")

  parent_title=$(jq -r '.parent_title // empty' <<<"$issue")
  if [ -n "$parent_title" ]; then
    parent_number=$(lookup_number "$parent_title")
    if [ -z "$parent_number" ]; then
      echo "parent not found for #$number: $parent_title" >&2
      exit 1
    fi
    gh issue edit "$parent_number" --repo "$REPO" --add-sub-issue "$number"
  fi

  mapfile -t blocked_by_titles < <(jq -r '.blocked_by_titles[]? // empty' <<<"$issue")
  for dep_title in "${blocked_by_titles[@]}"; do
    dep_number=$(lookup_number "$dep_title")
    if [ -z "$dep_number" ]; then
      echo "blocked_by not found for #$number: $dep_title" >&2
      exit 1
    fi
    gh issue edit "$number" --repo "$REPO" --add-blocked-by "$dep_number"
  done

  mapfile -t blocking_titles < <(jq -r '.blocking_titles[]? // empty' <<<"$issue")
  for dep_title in "${blocking_titles[@]}"; do
    dep_number=$(lookup_number "$dep_title")
    if [ -z "$dep_number" ]; then
      echo "blocking not found for #$number: $dep_title" >&2
      exit 1
    fi
    gh issue edit "$number" --repo "$REPO" --add-blocking "$dep_number"
  done

done

echo "wrote $MAP_FILE"
