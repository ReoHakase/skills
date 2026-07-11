# Triage and Agent Tier

この基準は、複数人・複数agentが迷わず同じ分類をできることを目的にする。

# Priority

Priorityは重要度。0が最低、3が最高。p1-normalとp2-highが通常作業の大半を占める。

## p0-optional

やらなくても当面困らない任意作業。

判定基準:

- 利用者価値、開発速度、安定性にほぼ影響しない。
- いつか直したいが、今週・今月にやらなくても問題ない。
- 他Issueをblockしない。
- 作業者が余った時に処理する。

例:

- 表記の軽微な改善。
- 使われていないコメントの整理。
- 任意のdocs追記。

## p1-normal

通常優先度。計画に入れる価値はあるが、順序を柔軟に変えられる。

判定基準:

- 機能完成、品質、開発体験に明確な価値がある。
- 他Issueを強くblockしない。
- 期限が近くない。
- agentの空きに応じて並列に流せる。

## p2-high

高優先度。現在の開発目標、milestone、releaseに直接効く。

判定基準:

- 主要機能の完成に必要。
- 後続Issueをblockしている。
- レビューや設計判断を早めに通す必要がある。
- current focusに入れる候補。

## p3-critical

最重要。放置すると既定ブランチ、リリース、利用者、セキュリティ、データ、開発全体に重大影響がある。

判定基準:

- 既定ブランチが壊れている。
- releaseを止めている。
- データ破壊、認証、漏洩、重大障害に関係する。
- 多数のIssueをblockしている。
- 直ちに人間ownerが確認する必要がある。

p3-criticalは少数に保つ。常時p3-criticalが多い場合、計画か品質ゲートが壊れている。

# Size

Sizeは変更量・レビュー量・PRの大きさ。難しさではない。

## s0-tiny

極小。差分とレビュー観点が少ない。

目安:

- 1〜2ファイル。
- 50行未満。
- テスト追加不要、または既存テストで十分。
- 文言、設定、軽微な修正。

## s1-small

小。1PRとして理想的な大きさ。

目安:

- 1〜5ファイル。
- 50〜250行程度。
- 受け入れ条件が1〜4個。
- テストまたは確認手順が明確。

## s2-medium

中。標準的だがレビューに注意が必要。

目安:

- 5〜12ファイル。
- 250〜800行程度。
- UI/API/DBなど複数箇所にまたがるが、境界は明確。
- 受け入れ条件が5〜7個。

## s3-large

大。原則分割を検討する。

目安:

- 12ファイル超。
- 800行超。
- 受け入れ条件が8個以上。
- UI、DB、API、infraを同時に広く変える。
- reviewが重すぎる。

s3-largeをそのまま実装するのは例外。先にcontract issue、spike、sub-issue分割を検討する。

# Complexity

Complexityは設計難度・未知性・推論量。

## c0-none

ほぼ判断不要。

- 既存パターンのコピー。
- 仕様が完全に明確。
- 失敗時の影響範囲が狭い。

## c1-simple

低複雑度。

- 既存の設計に沿えば実装できる。
- 迷う分岐が少ない。
- 主要な設計判断は不要。

## c2-moderate

中複雑度。

- 複数設計案の比較が必要。
- interfaceやデータ構造の整合を取る必要がある。
- agentが誤解しやすい非スコープがある。
- 既存実装との互換性を見ながら進める。

## c3-complex

高複雑度。

- 仕様自体に未確定要素がある。
- architecture、schema、security、concurrency、migrationなどの判断が必要。
- 失敗した場合の手戻りが大きい。
- 先にspikeを作るべき。

# Risk

Riskは壊した場合の影響度。

## r0-none

ほぼ無リスク。

- docs、コメント、表示文言など。
- 既定ブランチや利用者データに影響しない。

## r1-safe

低リスク。

- 局所的な変更。
- 巻き戻しが簡単。
- テストで十分検知できる。

## r2-moderate

中リスク。

- DB、API、認証、課金、CI、release、performanceの一部に影響する。
- 既存利用者や他PRと競合する可能性がある。
- merge_group CIとレビューが重要。

## r3-dangerous

高リスク。

- 既定ブランチ破壊、データ破壊、セキュリティ、不可逆な移行、大規模基盤、リリース停止に関係する。
- 人間review ownerを必ず明示する。
- frontier agentまたは人間主導を使う。

