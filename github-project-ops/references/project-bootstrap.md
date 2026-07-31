# Project初期構築と一括割当

Project、フィールド、既存IssueのProjectアイテム、項目値、ビューをまとめて整えるときに読む。GitHubを変更する配布スクリプトは使わず、GitHub MCP、`gh`、`jq`で段階実行する。

# 境界

Issueの分割、本文、Milestone、sub-issue、blocked by / blockingは`github-issue-pr-ops`で先に確定する。この資料は、番号、URL、node IDが確定したIssueをProjectへ割り当てる。これらは読取専用の前提であり、この資料の手順から作成・変更しない。

このスキルで行う順序は次で固定する。

1. Project
2. フィールド
3. Projectアイテム
4. 項目値
5. ビュー

各段階で、探索、変更計画、確認、適用、再取得を完了してから次へ進む。複数段階を1つのスクリプトや`eval`へまとめない。

# 入力

- `assets/project-fields.json`: Projectフィールドと選択肢の定義例
- `assets/project-views.json`: ビュー名、レイアウト、絞り込み条件の定義例
- `assets/project-items.example.json`: 作成済みIssueとProject項目値を結ぶ割当計画例

ページング付きGraphQL読取、正規化、単一選択肢の色・説明更新は`references/project-api-queries.md`を読む。

作業時はJSONを一時領域へ複製し、確認済みの値へ置き換える。リポジトリ内の例を実行記録として上書きしない。一時キーはIssue作成計画との対応にだけ使い、GitHub上の結合にはIssue番号、URL、node IDを使う。タイトルで結合しない。

# 共通の停止条件

次のいずれかがあれば、書き込み前または現在の段階で停止する。

- プレースホルダー、対象不一致、重複、一覧の取得不足
- 401、403、権限不足、所有者や公開範囲の不一致
- 同名異型のフィールド、選択肢の不一致、正本の衝突
- Project内の別組織Issue、PR、Draft Issueなど、採用した正本で表せないアイテム
- Project、フィールド、アイテム、ビューの全ページを取得できない状態
- 計画にない既存値を消す必要がある状態

途中で失敗した場合は自動削除で巻き戻さない。成功済みのProject番号、Project ID、Issue URL、ProjectアイテムID、フィールドIDと、未実行項目を記録し、実状態を再取得して計画からやり直す。

# 段階ごとの適用確認

Project作成以外も、各段階の変更直前に対象、変更件数、変更内容を表示し、次の確認文字列への明示同意を得る。

```text
OWNER/REPO#PROJECT_NUMBER:fields:CHANGE_COUNT
OWNER/REPO#PROJECT_NUMBER:items:ADD_COUNT
OWNER/REPO#PROJECT_NUMBER:values:ITEM_COUNT:VALUE_COUNT
OWNER/REPO#PROJECT_NUMBER:views:CREATE_COUNT
```

フィールドは名前、型、全選択肢、色、説明を示す。アイテムは全Issue番号とURLを示す。項目値はIssueごとに項目名、正本経路、変更前、変更後を示す。ビューは名前、レイアウト、絞り込み条件を示す。確認後も各変更の直前に実状態を再取得し、差分が変わっていれば確認からやり直す。

# 1. ローカル計画を検証する

JSONとして読めることを確認する。

```bash
jq -e . project-fields.json >/dev/null
jq -e . project-views.json >/dev/null
jq -e . project-items.json >/dev/null
```

Projectフィールド定義を検証する。

```bash
jq -e '
  type == "array" and length > 0 and
  ([.[].name] | length) == ([.[].name] | unique | length) and
  all(.[];
    (.name | type == "string" and length > 0) and
    (.type == "TEXT" or .type == "SINGLE_SELECT" or .type == "DATE" or .type == "NUMBER") and
    (if .type == "SINGLE_SELECT" then
       (.options | type == "array" and length > 0) and
       ([.options[].name] | length) == ([.options[].name] | unique | length) and
       all(.options[];
         type == "object" and
         (.name | type == "string" and length > 0) and
         (.description | type == "string" and length > 0) and
         (.color == "GRAY" or .color == "BLUE" or .color == "GREEN" or
          .color == "YELLOW" or .color == "ORANGE" or .color == "RED" or
          .color == "PINK" or .color == "PURPLE")
       )
     else
       (has("options") | not)
     end)
  )
' project-fields.json >/dev/null
```

ビュー定義を検証する。

