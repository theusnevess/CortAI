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

from app.creative.agents.video_qc.models import VideoQcInput
from app.creative.agents.video_qc.service import VideoQcAgentService
from app.creative.agents.video_qc.trace_auditability import QC_TRACE_VERSION, REQUIRED_QC_TRACE_SECTIONS, VideoQcTraceBuilder


class _StaticProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": 1080, "height": 1920, "has_audio": True, "probe_mode": "ffprobe"}


class _UnavailableProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": None, "height": None, "has_audio": False, "probe_mode": "unavailable"}


class VideoQcTraceAuditabilityTests(unittest.TestCase):
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
            "render_job_id": "qc_trace",
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

    def test_approve_qc_trace_is_present_and_reconstructible(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        trace = qc.qc_trace

        self.assertEqual(qc.status, "APPROVE")
        self.assertEqual(trace["trace_version"], QC_TRACE_VERSION)
        for section in REQUIRED_QC_TRACE_SECTIONS:
            self.assertIn(section, trace)
        self.assertTrue(trace["audit_summary"]["reconstructible"])
        self.assertEqual(trace["final_qc_decision_rationale"]["decision"], "APPROVE")
        self.assertEqual(trace["final_qc_decision_rationale"]["dominant_failure_type"], "none")
        self.assertEqual(qc.details["qc_trace"], trace)
        self.assertEqual(qc.decision.decision_trace["qc_trace"], trace)
        json.dumps(qc.to_dict())

    def test_hold_qc_trace_explains_warnings(self) -> None:
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
        trace = qc.qc_trace

        self.assertEqual(qc.status, "HOLD")
        self.assertFalse(qc.publishable)
        self.assertTrue(trace["audit_summary"]["reconstructible"])
        self.assertGreater(trace["final_qc_decision_rationale"]["warning_count"], 0)
        self.assertEqual(trace["decision_semantics"]["severity_level"], "medium")
        self.assertIn("QC_HOOK_QUALITY_BORDERLINE", trace["decision_semantics"]["warnings"])

    def test_reject_qc_trace_explains_blockers(self) -> None:
        self.metadata_path.unlink()

        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        trace = qc.qc_trace

        self.assertEqual(qc.status, "REJECT")
        self.assertFalse(qc.publishable)
        self.assertTrue(trace["audit_summary"]["reconstructible"])
        self.assertEqual(trace["final_qc_decision_rationale"]["dominant_failure_type"], "technical")
        self.assertGreater(trace["final_qc_decision_rationale"]["blocker_count"], 0)
        self.assertIn("QC_METADATA_MISSING", trace["decision_semantics"]["blockers"])

    def test_missing_inputs_are_visible_in_qc_trace(self) -> None:
        self.metadata_path.unlink()

        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        missing = qc.qc_trace["missing_or_degraded_inputs"]

        self.assertIn("metadata_artifact", missing["missing_inputs"])
        self.assertIn("QC_MISSING_INPUTS_VISIBLE", missing["limitations_detected"])
        self.assertEqual(missing["probe_mode"], "unavailable")

    def test_degraded_inputs_are_visible_in_qc_trace(self) -> None:
        self.audio_path.write_bytes(b"")

        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        missing = qc.qc_trace["missing_or_degraded_inputs"]

        self.assertEqual(qc.status, "REJECT")
        self.assertIn("audio_artifact", missing["degraded_inputs"])
        self.assertIn("metadata_artifact", missing["degraded_inputs"])
        self.assertIn("QC_DEGRADED_INPUTS_VISIBLE", missing["limitations_detected"])

    def test_metadata_fallback_is_visible_in_qc_trace(self) -> None:
        qc = _UnavailableProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        missing = qc.qc_trace["missing_or_degraded_inputs"]

        self.assertEqual(qc.status, "APPROVE")
        self.assertTrue(missing["metadata_fallback_used"])
        self.assertEqual(missing["probe_mode"], "metadata_fallback")
        self.assertIn("QC_METADATA_FALLBACK_USED", missing["limitations_detected"])
        self.assertIn("QC_METADATA_FALLBACK_PROBE_USED", qc.qc_trace["evidence_summary"]["environment_limitations"])

    def test_confidence_and_decision_consistency_are_visible(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        trace = qc.qc_trace

        self.assertEqual(trace["final_qc_decision_rationale"]["confidence"], qc.confidence)
        self.assertEqual(trace["final_qc_decision_rationale"]["confidence_level"], qc.confidence_level)
        self.assertTrue(trace["audit_summary"]["decision_trace_consistent"])
        self.assertTrue(trace["audit_summary"]["confidence_consistent"])
        self.assertTrue(trace["audit_summary"]["input_coverage_complete"])

    def test_builder_marks_trace_not_reconstructible_when_required_sections_missing(self) -> None:
        trace = VideoQcTraceBuilder().build(
            status="APPROVE",
            publishable=True,
            reasons=[],
            qc_input_governance={},
            qc_evidence_scoring={},
            confidence_calibration={},
            decision_semantics={},
            details={},
        )

        self.assertFalse(trace["audit_summary"]["reconstructible"])
        self.assertFalse(trace["audit_summary"]["required_sections_present"])
        self.assertIn("QC_TRACE_REQUIRED_SECTION_MISSING:input_governance", trace["audit_summary"]["silent_failure_indicators"])
        self.assertIn("QC_TRACE_CONFIDENCE_INCONSISTENT", trace["audit_summary"]["silent_failure_indicators"])

    def test_qc_trace_is_deterministic_for_same_input(self) -> None:
        service = _StaticProbeVideoQcAgentService()
        first = service.evaluate(qc_input=self._qc_input()).qc_trace
        second = service.evaluate(qc_input=self._qc_input()).qc_trace

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
