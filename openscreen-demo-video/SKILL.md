---
name: openscreen-demo-video
description: OpenScreen CLIと`.openscreen` JSONを使い、アプリのデモ動画を録画・編集・書き出しする。Use when Codex needs to automate a target window with Computer Use while recording, transcribe/correct captions, adjust cuts or zooms, add upper-left headings or lower-left notes, turn a corrected transcript into a narration script, attach TTS audio, or render MP4/GIF. legacy v2とGUI document v7を判定し、安全な編集経路へ分岐する。
---

# OpenScreen demo video

OpenScreenの標準CLIを優先し、JSON編集は同梱helperが検証できる範囲だけ行う。録画、編集、字幕、台本、TTS、書き出しを一つの追跡可能な作業bundleとして扱う。

## 守ること

- 最初にインストール済みCLIの`openscreen help`と対象projectの形式を確認する。CLIとproject schemaは破壊的変更があり得る。
- 元の`.openscreen`を直接編集しない。GUIを閉じ、project、media、`.cursor.json`を作業directoryへ`pack`またはcopyしてから編集する。
- shell pathを常にquoteする。Markdown表示の`proj\_...`にあるbackslashは通常ファイル名の一部ではない。
- JSON object全体を再構築しない。同梱helperで未知fieldを保持し、別の`--output`へatomic writeする。
- cloud TTSへ音声や台本を送る前に、providerとデータ送信をユーザーが許可しているか確認する。指定がなければprovider-neutralな台本まで作り、local TTSを候補にする。
- すべてのexportを最後まで待ち、exit code、NDJSONの`done.success`、出力file、映像、音声、字幕を確認する。途中でexport processをkillしない。

## 1. Preflightと形式判定

1. `command -v openscreen`を確認する。macOSでPATHにない場合は`/Applications/Openscreen.app/Contents/MacOS/Openscreen`をquoteして使う。`--version`は使わず、`help`のsignatureとapp versionを記録する。
2. `openscreen help`を読み、このskillで使うoptionが実機にあることを確認する。
3. 同梱helperは絶対pathで呼ぶ。以降`<skill-dir>`はこの`SKILL.md`のdirectoryである。

作業ごとに元projectの外へ新しい絶対pathを決める。既存projectを編集するときは`$PROJECT`も実pathへ設定する。以降はこの2変数を使う。

```bash
PROJECT="/absolute/path/to/project.openscreen"
OPENSCREEN_WORK_DIR="/absolute/path/to/new-openscreen-work"
mkdir -p "$OPENSCREEN_WORK_DIR"
```

既存projectがある場合は形式を判定する。新しく録画する場合はここだけ飛ばし、`record`完了後に返された`projectPath`を同じhelperで判定する。

```bash
python3 "<skill-dir>/scripts/openscreen_project.py" inspect "$PROJECT" --json
```

4. 結果で必ず分岐する。
   - `legacy-v2`: CLI `record --project`が作る`{version, media, editor}`。`captions`、JSON編集、`export`の完全なCLI workflowを使う。
   - `document-v7`: GUIの`~/Library/Application Support/openscreen/projects/`に多い`{schemaVersion,...}`。同梱helperの限定編集とtranscript TSV修正だけ使える。現行v1.10系CLIの`captions`/`export`はこの形式を拒否し得るため、GUIをComputer Useで開いてpreview/exportするか、CLIで録り直す。v7→v2を推測で変換しない。
   - 未知schema: 書き込まず停止し、実機CLI/sourceの対応状況を調べる。

詳細なcommand、schema、互換性根拠が必要なら[CLIとproject形式](references/cli-project-format.md)を読む。

## 2. Computer Useとwindow録画

対象windowを起動して初期画面へ戻し、通知、個人情報、token、password managerを隠す。操作台本を短いbeatへ分け、各beatの完了条件を決める。

1. 録画直前にsourceを再列挙する。

```bash
openscreen sources -o "$OPENSCREEN_WORK_DIR/sources.json"
```

