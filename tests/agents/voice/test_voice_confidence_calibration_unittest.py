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
from app.creative.agents.voice.confidence_calibration import VoiceConfidenceCalibrator
from app.creative.agents.voice.delivery_semantics import VoiceDeliverySemanticsMapper
from app.creative.agents.voice.monotony_contrast import VoiceMonotonyContrastAnalyzer
from app.creative.agents.voice.provider_fallback_honesty import VoiceProviderFallbackHonestyReporter
from app.creative.agents.voice.segment_timing import VoiceSegmentTimingAnalyzer
from app.creative.agents.voice.service import VoiceAgentService
from app.creative.agents.voice.voice_plan_governance import VoicePlanGovernanceEvaluator
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import (
    ScriptPlan,
    VoiceDeliveryProfile,
    VoicePlan,
    VoiceRuntimeConstraints,
    VoiceSegmentPlan,
)


def _script() -> ScriptPlan:
    return ScriptPlan(
        hook="The first voice appears before the recording starts",
        setup="The audio log skips only the seconds with footsteps",
        payoff="The missing seconds contain the name of the caller",
        generation_mode="test_structured",
    )


def _voice_plan(
    *,
    hook: VoiceSegmentPlan | None = None,
    setup: VoiceSegmentPlan | None = None,
    payoff: VoiceSegmentPlan | None = None,
) -> VoicePlan:
    return VoicePlan(
        provider="kokoro",
        voice_id="af_heart",
        style="dark_calm",
        delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
        segments={
            "hook": hook or VoiceSegmentPlan(rate=1.08, emphasis="high", pause_after_ms=360),
            "setup": setup or VoiceSegmentPlan(rate=1.0, emphasis="medium", pause_after_ms=120),
            "payoff": payoff or VoiceSegmentPlan(rate=0.88, emphasis="high", pause_before_ms=480),
        },
        runtime_constraints=VoiceRuntimeConstraints(allow_provider_fallback=True, fallback_order=["kokoro", "piper"]),
    )


def _calibrate(plan: VoicePlan, *, tts_trace=None) -> dict:
    governance = VoicePlanGovernanceEvaluator().evaluate(voice_plan=plan).to_dict()
    semantics = VoiceDeliverySemanticsMapper().map(voice_plan=plan, script_plan=_script()).to_dict()
    timing = VoiceSegmentTimingAnalyzer().analyze(voice_plan=plan, delivery_semantics=semantics).to_dict()
    monotony = VoiceMonotonyContrastAnalyzer().analyze(
        voice_plan=plan,
        segment_timing=timing,
        delivery_semantics=semantics,
    ).to_dict()
    fallback = FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason="")
    provider_honesty = VoiceProviderFallbackHonestyReporter().report(
        voice_plan=plan,
        voice_agent_fallback=fallback,
        tts_execution_trace=tts_trace,
    ).to_dict()
    audio_linkage = VoiceAudioValidationLinker().link(
        voice_plan=plan,
        tts_trace=tts_trace,
        audio_artifact={"audio_path": "OUT/audio/test.wav"} if tts_trace else None,
    ).to_dict()
    return VoiceConfidenceCalibrator().calibrate(
        voice_plan_governance=governance,
        delivery_semantics=semantics,
        segment_timing=timing,
        monotony_contrast_analysis=monotony,
        provider_fallback_honesty=provider_honesty,
        audio_validation_linkage=audio_linkage,
    ).to_dict()


def _tts_trace(*, fallback_used: bool = False) -> TtsExecutionTrace:
    return TtsExecutionTrace(
        provider_requested="kokoro",
        provider_executed="piper" if fallback_used else "kokoro",
        voice_id_requested="af_heart",
        voice_id_executed="en_US-lessac-medium.onnx" if fallback_used else "af_heart",
        style_requested="dark_calm",
        fallback_used=fallback_used,
        fallback_reason="kokoro:timeout" if fallback_used else "",
        latency_s=0.32,
        audio_duration_s=8.6,
        segment_durations=[2.2, 3.1, 3.3],
    )


