# Priority / Size / Complexity / Risk / Agent Tier基準

この基準は、複数人・複数agentが迷わず同じ分類をできることを目的にする。

# Priority

Priorityは重要度。0が最低、3が最高。P1-normalとP2-highが通常作業の大半を占める。

## P0-optional

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

## P1-normal

通常優先度。計画に入れる価値はあるが、順序を柔軟に変えられる。

判定基準:

- 機能完成、品質、開発体験に明確な価値がある。
- 他Issueを強くblockしない。
- 期限が近くない。
- agentの空きに応じて並列に流せる。

## P2-high

高優先度。現在の開発目標、milestone、releaseに直接効く。

判定基準:

- 主要機能の完成に必要。
- 後続Issueをblockしている。
- レビューや設計判断を早めに通す必要がある。
- current focusに入れる候補。

## P3-critical

最重要。放置するとmain、release、利用者、セキュリティ、データ、開発全体に重大影響がある。

判定基準:

- mainが壊れている。
- releaseを止めている。
- データ破壊、認証、漏洩、重大障害に関係する。
- 多数のIssueをblockしている。
- 直ちに人間ownerが確認する必要がある。

P3-criticalは少数に保つ。常時P3-criticalが多い場合、計画か品質ゲートが壊れている。

# Size

Sizeは変更量・レビュー量・PRの大きさ。難しさではない。

## S0-tiny

極小。数分〜30分程度。差分は小さく、レビューも即時。

目安:

- 1〜2ファイル。
- 50行未満。
- テスト追加不要、または既存テストで十分。
- 文言、設定、軽微な修正。

## S1-small

小。1PRとして理想的な大きさ。

目安:

- 1〜5ファイル。
- 50〜250行程度。
- 受け入れ条件が1〜4個。
- テストまたは確認手順が明確。

## S2-medium

中。標準的だがレビューに注意が必要。

目安:

- 5〜12ファイル。
- 250〜800行程度。
- UI/API/DBなど複数箇所にまたがるが、境界は明確。
- 受け入れ条件が5〜7個。

## S3-large

大。原則分割を検討する。

目安:

- 12ファイル超。
- 800行超。
- 受け入れ条件が8個以上。
- UI、DB、API、infraを同時に広く変える。
- reviewが重すぎる。

S3-largeをそのまま実装するのは例外。先にcontract issue、spike、sub-issue分割を検討する。

# Complexity

Complexityは設計難度・未知性・推論量。

## C0-none

ほぼ判断不要。

- 既存パターンのコピー。
- 仕様が完全に明確。
- 失敗時の影響範囲が狭い。

## C1-simple

低複雑度。

- 既存の設計に沿えば実装できる。
- 迷う分岐が少ない。
- 主要な設計判断は不要。

## C2-moderate

中複雑度。

- 複数設計案の比較が必要。
- interfaceやデータ構造の整合を取る必要がある。
- agentが誤解しやすい非スコープがある。
- 既存実装との互換性を見ながら進める。

## C3-complex

高複雑度。

- 仕様自体に未確定要素がある。
- architecture、schema、security、concurrency、migrationなどの判断が必要。
- 失敗した場合の手戻りが大きい。
- 先にspikeを作るべき。

# Risk

Riskは壊した場合の影響度。

## R0-none

ほぼ無リスク。

- docs、コメント、表示文言など。
- mainや利用者データに影響しない。

## R1-safe

低リスク。

- 局所的な変更。
- rollbackが簡単。
- テストで十分検知できる。

## R2-moderate

中リスク。

- DB、API、認証、課金、CI、release、performanceの一部に影響する。
- 既存利用者や他PRと競合する可能性がある。
- merge_group CIとレビューが重要。

## R3-dangerous

高リスク。

- main破壊、データ破壊、セキュリティ、不可逆migration、大規模infra、release停止に関係する。
- 人間review ownerを必ず明示する。
- frontier agentまたは人間主導を使う。

# Agent Tier

Agent Tierは必要な推論・検証・慎重さの層。具体モデル名ではない。

## agent:fast

適用条件:

- ComplexityがC0-noneまたはC1-simple。
- RiskがR0-noneまたはR1-safe。
- SizeがS0-tinyまたはS1-small。
- 非スコープが単純。

向く作業:

- docs修正。
- 小さなfix。
- 単純なtest追加。
- 既存patternの反復。

## agent:standard

適用条件:

- ComplexityがC2-moderate以下。
- RiskがR2-moderate以下。
- SizeがS1-smallまたはS2-medium。
- 通常のfeature/fix/refactor。

向く作業:

- 一般的な機能実装。
- 小〜中規模UI/API/DB変更。
- テスト追加を含むPR。

## agent:frontier

適用条件:

- ComplexityがC3-complex、またはRiskがR3-dangerous。
- 設計判断、セキュリティ、migration、concurrency、merge queue、CI基盤に関係する。
- 誤実装の手戻りが大きい。

向く作業:

- architecture設計。
- spikeからfeatureへの分解。
- 高リスクmigration。
- 複雑な障害調査。

# 自動判定式

形容詞は読みやすさのために付ける。自動判定やsortでは、`C2-moderate` の `2` のように数値prefixだけを比較する。

```text
max(Complexity.number, Risk.number) <= 1 かつ Size.number <= 1 -> agent:fast
max(Complexity.number, Risk.number) == 2 または Size.number == 2 -> agent:standard
max(Complexity.number, Risk.number) == 3 または Size.number == 3 -> agent:frontier候補
```

ただし、SizeだけがS3-largeでComplexity/Riskが低い場合は、frontier agentへ投げるよりIssue分割を優先する。
