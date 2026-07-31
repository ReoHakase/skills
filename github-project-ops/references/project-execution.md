# Projectでの実行管理

Projectの`Status`、`Agent Run`同期、WIP上限、実行Waveを扱うときに読む。

## 責務の境界

Project側が決めるのは、Project内での状態表示、容量、投入順、`Forecast`である。
次の情報は`github-issue-pr-ops`で確定した結果だけを受け取る。

- `Assignee`、linked branch、open PRの整合と着手情報
- Issue本文、受け入れ条件、非スコープ、確認手順、変更予定ファイル
- branchと`worktree`の対応、PR本文、レビュー契約、マージ方法
- sub-issue、`blocked by` / `blocking`、Milestoneと期限

Project側で着手者や着手対象を決めない。Issue/PR側から、Issue番号、URL、node ID、
`Assignee`、linked branch、open PRを含む確定済み着手情報を受け取る。現在の実行環境が
公開可能なIDまたはタスクURLを明示した場合は、任意の`Agent Run`追跡値として別に受け取る。open PRがまだない段階は、
欠落と区別できるよう「なし」と明記された情報だけを受け付ける。GitHub MCPまたは`gh`で現在値を
再取得し、同じIssue、担当、branch、PRを示す場合だけ同期する。

複数の`Assignee`、linked branch、open PR、または着手情報があり対応を一意に確認できない場合、
識別子が一致しない場合、現在のGitHub状態と矛盾する場合は更新せず停止する。Project側では、
並び順、時刻、既存の`Agent Run`などを使って採用候補を決めない。差異を列挙して
`github-issue-pr-ops`へ返し、整合した着手情報が改めて確定するまで待つ。

整合しているとは、確定済み着手情報の担当ログインがIssueの`Assignee`に含まれ、対象branchが
Issueのlinked branchであり、open PRがある場合はそのhead branchとIssue参照が一致する状態を指す。
GitHub MCPで確認できない場合は、少なくとも次を実行し、出力を同じIssue番号とbranch名で照合する。

```bash
gh issue view ISSUE_NUMBER --repo OWNER/REPO --json id,number,url,assignees,state
gh issue develop --list ISSUE_NUMBER --repo OWNER/REPO
gh pr list --repo OWNER/REPO --state open --limit 1000 \
  --json id,number,url,headRefName,headRepository,isDraft,closingIssuesReferences
```

Milestone期限、sub-issue、依存関係、変更予定ファイル、branch、PR状態は、容量と日程を
計算するための読取入力である。このスキルから作成、編集、解除しない。

## Statusの意味

`Status`はProject上で次に可能な操作を示す。IssueやPRの契約を置き換えない。

| `Status`      | Project上の意味                                                                          |
| ------------- | ---------------------------------------------------------------------------------------- |
| `inbox`       | Projectへ流入したが、Issue/PR側のトリアージ結果をまだ受け取っていない                    |
| `triaged`     | 分類結果を受け取ったが、開始条件または投入順が確定していない                             |
| `ready`       | 開始条件を満たす末端Issue。`Agent Run`は空で、容量があれば投入候補にできる               |
| `in-progress` | 整合を確認済みの着手情報があり、実装、調査、Draft PR、レビュー修正など実行者の操作が残る |
| `in-review`   | PRがレビュー可能で、レビュー、CI、共有環境検証、またはマージを待つ                       |
| `blocked`     | 実行者の局所操作では解消できない阻害要因により進められない                               |
| `done`        | Issue/PR側で完了条件を満たしたと確定した                                                 |
| `canceled`    | Issue/PR側で実行しないと確定した                                                         |

容量不足、変更競合、単なるレビュー待ち、CI実行中、マージ待ちを`blocked`にしない。
容量待ちと変更競合待ちは、開始条件を満たす限り`ready`のまま実行Waveから外す。
修正可能なレビュー指摘、CI失敗、マージ競合は`in-progress`へ戻す。

`needs-info`や`ready-to-merge`などの値を追加して途中状態を表さない。レビュー、CI、共有環境、
マージ待ちはPRの実状態を読み、個別のWIPとして数える。

## 着手情報と状態の同期

同期前に対象Issue、Projectアイテム、現在の`Status`と`Agent Run`、`Assignee`、linked branch、
open PRを再取得する。同期後も同じ対象を再取得し、計画値と完全一致することを確認する。

