from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.agents.voice.models import VoiceAgentInput
from app.creative.contracts.creative_pack import VoicePlan, VoiceSegmentPlan


VOICE_PLAN_GOVERNANCE_VERSION = "voice_plan_governance_v2_6"


@dataclass(frozen=True)
class VoicePlanSegmentGovernance:
    segment_name: str
    present: bool
    complete: bool
    rate: float | None
    emphasis: str
    pause_after_ms: int
    pause_before_ms: int
    missing_fields: list[str] = field(default_factory=list)
    degraded_fields: list[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_name": self.segment_name,
            "present": self.present,
            "complete": self.complete,
            "rate": self.rate,
            "emphasis": self.emphasis,
            "pause_after_ms": self.pause_after_ms,
            "pause_before_ms": self.pause_before_ms,
            "missing_fields": list(self.missing_fields),
            "degraded_fields": list(self.degraded_fields),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class VoicePlanGovernanceResult:
    contract_version: str
    contract_complete: bool
    provider_requested: str
    voice_id_requested: str
    style_requested: str
    fallback_order: list[str]
    fallback_allowed: bool
    provider_in_fallback_order: bool
    fallback_order_non_empty: bool
    fallback_policy_coherent: bool
    delivery_profile_complete: bool
    segments_present: list[str]
    segment_completeness: dict[str, dict[str, Any]]
    missing_fields: list[str]
    degraded_fields: list[str]
    policy_respected: bool
    execution_boundary: dict[str, Any]
    boundary_statement: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "contract_complete": self.contract_complete,
            "provider_requested": self.provider_requested,
            "voice_id_requested": self.voice_id_requested,
            "style_requested": self.style_requested,
            "fallback_order": list(self.fallback_order),
            "fallback_allowed": self.fallback_allowed,
            "provider_in_fallback_order": self.provider_in_fallback_order,
            "fallback_order_non_empty": self.fallback_order_non_empty,
            "fallback_policy_coherent": self.fallback_policy_coherent,
            "delivery_profile_complete": self.delivery_profile_complete,
            "segments_present": list(self.segments_present),
            "segment_completeness": {key: dict(value) for key, value in self.segment_completeness.items()},
            "missing_fields": list(self.missing_fields),
            "degraded_fields": list(self.degraded_fields),
            "policy_respected": self.policy_respected,
            "execution_boundary": dict(self.execution_boundary),
            "boundary_statement": self.boundary_statement,
            "rationale": list(self.rationale),
        }


