# Lifecycle comment の記入済み例

このfileはgeneric templateではない。状態別の記入済み例として読む。canonical templateは `references/message-templates.md` を使う。

# Inbox

📥 流入内容を整理した。

流入元: 問い合わせフォームから、検索結果がなぜ一致したか分からないという報告があった。 (https://example.com/form/post/123)
要約: 検索結果カードに動画全体の情報だけが出ており、一致したシーンの説明やセリフが見えない。
影響: 検索結果を見ても、目的の場面かどうか判断しづらい。
次に確認すること: 一致シーンの説明、タグ、セリフ抜粋をAPIから取得できるか確認する。

# Triaged

🔎 トリアージした。

判断根拠:

- 1つのカード表示改善として分離できる。
- 検索rankingやプレイヤーの挙動は変更しなくてよい。

未確定事項: 一致シーンの説明がない既存データのfallback表示を決める必要がある。
Readyへ進めない理由: fallback表示が未決定。

# Ready

🟢 Ready状態になった。

確認済み:

- 受け入れ条件が判定可能
- 非スコープが明確
- 確認手順がある
- 作業開始を止めるblockerがない

補足: fallbackは「未取得」と表示する方針に決定済み。

# In Progress

🚧 作業中の補足。

(担当者変更に備えて、作業中に悩んだこと、メモ、ログなどをタスクに合わせて必要に応じて残す。)

# In Review

👀 特筆事項がないため、In Review commentは省略する。

(基本的には書かない。PRやGitHub metadataで分かる内容をcommentへ重複させない。)

# Blocked

⛔ ブロックに変更した。

理由: fixtureに一致シーンの説明がないケースが不足しており、fallback表示確認ができない。
解除できる人: @fixture-owner
依存: fixture追加PR https://github.com/example/search-ui/pull/219
次の確認タイミング: fixture追加PRのcheck完了後。

# Unblocked / resume

🔓 ブロックが解消した。

解消内容: fixtureに一致シーン説明なしのケースが追加された。
戻す状態: review再開。
再確認したこと: fallback表示の確認手順をPR本文に反映済み。

# Blocked: upstream PR待ち

⛔ ブロックに変更した。

理由: 依存ライブラリの不具合修正がupstreamでreview中で、mergeされるまでこちらの実装を確定できない。

解除できる人: upstream maintainer https://github.com/upstream-maintainer

依存:

- upstream修正PR: https://github.com/example/video-search-sdk/pull/482
- Issue: https://github.com/example/video-search-ui/issues/123

次の確認タイミング: upstream PRのreview更新後、または翌営業日。

# Unblocked / resume: upstream PR merge

🔓 ブロックが解消した。

解消内容: upstream修正PRがmergeされ、依存ライブラリ側の修正方針が確定した。
戻す状態: 作業再開。
再確認したこと: こちらの実装方針がupstreamの修正内容と矛盾していない。依存バージョン更新の要否をPR本文の確認手順に反映済み。

- こちらの実装方針がupstreamの修正内容と矛盾していない。
- 依存バージョン更新の要否をPR本文の確認手順に反映済み。

# Blocked: Figma確定待ち

⛔ ブロックに変更した。

理由: 検索結果カードの密度とfallback表示の見た目がFigma上で未確定のため、UI実装を確定できない。
解除できる人: Figma owner: https://teams.microsoft.com/l/person/48:notes/00000000-0000-0000-0000-000000000000
依存: Figma design: https://www.figma.com/design/AbCdEfGhIj/Search-Results?node-id=12-34
次の確認タイミング: Figmaの該当frameが確定した後。

# Unblocked / resume: Figma確定

🔓 ブロックが解消した。

解消内容: Figma上で検索結果カードの密度、fallback表示、長い商品名の折り返し方針が確定した。
戻す状態: 作業再開。
再確認したこと:

- Issue bodyの受け入れ条件を確定デザインに合わせて更新済み。
- 古い表示方針はdetailsに移して、現在の確認手順と混ざらないようにした。
