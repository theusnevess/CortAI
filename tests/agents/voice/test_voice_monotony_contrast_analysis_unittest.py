from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.voice.delivery_semantics import VoiceDeliverySemanticsMapper
from app.creative.agents.voice.monotony_contrast import VoiceMonotonyContrastAnalyzer
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
        hook="The first sound is not in the recording",
        setup="The waveform changes when the room goes silent",
        payoff="The missing sound is the only part that repeats",
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


def _analyze(plan: VoicePlan) -> dict:
    delivery_semantics = VoiceDeliverySemanticsMapper().map(voice_plan=plan, script_plan=_script()).to_dict()
    segment_timing = VoiceSegmentTimingAnalyzer().analyze(
        voice_plan=plan,
        delivery_semantics=delivery_semantics,
    ).to_dict()
    return VoiceMonotonyContrastAnalyzer().analyze(
        voice_plan=plan,
        segment_timing=segment_timing,
        delivery_semantics=delivery_semantics,
    ).to_dict()


class VoiceMonotonyContrastAnalysisTests(unittest.TestCase):
    def test_service_exposes_monotony_contrast_analysis_without_changing_voice_plan(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        analysis = result.monotony_contrast_analysis

        self.assertEqual(analysis["analysis_version"], "voice_monotony_contrast_v2_6")
        self.assertEqual(result.voice_plan.provider, "kokoro")
        self.assertEqual(result.voice_plan.voice_id, "af_heart")
        self.assertEqual(result.voice_plan.runtime_constraints.fallback_order, ["kokoro", "piper"])
        self.assertFalse(result.fallback.used)

    def test_high_monotony_when_rate_emphasis_and_pauses_are_identical(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            payoff=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
        )

        analysis = _analyze(plan)

        self.assertEqual(analysis["monotony_risk_level"], "high")
        self.assertEqual(analysis["contrast_level"], "low")
        self.assertEqual(analysis["rate_variation"], 0.0)
        self.assertFalse(analysis["emphasis_variation"])
        self.assertEqual(analysis["pause_variation_ms"], 0)
        self.assertFalse(analysis["segment_role_alignment"])
        self.assertIn("HIGH_MONOTONY_RISK", analysis["reason_codes"])
        self.assertIn("LOW_CONTRAST_DETECTED", analysis["reason_codes"])

    def test_strong_contrast_produces_low_monotony_risk(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=1.08, emphasis="high", pause_after_ms=360),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=120),
            payoff=VoiceSegmentPlan(rate=0.88, emphasis="high", pause_before_ms=480),
        )

        analysis = _analyze(plan)

        self.assertEqual(analysis["monotony_risk_level"], "low")
        self.assertEqual(analysis["contrast_level"], "high")
        self.assertEqual(analysis["rate_variation"], 0.2)
        self.assertTrue(analysis["emphasis_variation"])
        self.assertEqual(analysis["pause_variation_ms"], 360)
        self.assertTrue(analysis["segment_role_alignment"])
        self.assertIn("STRONG_CONTRAST_DETECTED", analysis["reason_codes"])
        self.assertIn("LOW_MONOTONY_RISK", analysis["reason_codes"])

    def test_partial_variation_produces_medium_monotony_risk(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=1.0, emphasis="high", pause_after_ms=160),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=120),
            payoff=VoiceSegmentPlan(rate=0.96, emphasis="medium", pause_before_ms=180),
        )

        analysis = _analyze(plan)

        self.assertEqual(analysis["monotony_risk_level"], "medium")
        self.assertEqual(analysis["contrast_level"], "medium")
        self.assertEqual(analysis["rate_variation"], 0.04)
        self.assertTrue(analysis["emphasis_variation"])
        self.assertEqual(analysis["pause_variation_ms"], 60)
        self.assertTrue(analysis["segment_role_alignment"])
        self.assertIn("PARTIAL_CONTRAST_DETECTED", analysis["reason_codes"])

    def test_missing_segment_degrades_analysis(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=1.08, emphasis="high", pause_after_ms=360),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=120),
        )

        analysis = _analyze(plan)

        self.assertFalse(analysis["analysis_complete"])
        self.assertEqual(analysis["monotony_risk_level"], "high")
        self.assertFalse(analysis["segment_role_alignment"])
        self.assertIn("voice_plan.segments.payoff_missing", analysis["missing_or_degraded_inputs"])
        self.assertIn("MONOTONY_ANALYSIS_DEGRADED_INPUT", analysis["reason_codes"])

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
        self.assertIn("voice_monotony_contrast_v2_6", encoded)

    def test_boundary_excludes_audio_execution_ml_and_performance_prediction(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        analysis = result.monotony_contrast_analysis
        encoded = json.dumps(analysis, sort_keys=True)

        self.assertEqual(
            analysis["boundary_statement"],
            "Voice monotony analysis is audit-only; TTS Router performs synthesis.",
        )
        self.assertNotIn("tts_provider_executed", analysis)
        self.assertNotIn("expected_performance", encoded)
        self.assertNotIn("prediction", encoded)
        self.assertNotIn("ml", encoded.lower())

    def test_monotony_contrast_analysis_is_deterministic(self) -> None:
        service = VoiceAgentService()

        first = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).monotony_contrast_analysis
        second = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).monotony_contrast_analysis

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
