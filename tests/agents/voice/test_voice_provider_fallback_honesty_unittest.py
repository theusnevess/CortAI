from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.voice.provider_fallback_honesty import VoiceProviderFallbackHonestyReporter
from app.creative.agents.voice.service import VoiceAgentService
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
        hook="The phone rings after the line is cut",
        setup="The call log shows no outgoing number",
        payoff="The voicemail is timestamped tomorrow",
        generation_mode="test_structured",
    )


def _voice_plan(*, provider: str = "kokoro", fallback_order: list[str] | None = None) -> VoicePlan:
    return VoicePlan(
        provider=provider,
        voice_id="af_heart",
        style="dark_calm",
        delivery_profile=VoiceDeliveryProfile(overall_mode="dark_calm", overall_rate=1.0, overall_intensity="medium"),
        segments={
            "hook": VoiceSegmentPlan(rate=1.0, emphasis="high"),
            "setup": VoiceSegmentPlan(rate=1.0, emphasis="medium"),
            "payoff": VoiceSegmentPlan(rate=1.0, emphasis="high"),
        },
        runtime_constraints=VoiceRuntimeConstraints(
            allow_provider_fallback=True,
            fallback_order=fallback_order or ["kokoro", "piper"],
        ),
    )


class VoiceProviderFallbackHonestyTests(unittest.TestCase):
    def test_service_exposes_requested_provider_and_fallback_order(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        honesty = result.provider_fallback_honesty

        self.assertEqual(honesty["honesty_version"], "voice_provider_fallback_honesty_v2_6")
        self.assertEqual(honesty["provider_requested"], "kokoro")
        self.assertEqual(honesty["voice_id_requested"], "af_heart")
        self.assertEqual(honesty["fallback_order"], ["kokoro", "piper"])
        self.assertTrue(honesty["fallback_allowed"])
        self.assertTrue(honesty["provider_order_preserved"])

    def test_voice_agent_does_not_fabricate_executed_provider_without_tts_trace(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        honesty = result.provider_fallback_honesty

        self.assertFalse(honesty["real_tts_execution_trace_present"])
        self.assertIsNone(honesty["tts_executed_provider"])
        self.assertEqual(honesty["tts_executed_provider_status"], "not_reported_by_voice_agent")
        self.assertFalse(honesty["fabricated_execution_claim"])
        self.assertIn("TTS_EXECUTED_PROVIDER_NOT_REPORTED_BY_VOICE_AGENT", honesty["reason_codes"])

    def test_tts_fallback_usage_is_not_claimed_without_router_trace(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        honesty = result.provider_fallback_honesty

        self.assertIsNone(honesty["tts_fallback_used"])
        self.assertEqual(honesty["tts_fallback_status"], "not_reported_by_voice_agent")
        self.assertIsNone(honesty["tts_fallback_reason"])
        self.assertIn("TTS_FALLBACK_USAGE_NOT_REPORTED_BY_VOICE_AGENT", honesty["reason_codes"])

    def test_voice_agent_fallback_is_scoped_to_plan_generation(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        fallback = result.provider_fallback_honesty["voice_agent_fallback"]

        self.assertFalse(fallback["used"])
        self.assertEqual(fallback["mode"], FallbackMode.NONE.value)
        self.assertEqual(fallback["scope"], "voice_plan_generation")

    def test_real_tts_trace_can_report_executed_provider_and_fallback(self) -> None:
        trace = {
            "provider_requested": "kokoro",
            "provider_executed": "piper",
            "fallback_used": True,
            "fallback_reason": "kokoro:timeout",
            "provider_attempts": [{"provider": "kokoro", "status": "failed"}, {"provider": "piper", "status": "ok"}],
        }

        honesty = VoiceProviderFallbackHonestyReporter().report(
            voice_plan=_voice_plan(),
            voice_agent_fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            tts_execution_trace=trace,
        ).to_dict()

        self.assertTrue(honesty["real_tts_execution_trace_present"])
        self.assertEqual(honesty["tts_executed_provider"], "piper")
        self.assertEqual(honesty["tts_executed_provider_status"], "reported_by_tts_router_trace")
        self.assertTrue(honesty["tts_fallback_used"])
        self.assertEqual(honesty["tts_fallback_status"], "reported_by_tts_router_trace")
        self.assertEqual(honesty["tts_fallback_reason"], "kokoro:timeout")
        self.assertEqual(len(honesty["provider_attempts"]), 2)

    def test_provider_order_deviation_is_visible_but_not_rewritten(self) -> None:
        honesty = VoiceProviderFallbackHonestyReporter().report(
            voice_plan=_voice_plan(provider="piper", fallback_order=["piper"]),
            voice_agent_fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
        ).to_dict()

        self.assertEqual(honesty["provider_requested"], "piper")
        self.assertEqual(honesty["fallback_order"], ["piper"])
        self.assertFalse(honesty["provider_order_preserved"])
        self.assertIn("PROVIDER_ORDER_DEVIATES_FROM_KOKORO_PIPER", honesty["reason_codes"])

    def test_boundary_statement_keeps_voice_agent_separate_from_tts_router(self) -> None:
        result = VoiceAgentService().resolve(account_id="acc_1", niche="horror", script_plan=_script())

        boundary = result.provider_fallback_honesty["execution_boundary"]

        self.assertTrue(boundary["voice_agent_requests_provider"])
        self.assertFalse(boundary["voice_agent_executes_tts"])
        self.assertTrue(boundary["tts_router_executes_provider"])
        self.assertTrue(boundary["voice_agent_reports_tts_execution_only_with_router_trace"])

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
        self.assertIn("voice_provider_fallback_honesty_v2_6", encoded)

    def test_provider_fallback_honesty_is_deterministic(self) -> None:
        service = VoiceAgentService()

        first = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).provider_fallback_honesty
        second = service.resolve(account_id="acc_1", niche="horror", script_plan=_script()).provider_fallback_honesty

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
