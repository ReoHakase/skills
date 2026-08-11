---
name: github-issue-pr-image-attach
description: GitHub Issue／PR の本文・コメントへ画像・動画・ファイルを添付する。bunx @playwright/cli で URL を取得し、gh issue／pr で反映する。サイズ検査と圧縮案内に対応。行レビューは対象外。
---

# GitHub Issue／PR への画像添付

画像・動画・ファイルを対象にする。大きいファイルは [圧縮とサイズ確認](references/compression.md) を先に読む。

## 規則

- Playwright CLI は画像アップロードと `user-attachments` URL の取得だけに使う。ブラウザでは投稿、保存、更新をしない。
- 反映には `gh issue` または `gh pr` を使う。内部アップロード API、upload policy、`curl` は使わない。
- token、Cookie、storage state、既存本文を出力しない。正常系では `--raw` を使い、snapshot を読まない。
- URL 取得後に `gh` が失敗しても再アップロードせず、取得済み URL を再利用する。
- 対象は本文またはトップレベルコメントだけである。PR の行レビューコメントには使わない。

## 入力

- `KIND`: `issue` または `pr`
- `TARGET`: URL、番号、ブランチ名。現在のブランチの PR では省略可
- `DEST`: `body` または `comment`。既定値は `body`
- 画像・動画・ファイルのパスと1行のキャプション。省略時は `添付ファイル 1` などを使う

## サイズ・形式・タイムアウト

- `scripts/upload-url.sh` はブラウザを開く前に MIME とサイズを検査する。既定上限は画像 10 MB、動画 10 MB、その他 25 MB。
- 有料プランで動画 100 MB が許可される場合だけ `GITHUB_VIDEO_MAX_MB=100` を指定する。上限超過や MP4／MOV／WebM 以外の動画はアップロードしない。
- URL 待ちは `GITHUB_ATTACHMENT_TIMEOUT_SECONDS`（既定 120 秒）。Playwright のアップロード失敗は握りつぶさず終了する。
- 動画・その他のファイルは画像構文ではなく `[キャプション](URL)` として本文へ追記する。

## 手順

以下を同じ Bash 実行内で行う。

```bash
set -euo pipefail
umask 077
export GH_NO_UPDATE_NOTIFIER=1
DEST=${DEST:-body}

if [[ $KIND == pr && -z ${TARGET:-} ]]; then
  TARGET_URL=$(gh pr view --json url --jq .url)
else
  TARGET_URL=$(gh "$KIND" view "$TARGET" --json url --jq .url)
fi
```

失敗時はアップロードせず、[初期設定と認証](references/setup-auth.md) を読む。

`SKILL_DIR` をこの skill ディレクトリの絶対パスにする。失敗時に URL を再利用できるよう、一時ファイルは成功確認まで残す。

```bash
WORK=$(mktemp -d)
MD=$WORK/attachments.md
printf 'recovery directory: %s\n' "$WORK" >&2
```

画像ごとに次を繰り返す。`ALT` の改行は空白にし、Markdown 上の `\` と `]` をエスケープする。

```bash
URL=$("$SKILL_DIR/scripts/upload-url.sh" "$TARGET_URL" "$IMAGE")
case "$IMAGE" in
  *.png|*.PNG|*.gif|*.GIF|*.jpg|*.JPG|*.jpeg|*.JPEG|*.svg|*.SVG|*.webp|*.WEBP|*.bmp|*.BMP|*.tif|*.TIF|*.tiff|*.TIFF)
    printf '![%s](%s)\n\n' "$ALT" "$URL" >>"$MD"
    ;;
  *)
    printf '[%s](%s)\n\n' "$ALT" "$URL" >>"$MD"
    ;;
esac
```

スクリプトの標準出力は添付 URL 1行だけでなければならない。失敗時だけ [障害対応](references/troubleshooting.md) を読む。

本文末尾へ追記する場合は、更新直前に最新本文を取得する。

```bash
BODY=$WORK/body.md
gh "$KIND" view "$TARGET_URL" --json body --template '{{.body}}' >"$BODY"
grep -q '[^[:space:]]' "$BODY" && printf '\n\n' >>"$BODY" || true
cat "$MD" >>"$BODY"
gh "$KIND" edit "$TARGET_URL" --body-file "$BODY"
```

トップレベルコメントを作る場合は次を使う。

```bash
gh "$KIND" comment "$TARGET_URL" --body-file "$MD"
```

反映後、本文または作成コメントに `attachments.md` の全 URL があることを確認する。成功後だけ `rm -rf "$WORK"` を実行する。報告は対象 URL、反映先、添付 URL のみにする。

## 条件付き reference

- コマンド／ブラウザ不足、初回ログイン、`gh` 認証、非公開リポジトリ、MFA、SAML SSO、GHES: [初期設定と認証](references/setup-auth.md)
- 投稿入力欄の不検出、サイズ超過、404、ロック、タイムアウト、ファイルアクセス、`gh` 再試行、セッション異常: [障害対応](references/troubleshooting.md)
