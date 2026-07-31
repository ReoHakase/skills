# Project運用の解除

GitHub Projectsの運用だけを止めるときに読む。標準は復元しやすい順に`detach`、`disable`、`archive`を選び、復元できない削除は`destroy`に限定する。

# 不変条件

どのモードでも、次の対象は変更も削除もしない。

- IssueとPRの本文、状態、担当者、ラベル、コメント
- Milestoneと割り当て
- sub-issue、blocked by、blocking
- `.github/ISSUE_TEMPLATE/`以下のIssue Forms
- `.github/pull_request_template.md`などのPRテンプレート
- `.github/workflows/`以下のCI設定

解除対象は、Project本体、リポジトリとの紐付け、Projectアイテム、Project独自フィールド、Projectビュー、導入時にコピーした`.github/project/views.md`だけである。Projectアイテムを削除しても、紐付くリポジトリIssueやPRは削除しない。Project内だけに存在する下書きIssueはProjectデータなので、破壊的操作の前に題名と本文を必ず書き出す。

# モード

| モード       | 変更対象                                          | 復元可能性                                       |
| ------------ | ------------------------------------------------- | ------------------------------------------------ |
| `detach`     | リポジトリとProjectの紐付け                       | `gh project link`で復元できる                    |
| `disable`    | Projectの開閉状態                                 | `gh project close --undo`で復元できる            |
| `archive`    | 指定したProjectアイテムのアーカイブ状態           | `gh project item-archive --undo`で復元できる     |
| `remove-doc` | `.github/project/views.md`                        | Git履歴または退避ファイルから復元できる          |
| `destroy`    | 指定したアイテム、独自フィールド、ビュー、Project | 書き出しを使った手動再構築だけ。IDは元に戻らない |

運用停止だけなら`disable`を標準とする。一覧から一部を隠すだけなら`archive`、リポジトリから入口だけを外すなら`detach`を使う。`destroy`は他のモードで目的を満たせない場合だけ選ぶ。

# 共通の事前確認

GitHub MCPで対象を探索できる場合は先に使い、変更前の正確な識別子を得る。変更と最終確認は`gh`で行う。推測した所有者、Project番号、Project ID、アイテムID、フィールドID、ビュー番号を使わない。

```bash
gh repo view OWNER/REPO --json id,nameWithOwner,url
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 10000
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 1000
```

Project IDとURLが依頼対象に一致することを確認する。同名Projectが複数ある場合は停止する。

## 全件を書き出す

すべてのモードで、変更前に次を別ディレクトリへ保存する。

```bash
mkdir -p github-project-ops-export
gh project view PROJECT_NUMBER --owner OWNER --format json \
  > github-project-ops-export/project.json
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 10000 \
  > github-project-ops-export/items-cli.json
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 1000 \
  > github-project-ops-export/fields-cli.json
```

紐付くリポジトリはProject IDから全ページを書き出す。2ページ目以降は`-F after=END_CURSOR`を加える。

```bash
gh api graphql \
  -F projectId='PROJECT_ID' \
  -f query='
query($projectId: ID!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      repositories(first: 100, after: $after) {
        totalCount
        nodes { id nameWithOwner url }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}' > github-project-ops-export/repositories-page-1.json
```

`project-api-queries.md`の次の問い合わせも実行し、カーソルごとの応答を保存する。

- 「リポジトリとProjectの紐付け」: 対象リポジトリ側からの照合
- 「Projectフィールド」: 組み込みフィールドとProject独自フィールド
- 「Projectアイテムと全項目値」: 全アイテム、アーカイブ状態、全Project項目値
- 「Projectビュー」: 全ビューのID、番号、名前、レイアウト、絞り込み条件

各接続は`hasNextPage`が`false`になるまで`gh api graphql`を繰り返す。`totalCount`と保存した件数が一致しない場合、上限到達、取得権限不足、未取得ページがある場合は解除しない。CLIの件数もGraphQLの件数と照合する。

リポジトリ側の説明ファイルも退避する。

