from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PatternSignature:
    hook_family: str = "other"
    payoff_structure: str = "other"
    semantic_closure_type: str = "other"
    visual_payoff_family: str = "other"
    motif_signature: str = "other"
    strategy_variation_policy: str = "low"
    content_mode: str = "standard"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NoveltyPressureProfile:
    semantic_saturation_level: str = "none"
    visual_saturation_level: str = "none"
    structural_saturation_level: str = "none"
    dominant_repeated_patterns: list[str] = field(default_factory=list)
    novelty_budget: str = "low"
    pressure_level: str = "low"
    recommended_variation_policy: str = "low"
    blocked_payoff_structures: list[str] = field(default_factory=list)
    blocked_visual_payoff_categories: list[str] = field(default_factory=list)
    preferred_alternative_payoff_families: list[str] = field(default_factory=list)
    trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "semantic_saturation_level": self.semantic_saturation_level,
            "visual_saturation_level": self.visual_saturation_level,
            "structural_saturation_level": self.structural_saturation_level,
            "dominant_repeated_patterns": list(self.dominant_repeated_patterns),
            "novelty_budget": self.novelty_budget,
            "pressure_level": self.pressure_level,
            "recommended_variation_policy": self.recommended_variation_policy,
            "blocked_payoff_structures": list(self.blocked_payoff_structures),
            "blocked_visual_payoff_categories": list(self.blocked_visual_payoff_categories),
            "preferred_alternative_payoff_families": list(self.preferred_alternative_payoff_families),
            "trace": dict(self.trace),
        }


@dataclass(frozen=True)
class NoveltyInput:
    account_id: str
    recent_approved_executions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "recent_approved_executions": list(self.recent_approved_executions),
        }


@dataclass(frozen=True)
class NoveltyResult:
    novelty_pressure_profile: NoveltyPressureProfile
    signatures_considered: list[PatternSignature] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "novelty_pressure_profile": self.novelty_pressure_profile.to_dict(),
            "signatures_considered": [item.to_dict() for item in self.signatures_considered],
        }
