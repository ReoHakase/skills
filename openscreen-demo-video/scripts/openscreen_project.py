#!/usr/bin/env python3
"""OpenScreenプロジェクトを非破壊で点検・限定編集する補助CLI。"""

from __future__ import annotations

import argparse
import copy
import csv
import html
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Any


class ProjectError(ValueError):
    """入力やプロジェクト形式が安全に処理できない場合のエラー。"""


LEGACY_FORMAT = "legacy-v2"
DOCUMENT_FORMAT = "document-v7"
TEXT_STYLE = {
    "color": "#ffffff",
    "backgroundColor": "transparent",
    "fontSize": 32,
    "fontFamily": "Inter",
    "fontWeight": "bold",
    "fontStyle": "normal",
    "textDecoration": "none",
    "textAlign": "left",
    "textAnimation": "none",
}
TEXT_PRESETS = {
    "heading": {
        "position": {"x": 4, "y": 4},
        "size": {"width": 72, "height": 11},
        "style": TEXT_STYLE,
    },
    # OpenScreen標準字幕（y=86, height=12）と重ねない。
    "note": {
        "position": {"x": 4, "y": 70},
        "size": {"width": 58, "height": 13},
        "style": {
            **TEXT_STYLE,
            "backgroundColor": "rgba(0, 0, 0, 0.65)",
            "fontSize": 24,
            "fontWeight": "normal",
        },
    },
}
CAPTION_LAYOUT = {
    "position": {"x": 4, "y": 86},
    "size": {"width": 92, "height": 12},
    "style": {
        **TEXT_STYLE,
        "backgroundColor": "rgba(255, 255, 255, 0)",
        "fontSize": 24,
        "fontWeight": "normal",
        "textAlign": "center",
    },
}
TIME_RE = re.compile(r"^(?:(?P<h>\d+):)?(?P<m>\d{2}):(?P<s>\d{2})[.,](?P<ms>\d{3})$")
ALLOWED_PLAN_KEYS = {"trimRegions", "zoomRegions", "textAnnotations", "deleteIds"}


