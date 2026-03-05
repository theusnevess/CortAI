from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.product.attribution.errors import (
    AttributionBuildError,
    AttributionMetricsMissingError,
    AttributionWindowMissingError,
    PolicyStageNotFoundError,
    PublishRecordNotFoundError,
)
from app.product.attribution.schema import validate_content_attribution


@dataclass(frozen=True)
class AttributionDeps:
    """Dependências de leitura usadas pelo builder de attribution."""

    publish_records_repo: Any
    video_metrics_repo: Any
    window_metrics_repo: Any
    scorecard_repo: Any | None = None


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _call_optional(repo: Any, method_names: tuple[str, ...], *args: Any) -> Any:
    for name in method_names:
        method = getattr(repo, name, None)
        if callable(method):
            return method(*args)
    return None


def _must_call(repo: Any, method_names: tuple[str, ...], *args: Any) -> Any:
    result = _call_optional(repo, method_names, *args)
    if result is None:
        raise AttributionBuildError(f"DEPENDENCY_METHOD_MISSING: expected one of {method_names}")
    return result


def _resolve_policy_stage(
    *,
    publish: dict[str, Any],
    window_metrics: dict[str, Any],
    scorecard: dict[str, Any] | None,
) -> str:
    stage = publish.get("policy_stage")
    if isinstance(stage, str) and stage.strip():
        return stage.strip()
    stage = window_metrics.get("policy_stage")
    if isinstance(stage, str) and stage.strip():
        return stage.strip()
    if scorecard is not None:
        stage = scorecard.get("policy_stage")
        if isinstance(stage, str) and stage.strip():
            return stage.strip()
    raise PolicyStageNotFoundError()


def _resolve_hook_strategy(publish: dict[str, Any]) -> str:
    metadata = publish.get("metadata")
    if isinstance(metadata, dict):
        strategy = metadata.get("hook_strategy")
        if isinstance(strategy, str) and strategy.strip():
            return strategy.strip()
        creative_pack = metadata.get("creative_pack")
        if isinstance(creative_pack, dict):
            strategy = creative_pack.get("strategy_used")
            if isinstance(strategy, str) and strategy.strip():
                return strategy.strip()
    return "UNKNOWN_HOOK_STRATEGY"


def _resolve_duration_field(publish: dict[str, Any], field_name: str) -> int | None:
    metadata = publish.get("metadata")
    if not isinstance(metadata, dict):
        return None
    value = metadata.get(field_name)
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


def build_attribution(publish_id: str, deps: AttributionDeps) -> dict[str, Any]:
    """Constrói 1 content attribution por publish_id sem efeitos colaterais."""
    publish = _must_call(deps.publish_records_repo, ("get_by_publish_id",), publish_id)
    if not isinstance(publish, dict):
        raise PublishRecordNotFoundError()

    account_id = str(publish.get("account_id") or "")
    video_id = str(publish.get("video_id") or "")
    job_id = str(publish.get("job_id") or "")
    if not account_id or not video_id or not job_id:
        raise PublishRecordNotFoundError("PUBLISH_RECORD_NOT_FOUND")

    publish_window_id = publish.get("window_id")
    metrics: dict[str, Any] | None = None
    if isinstance(publish_window_id, str) and publish_window_id.strip():
        metrics = _call_optional(
            deps.video_metrics_repo,
            ("get_best",),
            account_id,
            video_id,
            publish_window_id.strip(),
        )
    if metrics is None:
        metrics = _call_optional(
            deps.video_metrics_repo,
            ("get_latest_for_video",),
            account_id,
            video_id,
        )
    if not isinstance(metrics, dict):
        raise AttributionMetricsMissingError()

    window_id = publish_window_id if isinstance(publish_window_id, str) and publish_window_id.strip() else None
    if window_id is None:
        raw_window = metrics.get("captured_window_id")
        if isinstance(raw_window, str) and raw_window.strip():
            window_id = raw_window.strip()
    if not window_id:
        raise AttributionWindowMissingError()

    window_metrics = _call_optional(
        deps.window_metrics_repo,
        ("get_by_key", "get"),
        account_id,
        window_id,
    )
    if not isinstance(window_metrics, dict):
        raise AttributionWindowMissingError("WINDOW_METRICS_NOT_FOUND")

    scorecard = None
    if deps.scorecard_repo is not None:
        scorecard = _call_optional(deps.scorecard_repo, ("get_by_key", "get"), account_id, window_id)

    policy_stage = _resolve_policy_stage(publish=publish, window_metrics=window_metrics, scorecard=scorecard)

    publish_mode = str(publish.get("publish_mode") or "").strip().lower()
    explicit_patch = bool(publish.get("human_patch_detected"))
    human_patch_detected = explicit_patch or publish_mode != "auto"

    dominant_failure_reason = None
    if isinstance(scorecard, dict):
        value = scorecard.get("dominant_failure_reason")
        if isinstance(value, str) and value.strip():
            dominant_failure_reason = value.strip()
    if dominant_failure_reason is None:
        value = window_metrics.get("dominant_failure_reason")
        if isinstance(value, str) and value.strip():
            dominant_failure_reason = value.strip()

    candidate = {
        "attribution_id": f"attr_{publish_id}",
        "account_id": account_id,
        "publish_id": publish_id,
        "video_id": video_id,
        "job_id": job_id,
        "window_id": window_id,
        "policy_stage": policy_stage,
        "hook_strategy": _resolve_hook_strategy(publish),
        "dominant_failure_reason": dominant_failure_reason,
        "effective_duration_s": _resolve_duration_field(publish, "effective_duration_s"),
        "rare_fact_placement_s": _resolve_duration_field(publish, "rare_fact_placement_s"),
        "human_patch_detected": human_patch_detected,
        "views": metrics.get("views"),
        "retention_3s": metrics.get("retention_3s"),
        "completion_rate": metrics.get("completion_rate"),
        "likes": metrics.get("likes"),
        "follows": metrics.get("follows"),
        "rpm": metrics.get("rpm"),
        "captured_at": metrics.get("captured_at"),
        "generated_at": _now_utc_iso(),
    }
    return validate_content_attribution(candidate)

