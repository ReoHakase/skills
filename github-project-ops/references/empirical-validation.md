# Empirical validation

このskillは、曖昧さを減らすために実例で検証しながら改善する。

# 検証手順

1. 代表的なIssue作成シナリオを用意する。
2. skillだけを読んだagentにIssueを作らせる。
3. 別agentまたは人間が検証する。
4. 失敗を分類する。
5. skill本文、references、examples、scriptsを修正する。
6. 同じシナリオで再実行する。

# 評価観点

- Issue titleは自然な日本語か。
- TypeとScopeがtitleではなくfieldにあるか。
- Size/Complexity/Risk/Agent Tierが基準通りか。
- 独自WBS番号やkeyを作っていないか。
- sub-issueとblocked by/blockingを混同していないか。
- 作業開始時にAssignee、Agent Harness、Agent Modelが設定されるか。
- PR本文に具体モデル名を書いていないか。
- PR本文にclosing keywordがあるか。
- merge queue前提のCI workflowがあるか。

# 失敗分類

- Missing context: Issue本文だけで作業できない。
- Oversized issue: 1PRで閉じられない。
- Wrong dependency: 親子関係と順序依存を混同している。
- Wrong title: Conventional Commit風titleにしている。
- Wrong estimation: P/S/C/R/Agent Tierの基準違い。
- Missing ownership: 作業開始時にAssigneeまたはReviewer Ownerがない。
- Model leakage: Issue/PR本文に具体モデル名を書いている。
- Merge policy mismatch: squash/rebase/linear history前提になっている。

# 合格条件

- 新しいagentがskillだけで同じ運用を再現できる。
- scriptsがdry-run可能。
- templatesが低コンテクストである。
- 人間がProject viewで進捗を把握できる。