def load_json(path: Path) -> dict[str, Any]:
    """JSON objectを読み込む。"""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProjectError(f"ファイルがありません: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProjectError(f"JSONとして読めません: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectError(f"JSONのルートはobjectである必要があります: {path}")
    return value


def detect_format(project: dict[str, Any]) -> str:
    """対応する2種類の.openscreen形式を判定する。"""
    if project.get("version") == 2 and isinstance(project.get("editor"), dict):
        return LEGACY_FORMAT
    if project.get("schemaVersion") == 7:
        required = ("project", "assets", "timeline", "annotations", "zoomRanges")
        if all(key in project for key in required):
            return DOCUMENT_FORMAT
    if "schemaVersion" in project:
        raise ProjectError(
            f"未対応のdocument schemaVersionです: {project.get('schemaVersion')!r}（対応: 7）"
        )
    if "version" in project:
        raise ProjectError(f"未対応のlegacy versionです: {project.get('version')!r}（対応: 2）")
    raise ProjectError("対応するOpenScreen JSON形式ではありません")


def finite_number(value: Any, label: str) -> float:
    """boolを除く有限数へ変換する。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProjectError(f"{label} は数値である必要があります")
    result = float(value)
    if not math.isfinite(result):
        raise ProjectError(f"{label} は有限数である必要があります")
    return result


def integer_ms(value: Any, label: str) -> int:
    """非負のミリ秒へ変換する。"""
    result = round(finite_number(value, label))
    if result < 0:
        raise ProjectError(f"{label} は0以上である必要があります")
    return result


def require_id(value: Any, label: str) -> str:
    """空でないIDを検証する。"""
    if not isinstance(value, str) or not value.strip():
        raise ProjectError(f"{label} は空でない文字列である必要があります")
    return value.strip()


def interval_ms(
    item: dict[str, Any], existing: dict[str, Any] | None, label: str
) -> tuple[int, int]:
    """plan itemと既存regionから編集後の区間を得る。"""
    if "startMs" in item:
        start = integer_ms(item["startMs"], f"{label}.startMs")
    elif existing is not None and "startMs" in existing:
        start = integer_ms(existing["startMs"], f"{label}.startMs")
    else:
        raise ProjectError(f"新規{label}には startMs が必要です")
    if "endMs" in item:
        end = integer_ms(item["endMs"], f"{label}.endMs")
    elif existing is not None and "endMs" in existing:
        end = integer_ms(existing["endMs"], f"{label}.endMs")
    else:
        raise ProjectError(f"新規{label}には endMs が必要です")
    if end <= start:
        raise ProjectError(f"{label} は endMs > startMs である必要があります")
    return start, end


def project_arrays(
    project: dict[str, Any], project_format: str
) -> tuple[list[Any], list[Any], list[Any]]:
    """annotation/zoom/trim配列を形式差なしで返す。"""
    if project_format == LEGACY_FORMAT:
        editor = project["editor"]
        return (
            editor.setdefault("annotationRegions", []),
            editor.setdefault("zoomRegions", []),
            editor.setdefault("trimRegions", []),
        )
    timeline = project["timeline"]
    if not isinstance(timeline, dict):
        raise ProjectError("timeline はobjectである必要があります")
    return (
        project["annotations"],
        project["zoomRanges"],
        timeline.setdefault("trimRanges", []),
    )


def ensure_lists(*values: Any) -> None:
    """編集対象がすべてarrayであることを確認する。"""
    if not all(isinstance(value, list) for value in values):
        raise ProjectError("編集regionの格納先がarrayではありません")


def write_project(
    source: Path,
    output: Path,
    project: dict[str, Any],
    *,
    force: bool,
) -> None:
    """元ファイルを拒否し、別pathへatomicにJSONを書き出す。"""
    if source.resolve() == output.resolve():
        raise ProjectError("元の.openscreenは上書きできません。別の --output を指定してください")
    if output.exists() and not force:
        raise ProjectError(f"出力先が既にあります（上書きには --force）: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(project, ensure_ascii=False, indent=2) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def raw_trim_spans(project: dict[str, Any], project_format: str) -> list[tuple[int, int]]:
    """trimを編集前timeline上のミリ秒区間へ揃える。"""
    _, _, trims = project_arrays(project, project_format)
    ensure_lists(trims)
    spans: list[tuple[int, int]] = []
    if project_format == LEGACY_FORMAT:
        for index, trim in enumerate(trims):
            if not isinstance(trim, dict):
                raise ProjectError(f"trimRegions[{index}] がobjectではありません")
            spans.append(interval_ms(trim, None, f"trimRegions[{index}]"))
        return merge_spans(spans)

    clips = clips_by_id(project)
    for index, trim in enumerate(trims):
        if not isinstance(trim, dict):
            raise ProjectError(f"trimRanges[{index}] がobjectではありません")
        clip_id = require_id(trim.get("clipId"), f"trimRanges[{index}].clipId")
        clip = clips.get(clip_id)
        if clip is None:
            raise ProjectError(f"trimRanges[{index}] のclipIdが見つかりません: {clip_id}")
        source_start = finite_number(trim.get("startSec"), f"trimRanges[{index}].startSec")
        source_end = finite_number(trim.get("endSec"), f"trimRanges[{index}].endSec")
        clip_source_start = finite_number(clip.get("sourceStartSec"), "clip.sourceStartSec")
        timeline_start = finite_number(clip.get("timelineStartSec"), "clip.timelineStartSec")
        start = round((timeline_start + source_start - clip_source_start) * 1000)
        end = round((timeline_start + source_end - clip_source_start) * 1000)
        if start < 0 or end <= start:
            raise ProjectError(f"trimRanges[{index}] の時間対応が不正です")
        spans.append((start, end))
    return merge_spans(spans)


def merge_spans(spans: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    """重なる区間を結合する。"""
    merged: list[list[int]] = []
    for start, end in sorted(spans):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(start, end) for start, end in merged]


def inspect_project(project: dict[str, Any], project_format: str) -> dict[str, Any]:
    """レビュー用の機械可読summaryを作る。"""
    annotations, zooms, trims = project_arrays(project, project_format)
    ensure_lists(annotations, zooms, trims)
    if project_format == LEGACY_FORMAT:
        media = project.get("media")
        if not isinstance(media, dict):
            media = {}
        return {
            "format": project_format,
            "version": project.get("version"),
            "screenVideoPath": media.get("screenVideoPath") or project.get("videoPath"),
            "annotations": len(annotations),
            "autoCaptions": sum(
                isinstance(item, dict) and item.get("annotationSource") == "auto-caption"
                for item in annotations
            ),
            "zooms": len(zooms),
            "trims": len(trims),
        }
    assets = project.get("assets")
    transcripts = project.get("transcripts")
    clips = project.get("timeline", {}).get("clips")
    if (
        not isinstance(assets, list)
        or not isinstance(transcripts, list)
        or not isinstance(clips, list)
    ):
        raise ProjectError("編集regionの格納先がarrayではありません")
    return {
        "format": project_format,
        "schemaVersion": project.get("schemaVersion"),
        "title": project.get("project", {}).get("title"),
        "assets": len(assets),
        "clips": len(clips),
        "transcripts": len(transcripts),
        "transcriptWords": sum(
            len(item.get("words", [])) for item in transcripts if isinstance(item, dict)
        ),
        "annotations": len(annotations),
        "zooms": len(zooms),
        "trims": len(trims),
        "cliCompatibility": "GUI document-v7; current export/captions CLI may reject it",
    }


def print_inspection(summary: dict[str, Any], as_json: bool) -> None:
    """summaryをstdoutへ出す。"""
    if as_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return
    for key, value in summary.items():
        print(f"{key}: {value}")


def format_vtt_time(milliseconds: int) -> str:
    """ミリ秒をWebVTT timestampへ変換する。"""
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def parse_vtt_time(value: str) -> int:
    """WebVTT timestampをミリ秒へ変換する。"""
    match = TIME_RE.fullmatch(value.strip())
    if not match:
        raise ProjectError(f"未対応のWebVTT timestampです: {value!r}")
    hours = int(match.group("h") or 0)
    minutes = int(match.group("m"))
    seconds = int(match.group("s"))
    millis = int(match.group("ms"))
    if minutes >= 60 or seconds >= 60:
        raise ProjectError(f"不正なWebVTT timestampです: {value!r}")
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def export_vtt(project: dict[str, Any], project_format: str, output: Path) -> int:
    """legacy auto-caption annotationをWebVTTへ書き出す。"""
    if project_format != LEGACY_FORMAT:
        raise ProjectError(
            "document-v7の字幕正本はtranscripts[].wordsです。export-transcript-tsvを使ってください"
        )
    annotations, _, _ = project_arrays(project, project_format)
    cues = [
        item
        for item in annotations
        if isinstance(item, dict) and item.get("annotationSource") == "auto-caption"
    ]
    cues.sort(key=lambda item: (item.get("startMs", 0), item.get("endMs", 0)))
    if not cues:
        raise ProjectError(
            "auto-caption annotationがありません。先に openscreen captions を実行してください"
        )
    lines = ["WEBVTT", ""]
    for index, cue in enumerate(cues):
        cue_id = require_id(cue.get("id"), f"caption[{index}].id")
        start, end = interval_ms(cue, None, f"caption[{index}]")
        text = cue.get("textContent", cue.get("content", ""))
        if not isinstance(text, str):
            raise ProjectError(f"caption[{index}] のtextが文字列ではありません")
        lines.extend([cue_id, f"{format_vtt_time(start)} --> {format_vtt_time(end)}", text, ""])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return len(cues)


def parse_vtt(path: Path) -> list[dict[str, Any]]:
    """plain-text WebVTT cueを読む。"""
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if not lines or not lines[0].strip().startswith("WEBVTT"):
        raise ProjectError("WebVTTは WEBVTT headerで始めてください")
    cues: list[dict[str, Any]] = []
    cue_ids: set[str] = set()
    index = 1
    while index < len(lines):
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines):
            break
        if lines[index].lstrip().startswith(("NOTE", "STYLE", "REGION")):
            while index < len(lines) and lines[index].strip():
                index += 1
            continue
        cue_id = ""
        timing = lines[index].strip()
        if "-->" not in timing:
            cue_id = timing
            if cue_id in cue_ids:
                raise ProjectError(f"WebVTT cue IDが重複しています: {cue_id}")
            cue_ids.add(cue_id)
            index += 1
            if index >= len(lines):
                raise ProjectError(f"cue {cue_id!r} にtiming行がありません")
            timing = lines[index].strip()
        if "-->" not in timing:
            raise ProjectError(f"WebVTT timing行ではありません: {timing!r}")
        left, right = (part.strip() for part in timing.split("-->", 1))
        end_token = right.split()[0]
        start = parse_vtt_time(left)
        end = parse_vtt_time(end_token)
        if end <= start:
            raise ProjectError(f"cue {cue_id or len(cues) + 1} は end > start である必要があります")
        index += 1
        content: list[str] = []
        while index < len(lines) and lines[index].strip():
            content.append(lines[index])
            index += 1
        cue_text = html.unescape("\n".join(content).strip())
        if not cue_text:
            raise ProjectError(f"cue {cue_id or len(cues) + 1} の本文が空です")
        cues.append({"id": cue_id, "startMs": start, "endMs": end, "text": cue_text})
    if not cues:
        raise ProjectError("WebVTTにcueがありません")
    return cues


def next_annotation_id(used_ids: set[str]) -> str:
    """OpenScreen標準に近い一意なannotation IDを作る。"""
    largest = 0
    for value in used_ids:
        match = re.search(r"(\d+)$", value)
        if match:
            largest = max(largest, int(match.group(1)))
    while True:
        largest += 1
        candidate = f"annotation-{largest}"
        if candidate not in used_ids:
            return candidate


def import_vtt(
    project: dict[str, Any],
    project_format: str,
    cues: list[dict[str, Any]],
) -> dict[str, Any]:
    """WebVTTをlegacy auto-caption annotationsへ置換する。"""
    if project_format != LEGACY_FORMAT:
        raise ProjectError(
            "document-v7へVTTを直接importしないでください。import-transcript-tsvでword単位に修正します"
        )
    result = copy.deepcopy(project)
    annotations, zooms, trims = project_arrays(result, project_format)
    ensure_lists(annotations, zooms, trims)
    old_auto = {
        item["id"]: item
        for item in annotations
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and item.get("annotationSource") == "auto-caption"
    }
    manual = [
        item
        for item in annotations
        if not (isinstance(item, dict) and item.get("annotationSource") == "auto-caption")
    ]
    all_regions = [*manual, *zooms, *trims]
    used_ids = {
        item["id"]
        for item in all_regions
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    z_index = max(
        (int(item.get("zIndex", 0)) for item in manual if isinstance(item, dict)),
        default=0,
    )
    template = next(iter(old_auto.values()), None)
    imported: list[dict[str, Any]] = []
    seen_cue_ids: set[str] = set()
    for cue in cues:
        requested_id = cue["id"]
        if requested_id in old_auto and requested_id not in seen_cue_ids:
            region_id = requested_id
        else:
            region_id = next_annotation_id(used_ids | seen_cue_ids)
        seen_cue_ids.add(region_id)
        base = copy.deepcopy(old_auto.get(region_id, template or CAPTION_LAYOUT))
        if not isinstance(base, dict):
            base = copy.deepcopy(CAPTION_LAYOUT)
        z_index += 1
        base.update(
            {
                "id": region_id,
                "startMs": cue["startMs"],
                "endMs": cue["endMs"],
                "type": "text",
                "content": cue["text"],
                "textContent": cue["text"],
                "annotationSource": "auto-caption",
                "zIndex": z_index,
            }
        )
        for key in ("position", "size", "style"):
            if key not in base:
                base[key] = copy.deepcopy(CAPTION_LAYOUT[key])
        imported.append(base)
    result["editor"]["annotationRegions"] = [*manual, *imported]
    validate_region_ids(result, project_format)
    return result


TSV_FIELDS = [
    "asset_id",
    "word_id",
    "segment_id",
    "start_sec",
    "end_sec",
    "expected_text",
    "corrected_text",
    "original_text",
    "source",
]


def document_transcripts(project: dict[str, Any]) -> list[dict[str, Any]]:
    """document-v7のtranscript配列を検証して返す。"""
    transcripts = project.get("transcripts")
    if not isinstance(transcripts, list):
        raise ProjectError("transcripts がarrayではありません")
    if not all(isinstance(item, dict) for item in transcripts):
        raise ProjectError("transcripts[] にobject以外が含まれています")
    return transcripts


def export_transcript_tsv(project: dict[str, Any], project_format: str, output: Path) -> int:
    """document-v7 transcriptをword単位TSVへ書き出す。"""
    if project_format != DOCUMENT_FORMAT:
        raise ProjectError("legacy-v2の字幕修正には export-vtt を使ってください")
    transcripts = document_transcripts(project)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TSV_FIELDS, delimiter="\t")
        writer.writeheader()
        for transcript in transcripts:
            asset_id = require_id(transcript.get("assetId"), "transcript.assetId")
            words = transcript.get("words")
            if not isinstance(words, list):
                raise ProjectError(f"transcript {asset_id} のwordsがarrayではありません")
            for word in words:
                if not isinstance(word, dict):
                    raise ProjectError(f"transcript {asset_id} のwordがobjectではありません")
                writer.writerow(
                    {
                        "asset_id": asset_id,
                        "word_id": word.get("id", ""),
                        "segment_id": word.get("segmentId", ""),
                        "start_sec": word.get("startSec", ""),
                        "end_sec": word.get("endSec", ""),
                        "expected_text": word.get("text", ""),
                        "corrected_text": word.get("text", ""),
                        "original_text": word.get("originalText", ""),
                        "source": word.get("source", ""),
                    }
                )
                count += 1
    if count == 0:
        raise ProjectError("transcript wordがありません")
    return count


def is_cjk(character: str) -> bool:
    """日本語・中国語の語間空白を避けるため文字種を粗く判定する。"""
    if not character:
        return False
    name = unicodedata.name(character, "")
    return any(token in name for token in ("CJK", "HIRAGANA", "KATAKANA"))


def join_segment_text(values: Iterable[str]) -> str:
    """公式setWordText相当の規則でsegment本文を再構築する。"""
    tokens = [value.strip() for value in values if value.strip()]
    result = ""
    closing = set(",.;:!?%。，、；：！？…）)]}>》」』】〕")
    opening = set("([<{《「『【〔（")
    for token in tokens:
        if not result:
            result = token
        elif token[0] in closing or result[-1] in opening:
            result += token
        else:
            left_content = result.rstrip("".join(closing))
            left_edge = left_content[-1] if left_content else ""
            if is_cjk(left_edge) and is_cjk(token[0]):
                result += token
            else:
                result += f" {token}"
            continue
    return result


def import_transcript_tsv(
    project: dict[str, Any],
    project_format: str,
    tsv_path: Path,
) -> tuple[dict[str, Any], int]:
    """word textだけを反映し、provenanceとlegacy mirrorを同期する。"""
    if project_format != DOCUMENT_FORMAT:
        raise ProjectError("legacy-v2の字幕修正には import-vtt を使ってください")
    result = copy.deepcopy(project)
    transcripts = document_transcripts(result)
    words: dict[tuple[str, str], dict[str, Any]] = {}
    for transcript in transcripts:
        asset_id = require_id(transcript.get("assetId"), "transcript.assetId")
        transcript_words = transcript.get("words")
        if not isinstance(transcript_words, list):
            raise ProjectError(f"transcript {asset_id} のwordsがarrayではありません")
        for word in transcript_words:
            if not isinstance(word, dict):
                raise ProjectError(f"transcript {asset_id} のwordがobjectではありません")
            key = (asset_id, require_id(word.get("id"), "word.id"))
            if key in words:
                raise ProjectError(f"word IDが重複しています: {key}")
            words[key] = word

    with tsv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != TSV_FIELDS:
            raise ProjectError(f"TSV headerを変更しないでください: {TSV_FIELDS}")
        rows = list(reader)
    row_keys: set[tuple[str, str]] = set()
    changed = 0
    for row_number, row in enumerate(rows, start=2):
        key = (row["asset_id"], row["word_id"])
        if key in row_keys:
            raise ProjectError(f"TSV {row_number}行目: wordが重複しています: {key}")
        row_keys.add(key)
        word = words.get(key)
        if word is None:
            raise ProjectError(f"TSV {row_number}行目: projectに存在しないwordです: {key}")
        fixed_columns = {
            "segment_id": str(word.get("segmentId", "")),
            "start_sec": str(word.get("startSec", "")),
            "end_sec": str(word.get("endSec", "")),
            "expected_text": str(word.get("text", "")),
        }
        for column, expected in fixed_columns.items():
            if row[column] != expected:
                if column == "expected_text":
                    raise ProjectError(
                        f"TSV {row_number}行目: expected_textがprojectと一致しません。"
                        "GUIを閉じ、最新projectからTSVを再exportしてください"
                    )
                raise ProjectError(f"TSV {row_number}行目: {column} は編集しないでください")
        new_text = row["corrected_text"]
        if new_text == word.get("text", ""):
            continue
        if word.get("source") == "synth":
            word["text"] = new_text
        else:
            original = word.get("originalText", word.get("text", ""))
            word["text"] = new_text
            if new_text == original:
                word.pop("originalText", None)
                word.pop("source", None)
            else:
                word["originalText"] = original
                word["source"] = "user"
        changed += 1
    if row_keys != set(words):
        missing = sorted(set(words) - row_keys)[:3]
        raise ProjectError(f"TSVからword行が欠落しています（例: {missing}）")

    for transcript in transcripts:
        by_id = {word["id"]: word for word in transcript.get("words", [])}
        segments = transcript.get("segments")
        if not isinstance(segments, list):
            raise ProjectError("transcript.segments がarrayではありません")
        for segment in segments:
            if not isinstance(segment, dict) or not isinstance(segment.get("wordIds"), list):
                raise ProjectError("transcript segmentの形が不正です")
            try:
                segment["text"] = join_segment_text(
                    by_id[word_id]["text"] for word_id in segment["wordIds"]
                )
            except KeyError as exc:
                raise ProjectError(f"segmentが存在しないwordを参照しています: {exc}") from exc

    primary_asset_id = result.get("project", {}).get("primaryAssetId")
    primary = next((item for item in transcripts if item.get("assetId") == primary_asset_id), None)
    if primary is not None:
        result["transcript"] = copy.deepcopy(primary)
    return result, changed


def clips_by_id(project: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """document-v7 clipをIDで引く。"""
    clips = project.get("timeline", {}).get("clips")
    if not isinstance(clips, list):
        raise ProjectError("timeline.clips がarrayではありません")
    result: dict[str, dict[str, Any]] = {}
    for clip in clips:
        if not isinstance(clip, dict):
            raise ProjectError("timeline.clips[] がobjectではありません")
        clip_id = require_id(clip.get("id"), "clip.id")
        if clip_id in result:
            raise ProjectError(f"clip IDが重複しています: {clip_id}")
        result[clip_id] = clip
    return result


def anchor_interval(project: dict[str, Any], start_ms: int, end_ms: int) -> dict[str, Any]:
    """単一clip内のtimeline区間をdocument-v7 source区間へ対応付ける。"""
    start_sec = start_ms / 1000
    end_sec = end_ms / 1000
    matches: list[dict[str, Any]] = []
    for clip in clips_by_id(project).values():
        timeline_start = finite_number(clip.get("timelineStartSec"), "clip.timelineStartSec")
        timeline_end = finite_number(clip.get("timelineEndSec"), "clip.timelineEndSec")
        if start_sec >= timeline_start and end_sec <= timeline_end:
            matches.append(clip)
    if len(matches) != 1:
        raise ProjectError(
            f"document-v7の {start_sec:.3f}–{end_sec:.3f}s は単一clip内に収まりません。"
            "clip境界でplanを分割するかOpenScreen GUIで編集してください"
        )
    clip = matches[0]
    source_base = finite_number(clip.get("sourceStartSec"), "clip.sourceStartSec")
    timeline_base = finite_number(clip.get("timelineStartSec"), "clip.timelineStartSec")
    return {
        "assetId": require_id(clip.get("assetId"), "clip.assetId"),
        "clipId": require_id(clip.get("id"), "clip.id"),
        "sourceStartSec": source_base + start_sec - timeline_base,
        "sourceEndSec": source_base + end_sec - timeline_base,
    }


def index_regions(regions: list[Any], label: str) -> dict[str, dict[str, Any]]:
    """region配列をIDで引く。"""
    result: dict[str, dict[str, Any]] = {}
    for index, region in enumerate(regions):
        if not isinstance(region, dict):
            raise ProjectError(f"{label}[{index}] がobjectではありません")
        region_id = require_id(region.get("id"), f"{label}[{index}].id")
        if region_id in result:
            raise ProjectError(f"{label}内でIDが重複しています: {region_id}")
        result[region_id] = region
    return result


def upsert(items: list[dict[str, Any]], region: dict[str, Any]) -> None:
    """同じIDを置換し、なければ末尾へ追加する。"""
    for index, item in enumerate(items):
        if item.get("id") == region["id"]:
            items[index] = region
            return
    items.append(region)


def apply_edit_plan(
    project: dict[str, Any],
    project_format: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """限定されたedit planを2形式のregionへ適用する。"""
    unknown = set(plan) - ALLOWED_PLAN_KEYS
    if unknown:
        raise ProjectError(f"edit planに未対応keyがあります: {sorted(unknown)}")
    result = copy.deepcopy(project)
    annotations, zooms, trims = project_arrays(result, project_format)
    ensure_lists(annotations, zooms, trims)
    validate_region_ids(result, project_format)
    for key in ("trimRegions", "zoomRegions", "textAnnotations", "deleteIds"):
        if key in plan and not isinstance(plan[key], list):
            raise ProjectError(f"edit planの {key} はarrayである必要があります")

    delete_ids = {require_id(value, "deleteIds[]") for value in plan.get("deleteIds", [])}
    annotations[:] = [item for item in annotations if item.get("id") not in delete_ids]
    zooms[:] = [item for item in zooms if item.get("id") not in delete_ids]
    trims[:] = [item for item in trims if item.get("id") not in delete_ids]

    trim_index = index_regions(trims, "trimRegions")
    for position, item in enumerate(plan.get("trimRegions", [])):
        if not isinstance(item, dict):
            raise ProjectError(f"trimRegions[{position}] がobjectではありません")
        region_id = require_id(item.get("id"), f"trimRegions[{position}].id")
        existing = trim_index.get(region_id)
        if project_format == DOCUMENT_FORMAT and existing is not None:
            # v7 trimはsource timeのみなので、更新時もplanにtimeline timeを明示させる。
            if "startMs" not in item or "endMs" not in item:
                raise ProjectError(
                    "document-v7のtrim更新には startMs と endMs を両方指定してください"
                )
        start, end = interval_ms(item, existing, f"trimRegions[{position}]")
        if project_format == LEGACY_FORMAT:
            region = {**(existing or {}), "id": region_id, "startMs": start, "endMs": end}
        else:
            anchor = anchor_interval(result, start, end)
            region = {
                **(existing or {}),
                "id": region_id,
                "assetId": anchor["assetId"],
                "clipId": anchor["clipId"],
                "startSec": anchor["sourceStartSec"],
                "endSec": anchor["sourceEndSec"],
                "reason": str(item.get("reason", (existing or {}).get("reason", "manual cut"))),
                "origin": "user",
            }
        upsert(trims, region)
        trim_index[region_id] = region

    zoom_index = index_regions(zooms, "zoomRegions")
    for position, item in enumerate(plan.get("zoomRegions", [])):
        if not isinstance(item, dict):
            raise ProjectError(f"zoomRegions[{position}] がobjectではありません")
        region_id = require_id(item.get("id"), f"zoomRegions[{position}].id")
        existing = zoom_index.get(region_id)
        start, end = interval_ms(item, existing, f"zoomRegions[{position}]")
        depth = item.get("depth", (existing or {}).get("depth", 3))
        if isinstance(depth, bool) or not isinstance(depth, int) or depth not in range(1, 7):
            raise ProjectError(f"zoomRegions[{position}].depth は1..6の整数です")
        focus = copy.deepcopy(
            item.get("focus", (existing or {}).get("focus", {"cx": 0.5, "cy": 0.5}))
        )
        if not isinstance(focus, dict):
            raise ProjectError(f"zoomRegions[{position}].focus はobjectです")
        cx = finite_number(focus.get("cx"), f"zoomRegions[{position}].focus.cx")
        cy = finite_number(focus.get("cy"), f"zoomRegions[{position}].focus.cy")
        if not 0 <= cx <= 1 or not 0 <= cy <= 1:
            raise ProjectError("zoom focusのcx/cyは0..1です")
        region = {
            **(existing or {}),
            "id": region_id,
            "startMs": start,
            "endMs": end,
            "depth": depth,
            "focus": {"cx": cx, "cy": cy},
            "focusMode": item.get("focusMode", (existing or {}).get("focusMode", "manual")),
            "source": item.get("source", (existing or {}).get("source", "manual")),
        }
        if region["focusMode"] not in ("manual", "auto"):
            raise ProjectError("zoom focusModeはmanualまたはautoです")
        if region["source"] not in ("manual", "auto"):
            raise ProjectError("zoom sourceはmanualまたはautoです")
        if "customScale" in item:
            if item["customScale"] is None:
                region.pop("customScale", None)
            else:
                custom_scale = finite_number(
                    item["customScale"], f"zoomRegions[{position}].customScale"
                )
                if not 1 <= custom_scale <= 5:
                    raise ProjectError("zoom customScaleは1..5です")
                region["customScale"] = custom_scale
        elif "depth" in item:
            # customScaleはdepthより優先されるため、depth修正時に古い値を残さない。
            region.pop("customScale", None)
        if "rotationPreset" in item:
            if item["rotationPreset"] not in ("iso", "left", "right", None):
                raise ProjectError("rotationPresetはiso/left/right/nullです")
            if item["rotationPreset"] is None:
                region.pop("rotationPreset", None)
            else:
                region["rotationPreset"] = item["rotationPreset"]
        if project_format == DOCUMENT_FORMAT:
            region.update(anchor_interval(result, start, end))
        upsert(zooms, region)
        zoom_index[region_id] = region

    annotation_index = index_regions(annotations, "textAnnotations")
    next_z = max(
        (int(item.get("zIndex", 0)) for item in annotations if isinstance(item, dict)),
        default=0,
    )
    for position, item in enumerate(plan.get("textAnnotations", [])):
        if not isinstance(item, dict):
            raise ProjectError(f"textAnnotations[{position}] がobjectではありません")
        region_id = require_id(item.get("id"), f"textAnnotations[{position}].id")
        existing = annotation_index.get(region_id)
        if existing is not None and existing.get("annotationSource") == "auto-caption":
            raise ProjectError("auto-caption本文はVTT/TSV workflowで修正してください")
        if existing is not None and existing.get("type") != "text":
            raise ProjectError(f"既存annotation {region_id} はtextではありません")
        start, end = interval_ms(item, existing, f"textAnnotations[{position}]")
        preset_name = item.get("preset")
        if preset_name is not None and preset_name not in TEXT_PRESETS:
            raise ProjectError("text presetはheadingまたはnoteです")
        if existing is None:
            preset = copy.deepcopy(TEXT_PRESETS[preset_name or "heading"])
            next_z += 1
            region: dict[str, Any] = {
                "id": region_id,
                "type": "text",
                "content": "",
                "textContent": "",
                "zIndex": next_z,
                **preset,
            }
        else:
            region = copy.deepcopy(existing)
            if preset_name is not None:
                region.update(copy.deepcopy(TEXT_PRESETS[preset_name]))
        text = item.get("text", region.get("textContent", region.get("content")))
        if not isinstance(text, str) or not text.strip():
            raise ProjectError(f"textAnnotations[{position}].text は空でない文字列です")
        region.update(
            {
                "id": region_id,
                "startMs": start,
                "endMs": end,
                "type": "text",
                "content": text,
                "textContent": text,
            }
        )
        for key in ("position", "size", "style"):
            if key in item:
                if not isinstance(item[key], dict):
                    raise ProjectError(f"textAnnotations[{position}].{key} はobjectです")
                region[key] = {**region.get(key, {}), **item[key]}
        if "zIndex" in item:
            region["zIndex"] = int(finite_number(item["zIndex"], "zIndex"))
        validate_text_region(region, f"textAnnotations[{position}]")
        if project_format == DOCUMENT_FORMAT:
            region.update(anchor_interval(result, start, end))
        upsert(annotations, region)
        annotation_index[region_id] = region

    validate_region_ids(result, project_format)
    return result


def validate_text_region(region: dict[str, Any], label: str) -> None:
    """OpenScreen text annotationの主要boundsを確認する。"""
    for key in ("position", "size", "style"):
        if not isinstance(region.get(key), dict):
            raise ProjectError(f"{label}.{key} がobjectではありません")
    x = finite_number(region["position"].get("x"), f"{label}.position.x")
    y = finite_number(region["position"].get("y"), f"{label}.position.y")
    width = finite_number(region["size"].get("width"), f"{label}.size.width")
    height = finite_number(region["size"].get("height"), f"{label}.size.height")
    if not (0 <= x <= 100 and 0 <= y <= 100 and width > 0 and height > 0):
        raise ProjectError(f"{label} のposition/sizeが範囲外です")


def validate_region_ids(project: dict[str, Any], project_format: str) -> None:
    """全modifierでIDが一意であることを確認する。"""
    annotations, zooms, trims = project_arrays(project, project_format)
    ensure_lists(annotations, zooms, trims)
    ids: set[str] = set()
    for label, regions in (("annotation", annotations), ("zoom", zooms), ("trim", trims)):
        for index, region in enumerate(regions):
            if not isinstance(region, dict):
                raise ProjectError(f"{label}[{index}] がobjectではありません")
            region_id = require_id(region.get("id"), f"{label}[{index}].id")
            if region_id in ids:
                raise ProjectError(f"modifier IDが重複しています: {region_id}")
            ids.add(region_id)


def document_transcript_cues(project: dict[str, Any], project_format: str) -> list[dict[str, Any]]:
    """v7 transcript segmentをclipごとのraw timeline cueへ写す。"""
    if project_format != DOCUMENT_FORMAT:
        raise ProjectError("legacy-v2の台本化には make-script と修正VTTを使ってください")

    transcripts_by_asset: dict[str, dict[str, Any]] = {}
    for transcript in document_transcripts(project):
        asset_id = require_id(transcript.get("assetId"), "transcript.assetId")
        if asset_id in transcripts_by_asset:
            raise ProjectError(f"同じassetのtranscriptが重複しています: {asset_id}")
        segments = transcript.get("segments")
        if not isinstance(segments, list):
            raise ProjectError(f"transcript {asset_id} のsegmentsがarrayではありません")
        transcripts_by_asset[asset_id] = transcript

    clips = list(clips_by_id(project).values())
    clips.sort(
        key=lambda clip: finite_number(clip.get("timelineStartSec"), "clip.timelineStartSec")
    )
    cues: list[dict[str, Any]] = []
    for clip in clips:
        clip_id = require_id(clip.get("id"), "clip.id")
        asset_id = require_id(clip.get("assetId"), "clip.assetId")
        transcript = transcripts_by_asset.get(asset_id)
        if transcript is None:
            continue
        source_start = finite_number(clip.get("sourceStartSec"), "clip.sourceStartSec")
        timeline_start = finite_number(clip.get("timelineStartSec"), "clip.timelineStartSec")
        timeline_end = finite_number(clip.get("timelineEndSec"), "clip.timelineEndSec")
        source_end_value = clip.get("sourceEndSec")
        source_end = (
            finite_number(source_end_value, "clip.sourceEndSec")
            if source_end_value is not None
            else source_start + timeline_end - timeline_start
        )
        if source_end <= source_start or timeline_end <= timeline_start:
            raise ProjectError(f"clip {clip_id} の時間範囲が不正です")

        segment_ids: set[str] = set()
        for position, segment in enumerate(transcript["segments"]):
            if not isinstance(segment, dict):
                raise ProjectError(f"transcript {asset_id} のsegmentがobjectではありません")
            segment_id = require_id(
                segment.get("id"), f"transcript {asset_id}.segments[{position}].id"
            )
            if segment_id in segment_ids:
                raise ProjectError(f"segment IDが重複しています: {asset_id}/{segment_id}")
            segment_ids.add(segment_id)
            kind = segment.get("kind")
            if kind == "silence":
                continue
            if kind != "speech":
                raise ProjectError(f"segment {asset_id}/{segment_id} のkindが不正です")
            start = finite_number(segment.get("startSec"), f"segment {segment_id}.startSec")
            end = finite_number(segment.get("endSec"), f"segment {segment_id}.endSec")
            if end <= start:
                raise ProjectError(f"segment {asset_id}/{segment_id} の時間範囲が不正です")
            if min(end, source_end) <= max(start, source_start):
                continue
            if start < source_start or end > source_end:
                raise ProjectError(
                    f"segment {asset_id}/{segment_id} がclip {clip_id} のsource境界をまたぎます。"
                    "GUIでsegment/clip境界を直すか、台本を手動レビューしてください"
                )
            text = segment.get("text")
            if not isinstance(text, str):
                raise ProjectError(f"segment {asset_id}/{segment_id} のtextが文字列ではありません")
            if not text.strip():
                continue
            cues.append(
                {
                    "id": f"{clip_id}:{segment_id}",
                    "startMs": round((timeline_start + start - source_start) * 1000),
                    "endMs": round((timeline_start + end - source_start) * 1000),
                    "text": text,
                }
            )

    cues.sort(key=lambda cue: (cue["startMs"], cue["endMs"], cue["id"]))
    if not cues:
        raise ProjectError("timeline上に台本化できるspeech segmentがありません")
    return cues


def make_transcript_script(
    project: dict[str, Any],
    project_format: str,
    markdown_output: Path,
    plain_output: Path | None,
) -> int:
    """v7 transcriptをclipへ写し、cut-aware台本を生成する。"""
    return make_script(
        project,
        project_format,
        document_transcript_cues(project, project_format),
        markdown_output,
        plain_output,
    )


def output_time(raw_ms: int, trims: list[tuple[int, int]]) -> int:
    """raw timeline時刻からtrim圧縮後の時刻を求める。"""
    removed = 0
    for start, end in trims:
        if raw_ms <= start:
            break
        removed += max(0, min(raw_ms, end) - start)
    return max(0, raw_ms - removed)


def cue_trim_note(start: int, end: int, trims: list[tuple[int, int]]) -> str:
    """cueとtrimの関係を分類する。"""
    overlaps = [(a, b) for a, b in trims if min(end, b) > max(start, a)]
    if not overlaps:
        return ""
    covered = sum(min(end, b) - max(start, a) for a, b in overlaps)
    return "removed" if covered >= end - start else "partial trim: review"


def make_script(
    project: dict[str, Any],
    project_format: str,
    cues: list[dict[str, Any]],
    markdown_output: Path,
    plain_output: Path | None,
) -> int:
    """修正済みVTTとcutを突合し、台本を生成する。"""
    trims = raw_trim_spans(project, project_format)
    kept: list[dict[str, Any]] = []
    rows = [
        "# ナレーション台本",
        "",
        "| # | 元時刻 | 編集後時刻 | テキスト | 注記 |",
        "|---:|:---|:---|:---|:---|",
    ]
    for cue in cues:
        note = cue_trim_note(cue["startMs"], cue["endMs"], trims)
        if note == "removed":
            continue
        kept.append(cue)
        source = f"{format_vtt_time(cue['startMs'])}–{format_vtt_time(cue['endMs'])}"
        edited = (
            f"{format_vtt_time(output_time(cue['startMs'], trims))}–"
            f"{format_vtt_time(output_time(cue['endMs'], trims))}"
        )
        safe_text = cue["text"].replace("|", "\\|").replace("\n", "<br>")
        rows.append(f"| {len(kept)} | {source} | {edited} | {safe_text} | {note} |")
    if not kept:
        raise ProjectError("cut後に台本へ残るcueがありません")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text("\n".join(rows) + "\n", encoding="utf-8")
    if plain_output is not None:
        plain_output.parent.mkdir(parents=True, exist_ok=True)
        plain_output.write_text(
            "\n".join(cue["text"].replace("\n", " ") for cue in kept) + "\n", encoding="utf-8"
        )
    return len(kept)


def build_parser() -> argparse.ArgumentParser:
    """CLI parserを作る。"""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="project形式と件数を表示")
    inspect_parser.add_argument("project", type=Path)
    inspect_parser.add_argument("--json", action="store_true")

    export_vtt_parser = subparsers.add_parser("export-vtt", help="legacy captionをVTTへ出力")
    export_vtt_parser.add_argument("project", type=Path)
    export_vtt_parser.add_argument("output", type=Path)

    import_vtt_parser = subparsers.add_parser("import-vtt", help="VTTでlegacy captionを置換")
    import_vtt_parser.add_argument("project", type=Path)
    import_vtt_parser.add_argument("vtt", type=Path)
    import_vtt_parser.add_argument("--output", type=Path, required=True)
    import_vtt_parser.add_argument("--force", action="store_true")

    export_tsv_parser = subparsers.add_parser(
        "export-transcript-tsv", help="document-v7 transcriptをTSVへ出力"
    )
    export_tsv_parser.add_argument("project", type=Path)
    export_tsv_parser.add_argument("output", type=Path)

    import_tsv_parser = subparsers.add_parser(
        "import-transcript-tsv", help="修正TSVをdocument-v7 transcriptへ反映"
    )
    import_tsv_parser.add_argument("project", type=Path)
    import_tsv_parser.add_argument("tsv", type=Path)
    import_tsv_parser.add_argument("--output", type=Path, required=True)
    import_tsv_parser.add_argument("--force", action="store_true")

    apply_parser = subparsers.add_parser("apply-plan", help="cut/zoom/text edit planを適用")
    apply_parser.add_argument("project", type=Path)
    apply_parser.add_argument("plan", type=Path)
    apply_parser.add_argument("--output", type=Path, required=True)
    apply_parser.add_argument("--force", action="store_true")

    script_parser = subparsers.add_parser("make-script", help="VTTとcutから台本を作成")
    script_parser.add_argument("project", type=Path)
    script_parser.add_argument("vtt", type=Path)
    script_parser.add_argument("--output", type=Path, required=True)
    script_parser.add_argument("--plain-output", type=Path)

    transcript_script_parser = subparsers.add_parser(
        "make-transcript-script", help="document-v7 transcriptとcutから台本を作成"
    )
    transcript_script_parser.add_argument("project", type=Path)
    transcript_script_parser.add_argument("--output", type=Path, required=True)
    transcript_script_parser.add_argument("--plain-output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint。"""
    args = build_parser().parse_args(argv)
    try:
        project = load_json(args.project)
        project_format = detect_format(project)
        if args.command == "inspect":
            print_inspection(inspect_project(project, project_format), args.json)
        elif args.command == "export-vtt":
            count = export_vtt(project, project_format, args.output)
            print(f"{count} cue(s) -> {args.output}")
        elif args.command == "import-vtt":
            cues = parse_vtt(args.vtt)
            result = import_vtt(project, project_format, cues)
            write_project(args.project, args.output, result, force=args.force)
            print(f"{len(cues)} cue(s) -> {args.output}")
        elif args.command == "export-transcript-tsv":
            count = export_transcript_tsv(project, project_format, args.output)
            print(f"{count} word(s) -> {args.output}")
        elif args.command == "import-transcript-tsv":
            result, changed = import_transcript_tsv(project, project_format, args.tsv)
            write_project(args.project, args.output, result, force=args.force)
            print(f"{changed} changed word(s) -> {args.output}")
        elif args.command == "apply-plan":
            plan = load_json(args.plan)
            result = apply_edit_plan(project, project_format, plan)
            write_project(args.project, args.output, result, force=args.force)
            print(f"edit plan -> {args.output}")
        elif args.command == "make-transcript-script":
            count = make_transcript_script(
                project,
                project_format,
                args.output,
                args.plain_output,
            )
            print(f"{count} line(s) -> {args.output}")
        elif args.command == "make-script":
            cues = parse_vtt(args.vtt)
            count = make_script(
                project,
                project_format,
                cues,
                args.output,
                args.plain_output,
            )
            print(f"{count} line(s) -> {args.output}")
        else:  # pragma: no cover
            raise AssertionError(args.command)
    except (OSError, ProjectError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
