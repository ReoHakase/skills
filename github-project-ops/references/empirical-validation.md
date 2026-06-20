# Empirical validation

このskillは、曖昧さを減らすために実例で検証しながら改善する。

# 検証手順

1. 代表的なIssue作成シナリオを用意する。
2. skillだけを読んだagentにIssueを作らせる。
3. 別agentまたは人間が検証する。
4. 失敗を分類する。
5. skill本文、references、assetsを修正する。
6. 同じシナリオで再実行する。

# 評価観点

- Issue titleは自然な日本語か。
- TypeとScopeがtitleではなくfieldにあるか。
- Milestone due dateを先に確認してからIssue/WBS Forecastを組んでいるか。
- Issue ForecastからMilestone期限を逆算していないか。
- bootstrap既定Milestoneが期限付きの `First Release` だけになっているか。
- Size/Complexity/Risk/Agent Tierが基準通りか。
- 独自WBS番号やkeyを作っていないか。
- sub-issueとblocked by/blockingを混同していないか。
- `ready` を仕様確定済みの意味で使っていないか。
- 未解決の `blocked by` があるIssueを `ready` にしていないか。
- `blocked` を `blocked by` / `blocking` からの自動同期状態として扱っていないか。
- external blockerをdummy Issueへ押し込まず、blocked commentにURL付きで記録しているか。
- 直列依存するIssue同士のForecast Start / Forecast Endが重なっていないか。
- epic Issueを作業開始対象として `ready` にしていないか。
- 作業開始時にAssignee、Agent Harness、Agent Modelが設定されるか。
- Issue/PR本文や作業開始コメントにProject field assignmentを書いていないか。
- PR本文に具体モデル名を書いていないか。
- PR本文にclosing keywordがあるか。
- merge queue前提のCI workflowがあるか。

# 失敗分類

- Missing context: Issue本文だけで作業できない。
- Oversized issue: 1PRで閉じられない。
- Wrong dependency: 親子関係と順序依存を混同している。
- Wrong readiness: ready、blocked、blocking、blocked byの意味を混同している。
- Wrong blocker source: external blockerをIssue dependencyへ無理に変換している。
- Overlapping forecast: 直列依存するIssueの計画期間が重なっている。
- Wrong title: Conventional Commit風titleにしている。
- Wrong milestone deadline: Issue ForecastからMilestone期限を推測している。
- Wrong estimation: P/S/C/R/Agent Tierの基準違い。
- Missing ownership: 作業開始時にAssigneeまたはReviewer Ownerがない。
- Metadata leakage: Issue/PR本文や作業開始コメントにProject field assignmentを書いている。
- Model leakage: Issue/PR本文に具体モデル名を書いている。
- Merge policy mismatch: squash/rebase/linear history前提になっている。

# 合格条件

- 新しいagentがskillだけで同じ運用を再現できる。
- GitHub操作がMCPまたは `gh` の明示手順で再現できる。
- templatesが低コンテクストである。
- 人間がProject viewで進捗を把握できる。
