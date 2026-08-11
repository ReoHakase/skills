#!/usr/bin/env bash
set -euo pipefail
target=${1:?usage: upload-url.sh TARGET_URL IMAGE}
image=${2:?usage: upload-url.sh TARGET_URL IMAGE}
[[ -f "$image" && -r "$image" && -s "$image" ]] || { echo "image is missing, unreadable, or empty: $image" >&2; exit 2; }
command -v file >/dev/null 2>&1 || { echo "file command is required" >&2; exit 2; }

GITHUB_IMAGE_MAX_MB=${GITHUB_IMAGE_MAX_MB:-10}
GITHUB_VIDEO_MAX_MB=${GITHUB_VIDEO_MAX_MB:-10}
GITHUB_OTHER_MAX_MB=${GITHUB_OTHER_MAX_MB:-25}
GITHUB_ATTACHMENT_TIMEOUT_SECONDS=${GITHUB_ATTACHMENT_TIMEOUT_SECONDS:-120}

positive_integer() {
  [[ $1 =~ ^[1-9][0-9]*$ ]]
}

positive_integer "$GITHUB_IMAGE_MAX_MB" ||
  { echo "GITHUB_IMAGE_MAX_MB must be a positive integer" >&2; exit 2; }
positive_integer "$GITHUB_VIDEO_MAX_MB" ||
  { echo "GITHUB_VIDEO_MAX_MB must be a positive integer" >&2; exit 2; }
positive_integer "$GITHUB_OTHER_MAX_MB" ||
  { echo "GITHUB_OTHER_MAX_MB must be a positive integer" >&2; exit 2; }
positive_integer "$GITHUB_ATTACHMENT_TIMEOUT_SECONDS" ||
  { echo "GITHUB_ATTACHMENT_TIMEOUT_SECONDS must be a positive integer" >&2; exit 2; }

file_size() {
  local size
  if [[ $(uname -s) == Darwin ]]; then
    size=$(stat -f %z "$1" 2>/dev/null) || return 1
  else
    size=$(stat -c %s "$1" 2>/dev/null) || return 1
  fi
  [[ $size =~ ^[0-9]+$ ]] || return 1
  printf '%s' "$size"
}

mime=$(file -b --mime-type "$image" 2>/dev/null) ||
  { echo "could not inspect file type: $image" >&2; exit 2; }
extension=$(printf '%s' "${image##*.}" | tr '[:upper:]' '[:lower:]')
attachment_kind=file
case "$mime" in
  image/*)
    attachment_kind=image
    max_mb=$GITHUB_IMAGE_MAX_MB
    ;;
  video/mp4|video/quicktime|video/webm)
    attachment_kind=video
    max_mb=$GITHUB_VIDEO_MAX_MB
    ;;
  video/*)
    echo "unsupported video format: $mime (use mp4, mov, or webm)" >&2
    exit 2
    ;;
  *)
    case "$extension" in
      mp4|mov|webm)
        attachment_kind=video
        max_mb=$GITHUB_VIDEO_MAX_MB
        ;;
      *)
        max_mb=$GITHUB_OTHER_MAX_MB
        ;;
    esac
    ;;
esac
file_bytes=$(file_size "$image") ||
  { echo "could not inspect file size: $image" >&2; exit 2; }
max_bytes=$((max_mb * 1000 * 1000))
if (( file_bytes > max_bytes )); then
  printf 'file is too large: %s bytes (limit %s MB for %s)\n' \
    "$file_bytes" "$max_mb" "$attachment_kind" >&2
  exit 2
fi

host=${target#https://}; host=${host%%/*}
session="github-attach-${host//[^[:alnum:]]/-}"
pw=(bunx @playwright/cli -s="$session" --raw)
stage=$(mktemp -d "$PWD/.github-attach.XXXXXX")
trap 'rm -rf -- "$stage"' EXIT
file=$stage/${image##*/}
cp -- "$image" "$file"

# `eval` returns JSON-quoted strings even with `--raw`.
eval_string() {
  local value=$1
  if (( ${#value} >= 2 )) && [[ ${value:0:1} == '"' && ${value: -1} == '"' ]]; then
    value=${value:1:${#value}-2}
  fi
  printf '%s' "$value"
}

"${pw[@]}" goto "$target" >/dev/null 2>&1 || "${pw[@]}" open "$target" --persistent >/dev/null
state_raw=$("${pw[@]}" eval '(()=>{const e=[...document.querySelectorAll("textarea")].filter(e=>e.getClientRects().length).at(-1);return !e?"missing":e.value?"dirty":"ready"})()')
state=$(eval_string "$state_raw")
[[ $state == ready ]] || { echo "GitHub composer is $state; read references/troubleshooting.md" >&2; exit 3; }
"${pw[@]}" click "getByRole('button',{name:/(Paste, drop, or click to add files|ファイル.*追加)/i}).last()" >/dev/null
if ! "${pw[@]}" upload "$file" >/dev/null; then
  echo "Playwright file upload failed" >&2
  exit 4
fi

url=
for ((elapsed=0; elapsed<GITHUB_ATTACHMENT_TIMEOUT_SECONDS; elapsed++)); do
  url_raw=$("${pw[@]}" eval '(()=>{const e=[...document.querySelectorAll("textarea")].filter(e=>e.getClientRects().length).at(-1);return(e?.value.match(/https:\/\/[^\s)]+\/user-attachments\/assets\/[A-Za-z0-9._-]+/g)||[]).at(-1)||""})()' 2>/dev/null)
  url=$(eval_string "$url_raw")
  [[ $url == https://*/user-attachments/assets/* ]] && break
  if (( elapsed + 1 < GITHUB_ATTACHMENT_TIMEOUT_SECONDS )); then
    sleep 1
  fi
done
[[ -n $url ]] || { printf 'attachment URL was not produced within %ss; read references/troubleshooting.md\n' "$GITHUB_ATTACHMENT_TIMEOUT_SECONDS" >&2; exit 4; }
"${pw[@]}" eval '(()=>{const e=[...document.querySelectorAll("textarea")].filter(e=>e.getClientRects().length).at(-1);if(!e)return;Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,"value").set.call(e,"");e.dispatchEvent(new Event("input",{bubbles:true}))})()' >/dev/null 2>&1 || true
printf '%s\n' "$url"
