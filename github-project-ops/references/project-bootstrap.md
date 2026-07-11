# Project初期構築

新規リポジトリにProject、Milestone、項目、WBS Issue、sub-issue、blocked by / blocking、Project項目値をまとめて作るときに読む。

この参照資料は初期一括作成専用である。初期構築後のIssue追加、sub-issue追加、依存関係追加、Forecast変更は `references/issue-authoring.md` と `references/project-setup.md` を読む。Project/Milestoneを外す場合は `references/uninstall.md` を読む。

# 目的

大量のWBS起票では、GitHub UIだけで作るとProject項目、親子関係、依存関係の入れ忘れが起きやすい。先にGitHub上の実状態を確認し、`gh` と `gh api graphql` で再現可能な手順へ落とす。

この参照資料は実例から抽出した手順である。対象リポジトリへそのまま流し込まず、`OWNER/REPO`、Projectの所有者・番号・ID、Issue一覧、項目値を確認してから実行する。運用中の変更を初期構築テンプレートの再実行だけで吸収しようとしない。

実行境界は `plan -> apply -> verify` に固定する。`plan` は書き込みを行わない。`apply` は対象リポジトリとProject番号を含む確認文字列が一致した場合だけ書き込み、直後に全対象を `verify` する。

# 事前確認

GitHub CLIに `project` 権限が必要である。

```bash
gh auth status
gh auth refresh -s project
```

リポジトリと既存Issueを確認する。

```bash
gh repo view OWNER/REPO --json id,nameWithOwner,url,defaultBranchRef,owner,isPrivate
DEFAULT_BRANCH=$(gh repo view OWNER/REPO --json defaultBranchRef --jq '.defaultBranchRef.name')
gh api --method GET -H "X-GitHub-Api-Version: 2026-03-10" repos/OWNER/REPO
gh issue list --repo OWNER/REPO --state all --limit 100 --json number,title,state,url
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100
gh project list --owner OWNER --format json --limit 100
```

REST応答の所有者種別 `owner.type`、公開範囲 `visibility`、組織の契約プラン `plan.name` から能力を判定する。組織所有リポジトリでは次も読み、組織Issue Type / Issue FieldとProject項目を同義で二重作成しない。

```bash
gh api --method GET \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/OWNER/REPO/issue-types

gh api --method GET \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  orgs/ORG/issue-fields
```

- 正規のType一式がリポジトリのIssue Typeに揃う場合は組織Issue Typeを正本にし、それ以外はProject Typeを使う。組織Issue FieldをTypeの代用にはしない。同名の組織Issue Fieldがある場合は表示上も衝突するため停止する。
- 同名・同型・同じ選択肢の組織Issue Fieldがある場合は、その項目を正本にする。
- 公開ProjectまたはEnterprise Managed Usersのinternal Projectでは、`visibility: all` の組織Issue Fieldだけを使う。組織内限定項目は表示できないため停止する。
- 個人所有または組織側に対応項目がない場合はProject項目へ切り替える。
- 同名だが型または選択肢が異なる場合、読み取り権限がなく404になる場合は、推測で続行せず正本の衝突として停止する。
- 既存Projectに対象組織以外のIssue、PR、Draft Issue、削除済み項目があれば、組織項目では全行を表せないため停止する。対象組織のIssueだけを持つProjectへ分けてから再実行する。

`OWNER` が自分の場合でも、Project操作では `--owner @me` とログイン名のどちらが使えるかを実コマンドで確認する。リポジトリとの紐づけでは `--owner OWNER --repo REPO_NAME` のようにログイン名とリポジトリ名を明示する方が誤解釈を避けやすい。

`assets/project-bootstrap-template.py` は書き込み前に、プレースホルダー、ProjectのID・番号・所有者・公開範囲、リポジトリのnode ID、既定ブランチ、リポジトリとProjectの紐づけ、組織メタデータ能力、明示した再利用Issueの番号とタイトルを照合する。`plan` には採用したメタデータ正本、利用資格に基づく推奨マージ方式、全項目値更新を表示する。推奨方式は設定済みという意味ではなく、`configuration_verified: false` のまま出す。契約プランを確認できない場合は `recommended_mode: undetermined` とし、方式を推測しない。

