# Project API読取と選択肢更新

`gh project`だけでは全ページ、選択肢の色・説明、ビュー、Projectアイテムの全項目値を厳密に確認できない場合に読む。通常の変更は高水準コマンドを優先し、この資料のGraphQLとREST APIは不足する読取・更新だけに使う。

# ページング

各接続は最初に`after`を渡さず取得する。`pageInfo.hasNextPage`が`true`なら、返された`endCursor`を次の`-F after=END_CURSOR`へ渡す。`false`になるまで同じ問い合わせを繰り返す。

ページは`/tmp`へ分けて保存し、最後に次を確認する。

```bash
jq -s -e '
  (last | .data.node.fields.pageInfo.hasNextPage) == false and
  (.[0].data.node.fields.totalCount ==
    ([.[].data.node.fields.nodes[]] | length))
' /tmp/project-fields-page-*.json >/dev/null
```

取得途中で401、403、空の`node`、同じ`endCursor`の反復、欠落ページがあれば停止する。ページを連結した後にだけ差分判定する。

# リポジトリとProjectの紐付け

最初のページ:

```bash
gh api graphql \
  -f owner='OWNER' \
  -f repo='REPO' \
  -f query='
query($owner: String!, $repo: String!, $after: String) {
  repository(owner: $owner, name: $repo) {
    id
    nameWithOwner
    projectsV2(first: 100, after: $after) {
      totalCount
      nodes { id number title url }
      pageInfo { hasNextPage endCursor }
    }
  }
}'
```

2ページ目以降は同じコマンドへ`-F after=END_CURSOR`を追加する。全ページ連結後、対象Project IDが正確に1件あることを確認する。

```bash
jq -s -e --arg project_id 'PROJECT_ID' '
  ([.[].data.repository.projectsV2.nodes[] |
    select(.id == $project_id)] | length) == 1 and
  (last | .data.repository.projectsV2.pageInfo.hasNextPage) == false and
  (.[0].data.repository.projectsV2.totalCount ==
    ([.[].data.repository.projectsV2.nodes[]] | length))
' /tmp/repository-projects-page-*.json >/dev/null
```

# Projectフィールド

```bash
gh api graphql \
  -F projectId='PROJECT_ID' \
  -f query='
query($projectId: ID!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      fields(first: 100, after: $after) {
        totalCount
        nodes {
          __typename
          ... on ProjectV2Field { id name dataType }
          ... on ProjectV2SingleSelectField {
            id
            name
            dataType
            options { id name color description }
          }
          ... on ProjectV2IterationField { id name dataType }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}'
```

2ページ目以降は`-F after=END_CURSOR`を追加する。全ページを次の形へ正規化する。

```bash
jq -s '
  [.[].data.node.fields.nodes[] |
    select(.name != null and .dataType != null) |
    {
      id,
      name,
      type: .dataType,
      options: ((.options // []) |
        map({id, name, color, description}))
    }
  ] | sort_by(.name)
' /tmp/project-fields-page-*.json
```

`totalCount`と連結後の件数を一致させる。同名フィールドが複数ある場合、型が異なる場合、単一選択肢のIDを取得できない場合は停止する。

# Projectアイテムと全項目値

Projectアイテムと項目値は別々にページングする。Projectアイテムのページ:

```bash
gh api graphql \
  -F projectId='PROJECT_ID' \
  -f query='
query($projectId: ID!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      items(first: 100, after: $after) {
        totalCount
        nodes {
          id
          type
          isArchived
          content {
            __typename
            ... on Issue {
              id
              number
              url
              repository { nameWithOwner }
            }
            ... on PullRequest { id number url }
            ... on DraftIssue { id title }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}'
```

Projectアイテムの2ページ目以降は`-F after=END_CURSOR`を追加する。全ページを連結し、`totalCount`と件数を一致させる。計画対象のIssue URLが正確に1件あり、`type`が`ISSUE`で、`isArchived`が`false`であることを確認する。