```bash
test ! -f .github/project/views.md || \
  cp .github/project/views.md github-project-ops-export/views.md
```

書き出し後に、次を記録する。

- Projectの所有者、番号、ID、題名、URL、開閉状態
- 紐付く全リポジトリ
- 全アイテム数と全アイテムID
- 削除対象の独自フィールド名、ID、型、選択肢
- 全ビュー名、ID、番号、レイアウト、絞り込み条件
- Project内だけに存在する下書きIssueの題名と本文

## 確認文字列

書き出しを検査してから、実行するモードに対応する文字列を利用者へ提示し、完全一致を得る。`TARGET_*_COUNT`は今回変更する件数、`TOTAL_*_COUNT`は書き出した全件数である。

```text
OWNER/REPO#PROJECT_NUMBER:PROJECT_ID:detach
OWNER#PROJECT_NUMBER:PROJECT_ID:disable
OWNER#PROJECT_NUMBER:PROJECT_ID:archive:TARGET_ITEM_COUNT
OWNER/REPO:remove-project-views-doc
OWNER#PROJECT_NUMBER:PROJECT_ID:destroy-parts:TARGET_ITEM_COUNT:TARGET_FIELD_COUNT:TARGET_VIEW_COUNT
OWNER#PROJECT_NUMBER:PROJECT_ID:destroy-project:TOTAL_ITEM_COUNT:TOTAL_FIELD_COUNT:TOTAL_VIEW_COUNT
```

確認文字列を得る前に変更しない。対象や件数が変わった場合は再取得し、新しい文字列で確認し直す。

# `detach`: リポジトリとの紐付けを外す

1つのリポジトリ紐付けだけを外す。Project、アイテム、フィールド、ビューは残す。

```bash
gh project unlink PROJECT_NUMBER --owner OWNER --repo OWNER/REPO
```

直後に`project-api-queries.md`の「リポジトリとProjectの紐付け」を全ページ再取得し、対象Project IDが0件、他のProject紐付けが変更前と同じであることを確認する。Project本体と全アイテムも再取得し、件数とIDが変わっていないことを確認する。

復元:

```bash
gh project link PROJECT_NUMBER --owner OWNER --repo OWNER/REPO
```

復元後も同じ問い合わせを行い、対象Project IDが正確に1件あることを確認する。

# `disable`: Projectを閉じる

Projectを履歴として残したまま通常運用から外す。紐付け、アイテム、フィールド、ビューは残す。

```bash
gh project close PROJECT_NUMBER --owner OWNER
```

直後に再取得する。

```bash
gh project view PROJECT_NUMBER --owner OWNER --format json
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 10000
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 1000
```

Projectが閉じており、Project ID、全アイテムID、独自フィールドID、ビューID、リポジトリ紐付けが変更前と一致することを確認する。

復元:

```bash
gh project close PROJECT_NUMBER --owner OWNER --undo
```

再取得し、Projectが開いており、他の情報が変わっていないことを確認する。

# `archive`: Projectアイテムをアーカイブする

書き出した対象アイテムIDを1件ずつ明示して実行する。一括変更用スクリプトは作らない。

```bash
gh project item-archive PROJECT_NUMBER --owner OWNER --id PROJECT_ITEM_ID
```

各操作の直後に「Projectアイテムと全項目値」を再取得し、対象の`isArchived`だけが`true`になり、内容IDとProject項目値が保持されていることを確認してから次へ進む。リポジトリIssueやPRは閲覧だけに留め、変更しない。

復元:

```bash
gh project item-archive PROJECT_NUMBER --owner OWNER --id PROJECT_ITEM_ID --undo
```

復元後に`isArchived`が`false`、内容IDとProject項目値が変更前と一致することを確認する。

# `remove-doc`: リポジトリ側の説明だけを外す

対象リポジトリへ、このスキルのProject運用説明としてコピーした`.github/project/views.md`だと確認できる場合だけ削除する。他の`.github`ファイルは対象にしない。

```bash
git diff -- .github/project/views.md
git rm -- .github/project/views.md
git diff --cached -- .github/project/views.md
```

