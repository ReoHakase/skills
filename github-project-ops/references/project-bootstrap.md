# Project bootstrap

新規repositoryにProject、項目、WBS Issues、sub-issues、blocked by / blocking、Project item項目値をまとめて作るときに読む。

# 目的

大量のWBS起票では、GitHub UIだけで作るとProject field、親子関係、依存関係の入れ忘れが起きやすい。先にGitHub上の実状態を確認し、`gh` と `gh api graphql` で再現可能な手順へ落とす。

このreferenceは実例から抽出した手順である。対象repositoryへそのまま流し込まず、`OWNER/REPO`、Project owner/number/id、Issue一覧、field値を確認してから実行する。

# 事前確認

GitHub CLIに `project` scope が必要である。

```bash
gh auth status
gh auth refresh -s project
```

repositoryと既存Issueを確認する。

```bash
gh repo view OWNER/REPO --json id,nameWithOwner,url,defaultBranchRef,owner,isPrivate
gh issue list --repo OWNER/REPO --state all --limit 100 --json number,title,state,url
gh project list --owner OWNER --format json --limit 100
```

`OWNER` が自分の場合でも、Project操作では `--owner @me` と login 名のどちらが使えるかを実コマンドで確認する。repository linkでは `--owner OWNER --repo REPO_NAME` のように login と repo 名を明示する方が誤解釈を避けやすい。

# Project作成とrepository link

Projectを新規作成する。

```bash
gh project create --owner @me --title "PROJECT_TITLE" --format json
```

返ってきた `number` と `id` を控える。以後の例では次のplaceholderを使う。

```text
PROJECT_NUMBER=1
PROJECT_ID=PVT_xxx
PROJECT_OWNER=@me
REPO=OWNER/REPO
```

repositoryへlinkする。

```bash
gh project link PROJECT_NUMBER --owner OWNER --repo REPO_NAME
```

# Project fields

フィールド定義は `assets/project-fields.json` を正本にする。Python側へ同じ一覧を複製しない。既定Projectには `Status` が `Todo`、`In Progress`、`Done` で作られることがあるため、同名フィールドを重複作成しない。

Single select optionは、単なる文字列と次のobject形式の両方を扱える。標準assetでは `name`、`color`、`description` を持つobject形式を使う。

```json
{
  "name": "ready",
  "color": "GREEN",
  "description": "阻害要因と受け入れ条件を確認済みで、作業開始できる。"
}
```

`gh project field-create --single-select-options` はoption名だけを受け取る。色と説明文は、作成後または既存field更新時にGraphQL `updateProjectV2Field` で反映する。

field一覧を読む。

```bash
gh project field-list PROJECT_NUMBER --owner @me --format json --limit 100
```

存在しないfieldは作る。

```bash
gh project field-create PROJECT_NUMBER \
  --owner @me \
  --name "Type" \
  --data-type SINGLE_SELECT \
  --single-select-options "epic,feat,fix,docs,style,refactor,perf,test,build,ci,chore,revert,spike" \
  --format json
```

Text/Date fieldは `--data-type TEXT` または `--data-type DATE` で作る。

既存single select fieldのoptionを置き換える場合、またはoptionの色・説明文を反映する場合はGraphQLを使う。

```bash
gh api graphql -f query='
mutation {
  updateProjectV2Field(input:{
    fieldId:"FIELD_ID",
    singleSelectOptions:[
      {name:"inbox",color:GRAY,description:"新しく起票され、まだトリアージされていない。"},
      {name:"triaged",color:BLUE,description:"分類済みだが、まだ実装開始できるとは限らない。"},
      {name:"ready",color:GREEN,description:"阻害要因と受け入れ条件を確認済みで、作業開始できる。"},
      {name:"in-progress",color:YELLOW,description:"現在作業中。"},
      {name:"in-review",color:ORANGE,description:"プルリクエストがあり、レビュー、CI、またはマージキュー待ち。"},
      {name:"blocked",color:RED,description:"外部依存、判断待ち、失敗対応などが解消するまで進められない。"},
      {name:"done",color:PURPLE,description:"マージまたは完了確認済み。"},
      {name:"canceled",color:GRAY,description:"不要、無効、重複、対象外などの理由で実装せず終了。"}
    ]
  }) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        name
        options { id name }
      }
    }
  }
}'
```

`assets/project-bootstrap-template.py` はこの流れを一括処理化している。テンプレートは `PROJECT_FIELDS_PATH` のJSONを読む。テンプレートだけを一時パスへコピーする場合は、`project-fields.json` も同じディレクトリへ置くか、`PROJECT_FIELDS_PATH` を元アセットの絶対パスへ向ける。

項目作成時は選択肢名だけをCLIへ渡し、メタデータ付き選択肢定義がある場合はGraphQLで色と説明文を上書きする。

# Issue作成