次に、計画対象の各ProjectアイテムIDについて項目値を取得する。

```bash
gh api graphql \
  -F itemId='PROJECT_ITEM_ID' \
  -f query='
query($itemId: ID!, $after: String) {
  node(id: $itemId) {
    ... on ProjectV2Item {
      id
      fieldValues(first: 100, after: $after) {
        totalCount
        nodes {
          __typename
          ... on ProjectV2ItemFieldSingleSelectValue {
            name
            optionId
            field { ... on ProjectV2SingleSelectField { id name } }
          }
          ... on ProjectV2ItemFieldTextValue {
            text
            field { ... on ProjectV2Field { id name } }
          }
          ... on ProjectV2ItemFieldNumberValue {
            number
            field { ... on ProjectV2Field { id name } }
          }
          ... on ProjectV2ItemFieldDateValue {
            date
            field { ... on ProjectV2Field { id name } }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}'
```

2ページ目以降は`-F after=END_CURSOR`を追加する。1アイテム分の全ページについて、最終ページと件数を検証する。

```bash
jq -s -e '
  (last | .data.node.fieldValues.pageInfo.hasNextPage) == false and
  (.[0].data.node.fieldValues.totalCount ==
    ([.[].data.node.fieldValues.nodes[]] | length)) and
  (([.[].data.node.fieldValues.pageInfo.endCursor | select(. != null)] | length) ==
    ([.[].data.node.fieldValues.pageInfo.endCursor | select(. != null)] |
      unique | length))
' /tmp/project-item-values-PROJECT_ITEM_ID-page-*.json >/dev/null
```

Projectの`field_sources.kind`が`project_field`である項目だけを次の形へ正規化する。組織Issue Fieldは`ProjectV2ItemIssueFieldValue`から推測せず、Issue Field値のREST APIで別に再取得する。Projectの組み込み項目と、今回扱わない型は比較対象から除く。

```bash
jq '[.field_sources[] |
  select(.kind == "project_field") |
  .field_id
]' project-items.json > /tmp/managed-project-field-ids.json

jq -s --slurpfile managed_field_ids /tmp/managed-project-field-ids.json '
  def normalized_value:
    if .__typename == "ProjectV2ItemFieldSingleSelectValue" then .name
    elif .__typename == "ProjectV2ItemFieldTextValue" then .text
    elif .__typename == "ProjectV2ItemFieldNumberValue" then .number
    elif .__typename == "ProjectV2ItemFieldDateValue" then .date
    else null
    end;
  [.[].data.node.fieldValues.nodes[] |
    select(
      .__typename == "ProjectV2ItemFieldSingleSelectValue" or
      .__typename == "ProjectV2ItemFieldTextValue" or
      .__typename == "ProjectV2ItemFieldNumberValue" or
      .__typename == "ProjectV2ItemFieldDateValue"
    ) |
    .field.id as $field_id |
    select(any($managed_field_ids[0][]; . == $field_id)) |
    {key: .field.name, value: normalized_value}
  ] as $entries |
  if any($entries[]; .key == null or .key == "") then
    error("Project項目名を取得できません")
  elif ([$entries[].key] | length) != ([$entries[].key] | unique | length) then
    error("同名のProject項目値が複数あります")
  else
    {
      item_id: .[0].data.node.id,
      fields: ($entries | from_entries)
    }
  end
' /tmp/project-item-values-PROJECT_ITEM_ID-page-*.json
```

正規化後は、計画で`project_field`を選び、非`null`値を指定した全項目名が正確に1件存在し、値が一致することを確認する。計画にないProject独自フィールド値は消さない。

# 組織Issue Fieldの値

`field_sources.kind`が`organization_issue_field`の値は、Issue Field値のREST APIへ渡す。1件のIssueについて、非`null`値だけを入力JSONへ変換する。