# Effort

Effortは正のNumberで記録する理想作業時間である。Projectごとに単位を固定し、標準は `ideal-hours` とする。実装、直接確認、テスト、文書更新、通常見込むレビュー修正を含める。CI待ち、外部判断待ち、レビュー待ち、マージ待ちは含めない。

- ブランチ作成型Issue、spike、リポジトリ差分なしIssueには、`ready` へ進める前にEffortを設定する。
- epicのEffortは空欄にする。集計は実行対象の末端Issueだけで行い、親子で二重計上しない。
- Effortは経過時間の約束ではない。Forecastは依存関係、稼働カレンダー、有限WIP、レビュー/CI/マージの予備日を加えて計算する。
- `0`、負数、NaN、Infinityは無効である。

# Estimate Confidence

Estimate ConfidenceはEffortの根拠がどの程度揃っているかを表す。

| 値           | 判定                                                                      |
| ------------ | ------------------------------------------------------------------------- |
| `ec0-low`    | 未知要素が多く、再見積りの可能性が高い。作業境界も揺れるならspikeへ分ける |
| `ec1-medium` | 作業境界は明確だが、一部に未知要素がある                                  |
| `ec2-high`   | 類似実績、変更範囲、確認手順が揃っている                                  |

epicでは空欄にする。末端IssueではEffortと同時に設定する。Estimate Confidenceの変更は再トリアージを起こす。

# Agent Tier

Agent Tierは必要な推論・検証・慎重さの層。具体モデル名ではない。

実行対象の末端Issueにだけ設定し、epicは空欄にする。

# 自動判定式

形容詞は読みやすさのために付ける。自動判定では、`c2-moderate` の `2` のように数値prefixだけを比較し、上から最初に成立した規則を使う。

```text
Size == s3-large
  -> 原則としてIssueを分割する
  -> 例外承認して続行する場合だけagent-frontier

max(Complexity.number, Risk.number) == 3
  -> agent-frontier

max(Complexity.number, Risk.number) == 2 または Size == s2-medium
  -> agent-standard

それ以外
  -> agent-fast
```

Agent Tierだけを手動で上書きしない。より強い段階が必要なら、根拠となるComplexityまたはRiskを先に更新する。`r3-dangerous` はAgent Tierに関係なく人間のReviewer Ownerを必須にする。

`s3-large` を分割せず続行する例外は、人間Reviewer Ownerが理由をコメントへ記録した場合だけ認める。bootstrapでは例外承認を確認できないため、`s3-large` を `ready` にする計画を拒否する。

| Tier             | 代表的な作業                                                    |
| ---------------- | --------------------------------------------------------------- |
| `agent-fast`     | ドキュメント、小さな修正、単純なテスト、既存パターンの反復      |
| `agent-standard` | 通常の機能追加・修正・リファクタリング、小〜中規模UI/API/DB変更 |
| `agent-frontier` | 設計、セキュリティ、移行、並行処理、複雑な障害調査              |

# 再トリアージ

次の変更があればPriorityだけを据え置いて作業を続けず、Size、Complexity、Risk、Effort、Estimate Confidence、Agent Tier、Forecast、依存関係を再判定する。

- 受け入れ条件、非スコープ、変更ファイル、参照contractが実質的に変わった。
- dependencyを追加、削除、置換した。blockerがcanceledになった。
- security、data、migration、権限、外部操作のリスクが判明した。
- EffortまたはEstimate Confidenceを変更した。
- Size、Complexity、Riskの数値境界を越えた。
- ForecastがMilestone期限または容量制約を超えた。
- 作業権が引き継がれた、実行終了を確認した、Issueがreopenされた。
- PR差分がIssue本文の変更ファイルまたは受け入れ条件から大きく外れた。

状態は次のように戻す。

- `ready` 以前は `triaged` へ戻す。
- `in-progress` / `in-review` は進行中のマージ処理を止める。リポジトリ内で修正可能なら `in-progress`、外部判断待ちなら `blocked` にする。
- `done` / `canceled` をreopenする場合は、以前のActual Start / Actual Endを再開コメントへ残して両fieldをclearし、`triaged` にする。Agent Runは新しく作業権を取得するまで空欄にする。
