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

REQUIRED_EVIDENCE_INPUTS = (
    "publish_record",
    "video_metrics",
    "window_metrics",
)

OPTIONAL_EVIDENCE_INPUTS = (
    "scorecard",
    "experiment_assignment_record",
    "experiment_result_record",
)

EXPERIMENT_LINKAGE_STATUS = {
    "LINKED",
    "NOT_PRESENT",
    "MISSING_ASSIGNMENT",
    "MISSING_RESULT",
    "UNSAFE_TO_INFER",
}


@dataclass(frozen=True)
class AttributionDeps:
    """Dependencias de leitura usadas pelo builder de attribution."""

    publish_records_repo: Any
    video_metrics_repo: Any
    window_metrics_repo: Any
    scorecard_repo: Any | None = None
    experiment_assignments_repo: Any | None = None
    experiment_results_repo: Any | None = None


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _call_optional(repo: Any, method_names: tuple[str, ...], *args: Any) -> Any:
    if repo is None:
        return None
    for name in method_names:
        method = getattr(repo, name, None)
        if callable(method):
            return method(*args)
    return None


def _lookup_repo_record_by_id(repo: Any, *, direct_methods: tuple[str, ...], key_field: str, value: str) -> Any:
    if repo is None or not value:
        return None
    for name in direct_methods:
        method = getattr(repo, name, None)
        if callable(method):
            return method(value)
    method = getattr(repo, "get_by_key", None)
    if callable(method):
        return method(key_field, value)
    method = getattr(repo, "get", None)
    if callable(method):
        return method(value)
    return None


def _must_call(repo: Any, method_names: tuple[str, ...], *args: Any) -> Any:
    for name in method_names:
        method = getattr(repo, name, None)
        if callable(method):
            return method(*args)
    raise AttributionBuildError(f"DEPENDENCY_METHOD_MISSING: expected one of {method_names}")


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


def build_evidence_summary(
    *,
    publish_present: bool,
    metrics_present: bool,
    window_metrics_present: bool,
    scorecard_present: bool,
    experiment_assignment_present: bool = False,
    experiment_result_present: bool = False,
) -> dict[str, Any]:
    required_present = {
        "publish_record": bool(publish_present),
        "video_metrics": bool(metrics_present),
        "window_metrics": bool(window_metrics_present),
    }
    optional_present = {
        "scorecard": bool(scorecard_present),
        "experiment_assignment_record": bool(experiment_assignment_present),
        "experiment_result_record": bool(experiment_result_present),
    }
    required_complete = all(required_present.values())
    evidence_mode = "WITH_OPTIONAL_SCORECARD" if required_complete and optional_present["scorecard"] else "REQUIRED_ONLY"
    if not required_complete:
        evidence_mode = "INCOMPLETE_REQUIRED_EVIDENCE"
    return {
        "required_inputs": list(REQUIRED_EVIDENCE_INPUTS),
        "optional_inputs": list(OPTIONAL_EVIDENCE_INPUTS),
        "required_present": required_present,
        "optional_present": optional_present,
        "required_evidence_complete": required_complete,
        "evidence_mode": evidence_mode,
    }


def build_experiment_linkage(
    *,
    publish: dict[str, Any],
    deps: AttributionDeps,
) -> dict[str, Any]:
    metadata = publish.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    explicit_assignment_id = str(metadata.get("experiment_assignment_id") or "").strip()
    explicit_result_id = str(metadata.get("experiment_result_id") or "").strip()
    explicit_experiment_id = str(metadata.get("experiment_id") or "").strip()
    explicit_variant_id = str(metadata.get("experiment_variant_id") or metadata.get("variant_id") or "").strip()
    explicit_subject_key = str(metadata.get("experiment_subject_key") or "").strip()
    creative_pack_id = str(metadata.get("creative_pack_id") or "").strip()

    assignment = None
    result = None

    if not any((explicit_assignment_id, explicit_result_id, explicit_experiment_id, explicit_variant_id, explicit_subject_key)):
        status = "UNSAFE_TO_INFER" if creative_pack_id else "NOT_PRESENT"
        return {
            "experiment_linkage_status": status,
            "experiment_context": None,
            "experiment_result_available": False,
        }

    if explicit_assignment_id:
        assignment = _lookup_repo_record_by_id(
            deps.experiment_assignments_repo,
            direct_methods=("get_by_assignment_id",),
            key_field="assignment_id",
            value=explicit_assignment_id,
        )
        if deps.experiment_assignments_repo is not None and not isinstance(assignment, dict):
            return {
                "experiment_linkage_status": "MISSING_ASSIGNMENT",
                "experiment_context": {
                    "assignment_id": explicit_assignment_id,
                    "experiment_id": explicit_experiment_id or None,
                    "variant_id": explicit_variant_id or None,
                    "subject_key": explicit_subject_key or None,
                    "result_id": explicit_result_id or None,
                },
                "experiment_result_available": False,
            }

    if explicit_result_id:
        result = _lookup_repo_record_by_id(
            deps.experiment_results_repo,
            direct_methods=("get_by_result_id",),
            key_field="result_id",
            value=explicit_result_id,
        )
        if deps.experiment_results_repo is not None and not isinstance(result, dict):
            return {
                "experiment_linkage_status": "MISSING_RESULT",
                "experiment_context": {
                    "assignment_id": explicit_assignment_id or (None if not isinstance(assignment, dict) else str(assignment.get("assignment_id") or "") or None),
                    "experiment_id": explicit_experiment_id or (None if not isinstance(assignment, dict) else str(assignment.get("experiment_id") or "") or None),
                    "variant_id": explicit_variant_id or (None if not isinstance(assignment, dict) else str(assignment.get("variant") or "") or None),
                    "subject_key": explicit_subject_key or (None if not isinstance(assignment, dict) else str(assignment.get("subject_key") or "") or None),
                    "result_id": explicit_result_id,
                },
                "experiment_result_available": False,
            }

    experiment_context = {
        "assignment_id": explicit_assignment_id or (None if not isinstance(assignment, dict) else str(assignment.get("assignment_id") or "") or None),
        "experiment_id": explicit_experiment_id
        or (None if not isinstance(assignment, dict) else str(assignment.get("experiment_id") or "") or None)
        or (None if not isinstance(result, dict) else str(result.get("experiment_id") or "") or None),
        "variant_id": explicit_variant_id
        or (None if not isinstance(assignment, dict) else str(assignment.get("variant") or "") or None)
        or (None if not isinstance(result, dict) else str(result.get("variant") or "") or None),
        "subject_key": explicit_subject_key
        or (None if not isinstance(assignment, dict) else str(assignment.get("subject_key") or "") or None)
        or (None if not isinstance(result, dict) else str(result.get("subject_key") or "") or None),
        "result_id": explicit_result_id or (None if not isinstance(result, dict) else str(result.get("result_id") or "") or None),
    }
    if not any(experiment_context.values()):
        return {
            "experiment_linkage_status": "NOT_PRESENT",
            "experiment_context": None,
            "experiment_result_available": False,
        }

    return {
        "experiment_linkage_status": "LINKED",
        "experiment_context": experiment_context,
        "experiment_result_available": isinstance(result, dict),
    }


def build_attribution(publish_id: str, deps: AttributionDeps) -> dict[str, Any]:
    """Constroi 1 content attribution por publish_id sem efeitos colaterais."""
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
