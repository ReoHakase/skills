# リポジトリ作業規約

## 配置

- スキルはリポジトリ直下の `<skill-name>/SKILL.md` に置く。
- スキル固有の参照資料は、そのスキルの `references/` ディレクトリに置く。
- コピーして使うテンプレートや補助アセットは、そのスキルの `assets/` ディレクトリに置く。

## 整形と確認

- Node系ツールはBunを使う。
- Markdown、YAML、JSON、TOML、TypeScriptの整形は `bun run format` で `oxfmt` を実行する。
- Python以外の整形確認だけが必要な場合は、レビュー前に `bun run format:check` を使う。
- TypeScriptの型確認は `bun run typecheck` を使う。
- Bun管理の確認は `bun run check` を使う。
- `package.json` にuvコマンドを入れない。Pythonの確認はuvで直接実行する。
- Pythonのlintは `uv run ruff check .` を使う。
- Pythonファイルの整形は `uv run ruff format .` を使う。
- Python整形の確認は `uv run ruff format --check .` を使う。
- Pythonの型確認は `uv run ty check .` を使う。
- Pythonテストは `uv run pytest` を使う。

## Python用アセット

- Pythonツールは `pyproject.toml` でuv管理する。
- スキルの `assets/` ディレクトリにあるPythonスクリプトは、pytestが安全に読み込めるよう、読み込み時の副作用を少なく保つ。
- `assets/` ディレクトリ配下の非テスト `*.py` ファイルには、同じディレクトリに対応するpytestファイルを置く。
- 対応するテストファイル名は `test_<asset_stem>.py` にする。アセット名にハイフンがある場合はアンダースコアへ置き換える。
- アセットのテストは、実GitHub、ネットワーク、シェル副作用を必須にしない。純粋な補助関数は直接テストし、subprocessを呼ぶ処理は必要に応じてモックする。
