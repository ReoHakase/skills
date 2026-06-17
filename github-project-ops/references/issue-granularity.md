# Issue粒度基準

# branchable issueの条件

branchable issueは、1 branchと1 PRを持てるIssueである。次をすべて満たす。

- 1 PRで閉じられる。
- 受け入れ条件が第三者に判定可能。
- titleが自然な日本語で、何が変わるか分かる。
- TypeとScopeはProject fieldに入っている。
- 主componentが1つ、またはinterface境界が1つ。
- 非スコープが明記されている。
- blocked by / blockingが明記されている。
- テストまたは確認手順がある。
- Issue本文だけでagentが作業できる。

# 分割すべき兆候

- 受け入れ条件が8個以上。
- 変更ファイルが12個を超える見込み。
- UI、DB、API、infra、docsを同時に広く変更する。
- 仕様未確定の判断が複数残っている。
- 複数agentが並列実行できる作業を1 Issueに押し込んでいる。
- review focusが3つ以上ある。
- 失敗時のrollbackが複数段階になる。

# epic

epicは親Issue。実装branchを持たない。

書くべき内容:

- 目的
- 成功条件
- sub-issue一覧
- 主要依存関係
- 完了条件

# spike

spikeは未確定要素を減らすための調査Issue。

成果物:

- 調査結果
- 採用案
- 棄却案
- 後続Issue案
- 実装しない判断の理由

spikeはコード変更を含んでもよいが、本番機能を完成させるIssueではない。

# bug

bug Issueには必ず再現条件を書く。

- 期待動作
- 実際の動作
- 再現手順
- 環境
- ログ
- 影響範囲
- 修正の受け入れ条件

# debug log / chat / inquiryからの起票

ログ、チャット、お問い合わせからIssueを起こす場合は、最初はStatusをInboxにする。

SourceはProject fieldに入れる。Issue本文にはSourceなどのProject field assignmentを書かない。

Issue本文に必ず書く:

- 原文または要約
- 影響しているユーザーまたは機能
- 再現性
- 緊急度の仮判定
- 次のtriageで確認すべきこと

Inboxから直接In Progressにしない。必ずTriagedまたはReadyを通す。
