from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from src.core.policy.default_policy_by_stage import (
    ACCOUNT_POLICY_STAGES,
    DEFAULT_POLICY_BY_STAGE_V1,
)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def resolve_policy(account_metrics: dict[str, Any], target_rpm: float) -> str:
    """
    Resolve stage deterministically (v1.0).
    Precedence: RECOVERY > MONETIZATION > GROWTH.
    """
    videos_last_10_count = _as_int(account_metrics.get("videos_last_10_count"), default=0)
    avg_3s_retention_last_10 = _as_float(account_metrics.get("avg_3s_retention_last_10"), default=0.0)
    followers = _as_int(account_metrics.get("followers"), default=0)
    avg_rpm_last_10 = _as_float(account_metrics.get("avg_rpm_last_10"), default=0.0)

    if videos_last_10_count < 10:
        return "GROWTH"

    if avg_3s_retention_last_10 < 0.35:
        return "RECOVERY"

    if followers >= 10000 and avg_rpm_last_10 >= _as_float(target_rpm, default=0.0):
        return "MONETIZATION"

    return "GROWTH"


def compose_policy(
    account_id: str,
    metrics: dict[str, Any],
    target_rpm: float,
    *,
    updated_at: str | None = None,
) -> dict[str, Any]:
    """
    Compose full policy document from resolved stage + stage defaults.
    """
    stage = resolve_policy(metrics, target_rpm=target_rpm)
    if stage not in ACCOUNT_POLICY_STAGES:
        raise ValueError("ContractViolation: invalid stage from resolver")

    stage_defaults = deepcopy(DEFAULT_POLICY_BY_STAGE_V1[stage])
    videos_considered = _as_int(metrics.get("videos_last_10_count"), default=0)
    ts = updated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    return {
        "account_id": account_id,
        "stage": stage,
        "targets": stage_defaults["targets"],
        "constraints": stage_defaults["constraints"],
        "metrics_window": {
            "videos_considered": videos_considered,
            "updated_at": ts,
        },
    }