class VoicePlanGovernanceEvaluator:
    """Audits VoicePlan contract completeness without changing provider execution."""

    REQUIRED_SEGMENTS: tuple[str, ...] = ("hook", "setup", "payoff")
    EXPECTED_PROVIDER: str = "kokoro"
    EXPECTED_FALLBACK: str = "piper"

    def evaluate(
        self,
        *,
        voice_plan: VoicePlan,
        request: VoiceAgentInput | None = None,
    ) -> VoicePlanGovernanceResult:
        del request
        missing_fields: list[str] = []
        degraded_fields: list[str] = []
        provider_requested = str(voice_plan.provider or "").strip()
        voice_id_requested = str(voice_plan.voice_id or "").strip()
        style_requested = str(voice_plan.style or "").strip()
        fallback_order = [str(item).strip().lower() for item in voice_plan.runtime_constraints.fallback_order if str(item).strip()]

        fallback_allowed = bool(voice_plan.runtime_constraints.allow_provider_fallback)
        fallback_order_non_empty = bool(fallback_order)

        if not provider_requested:
            degraded_fields.append("voice_plan.provider_empty")
        if not voice_id_requested:
            degraded_fields.append("voice_plan.voice_id_empty")
        if not style_requested:
            degraded_fields.append("voice_plan.style_empty")
        if not fallback_order:
            missing_fields.append("voice_plan.runtime_constraints.fallback_order")
            degraded_fields.append("voice_plan.fallback_order_empty")

        if provider_requested and provider_requested.lower() != self.EXPECTED_PROVIDER:
            degraded_fields.append("voice_plan.provider_not_current_primary")
        provider_in_fallback_order = bool(provider_requested and provider_requested.lower() in fallback_order)
        if provider_requested and not provider_in_fallback_order:
            degraded_fields.append("voice_plan.provider_not_in_fallback_order")
        if fallback_order and fallback_order[0] != self.EXPECTED_PROVIDER:
            degraded_fields.append("voice_plan.fallback_order_primary_not_first")
        if fallback_order and self.EXPECTED_FALLBACK not in fallback_order:
            degraded_fields.append("voice_plan.fallback_order_missing_piper")
        fallback_policy_coherent = (fallback_allowed and len(fallback_order) >= 2) or (
            not fallback_allowed and len(fallback_order) <= 1
        )
        if fallback_allowed and len(fallback_order) < 2:
            degraded_fields.append("voice_plan.fallback_allowed_without_fallback_provider")
        if not fallback_allowed and len(fallback_order) >= 2:
            degraded_fields.append("voice_plan.fallback_disabled_with_fallback_order")

        (
            delivery_profile_complete,
            delivery_profile_missing,
            delivery_profile_degraded,
        ) = self._delivery_profile_findings(voice_plan)
        missing_fields.extend(delivery_profile_missing)
        degraded_fields.extend(delivery_profile_degraded)

        segment_summaries = {
            segment_name: self._segment_governance(segment_name, voice_plan.segments.get(segment_name)).to_dict()
            for segment_name in self.REQUIRED_SEGMENTS
        }
        for segment_name, summary in segment_summaries.items():
            if not summary["present"]:
                missing_fields.append(f"voice_plan.segments.{segment_name}")
            for field_name in summary["missing_fields"]:
                missing_fields.append(f"voice_plan.segments.{segment_name}.{field_name}")
            for field_name in summary["degraded_fields"]:
                degraded_fields.append(f"voice_plan.segments.{segment_name}.{field_name}")

        segments_present = [name for name in self.REQUIRED_SEGMENTS if name in voice_plan.segments]
        missing_fields = self._unique(missing_fields)
        degraded_fields = self._unique(degraded_fields)
        contract_complete = (
            not missing_fields
            and not degraded_fields
            and delivery_profile_complete
            and all(summary["complete"] for summary in segment_summaries.values())
        )
        policy_respected = (
            contract_complete
            and not degraded_fields
            and provider_requested.lower() == self.EXPECTED_PROVIDER
            and fallback_order[:2] == [self.EXPECTED_PROVIDER, self.EXPECTED_FALLBACK]
            and provider_in_fallback_order
            and fallback_policy_coherent
        )
        rationale = self._rationale(
            contract_complete=contract_complete,
            policy_respected=policy_respected,
            missing_fields=missing_fields,
            degraded_fields=degraded_fields,
            fallback_order=fallback_order,
            fallback_allowed=fallback_allowed,
            provider_in_fallback_order=provider_in_fallback_order,
            fallback_policy_coherent=fallback_policy_coherent,
        )
        return VoicePlanGovernanceResult(
            contract_version=VOICE_PLAN_GOVERNANCE_VERSION,
            contract_complete=contract_complete,
            provider_requested=provider_requested,
            voice_id_requested=voice_id_requested,
            style_requested=style_requested,
            fallback_order=fallback_order,
            fallback_allowed=fallback_allowed,
            provider_in_fallback_order=provider_in_fallback_order,
            fallback_order_non_empty=fallback_order_non_empty,
            fallback_policy_coherent=fallback_policy_coherent,
            delivery_profile_complete=delivery_profile_complete,
            segments_present=segments_present,
            segment_completeness=segment_summaries,
            missing_fields=missing_fields,
            degraded_fields=degraded_fields,
            policy_respected=policy_respected,
            execution_boundary={
                "voice_agent_executes_tts": False,
                "tts_router_executes_provider": True,
                "executed_provider_reported_by_voice_agent": False,
            },
            boundary_statement="Voice plans delivery only; TTS Router executes providers.",
            rationale=rationale,
        )

    def _delivery_profile_findings(self, voice_plan: VoicePlan) -> tuple[bool, list[str], list[str]]:
        profile = voice_plan.delivery_profile
        missing_fields: list[str] = []
        degraded_fields: list[str] = []
        if profile is None:
            missing_fields.append("voice_plan.delivery_profile")
            degraded_fields.append("voice_plan.delivery_profile_missing")
            return False, missing_fields, degraded_fields
        if not str(profile.overall_mode or "").strip():
            degraded_fields.append("voice_plan.delivery_profile.overall_mode_empty")
        if self._as_float(profile.overall_rate) <= 0.0:
            degraded_fields.append("voice_plan.delivery_profile.overall_rate_invalid")
        if not str(profile.overall_intensity or "").strip():
            degraded_fields.append("voice_plan.delivery_profile.overall_intensity_empty")
        return not degraded_fields, missing_fields, degraded_fields

    def _segment_governance(
        self,
        segment_name: str,
        segment: Any,
    ) -> VoicePlanSegmentGovernance:
        if segment is None:
            return VoicePlanSegmentGovernance(
                segment_name=segment_name,
                present=False,
                complete=False,
                rate=None,
                emphasis="",
                pause_after_ms=0,
                pause_before_ms=0,
                missing_fields=["segment"],
                rationale=f"{segment_name} segment is missing from VoicePlan.",
            )
        missing_fields: list[str] = []
        degraded_fields: list[str] = []
        if not isinstance(segment, VoiceSegmentPlan):
            return VoicePlanSegmentGovernance(
                segment_name=segment_name,
                present=True,
                complete=False,
                rate=None,
                emphasis="",
                pause_after_ms=0,
                pause_before_ms=0,
                degraded_fields=["segment_invalid"],
                rationale=f"{segment_name} segment is present but is not a valid VoiceSegmentPlan.",
            )
        rate = self._as_float(segment.rate)
        pause_after = self._as_int(segment.pause_after_ms)
        pause_before = self._as_int(segment.pause_before_ms)
        if rate <= 0.0:
            degraded_fields.append("rate_invalid")
        if not str(segment.emphasis or "").strip():
            degraded_fields.append("emphasis_empty")
        if pause_after is None:
            degraded_fields.append("pause_after_ms_invalid")
            pause_after = 0
        elif pause_after < 0:
            degraded_fields.append("pause_after_ms_negative")
        if pause_before is None:
            degraded_fields.append("pause_before_ms_invalid")
            pause_before = 0
        elif pause_before < 0:
            degraded_fields.append("pause_before_ms_negative")
        complete = not missing_fields and not degraded_fields
        if complete:
            rationale = f"{segment_name} segment has rate, emphasis, and non-negative pause fields."
        else:
            rationale = f"{segment_name} segment has incomplete or degraded delivery fields."
        return VoicePlanSegmentGovernance(
            segment_name=segment_name,
            present=True,
            complete=complete,
            rate=rate,
            emphasis=str(segment.emphasis or ""),
            pause_after_ms=pause_after,
            pause_before_ms=pause_before,
            missing_fields=missing_fields,
            degraded_fields=degraded_fields,
            rationale=rationale,
        )

    def _rationale(
        self,
        *,
        contract_complete: bool,
        policy_respected: bool,
        missing_fields: list[str],
        degraded_fields: list[str],
        fallback_order: list[str],
        fallback_allowed: bool,
        provider_in_fallback_order: bool,
        fallback_policy_coherent: bool,
    ) -> list[str]:
        rationale = [
            "VoicePlan governance audits the emitted plan only; it does not execute TTS.",
            "Provider execution remains owned by TTS Router.",
        ]
        if contract_complete:
            rationale.append("VoicePlan contract contains requested provider, voice id, style, delivery profile, and hook/setup/payoff segments.")
        elif missing_fields:
            rationale.append("VoicePlan contract has missing fields: " + ", ".join(missing_fields))
        else:
            rationale.append("VoicePlan contract has degraded fields but no missing required fields.")
        if degraded_fields:
            rationale.append("VoicePlan has degraded fields: " + ", ".join(degraded_fields))
        if fallback_order:
            rationale.append("Fallback order is explicit: " + " -> ".join(fallback_order))
        if not provider_in_fallback_order:
            rationale.append("Requested provider is not present in fallback order.")
        if not fallback_policy_coherent:
            rationale.append(
                "Fallback allowed flag is not coherent with fallback order length: "
                + f"fallback_allowed={fallback_allowed}, fallback_order_size={len(fallback_order)}."
            )
        if policy_respected:
            rationale.append("Current Kokoro primary and Piper fallback policy is respected.")
        else:
            rationale.append("Current Kokoro/Piper policy is not fully respected or contract is incomplete.")
        return rationale

    def _as_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _as_int(self, value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        output: list[str] = []
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            output.append(value)
        return output
