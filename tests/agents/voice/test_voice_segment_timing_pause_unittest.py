from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.voice.segment_timing import VoiceSegmentTimingAnalyzer
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
        hook="The first frame contains a second shadow",
        setup="The camera angle changes before anyone enters",
        payoff="The shadow belongs to the person holding the camera",
        generation_mode="test_structured",
    )


def _voice_plan(
    *,
    hook: VoiceSegmentPlan | None = None,
    setup: VoiceSegmentPlan | None = None,
    payoff: VoiceSegmentPlan | None = None,
) -> VoicePlan:
    segments = {}
    if hook is not None:
        segments["hook"] = hook
    if setup is not None:
        segments["setup"] = setup
    if payoff is not None:
        segments["payoff"] = payoff
    return VoicePlan(
        provider="kokoro",
        voice_id="af_heart",
        style="dark_calm",
        delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
        segments=segments,
        runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
    )


class VoiceSegmentTimingPauseTests(unittest.TestCase):
    def test_service_exposes_segment_timing_without_changing_voice_plan(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        timing = result.segment_timing

        self.assertEqual(timing["timing_version"], "voice_segment_timing_v2_6")
        self.assertEqual(result.voice_plan.provider, "kokoro")
        self.assertEqual(result.voice_plan.voice_id, "af_heart")
        self.assertEqual(result.voice_plan.runtime_constraints.fallback_order, ["kokoro", "piper"])
        self.assertFalse(result.fallback.used)

    def test_segment_timing_contains_rate_emphasis_and_pause_statuses(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        segment_timing = result.segment_timing["segment_timing"]

        self.assertEqual(segment_timing["hook"]["rate_status"], "slow")
        self.assertEqual(segment_timing["hook"]["emphasis_status"], "high")
        self.assertEqual(segment_timing["hook"]["pause_status"], "attention_pause")
        self.assertEqual(segment_timing["setup"]["rate_status"], "measured")
        self.assertEqual(segment_timing["payoff"]["pause_status"], "landing_pause")

    def test_hook_setup_payoff_contrast_is_detected(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        contrast = result.segment_timing["timing_contrast"]

        self.assertTrue(contrast["contrast_detected"])
        self.assertTrue(contrast["expected_contrast_present"])
        self.assertEqual(contrast["contrast_level"], "high")
        self.assertTrue(contrast["hook_has_attention_pause"])
        self.assertTrue(contrast["payoff_has_landing_pause"])

    def test_invalid_rate_and_empty_emphasis_are_degraded(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=0.0, emphasis="", pause_after_ms=320),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=180),
            payoff=VoiceSegmentPlan(rate=0.93, emphasis="high", pause_before_ms=420),
        )

        timing = VoiceSegmentTimingAnalyzer().analyze(voice_plan=plan).to_dict()

        self.assertFalse(timing["timing_complete"])
        self.assertIn("voice_plan.segments.hook.rate_invalid", timing["missing_or_degraded_inputs"])
        self.assertIn("voice_plan.segments.hook.emphasis_empty", timing["missing_or_degraded_inputs"])
        self.assertEqual(timing["segment_timing"]["hook"]["rate_status"], "invalid")

    def test_negative_pause_is_degraded(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=0.96, emphasis="high", pause_after_ms=-1),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=180),
            payoff=VoiceSegmentPlan(rate=0.93, emphasis="high", pause_before_ms=420),
        )

        timing = VoiceSegmentTimingAnalyzer().analyze(voice_plan=plan).to_dict()

        self.assertFalse(timing["timing_complete"])
        self.assertIn("voice_plan.segments.hook.pause_after_ms_negative", timing["missing_or_degraded_inputs"])
        self.assertEqual(timing["segment_timing"]["hook"]["pause_status"], "invalid")

    def test_weak_timing_contrast_is_visible_without_audio_changes(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            payoff=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
        )

        timing = VoiceSegmentTimingAnalyzer().analyze(voice_plan=plan).to_dict()

        self.assertFalse(timing["timing_complete"])
        self.assertFalse(timing["timing_contrast"]["expected_contrast_present"])
        self.assertEqual(timing["timing_contrast"]["contrast_level"], "none")
        self.assertIn("voice_plan.segments.hook.attention_pause_weak", timing["missing_or_degraded_inputs"])
        self.assertIn("voice_plan.segments.payoff.landing_pause_weak", timing["missing_or_degraded_inputs"])

    def test_missing_segment_is_visible(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=0.96, emphasis="high", pause_after_ms=320),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=180),
        )

        timing = VoiceSegmentTimingAnalyzer().analyze(voice_plan=plan).to_dict()

        self.assertFalse(timing["segment_timing"]["payoff"]["present"])
        self.assertIn("voice_plan.segments.payoff_missing", timing["missing_or_degraded_inputs"])
        self.assertFalse(timing["timing_complete"])

    def test_boundary_excludes_tts_execution_confidence_and_monotony(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        timing = result.segment_timing
        encoded = json.dumps(timing, sort_keys=True)

        self.assertEqual(
            timing["boundary_statement"],
            "Voice timing analysis is audit-only; TTS Router performs synthesis.",
        )
        self.assertNotIn("tts_provider_executed", timing)
        self.assertNotIn("confidence", timing)
        self.assertNotIn("monotony", encoded)

    def test_result_payload_remains_backward_compatible_and_serializable(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="facts", script_plan=_script())

        payload = result.to_dict()
        encoded = json.dumps(payload, sort_keys=True)

        self.assertIn("voice_plan", payload)
        self.assertIn("fallback", payload)
        self.assertIn("voice_plan_governance", payload)
        self.assertIn("delivery_semantics", payload)
        self.assertIn("segment_timing", payload)
        self.assertIn("voice_segment_timing_v2_6", encoded)

    def test_segment_timing_is_deterministic(self) -> None:
        service = VoiceAgentService()

        first = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).segment_timing
        second = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).segment_timing

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
