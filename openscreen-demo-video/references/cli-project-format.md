# OpenScreen CLIとproject形式

確認日: 2026-09-05

## 目次

1. [公式source](#公式source)
2. [CLI binary](#cli-binary)
3. [Command contract](#command-contract)
4. [同じ拡張子にある2形式](#同じ拡張子にある2形式)
5. [Caption settings](#caption-settingsdocument-v7)

このreferenceはOpenScreen公式v1.10.0と、確認日時点の公式`main`を根拠にする。OpenScreen自身がCLIと`.openscreen`形式のbreaking changeを予告しているため、実行時は必ずインストール済み`openscreen help`とproject shapeを優先する。

## 公式source

- [v1.10.0 CLI docs](https://github.com/getopenscreen/openscreen/blob/v1.10.0/docs/cli.md)
- [CLI argument parser](https://github.com/getopenscreen/openscreen/blob/v1.10.0/electron/cli/args.ts)
- [legacy project persistence](https://github.com/getopenscreen/openscreen/blob/v1.10.0/src/components/video-editor/projectPersistence.ts)
- [legacy editor region types](https://github.com/getopenscreen/openscreen/blob/v1.10.0/src/components/video-editor/types.ts)
- [document schema](https://github.com/getopenscreen/openscreen/blob/v1.10.0/src/lib/ai-edition/schema/index.ts)
- [CLI captions runner](https://github.com/getopenscreen/openscreen/blob/v1.10.0/src/cli/CliCaptionsRunner.tsx)
- [CLI export runner](https://github.com/getopenscreen/openscreen/blob/v1.10.0/src/cli/CliExportRunner.tsx)
- [caption settings](https://github.com/getopenscreen/openscreen/blob/v1.10.0/src/lib/ai-edition/captions/settings.ts)
- [document-v7 editor shell](https://github.com/getopenscreen/openscreen/blob/v1.10.0/src/components/ai-edition/NewEditorShell.tsx)
- [document-v7 audio preview](https://github.com/getopenscreen/openscreen/blob/v1.10.0/src/components/ai-edition/VirtualPreview.tsx)
- [caption/transcript docs](https://getopenscreen.com/docs/captions/)
- [editing/timeline docs](https://getopenscreen.com/docs/editing-timeline/)
- [OpenAI Whisper](https://github.com/openai/whisper)

## CLI binary

Packaged macOS appのbinaryは通常次である。

```text
/Applications/Openscreen.app/Contents/MacOS/Openscreen
```

PATHへ`openscreen` symlinkがあるならそれを使う。CLIに安定した`--version` optionはない。`openscreen help`を実行し、必要ならmacOS app bundleの`Info.plist`からversionを読む。

CLIはGUIと同時起動できる設計だが、GUIが同じprojectをautosaveし得る。外部JSON編集時はGUIを閉じる。

## Command contract

### `sources`

```bash
openscreen sources -o sources.json
```

`-o`はbare JSON、`--json` stdoutはfinal `done` envelope内のpayloadである。wrapperがstderrをstdoutへ混ぜる環境では`-o`を使う。既存fileが残っていても失敗時には更新されないため、file存在だけでなくexit codeを確認する。

`sources.json`の主要shape:

```json
{
  "displays": [{ "index": 0, "id": "screen:0:0", "name": "Built-in Display" }],
  "windows": [{ "id": "window:123:0", "name": "My App" }],
  "microphones": [{ "label": "MacBook Microphone" }],
  "microphoneLabelsUnavailable": false
}
```

`--display`が受け取るのはdisplay名や`id`ではなく、非負整数の`index`である。候補を目視で選んだ後も、そのindexが列挙結果に1件だけあることを開始条件にする。

```bash
DISPLAY_INDEX=0
jq -e --argjson n "$DISPLAY_INDEX" \
  '[.displays[] | select(.index == $n)] | length == 1' sources.json
```

`display.index`は`sources`がscreenだけを列挙した順番で、`record --display`も同じ順番を使う。録画直前に再列挙し、古いindexを再利用しない。

### `record`

```bash
openscreen record --window "My App" --mic --system-audio \
  --project demo.openscreen --json
```

- `--window`はwindow titleのcase-insensitive substringで最初に一致したものを選ぶ。
- default `--cursor editable-overlay`はvideoへcursorを焼かず、`<video>.cursor.json` telemetryを残す。
- `--duration`なしの正常停止はSIGINT/SIGTERMまたはstdinの`stop`。Windowsではstdin `stop`、Ctrl+C、`--duration`を使う。
- hard killはrecordingを失い得る。
- final NDJSON `done`は`screenVideoPath`、`cursorDataPath`、`durationMs`、`projectPath`を返す。

`--json`時の重要eventは次の形になる。pathは例である。

```json
{"event":"started","command":"record"}
{"event":"log","message":"Recording started"}
{"event":"stopping","reason":"stdin"}
{"event":"done","success":true,"screenVideoPath":"/path/demo.mp4","cursorDataPath":"/path/demo.mp4.cursor.json","durationMs":4200,"projectPath":"/path/demo.openscreen"}
```

`started`はhidden runnerの起動通知で、capture開始通知ではない。Computer Use開始predicateは`event == "log" && message == "Recording started"`、完了predicateは`event == "done" && success == true`にする。

### `captions`

```bash
openscreen captions demo.openscreen --min-words 2 --max-words 7
```

legacy-v2 projectの音声を内蔵whisper.cppで起こし、`editor.annotationRegions`へ`annotationSource: "auto-caption"`として書く。再実行時は既存auto-captionだけを全置換し、manual annotationは保持する。保存はproject pathへの直接writeなので、originalではなく作業copyに実行する。

CLI captionの既定layout:

```json
{
  "position": { "x": 4, "y": 86 },
  "size": { "width": 92, "height": 12 },
  "style": {
    "color": "#ffffff",
    "backgroundColor": "rgba(255, 255, 255, 0)",
    "fontSize": 24,
    "fontFamily": "Inter",
    "fontWeight": "normal",
    "fontStyle": "normal",
    "textDecoration": "none",
    "textAlign": "center"
  }
}
```

### `export`

```bash
openscreen export demo.openscreen -o demo.mp4 --quality source --json
```

- `--auto-zoom`はcursor telemetryからsuggestionをmemory上へ追加する。project JSONには保存しない。既存zoomは残り、suggestionは既存zoomへ重ならない。
- `--audio <mp3|wav|m4a>`はMP4だけで使える。AIFFは非対応。
- `--audio-mode replace`は元音声を捨てる。
- `--audio-mode mix`は元音声全体を0.4倍にしてvoiceoverを重ねる。voiceover中だけのdynamic duckではない。
- `--audio-offset`は単一のglobal delay。負値は使わない。
- voiceover処理は動画尺のaudio contextへ配置する。短ければ末尾は無音、長ければ動画末尾で切れる。
- mediaはapp recordings directory内かproject fileと同じdirectoryに置く。portable化には`pack`を使う。
- native compositorにcancel機構はない。途中停止せず完了を待つ。

### `pack`と`info`

```bash
openscreen pack demo.openscreen --out bundle
openscreen info bundle/demo.openscreen --json
```

`pack`はproject、screen/webcam media、cursor sidecarをcopyし、media pathを書き換える。`info`の実装はlegacy shapeを前提にしたsummaryであり、document-v7の妥当性検証には使えない。

## 同じ拡張子にある2形式

### legacy-v2

CLI `record --project`の出力。top-level shape:

```json
{
  "version": 2,
  "media": {
    "screenVideoPath": "/absolute/path/video.mp4",
    "webcamVideoPath": "/optional/camera.mp4",
    "cursorCaptureMode": "editable-overlay"
  },
  "editor": {
    "trimRegions": [],
    "zoomRegions": [],
    "speedRegions": [],
    "annotationRegions": []
  }
}
```

旧projectはtop-level `videoPath`を使うことがある。OpenScreen loaderが許容していても、helperは未知fieldを保持する。

主要region:

```json
{
  "trim": { "id": "trim-1", "startMs": 1000, "endMs": 1800 },
  "zoom": {
    "id": "zoom-1",
    "startMs": 2000,
    "endMs": 5000,
    "depth": 3,
    "focus": { "cx": 0.7, "cy": 0.35 },
    "focusMode": "manual",
    "source": "manual"
  },
  "text": {
    "id": "heading-1",
    "startMs": 0,
    "endMs": 8000,
    "type": "text",
    "content": "Heading",
    "textContent": "Heading",
    "position": { "x": 4, "y": 4 },
    "size": { "width": 72, "height": 11 },
    "style": {},
    "zIndex": 1
  }
}
```

`startMs`/`endMs`はtrim圧縮前のraw/source寄りruler time。cut済みexport上の時刻をそのまま再編集へ使わない。

Zoom `depth`はordinalで、1..6が概ね1.25x、1.5x、1.8x、2.2x、3.5x、5xに対応する。`customScale`があるbuildではdepthより優先され得るため、depthだけ直す場合は実機挙動をpreviewする。

Annotationの`position`はbox左上、`position`/`size`はcanvasに対する百分率。text animationは`none`、`fade`、`rise`、`pop`、`slide-left`、`typewriter`、`pulse`。

### document-v7

GUI project directoryで使われるSSOT。top-levelには概ね次がある。

```text
schemaVersion, project, assets, transcript, transcripts, timeline,
annotations, zoomRanges, audioTracks, legacyEditor
```

- cutは`timeline.trimRanges[]`のsource secondsで、`assetId`と`clipId`を参照する。
- clipは`sourceStartSec/sourceEndSec`と`timelineStartSec/timelineEndSec`の対応を持つ。
- zoom/annotationは`clipId/sourceStartSec/sourceEndSec`が正本で、`startMs/endMs`はderived cacheである。
- clip境界をまたぐmodifierは複数fragmentへ分割する必要がある。同梱helperは曖昧な自動分割をせず拒否する。
- 字幕は`transcripts[].words`からliveに派生する。legacy auto-caption annotationを追加しない。
- word修正では、word text、所属segment text、primary assetのroot `transcript` mirrorを同期する。
- GUIからimportした`audioTracks`はrecordingへ重ねてpreview/exportされる。legacy CLIの`--audio-mode replace`と同じ原音除外を仮定しない。

確認時点のv1.10系ではCLI `export`/`captions`のvalidatorがlegacy `{version, media, editor}`を要求する。一方GUI projectはdocument-v7を保存する。公式のv7→v2変換はない。この互換性を実機で確認できるまで、document-v7はGUI preview/exportへ回す。

## Caption settings（document-v7）

`legacyEditor.captions`が表示設定を持つ。v1.10.0の主要既定値:

```json
{
  "enabled": false,
  "language": null,
  "fontSize": 48,
  "fontFamily": "Inter",
  "fontWeight": "bold",
  "color": "#ffffff",
  "backgroundEnabled": true,
  "backgroundColor": "#000000",
  "backgroundOpacity": 0.55,
  "anchorV": "bottom",
  "insetY": 1.5,
  "anchorH": "center",
  "insetX": 10,
  "minWordsPerLine": 2,
  "maxWordsPerLine": 7
}
```

縦長出力では既定insetが変わり得る。GUI previewを正とする。