```bash
jq --argjson issue_number ISSUE_NUMBER '
  . as $plan |
  ($plan.items[] | select(.issue_number == $issue_number)) as $item |
  [$item.fields | to_entries[] |
    .key as $name |
    .value as $value |
    $plan.field_sources[$name] as $source |
    select($source.kind == "organization_issue_field" and $value != null) |
    {field_id: $source.field_id, value: $value}
  ] as $values |
  if ($values | length) == 0 then
    error("書き込む組織Issue Field値がありません")
  else
    {issue_field_values: $values}
  end
' project-items.json > issue-field-values-ISSUE_NUMBER.json
```

生成した配列が空でないこと、フィールドIDが重複しないこと、対象Issueの現在値との差分を確認する。適用後は全ページを再取得する。

```bash
gh api --paginate --slurp \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "repos/OWNER/REPO/issues/ISSUE_NUMBER/issue-field-values?per_page=100" \
  > /tmp/issue-field-values-ISSUE_NUMBER-pages.json

jq -e '
  [.[][] |
    {
      field_id: .issue_field_id,
      name: .issue_field_name,
      type: .data_type,
      value: (
        if .data_type == "single_select" then
          .single_select_option.name
        else
          .value
        end
      )
    }
  ] as $values |
  ([$values[].field_id] | length) ==
  ([$values[].field_id] | unique | length)
' /tmp/issue-field-values-ISSUE_NUMBER-pages.json >/dev/null
```

正規化した値から、計画で指定した全フィールドIDが正確に1件あり、値が一致することを確認する。TypeはIssue本体の`type`を再取得し、Issue Field値と混ぜない。

# Projectビュー

```bash
gh api graphql \
  -F projectId='PROJECT_ID' \
  -f query='
query($projectId: ID!, $after: String) {
  node(id: $projectId) {
    ... on ProjectV2 {
      views(first: 100, after: $after) {
        totalCount
        nodes { id number name layout filter }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}'
```

2ページ目以降は`-F after=END_CURSOR`を追加する。GraphQLのレイアウト値を、`project-views.json`と同じ値へ正規化する。

```bash
jq -s '
  [.[].data.node.views.nodes[] |
    {
      id,
      number,
      name,
      layout: ({
        BOARD_LAYOUT: "board",
        ROADMAP_LAYOUT: "roadmap",
        TABLE_LAYOUT: "table"
      }[.layout]),
      filter: (.filter // "")
    }
  ] | sort_by(.name)
' /tmp/project-views-page-*.json
```

不明なレイアウトが`null`へ正規化された場合は停止する。ビュー作成直後にも全ページを再取得し、名前、レイアウト、絞り込み条件を検証する。

# 単一選択肢の色と説明を更新する

`gh project field-create`で作成した後、上記のフィールド読取で全選択肢IDを取得する。同名選択肢が正確に1件あり、既存選択肢に削除・改名がないことを確認する。

次は`Estimate Confidence`の3選択肢すべてを保持して更新する例である。実IDへ置き換え、1つでも取得できない場合は実行しない。

```bash
gh api graphql \
  -F fieldId='FIELD_ID' \
  -f query='
mutation($fieldId: ID!) {
  updateProjectV2Field(input: {
    fieldId: $fieldId
    singleSelectOptions: [
      {
        id: "OPTION_EC0_ID"
        name: "ec0-low"
        color: RED
        description: "未知要素が多く、再見積りの可能性が高い。"
      }
      {
        id: "OPTION_EC1_ID"
        name: "ec1-medium"
        color: YELLOW
        description: "作業境界は明確だが、一部に未知要素がある。"
      }
      {
        id: "OPTION_EC2_ID"
        name: "ec2-high"
        color: GREEN
        description: "類似実績、変更範囲、確認手順が揃っている。"
      }
    ]
  }) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        name
        options { id name color description }
      }
    }
  }
}'
```

応答と全フィールドを再取得し、`project-fields.json`の名前、順序、色、説明、既存IDが一致することを確認する。差分が残る場合は次のフィールドへ進まない。
