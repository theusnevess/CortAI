from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.models import TtsExecutionTrace
from app.creative.agents.voice.audio_validation_linkage import VoiceAudioValidationLinker
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.contracts.creative_pack import (
    ScriptPlan,
    VoiceDeliveryProfile,
    VoicePlan,
    VoiceRuntimeConstraints,
    VoiceSegmentPlan,
)


def _script() -> ScriptPlan:
    return ScriptPlan(
        hook="The doorbell rings from inside the basement",
        setup="The camera feed freezes at the exact same frame",
        payoff="The timestamp shows it happened before the house was built",
        generation_mode="test_structured",
    )


def _voice_plan() -> VoicePlan:
    return VoicePlan(
        provider="kokoro",
        voice_id="af_heart",
        style="dark_calm",
        delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
        segments={
            "hook": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
        },
        runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
    )


class VoiceAudioValidationLinkageTests(unittest.TestCase):
    def test_service_marks_audio_trace_absent_explicitly(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        linkage = result.audio_validation_linkage

        self.assertEqual(linkage["linkage_version"], "voice_audio_validation_linkage_v2_6")
        self.assertFalse(linkage["audio_trace_available"])
        self.assertFalse(linkage["provider_execution_verified"])
        self.assertFalse(linkage["duration_available"])
        self.assertFalse(linkage["segment_durations_available"])
        self.assertEqual(linkage["validation_status"], "missing_trace")
        self.assertIn("tts_trace", linkage["missing_evidence"])

    def test_no_audio_file_is_inspected_without_artifact(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        linkage = result.audio_validation_linkage

        self.assertIsNone(linkage["audio_artifact_path"])
        self.assertEqual(linkage["audio_artifact_status"], "not_provided")
        self.assertIn("AUDIO_ARTIFACT_PATH_MISSING", linkage["reason_codes"])

    def test_complete_tts_trace_links_provider_and_durations(self) -> None:
        trace = TtsExecutionTrace(
            provider_requested="kokoro",
            provider_executed="kokoro",
            voice_id_requested="af_heart",
            voice_id_executed="af_heart",
            style_requested="dark_calm",
            fallback_used=False,
            fallback_reason="",
            latency_s=0.25,
            audio_duration_s=8.4,
            segment_durations=[2.1, 3.2, 3.1],
        )

        linkage = VoiceAudioValidationLinker().link(
            voice_plan=_voice_plan(),
            tts_trace=trace,
            audio_artifact={"audio_path": "OUT/audio/test.wav"},
        ).to_dict()

        self.assertTrue(linkage["audio_trace_available"])
        self.assertTrue(linkage["provider_execution_verified"])
        self.assertTrue(linkage["duration_available"])
        self.assertTrue(linkage["segment_durations_available"])
        self.assertEqual(linkage["provider_executed"], "kokoro")
        self.assertEqual(linkage["audio_duration_s"], 8.4)
        self.assertEqual(linkage["segment_durations"], [2.1, 3.2, 3.1])
        self.assertEqual(linkage["audio_artifact_status"], "provided_not_inspected")
        self.assertEqual(linkage["validation_status"], "linked")

    def test_partial_tts_trace_does_not_fake_duration(self) -> None:
        trace = {
            "provider_requested": "kokoro",
            "provider_executed": "kokoro",
            "voice_id_requested": "af_heart",
            "voice_id_executed": "af_heart",
            "fallback_used": False,
        }

        linkage = VoiceAudioValidationLinker().link(voice_plan=_voice_plan(), tts_trace=trace).to_dict()

        self.assertTrue(linkage["audio_trace_available"])
        self.assertTrue(linkage["provider_execution_verified"])
        self.assertFalse(linkage["duration_available"])
        self.assertFalse(linkage["segment_durations_available"])
        self.assertIsNone(linkage["audio_duration_s"])
        self.assertEqual(linkage["segment_durations"], [])
        self.assertEqual(linkage["validation_status"], "partial")
        self.assertIn("audio_duration_s", linkage["missing_evidence"])

    def test_provider_execution_not_verified_when_requested_provider_mismatches(self) -> None:
        trace = {
            "provider_requested": "piper",
            "provider_executed": "piper",
            "voice_id_requested": "af_heart",
            "voice_id_executed": "en_US-lessac-medium.onnx",
            "fallback_used": True,
            "audio_duration_s": 7.0,
            "segment_durations": [2.0, 2.0, 3.0],
        }

        linkage = VoiceAudioValidationLinker().link(voice_plan=_voice_plan(), tts_trace=trace).to_dict()

        self.assertTrue(linkage["audio_trace_available"])
        self.assertFalse(linkage["provider_execution_verified"])
        self.assertIn("provider_execution_verification", linkage["missing_evidence"])
        self.assertIn("PROVIDER_EXECUTION_NOT_VERIFIED", linkage["reason_codes"])

    def test_invalid_duration_values_are_not_fabricated(self) -> None:
        trace = {
            "provider_requested": "kokoro",
            "provider_executed": "kokoro",
            "voice_id_requested": "af_heart",
            "voice_id_executed": "af_heart",
            "audio_duration_s": 0,
            "segment_durations": [2.0, "bad", 3.0],
        }

        linkage = VoiceAudioValidationLinker().link(voice_plan=_voice_plan(), tts_trace=trace).to_dict()

        self.assertFalse(linkage["duration_available"])
        self.assertFalse(linkage["segment_durations_available"])
        self.assertIsNone(linkage["audio_duration_s"])
        self.assertEqual(linkage["segment_durations"], [])

    def test_boundary_statement_excludes_synthesis_and_file_reading(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        linkage = result.audio_validation_linkage
        encoded = json.dumps(linkage, sort_keys=True)

        self.assertEqual(
            linkage["boundary_statement"],
            "Voice links audio validation evidence only when supplied; it does not synthesize or inspect audio files.",
        )
        self.assertNotIn("file_read", encoded)
        self.assertNotIn("synthesized", encoded)

    def test_result_payload_remains_backward_compatible_and_serializable(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="facts", script_plan=_script())

        payload = result.to_dict()
        encoded = json.dumps(payload, sort_keys=True)

        self.assertIn("voice_plan", payload)
        self.assertIn("fallback", payload)
        self.assertIn("voice_plan_governance", payload)
        self.assertIn("delivery_semantics", payload)
        self.assertIn("segment_timing", payload)
        self.assertIn("monotony_contrast_analysis", payload)
        self.assertIn("provider_fallback_honesty", payload)
        self.assertIn("audio_validation_linkage", payload)
        self.assertIn("voice_audio_validation_linkage_v2_6", encoded)

    def test_audio_validation_linkage_is_deterministic(self) -> None:
        service = VoiceAgentService()

        first = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).audio_validation_linkage
        second = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).audio_validation_linkage

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