```bash
jq -e '
  type == "array" and length > 0 and
  ([.[].name] | length) == ([.[].name] | unique | length) and
  all(.[];
    (.name | type == "string" and length > 0) and
    (.layout == "table" or .layout == "board" or .layout == "roadmap") and
    (.filter | type == "string")
  )
' project-views.json >/dev/null
```

割当計画を検証する。

```bash
jq -e --slurpfile definitions project-fields.json '
  .repository as $repository |
  .field_sources as $sources |
  ($definitions[0] | map(.name) | sort) as $definition_names |
  .schema_version == 1 and
  ($repository | test("^[^/]+/[^/]+$")) and
  (.project.owner | type == "string" and length > 0) and
  (.project.number == null or
    (.project.number | type == "number" and . > 0 and floor == .)) and
  (.project.id == null or
    (.project.id | type == "string" and startswith("PVT_"))) and
  (.project.title | type == "string" and length > 0) and
  (.project.visibility == "PUBLIC" or .project.visibility == "PRIVATE") and
  ($sources | type == "object") and
  (($sources | keys | sort) == $definition_names) and
  all($sources | to_entries[];
    .key as $name |
    .value as $source |
    ($source.kind == "project_field" or
     $source.kind == "organization_issue_field" or
     $source.kind == "organization_issue_type") and
    (if $source.kind == "project_field" then
       ($source.field_id == null or
        ($source.field_id | type == "string" and length > 0))
     elif $source.kind == "organization_issue_field" then
       ($source.field_id == null or
        ($source.field_id | type == "number" and . > 0 and floor == .))
     else
       ($name == "Type" and
        ($source.value_map | type == "object" and length > 0))
     end)
  ) and
  ([$sources[] | .field_id? | select(. != null)] | length) ==
  ([$sources[] | .field_id? | select(. != null)] | unique | length) and
  (.items | type == "array" and length > 0) and
  ([.items[].issue_key] | length) == ([.items[].issue_key] | unique | length) and
  ([.items[].issue_number] | length) == ([.items[].issue_number] | unique | length) and
  ([.items[].issue_url] | length) == ([.items[].issue_url] | unique | length) and
  ([.items[].issue_node_id] | length) == ([.items[].issue_node_id] | unique | length) and
  ([.items[].item_id | select(. != null)] | length) ==
  ([.items[].item_id | select(. != null)] | unique | length) and
  all(.items[];
    . as $item |
    ($item.issue_key | test("^[a-z0-9]+(?:-[a-z0-9]+)*$")) and
    ($item.issue_number | type == "number" and . > 0 and floor == .) and
    ($item.issue_url ==
      ("https://github.com/" + $repository + "/issues/" +
       ($item.issue_number | tostring))) and
    ($item.issue_node_id | type == "string" and startswith("I_")) and
    ($item.item_id == null or
      ($item.item_id | type == "string" and startswith("PVTI_"))) and
    ($item.fields | type == "object" and length > 0)
  ) and
  all(.items[].fields | to_entries[];
    . as $entry |
    ($definitions[0] | map(select(.name == $entry.key)) | first) as $definition |
    ($definition != null) and
    ($entry.value == null or
      (if $definition.type == "NUMBER" then
         ($entry.value | type == "number")
       elif $definition.type == "TEXT" then
         ($entry.value | type == "string")
       elif $definition.type == "DATE" then
         ($entry.value | type == "string") and
         (try (
           (($entry.value + "T00:00:00Z" |
             fromdateiso8601 |
             strftime("%Y-%m-%d")) == $entry.value)
         ) catch false)
       elif $definition.type == "SINGLE_SELECT" then
         ($entry.value | type == "string") and
         any($definition.options[]; .name == $entry.value)
       else
         false
       end))
  ) and
  all(.items[];
    (.fields.Effort? == null) or
    ((.fields.Effort | type == "number") and .fields.Effort > 0)
  )
' project-items.json >/dev/null
```

作成前に確定できるプレースホルダーを置換済みであることも別に確認する。新規Projectの番号、Project ID、ProjectフィールドIDは、この時点では`null`でよい。

```bash
jq -e '
  .repository != "OWNER/REPO" and
  .project.owner != "OWNER" and
  (.project.title | contains("PROJECT_TITLE") | not) and
  all(.items[];
    (.issue_url | contains("OWNER/REPO") | not) and
    (.issue_node_id | contains("ISSUE_NODE_ID") | not)
  )
' project-items.json >/dev/null
```

