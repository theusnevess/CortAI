from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan, StrategyProfile, VoicePlan


@dataclass(frozen=True)
class VoiceAgentInput:
    account_id: str
    niche: str
    script_plan: ScriptPlan | None = None
    strategy_profile: StrategyProfile | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.script_plan is not None:
            payload["script_plan"] = self.script_plan.to_dict()
        if self.strategy_profile is not None:
            payload["strategy_profile"] = self.strategy_profile.to_dict()
        return payload


@dataclass(frozen=True)
class VoiceAgentResult:
    voice_plan: VoicePlan
    fallback: FallbackDecision
    voice_plan_governance: dict[str, Any] = field(default_factory=dict)
    delivery_semantics: dict[str, Any] = field(default_factory=dict)
    segment_timing: dict[str, Any] = field(default_factory=dict)
    monotony_contrast_analysis: dict[str, Any] = field(default_factory=dict)
    provider_fallback_honesty: dict[str, Any] = field(default_factory=dict)
    audio_validation_linkage: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    confidence_level: str = "low"
    confidence_components: dict[str, float] = field(default_factory=dict)
    confidence_rationale: dict[str, Any] = field(default_factory=dict)
    confidence_calibration: dict[str, Any] = field(default_factory=dict)
    voice_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "voice_plan": self.voice_plan.to_dict(),
            "fallback": self.fallback.to_dict(),
            "voice_plan_governance": dict(self.voice_plan_governance),
            "delivery_semantics": dict(self.delivery_semantics),
            "segment_timing": dict(self.segment_timing),
            "monotony_contrast_analysis": dict(self.monotony_contrast_analysis),
            "provider_fallback_honesty": dict(self.provider_fallback_honesty),
            "audio_validation_linkage": dict(self.audio_validation_linkage),
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "confidence_components": dict(self.confidence_components),
            "confidence_rationale": dict(self.confidence_rationale),
            "confidence_calibration": dict(self.confidence_calibration),
            "voice_trace": dict(self.voice_trace),
        }