対象を確認したら、書き込みなしの `plan` を出す。

```bash
python project-bootstrap.py plan
python project-bootstrap.py plan --update-existing-fields
python project-bootstrap.py plan --backlog backlog.flat.json
```

2行目は既存の単一選択項目のメタデータ更新も計画するときだけ使う。3行目はコード内の `ISSUES` に代えてJSON入力を使う例である。

# Project作成とリポジトリの紐づけ

Projectを新規作成する。

```bash
gh project create --owner OWNER --title "PROJECT_TITLE" --format json
```

返ってきた `number` と `id` を控える。以後の例では次のプレースホルダーを使う。

```text
PROJECT_NUMBER=1
PROJECT_ID=PVT_xxx
PROJECT_OWNER=OWNER
REPO=OWNER/REPO
```

リポジトリへ紐づける。

```bash
gh project link PROJECT_NUMBER --owner OWNER --repo REPO_NAME
```

# Milestone

MilestoneはGitHub標準のMilestoneを使う。Project項目へ複製しない。

初期構築の既定では `First Release` Milestoneを作る。`First Release` は期限必須で、`assets/project-bootstrap-template.py` 実行時に `YYYY-MM-DD` を標準入力で聞く。締切未定Milestoneを追加する場合は、`required_due_on=False`、`due_on=""` のまま作ってよい。

Milestoneの期限を先に決め、その締切目標からIssue/WBSのForecast Start / Forecast Endを組む。IssueのForecastからMilestone期限を逆算しない。

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

Milestone作成はREST APIを使う。Issue作成時のMilestone割当は `gh issue create --milestone "First Release"` を使う。既存Issueへ後付けする場合は `gh issue edit ISSUE_NUMBER --milestone "First Release"` を使う。

# Project項目

項目の正規定義は `assets/project-fields.json` に置き、Python側へ同じ一覧を複製しない。ただし値の保存先は能力確認後に決める。互換な組織Issue Fieldがあればその項目を正本にし、Project項目の作成対象から外す。正規Type一式が組織Issue Typeに揃う場合も同様に、Project独自Typeを作らない。`Status` はProject固有の運用状態なのでProject項目に残す。

既定Projectには `Status` が `Todo`、`In Progress`、`Done` で作られることがあるため、同名フィールドを重複作成しない。同名の組織Issue Fieldが正規定義と一致しない場合も、Project側に同名項目を作って回避せず停止する。

単一選択肢は、単なる文字列と次のJSONオブジェクト形式の両方を扱える。標準アセットでは `name`、`color`、`description` を持つ形式を使う。

```json
{
  "name": "ready",
  "color": "GREEN",
  "description": "受け入れ条件と確認手順があり、未解決のblocked byがなく、作業開始できる。"
}
```

`gh project field-create --single-select-options` は選択肢名だけを受け取る。色と説明文は、作成後または既存項目の更新時にGraphQL `updateProjectV2Field` で反映する。

項目一覧を読む。

```bash
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 100
```

存在しない項目は作る。

```bash
gh project field-create PROJECT_NUMBER \
  --owner OWNER \
  --name "Type" \
  --data-type SINGLE_SELECT \
  --single-select-options "epic,feat,fix,docs,style,refactor,perf,test,build,ci,chore,revert,spike" \
  --format json
```

テキスト・日付項目は `--data-type TEXT` または `--data-type DATE` で作る。

既存の単一選択項目を更新する場合は、同名選択肢の既存IDを必ず引き継ぐ。IDを省略した既存選択肢は、その選択肢を参照するProject項目の値を消去し得る。削除と名前変更は初期構築では行わず、対象項目と値を書き出した専用移行へ分ける。例外は、`apply` 直前の読み取りでProject項目数が0だと確認できた初期Projectだけである。この場合も `--update-existing-fields` を要求し、GitHub既定のStatus選択肢を正規定義へ置き換える。

次の例は、対象項目にこの8選択肢だけが存在し、各 `OPTION_*_ID` を事前に取得済みの場合に限る。既存選択肢を省略しない。

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

