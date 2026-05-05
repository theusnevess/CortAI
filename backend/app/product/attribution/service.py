from __future__ import annotations

from pathlib import Path
from typing import Any

from app.product.attribution.builder import (
    AttributionDeps,
    build_attribution,
    build_evidence_summary,
    build_experiment_linkage,
)
from app.product.attribution.errors import (
    AttributionBuildError,
    AttributionMetricsMissingError,
    AttributionWindowMissingError,
    PolicyStageNotFoundError,
    PublishRecordNotFoundError,
)
from app.product.attribution.repo import save_if_absent


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


def generate_and_save_attribution(
    *,
    publish_id: str,
    deps: AttributionDeps,
    path: Path | None = None,
) -> dict[str, Any]:
    """Canonical write-path wrapper for content attribution.

    Phase B/C intent:
    - keep the canonical record stable
    - make evidence presence explicit
    - return honest status/reason codes on missing required evidence
    - link experiment context only when explicit metadata exists
    """
    publish = None
    metrics = None
    window_metrics = None
    scorecard = None
    experiment_assignment = None
    experiment_result = None
    experiment_linkage_status = "NOT_PRESENT"
    experiment_context = None
    experiment_result_available = False

    try:
        publish = deps.publish_records_repo.get_by_publish_id(publish_id)
        if not isinstance(publish, dict):
            raise PublishRecordNotFoundError()

        account_id = str(publish.get("account_id") or "")
        video_id = str(publish.get("video_id") or "")
        if not account_id or not video_id:
            raise PublishRecordNotFoundError()

        publish_window_id = publish.get("window_id")
        if isinstance(publish_window_id, str) and publish_window_id.strip():
            metrics = _call_optional(deps.video_metrics_repo, ("get_best",), account_id, video_id, publish_window_id.strip())
        if metrics is None:
            metrics = _call_optional(deps.video_metrics_repo, ("get_latest_for_video",), account_id, video_id)
        if not isinstance(metrics, dict):
            raise AttributionMetricsMissingError()

        window_id = publish_window_id if isinstance(publish_window_id, str) and publish_window_id.strip() else None
        if window_id is None:
            raw_window = metrics.get("captured_window_id")
            if isinstance(raw_window, str) and raw_window.strip():
                window_id = raw_window.strip()
        if not window_id:
            raise AttributionWindowMissingError()

        window_metrics = _call_optional(deps.window_metrics_repo, ("get_by_key", "get"), account_id, window_id)
        if not isinstance(window_metrics, dict):
            raise AttributionWindowMissingError("WINDOW_METRICS_NOT_FOUND")

        if deps.scorecard_repo is not None:
            scorecard = _call_optional(deps.scorecard_repo, ("get_by_key", "get"), account_id, window_id)

        experiment_linkage = build_experiment_linkage(publish=publish, deps=deps)
        experiment_linkage_status = str(experiment_linkage.get("experiment_linkage_status") or "NOT_PRESENT")
        experiment_context = experiment_linkage.get("experiment_context")
        experiment_result_available = bool(experiment_linkage.get("experiment_result_available"))

        if isinstance(experiment_context, dict):
            assignment_id = str(experiment_context.get("assignment_id") or "")
            result_id = str(experiment_context.get("result_id") or "")
            experiment_assignment = _lookup_repo_record_by_id(
                deps.experiment_assignments_repo,
                direct_methods=("get_by_assignment_id",),
                key_field="assignment_id",
                value=assignment_id,
            )
            experiment_result = _lookup_repo_record_by_id(
                deps.experiment_results_repo,
                direct_methods=("get_by_result_id",),
                key_field="result_id",
                value=result_id,
            )

        record = build_attribution(publish_id, deps)
        write_action = save_if_absent(record, path=path)
        return {
            "status": write_action,
            "reason_code": "ATTRIBUTION_OK",
            "record_written": write_action == "WRITTEN",
            "attribution": record,
            "experiment_linkage_status": experiment_linkage_status,
            "experiment_context": experiment_context,
            "experiment_result_available": experiment_result_available,
            "evidence_summary": build_evidence_summary(
                publish_present=True,
                metrics_present=True,
                window_metrics_present=True,
                scorecard_present=isinstance(scorecard, dict),
                experiment_assignment_present=isinstance(experiment_assignment, dict),
                experiment_result_present=isinstance(experiment_result, dict),
            ),
        }
    except (PublishRecordNotFoundError, AttributionMetricsMissingError, AttributionWindowMissingError, PolicyStageNotFoundError) as exc:
        if isinstance(publish, dict):
            experiment_linkage = build_experiment_linkage(publish=publish, deps=deps)
            experiment_linkage_status = str(experiment_linkage.get("experiment_linkage_status") or "NOT_PRESENT")
            experiment_context = experiment_linkage.get("experiment_context")
            experiment_result_available = bool(experiment_linkage.get("experiment_result_available"))
        return {
            "status": "SKIPPED",
            "reason_code": str(exc),
            "record_written": False,
            "attribution": None,
            "experiment_linkage_status": experiment_linkage_status,
            "experiment_context": experiment_context,
            "experiment_result_available": experiment_result_available,
            "evidence_summary": build_evidence_summary(
                publish_present=isinstance(publish, dict),
                metrics_present=isinstance(metrics, dict),
                window_metrics_present=isinstance(window_metrics, dict),
                scorecard_present=isinstance(scorecard, dict),
                experiment_assignment_present=isinstance(experiment_assignment, dict),
                experiment_result_present=isinstance(experiment_result, dict),
            ),
        }
    except AttributionBuildError as exc:
        if isinstance(publish, dict):
            experiment_linkage = build_experiment_linkage(publish=publish, deps=deps)
            experiment_linkage_status = str(experiment_linkage.get("experiment_linkage_status") or "NOT_PRESENT")
            experiment_context = experiment_linkage.get("experiment_context")
            experiment_result_available = bool(experiment_linkage.get("experiment_result_available"))
        return {
            "status": "ERROR",
            "reason_code": str(exc),
            "record_written": False,
            "attribution": None,
            "experiment_linkage_status": experiment_linkage_status,
            "experiment_context": experiment_context,
            "experiment_result_available": experiment_result_available,
            "evidence_summary": build_evidence_summary(
                publish_present=isinstance(publish, dict),
                metrics_present=isinstance(metrics, dict),
                window_metrics_present=isinstance(window_metrics, dict),
                scorecard_present=isinstance(scorecard, dict),
                experiment_assignment_present=isinstance(experiment_assignment, dict),
                experiment_result_present=isinstance(experiment_result, dict),
            ),
        }
