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

from app.creative.agents.video_qc.input_governance import QC_INPUT_GOVERNANCE_VERSION
from app.creative.agents.video_qc.models import VideoQcInput
from app.creative.agents.video_qc.service import VideoQcAgentService


class _StaticProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": 1080, "height": 1920, "has_audio": True, "probe_mode": "ffprobe"}


class _UnavailableProbeVideoQcAgentService(VideoQcAgentService):
    def _probe_video(self, video_path: Path) -> dict[str, object]:
        return {"width": None, "height": None, "has_audio": False, "probe_mode": "unavailable"}


class VideoQcInputGovernanceTests(unittest.TestCase):
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

    def _qc_input(self, **overrides: object) -> VideoQcInput:
        payload = {
            "render_job_id": "qc_input_gov",
            "video_path": str(self.video_path),
            "audio_path": str(self.audio_path),
            "metadata_path": str(self.metadata_path),
            "script_text": "The camera catches a shadow before the room goes quiet and the door opens twice.",
            "tts_trace": {"segment_durations": [2.0, 2.6, 1.8]},
            "visual_trace": {},
            "edit_trace": {"editor_version": "test"},
        }
        payload.update(overrides)
        return VideoQcInput(**payload)

    def _signal(self, governance: dict[str, object], input_key: str) -> dict[str, object]:
        for signal in governance["input_signals"]:
            if signal["input_key"] == input_key:
                return signal
        raise AssertionError(f"missing governance signal: {input_key}")

    def test_clean_qc_exposes_input_governance_without_changing_decision(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())

        self.assertEqual(qc.status, "APPROVE")
        self.assertTrue(qc.publishable)
        self.assertEqual(qc.qc_input_governance["governance_version"], QC_INPUT_GOVERNANCE_VERSION)
        self.assertEqual(qc.details["qc_input_governance"], qc.qc_input_governance)
        self.assertEqual(qc.decision.decision_trace["qc_input_governance"], qc.qc_input_governance)
        json.dumps(qc.to_dict())

    def test_clean_governance_marks_required_artifacts_available_and_used(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        governance = qc.qc_input_governance

        self.assertTrue(governance["policy_respected"])
        for input_key in ["render_job_id", "video_artifact", "audio_artifact", "metadata_artifact"]:
            self.assertIn(input_key, governance["available_inputs"])
            self.assertIn(input_key, governance["used_inputs"])
            self.assertEqual(self._signal(governance, input_key)["status"], "available")
        self.assertIn("visual_trace", governance["missing_inputs"])

    def test_missing_metadata_remains_reject_and_is_governance_missing(self) -> None:
        self.metadata_path.unlink()

        qc = _StaticProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        governance = qc.qc_input_governance

        self.assertEqual(qc.status, "REJECT")
        self.assertFalse(qc.publishable)
        self.assertIn("QC_METADATA_MISSING", qc.reasons)
        self.assertFalse(governance["policy_respected"])
        self.assertIn("metadata_artifact", governance["missing_inputs"])
        self.assertEqual(self._signal(governance, "metadata_artifact")["status"], "missing")

    def test_optional_script_and_trace_absence_is_explicit_not_fabricated(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(
            qc_input=self._qc_input(script_text="", tts_trace={}, visual_trace={}, edit_trace={})
        )
        governance = qc.qc_input_governance

        self.assertIn("script_text", governance["missing_inputs"])
        self.assertIn("tts_trace", governance["missing_inputs"])
        self.assertIn("visual_trace", governance["missing_inputs"])
        self.assertIn("edit_trace", governance["missing_inputs"])
        self.assertFalse(self._signal(governance, "tts_trace")["available"])
        self.assertFalse(self._signal(governance, "edit_trace")["available"])

    def test_metadata_fallback_probe_is_visible(self) -> None:
        qc = _UnavailableProbeVideoQcAgentService().evaluate(qc_input=self._qc_input())
        governance = qc.qc_input_governance

        self.assertEqual(qc.status, "APPROVE")
        self.assertEqual(qc.details["probe_mode"], "metadata_fallback")
        self.assertTrue(governance["environment_summary"]["metadata_fallback_used"])
        self.assertIn("metadata_fallback_probe", governance["used_inputs"])
        self.assertIn("metadata_fallback_probe", governance["environment_dependent_inputs"])
        self.assertEqual(self._signal(governance, "media_probe_capability")["status"], "environment_dependent")

    def test_visual_trace_present_is_visible_but_ignored_by_current_qc(self) -> None:
        qc = _StaticProbeVideoQcAgentService().evaluate(
            qc_input=self._qc_input(visual_trace={"asset_trace": {"alignment": "available"}})
        )
        signal = self._signal(qc.qc_input_governance, "visual_trace")

        self.assertTrue(signal["available"])
        self.assertFalse(signal["used"])
        self.assertEqual(signal["status"], "ignored")
        self.assertIn("visual_trace", qc.qc_input_governance["ignored_inputs"])

    def test_input_governance_is_deterministic_for_same_input(self) -> None:
        service = _StaticProbeVideoQcAgentService()
        first = service.evaluate(qc_input=self._qc_input()).qc_input_governance
        second = service.evaluate(qc_input=self._qc_input()).qc_input_governance

        self.assertEqual(first, second)

    def test_exception_path_still_returns_controlled_reject_with_governance(self) -> None:
        class _BrokenVideoQcAgentService(VideoQcAgentService):
            def _build_input(self, *, render_job_id: str, artifacts: object | None, base_dir: Path) -> VideoQcInput:
                raise RuntimeError("controlled failure")

        qc = _BrokenVideoQcAgentService().evaluate(render_job_id="qc_exception", artifacts={}, base_dir=self.root)

        self.assertEqual(qc.status, "REJECT")
        self.assertFalse(qc.publishable)
        self.assertIn("QC_INTERNAL_ERROR", qc.reasons)
        self.assertEqual(qc.qc_input_governance["governance_version"], QC_INPUT_GOVERNANCE_VERSION)
        self.assertIn("qc_input_governance", qc.decision.decision_trace)


if __name__ == "__main__":
    unittest.main()