`assets/project-bootstrap-template.py` はこの流れを一括処理化している。テンプレートは `PROJECT_FIELDS_PATH` と `PROJECT_VIEWS_PATH` のJSONを読む。テンプレートだけを一時パスへコピーする場合は、`project-fields.json` と `project-views.json` も同じディレクトリへ置くか、各パスを元アセットの絶対パスへ向ける。

項目作成時は選択肢名だけをCLIへ渡し、作成後に取得した選択肢IDを付けて色と説明文を上書きする。既存項目の差分は `--update-existing-fields` なしでは停止する。同名選択肢のID、順序、色、説明が一致する場合は更新しない。

# Issue作成

Issue本文には組織Issue Field / Project項目の値、sub-issue一覧、依存関係の節、実装メモを書かない。現在信頼してよい概要、背景、非スコープ、変更ファイル、参照ドキュメント、受け入れ条件、確認手順を書く。sub-issue、blocked by / blocking、構造化項目値はGitHubメタデータをSSoTにする。

`assets/project-bootstrap-template.py` はIssue作成前にローカル定義を検証する。

- `First Release` の期限を `YYYY-MM-DD` で入力する。
- Milestoneタイトルの重複を作らない。
- Issueが参照するMilestoneタイトルは `MILESTONES` 内に置く。
- `epic` IssueのStatusを `ready` にしない。
- 未解決の `blocked_by` がある初期WBS Issueを `ready` にしない。阻害Issueが型別`done`済みなら `ready` を許可する。
- 再利用する`done`の阻害Issueは、既存Issueが終了済みでProject Statusも`done`であることを、書き込みなしの事前確認で照合する。PRマージ、`spike`の結論、外部操作の証跡など、成果種別固有の`done`条件も人間またはエージェントが確認する。
- 依存関係とsub-issue階層の自己参照、重複、循環を作らない。canceled blockerを完了扱いにしない。
- `epic` のEffort、Estimate Confidence、Agent Tierは空欄にする。その他の実行対象Issueには正の有限Effort、Estimate Confidence、判定式どおりのAgent Tierを設定する。
- 初期Agent Runは空欄にする。`r3-dangerous` にはReviewer Ownerを設定する。
- Issue本文には `変更ファイル` と `参照ドキュメント` を含める。参照コミットはブランチ名ではなく実SHAにする。
- 組織Issue Type / Issue Field、Project項目のどれを正本にしたかを `plan` で確認する。同義項目を両方へ設定しない。
- Forecast Start / Forecast EndはISO日付にする。
- Forecast Start / Forecast Endは `WORKING_WEEKDAYS` と `HOLIDAYS` で定義した稼働日に置く。
- 直列依存では、後続IssueのForecast Startをすべての `blocked_by` 先のForecast Endより後の日付にする。

これは初期WBS投入前の局所検証であり、運用中のProject Statusを `blocked by` / `blocking` から自動同期するための規則ではない。上流PR、Figmaデザイン、権限、担当外のCI基盤障害、設計判断待ちなどで`blocked`になるIssueもあるため、Status更新はGitHub上の関係と阻害コメントを確認して行う。

```bash
gh issue create \
  --repo OWNER/REPO \
  --title "自然な日本語のIssueタイトル" \
  --milestone "First Release" \
  --body-file -
```

作成済みIssueはタイトルだけで再利用しない。`Issue.number` に確認済み番号を明示し、実Issueのタイトルと一致した場合だけ再利用する。番号未指定の同名Issueが存在する場合は停止する。初期構築対象内のタイトル重複もIssue作成前に拒否する。

Pythonテンプレートには長いIssue本文例を置かない。初期起票用の本文は `references/issue-authoring.md` の `Issue本文テンプレート` をもとに、対象リポジトリの仕様、設計、README、文書へのコミット固定URLを入れて作る。

初期構築後にIssueを追加する場合は、既存の親Issue、sub-issue、blocked by / blocking、Milestoneを確認してから `references/issue-authoring.md` の手順で個別に追加する。

# 選択した正本への値設定

組織Issue Typeを正本にした場合は、Issue作成後にリポジトリで利用できる実際のType名を設定する。

