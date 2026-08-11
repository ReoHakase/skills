# 障害対応

## サイズ超過または動画形式エラー

スクリプトはアップロード前に MIME とサイズを検査する。画像は 10 MB、動画は既定 10 MB、その他は 25 MB。
有料プランの動画上限を使う場合だけ `GITHUB_VIDEO_MAX_MB=100` を指定する。圧縮方法は
[圧縮とサイズ確認](compression.md) を参照する。

対応動画形式は MP4、MOV、WebM。MKV などは、ffmpeg で MP4 に変換してから再実行する。

## タイムアウトまたはアップロード失敗

URL 待ちの既定値は 120 秒で、`GITHUB_ATTACHMENT_TIMEOUT_SECONDS` で変更できる。Playwright の
アップロードコマンドが失敗した場合は即時終了する。タイムアウト後に同じ画像を無条件で再アップロードせず、
最後の textarea に URL または失敗文がないか確認する。

`scripts/upload-url.sh` または `gh` が失敗した場合だけ読む。

## ログイン画面または非公開リポジトリの 404

`gh` とブラウザは別認証である。[初期設定と認証](setup-auth.md) に従い、同じセッションを `--headed` で開いてログインする。ブラウザ側のアカウント、リポジトリ権限、組織の SSO、GHES ホストを確認する。

## 投稿入力欄が `missing` または `dirty`

- `missing`: ログイン切れ、Issue／PR のロック、書き込み権限不足、ページ読込み失敗を確認する。
- `dirty`: 専用セッションに未送信文がある。破棄せず、ユーザーが処理してから再実行する。

ブラウザで投稿して回避しない。

## 添付ボタンが見つからない

同じ `SESSION` で、まず局所検索する。

```bash
bunx @playwright/cli -s="$SESSION" find "Paste, drop, or click to add files"
```

見つからない場合だけ浅い snapshot（ページ構造の要約）を取る。

```bash
bunx @playwright/cli -s="$SESSION" snapshot --depth=5
```

得た ref で `click REF` を実行し、続けてワークスペース配下へ一時コピーした画像を `upload IMAGE` する。ページ遷移後に古い ref を再利用しない。

## URL のタイムアウトまたはファイルアクセスエラー

最後の表示中 textarea だけを確認する。

```bash
bunx @playwright/cli -s="$SESSION" --raw eval '([...document.querySelectorAll("textarea")].filter(e=>e.getClientRects().length).at(-1)?.value)||""'
```

`Uploading`、失敗文、空文字を確認する。アップロードの再試行は1回までとし、取得済み URL がある画像は再アップロードしない。画像はワークスペース配下へ一時コピーし、無制限ファイルアクセスは有効にしない。

## `gh` 失敗後の再開

エラー時に表示された recovery directory の `attachments.md` を使い、Playwright を再実行せず `gh` だけを再試行する。`body.md` は既存本文を含むため削除し、本文は必ず取り直す。

- 本文: 最新本文を再取得し、既存 URL を確認してから未反映分だけ追記する。
- コメント投稿は冪等ではない。成否不明なら直近の自分のコメントを確認し、URL がない場合だけ再投稿する。

## セッション異常

```bash
bunx @playwright/cli list
bunx @playwright/cli -s="$SESSION" close
```

通常の `close` で直らない zombie process（終了不能な残留プロセス）に限り `kill-all` を使う。`delete-data` は認証情報削除をユーザーが明示した場合だけ使う。