2. flowを録画なしでdry-runする。単一windowに収まるなら`windows[].name`から一意なtitle substringを選ぶ。OAuth popupなど別windowも必要なら、録画範囲がdisplay全体へ広がることをユーザーに説明して明示承認を得てから、直前の`sources.json`にある`displays[].index`を選ぶ。承認がなければ同一window化するか停止する。
3. 長寿命PTY/sessionで録画を開始する。`--window "$WINDOW_TITLE"`または`--display "$DISPLAY_INDEX"`の片方だけを使い、編集可能cursor telemetryを残すため通常は既定の`editable-overlay`を使う。

```bash
openscreen record --window "$WINDOW_TITLE" --mic \
  --project "$OPENSCREEN_WORK_DIR/demo.openscreen" --json
```

4. `{"event":"log","message":"Recording started"}`を確認してからComputer Useを始める。`{"event":"started","command":"record"}`だけでは開始しない。開始と終了に1秒前後の静止余白を残し、重要な状態では0.5–1秒止める。real OS pointer/keyboard操作を使い、DOM/CDPだけのsynthetic操作に依存しない。
5. 同じprocessのstdinへ`stop\n`を一度送り、30秒以下のpollを繰り返して最大120秒までfinal `done`を待つ。来なければ同じsessionへSIGINTを一度送り、同様に最大120秒待つ。それでもprocessが生きていれば成功扱いやretryをせず、hard killせずにblockerとして報告する。`event == "done" && success == true`、exit code、`screenVideoPath`、`cursorDataPath`、`projectPath`を検証し、返されたprojectをhelperで`legacy-v2`と確認して、以後の`PROJECT`をその`projectPath`にする。
6. 録画結果をbundle化する。

```bash
openscreen pack "$OPENSCREEN_WORK_DIR/demo.openscreen" --out "$OPENSCREEN_WORK_DIR/bundle"
```

Computer Useの失敗復旧、macOS権限、pause設計は[録画・編集・音声workflow](references/workflows.md)を読む。

## 3. 編集計画を作る

まず低品質のdraftで時刻を確認する。`legacy-v2`はCLIのmedium export、`document-v7`はGUI preview/exportを使い、互換probe前のv7をCLIへ渡さない。source/raw timelineのミリ秒で、削る区間、残す説明、画面上の注目点をedit planへ記録する。既存regionは形式に応じて次を読む。

```bash
jq '.editor | {trimRegions,zoomRegions,annotationRegions}' "$PROJECT"        # legacy-v2
jq '{trims:.timeline.trimRanges, zooms:.zoomRanges, text:.annotations}' "$PROJECT" # document-v7
```

planの最小例:

```json
{
  "trimRegions": [{ "id": "trim-intro", "startMs": 0, "endMs": 650 }],
  "zoomRegions": [
    {
      "id": "zoom-consent",
      "startMs": 1800,
      "endMs": 4300,
      "depth": 3,
      "focus": { "cx": 0.72, "cy": 0.38 },
      "focusMode": "manual",
      "source": "manual"
    }
  ],
  "textAnnotations": [
    {
      "id": "heading-oauth",
      "startMs": 0,
      "endMs": 9000,
      "preset": "heading",
      "text": "OAuth Remote MCP経由のChatGPT連携"
    },
    {
      "id": "note-consent",
      "startMs": 2100,
      "endMs": 4100,
      "preset": "note",
      "text": "接続先と権限を確認"
    }
  ],
  "deleteIds": ["zoom-bad-1"]
}
```

適用先は必ず別fileにする。

```bash
python3 "<skill-dir>/scripts/openscreen_project.py" apply-plan \
  "$PROJECT" "$OPENSCREEN_WORK_DIR/edit-plan.json" --output "$OPENSCREEN_WORK_DIR/01-edited.openscreen"
```

`document-v7`ではhelperが単一clip内のraw timeline timeを`clipId`とsource timeへ変換する。clip境界をまたぐregionは拒否されるので分割するかGUIで編集する。

### Auto zoom