| Issue/PR側で確定した状態                   | `Agent Run`                                  | `Status`                                                  |
| ------------------------------------------ | -------------------------------------------- | --------------------------------------------------------- |
| 新規流入                                   | 空欄                                         | `inbox`                                                   |
| トリアージ完了。ただし開始条件は未充足     | 空欄                                         | `triaged`                                                 |
| 開始条件を満たした末端Issue                | 空欄                                         | `ready`                                                   |
| 着手情報の整合を確認                       | 提示値があれば記録。なければ空欄             | `in-progress`                                             |
| 実装、調査、Draft PRの継続                 | 既存値を維持。空欄でも補完しない             | `in-progress`                                             |
| PRをReady for reviewへ変更                 | 既存値を維持。空欄でも補完しない             | `in-review`                                               |
| 対応可能なレビュー指摘、CI失敗、マージ競合 | 既存値を維持。空欄でも補完しない             | `in-progress`                                             |
| 外部の阻害要因で停止                       | 継続する着手情報が確定済みなら既存値を維持   | `blocked`                                                 |
| 阻害要因が解消                             | 未着手なら空欄。継続確認済みなら既存値を維持 | `ready`、`in-progress`、`in-review`のうち確定した再開地点 |
| 担当変更後の着手情報を確認                 | 新しい提示値があれば更新。なければ空欄       | `in-progress`または`in-review`                            |
| 着手の取り下げ                             | 空欄                                         | 開始条件に応じて`ready`、`triaged`、`blocked`             |
| 完了                                       | 最終実行IDがあれば追跡用に維持               | `done`                                                    |
| 中止                                       | 空欄                                         | `canceled`                                                |
| 完了または中止の取り消し                   | 空欄                                         | `triaged`                                                 |

Project側は、着手情報の自然文から実行IDや遷移先を補完しない。追跡値が提示されなければ、
`Agent Run`を空欄のまま`Status`だけを同期してよい。提示値と既存値が異なる場合は、確認済みの
担当変更でない限り上書きしない。同じ対象について確定済み情報とGitHubの実状態が矛盾する場合は、
古い情報を適用せず停止する。`Agent Run`と`Status`の両方を更新する計画で一方だけ失敗した場合は
成功扱いにせず、再取得した実状態から同期計画を作り直す。

## epicの集約

`epic`は原則として`Agent Run`を持たず、`ready`または実行Waveへ入れない。Project上の
`Status`は、Issue/PR側で確定したepic自体の判断と、必須の末端Issueの状態を次の順で集約する。

1. epic自体の中止が確定していれば`canceled`。
2. epicの完了が確定し、必要な末端Issueがすべて`done`、または不要化・置換を承認済みの
   `canceled`なら`done`。
3. 未完了の必須Issueがあり、実行可能または実行中の末端Issueが0件で、実際の阻害要因が
   すべての進行を止めていれば`blocked`。
4. 必須の末端Issueに`in-progress`、`in-review`、`done`が1件以上あれば`in-progress`。
5. 分割と分類が確定し、まだ開始していなければ`triaged`。
6. それ以外は`inbox`。

`canceled`の末端Issueを自動的に達成扱いにしない。不要化または置換の承認はIssue/PR側から
受け取る。epicの`Effort`と`Estimate Confidence`は空欄にし、末端Issueの`Effort`だけを
日程計算へ使う。epicの`Forecast Start`と`Forecast End`は必要な末端Issue全体を包む期間にする。

## WIPの数え方

Project運用設定から各上限を読み、設定が存在しないことを確認できた場合だけ各1として安全側に扱う。権限不足や取得失敗で未設定か判定できない場合は初期値を使わず、実行Waveと書き込みを停止する。`Effort`は作業量、WIPは同時処理数であり、`Size`を合計して容量へ換算しない。

