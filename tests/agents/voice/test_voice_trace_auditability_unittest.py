from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.voice.service import VoiceAgentService
from app.creative.agents.voice.trace_auditability import REQUIRED_VOICE_TRACE_SECTIONS, VoiceTraceBuilder
from app.creative.contracts.creative_pack import ScriptPlan


def _script() -> ScriptPlan:
    return ScriptPlan(
        hook="The elevator opens on a floor that was removed",
        setup="The security feed labels the empty hallway as occupied",
        payoff="The missing floor appears only in the audio transcript",
        generation_mode="test_structured",
    )


class VoiceTraceAuditabilityTests(unittest.TestCase):
    def test_voice_trace_exists_in_result(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        self.assertIn("trace_version", result.voice_trace)
        self.assertEqual(result.voice_trace["trace_version"], "voice_trace_v2_6")

    def test_all_required_sections_are_present(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        for section in REQUIRED_VOICE_TRACE_SECTIONS:
            self.assertIn(section, result.voice_trace)
        self.assertTrue(result.voice_trace["audit_summary"]["required_sections_present"])

    def test_final_voice_plan_rationale_reconstructs_voice_plan(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="true_crime", script_plan=_script())

        rationale = result.voice_trace["final_voice_plan_rationale"]

        self.assertTrue(rationale["voice_plan_emitted"])
        self.assertEqual(rationale["provider_requested"], result.voice_plan.provider)
        self.assertEqual(rationale["voice_id_requested"], result.voice_plan.voice_id)
        self.assertEqual(rationale["style_requested"], result.voice_plan.style)
        self.assertEqual(rationale["fallback_order"], result.voice_plan.runtime_constraints.fallback_order)
        self.assertEqual(rationale["confidence"], result.confidence)
        self.assertEqual(rationale["confidence_level"], result.confidence_level)

    def test_missing_or_degraded_inputs_include_missing_audio_trace_and_confidence_penalties(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        identifiers = {item["identifier"] for item in result.voice_trace["missing_or_degraded_inputs"]}

        self.assertIn("tts_execution_trace", identifiers)
        self.assertIn("tts_trace", identifiers)
        self.assertIn("TTS_EXECUTION_TRACE_MISSING", identifiers)
        self.assertIn("AUDIO_TRACE_MISSING_CAP_APPLIED", identifiers)

    def test_audit_summary_is_reconstructible_when_all_sections_exist(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        summary = result.voice_trace["audit_summary"]

        self.assertTrue(summary["reconstructible"])
        self.assertTrue(summary["fallback_visible"])
        self.assertTrue(summary["audio_trace_status_visible"])
        self.assertTrue(summary["confidence_visible"])
        self.assertEqual(summary["silent_failure_indicators"], [])

    def test_audit_summary_reconstructible_false_when_required_section_missing(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())
        trace = dict(result.voice_trace)
        trace.pop("segment_timing")

        rebuilt_summary = VoiceTraceBuilder()._audit_summary(trace)

        self.assertFalse(rebuilt_summary["reconstructible"])
        self.assertFalse(rebuilt_summary["required_sections_present"])
        self.assertIn("MISSING_SECTION:segment_timing", rebuilt_summary["silent_failure_indicators"])

    def test_legacy_result_fields_remain_present(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="facts", script_plan=_script())

        payload = result.to_dict()

        self.assertIn("voice_plan", payload)
        self.assertIn("fallback", payload)
        self.assertIn("voice_plan_governance", payload)
        self.assertIn("delivery_semantics", payload)
        self.assertIn("segment_timing", payload)
        self.assertIn("monotony_contrast_analysis", payload)
        self.assertIn("provider_fallback_honesty", payload)
        self.assertIn("audio_validation_linkage", payload)
        self.assertIn("confidence_calibration", payload)
        self.assertIn("voice_trace", payload)

    def test_voice_trace_is_serializable(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="facts", script_plan=_script())

        encoded = json.dumps(result.to_dict(), sort_keys=True)

        self.assertIn("voice_trace_v2_6", encoded)

    def test_voice_trace_is_deterministic(self) -> None:
        service = VoiceAgentService()

        first = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).voice_trace
        second = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).voice_trace

        self.assertEqual(first, second)

    def test_trace_does_not_recalculate_or_override_confidence(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        self.assertEqual(result.voice_trace["confidence_calibration"], result.confidence_calibration)
        self.assertEqual(result.voice_trace["final_voice_plan_rationale"]["confidence"], result.confidence)


if __name__ == "__main__":
    unittest.main()