差分に他のパスが含まれず、Issue Forms、PRテンプレート、CI設定が残っていることを確認する。GitHub上へ反映するかどうかは通常のリポジトリ変更手順で別に判断する。

復元は削除を含むコミットをrevertするか、退避した`github-project-ops-export/views.md`を同じパスへ戻す。ファイルに利用者の追記がある場合は、削除せずProject運用部分だけを別途整理する。

# `destroy`: Projectデータを削除する

`destroy`は復元不能である。削除対象を全件書き出し、確認文字列が一致し、個別のID一覧が確定した場合だけ進む。実行中に失敗しても自動で巻き戻さず、成功済みIDと未実行IDを記録して再取得する。

## アイテムを削除する

Projectからだけ外す。紐付くリポジトリIssueやPRには操作しない。

```bash
gh project item-delete PROJECT_NUMBER --owner OWNER --id PROJECT_ITEM_ID
```

1件ごとに全アイテムを再取得し、対象アイテムIDが0件、他のアイテムIDと値が変更前どおりであることを確認する。Project内だけの下書きIssueはこの操作で失われるため、題名と本文の書き出しなしに削除しない。

## Project独自フィールドを削除する

組み込みフィールド、組織Issue Type、組織Issue Fieldは対象外とする。全アイテムから対象フィールドの値を先に書き出し、Project独自フィールドIDを1件ずつ指定する。

```bash
gh project field-delete --id FIELD_ID
```

1件ごとに全フィールドと全アイテム値を再取得し、対象フィールドIDだけが消え、他のフィールドと値が変わっていないことを確認する。

## ビューを削除する

組織所有Projectでは、書き出したビュー番号を1件ずつ指定する。

```bash
gh api --method DELETE \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "orgs/ORG/projectsV2/PROJECT_NUMBER/views/VIEW_NUMBER"
```

個人所有Projectでは数値の利用者IDを確認してから実行する。

```bash
gh api users/USER --jq .id
gh api --method DELETE \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "users/USER_ID/projectsV2/PROJECT_NUMBER/views/VIEW_NUMBER"
```

1件ごとに「Projectビュー」を全ページ再取得し、対象ビューIDが0件、他のビューIDと設定が変更前どおりであることを確認する。

## Project本体を削除する

Project本体を削除すると、配下のアイテム、独自フィールド、ビューも失われる。Project全体の廃棄が目的なら、個別削除を重ねず、全件書き出し後に本体だけを削除する。

```bash
gh project delete PROJECT_NUMBER --owner OWNER
```

直後に次を確認する。

```bash
gh project view PROJECT_NUMBER --owner OWNER --format json
```

このコマンドが「対象Projectなし」として失敗することを確認する。さらに、紐付いていた各リポジトリのProject一覧を全ページ再取得し、対象Project IDが0件であることを確認する。リポジトリIssue、PR、Milestone、sub-issue、blocked byは変更前の読取結果と一致し、Issue Forms、PRテンプレート、CI設定に差分がないことも確認する。

## `destroy`後の復元可能性

- 削除したアイテムは、元のIssueまたはPRのURLを`gh project item-add`で追加し直し、書き出した値を`gh project item-edit`で再設定する。新しいProjectアイテムIDになる。
- 削除した下書きIssueは、書き出した題名と本文から`gh project item-create`で作り直す。新しいIDになる。
- 削除した独自フィールドは`gh project field-create`で作り直し、選択肢と全アイテム値を再設定する。フィールドIDと選択肢IDは新しくなる。
- 削除したビューは書き出した名前、レイアウト、絞り込み条件をREST APIの作成操作で再作成する。ビューIDと番号は新しくなる。
- 削除したProjectは`gh project create`で新規作成し、紐付け、フィールド、アイテム、値、ビューの順に再構築する。元のProject IDと番号へは戻せない。

復元後は代表例だけで済ませず、書き出した全リポジトリ紐付け、全アイテム、全Project項目値、全独自フィールド、全ビューを再取得して比較する。未確認項目が1件でもあれば復元完了にしない。
