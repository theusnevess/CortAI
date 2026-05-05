from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import VoicePlan


VOICE_PROVIDER_FALLBACK_HONESTY_VERSION = "voice_provider_fallback_honesty_v2_6"


@dataclass(frozen=True)
class VoiceProviderFallbackHonestyResult:
    honesty_version: str
    provider_requested: str
    voice_id_requested: str
    fallback_order: list[str]
    fallback_allowed: bool
    provider_order_preserved: bool
    voice_agent_fallback: dict[str, Any]
    real_tts_execution_trace_present: bool
    tts_executed_provider: str | None
    tts_executed_provider_status: str
    tts_fallback_used: bool | None
    tts_fallback_status: str
    tts_fallback_reason: str | None
    provider_attempts: list[dict[str, Any]]
    execution_boundary: dict[str, Any]
    fabricated_execution_claim: bool
    honest: bool
    reason_codes: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "honesty_version": self.honesty_version,
            "provider_requested": self.provider_requested,
            "voice_id_requested": self.voice_id_requested,
            "fallback_order": list(self.fallback_order),
            "fallback_allowed": self.fallback_allowed,
            "provider_order_preserved": self.provider_order_preserved,
            "voice_agent_fallback": dict(self.voice_agent_fallback),
            "real_tts_execution_trace_present": self.real_tts_execution_trace_present,
            "tts_executed_provider": self.tts_executed_provider,
            "tts_executed_provider_status": self.tts_executed_provider_status,
            "tts_fallback_used": self.tts_fallback_used,
            "tts_fallback_status": self.tts_fallback_status,
            "tts_fallback_reason": self.tts_fallback_reason,
            "provider_attempts": [dict(item) for item in self.provider_attempts],
            "execution_boundary": dict(self.execution_boundary),
            "fabricated_execution_claim": self.fabricated_execution_claim,
            "honest": self.honest,
            "reason_codes": list(self.reason_codes),
            "rationale": list(self.rationale),
        }