Projectを作成または確定した後は番号とIDを計画へ記録し、次を通してからフィールドへ進む。

```bash
jq -e '
  (.project.number | type == "number" and . > 0 and floor == .) and
  (.project.id | type == "string" and startswith("PVT_"))
' project-items.json >/dev/null
```

メタデータの正本と全フィールドを確定した後は、`field_sources`を更新して次を通す。ProjectフィールドID、組織Issue Field ID、Type名の対応表のいずれも未確定のまま項目値設定へ進めない。

```bash
jq -e '
  . as $plan |
  all(.field_sources | to_entries[];
    .value as $source |
    if $source.kind == "project_field" then
      ($source.field_id |
        type == "string" and length > 0 and
        (contains("FIELD_ID") | not))
    elif $source.kind == "organization_issue_field" then
      ($source.field_id | type == "number" and . > 0 and floor == .)
    else
      ($source.value_map |
        type == "object" and length > 0 and
        all(to_entries[];
          (.key | type == "string" and length > 0) and
          (.value | type == "string" and length > 0)))
    end
  ) and
  all($plan.items[].fields | to_entries[];
    .key as $name |
    .value as $value |
    $plan.field_sources[$name] as $source |
    if $source.kind == "organization_issue_type" and $value != null then
      $source.value_map | has($value)
    else
      true
    end
  )
' project-items.json >/dev/null
```

`null`または省略した項目値は「変更しない」と解釈する。初期構築で暗黙の消去へ変換しない。`field_sources`は、各項目を`project_field`、`organization_issue_field`、`organization_issue_type`のどこへ書くかを示す。組織Issue TypeではProject側の値から実際のType名への`value_map`も持たせる。

組織側を正本にする場合は、同じ項目名の経路を次のように置き換える。

```json
{
  "field_sources": {
    "Type": {
      "kind": "organization_issue_type",
      "value_map": {
        "feat": "Feature",
        "fix": "Bug"
      }
    },
    "Priority": {
      "kind": "organization_issue_field",
      "field_id": 123
    }
  }
}
```

この断片は差分例であり、実際の`field_sources`には`project-fields.json`の全項目を1回ずつ含める。`items[].fields`は初期値を設定する項目だけを持つ部分集合でよい。

計画値は`references/project-setup.md`と`references/triage-and-agent-tier.md`に照らして、次も確認する。

- `ready`はIssue/PR側で開始可能と確定済みの場合だけ設定し、Project側で開始条件を再定義しない。
- `epic`へ`ready`、`Effort`、`Estimate Confidence`、`Agent Tier`を設定しない。
- 実行対象の末端Issueは、正の有限な`Effort`と`Estimate Confidence`を持つ。
- 初期割当では`Agent Run`、`Actual Start`、`Actual End`を設定しない。
- `Forecast Start`と`Forecast End`はISO日付で、稼働日、Issue依存、Milestone期限、容量に整合する。
- `r3-dangerous`は`Reviewer Owner`を持つ。

# 2. 対象と権限を発見する

対象リポジトリ、Issueの同一性、Project内のアイテム種別の探索は、利用可能ならGitHub MCPを優先する。Projectの操作に必要な能力がMCPにない場合は`gh project`を使う。再現可能な確認記録が必要な場合も`gh ... --json`を使う。

```bash
gh auth status
gh repo view OWNER/REPO \
  --json id,nameWithOwner,url,owner,defaultBranchRef,isPrivate
gh project list \
  --owner PROJECT_OWNER \
  --closed \
  --limit 10000 \
  --format json
```

`project`権限が不足する場合は、利用者の同意を得てから`gh auth refresh -s project`を実行する。権限を取得できなければ停止する。

出力を`/tmp/projects.json`へ保存した場合は、`jq -e '.totalCount == (.projects | length)' /tmp/projects.json`で全件取得を確認する。一覧件数が指定した`--limit`と同じ、または`totalCount`と配列長が異なる場合は、全件取得できたとみなさず、上限を増やすかGraphQLのカーソルで続きも取得する。閉じたProjectを除外せず、同名Project、所有者、番号、ID、公開範囲を確認する。

既存Projectを使う場合:

```bash
gh project view PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --format json
```

次を計画へ固定する。

- `OWNER/REPO`とリポジトリnode ID
- Project所有者、所有者種別、番号、node ID、タイトル、URL、公開範囲
- 既定ブランチ
- リポジトリとProjectの紐付け
- Project内の全アイテム種別とURL
- 組織Issue Type、組織Issue Field、Projectフィールドの候補