| 枠         | 消費中と数える条件                                                                                                    |
| ---------- | --------------------------------------------------------------------------------------------------------------------- |
| 実装       | 整合を確認済みの着手情報があり、実装、調査、Draft PR、レビュー修正、修正可能なCI失敗またはマージ競合へ対応中          |
| `worktree` | Issue/PR側でlinked branchとの対応が確定した独立`worktree`を実行役が使用中。存在だけでなく着手情報と実行状態を照合する |
| レビュー   | Ready for reviewのPRに未承認または未解決のレビュー会話がある                                                          |
| 重いCI     | Project運用設定で重い検査と指定した実行が待機中または実行中                                                           |
| 共有環境   | 排他的な共有試験環境、共有テストデータ、実機などを確保している                                                        |
| マージ待ち | 承認と必須ステータスチェックが完了し、設定済みのキュー、自動、または手動統合を待つ                                    |

同じIssueが同時に複数の実資源を使う場合は、それぞれの枠で1件と数える。通常の軽いCIは
重いCI枠へ数えない。重いCIと共有環境を単一上限で運用する設定なら、両方を同じ枠へ合算する。

実装へ使える件数は`min(Agent枠上限, worktree枠上限)`とする。停止済みの`worktree`を
Project側の判断だけで削除したり、`Assignee`、linked branch、open PRを変更したりしない。
担当変更または着手の取り下げが必要なら、対象Issueの番号、URL、node IDと理由を
`github-issue-pr-ops`へ返し、整合した状態が確定するまで待つ。

## 実行Waveの選定

実行Waveは投入候補の計画であり、着手の確定でも`Status`の変更でもない。Waveへ選んだだけでは
`Agent Run`、`Assignee`、branch、`worktree`、PRを変更しない。

1. Project項目、各WIPの実使用数、関連PR、Milestone期限、sub-issue、依存関係、
   変更予定ファイルを再取得する。
2. `ready`で`Agent Run`が空欄の末端Issueから、未解決の実依存があるものを除く。
3. 依存関係に自己参照または循環があれば選定を止め、Issue/PR側へ関係修正の候補を返す。
4. 候補を次の安定した順序で並べる。
   1. `Priority`の高い順。
   2. Milestone期限の早い順。期限なしは最後。
   3. 下流の未完了末端Issueを含む残りクリティカルパスが長い順。
   4. Issue番号の小さい順。
5. 実装、`worktree`、レビュー、重いCI、共有環境、マージ待ちの上限と変更競合を満たす候補を
   `Wave 1`から順に配置する。
6. Issue番号、URL、node ID、候補Wave、選定理由、見送り理由、再評価条件を出力し、
   作業開始の候補として`github-issue-pr-ops`へ返す。

同じ入力、同じProject項目、同じ容量なら同じWaveになるようにする。手動で順番を変える場合は、
元の順位と理由を計画へ残す。前のWaveの全件完了を機械的に待たず、実依存が解消し、必要な枠が
空いた時点で次の候補を選ぶ。

## 容量不足時の停止

次のいずれかを満たす場合、新しいIssueの投入数を0件にする。

- Agent枠または`worktree`枠に空きがない。
- レビューWIPが上限に達している。
- 重いCIまたは共有環境WIPが上限に達している。
- マージ待ちWIPが上限に達している。
- 現在の候補を入れると、予測した下流到着時に上限を超える。

容量不足だけを理由に`ready`から`blocked`へ変えない。`Agent Run`も書かない。見送り対象、
埋まっている枠、現在値と上限、再評価条件を実行Waveの結果へ記録する。着手情報が確定済みのIssueを
容量調整だけで外さない。停止または移管が必要ならIssue/PR側へ候補を返し、担当変更、着手の
取り下げ、中止が確定した後に同期する。

## 再計画

次の変化を検出したら、GitHub上の実状態を再取得して`Forecast`と実行Waveを作り直す。

- 各WIP枠の使用開始または解放
- Issue/PR側で確定した開始、レビュー移行、停止、再開、担当変更、着手の取り下げ、完了、中止
- `Effort`、`Estimate Confidence`、`Priority`、`Complexity`、`Risk`の変更
- Milestone期限、依存関係、sub-issue、変更予定ファイルの変更
- PRのDraft状態、レビュー、CI、共有環境、マージ待ち状態の変更

再配置するのは着手情報が確定していない候補だけとする。進行中Issueの`Assignee`やbranchを
Project側から変更しない。Milestone期限または容量へ収まらない場合は、日付だけを圧縮しない。範囲削減、
期限変更、依存解消、容量追加の候補と影響を示し、Issue/PR側または利用者の決定が確定するまで
実現可能と報告しない。
