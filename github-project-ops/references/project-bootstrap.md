# Project bootstrap

新規repositoryにProject、Milestone、項目、WBS Issues、sub-issues、blocked by / blocking、Project item項目値をまとめて作るときに読む。

このreferenceは初期一括作成専用である。bootstrap後のIssue追加、sub-issue追加、依存関係追加、Forecast変更は `references/issue-authoring.md` と `references/project-setup.md` を読む。Project/Milestoneを剥がす場合は `references/uninstall.md` を読む。

# 目的

大量のWBS起票では、GitHub UIだけで作るとProject field、親子関係、依存関係の入れ忘れが起きやすい。先にGitHub上の実状態を確認し、`gh` と `gh api graphql` で再現可能な手順へ落とす。

このreferenceは実例から抽出した手順である。対象repositoryへそのまま流し込まず、`OWNER/REPO`、Project owner/number/id、Issue一覧、field値を確認してから実行する。運用中の変更をbootstrap templateの再実行だけで吸収しようとしない。

実行境界は `plan -> apply -> verify` に固定する。引数なし実行や `plan` はmutationを行わない。`apply` は対象repositoryとProject numberを含むtyped confirmationが一致した場合だけ書き込み、直後に全対象をverifyする。

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
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100
gh project list --owner OWNER --format json --limit 100
```

`OWNER` が自分の場合でも、Project操作では `--owner @me` と login 名のどちらが使えるかを実コマンドで確認する。repository linkでは `--owner OWNER --repo REPO_NAME` のように login と repo 名を明示する方が誤解釈を避けやすい。

`assets/project-bootstrap-template.py` はmutation前に、placeholder、Project ID/number/owner、repository node、default branch、repositoryとProjectのlink、明示した再利用Issue numberとtitleを照合する。

対象を確認したらread-only planを出す。

```bash
python project-bootstrap.py plan
python project-bootstrap.py plan --update-existing-fields
python project-bootstrap.py plan --backlog backlog.flat.json
```

2行目は既存single-select fieldのmetadata更新も計画するときだけ使う。3行目はコード内の `ISSUES` に代えてJSON入力を使う例である。

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

# Milestones

MilestoneはGitHub native milestoneを使う。Project fieldへ複製しない。

bootstrap既定では `First Release` milestoneを作る。`First Release` は期限必須で、`assets/project-bootstrap-template.py` 実行時に `YYYY-MM-DD` を標準入力で聞く。締切未定Milestoneを追加する場合は、`required_due_on=False`、`due_on=""` のまま作ってよい。

Milestone due dateを先に決め、その締切目標からIssue/WBSのForecast Start / Forecast Endを組む。IssueのForecastからMilestone期限を逆算しない。

Milestone一覧を読む。

```bash
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100
```

Milestoneを作る。

```bash
gh api repos/OWNER/REPO/milestones \
  -f title="First Release" \
  -f description="初回利用可能版。Milestone期限を先に決めてからIssue/WBSのForecastを組む。" \
  -f due_on="2026-07-31T23:59:59Z"