```bash
gh issue edit ISSUE_NUMBER --repo OWNER/REPO --type "TYPE_NAME"
gh issue view ISSUE_NUMBER --repo OWNER/REPO --json number,issueType
```

組織Issue Fieldを正本にした場合は、Issue Field Values REST APIの `POST` で対象項目だけを追加・更新する。`PUT` はそのIssueの既存項目値をすべて置き換えるため、一括作成では使わない。

```json
{
  "issue_field_values": [
    { "field_id": 123, "value": "p2-high" },
    { "field_id": 456, "value": 3 }
  ]
}
```

```bash
gh api --method POST \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "repos/OWNER/REPO/issues/ISSUE_NUMBER/issue-field-values" \
  --input issue-field-values.json

gh api --method GET \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "repos/OWNER/REPO/issues/ISSUE_NUMBER/issue-field-values" \
  -F per_page=100
```

Project独自項目を正本にした値だけを、後述の `updateProjectV2ItemFieldValue` で設定する。同義の値を複数の正本へ書かない。一括作成テンプレートはこの分岐を全Issueに適用し、`verify` で各保存先から値を読み戻す。

# sub-issue / 依存関係の代替操作

`gh issue edit --parent`、`--add-sub-issue`、`--add-blocked-by`、`--add-blocking` が使える場合は高水準コマンドでよい。

```bash
gh issue edit CHILD_NUMBER --repo OWNER/REPO --parent PARENT_NUMBER
gh issue edit ISSUE_NUMBER --repo OWNER/REPO --add-blocked-by BLOCKER_NUMBER
```

大量作成時にこれらのコマンドが使えない、または冪等再実行で扱いにくい場合はGraphQLへ切り替える。まずIssueのnode IDを読む。

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

既に同じ関係がある場合、GitHubは重複系の検証エラーを返す。初期構築の再実行では、操作別に既知の重複エラーだけを警告として扱う。重複と権限・スキーマエラーが混在する場合を含め、その他は安全側に停止する。`apply` 後は全対象Issueの `parent` と `blockedBy` を再取得して一致を確認する。

# Project項目の追加と値設定

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

Project項目値はGraphQLで設定する。

単一選択:

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

テキスト:

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

日付:

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

大量設定では `assets/project-bootstrap-template.py` をコピーまたは一時ファイルへ展開し、対象リポジトリ用に編集する。Project項目は `assets/project-fields.json`、ビューは `assets/project-views.json` を読み込ませる。Issue入力は次のどちらか一方に統一する。

- 少数ならコード内の `ISSUES` を編集する。`body` は `dedent("""...""").strip()` で書く。
- 多数なら `assets/backlog.flat.json` を複製し、全サブコマンドへ同じ `--backlog PATH` を渡す。`parent_title` と `blocked_by_titles` はそれぞれ `parent` と `blocked_by` へ変換される。未対応項目、欠落項目、不正なJSONはGitHubへ接続する前に拒否される。

どちらも本文の構成は `references/issue-authoring.md` を正とする。型別の必須節、内容、構造化項目や依存関係の重複禁止、コミットSHAへ固定した参照ドキュメントをGitHubへ接続する前に検証する。

`plan` の `blockers` が空であることを確認してから `apply` する。確認文字列は設定したリポジトリとProject番号そのものを使う。

```bash
python project-bootstrap.py apply \
  --backlog backlog.flat.json \
  --confirm "OWNER/REPO#PROJECT_NUMBER"
```

既存項目の安全なメタデータ更新も承認した場合だけ、`apply` にも同じオプションを付ける。

```bash
python project-bootstrap.py apply \
  --update-existing-fields \
  --confirm "OWNER/REPO#PROJECT_NUMBER"
```

`apply` 出力のIssue番号、URL、Project項目IDは実行記録として保存し、再実行前に `ISSUES` または初期Issue一覧JSONの各 `number` へ反映する。途中失敗時はタイトル照合で続行せず、出力とGitHub実状態を読み、明示番号を設定して `plan` から再開する。

# Projectビュー

