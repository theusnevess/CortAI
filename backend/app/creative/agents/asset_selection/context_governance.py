from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.asset_selection.models import AssetSelectionInput
from app.creative.contracts.creative_pack import AssetPlan, ScriptPlan, StrategyProfile, TrendProfile


ASSET_CONTEXT_GOVERNANCE_VERSION = "asset_context_governance_v2_6"


CONTEXT_PRIORITY = [
    "script_context",
    "strategy_context",
    "trend_context",
    "topic_context",
    "niche_context",
    "local_catalog_context",
    "experiment_context",
]


@dataclass(frozen=True)
class AssetContextSignal:
    context_key: str
    available: bool
    used: bool
    status: str
    priority_rank: int | None
    reason_code: str
    rationale: str
    evidence_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetContextGovernanceResult:
    governance_version: str
    policy_respected: bool
    available_context: list[str]
    used_context: list[str]
    ignored_context: list[str]
    missing_context: list[str]
    degraded_context: list[str]
    context_priority: list[str]
    context_signals: list[AssetContextSignal]
    context_summary: dict[str, Any]
    boundary_statement: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["context_signals"] = [signal.to_dict() for signal in self.context_signals]
        return payload


@dataclass(frozen=True)
class AssetContextGovernanceEvaluator:
    """Trace-only evaluator for the context consumed by Asset Selection."""

    def evaluate(
        self,
        *,
        data: AssetSelectionInput,
        asset_selection: AssetPlan,
        local_assets_available: bool,
        script_plan_used: ScriptPlan | None,
        script_fallback_used: bool,
        asset_fallback_used: bool,
        asset_fallback_reason: str,
    ) -> AssetContextGovernanceResult:
        signals = [
            self._script_signal(
                provided_script=data.script_plan,
                script_plan_used=script_plan_used,
                script_fallback_used=script_fallback_used,
            ),
            self._strategy_signal(data.strategy_profile),
            self._trend_signal(data.trend_profile),
            self._text_signal(
                context_key="topic_context",
                value=data.topic,
                reason_prefix="TOPIC",
                rationale_name="Topic",
            ),
            self._text_signal(
                context_key="niche_context",
                value=data.niche,
                reason_prefix="NICHE",
                rationale_name="Niche",
            ),
            self._local_catalog_signal(
                local_assets_available=local_assets_available,
                asset_selection=asset_selection,
                asset_fallback_used=asset_fallback_used,
                asset_fallback_reason=asset_fallback_reason,
            ),
            self._ignored_signal(
                context_key="experiment_context",
                reason_code="EXPERIMENT_CONTEXT_NOT_IN_ASSET_SELECTION_CONTRACT",
                rationale="Experiment context is not part of the current AssetSelectionInput contract.",
            ),
        ]

        available_context = [signal.context_key for signal in signals if signal.available]
        used_context = [signal.context_key for signal in signals if signal.used]
        ignored_context = [signal.context_key for signal in signals if signal.status == "ignored"]
        missing_context = [
            signal.context_key
            for signal in signals
            if signal.status == "missing" or (signal.status == "degraded" and not signal.available)
        ]
        degraded_context = [signal.context_key for signal in signals if signal.status == "degraded"]
        contradiction_codes = [
            signal.reason_code
            for signal in signals
            if signal.used and not signal.available and "FALLBACK" not in signal.reason_code
        ]
        policy_respected = not contradiction_codes

        rationale = [
            "Asset Selection context governance is trace-only and does not alter asset ranking or fallback.",
            "Context priority is explicit for auditability; existing selection behavior remains authoritative.",
        ]
        if degraded_context:
            rationale.append("Degraded context was exposed instead of being treated as complete.")
        if missing_context:
            rationale.append("Missing context was exposed instead of being fabricated.")

        return AssetContextGovernanceResult(
            governance_version=ASSET_CONTEXT_GOVERNANCE_VERSION,
            policy_respected=policy_respected,
            available_context=available_context,
            used_context=used_context,
            ignored_context=ignored_context,
            missing_context=missing_context,
            degraded_context=degraded_context,
            context_priority=list(CONTEXT_PRIORITY),
            context_signals=signals,
            context_summary={
                "script_present": data.script_plan is not None,
                "script_fallback_used": script_fallback_used,
                "strategy_present": data.strategy_profile is not None,
                "trend_present": data.trend_profile is not None,
                "topic_present": bool(str(data.topic or "").strip()),
                "niche_present": bool(str(data.niche or "").strip()),
                "local_catalog_available": local_assets_available,
                "asset_fallback_used": asset_fallback_used,
                "asset_fallback_reason": asset_fallback_reason,
            },
            boundary_statement="Asset Selection uses context for visual selection only; Strategy remains the control layer.",
            rationale=rationale,
        )

    def _rank(self, context_key: str) -> int | None:
        if context_key not in CONTEXT_PRIORITY:
            return None
        return CONTEXT_PRIORITY.index(context_key) + 1

    def _script_signal(
        self,
        *,
        provided_script: ScriptPlan | None,
        script_plan_used: ScriptPlan | None,
        script_fallback_used: bool,
    ) -> AssetContextSignal:
        context_key = "script_context"
        if provided_script is None:
            return AssetContextSignal(
                context_key=context_key,
                available=False,
                used=script_plan_used is not None,
                status="degraded" if script_fallback_used else "missing",
                priority_rank=self._rank(context_key),
                reason_code="SCRIPT_CONTEXT_MISSING_FALLBACK_USED" if script_fallback_used else "SCRIPT_CONTEXT_MISSING",
                rationale=(
                    "Script context was not provided; Asset Selection used its existing fallback script."
                    if script_fallback_used
                    else "Script context was not provided before asset fallback was returned."
                ),
                evidence_summary=self._script_evidence(script_plan_used),
            )

        missing_segments = [
            name
            for name, value in (
                ("hook", provided_script.hook),
                ("setup", provided_script.setup),
                ("payoff", provided_script.payoff),
            )
            if not str(value or "").strip()
        ]
        if missing_segments:
            return AssetContextSignal(
                context_key=context_key,
                available=True,
                used=True,
                status="degraded",
                priority_rank=self._rank(context_key),
                reason_code="SCRIPT_CONTEXT_SEGMENT_EMPTY",
                rationale="Script context is present but one or more narrative segments are empty.",
                evidence_summary={
                    **self._script_evidence(provided_script),
                    "missing_segments": missing_segments,
                },
            )
        return AssetContextSignal(
            context_key=context_key,
            available=True,
            used=True,
            status="available",
            priority_rank=self._rank(context_key),
            reason_code="SCRIPT_CONTEXT_AVAILABLE",
            rationale="Script hook/setup/payoff context is available for visual interpretation.",
            evidence_summary=self._script_evidence(provided_script),
        )

    def _script_evidence(self, script_plan: ScriptPlan | None) -> dict[str, Any]:
        if script_plan is None:
            return {"segments_present": {"hook": False, "setup": False, "payoff": False}}
        return {
            "segments_present": {
                "hook": bool(str(script_plan.hook or "").strip()),
                "setup": bool(str(script_plan.setup or "").strip()),
                "payoff": bool(str(script_plan.payoff or "").strip()),
            },
            "generation_mode": script_plan.generation_mode,
        }

    def _strategy_signal(self, strategy_profile: StrategyProfile | None) -> AssetContextSignal:
        context_key = "strategy_context"
        if strategy_profile is None:
            return AssetContextSignal(
                context_key=context_key,
                available=False,
                used=False,
                status="missing",
                priority_rank=self._rank(context_key),
                reason_code="STRATEGY_CONTEXT_MISSING",
                rationale="Strategy profile was not provided.",
            )
        degraded_fields = [
            field_name
            for field_name in ("content_mode", "variation_policy", "target_duration_range")
            if not str(getattr(strategy_profile, field_name, "") or "").strip()
        ]
        status = "degraded" if degraded_fields else "available"
        return AssetContextSignal(
            context_key=context_key,
            available=True,
            used=True,
            status=status,
            priority_rank=self._rank(context_key),
            reason_code="STRATEGY_CONTEXT_DEGRADED" if degraded_fields else "STRATEGY_CONTEXT_AVAILABLE",
            rationale=(
                "Strategy profile is present but has empty fields relevant to asset variation."
                if degraded_fields
                else "Strategy profile is available for bounded variation and constraint context."
            ),
            evidence_summary={
                "content_mode": strategy_profile.content_mode,
                "variation_policy": strategy_profile.variation_policy,
                "target_duration_range": strategy_profile.target_duration_range,
                "degraded_fields": degraded_fields,
            },
        )

    def _trend_signal(self, trend_profile: TrendProfile | None) -> AssetContextSignal:
        context_key = "trend_context"
        if trend_profile is None:
            return AssetContextSignal(
                context_key=context_key,
                available=False,
                used=False,
                status="missing",
                priority_rank=self._rank(context_key),
                reason_code="TREND_CONTEXT_MISSING",
                rationale="Trend profile was not provided.",
            )
        degraded_fields = [
            field_name
            for field_name in ("visual_style", "pacing", "trend_source")
            if not str(getattr(trend_profile, field_name, "") or "").strip()
        ]
        status = "degraded" if degraded_fields else "available"
        return AssetContextSignal(
            context_key=context_key,
            available=True,
            used=True,
            status=status,
            priority_rank=self._rank(context_key),
            reason_code="TREND_CONTEXT_DEGRADED" if degraded_fields else "TREND_CONTEXT_AVAILABLE",
            rationale=(
                "Trend profile is present but has empty visual context fields."
                if degraded_fields
                else "Trend profile is available for visual style and pacing context."
            ),
            evidence_summary={
                "visual_style": trend_profile.visual_style,
                "pacing": trend_profile.pacing,
                "trend_source": trend_profile.trend_source,
                "sample_size": trend_profile.sample_size,
                "degraded_fields": degraded_fields,
            },
        )

    def _text_signal(
        self,
        *,
        context_key: str,
        value: str,
        reason_prefix: str,
        rationale_name: str,
    ) -> AssetContextSignal:
        present = bool(str(value or "").strip())
        return AssetContextSignal(
            context_key=context_key,
            available=present,
            used=present,
            status="available" if present else "missing",
            priority_rank=self._rank(context_key),
            reason_code=f"{reason_prefix}_CONTEXT_AVAILABLE" if present else f"{reason_prefix}_CONTEXT_MISSING",
            rationale=(
                f"{rationale_name} context is available for asset selection."
                if present
                else f"{rationale_name} context is missing."
            ),
            evidence_summary={"present": present},
        )

    def _local_catalog_signal(
        self,
        *,
        local_assets_available: bool,
        asset_selection: AssetPlan,
        asset_fallback_used: bool,
        asset_fallback_reason: str,
    ) -> AssetContextSignal:
        context_key = "local_catalog_context"
        selected_paths = {
            "hook": asset_selection.hook_asset,
            "setup": asset_selection.setup_asset,
            "payoff": asset_selection.payoff_asset,
        }
        missing_segments = [name for name, path in selected_paths.items() if not str(path or "").strip()]
        if not local_assets_available:
            return AssetContextSignal(
                context_key=context_key,
                available=False,
                used=False,
                status="missing",
                priority_rank=self._rank(context_key),
                reason_code="LOCAL_CATALOG_CONTEXT_MISSING",
                rationale="No local image catalog was available; existing safe fallback path was used.",
                evidence_summary={
                    "selected_paths_present": {name: bool(path) for name, path in selected_paths.items()},
                    "asset_fallback_used": asset_fallback_used,
                    "asset_fallback_reason": asset_fallback_reason,
                },
            )
        if asset_fallback_used or missing_segments:
            return AssetContextSignal(
                context_key=context_key,
                available=True,
                used=True,
                status="degraded",
                priority_rank=self._rank(context_key),
                reason_code="LOCAL_CATALOG_CONTEXT_DEGRADED",
                rationale="Local catalog is available, but one or more segment selections required fallback or remained empty.",
                evidence_summary={
                    "selected_paths_present": {name: bool(path) for name, path in selected_paths.items()},
                    "missing_segments": missing_segments,
                    "asset_fallback_used": asset_fallback_used,
                    "asset_fallback_reason": asset_fallback_reason,
                },
            )
        return AssetContextSignal(
            context_key=context_key,
            available=True,
            used=True,
            status="available",
            priority_rank=self._rank(context_key),
            reason_code="LOCAL_CATALOG_CONTEXT_AVAILABLE",
            rationale="Local catalog is available and all segment assets were selected.",
            evidence_summary={
                "selected_paths_present": {name: bool(path) for name, path in selected_paths.items()},
                "asset_fallback_used": asset_fallback_used,
            },
        )

    def _ignored_signal(self, *, context_key: str, reason_code: str, rationale: str) -> AssetContextSignal:
        return AssetContextSignal(
            context_key=context_key,
            available=False,
            used=False,
            status="ignored",
            priority_rank=self._rank(context_key),
            reason_code=reason_code,
            rationale=rationale,
        )
