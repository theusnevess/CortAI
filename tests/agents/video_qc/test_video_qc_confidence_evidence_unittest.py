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

from app.creative.agents.video_qc.confidence_evidence import QC_EVIDENCE_SCORING_VERSION
from app.creative.agents.video_qc.models import VideoQcInput
from app.creative.agents.video_qc.service import VideoQcAgentService


class _StaticProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": 1080, "height": 1920, "has_audio": True, "probe_mode": "ffprobe"}


class _BadResolutionProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": 1280, "height": 720, "has_audio": True, "probe_mode": "ffprobe"}


class _UnavailableProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": None, "height": None, "has_audio": False, "probe_mode": "unavailable"}


class VideoQcConfidenceEvidenceTests(unittest.TestCase):
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
            "render_job_id": "qc_confidence",
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

    def test_high_confidence_approve_with_complete_evidence(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())

        self.assertEqual(qc.status, "APPROVE")
        self.assertEqual(qc.confidence_level, "high")
        self.assertGreaterEqual(qc.confidence, 0.75)
        self.assertEqual(qc.confidence_rationale["confidence_meaning"], "trust_in_qc_decision")
        self.assertEqual(qc.qc_evidence_scoring["scoring_version"], QC_EVIDENCE_SCORING_VERSION)
        self.assertEqual(qc.qc_evidence_scoring["decision_rule_applied"], "clean_approve")
        self.assertIn("confidence_calibration", qc.decision.decision_trace)
        self.assertIn("qc_evidence_scoring", qc.details)

    def test_clear_bad_resolution_reject_has_technical_evidence(self) -> None:
        qc = _BadResolutionProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())

        self.assertEqual(qc.status, "REJECT")
        self.assertFalse(qc.publishable)
        self.assertIn("QC_RESOLUTION_INVALID", qc.reasons)
        self.assertIn("QC_RESOLUTION_INVALID", qc.qc_evidence_scoring["failure_categories"]["technical_failures"])
        self.assertGreaterEqual(qc.confidence_components["media_probe_quality"], 1.0)
        self.assertEqual(qc.qc_evidence_scoring["decision_rule_applied"], "hard_failure_reject")

    def test_hold_decision_is_not_high_confidence(self) -> None:
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

        self.assertEqual(qc.status, "HOLD")
        self.assertLess(qc.confidence, 0.75)
        self.assertEqual(qc.confidence_level, "medium")
        self.assertIn("QC_HOLD_IS_BORDERLINE_DECISION", [item["reason_code"] for item in qc.confidence_rationale["penalties"]])
        self.assertEqual(qc.qc_evidence_scoring["decision_rule_applied"], "soft_failure_hold")

    def test_missing_metadata_lowers_confidence_and_stays_reject(self) -> None:
        self.metadata_path.unlink()

        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())

        self.assertEqual(qc.status, "REJECT")
        self.assertIn("QC_METADATA_MISSING", qc.reasons)
        self.assertLess(qc.confidence, 0.75)
        self.assertIn("QC_METADATA_MISSING", qc.qc_evidence_scoring["failure_categories"]["technical_failures"])
        self.assertIn("QC_REQUIRED_ARTIFACT_EVIDENCE_MISSING", [item["reason_code"] for item in qc.confidence_rationale["penalties"]])

    def test_metadata_fallback_reduces_confidence_and_is_visible(self) -> None:
        qc = _UnavailableProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())

        self.assertEqual(qc.status, "APPROVE")
        self.assertEqual(qc.details["probe_mode"], "metadata_fallback")
        self.assertLess(qc.confidence, 0.75)
        self.assertEqual(qc.confidence_level, "medium")
        self.assertIn("QC_METADATA_FALLBACK_LIMITS_MEDIA_EVIDENCE", [item["reason_code"] for item in qc.confidence_rationale["penalties"]])
        self.assertIn("QC_METADATA_FALLBACK_PROBE_USED", qc.qc_evidence_scoring["failure_categories"]["environment_limitations"])

    def test_missing_traces_reduce_confidence_without_changing_decision(self) -> None:
        service = _StaticProbeVideoQcAgentService()
        complete = service.evaluate(qc_input=self._qc_input())
        missing_traces = service.evaluate(qc_input=self._qc_input(tts_trace={}, visual_trace={}, edit_trace={}))

        self.assertEqual(complete.status, missing_traces.status)
        self.assertLess(missing_traces.confidence, complete.confidence)
        self.assertIn("QC_OPTIONAL_UPSTREAM_TRACE_MISSING", [item["reason_code"] for item in missing_traces.confidence_rationale["penalties"]])

    def test_perceptual_and_product_failures_are_distinguished(self) -> None:
        dark_metadata = self._metadata()
        dark_metadata["payoff_background_mean_luma"] = 20.0
        self._write_metadata(dark_metadata)
        dark_qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        self.assertIn("QC_PAYOFF_TOO_DARK", dark_qc.qc_evidence_scoring["failure_categories"]["perceptual_failures"])

        product_metadata = self._metadata()
        product_metadata["subtitle_cues"][0]["start"] = 1.0
        product_metadata["subtitle_cues"][0]["end"] = 1.1
        product_metadata["subtitle_cues"][0]["text"] = "RUN"
        self._write_metadata(product_metadata)
        product_qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        self.assertIn("QC_HOOK_QUALITY_FAIL", product_qc.qc_evidence_scoring["failure_categories"]["product_failures"])
        self.assertEqual(product_qc.qc_evidence_scoring["decision_rule_applied"], "product_veto_reject")

    def test_score_evidence_covers_existing_score_summary(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        score_evidence = qc.qc_evidence_scoring["score_evidence"]

        for score_key in qc.decision.score_summary:
            self.assertIn(score_key, score_evidence)
            self.assertIn("score", score_evidence[score_key])
            self.assertIn("rationale", score_evidence[score_key])

    def test_confidence_evidence_is_deterministic_for_same_input(self) -> None:
        service = _StaticProbeVideoQcAgentService()
        first = service.evaluate(qc_input=self._qc_input())
        second = service.evaluate(qc_input=self._qc_input())

        self.assertEqual(first.qc_evidence_scoring, second.qc_evidence_scoring)
        self.assertEqual(first.confidence, second.confidence)
        self.assertEqual(first.confidence_components, second.confidence_components)
        self.assertEqual(first.confidence_rationale, second.confidence_rationale)

    def test_result_remains_backward_compatible_and_serializable(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        payload = qc.to_dict()

        self.assertIn("decision", payload)
        self.assertIn("status", payload)
        self.assertIn("reasons", payload)
        self.assertIn("publishable", payload)
        self.assertIn("details", payload)
        self.assertIn("confidence", payload)
        json.dumps(payload)


if __name__ == "__main__":
    unittest.main()
