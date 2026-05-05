from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.video_qc.decision_semantics import QC_DECISION_SEMANTICS_VERSION
from app.creative.agents.video_qc.models import VideoQcInput
from app.creative.agents.video_qc.service import VideoQcAgentService


class _StaticProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": 1080, "height": 1920, "has_audio": True, "probe_mode": "ffprobe"}


class _UnavailableProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": None, "height": None, "has_audio": False, "probe_mode": "unavailable"}


class VideoQcDecisionSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.video_path = self.root / "video.mp4"
        self.audio_path = self.root / "audio.wav"
        self.metadata_path = self.root / "metadata.json"
        self.video_path.write_bytes(b"video-bytes")
        self.audio_path.write_bytes(b"audio-bytes")
        self.metadata_path.write_text(json.dumps(self._metadata()), encoding="utf-8")

    def _metadata(self) -> dict[str, object]:
        return {
            "aspect_ratio": "9:16",
            "render_duration_s": 8.0,
            "setup_background_mean_luma": 90.0,
            "payoff_background_mean_luma": 105.0,
            "subtitle_cues": [
                {"start": 0.0, "end": 2.0, "text": "The camera catches a shadow"},
                {"start": 2.2, "end": 4.8, "text": "Then the room goes quiet"},
                {"start": 6.0, "end": 7.8, "text": "Now the door opens twice"},
            ],
        }

    def _write_metadata(self, metadata: dict[str, object]) -> None:
        self.metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    def _qc_input(self, **overrides: object) -> VideoQcInput:
        payload = {
            "render_job_id": "qc_semantics",
            "video_path": str(self.video_path),
            "audio_path": str(self.audio_path),
            "metadata_path": str(self.metadata_path),
            "script_text": "The camera catches a shadow before the room goes quiet and the door opens twice.",
            "tts_trace": {"segment_durations": [2.0, 2.6, 1.8]},
            "visual_trace": {"asset_trace": {"selected": True}},
            "edit_trace": {"editor_version": "test"},
        }
        payload.update(overrides)
        return VideoQcInput(**payload)

    def _reason(self, semantics: dict[str, object], reason_code: str) -> dict[str, object]:
        for item in semantics["reason_semantics"]:
            if item["reason_code"] == reason_code:
                return item
        raise AssertionError(f"missing reason semantics: {reason_code}")

    def test_approve_semantics_are_clean_and_publishable(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        semantics = qc.decision_semantics

        self.assertEqual(qc.status, "APPROVE")
        self.assertEqual(semantics["semantics_version"], QC_DECISION_SEMANTICS_VERSION)
        self.assertEqual(semantics["status"], "APPROVE")
        self.assertEqual(semantics["severity_level"], "none")
        self.assertEqual(semantics["decision_rule_applied"], "APPROVE_NO_FAILURES_AND_PUBLISHABLE_SIGNAL")
        self.assertEqual(semantics["blockers"], [])
        self.assertEqual(semantics["warnings"], [])
        self.assertTrue(semantics["publishability_rationale"]["publishable"])
        self.assertTrue(semantics["decision_consistency"])

    def test_hold_semantics_use_warnings_not_blockers(self) -> None:
        metadata = self._metadata()
        metadata["subtitle_cues"][0]["start"] = 0.6
        metadata["subtitle_cues"][0]["end"] = 1.6
        metadata["subtitle_cues"][0]["text"] = "LOOK BACK"
        metadata["subtitle_cues"][-1]["start"] = 6.7
        metadata["subtitle_cues"][-1]["end"] = 7.7
        metadata["subtitle_cues"][-1]["text"] = "TURN NOW"
        self._write_metadata(metadata)

        qc = _StaticProbeVideoQcAgentService().evaluate(
            qc_input=self._qc_input(script_text="Look back now. Turn away before the final door opens.")
        )
        semantics = qc.decision_semantics

        self.assertEqual(qc.status, "HOLD")
        self.assertFalse(qc.publishable)
        self.assertEqual(semantics["decision_rule_applied"], "HOLD_SOFT_FAILURES_WITHOUT_BLOCKERS")
        self.assertEqual(semantics["blockers"], [])
        self.assertIn("QC_HOOK_QUALITY_BORDERLINE", semantics["warnings"])
        self.assertEqual(self._reason(semantics, "QC_HOOK_QUALITY_BORDERLINE")["disposition"], "warning")
        self.assertEqual(semantics["severity_level"], "medium")

    def test_missing_metadata_reject_is_critical_technical_blocker(self) -> None:
        self.metadata_path.unlink()

        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        semantics = qc.decision_semantics

        self.assertEqual(qc.status, "REJECT")
        self.assertIn("QC_METADATA_MISSING", semantics["blockers"])
        self.assertEqual(self._reason(semantics, "QC_METADATA_MISSING")["category"], "technical")
        self.assertEqual(self._reason(semantics, "QC_METADATA_MISSING")["severity"], "critical")
        self.assertEqual(semantics["decision_rule_applied"], "REJECT_HARD_FAILURE_BLOCKER")
        self.assertFalse(semantics["publishability_rationale"]["publishable"])

    def test_product_veto_reject_is_product_blocker(self) -> None:
        metadata = self._metadata()
        metadata["subtitle_cues"][0]["start"] = 1.0
        metadata["subtitle_cues"][0]["end"] = 1.1
        metadata["subtitle_cues"][0]["text"] = "RUN"
        self._write_metadata(metadata)

        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        semantics = qc.decision_semantics

        self.assertEqual(qc.status, "REJECT")
        self.assertIn("QC_HOOK_QUALITY_FAIL", semantics["blockers"])
        self.assertEqual(self._reason(semantics, "QC_HOOK_QUALITY_FAIL")["category"], "product")
        self.assertEqual(self._reason(semantics, "QC_HOOK_QUALITY_FAIL")["decision_impact"], "reject_path")
        self.assertEqual(semantics["decision_rule_applied"], "REJECT_PRODUCT_VETO_BLOCKER")

    def test_perceptual_failure_is_distinguished_from_product_failure(self) -> None:
        metadata = self._metadata()
        metadata["payoff_background_mean_luma"] = 20.0
        self._write_metadata(metadata)

        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        semantics = qc.decision_semantics

        self.assertEqual(qc.status, "REJECT")
        self.assertEqual(self._reason(semantics, "QC_PAYOFF_TOO_DARK")["category"], "perceptual")
        self.assertEqual(self._reason(semantics, "QC_PAYOFF_TOO_DARK")["disposition"], "blocker")
        self.assertIn("payoff_background_mean_luma", self._reason(semantics, "QC_PAYOFF_TOO_DARK")["evidence_summary"])

    def test_monitorable_environment_and_missing_traces_do_not_become_blockers(self) -> None:
        qc = _UnavailableProbeVideoQcAgentService().evaluate(
            qc_input=self._qc_input(tts_trace={}, visual_trace={}, edit_trace={})
        )
        semantics = qc.decision_semantics

        self.assertEqual(qc.status, "APPROVE")
        self.assertIn("QC_METADATA_FALLBACK_PROBE_MONITORABLE", semantics["monitorable"])
        self.assertIn("QC_OPTIONAL_UPSTREAM_TRACE_MISSING_MONITORABLE", semantics["monitorable"])
        self.assertNotIn("QC_METADATA_FALLBACK_PROBE_MONITORABLE", semantics["blockers"])
        self.assertNotIn("QC_OPTIONAL_UPSTREAM_TRACE_MISSING_MONITORABLE", semantics["warnings"])
        self.assertEqual(self._reason(semantics, "QC_METADATA_FALLBACK_PROBE_MONITORABLE")["decision_impact"], "monitoring_only")

    def test_decision_semantics_are_in_details_and_decision_trace(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())

        self.assertEqual(qc.details["decision_semantics"], qc.decision_semantics)
        self.assertEqual(qc.decision.decision_trace["decision_semantics"], qc.decision_semantics)
        json.dumps(qc.to_dict())

    def test_decision_semantics_are_deterministic_for_same_input(self) -> None:
        service = _StaticProbeVideoQcAgentService()
        first = service.evaluate(qc_input=self._qc_input()).decision_semantics
        second = service.evaluate(qc_input=self._qc_input()).decision_semantics

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
