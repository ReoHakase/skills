# Project views example

# Kanban

- layout: board
- group by: Status
- sort: Priority desc, Risk desc
- visible fields: Type, Scope, Priority, Agent Tier, Assignee, Branch

# Ready Pool

- layout: table
- filter: `status:Ready -is:blocked`
- group by: Agent Tier
- sort: Priority desc, Risk desc, updated asc

# Current Focus

- layout: table or board
- Project field filter: Status = Ready, In Progress, In Review; Priority = P2-high, P3-critical
- group by: Status

# Review Queue

- layout: table
- filter: `status:In Review`
- sort: Risk desc, Priority desc, updated asc

# Blocked

- layout: table
- filter: `status:Blocked`
- visible fields: blocked by, blocking, Risk, Assignee, updated

# Frontier Queue

- layout: table
- Project field filter: Agent Tier = agent:frontier; Status = Ready, In Progress, In Review

# Merge Queue Candidates

- layout: table
- filter: `status:In Review is:pr review:approved`

# Velocity

- layout: table
- filter: `status:Done closed:>=YYYY-MM-DD`
- group by: Scope or Agent Tier
