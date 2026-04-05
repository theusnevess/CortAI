from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.edit_plan import EditPlan


@dataclass(frozen=True)
class StrategyProfile:
    goal: str = "retention"
    content_mode: str = "standard"
    hook_aggressiveness: str = "medium"
    target_duration_range: str = "8-12s"
    variation_policy: str = "low"
    novelty_hints: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrendEvidenceReference:
    evidence_type: str = ""
    source: str = ""
    reference_id: str = ""
    reference_url: str = ""
    captured_at: str = ""
    region: str = "US"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrendProfile:
    niche: str = "default"
    dominant_hooks: list[str] = field(default_factory=list)
    avg_duration: str = "8-12"
    pacing: str = "baseline"
    visual_style: str = "phase1_baseline"
    text_style: str = "caption_focus"
    region: str = "US"
    trend_source: str = "manual_file_legacy"
    confidence_scores: dict[str, float] = field(default_factory=dict)
    updated_at: str = ""
    valid_until: str = ""
    sample_size: int = 0
    evidence: list[TrendEvidenceReference] = field(default_factory=list)
    trend_version: str = "2.0"
    collector_version: str = "trend-analysis-agent-v2_0"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        return payload


@dataclass(frozen=True)
class ScriptPlan:
    hook: str
    setup: str
    payoff: str
    generation_mode: str = "contextual"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def narration_text(self) -> str:
        blocks = []
        for value in (self.hook, self.setup, self.payoff):
            text = str(value or "").strip()
            if not text:
                continue
            if text.endswith(("?", "!", ".")):
                blocks.append(text)
            else:
                blocks.append(f"{text}.")
        return "\n\n".join(blocks)


@dataclass(frozen=True)
class VoiceDeliveryProfile:
    overall_mode: str = "baseline"
    overall_rate: float = 1.0
    overall_intensity: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VoiceSegmentPlan:
    rate: float = 1.0
    emphasis: str = "medium"
    pause_after_ms: int = 0
    pause_before_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VoiceRuntimeConstraints:
    allow_provider_fallback: bool = True
    fallback_order: list[str] = field(default_factory=lambda: ["piper"])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VoicePlan:
    provider: str
    voice_id: str
    style: str
    fallback_used: bool = False
    delivery_profile: VoiceDeliveryProfile = field(default_factory=VoiceDeliveryProfile)
    segments: dict[str, VoiceSegmentPlan] = field(default_factory=dict)
    runtime_constraints: VoiceRuntimeConstraints = field(default_factory=VoiceRuntimeConstraints)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "voice_id": self.voice_id,
            "style": self.style,
            "fallback_used": self.fallback_used,
            "delivery_profile": self.delivery_profile.to_dict(),
            "segments": {name: segment.to_dict() for name, segment in self.segments.items()},
            "runtime_constraints": self.runtime_constraints.to_dict(),
        }


@dataclass(frozen=True)
class AssetBackgroundPlan:
    source: str = "local"
    path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetDecisionContract:
    entity: str = ""
    event: str = ""
    anomaly_type: str = ""
    visibility_requirement: str = ""
    photographability: str = ""
    justification: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualQuery:
    subject: str = ""
    state_or_event: str = ""
    environment: str = ""
    lighting: str = ""
    framing: str = ""
    mood: str = ""
    search_query_real: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetSegmentPlan:
    background: AssetBackgroundPlan = field(default_factory=AssetBackgroundPlan)
    category: str = ""
    tags: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    decision_contract: AssetDecisionContract = field(default_factory=AssetDecisionContract)
    visual_query: VisualQuery = field(default_factory=VisualQuery)

    def to_dict(self) -> dict[str, Any]:
        return {
            "background": self.background.to_dict(),
            "category": self.category,
            "tags": list(self.tags),
            "effects": list(self.effects),
            "decision_contract": self.decision_contract.to_dict(),
            "visual_query": self.visual_query.to_dict(),
        }


