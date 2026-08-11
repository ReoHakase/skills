# 初期設定と認証

正常系が依存コマンド、ブラウザ、認証で停止した場合だけ読む。

## 依存コマンドとブラウザ

```bash
command -v bun
command -v gh
bunx @playwright/cli --help >/dev/null
gh --version
```

不足分だけ導入する。この skill から `package.json` や lockfile を変更しない。

通常、ブラウザは最初の `open` で自動導入される。事前導入する場合、または自動導入が失敗した場合だけ実行する。

```bash
bunx @playwright/cli install-browser
```

同じ OS、ユーザー、永続ファイルシステム、Playwright 対応ブラウザ版、キャッシュであれば通常1回でよい。CLI 更新、キャッシュ削除、別端末、別コンテナ、一時ランナーでは再導入が必要になり得る。毎回実行しない。

## `gh` の認証

```bash
HOST=${TARGET_URL#https://}; HOST=${HOST%%/*}
gh auth status --hostname "$HOST"
gh auth login --web --hostname "$HOST"
```

自動実行では token をコマンド引数へ書かない。`github.com` と `ghe.com` のサブドメインでは `GH_TOKEN`、GitHub Enterprise Server では `GH_ENTERPRISE_TOKEN` を使う。

非公開リポジトリ用の fine-grained PAT は対象リポジトリだけを選び、少なくとも次を許可する。

- `Issues: Read and write`
- `Pull requests: Read and write`

classic PAT が必要な場合は `repo` scope を使う。SAML SSO を使う組織では token を対象組織へ認可する。承認待ちなら続行しない。`gh auth status --show-token` と `--insecure-storage` は使わない。

## Playwright ブラウザのログイン

`gh` とブラウザの認証は独立している。対象ホストごとに persistent profile（永続プロファイル）を使う。

```bash
HOST=${TARGET_URL#https://}; HOST=${HOST%%/*}
SESSION="github-attach-${HOST//[^[:alnum:]]/-}"
bunx @playwright/cli -s="$SESSION" close >/dev/null 2>&1 || true
bunx @playwright/cli -s="$SESSION" open "$TARGET_URL" --persistent --headed
```

開いたブラウザでユーザー本人が GitHub ログイン、MFA、SAML SSO を完了する。パスワード、ワンタイムコード、リカバリーコードを Codex に入力させない。ブラウザ側のアカウントに対象リポジトリへの書き込み権限があることを確認する。

ログイン後はブラウザを閉じても、同じセッション名で永続プロファイルを再利用できる。通常の Chrome profile を `--profile` で使い回さない。認証情報の削除をユーザーが明示した場合だけ実行する。

```bash
bunx @playwright/cli -s="$SESSION" delete-data
```