class VoiceConfidenceCalibrationTests(unittest.TestCase):
    def test_service_default_missing_audio_trace_prevents_high_confidence(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        self.assertLess(result.confidence, 0.70)
        self.assertEqual(result.confidence_level, "medium")
        self.assertIn("TTS_EXECUTION_TRACE_MISSING", result.confidence_rationale["penalties"])
        self.assertIn("AUDIO_TRACE_MISSING_CAP_APPLIED", result.confidence_rationale["penalties"])

    def test_high_confidence_requires_complete_trace_and_strong_contrast(self) -> None:
        calibration = _calibrate(_voice_plan(), tts_trace=_tts_trace())

        self.assertGreaterEqual(calibration["confidence"], 0.70)
        self.assertEqual(calibration["confidence_level"], "high")
        self.assertEqual(calibration["confidence_rationale"]["confidence_meaning"], "trust_in_voice_plan_execution_readiness")
        self.assertTrue(calibration["confidence_components"]["audio_validation_support"] >= 0.9)

    def test_low_confidence_when_contract_and_timing_are_degraded(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=0.0, emphasis=""),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            payoff=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
        )

        calibration = _calibrate(plan)

        self.assertEqual(calibration["confidence_level"], "low")
        self.assertIn("VOICE_PLAN_CONTRACT_INCOMPLETE", calibration["confidence_rationale"]["penalties"])
        self.assertIn("HIGH_MONOTONY_RISK", calibration["confidence_rationale"]["penalties"])

    def test_low_contrast_reduces_confidence(self) -> None:
        plan = _voice_plan(
            hook=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            setup=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            payoff=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
        )

        calibration = _calibrate(plan, tts_trace=_tts_trace())

        self.assertLess(calibration["confidence_components"]["contrast_strength"], 0.30)
        self.assertIn("HIGH_MONOTONY_RISK", calibration["confidence_rationale"]["penalties"])
        self.assertLess(calibration["confidence"], 0.70)

    def test_executed_fallback_penalizes_confidence(self) -> None:
        no_fallback = _calibrate(_voice_plan(), tts_trace=_tts_trace(fallback_used=False))
        fallback = _calibrate(_voice_plan(), tts_trace=_tts_trace(fallback_used=True))

        self.assertLess(fallback["confidence"], no_fallback["confidence"])
        self.assertGreater(fallback["confidence_components"]["fallback_penalty"], 0.0)
        self.assertIn("FALLBACK_PENALTY_APPLIED", fallback["confidence_rationale"]["penalties"])

    def test_confidence_is_not_constant_across_scenarios(self) -> None:
        default = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script()).confidence
        complete = _calibrate(_voice_plan(), tts_trace=_tts_trace())["confidence"]
        degraded = _calibrate(
            _voice_plan(
                hook=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                setup=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
                payoff=VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            )
        )["confidence"]

        self.assertGreater(len({default, complete, degraded}), 2)

    def test_result_payload_remains_backward_compatible_and_serializable(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="facts", script_plan=_script())

        payload = result.to_dict()
        encoded = json.dumps(payload, sort_keys=True)

        self.assertIn("voice_plan", payload)
        self.assertIn("fallback", payload)
        self.assertIn("confidence", payload)
        self.assertIn("confidence_level", payload)
        self.assertIn("confidence_components", payload)
        self.assertIn("confidence_rationale", payload)
        self.assertIn("confidence_calibration", payload)
        self.assertIn("voice_confidence_calibration_v2_6", encoded)

    def test_confidence_boundary_excludes_performance_prediction(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())
        encoded = json.dumps(result.confidence_calibration, sort_keys=True)

        self.assertEqual(
            result.confidence_rationale["boundary_statement"],
            "Voice confidence is not performance prediction.",
        )
        self.assertNotIn("expected_performance", encoded)
        self.assertNotIn("likely_to_perform", encoded.lower())
        self.assertNotIn("publishability", encoded.lower())

    def test_confidence_is_deterministic(self) -> None:
        service = VoiceAgentService()

        first = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).confidence_calibration
        second = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).confidence_calibration

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