# 3. Projectを作成または確定する

新規作成では、同じ所有者の開いたProjectと閉じたProjectを全件取得し、同名がないことを確認する。書き込み前に次の文字列を利用者へ示し、完全一致の確認を得る。

```text
OWNER/REPO#create-project:PROJECT_OWNER:PROJECT_TITLE#VISIBILITY
```

確認後も1操作ずつ実行する。

```bash
gh project create \
  --owner PROJECT_OWNER \
  --title "PROJECT_TITLE" \
  --format json
```

返された番号とIDを保存し、Projectを再取得してから公開範囲を設定する。

```bash
gh project edit PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --visibility PRIVATE \
  --format json
```

再取得後にリポジトリへ紐付ける。

```bash
gh project link PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --repo OWNER/REPO
```

`create`、`edit`、`link`のどこかで失敗したら残りを止める。作成済みProjectを自動削除しない。Projectとリポジトリの紐付けは、`references/project-api-queries.md`の手順でリポジトリの`projectsV2`をページングし、対象IDが正確に1件含まれることを確認する。

# 4. メタデータの正本を決める

組織所有リポジトリでは、Issue TypeとIssue Fieldを全件取得する。

```bash
gh api --paginate --slurp \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "repos/OWNER/REPO/issue-types?per_page=100"

gh api --paginate --slurp \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "orgs/ORG/issue-fields?per_page=100"
```

フィールドごとに、名前、型、選択肢、公開範囲を`project-fields.json`と比較する。

- `Status`はProjectフィールドを正本にする。
- Type一式を組織Issue Typeで表せる場合だけ組織Issue Typeを使う。
- 同名・同型・同じ選択肢の組織Issue Fieldだけを採用する。
- 組織側にない項目はProjectフィールドへ置く。
- 同名異型、選択肢不足、公開範囲不一致、読み取り不能では停止する。
- Project内に別組織Issue、PR、Draft Issueが混在し、組織Issue Fieldで全件を表せない場合は停止する。

採用結果を割当計画の`field_sources`へ項目単位で記録する。`project_field`と`organization_issue_field`は確認済みのフィールドID、`organization_issue_type`は値の対応表を持つ。同じ値を複数の正本へ書かない。

# 5. Projectフィールドを整える

高水準コマンドで一覧を取得する。

```bash
gh project field-list PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --limit 10000 \
  --format json
```

出力を`/tmp/fields.json`へ保存した場合は、`jq -e '.totalCount == (.fields | length)' /tmp/fields.json`で全件取得を確認する。指定上限へ達した場合も取得不足として停止する。選択肢のID、色、説明、実データ型は`references/project-api-queries.md`のGraphQL読取で全ページを取得して比較する。

`field_sources`が`project_field`の不足フィールドだけを作る。組織Issue Typeまたは組織Issue Fieldを正本にした同名フィールドを作らない。

```bash
gh project field-create PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --name "Effort" \
  --data-type NUMBER \
  --format json

gh project field-create PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --name "Estimate Confidence" \
  --data-type SINGLE_SELECT \
  --single-select-options "ec0-low,ec1-medium,ec2-high" \
  --format json
```

各作成後にフィールド一覧を再取得する。同名フィールドを重複作成しない。既存フィールドの型や選択肢が異なる場合は自動更新しない。

単一選択肢の色・説明を更新する高水準コマンドはないため、必要な場合だけ`references/project-api-queries.md`のGraphQL `updateProjectV2Field`を使う。既存選択肢IDをすべて保持し、削除や改名は専用移行へ分ける。既存値を持つ選択肢を省略しない。

# 6. IssueをProjectアイテムへ追加する

割当計画の各Issueについて、番号から実Issueを再取得する。

```bash
gh issue view ISSUE_NUMBER \
  --repo OWNER/REPO \
  --json id,number,title,url,state
```

取得した番号、URL、node IDが計画と一致しない場合は停止する。タイトル一致だけで再利用しない。

Projectアイテムを全件取得する。

```bash
gh project item-list PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --limit 10000 \
  --format json
```

出力を`/tmp/items.json`へ保存した場合は、`jq -e '.totalCount == (.items | length)' /tmp/items.json`で全件取得を確認する。予定URLが既に正確に1件ある場合はそのアイテムIDを記録する。0件なら追加する。複数件、取得不足、別種類の同一URLがあれば停止する。