`openscreen export ... --auto-zoom`はcursor telemetryからrender時だけzoomを足し、projectへ保存しない。速いdraftには使う。修正可能な最終版では、良い区間をmanual `zoomRegions`としてplanへ保存する。manual zoomのある区間にはauto suggestionが重ならない。不要なら`--auto-zoom`を外す。

## 4. 字幕を起こして修正する

cut判断の材料が必要ならraw音声の予備transcriptを先に作ってよい。ただし最終cutを確定した後に字幕を生成し直す。字幕再生成は以前の自動字幕修正を置き換えるため、確定工程は`cut → final transcription → manual correction → export`にする。

### legacy-v2

cut判断用に予備字幕が必要なら、originalを変更しないcopyへ一度だけ生成する。このVTTはcut planの材料であり、手修正して最終字幕として使い回さない。

```bash
cp "$PROJECT" "$OPENSCREEN_WORK_DIR/00-preliminary.openscreen"
openscreen captions "$OPENSCREEN_WORK_DIR/00-preliminary.openscreen" \
  --min-words 2 --max-words 7
python3 "<skill-dir>/scripts/openscreen_project.py" export-vtt \
  "$OPENSCREEN_WORK_DIR/00-preliminary.openscreen" \
  "$OPENSCREEN_WORK_DIR/preliminary.vtt"
```

予備VTTのraw timeを使ってcutを確定し、`apply-plan`後のprojectへ次の最終transcriptionを実行する。

内蔵Whisperを既定経路にする。

```bash
openscreen captions "$OPENSCREEN_WORK_DIR/01-edited.openscreen" --min-words 2 --max-words 7
python3 "<skill-dir>/scripts/openscreen_project.py" export-vtt \
  "$OPENSCREEN_WORK_DIR/01-edited.openscreen" "$OPENSCREEN_WORK_DIR/captions.vtt"
```

VTTのcue IDとtiming行を維持し、本文を手動修正する。timingを変える場合もsource/raw timeのままにする。修正版を新しいprojectへ戻す。

```bash
python3 "<skill-dir>/scripts/openscreen_project.py" import-vtt \
  "$OPENSCREEN_WORK_DIR/01-edited.openscreen" "$OPENSCREEN_WORK_DIR/captions.corrected.vtt" \
  --output "$OPENSCREEN_WORK_DIR/02-captioned.openscreen"
```

内蔵`captions`がない、または明示的に別model/languageを使うときだけ`uvx --from openai-whisper whisper ... --output_format vtt`をfallbackにする。raw source mediaを起こし、cut済みexportを起こしてそのtimecodeをprojectへ戻さない。具体例は[workflow](references/workflows.md)を読む。

### document-v7

字幕はannotationではなく`transcripts[].words`から毎frame派生する。GUIでon-device transcriptionを完了し、CaptionsをONにしてpreviewする。transcriptが存在するだけでは字幕表示を仮定しない。GUIを閉じてword TSVを往復する。

```bash
python3 "<skill-dir>/scripts/openscreen_project.py" export-transcript-tsv \
  "$OPENSCREEN_WORK_DIR/01-edited.openscreen" "$OPENSCREEN_WORK_DIR/transcript.tsv"
# corrected_text列だけを修正する
python3 "<skill-dir>/scripts/openscreen_project.py" import-transcript-tsv \
  "$OPENSCREEN_WORK_DIR/01-edited.openscreen" "$OPENSCREEN_WORK_DIR/transcript.corrected.tsv" \
  --output "$OPENSCREEN_WORK_DIR/02-corrected.openscreen"
```

helperは`expected_text`を現projectと照合してから`originalText`/`source`、segment text、primary `transcript` mirrorを同期する。`corrected_text`以外の列、時刻、行を変更・削除しない。v7へlegacy auto-caption annotationを追加すると二重字幕になり得るため行わない。

## 5. 台本化してTTSを付ける

legacy-v2では修正VTTと最終cutから、元時刻とtrim圧縮後時刻を併記した台本を作る。

```bash
python3 "<skill-dir>/scripts/openscreen_project.py" make-script \
  "$OPENSCREEN_WORK_DIR/02-captioned.openscreen" "$OPENSCREEN_WORK_DIR/captions.corrected.vtt" \
  --output "$OPENSCREEN_WORK_DIR/narration.md" --plain-output "$OPENSCREEN_WORK_DIR/narration.txt"
```

