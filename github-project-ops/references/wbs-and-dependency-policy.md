# WBSと依存関係の方針

# WBS番号を使わない

`SJ-1.2.3` のような独自WBS番号は使わない。

理由:

- 動的な分割・統合で番号が壊れる。
- GitHub Issue numberと二重管理になる。
- sub-issueで親子関係を表せる。
- blocked by / blockingで順序依存を表せる。
- Project viewでgrouping、filtering、sortができる。

bootstrap用JSONにも独自keyを置かない。タイトルを一時的な照合キーとして使うため、初期作成ファイル内ではtitleを一意にする。

# sub-issueとdependencyの分離

sub-issue:

- WBS階層を表す。
- あるepicや親featureを構成する子Issueを示す。
- 実行順序は表さない。

blocked by / blocking:

- 実行順序を表す。
- あるIssueが別Issue完了まで開始できないことを示す。
- critical pathを短くするために最小限にする。

# critical pathを短くする

AI agentを使う前提では、並列実行可能なIssue数は無限に近いと仮定する。

最適化目標:

```text
総Issue数を減らすことではなく、完成までの直列Issue数を減らすこと。
```

# 分解手順

1. epicを作る。
2. 共有contractを切る。
3. contract完了後に並列実装Issueを切る。
4. test/docs/observabilityを別Issueにできるなら分ける。
5. C3-complex/R3-dangerousはspikeを先に切る。
6. branch同士の競合が予想される場合は、先にinterface PRを作る。

# 悪い分解

```text
Epic: 検索機能を全部作る
  - 検索UI、API、DB、ranking、test、docsを1Issueで実装する
```

問題:

- 直列化される。
- reviewが重い。
- agentがscopeを広げやすい。
- merge conflictが増える。

# 良い分解

```text
Epic: 検索機能
  - 検索レスポンスのcontractを定義する
  - DB検索repositoryを追加する
  - 検索結果カードを表示する
  - 検索rankingのunit testを追加する
  - 検索UIの操作説明を追加する
```

依存:

```text
検索結果カードを表示する blocked by 検索レスポンスのcontractを定義する
DB検索repositoryを追加する blocked by 検索レスポンスのcontractを定義する
```

contract後はUI、DB、test、docsを並列化できる。
