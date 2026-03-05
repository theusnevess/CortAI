from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.product.strategy_learning.errors import (
    StrategyAttributionEmptyError,
    StrategyScorecardMissingError,
    StrategyWindowMetricsMissingError,
)
from app.product.strategy_learning.schema import PATCH_KIND, validate_strategy_patch


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _share(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return count / total


def learn_strategy_patch(
    *,
    scorecard: dict[str, Any] | None,
    window_metrics: dict[str, Any] | None,
    attributions: list[dict[str, Any]],
    policy_stage: str,
    generated_at: str | None = None,
    min_videos_required: int = 5,
) -> dict[str, Any]:
    """Gera patch determinístico sem IO/side effects."""
    if scorecard is None:
        raise StrategyScorecardMissingError()
    if window_metrics is None:
        raise StrategyWindowMetricsMissingError()
    if not attributions:
        raise StrategyAttributionEmptyError()

    account_id = str(window_metrics.get("account_id") or scorecard.get("account_id") or "")
    window_id = str(window_metrics.get("window_id") or scorecard.get("window_id") or "")
    if not account_id or not window_id:
        raise StrategyWindowMetricsMissingError()

    reasons: list[str] = []
    overrides = {
        "a1_prefs_override": {},
        "a4_defaults_override": {},
        "a5_rewrite_defaults_override": {},
    }
    layers_applied: list[str] = []
    active = False

    score_status = str(scorecard.get("status") or "").upper()
    if score_status != "STABLE":
        reasons.append("SCORECARD_RED")
    videos_with_metrics = int(window_metrics.get("videos_with_metrics") or len(attributions))
    if videos_with_metrics < min_videos_required:
        reasons.append("INSUFFICIENT_VIDEOS")

    if not reasons:
        total = len(attributions)
        missing_number_bad = sum(1 for row in attributions if row.get("dominant_failure_reason") == "missing_number")
        low_tension_bad = sum(1 for row in attributions if row.get("dominant_failure_reason") == "low_tension")
        curiosity_hooks = sum(1 for row in attributions if row.get("hook_strategy") == "curiosity_gap")

        if _share(missing_number_bad, total) >= 0.60:
            overrides["a4_defaults_override"]["force_number"] = True
            reasons.append("MISSING_NUMBER_HIGH")
            layers_applied.append("A4")
        if _share(low_tension_bad, total) >= 0.60:
            overrides["a4_defaults_override"]["increase_tension"] = True
            overrides["a4_defaults_override"]["max_words_preferred"] = 9
            reasons.append("LOW_TENSION_HIGH")
            if "A4" not in layers_applied:
                layers_applied.append("A4")
        if _share(curiosity_hooks, total) >= 0.60:
            overrides["a1_prefs_override"]["prefer_angles"] = ["curiosity_gap"]
            reasons.append("HOOK_STRATEGY_CONSISTENT")
            layers_applied.append("A1")

    if layers_applied:
        active = True
    else:
        if not reasons:
            reasons.append("NO_STRONG_SIGNAL")

    if generated_at is None:
        generated_at = _now_utc_iso()

    patch = {
        "patch_id": f"sp_{account_id}_{window_id}_{policy_stage}",
        "account_id": account_id,
        "window_id": window_id,
        "policy_stage": policy_stage,
        "inputs": {
            "window_metrics_id": str(window_metrics.get("window_id") or ""),
            "scorecard_id": str(scorecard.get("scorecard_id") or ""),
            "attribution_count": len(attributions),
        },
        "overrides": overrides,
        "active": active,
        "layers_applied": sorted(set(layers_applied)),
        "reason_codes": sorted(set(reasons)),
        "patch_kind": PATCH_KIND,
        "generated_at": generated_at,
    }
    return validate_strategy_patch(patch)