`partial trim: review`を必ず解消する。document-v7では修正済みprojectのtranscript、clips、trimRangesから同じ形式の台本を作る。

```bash
python3 "<skill-dir>/scripts/openscreen_project.py" make-transcript-script \
  "$OPENSCREEN_WORK_DIR/02-corrected.openscreen" \
  --output "$OPENSCREEN_WORK_DIR/narration.md" \
  --plain-output "$OPENSCREEN_WORK_DIR/narration.txt"
```

helperはreorder/duplicate clipをprogram timeへ写す。発話segmentがclip source境界をまたぐ場合は推測せず拒否するので、GUIで区切るかtranscript/cutを見直す。自然なナレーションへ整えるときも、固有名詞、操作順、意味を変えず、画面beatごとの尺を残す。

選んだTTSでMP3/WAV/M4Aを生成する。厳密同期が必要ならbeatごとに合成し、無音を含む1本のaudio bedへ整列する。一括TTSはdriftしやすい。`ffprobe`でdraft映像と音声のdurationを比較し、音声が`video duration - audio offset`を超えないことを確認する。超過分はCLIで切れる。

## 6. 書き出しとQA

legacy-v2をMP4へ書き出す。

```bash
openscreen export "$OPENSCREEN_WORK_DIR/02-captioned.openscreen" \
  -o "$OPENSCREEN_WORK_DIR/demo-final.mp4" --quality source \
  --audio "$OPENSCREEN_WORK_DIR/voiceover.m4a" --audio-mode replace --json
```

原音も残す依頼のときだけ`--audio-mode mix`を使う。mixは原音をvoiceover区間だけでなく全体的に40%へ下げる。GIFは`--audio`非対応である。

`document-v7`は互換probeに成功しない限りCLI exportへ渡さない。GUIをComputer Useで開き、修正copyの字幕、見出し、補足、cut、zoomをpreviewして、TTSをimportせず`picture-master.mp4`へ書き出す。GUIの外部audio trackは原録音へ重ねる経路なので、原音の厳密な置換には使わない。先に上記duration条件を満たしたことを確認し、次のcommandでvideoだけを映像masterから、audioだけをTTSからmapする。

```bash
ffmpeg -i "$OPENSCREEN_WORK_DIR/picture-master.mp4" \
  -i "$OPENSCREEN_WORK_DIR/voiceover.m4a" \
  -filter_complex "[1:a]apad[voice]" \
  -map 0:v:0 -map "[voice]" \
  -c:v copy -c:a aac -shortest -movflags +faststart \
  "$OPENSCREEN_WORK_DIR/demo-final.mp4"
```

`apad`と`-shortest`により短いTTSの末尾は無音で映像尺を保つ。長いTTSは映像末尾で切れるため、command前のduration検査を省略しない。原録音が無音、またはmixが依頼事項なら、代わりにGUIのvoiceover/audio importをplayhead 0で使ってもよい。

最後に次を目視・聴取する。

- 冒頭/末尾、各cut境界に音切れや瞬間frameがない。
- zoomのfocus、深さ、開始/終了が操作意図と合う。
- 左上見出しと左下補足がpointer、重要UI、標準字幕と重ならない。
- 字幕の固有名詞、句読点、改行、表示時間が正しい。
- TTSが画面beatと同期し、末尾で切れず、原音の扱いが依頼通りである。
- 最終artifactと一緒に、source project hash、作業project、edit plan、修正VTT/TSV、台本、TTS入力、実行commandを残す。

## 同梱resource

- `scripts/openscreen_project.py`: 形式判定、限定edit plan、legacy VTT往復、v7 transcript TSV往復、両形式のcut-aware台本化。
- [CLIとproject形式](references/cli-project-format.md): 公式sourceに基づくcommand/schema/互換性。
- [録画・編集・音声workflow](references/workflows.md): Computer Use、Whisper fallback、TTS尺合わせ、QAの詳細。