```bash
gh project item-add PROJECT_NUMBER \
  --owner PROJECT_OWNER \
  --url ISSUE_URL \
  --format json
```

追加直後にアイテム一覧を再取得し、Issue URLが正確に1件あり、返されたProjectアイテムIDと一致することを確認する。既存Projectでは、Project総アイテム数と計画Issue数を一致条件にしない。

# 7. 項目値を設定する

`field_sources.kind`に従って書込経路を選ぶ。Project ID、ProjectアイテムID、フィールドID、単一選択肢IDを再取得してから、`project_field`は1呼び出しで1項目だけ更新する。

```bash
gh project item-edit \
  --project-id PROJECT_ID \
  --id PROJECT_ITEM_ID \
  --field-id FIELD_ID \
  --number 3

gh project item-edit \
  --project-id PROJECT_ID \
  --id PROJECT_ITEM_ID \
  --field-id FIELD_ID \
  --single-select-option-id OPTION_ID

gh project item-edit \
  --project-id PROJECT_ID \
  --id PROJECT_ITEM_ID \
  --field-id FIELD_ID \
  --text "search"

gh project item-edit \
  --project-id PROJECT_ID \
  --id PROJECT_ITEM_ID \
  --field-id FIELD_ID \
  --date 2026-08-03
```

未指定または`null`は変更しない。値を消す`--clear`は、対象値と影響を再取得し、個別の明示承認を得た場合だけ使う。

`organization_issue_type`のTypeは`value_map`で実名へ変換し、`gh issue edit --type`で設定する。`organization_issue_field`の入力JSON生成と再取得は`references/project-api-queries.md`に従う。既存値を全置換する`PUT`ではなく`POST`で対象項目だけ追加・更新する。空の`issue_field_values`は全消去になるため送らない。

```bash
gh api --method POST \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "repos/OWNER/REPO/issues/ISSUE_NUMBER/issue-field-values" \
  --input issue-field-values.json
```

各Issueの値設定後に、Projectアイテム、組織Issue Type、組織Issue Fieldの採用した正本だけを再取得して計画と比較する。

# 8. ビューを整える

既存ビューは`references/project-api-queries.md`のGraphQLで全ページを取得し、レイアウト値を正規化する。`project-views.json`と、名前、レイアウト、絞り込み条件を比較する。同名不一致と標準外ビューは上書き・削除せず停止し、人間が残すか移行するかを決める。

不足ビューだけをREST APIで作る。組織所有Project:

```bash
gh api --method POST \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "orgs/ORG/projectsV2/PROJECT_NUMBER/views" \
  -f name='かんばん' \
  -f layout='board' \
  -f filter='is:issue is:open status:inbox,triaged,ready,in-progress,in-review,blocked'
```

個人所有Projectでは、`gh api users/USER --jq .id`で数値IDを確認し、`users/USER_ID/projectsV2/PROJECT_NUMBER/views`を使う。トークン種別と権限を確認し、401や403を同名ビューの存在として扱わない。

各ビュー作成直後に全ページを再取得し、名前、レイアウト、絞り込み条件を検証する。REST APIで設定できないグループ化、並び替え、ボード列、ロードマップの日付フィールド、表示項目は`assets/.github/project/views.md`と照合して画面で確認する。

# 9. 全件を検証する

代表例の抜き取りではなく、計画対象を全件確認する。

- Projectの所有者、番号、ID、タイトル、公開範囲、リポジトリ紐付け
- `field_sources`で採用した組織Issue Type、組織Issue Field、Projectフィールドの正本分担とID
- `project-fields.json`にある作成対象フィールドの名前、型、選択肢、色、説明
- 計画した全Issue URLがProject内に正確に1件あり、ProjectアイテムIDを持つこと
- `project-items.json`の全項目値が採用した正本と一致すること
- `project-views.json`の全ビューが名前、レイアウト、絞り込み条件まで一致すること
- 画面確認が必要なビュー設定を4ビューすべて確認したこと

一覧応答に`totalCount`がある場合は、配列長との一致を`jq -e`で確認する。上限到達、`hasNextPage: true`、欠落ページがあれば検証失敗とする。

検証結果には、成功件数だけでなく、対象Project URL、予定Issue URL、フィールド名、ビュー名、未確認値、画面確認の残件を記録する。未確認値が1つでもあれば初期構築を完了扱いにしない。