```

`gh` にはmilestone専用subcommandがない前提で扱う。Milestone作成はREST APIを使う。Issue作成時のMilestone割当は `gh issue create --milestone "First Release"` を使う。既存Issueへ後付けする場合は `gh issue edit ISSUE_NUMBER --milestone "First Release"` を使う。

# Project fields

フィールド定義は `assets/project-fields.json` を正本にする。Python側へ同じ一覧を複製しない。既定Projectには `Status` が `Todo`、`In Progress`、`Done` で作られることがあるため、同名フィールドを重複作成しない。

Single select optionは、単なる文字列と次のobject形式の両方を扱える。標準assetでは `name`、`color`、`description` を持つobject形式を使う。

```json
{
  "name": "ready",
  "color": "GREEN",
  "description": "受け入れ条件と確認手順があり、未解決のblocked byがなく、作業開始できる。"
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

既存single select fieldのoptionを更新する場合は、同名optionの既存IDを必ず引き継ぐ。IDを省略した既存optionは、そのoptionを参照するProject itemの値をclearし得る。削除とrenameはbootstrapでは行わず、対象item/valueをexportした専用migrationへ分ける。例外は、apply直前のreadでProject item数が0だと確認できた初期Projectだけである。この場合も `--update-existing-fields` を要求し、GitHub既定Status optionをcanonical定義へ置き換える。

次の例は、対象fieldにこの8 optionだけが存在し、各 `OPTION_*_ID` を事前readで取得済みの場合に限る。既存optionを省略しない。

```bash
gh api graphql -f query='
mutation {
  updateProjectV2Field(input:{
    fieldId:"FIELD_ID",
    singleSelectOptions:[
      {id:"OPTION_INBOX_ID",name:"inbox",color:GRAY,description:"新しく起票され、まだトリアージされていない。"},
      {id:"OPTION_TRIAGED_ID",name:"triaged",color:BLUE,description:"分類済み。仕様や依存の整理中。"},
      {id:"OPTION_READY_ID",name:"ready",color:GREEN,description:"開始条件が揃っている。"},
      {id:"OPTION_IN_PROGRESS_ID",name:"in-progress",color:YELLOW,description:"現在作業中。"},
      {id:"OPTION_IN_REVIEW_ID",name:"in-review",color:ORANGE,description:"レビュー、CI、またはmerge待ち。"},
      {id:"OPTION_BLOCKED_ID",name:"blocked",color:RED,description:"外部要因が解消するまで進められない。"},
      {id:"OPTION_DONE_ID",name:"done",color:PURPLE,description:"完了条件を確認済み。"},
      {id:"OPTION_CANCELED_ID",name:"canceled",color:GRAY,description:"実施せず終了。"}
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

項目作成時は選択肢名だけをCLIへ渡し、作成後に取得したoption IDを付けて色と説明文を上書きする。既存fieldの差分は `--update-existing-fields` なしでは停止する。同名optionのID、順序、色、説明が一致する場合は更新しない。

# Issue作成

Issue本文にはProject項目の割り当て、sub-issue一覧、依存関係section、実装メモを書かない。現在信頼してよい概要、背景、スコープ、非スコープ、変更ファイル、参照ドキュメント、受け入れ条件、確認手順を書く。sub-issue、blocked by / blocking、Project項目値はGitHubメタデータをSSoTにする。

`assets/project-bootstrap-template.py` はIssue作成前にローカル定義を検証する。

- `First Release` のdue dateを `YYYY-MM-DD` で入力する。
- Milestone titleの重複を作らない。
- Issueが参照するMilestone titleは `MILESTONES` 内に置く。
- epic IssueのStatusを `ready` にしない。
- 未解決の `blocked_by` がある初期WBS Issueを `ready` にしない。blockerが型別done済みならreadyを許可する。
- 再利用するdone blockerは、既存IssueがclosedでProject Statusもdoneであることをread-onlyの事前確認で照合する。PR merge、spikeの結論、外部操作の証跡など、成果種別固有のdone条件も人間またはagentが確認する。
- 依存関係とsub-issue階層の自己参照、重複、循環を作らない。canceled blockerを完了扱いにしない。
- epicのEffort、Estimate Confidence、Agent Tierは空欄にする。その他の実行対象Issueには正の有限Effort、Estimate Confidence、判定式どおりのAgent Tierを設定する。
- 初期Agent Runは空欄にする。`r3-dangerous` にはReviewer Ownerを設定する。
- Issue本文には `変更ファイル` と `参照ドキュメント` を含める。参照commitはbranch名ではなく実SHAにする。
- Forecast Start / Forecast EndはISO日付にする。
- Forecast Start / Forecast Endは `WORKING_WEEKDAYS` と `HOLIDAYS` で定義した稼働日に置く。
- 直列依存では、後続IssueのForecast Startをすべての `blocked_by` 先のForecast Endより後の日付にする。

これは初期WBS投入前の局所検証であり、運用中のProject Statusを `blocked by` / `blocking` から自動同期するためのルールではない。upstream PR、Figma design、権限、担当外のCI基盤障害、設計判断待ちなどでblockedになるIssueもあるため、Status更新はGitHub上の関係とblockedコメントを確認して行う。

```bash
gh issue create \
  --repo OWNER/REPO \
  --title "自然な日本語のIssue title" \
  --milestone "First Release" \
  --body-file -
```

作成済みIssueはtitleだけで再利用しない。`Issue.number` に確認済みnumberを明示し、実Issueのtitleと一致した場合だけ再利用する。number未指定の同名Issueが存在する場合は停止する。bootstrap対象内のtitle重複もIssue作成前に拒否する。

Pythonテンプレートには長いIssue本文例を置かない。初期起票用の本文は `references/issue-authoring.md` の `Issue本文テンプレート` をもとに、対象リポジトリの仕様、設計、README、docsへのコミット固定URLを入れて作る。

bootstrap後にIssueを追加する場合は、既存の親Issue、sub-issue、blocked by / blocking、Milestoneを確認してから `references/issue-authoring.md` の手順で個別に追加する。

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

既に同じ関係がある場合、GitHubは重複系の検証エラーを返す。bootstrap再実行では操作別に既知のduplicate errorだけを警告として扱う。duplicateと権限・schema errorが混在する場合を含め、その他はfail-closedで停止する。apply後は全対象IssueのparentとblockedByを再取得して一致を確認する。

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

大量設定では `assets/project-bootstrap-template.py` をコピーまたは一時ファイルへ展開し、対象リポジトリ用に編集する。Projectフィールドは `assets/project-fields.json` を読み込ませる。Issue入力は次のどちらか一方に統一する。

- 少数ならコード内の `ISSUES` を編集する。`body` は `dedent("""...""").strip()` で書く。
- 多数なら `assets/backlog.flat.json` を複製し、全サブコマンドへ同じ `--backlog PATH` を渡す。`parent_title` と `blocked_by_titles` はそれぞれ `parent` と `blocked_by` へ変換される。未対応項目、欠落項目、不正なJSONはGitHubへ接続する前に拒否される。

どちらも本文の構成は `references/issue-authoring.md` を正とする。型別の必須節、内容、Project fieldや依存関係の重複禁止、コミットSHAへ固定した参照ドキュメントをGitHubへ接続する前に検証する。

planの `blockers` が空であることを確認してからapplyする。確認文字列は設定したrepositoryとProject numberそのものを使う。

```bash
python project-bootstrap.py apply \
  --backlog backlog.flat.json \
  --confirm "OWNER/REPO#PROJECT_NUMBER"
```

既存fieldの安全なmetadata更新も承認した場合だけ、applyにも同じflagを付ける。

```bash
python project-bootstrap.py apply \
  --update-existing-fields \
  --confirm "OWNER/REPO#PROJECT_NUMBER"
```

apply出力のIssue number、URL、Project item IDはmanifestとして保存し、再実行前に `ISSUES` またはbacklog JSONの各 `number` へ反映する。途中失敗時はtitle照合で続行せず、出力とGitHub実状態を読み、明示numberを設定してplanから再開する。

# Project views

GitHub Projects API / `gh project` にはview作成・view編集のmutationやsubcommandが公開されていない前提で扱う。view名、目的、filter、group、sort、visible fieldsは `assets/.github/project/views.md` を対象repoの `.github/project/views.md` へコピーして残す。

Project UI上では次の4 viewだけを作る。

- `かんばん`
- `WBS/ロードマップ`
- `マージキュー候補`
- `Velocity`

# 検証

applyは完了直後にverifyを自動実行する。別processで再検証する場合は、apply出力のIssue numberを `ISSUES` またはbacklog JSONへ保存し、applyと同じ入力を指定する。

```bash
python project-bootstrap.py verify --backlog backlog.flat.json
```

verifyは全canonical field/type/options、Milestoneとdue date、全Issue identity、全parent/blockedBy、全Issue URLに対応するProject itemをread-onlyで確認する。代表Issueだけのspot checkで完了扱いにしない。

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

Milestones:

```bash
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100
```

repo側view説明:

```bash
test -f .github/project/views.md
```

最後に、実際に作った件数を数字で確認する。

```text
Milestones: expected First Release
Project fields: assets/project-fields.jsonの全canonical fieldと必要なbuilt-in field
Project items: expected created WBS issue count
Issues: existing dashboardやdependency issueを含む場合があるため、WBS issue number rangeで確認する
```