ProjectビューはREST APIで作成できる。`gh project` に作成サブコマンドがなくても、UIだけの作業として扱わない。`assets/project-views.json` をビュー名、レイアウト、フィルターの機械可読な正本にし、一括作成テンプレートの `plan`、`apply`、`verify` へ含める。同名ビューのレイアウトまたはフィルターが異なる場合や標準外ビューがある場合は、上書き・削除せず停止する。標準外ビューは内容を確認し、UIで残すか整理するかを決める。

作成APIは `name`、`layout`、`filter`、table/boardの数値項目IDによる `visible_fields` を受け付ける。組織Issue FieldとProject項目で表示項目IDが変わるため、一括作成テンプレートは名前、レイアウト、フィルターだけを作成する。表示項目、グループ化、並び替え、切り分けは作成後にUIで設定する。roadmapへ `visible_fields` は渡さない。

まず既存ビューを読み、同名ビューの設定が正本と一致することを確認する。RESTにはビュー一覧・更新APIがないため、読み取りと検証はGraphQLを使う。

```bash
gh api graphql \
  -F projectId=PROJECT_ID \
  -f query='query($projectId: ID!) {
    node(id: $projectId) {
      ... on ProjectV2 {
        views(first: 100) {
          nodes { id number name layout filter }
          pageInfo { hasNextPage }
        }
      }
    }
  }'
```

組織所有Projectでは、Projects組織書き込み権限を持つトークンで次の形を使う。

```bash
gh api --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  "orgs/ORG/projectsV2/PROJECT_NUMBER/views" \
  -f name='かんばん' \
  -f layout='board' \
  -f filter='is:issue is:open status:inbox,triaged,ready,in-progress,in-review,blocked'
```

個人所有ProjectはAPI経路を `users/USER_ID/projectsV2/PROJECT_NUMBER/views` へ変える。この経路はGitHub Appトークンとfine-grained PATに対応しないため、現在の `gh auth token` の種類を確認し、401/403を権限不足として握りつぶさない。

Projectには次の4ビューだけを作る。

- `かんばん`
- `WBS/ロードマップ`
- `マージ候補`
- `Velocity`

各ビューの目的、表示項目、UIで行うグループ化・並び替えは、`assets/.github/project/views.md` を対象リポジトリの `.github/project/views.md` へコピーして正本にする。Project項目はIssueとし、PRの承認や必須検査はProjectの絞り込み条件へ書かずPR自体で確認する。

# 検証

`apply` は完了直後に `verify` を自動実行する。別の処理で再検証する場合は、`apply` 出力のIssue番号を `ISSUES` または初期Issue一覧JSONへ保存し、`apply` と同じ入力を指定する。

```bash
python project-bootstrap.py verify --backlog backlog.flat.json
```

`verify` は `plan` で選んだ組織Issue Type / Issue FieldとProject項目の定義・値、4ビューの名前・レイアウト・フィルター、Milestoneと期限、全Issueの同一性、全 `parent` / `blockedBy`、全Issue URLに対応するProject項目を読み取りだけで確認する。代表Issueだけの抜き取り確認で完了扱いにしない。

Project項目:

```bash
gh project field-list PROJECT_NUMBER --owner OWNER --format json --limit 100
```

Project内のIssue:

```bash
gh project item-list PROJECT_NUMBER --owner OWNER --format json --limit 100
```

代表`epic`のsub-issue:

```bash
gh issue view EPIC_NUMBER \
  --repo OWNER/REPO \
  --json number,title,subIssues,subIssuesSummary
```

代表Issueの親子・依存関係:

```bash
gh issue view ISSUE_NUMBER \
  --repo OWNER/REPO \
  --json number,title,parent,blockedBy,blocking
```

Milestone:

```bash
gh api repos/OWNER/REPO/milestones --method GET -f state=all -F per_page=100
```

リポジトリ側のビュー説明:

```bash
test -f .github/project/views.md
```

最後に、実際に作った件数を数字で確認する。

```text
Milestone: First Releaseが存在する
メタデータ: planで選んだ組織Issue Type / Issue FieldとProject項目
Projectビュー: assets/project-views.jsonの4ビュー
Project項目: 作成予定のWBS Issue数と一致する
Issue: 既存Issueを含む場合があるため、対象Issue番号で確認する
```
