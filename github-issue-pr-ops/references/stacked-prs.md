# stacked PR

GitHubのStackを設計、作成、同期、レビュー、再構成、マージするときに読む。成果の階層はIssueの親子関係、差分の直列順序はStackのbase関係として分けて扱う。

## 目次

- [関係の意味](#関係の意味)
- [適用条件](#適用条件)
- [正本](#正本)
- [IssueとPRの設計](#issueとprの設計)
- [方式の選択](#方式の選択)
- [標準方式](#標準方式)
- [複数worktree方式](#複数worktree方式)
- [PR本文とレビュー](#pr本文とレビュー)
- [下段変更後の再確認](#下段変更後の再確認)
- [構成変更](#構成変更)
- [マージ](#マージ)
- [GitHub Actions](#github-actions)
- [停止と復旧](#停止と復旧)
- [公式資料](#公式資料)

## 関係の意味

| 関係                  | 意味                               | 正本                    |
| --------------------- | ---------------------------------- | ----------------------- |
| `epic` / sub-issue    | 成果の階層                         | Issueの親子関係         |
| blocked by / blocking | 完了するまで着手できない依存       | Issue dependencies      |
| Stackのbase関係       | branch、レビュー、マージの直列順序 | GitHubのStackメタデータ |

Stackの上段は、下段が未マージでも実装とレビューを進められる。したがって、隣接するPRを機械的にblocked byへ変換しない。下段の成果が完成しなければ上段の実装自体を始められない場合だけ、通常のIssue依存としてblocked byを別途設定する。

## 適用条件

Stackは、1つの変更を独立してレビューできる直列の差分へ分ける場合に使う。独立して並行できる変更は、同じStackへ押し込まず、通常PRまたは別のStackにする。

実行前に次を満たすことを確認する。

- GitHub.comを利用している。
- Gitが2.20以上である。
- `gh`が2.90.0以上で、認証済みである。
- `github/gh-stack`拡張が利用できる。
- 2件以上のPRを、同一リポジトリ内のbranchだけで直列に積む。
- 対象リポジトリへのbranch送信、PR作成、Stack操作の権限がある。
- 複数remoteがある場合、利用するremoteを確定している。

stacked PRはPublic Preview中である。固定した説明より、実行時に利用する版のヘルプを優先する。

```bash
git --version
gh --version
gh auth status
gh stack --version
gh stack COMMAND --help
git config --show-origin --get rerere.enabled
```

機能が未提供、拡張がない、版が不足、または権限がない場合は停止する。利用者の同意なく拡張を導入せず、通常PRへ勝手に切り替えない。同意を得た場合だけ、公式の拡張を導入して互換条件を再確認する。

```bash
gh extension install github/gh-stack
```

`gh stack init`は、版によって`git rerere`を自動で有効にする。未設定または無効の場合は、設定キー`rerere.enabled`、現在値、変更後の`true`、リポジトリ単位で競合解消を記録する影響を示し、この設定変更への個別の明示同意を得る。Stackの作成依頼だけを設定変更への同意とみなさない。同意後はリポジトリ単位で明示的に有効化してから初期化し、同意がなければ標準方式を開始しない。

```bash
git config --local rerere.enabled true
```

## 正本

- Stack番号、PRの順序、各PRのbaseはGitHubのStackメタデータを正本にする。
- `.git/gh-stack`は`gh stack`のローカル操作状態に限り、共同作業の正本にしない。
- 成果の親子関係はIssueのsub-issue、担当はIssueのAssigneeを正本にする。
- Stackと`epic`の所属は、各PRが閉じる末端Issueと、その末端Issueの共通する親Issueから判断する。独自ラベルやPR本文の一覧を正本にしない。
- branchとPRの対応はGitHubのlinked branchとPRメタデータを正本にする。
- PR本文にはその段の責務と確認範囲を書く。Stack番号、全PRの位置一覧、現在の順序は複製しない。
- Issueコメントは引き継ぎと構成変更の判断履歴に限り、通常の同期、リベース、レビュー待ちのたびに増やさない。

標準方式では、現在の専用worktreeからローカル追跡を取得する。

```bash
gh stack view --json
```

どちらの方式でも、書き込み前後にGitHub側のStackを再取得する。GitHub MCPを優先し、利用できなければ実行時のStacks REST API仕様を確認する。複数worktree方式はこの取得だけを使い、ローカル追跡を作らない。

```bash
gh api --method GET "repos/OWNER/REPO/stacks?pull_request=PR_NUMBER"
gh api --method GET "repos/OWNER/REPO/stacks/STACK_NUMBER"
```

Public Preview中はAPIの経路や返却項目が変わり得る。固定した`jq`式で欠落値を無視せず、Stack番号、下段からのPR順、各head branch、各base branchを取得できなければ停止する。標準方式では、ローカル追跡とGitHub側の値が一致することも確認する。

## IssueとPRの設計

1つのStackを、1つの`epic`配下にある末端Issueの直列な実装として設計する。

- すべてのStackを、正確に1つの`epic`へ所属させる。
- 1段を`1末端Issue = 1 branch = 1 PR`に対応させる。
- 各PRは対応する末端Issueだけを自動クローズし、`epic`を閉じない。
- `epic`はbranchを持たず、必須の末端Issueと成果条件を満たした後に閉じる。
- 1つの`epic`は複数Stackと通常PRを含めてよい。
- 1つのStackを複数の`epic`へまたがせない。
- 各段は単独で説明、確認、レビューできる粒度にする。
- `trunk`はStack最下段のbaseで、通常は既定ブランチとする。下段PRのhead branchを直上PRのbase branchにし、最下段PRだけを`trunk`へ向ける。

Stack導入前のIssueは、着手状態で扱いを分ける。

| 元Issueの状態                          | 再整理                                                           |
| -------------------------------------- | ---------------------------------------------------------------- |
| branchもPRもなく、作業が始まっていない | 元Issueを`epic`へ変更し、各段の末端Issueを作る                   |
| branch、PR、または作業済み差分がある   | 新しい`epic`を作り、元Issueを既存PRに対応する末端Issueとして残す |

既存branchやPRがある場合、元Issueを`epic`へ変更して`1 Issue = 1 branch = 1 PR`の対応を壊さない。Issue Typeを変更できない環境では、リポジトリの既存表現を確認し、独自ラベルを自動追加しない。

## 方式の選択

| 方式             | 選ぶ条件                                             | ローカル追跡 |
| ---------------- | ---------------------------------------------------- | ------------ |
| 標準方式         | 1人の調整担当が、1つの専用worktreeで全段を操作できる | 使う         |
| 複数worktree方式 | 段ごとに担当とworktreeを分ける必要がある             | 使わない     |

同じStackの途中で方式を混ぜない。標準方式のbranchを別worktreeで開くと、`gh stack`がbranchを切り替えられず、連鎖的なリベースや同期を安全に完了できない。複数worktree方式では`.git/gh-stack`へ依存する操作を避け、GitHub上のStackを正本として扱う。

## 標準方式

### 担当とworktree

- 1人の調整担当が`epic`と各末端Issueを担当する。
- Stack専用のworktreeを1つ用意し、全段をそこで操作する。
- 同じStackのbranchを別worktreeで開かない。
- 作業前に`git worktree list --porcelain`で、対象branchが他のworktreeにないことを確認する。
- 別worktreeが対象branchを保持している場合は、強制解除せず、利用者が扱いを決めるまで停止する。

### 初期化と段の追加

`trunk`、remote、下段からのbranch順を確定する。`init`、`add`、`checkout`は引数なしで実行せず、対象を明示する。

初期化前に`rerere.enabled`の設定元と有効値を確認する。未設定または無効なら、適用条件にある同意とリポジトリ単位の設定を先に完了する。`init`中の質問へ自動回答しない。

新規Stackの専用worktreeは、確認済みのremote上の`trunk`からdetached状態で先に作る。作成前に予定パスが未使用で、対象branchがどのworktreeにも保持されていないことを確認する。この専用worktreeへ移動してから、最下段の`gh issue develop --checkout`を実行する。

```bash
git fetch REMOTE TRUNK
git worktree add --detach STACK_WORKTREE REMOTE/TRUNK
cd STACK_WORKTREE
```

予定パスの衝突、remote上の`trunk`取得失敗、別worktreeによる対象branch保持があれば、既存worktreeやbranchを強制解除せず停止する。

既存branchをまとめて採用する場合は、各branchが対応する末端Issueのlinked branchまたはopen PRのheadであり、下段から線形であることを先に確認する。

```bash
gh stack init --base TRUNK BOTTOM_BRANCH MIDDLE_BRANCH TOP_BRANCH
gh stack view --json
```

新しい差分を1段ずつ作る場合は、`gh issue develop`で各末端Issueのlinked branchを作り、そのbranchを`gh stack init`または`gh stack add`へ採用する。`gh issue develop`の`--base`はremote branchを参照するため、直下の段をcommitして送信してから次段を作る。

```bash
gh issue develop BOTTOM_ISSUE \
  --repo OWNER/REPO \
  --branch-repo OWNER/REPO \
  --base TRUNK \
  --name BOTTOM_BRANCH \
  --checkout
gh stack init --base TRUNK BOTTOM_BRANCH
git add BOTTOM_PATH
git commit -m "BOTTOM_COMMIT_MESSAGE"
git push REMOTE BOTTOM_BRANCH

gh issue develop MIDDLE_ISSUE \
  --repo OWNER/REPO \
  --branch-repo OWNER/REPO \
  --base BOTTOM_BRANCH \
  --name MIDDLE_BRANCH
gh stack add MIDDLE_BRANCH
git add MIDDLE_PATH
git commit -m "MIDDLE_COMMIT_MESSAGE"
git push REMOTE MIDDLE_BRANCH

gh issue develop TOP_ISSUE \
  --repo OWNER/REPO \
  --branch-repo OWNER/REPO \
  --base MIDDLE_BRANCH \
  --name TOP_BRANCH
gh stack add TOP_BRANCH
git add TOP_PATH
git commit -m "TOP_COMMIT_MESSAGE"
gh stack view --json
```

中段以降は`gh issue develop`でremote上にbranchを作った時点ではcheckoutせず、現在の最上段から`gh stack add BRANCH`で既存名のbranchを採用してcheckoutする。作成後は`gh issue develop --list ISSUE --repo OWNER/REPO`、現在branch、直下branchとのcommit関係を再取得する。branch名の衝突、予期しないbase、linked branchの欠落、`stack add`による採用失敗があれば、branchを作り直さず停止する。

`gh stack add -A`や`-u`へ暗黙の一括ステージングを任せない。段ごとの差分を確認し、通常の`git add PATH`と`git commit`で対応する末端Issueの変更だけをcommitする。最上段は`submit`が送信するため事前送信を必須にしないが、さらに上へ段を追加する場合は先に送信する。

別のStackを取得または選択するときは、Stack番号、PR URL、またはbranchを明示する。数字だけの引数はStack番号とPR番号の解釈が変わり得るため、共同作業の手順ではPR URLを優先する。実行前にGitHub側の構成と既存のローカル追跡を比較し、差があれば`checkout`を実行しない。対話による構成選択を求められた場合も中止する。

```bash
gh stack checkout https://github.com/OWNER/REPO/pull/PR_NUMBER
gh stack view --json
```

### 提出

初回提出は非対話で行い、remoteを明示する。`--open`は付けず、新規PRをDraftのまま作る。

```bash
gh stack submit --auto --remote REMOTE
gh stack view --json
```

`submit`はbranchの送信、PRの作成または更新、base変更、GitHub上のStack更新を順に行うため、途中まで反映されることがある。完了表示や終了コードだけで判断せず、全branch、全PR、GitHub側のStack順序とbaseを再取得し、ローカル追跡とも照合する。

自動生成された各PR本文は、既存のPRテンプレートを満たす完成済みファイルで置き換える。必要ならタイトルも自然な言葉へ直す。

```bash
gh pr edit PR_NUMBER --repo OWNER/REPO --body-file PR_BODY_FILE
gh pr edit PR_NUMBER --repo OWNER/REPO --title "PRタイトル"
```

各段の実装、本文、確認結果が揃ったものだけ、個別にDraftを解除する。

```bash
gh pr ready PR_NUMBER --repo OWNER/REPO
```

### 同期とリベース

通常の同期ではremoteを明示し、疑似端末を割り当てない非対話環境で実行する。実行後にローカルとGitHubの両方を再取得する。

```bash
gh stack sync --remote REMOTE
gh stack view --json
```

`sync`はローカルとGitHub側の構成差を検出して処理を中止しても、成功終了になる場合がある。対話による採用元の選択を求められる状態では実行せず、標準出力の「Stack synced」だけでなく、取得した順序、base、head SHA、remote branchを比較する。「Branches synced」はGitHub上のStackが作成または更新されたことを意味しない。

下段変更後の連鎖的なリベースは、状態を取得してから実行する。

```bash
gh stack rebase --remote REMOTE
gh stack push --remote REMOTE
gh stack view --json
```

実行時の`gh stack rebase --help`と`gh stack push --help`を先に確認する。`push`の途中失敗では自動で再実行せず、remote上の全branchを再取得する。

## 複数worktree方式

### 担当と正本

- `epic`のAssigneeをStack全体の調整担当にする。
- 各末端IssueのAssigneeを、その段のbranch担当にする。
- 各branch担当は、自分のbranch専用worktreeだけを使う。
- GitHub上のStack番号、順序、baseを正本とし、`.git/gh-stack`のローカル追跡は作らない。
- 調整担当だけがStack構成の確定、`link`、全段の再取得、マージ範囲の確認を行う。

### Draft PRの作成とStackへの関連付け

各branch担当は、直下のbranchをbaseにしたDraft PRを作る。最下段だけを`trunk`へ向ける。

```bash
gh pr create \
  --repo OWNER/REPO \
  --base LOWER_BRANCH_OR_TRUNK \
  --head HEAD_BRANCH \
  --draft \
  --title "PRタイトル" \
  --body-file PR_BODY_FILE
```

調整担当は全PR、head、base、対応Issueを確認し、PR番号またはPR URLを下段から上段へ並べてlinkする。`--open`は付けず、remoteを明示する。

```bash
gh stack link --base TRUNK --remote REMOTE BOTTOM_PR MIDDLE_PR TOP_PR
```

`gh stack link`はローカル追跡を使わず、既存PRをGitHub上のStackへ関連付ける。新しいStackでは`--base`を省略しない。既存Stackへ追加するときはこの指定が無視されるため、先にGitHub側の`trunk`を確認する。既存StackのPRを黙って削除しないため、入力漏れや別Stack所属があれば構成変更へ進まず停止する。関連付け後はGitHub MCPまたはStacks REST APIで全段を再取得する。

### 直列の更新

下段が変わった場合、branch担当は下段から上段の順で次を繰り返す。

1. 下段担当が変更をcommit、確認、pushし、新しいhead SHAを調整担当へ伝える。
2. 直上担当がremoteをfetchし、自分のbranchを直下branchへrebaseする。
3. 直上担当が競合を解消し、該当確認を再実行する。
4. 直上担当が`--force-with-lease`で自分のbranchだけをpushする。
5. 調整担当が対象PRのhead SHA、base、レビュー判断、必須チェックを再取得してから、さらに上の担当へ進行を許可する。

```bash
git fetch REMOTE
git rebase REMOTE/LOWER_BRANCH
git push --force-with-lease REMOTE HEAD_BRANCH
```

複数担当が同時に連鎖的なリベースをしない。通常のリベース、同期、レビュー待ちはIssueコメントへ記録せず、担当変更を伴う場合だけ`lifecycle-comments.md`のStack全体の引き継ぎコメントを使う。

## PR本文とレビュー

各PRは通常のPRテンプレートを満たし、対応する末端Issueを正確に1件だけ閉じる。`レビュー案内`には次を書く。

- この段だけが担う責務
- 下段から引き継ぐ前提や公開面
- このPR単独で確認できる範囲
- 上段の存在を知らなくても判断できる確認順

Stack番号、全段の位置一覧、現在のbase一覧は書かない。レビュー時はGitHubのStack表示を使い、最下段から順に差分の前提を確認する。上段PRも下段のマージを待たずにレビューできる。

レビュー可能にする前と、最新のhead SHAごとに次を取得する。

```bash
gh pr view PR_NUMBER \
  --repo OWNER/REPO \
  --json isDraft,headRefOid,baseRefName,reviewDecision,statusCheckRollup,mergeable,mergeStateStatus
gh pr checks PR_NUMBER --repo OWNER/REPO --required
```

## 下段変更後の再確認

下段の変更は、上にある全段の差分とhead SHAを変え得る。連鎖的なリベースと送信の後、影響したすべてのPRについて次を取り直す。

- head SHAとbase branch
- Draft状態
- レビュー判断と失効した承認
- 必須チェックと進行中の確認
- 競合、マージ可能性、rulesetによる停止
- PR本文の確認結果が新しいhead SHAにも適用できるか

古い承認やチェックを流用しない。すべての再確認が終わるまで、影響範囲をマージ可能と判断しない。

## 構成変更

GitHub上の順序やbaseを変える操作は、通常のリベースと区別する。

- `gh stack modify`は対話式の操作であるため、エージェントは自動実行しない。人間の操作を待つ。
- 構成変更前に、Stack番号、変更前後の下段からのPR順、base、影響するIssueと担当を示す。
- 人間が変更した後、全段を再取得し、`lifecycle-comments.md`のStack構成変更コメントへ判断を残す。
- `unstack`からの再作成は、変更前後の構成、レビューとCIへの影響、ローカルだけかGitHub側も含むかを示し、利用者が明示同意した場合だけ行う。

予告外の構成差は、全段を再取得して変更前後を示し、人間が採用する構成を決めるまで変更しない。決定後の復旧方法は差の種類で分ける。

| 差の種類                                    | 決定後に使える方法                                                                                                                       | 禁止すること                                           |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 同じPR集合・同じ順序でbaseだけが違う        | 期待するbase連鎖への復旧が明示された場合だけ、調整担当が全PRを下段から`gh stack link --base TRUNK --remote REMOTE ...`へ渡して再取得する | 予告外の差を見つけた直後の自動再link                   |
| 既存Stackへ上段PRを追加するだけ             | 追加対象と順序が明示された場合だけ、`gh stack link STACK_NUMBER NEW_PR...`を使って再取得する                                             | 既存PRを入力から省いて除外できたとみなすこと           |
| PRの除外、並べ替え、別Stack所属、分割、統合 | 人間による`gh stack modify`、または明示同意済みの`unstack`と再作成                                                                       | additiveな`link`で削除や並べ替えを試すこと             |
| `link`の途中失敗                            | 全状態の再取得後、未実行の追加だけで構成を完成できると人間が確認した場合に限り再開する                                                   | 終了コードだけを根拠に同じコマンドを自動再実行すること |

どの復旧方法でも、実行後に全PRの順序、base、head SHA、レビュー判断、必須チェックを再取得し、`lifecycle-comments.md`のStack構成変更コメントへ決定と結果を残す。

`unstack`前は対象を明示し、引数なしで現在のStackを推測しない。

```bash
gh stack unstack STACK_NUMBER --local
gh stack unstack STACK_NUMBER
```

`--local`はローカル追跡だけ、指定なしはGitHub側と該当するローカル追跡を対象にする。いずれもbranchやPRを削除する操作として扱わない。ただしqueuedまたはauto-merge設定済みのPRはGitHub側の判断でStackに残り得るため、実行後に再取得する。

## マージ

通常PRの`gh pr merge`経路とStackの`gh stack merge`経路を混ぜない。Stackでは自動マージを使わず、`gh pr merge`で1段ずつ処理しない。

マージ前にGitHub上のStackを再取得し、マージ対象を最下段から連続する範囲として示す。対象となる全PRで次を確認する。

- openかつDraftではない。
- 必須承認が最新head SHAに対して有効である。
- 必須チェックが成功している。
- head SHA、base、Stack順序が確認開始後に変わっていない。
- 競合がなく、線形のbase関係が保たれている。
- ruleset、ブランチ保護、マージキューの要件を満たす。

部分マージでは、最下段から選んだPRまでの連続範囲だけを指定する。中段や上段だけを飛び越えてマージしない。直接マージでは指定範囲を一括で処理し、1件でも開始条件を満たさなければ範囲全体をマージしない。

マージ範囲より上のPRも、下段変更後のhead SHA、base、レビュー判断、必須チェックを再取得する。ただし、その上段だけのDraft、未承認、失敗中チェックは、選択した下段の連続範囲が自身の受け入れ条件と保護要件を満たす限り、部分マージを自動で止める理由にはしない。

上段の失敗は、確認名だけで判断せず、失敗した確認、該当差分、各末端Issueの受け入れ条件を根拠に分類する。

| 分類                       | 判定                                                               | 部分マージ                                   |
| -------------------------- | ------------------------------------------------------------------ | -------------------------------------------- |
| 選択範囲のheadでも再現する | 選択範囲の差分だけで同じ失敗を確認できる                           | 停止する                                     |
| 選択範囲の契約違反         | 上段でだけ実行された確認でも、選択範囲の受け入れ条件違反を直接示す | 停止する                                     |
| 上段固有                   | 上段の差分または上段Issueの受け入れ条件だけに対応する              | 上段を未完了として残し、選択範囲は続行できる |
| 帰属不能                   | ログ、再現手順、確認と受け入れ条件の対応が不足する                 | 安全側に停止する                             |

分類結果と根拠はマージ直前の判断記録へ残す。上段の失敗を消すために、選択範囲外の差分を下段へ混ぜない。

マージキュー利用時は方式を指定しない。

```bash
gh stack merge TARGET_PR_NUMBER --yes
```

直接マージ時だけ、リポジトリで明示された既定方式を指定する。

```bash
gh stack merge TARGET_PR_NUMBER --yes --merge
```

リポジトリの既定が`squash`または`rebase`なら、実行時ヘルプで対応するオプションを確認して置き換える。マージキューでは対象範囲を一緒に投入しても、複数の`merge_group`として下段から個別に処理される場合がある。投入完了をマージ完了とみなさず、下段が先にマージされた後で上段が失敗しても巻き戻されない前提で、各PRと必須チェックを追跡する。失敗時は全PRの状態を再取得し、実際にマージ済み、待機中、失敗を分けて報告する。

### 部分マージ後の同期

部分マージ後は、GitHubが残る上段のbase変更と連鎖的なリベースを行い得る。残るPRのGitHub側の順序、base、head SHAを再取得するまで、ローカルbranchを続きの正本として使わない。

- 標準方式では、専用worktreeに未commit差分と未送信commitがないことを確認してから、非対話の`gh stack sync --remote REMOTE`を実行する。構成差で中止した場合は、削除、再作成、強制的なbranch移動をせず停止する。
- 複数worktree方式では、各担当がremoteを取得し、自分のbranchとGitHub側のhead SHAを比較する。未送信commitや差分がある場合は自動で合わせず、採用する履歴を人間が決めるまで停止する。
- どちらの方式も、残る全PRのレビュー判断と必須チェックを取り直してから次の変更またはマージへ進む。

## GitHub Actions

各段のGitHub Actionsは、そのPR単独のbase差分ではなく、Stack全体のbase向けPRとして評価される。既存の必須確認を削らず、各段で同じ確認が動く前提にする。

- `pull_request`と、採用済みなら`merge_group`の既存起動条件を維持する。
- 必須チェック名をStack用に別名へ変えず、rulesetとマージキューの契約を保つ。
- 高負荷処理を絞る必要がある場合だけ、`github.event.pull_request.stack`の位置情報を使う。
- 位置情報がない通常PRでも必要な確認が動く条件を残す。
- Stack位置だけを根拠に、受け入れ条件へ必要な確認を省略しない。

## 停止と復旧

### 未提供、権限不足

Stack機能が表示されない、`gh-stack`拡張がない、終了コード`9`で機能未提供を示す、または権限不足の場合は停止する。通常PRへの切り替え、拡張の導入、権限回避を自動で行わない。

### submit、push、linkの途中失敗

1. 残りの変更を止める。
2. 全branchのremote SHAを取得する。
3. 全PRの番号、URL、head、base、Draft状態を取得する。
4. GitHub上のStack番号と順序を取得する。
5. 作成済み、更新済み、未実行、確認不能を分けて報告する。

自動削除、自動unstack、branchの巻き戻し、PRを閉じる操作をしない。

### syncの構成差

非対話の`sync`は、ローカルとGitHub側の構成差で中止しても成功終了になる場合がある。終了コードだけで成功扱いにせず、出力と再取得した順序を確認する。差が残る場合はpushや再linkをせず、どちらを採用するか人間の判断を待つ。

### rebase競合

競合の解消がIssue契約と既存実装から一意に判断できる場合だけ、該当確認を行って続行する。

```bash
gh stack rebase --continue
```

意図が不明、他担当の差分、生成物の再生成方針が不明、または受け入れ条件が衝突する場合は中止して停止する。

```bash
gh stack rebase --abort
```

複数worktree方式では通常の`git rebase --continue`または`git rebase --abort`を使い、対象branch担当以外が競合解消を代行しない。中止後はhead SHAと`worktree`の状態を確認し、未push差分を自動破棄しない。

### 構成変更とunstack

`unstack`前に、Stack番号、対象PR、ローカルだけかGitHub側も含むか、再作成の有無を確認する。branchやPRを削除せず、実行後に残ったStack、PR、ローカル追跡を再取得する。

## 公式資料

- [About stacked pull requests](https://docs.github.com/en/pull-requests/get-started/about-stacked-prs)
- [GitHub CLI commands for stacked pull requests](https://docs.github.com/en/pull-requests/reference/stacked-prs-cli-commands)
- [Creating stacked pull requests](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-stacked-pull-requests)
- [Managing stacked pull requests](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/managing-stacked-pull-requests)
- [Reviewing stacked pull requests](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-stacked-pull-requests)
- [Merging stacked pull requests](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-stacked-pull-requests)
- [Optimizing CI for stacked pull requests](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/optimizing-ci-for-stacked-pull-requests)
- [Stacked pull requests are now in public preview](https://github.blog/changelog/2026-07-30-stacked-pull-requests-are-now-in-public-preview/)
