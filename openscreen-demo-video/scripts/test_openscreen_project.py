"""openscreen_project.py の非破壊編集を検証する。"""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).with_name("openscreen_project.py")
SPEC = importlib.util.spec_from_file_location("openscreen_project", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def legacy_project() -> dict:
    """最小のlegacy-v2 fixtureを返す。"""
    return {
        "version": 2,
        "media": {"screenVideoPath": "/tmp/demo.mp4"},
        "editor": {
            "annotationRegions": [
                {
                    "id": "annotation-1",
                    "startMs": 1000,
                    "endMs": 2500,
                    "type": "text",
                    "content": "誤った字幕",
                    "annotationSource": "auto-caption",
                    "position": {"x": 4, "y": 86},
                    "size": {"width": 92, "height": 12},
                    "style": dict(MODULE.CAPTION_LAYOUT["style"]),
                    "zIndex": 1,
                }
            ],
            "zoomRegions": [],
            "trimRegions": [],
        },
    }


def document_project() -> dict:
    """最小のdocument-v7 fixtureを返す。"""
    transcript = {
        "assetId": "asset-1",
        "language": "ja",
        "segments": [
            {
                "id": "segment-1",
                "kind": "speech",
                "startSec": 1.0,
                "endSec": 2.0,
                "text": "OAuth連携",
                "wordIds": ["word-1", "word-2"],
            }
        ],
        "words": [
            {
                "id": "word-1",
                "segmentId": "segment-1",
                "startSec": 1.0,
                "endSec": 1.4,
                "text": "OAuth",
            },
            {
                "id": "word-2",
                "segmentId": "segment-1",
                "startSec": 1.4,
                "endSec": 2.0,
                "text": "連携",
            },
        ],
    }
    return {
        "schemaVersion": 7,
        "project": {
            "id": "project-1",
            "title": "Demo",
            "createdAt": "2026-09-05T00:00:00Z",
            "updatedAt": "2026-09-05T00:00:00Z",
            "primaryAssetId": "asset-1",
        },
        "assets": [
            {
                "id": "asset-1",
                "kind": "video",
                "label": "demo",
                "originalPath": "/tmp/demo.mp4",
                "cameraTrack": None,
            }
        ],
        "transcript": json.loads(json.dumps(transcript)),
        "transcripts": [transcript],
        "timeline": {
            "clips": [
                {
                    "id": "clip-1",
                    "assetId": "asset-1",
                    "sourceStartSec": 0,
                    "sourceEndSec": 10,
                    "timelineStartSec": 0,
                    "timelineEndSec": 10,
                    "wordRefs": [],
                    "origin": "user",
                    "reason": "",
                }
            ],
            "gaps": [],
            "trimRanges": [],
            "muteRanges": [],
            "speedRanges": [],
            "captionRanges": [],
        },
        "annotations": [],
        "zoomRanges": [],
        "audioTracks": [],
        "legacyEditor": {},
    }


class LegacyWorkflowTest(unittest.TestCase):
    """legacy-v2のVTTとedit planを検証する。"""

    def test_project_writer_refuses_to_overwrite_the_source(self) -> None:
        project = legacy_project()
        with tempfile.TemporaryDirectory() as directory:
            project_path = Path(directory) / "original.openscreen"
            original = json.dumps(project, ensure_ascii=False)
            project_path.write_text(original, encoding="utf-8")
            with self.assertRaisesRegex(MODULE.ProjectError, "上書きできません"):
                MODULE.write_project(
                    project_path,
                    project_path,
                    {**project, "extra": "changed"},
                    force=True,
                )
            self.assertEqual(project_path.read_text(encoding="utf-8"), original)

    def test_unknown_legacy_version_is_rejected(self) -> None:
        project = legacy_project()
        project["version"] = 3
        with self.assertRaisesRegex(MODULE.ProjectError, "未対応のlegacy version"):
            MODULE.detect_format(project)

    def test_duplicate_vtt_cue_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vtt_path = Path(directory) / "captions.vtt"
            vtt_path.write_text(
                "WEBVTT\n\nannotation-1\n00:00:01.000 --> 00:00:02.000\n一\n\n"
                "annotation-1\n00:00:02.000 --> 00:00:03.000\n二\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(MODULE.ProjectError, "cue IDが重複"):
                MODULE.parse_vtt(vtt_path)

    def test_vtt_round_trip_preserves_manual_regions(self) -> None:
        project = legacy_project()
        project["editor"]["annotationRegions"].append(
            {
                "id": "heading-oauth",
                "startMs": 0,
                "endMs": 5000,
                "type": "text",
                "content": "見出し",
                "position": {"x": 4, "y": 4},
                "size": {"width": 70, "height": 10},
                "style": dict(MODULE.TEXT_STYLE),
                "zIndex": 2,
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            vtt_path = Path(directory) / "captions.vtt"
            self.assertEqual(MODULE.export_vtt(project, MODULE.LEGACY_FORMAT, vtt_path), 1)
            vtt_path.write_text(
                vtt_path.read_text(encoding="utf-8").replace("誤った字幕", "修正した字幕"),
                encoding="utf-8",
            )
            result = MODULE.import_vtt(
                project,
                MODULE.LEGACY_FORMAT,
                MODULE.parse_vtt(vtt_path),
            )

        annotations = result["editor"]["annotationRegions"]
        self.assertEqual([item["id"] for item in annotations], ["heading-oauth", "annotation-1"])
        self.assertEqual(annotations[1]["content"], "修正した字幕")
        self.assertEqual(project["editor"]["annotationRegions"][0]["content"], "誤った字幕")

    def test_plan_adds_cut_zoom_and_two_text_presets(self) -> None:
        project = legacy_project()
        result = MODULE.apply_edit_plan(
            project,
            MODULE.LEGACY_FORMAT,
            {
                "trimRegions": [{"id": "trim-intro", "startMs": 0, "endMs": 600}],
                "zoomRegions": [
                    {
                        "id": "zoom-login",
                        "startMs": 1200,
                        "endMs": 3000,
                        "depth": 3,
                        "focus": {"cx": 0.7, "cy": 0.3},
                    }
                ],
                "textAnnotations": [
                    {
                        "id": "heading-oauth",
                        "startMs": 0,
                        "endMs": 5000,
                        "preset": "heading",
                        "text": "OAuth Remote MCP経由のChatGPT連携",
                    },
                    {
                        "id": "note-consent",
                        "startMs": 1400,
                        "endMs": 2800,
                        "preset": "note",
                        "text": "同意画面を確認",
                    },
                ],
            },
        )
        self.assertEqual(result["editor"]["trimRegions"][0]["endMs"], 600)
        self.assertEqual(result["editor"]["zoomRegions"][0]["focus"]["cx"], 0.7)
        manual = [
            item
            for item in result["editor"]["annotationRegions"]
            if item.get("annotationSource") != "auto-caption"
        ]
        self.assertEqual([item["position"]["y"] for item in manual], [4, 70])

    def test_depth_update_removes_an_old_custom_scale(self) -> None:
        project = legacy_project()
        project["editor"]["zoomRegions"] = [
            {
                "id": "zoom-1",
                "startMs": 1000,
                "endMs": 2000,
                "depth": 5,
                "customScale": 4.2,
                "focus": {"cx": 0.5, "cy": 0.5},
            }
        ]
        result = MODULE.apply_edit_plan(
            project,
            MODULE.LEGACY_FORMAT,
            {"zoomRegions": [{"id": "zoom-1", "depth": 2}]},
        )
        self.assertNotIn("customScale", result["editor"]["zoomRegions"][0])


class DocumentWorkflowTest(unittest.TestCase):
    """document-v7のword修正とclip anchorを検証する。"""

    def test_transcript_tsv_updates_provenance_segment_and_mirror(self) -> None:
        project = document_project()
        with tempfile.TemporaryDirectory() as directory:
            tsv_path = Path(directory) / "transcript.tsv"
            MODULE.export_transcript_tsv(project, MODULE.DOCUMENT_FORMAT, tsv_path)
            with tsv_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            rows[0]["corrected_text"] = "オーオース"
            with tsv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=MODULE.TSV_FIELDS, delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)
            result, changed = MODULE.import_transcript_tsv(
                project,
                MODULE.DOCUMENT_FORMAT,
                tsv_path,
            )

        self.assertEqual(changed, 1)
        word = result["transcripts"][0]["words"][0]
        self.assertEqual(word["originalText"], "OAuth")
        self.assertEqual(word["source"], "user")
        self.assertEqual(result["transcripts"][0]["segments"][0]["text"], "オーオース連携")
        self.assertEqual(result["transcript"], result["transcripts"][0])
        self.assertNotIn("originalText", project["transcripts"][0]["words"][0])

    def test_transcript_tsv_rejects_a_stale_project(self) -> None:
        project = document_project()
        with tempfile.TemporaryDirectory() as directory:
            tsv_path = Path(directory) / "transcript.tsv"
            MODULE.export_transcript_tsv(project, MODULE.DOCUMENT_FORMAT, tsv_path)
            project["transcripts"][0]["words"][0]["text"] = "GUIで変更済み"
            with self.assertRaisesRegex(MODULE.ProjectError, "expected_text"):
                MODULE.import_transcript_tsv(
                    project,
                    MODULE.DOCUMENT_FORMAT,
                    tsv_path,
                )

    def test_plan_anchors_regions_to_single_clip(self) -> None:
        result = MODULE.apply_edit_plan(
            document_project(),
            MODULE.DOCUMENT_FORMAT,
            {
                "trimRegions": [{"id": "trim-1", "startMs": 100, "endMs": 500}],
                "zoomRegions": [{"id": "zoom-1", "startMs": 1000, "endMs": 2000, "depth": 2}],
                "textAnnotations": [
                    {
                        "id": "heading-1",
                        "startMs": 0,
                        "endMs": 3000,
                        "text": "見出し",
                    }
                ],
            },
        )
        trim = result["timeline"]["trimRanges"][0]
        self.assertEqual((trim["assetId"], trim["clipId"]), ("asset-1", "clip-1"))
        self.assertEqual((trim["startSec"], trim["endSec"]), (0.1, 0.5))
        self.assertEqual(result["zoomRanges"][0]["sourceStartSec"], 1.0)
        self.assertEqual(result["annotations"][0]["clipId"], "clip-1")

    def test_cross_clip_edit_is_rejected(self) -> None:
        project = document_project()
        project["timeline"]["clips"][0]["timelineEndSec"] = 2
        project["timeline"]["clips"].append(
            {
                **project["timeline"]["clips"][0],
                "id": "clip-2",
                "sourceStartSec": 2,
                "sourceEndSec": 4,
                "timelineStartSec": 2,
                "timelineEndSec": 4,
            }
        )
        with self.assertRaisesRegex(MODULE.ProjectError, "単一clip"):
            MODULE.apply_edit_plan(
                project,
                MODULE.DOCUMENT_FORMAT,
                {"zoomRegions": [{"id": "zoom-cross", "startMs": 1500, "endMs": 2500}]},
            )

    def test_transcript_script_maps_trimmed_and_source_time(self) -> None:
        project = MODULE.apply_edit_plan(
            document_project(),
            MODULE.DOCUMENT_FORMAT,
            {"trimRegions": [{"id": "trim-intro", "startMs": 0, "endMs": 500}]},
        )
        with tempfile.TemporaryDirectory() as directory:
            markdown = Path(directory) / "narration.md"
            plain = Path(directory) / "narration.txt"
            count = MODULE.make_transcript_script(
                project,
                MODULE.DOCUMENT_FORMAT,
                markdown,
                plain,
            )
            body = markdown.read_text(encoding="utf-8")
            spoken = plain.read_text(encoding="utf-8")

        self.assertEqual(count, 1)
        self.assertIn("00:00:01.000–00:00:02.000", body)
        self.assertIn("00:00:00.500–00:00:01.500", body)
        self.assertIn("OAuth連携", spoken)
        self.assertNotIn("partial trim", body)

    def test_transcript_script_repeats_a_segment_for_a_duplicated_clip(self) -> None:
        project = document_project()
        duplicate = {
            **project["timeline"]["clips"][0],
            "id": "clip-2",
            "timelineStartSec": 10,
            "timelineEndSec": 20,
        }
        project["timeline"]["clips"].append(duplicate)

        cues = MODULE.document_transcript_cues(project, MODULE.DOCUMENT_FORMAT)

        self.assertEqual([cue["startMs"] for cue in cues], [1000, 11000])
        self.assertEqual([cue["text"] for cue in cues], ["OAuth連携", "OAuth連携"])

    def test_transcript_script_rejects_a_segment_crossing_a_clip_boundary(self) -> None:
        project = document_project()
        project["timeline"]["clips"][0]["sourceEndSec"] = 1.5
        project["timeline"]["clips"][0]["timelineEndSec"] = 1.5

        with self.assertRaisesRegex(MODULE.ProjectError, "source境界"):
            MODULE.document_transcript_cues(project, MODULE.DOCUMENT_FORMAT)

    def test_segment_join_compacts_cjk_after_closing_punctuation(self) -> None:
        self.assertEqual(MODULE.join_segment_text(["これは。", "テスト"]), "これは。テスト")


if __name__ == "__main__":
    unittest.main()