@dataclass(frozen=True)
class AssetRuntimeConstraints:
    allow_safe_fallback: bool = True
    allow_comfyui_generation_fallback: bool = False
    allow_comfyui_edit: bool = False
    deterministic_seed: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetPlan:
    hook_asset: str = ""
    setup_asset: str = ""
    payoff_asset: str = ""
    visual_style: str = "phase1_baseline"
    motion_profile: str = "phase1_baseline"
    visual_anchor: str = ""
    semantic_pattern: str = ""
    entity: str = ""
    case_visual_pack: dict[str, Any] = field(default_factory=dict)
    segments: dict[str, AssetSegmentPlan] = field(default_factory=dict)
    runtime_constraints: AssetRuntimeConstraints = field(default_factory=AssetRuntimeConstraints)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hook_asset": self.hook_asset,
            "setup_asset": self.setup_asset,
            "payoff_asset": self.payoff_asset,
            "visual_style": self.visual_style,
            "motion_profile": self.motion_profile,
            "visual_anchor": self.visual_anchor,
            "semantic_pattern": self.semantic_pattern,
            "entity": self.entity,
            "case_visual_pack": dict(self.case_visual_pack),
            "segments": {name: segment.to_dict() for name, segment in self.segments.items()},
            "runtime_constraints": self.runtime_constraints.to_dict(),
        }


@dataclass(frozen=True)
class LearningInsights:
    recommended_hook_type: str = "question"
    target_duration_range: str = "8-12s"
    preferred_visual_style: str = "phase1_baseline"
    preferred_voice_style: str = "phase1_baseline"
    saturation_signal: str = "baseline"
    recommendations: list[str] = field(default_factory=list)
    signal_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningPolicySignal:
    value: str = ""
    confidence: float = 0.0
    evidence_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningPolicy:
    hook_type_bias: LearningPolicySignal = field(default_factory=LearningPolicySignal)
    duration_bias: LearningPolicySignal = field(default_factory=LearningPolicySignal)
    payoff_specificity_bias: LearningPolicySignal = field(default_factory=LearningPolicySignal)
    risk_adjustment_hint: LearningPolicySignal = field(default_factory=LearningPolicySignal)
    variation_tolerance_hint: LearningPolicySignal = field(default_factory=LearningPolicySignal)
    confidence_summary: dict[str, Any] = field(default_factory=dict)
    policy_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hook_type_bias": self.hook_type_bias.to_dict(),
            "duration_bias": self.duration_bias.to_dict(),
            "payoff_specificity_bias": self.payoff_specificity_bias.to_dict(),
            "risk_adjustment_hint": self.risk_adjustment_hint.to_dict(),
            "variation_tolerance_hint": self.variation_tolerance_hint.to_dict(),
            "confidence_summary": dict(self.confidence_summary),
            "policy_trace": dict(self.policy_trace),
        }


@dataclass(frozen=True)
class PatternFindingSummary:
    pattern_name: str
    evidence_count: int = 0
    approve_rate: float = 0.0
    hold_rate: float = 0.0
    reject_rate: float = 0.0
    avg_overall_score: float = 0.0
    avg_product_quality: float = 0.0
    contaminated_evidence_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentPlan:
    experiment_id: str = "exp_default"
    variant_id: str = "A"
    variant_type: str = "baseline"
    variant_params: dict[str, Any] = field(default_factory=dict)
    fallback_used: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentAssignment:
    assignment_id: str
    experiment_id: str
    subject_key: str
    variant_id: str
    assigned_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CreativePack:
    creative_pack_id: str
    account_id: str
    niche: str
    topic: str
    strategy_profile: StrategyProfile
    trend_profile: TrendProfile
    script_plan: ScriptPlan
    voice_plan: VoicePlan
    asset_plan: AssetPlan
    learning_insights: LearningInsights
    experiment_plan: ExperimentPlan
    experiment_assignment: ExperimentAssignment | None
    generated_at: str
    orchestrator_version: str
    learning_policy: LearningPolicy = field(default_factory=LearningPolicy)
    pattern_findings_summary: list[PatternFindingSummary] = field(default_factory=list)
    account_health_status: str = "SAFE"
    recommended_constraints: dict[str, Any] = field(default_factory=dict)
    edit_plan: EditPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["strategy_profile"] = self.strategy_profile.to_dict()
        payload["trend_profile"] = self.trend_profile.to_dict()
        payload["script_plan"] = self.script_plan.to_dict()
        payload["voice_plan"] = self.voice_plan.to_dict()
        payload["asset_plan"] = self.asset_plan.to_dict()
        payload["asset_selection"] = self.asset_plan.to_dict()
        payload["edit_plan"] = None if self.edit_plan is None else self.edit_plan.to_dict()
        payload["learning_insights"] = self.learning_insights.to_dict()
        payload["learning_policy"] = self.learning_policy.to_dict()
        payload["pattern_findings_summary"] = [item.to_dict() for item in self.pattern_findings_summary]
        payload["experiment_plan"] = self.experiment_plan.to_dict()
        if self.experiment_assignment is not None:
            payload["experiment_assignment"] = self.experiment_assignment.to_dict()
        return payload