class VoiceProviderFallbackHonestyReporter:
    """Reports provider/fallback facts without claiming TTS execution."""

    EXPECTED_PROVIDER_ORDER: tuple[str, str] = ("kokoro", "piper")

    def report(
        self,
        *,
        voice_plan: VoicePlan,
        voice_agent_fallback: FallbackDecision,
        voice_plan_governance: dict[str, Any] | None = None,
        tts_execution_trace: Any | None = None,
    ) -> VoiceProviderFallbackHonestyResult:
        del voice_plan_governance
        provider_requested = str(voice_plan.provider or "").strip().lower()
        voice_id_requested = str(voice_plan.voice_id or "").strip()
        fallback_order = [
            str(provider).strip().lower()
            for provider in voice_plan.runtime_constraints.fallback_order
            if str(provider).strip()
        ]
        fallback_allowed = bool(voice_plan.runtime_constraints.allow_provider_fallback)
        provider_order_preserved = fallback_order[:2] == list(self.EXPECTED_PROVIDER_ORDER)
        trace = self._trace_dict(tts_execution_trace)
        real_trace_present = bool(trace)
        tts_executed_provider = self._trace_value(trace, "provider_executed")
        tts_fallback_used_value = self._trace_bool(trace, "fallback_used")
        tts_fallback_reason = self._trace_value(trace, "fallback_reason")
        provider_attempts = self._provider_attempts(trace)

        if real_trace_present and tts_executed_provider:
            executed_status = "reported_by_tts_router_trace"
        else:
            tts_executed_provider = None
            executed_status = "not_reported_by_voice_agent"

        if real_trace_present and "fallback_used" in trace:
            fallback_status = "reported_by_tts_router_trace"
            tts_fallback_used = bool(tts_fallback_used_value)
        else:
            fallback_status = "not_reported_by_voice_agent"
            tts_fallback_used = None
            tts_fallback_reason = None

        fabricated_execution_claim = False
        reason_codes = self._reason_codes(
            provider_requested=provider_requested,
            fallback_order=fallback_order,
            fallback_allowed=fallback_allowed,
            provider_order_preserved=provider_order_preserved,
            real_trace_present=real_trace_present,
            tts_executed_provider=tts_executed_provider,
            tts_fallback_used=tts_fallback_used,
        )
        honest = not fabricated_execution_claim and bool(provider_requested) and bool(fallback_order)
        rationale = self._rationale(
            provider_requested=provider_requested,
            fallback_order=fallback_order,
            real_trace_present=real_trace_present,
            executed_status=executed_status,
            fallback_status=fallback_status,
            reason_codes=reason_codes,
        )
        return VoiceProviderFallbackHonestyResult(
            honesty_version=VOICE_PROVIDER_FALLBACK_HONESTY_VERSION,
            provider_requested=provider_requested,
            voice_id_requested=voice_id_requested,
            fallback_order=fallback_order,
            fallback_allowed=fallback_allowed,
            provider_order_preserved=provider_order_preserved,
            voice_agent_fallback={
                "used": bool(voice_agent_fallback.used),
                "mode": str(voice_agent_fallback.mode or ""),
                "reason": str(voice_agent_fallback.reason or ""),
                "scope": "voice_plan_generation",
            },
            real_tts_execution_trace_present=real_trace_present,
            tts_executed_provider=tts_executed_provider,
            tts_executed_provider_status=executed_status,
            tts_fallback_used=tts_fallback_used,
            tts_fallback_status=fallback_status,
            tts_fallback_reason=tts_fallback_reason,
            provider_attempts=provider_attempts,
            execution_boundary={
                "voice_agent_requests_provider": True,
                "voice_agent_executes_tts": False,
                "tts_router_executes_provider": True,
                "voice_agent_reports_tts_execution_only_with_router_trace": True,
            },
            fabricated_execution_claim=fabricated_execution_claim,
            honest=honest,
            reason_codes=reason_codes,
            rationale=rationale,
        )

    def _trace_dict(self, trace: Any | None) -> dict[str, Any]:
        if trace is None:
            return {}
        if isinstance(trace, dict):
            return dict(trace)
        if hasattr(trace, "to_dict"):
            value = trace.to_dict()
            return dict(value) if isinstance(value, dict) else {}
        if hasattr(trace, "__dict__"):
            return dict(vars(trace))
        return {}

    def _trace_value(self, trace: dict[str, Any], key: str) -> str | None:
        value = trace.get(key)
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    def _trace_bool(self, trace: dict[str, Any], key: str) -> bool | None:
        if key not in trace:
            return None
        return bool(trace.get(key))

    def _provider_attempts(self, trace: dict[str, Any]) -> list[dict[str, Any]]:
        attempts = trace.get("provider_attempts") or trace.get("attempts") or []
        if not isinstance(attempts, list):
            return []
        normalized: list[dict[str, Any]] = []
        for item in attempts:
            if isinstance(item, dict):
                normalized.append(dict(item))
            else:
                normalized.append({"attempt": str(item)})
        return normalized

    def _reason_codes(
        self,
        *,
        provider_requested: str,
        fallback_order: list[str],
        fallback_allowed: bool,
        provider_order_preserved: bool,
        real_trace_present: bool,
        tts_executed_provider: str | None,
        tts_fallback_used: bool | None,
    ) -> list[str]:
        codes: list[str] = []
        if provider_requested:
            codes.append("PROVIDER_REQUEST_EXPLICIT")
        else:
            codes.append("PROVIDER_REQUEST_MISSING")
        if fallback_order:
            codes.append("FALLBACK_ORDER_EXPLICIT")
        else:
            codes.append("FALLBACK_ORDER_MISSING")
        if fallback_allowed:
            codes.append("FALLBACK_ALLOWED_BY_VOICE_PLAN")
        else:
            codes.append("FALLBACK_NOT_ALLOWED_BY_VOICE_PLAN")
        if provider_order_preserved:
            codes.append("PROVIDER_ORDER_KOKORO_PIPER_PRESERVED")
        else:
            codes.append("PROVIDER_ORDER_DEVIATES_FROM_KOKORO_PIPER")
        if real_trace_present and tts_executed_provider:
            codes.append("TTS_EXECUTED_PROVIDER_REPORTED_BY_ROUTER_TRACE")
        else:
            codes.append("TTS_EXECUTED_PROVIDER_NOT_REPORTED_BY_VOICE_AGENT")
        if tts_fallback_used is None:
            codes.append("TTS_FALLBACK_USAGE_NOT_REPORTED_BY_VOICE_AGENT")
        elif tts_fallback_used:
            codes.append("TTS_FALLBACK_USED_REPORTED_BY_ROUTER_TRACE")
        else:
            codes.append("TTS_FALLBACK_NOT_USED_REPORTED_BY_ROUTER_TRACE")
        return codes

    def _rationale(
        self,
        *,
        provider_requested: str,
        fallback_order: list[str],
        real_trace_present: bool,
        executed_status: str,
        fallback_status: str,
        reason_codes: list[str],
    ) -> list[str]:
        return [
            "Voice Agent reports requested provider and fallback order from VoicePlan only.",
            "Voice Agent does not execute TTS and must not fabricate executed provider or TTS fallback usage.",
            f"Requested provider is {provider_requested or 'missing'}; fallback order is {fallback_order}.",
            f"Real TTS execution trace present: {real_trace_present}. Executed provider status: {executed_status}. Fallback status: {fallback_status}.",
            "Reason codes: " + ", ".join(reason_codes),
        ]
