# 録画・編集・音声workflow

## 目次

1. [作業bundleとprovenance](#作業bundleとprovenance)
2. [Computer Use録画](#computer-use録画)
3. [legacy-v2編集](#legacy-v2編集)
4. [document-v7編集](#document-v7編集)
5. [外部Whisper fallback](#外部whisper-fallback)
6. [台本とTTS](#台本とtts)
7. [書き出しQA](#書き出しqa)
8. [失敗時の分岐](#失敗時の分岐)

## 作業bundleとprovenance

作業ごとに新しいdirectoryを作り、originalとは分離する。最低限次を残す。

```text
work/
├── sources.json
├── bundle/
│   ├── demo.openscreen
│   ├── recording.mp4
│   └── recording.mp4.cursor.json
├── edit-plan.json
├── captions.vtt または transcript.tsv
├── captions.corrected.vtt または transcript.corrected.tsv
├── narration.md
├── narration.txt
├── voiceover.m4a
├── demo-draft.mp4
├── picture-master.mp4
└── demo-final.mp4
```

開始時にsource project/mediaのSHA-256、OpenScreen app versionまたはhelp signature、実行commandを記録する。macOS例:

```bash
shasum -a 256 "$PROJECT" "$VIDEO"
```

Linuxでは`sha256sum`を使う。projectにspaceがあるので、変数展開は必ずquoteする。ユーザーがMarkdownで示した`proj\_...`のbackslashを実pathへ含めない。

## Computer Use録画

### Preflight

- OpenScreen/terminalへScreen RecordingとAccessibilityを許可する。
- micを使うならMicrophone権限とinput levelを確認する。
- 対象appを起動し、demo account、fixture data、初期URL/画面を準備する。
- desktop通知、credential、personal tab、password managerを閉じる。
- titleが動的に変わるappでは録画直前に`sources`を再実行する。
- system audioは必要な場合だけ有効にする。TTS `replace`を予定していても、操作音がレビューに必要ならdraft用に残す。

### Beatを作る

一つのbeatを「操作」と「画面で確認できる終了状態」の組にする。

```text
0. 初期画面で静止
1. Connectを押す → provider選択が開く
2. ChatGPTを選ぶ → OAuth同意画面が開く
3. Allowを押す → connected badgeが出る
4. 最終画面で静止
```

重要状態の前後に0.5–1秒の静止を置く。pointerを意味なく振らない。入力は事前にclipboardへ用意しても、secretは録画対象windowへ表示しない。

### 録画processとの同期

1. `openscreen sources -o "$OPENSCREEN_WORK_DIR/sources.json"`を実行する。
2. flowをdry-runし、OAuth popupなどが別windowへ移るか確認する。
3. 単一windowなら`windows[].name`に1件だけ部分一致するsubstringを選ぶ。
4. display全体が必要ならscope拡大の明示承認を得て、直前の`displays[]`から対象を目視確認し、その`index`が1件だけ存在することを`jq`で検証する。承認がなければ同一window化または停止にする。
5. terminal toolでTTY付き長寿命processとして`record`を開始する。`--window`か`--display`の片方だけを使い、固定尺が不要なら`--duration`を付けない。
6. `event == "log" && message == "Recording started"`を待つ。`event == "started"`だけでComputer Useへ進まない。
7. Computer Useのreal OS pointer/keyboardでbeatを順に実行する。
8. 同じrecord sessionのstdinへ`stop`と改行を一度送り、30秒以下のpollを繰り返して最大120秒待つ。
9. final `done`がなければ同じsessionへSIGINTを一度送り、さらに最大120秒pollする。それでも生存中ならhard killやretryをせず、ユーザーに手動停止を求めるblockerとして扱う。
10. `event == "done" && success == true`、exit code、`projectPath`、`screenVideoPath`、cursor sidecarを確認する。

対象windowが見つからない場合は、titleを推測してrecordを始めず、appの起動完了を待って再列挙する。部分一致が複数候補に当たり得る場合は、より長いsubstringかwindow配置を選び直す。

### 録画直後

`openscreen pack`でportable bundleを作る。raw recordingを一度再生し、解像度、cursor、mic、system audio、操作漏れを確認する。破綻したtakeを編集で救おうとする前に、短時間で撮り直せるなら撮り直す。

## legacy-v2編集

### 順序

1. raw takeを確認する。
2. trimを確定する。
3. manual zoomと説明annotationを置く。
4. `captions`を生成する。
5. VTTで字幕本文と必要なtimingを修正する。
6. 修正VTTを新しいproject copyへimportする。
7. 台本を作りTTSを生成する。
8. draft exportで同期を確認する。
9. final exportを行う。

`captions`を修正後に再実行すると修正が消えるため、この順を崩さない。

cut判断用の予備transcriptが必要なら、originalではなくcopyへ生成する。

```bash
cp "$PROJECT" "$OPENSCREEN_WORK_DIR/00-preliminary.openscreen"
openscreen captions "$OPENSCREEN_WORK_DIR/00-preliminary.openscreen" \
  --min-words 2 --max-words 7
python3 "<skill-dir>/scripts/openscreen_project.py" export-vtt \
  "$OPENSCREEN_WORK_DIR/00-preliminary.openscreen" \
  "$OPENSCREEN_WORK_DIR/preliminary.vtt"
```

予備VTTのraw timeでcutを決める。予備字幕を修正して使い続けず、`apply-plan`後に`captions`を再実行し、その最終VTTだけを手修正する。

### Cut

edit planの`trimRegions`は削除するraw spanである。台本の言い淀みだけでなく、操作待ちやerror stateも確認する。隣接/重複trimは人が理解できる単位へまとめる。

cut境界で語頭/語尾を切らない。波形またはtranscript word timeを使い、短いroom toneを残す。cut済みexportのtimecodeとraw timelineのtimecodeを混同しない。

### Zoom

`export --auto-zoom`はpreview候補として使う。次のどれかならmanual zoomへ置換する。

- focusが対象controlから外れる。
- zoomが発話より早い/遅い。
- 深さが強すぎる。
- 連続zoomで酔いやすい。
- title/annotationを隠す。

manual zoomを置いた区間にはauto suggestionが重ならない。最終版を完全に再現可能にしたい場合はmanual zoomだけ保存し、exportから`--auto-zoom`を外す。

### Text annotation

同梱helperの`heading` presetは左上、`note` presetは標準CLI字幕より上の左下へ置く。これは初期値であり、previewして重要UI、pointer、webcam、字幕と重なる場合はplanの`position`/`size`/`style`を上書きする。

見出しは章/ユースケース名を短く示し、長時間固定しすぎない。補足は画面から読み取れない前提や結果だけを書く。音声と同じ全文を重複表示しない。

### VTT修正

`export-vtt`がcaption annotation IDをcue IDへ入れる。修正時は次を守る。

- cue IDを削除/重複させない。
- timing lineは`HH:MM:SS.mmm --> HH:MM:SS.mmm`を保つ。
- 表示本文だけを直すのが既定。固有名詞、API名、英大文字小文字を確認する。
- timing変更はraw source timeで行う。
- manual heading/noteはVTT対象外で、そのまま保持される。

## document-v7編集

GUIを閉じ、originalのcopyだけを対象にする。v7のsubtitleは`transcripts[].words`が正本である。

transcriptの存在と字幕表示の有効化は別である。GUIのCaptionsをONにして、`legacyEditor.captions.enabled`と実previewを確認する。表示設定はGUIを正とし、文字修正用TSVで切り替えない。

`export-transcript-tsv`後は`corrected_text`列だけを修正する。`expected_text`、ID、segment、start/end、行数を変えない。同梱helperはimport時にprojectが途中変更されていないか照合し、次を一括更新する。

- `transcripts[assetId].words[].text`
- 初回訂正時の`originalText`と`source: user`
- `segments[].text`
- primary assetのroot `transcript` mirror

Zoom/text/cutのJSON patchは単一clip内だけhelperへ任せる。v7ではclip anchorが正本なので、clip境界をまたぐregion、複数clip、reorder、duplicate clipを伴う編集はGUIへ回す。

v1.10系のCLI `captions`/`export`はlegacy validatorを通るため、v7をそのまま渡さない。将来buildで対応した場合も、copyに対するprobe exportとGUI previewが一致することを確認してから採用する。

## 外部Whisper fallback

内蔵`openscreen captions`を使えないlegacy-v2だけを既定のfallback対象にする。OpenAI Whisper CLIにはffmpegとmodel downloadが必要である。

```bash
uvx --python 3.11 --from openai-whisper whisper "$VIDEO" \
  --model small \
  --language Japanese \
  --task transcribe \
  --output_format vtt \
  --word_timestamps True \
  --max_words_per_line 7 \
  --output_dir "$OPENSCREEN_WORK_DIR/whisper"
```

実機`whisper --help`でoptionを確認する。言語自動判定が適切なら`--language`を外す。モデルを大きくする前に速度、memory、固有名詞精度を比較する。

raw source videoを入力にする。cut済みexportを文字起こししたVTTはprogram timeなので、raw `.openscreen`へ直接importしない。外部VTTにはOpenScreen annotation IDがないため、helperが新しい一意IDを割り当てる。既存auto captionsと配列indexで対応付けない。

## 台本とTTS

### 台本化

修正字幕をそのまま読み上げ原稿にする前に、cutと画面beatを突き合わせる。

- filler、言い直し、待ち時間を削る。
- UI label、固有名詞、protocol名を画面表記と一致させる。
- 一文一操作を基本にする。
- 画面より先に答えを読み上げない。
- 読み上げない補足はlower-left noteへ移す。
- beatごとに目標開始時刻と許容durationを残す。

legacyでは`make-script`がraw time、trim圧縮後time、partial overlapを表にする。`partial trim: review`を残したままTTSへ進まない。

v7では修正済みprojectのword timeをclipsへ写し、trimRangesを除いた発話を台本化する。

```bash
python3 "<skill-dir>/scripts/openscreen_project.py" make-transcript-script \
  "$OPENSCREEN_WORK_DIR/02-corrected.openscreen" \
  --output "$OPENSCREEN_WORK_DIR/narration.md" \
  --plain-output "$OPENSCREEN_WORK_DIR/narration.txt"
```

helperはreorder/duplicate clipをprogram timeへ展開する。segmentがclip source境界をまたぐ場合は曖昧な切断をせず失敗するため、GUIで区切るかtranscript/cutを見直す。出力の`partial trim: review`を残したままTTSへ進まない。

### TTS provider

ユーザー指定provider/voiceがあればそれを使う。cloud providerへ送る場合は台本や固有データの送信許可を確認する。指定がなくmacOS local fallbackでよければ次のようにM4Aを作れる。

```bash
say -o "$OPENSCREEN_WORK_DIR/voiceover.m4a" --file-format=m4af -f "$OPENSCREEN_WORK_DIR/narration.txt"
```

`openscreen export --audio`はAIFFを受けないので、`say`のdefault AIFFをそのまま渡さない。

### 同期

OpenScreenが受け取るvoiceoverは1 fileと1 global offsetだけである。厳密同期ではTTSをbeatごとに生成し、外部audio toolで指定時刻までの無音を入れた一本のbedにする。

一括TTSを使う場合は、台本を短くするかproviderのrate controlで尺を合わせる。極端なtime stretchで音質を落とさない。

映像と音声のdurationを測る。

```bash
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$OPENSCREEN_WORK_DIR/demo-draft.mp4"
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 "$OPENSCREEN_WORK_DIR/voiceover.m4a"
```

`voiceover duration + audio offset <= video duration`を満たす。長い音声はOpenScreenが動画末尾で切る。短い音声は末尾無音になるため、意図した静止余白か確認する。

`replace`を既定にする。実演中の人声を綺麗なTTSへ置換する用途で`mix`を選ぶと、元の誤った発話も40%で残る。

legacy-v2はCLIの`--audio-mode replace`を使う。document-v7のGUI audio layerは原録音へmixされるため、厳密な置換ではGUIからTTSなしの映像masterを書き出し、audio streamを外で差し替える。

```bash
ffmpeg -i "$OPENSCREEN_WORK_DIR/picture-master.mp4" \
  -i "$OPENSCREEN_WORK_DIR/voiceover.m4a" \
  -filter_complex "[1:a]apad[voice]" \
  -map 0:v:0 -map "[voice]" \
  -c:v copy -c:a aac -shortest -movflags +faststart \
  "$OPENSCREEN_WORK_DIR/demo-final.mp4"
```

このmapに元映像のaudio streamを含めないため、原録音は残らない。`apad`は短いTTSの後ろを無音で埋め、`-shortest`は映像末尾で止める。TTSが映像より長い場合は切れるので、先にdurationを直す。GUIへTTSをimportするのは、原録音が無音かmixを意図するときだけにする。

## 書き出しQA

まず`--quality medium`のdraftで全尺を確認し、finalだけ`source`を使う。machine-readable modeではstdout NDJSONを保存し、stderrと混ぜない。

確認項目:

1. `done.success`と出力path。
2. fileが0 byteでなく、ffprobeでvideo/audio streamが読める。
3. 冒頭と末尾が切れていない。
4. 全cut境界で映像と音声が自然。
5. manual/auto zoomが重要UIを追う。
6. title/note/caption/webcamが重ならない。
7. captionの誤字、二重表示、早消えがない。
8. TTSの発話が画面beatを追い越さず、末尾で切れない。
9. `replace`/`mix`が依頼通り。
10. final command、hash、plan、字幕、台本をbundleに残す。

可能なら全尺を実時間で1回視聴する。frame samplingだけでは音切れ、subtitle timing、zoom easingを判断できない。

## 失敗時の分岐

- `Project file is not a valid .openscreen project`: helperでshapeを確認する。document-v7ならCLI compatibility gapとしてGUIへ回す。
- media missing/permission denied: `pack`し直し、projectとmediaを同directoryへ置く。勝手にpathだけ書き換えない。
- cursor telemetryなし: `--auto-zoom`を諦めmanual zoomを使う。録画済みvideoから架空のcursor pathを作らない。
- captionsが既存修正を消した: originalへ戻らず、修正VTT/TSVを最後のcaption生成後のcopyへ再適用する。
- v7 regionがclip境界をまたぐ: helperの拒否を回避せず、分割またはGUI操作に切り替える。
- TTSが長い: exportを繰り返す前に台本、rate、beat間pauseを直し、ffprobeで再確認する。
- Computer Useが途中で失敗: recordingを正常停止し、takeを保存してから再開位置を判断する。record processを放置しない。
