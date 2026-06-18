# Project views の設定例

# カンバン

- レイアウト: board
- グループ化: Status
- 並び順: Priority desc, Risk desc
- 表示field: Type, Scope, Priority, Agent Tier, Assignee, Branch

# 着手待ち

- レイアウト: table
- filter: `status:Ready -is:blocked`
- グループ化: Agent Tier
- 並び順: Priority desc, Risk desc, updated asc

# 現在の注力

- レイアウト: table または board
- Project field filter: Status = Ready, In Progress, In Review; Priority = P2-high, P3-critical
- グループ化: Status

# レビュー待ち

- レイアウト: table
- filter: `status:In Review`
- 並び順: Risk desc, Priority desc, updated asc

# 停止中

- レイアウト: table
- filter: `status:Blocked`
- 表示field: blocked by, blocking, Risk, Assignee, updated

# frontier向け

- レイアウト: table
- Project field filter: Agent Tier = agent:frontier; Status = Ready, In Progress, In Review

# merge queue候補

- レイアウト: table
- filter: `status:In Review is:pr review:approved`

# 処理量

- レイアウト: table
- filter: `status:Done closed:>=YYYY-MM-DD`
- グループ化: Scope または Agent Tier