Issue本文にはProject項目の割り当て、sub-issue一覧、依存関係section、実装メモを書かない。現在信頼してよい概要、背景、スコープ、非スコープ、受け入れ条件、確認手順だけを書く。sub-issue、blocked by / blocking、Project項目値はGitHubメタデータをSSoTにする。

```bash
gh issue create \
  --repo OWNER/REPO \
  --title "自然な日本語のIssue title" \
  --body-file -
```

作成済みIssueを再利用する一括処理では、titleを一時照合keyにする。bootstrap対象内ではtitleを一意にする。

# sub-issue / dependency fallback

`gh issue edit --parent`、`--add-sub-issue`、`--add-blocked-by`、`--add-blocking` が使える場合は高水準commandでよい。

```bash
gh issue edit CHILD_NUMBER --repo OWNER/REPO --parent PARENT_NUMBER
gh issue edit ISSUE_NUMBER --repo OWNER/REPO --add-blocked-by BLOCKER_NUMBER
```

大量作成時にこれらのcommandが返らない、または冪等再実行で扱いにくい場合はGraphQLへ切り替える。まずIssue node idを読む。

```bash
gh issue view ISSUE_NUMBER --repo OWNER/REPO --json id,number,title,url
```

sub-issueを追加する。

```bash
gh api graphql -f query='
mutation {
  addSubIssue(input:{
    issueId:"PARENT_ISSUE_NODE_ID",
    subIssueId:"CHILD_ISSUE_NODE_ID",
    replaceParent:true
  }) {
    clientMutationId
  }
}'
```

blocked byを追加する。

```bash
gh api graphql -f query='
mutation {
  addBlockedBy(input:{
    issueId:"BLOCKED_ISSUE_NODE_ID",
    blockingIssueId:"BLOCKER_ISSUE_NODE_ID"
  }) {
    clientMutationId
  }
}'
```

既に同じ関係がある場合、GitHubは重複系の検証エラーを返す。bootstrap再実行では警告として扱い、最後に実状態を検証する。

# Project item追加とfield値設定

`gh project item-add` が返らない場合は、GraphQL `addProjectV2ItemById` を使う。

```bash
gh api graphql -f query='
mutation {
  addProjectV2ItemById(input:{
    projectId:"PROJECT_ID",
    contentId:"ISSUE_NODE_ID"
  }) {
    item { id }
  }
}'
```

Project item field valueはGraphQLで設定する。

Single select:

```bash
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(input:{
    projectId:"PROJECT_ID",
    itemId:"PROJECT_ITEM_ID",
    fieldId:"FIELD_ID",
    value:{singleSelectOptionId:"OPTION_ID"}
  }) {
    projectV2Item { id }
  }
}'
```

Text:

```bash
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(input:{
    projectId:"PROJECT_ID",
    itemId:"PROJECT_ITEM_ID",
    fieldId:"FIELD_ID",
    value:{text:"db"}
  }) {
    projectV2Item { id }
  }
}'
```

Date:

```bash
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(input:{
    projectId:"PROJECT_ID",
    itemId:"PROJECT_ITEM_ID",
    fieldId:"FIELD_ID",
    value:{date:"2026-06-20"}
  }) {
    projectV2Item { id }
  }
}'
```

大量設定では `assets/project-bootstrap-template.py` をコピーまたは一時ファイルへ展開し、対象リポジトリ用に編集する。Projectフィールドは `assets/project-fields.json` を読み込ませる。`ISSUES` の `body` は `dedent("""...""").strip()` で書き、長い文字列連結にしない。PythonテンプレートにはIssue本文例を置かず、本文の構成と記入例は `references/issue-authoring.md` を参照する。空のbodyは未設定として扱い、Issue作成前に停止する。

# Project views

GitHub Projects API / `gh project` にはview作成・view編集のmutationやsubcommandが公開されていない前提で扱う。view名、目的、filter、group、sort、visible fieldsは `assets/.github/project/views.md` を対象repoの `.github/project/views.md` へコピーして残す。

Project UI上では次の4 viewだけを作る。

- `かんばん`
- `WBS/ロードマップ`
- `マージキュー候補`
- `Velocity`

# 検証

Project fields:

```bash
gh project field-list PROJECT_NUMBER --owner @me --format json --limit 100
```

Project items:

```bash
gh project item-list PROJECT_NUMBER --owner @me --format json --limit 100
```

代表epicのsub-issues:

```bash
gh issue view EPIC_NUMBER \
  --repo OWNER/REPO \
  --json number,title,subIssues,subIssuesSummary
```

代表Issueのparent / dependency:

```bash
gh issue view ISSUE_NUMBER \
  --repo OWNER/REPO \
  --json number,title,parent,blockedBy,blocking
```

repo側view説明:

```bash
test -f .github/project/views.md
```

最後に、実際に作った件数を数字で確認する。

```text
Project fields: expected 29 including built-ins
Project items: expected created WBS issue count
Issues: existing dashboardやdependency issueを含む場合があるため、WBS issue number rangeで確認する
```
