from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from app.data.video_metrics.repo import get_best, list_for_window
from app.data.window_metrics.repo import get_by_key
from app.data.window_metrics.selector import select_window_video_ids
from app.guard.data_consistency.check_catalog_v1 import CHECK_CATALOG_V1
from app.guard.data_consistency.errors import ConsistencyDependencyMissing
from app.guard.data_consistency.models import GuardResult, Violation

JobSpecExistsFn = Callable[[str], bool]


def _mk_violation(
    check_id: str,
    *,
    status: str,
    details: dict[str, Any],
) -> Violation:
    catalog = CHECK_CATALOG_V1[check_id]
    return Violation(
        check_id=check_id,
        reason_code=catalog["reason_code"],
        severity=catalog["severity"],
        action=catalog["action"],
        status=status,
        details=details,
    )


def _window_bounds_from_window_id(window_id: str) -> tuple[str, str]:
    if not isinstance(window_id, str) or not window_id.startswith("w_"):
        raise ValueError("ContractViolation: invalid window_id")
    payload = window_id[2:]
    parts = payload.split("_", 1)
    if len(parts) != 2:
        raise ValueError("ContractViolation: invalid window_id")
    return parts[0], parts[1]


def run_data_consistency_guard(
    account_id: str,
    window_id: str,
    deps: dict[str, Any],
) -> GuardResult:
    """Executa checks de consistencia da janela sem efeitos colaterais."""
    publish_path = deps.get("publish_records_path")
    video_metrics_path = deps.get("video_metrics_path")
    window_metrics_path = deps.get("window_metrics_path")

    if publish_path is None or video_metrics_path is None or window_metrics_path is None:
        raise ConsistencyDependencyMissing()

    publish_path = Path(publish_path)
    video_metrics_path = Path(video_metrics_path)
    window_metrics_path = Path(window_metrics_path)

    start, end = _window_bounds_from_window_id(window_id)
    publish_video_ids = select_window_video_ids(
        account_id=account_id,
        window_start=start,
        window_end=end,
        path=publish_path,
    )
    publish_video_set = set(publish_video_ids)

    best_metrics = list_for_window(account_id, window_id, path=video_metrics_path)
    metrics_video_set = {str(item["video_id"]) for item in best_metrics}

    violations: list[Violation] = []

    # VCG_001: todo video em metrics precisa existir em publish_records da janela.
    orphan_metrics = sorted(metrics_video_set - publish_video_set)
    if orphan_metrics:
        violations.append(
            _mk_violation(
                "VCG_001",
                status="FAILED",
                details={"orphan_video_ids": orphan_metrics},
            )
        )

    # VCG_002: job_id deve existir em job_specs quando repositorio existir.
    job_specs_exists_fn = deps.get("job_specs_exists")
    if job_specs_exists_fn is None:
        violations.append(
            _mk_violation(
                "VCG_002",
                status="SKIPPED_NOT_AVAILABLE",
                details={"dependency": "job_specs_exists"},
            )
        )
    else:
        from app.data.publish_records.store_jsonl import read_all_records

        records = read_all_records(publish_path)
        missing_job_ids: list[str] = []
        for record in records:
            if record.get("account_id") != account_id or record.get("status") != "posted":
                continue
            job_id = record.get("job_id")
            if not isinstance(job_id, str) or not job_id:
                continue
            if not job_specs_exists_fn(job_id):
                missing_job_ids.append(job_id)
        if missing_job_ids:
            violations.append(
                _mk_violation(
                    "VCG_002",
                    status="FAILED",
                    details={"missing_job_ids": sorted(set(missing_job_ids))},
                )
            )

    window_metrics = get_by_key(account_id, window_id, path=window_metrics_path)
    if window_metrics is None:
        raise ConsistencyDependencyMissing("CONSISTENCY_DEPENDENCY_MISSING: window_metrics not found")

    # VCG_003: videos_considered precisa refletir o total de publishes na janela.
    expected_considered = len(publish_video_ids)
    current_considered = int(window_metrics.get("videos_considered", -1))
    if current_considered != expected_considered:
        violations.append(
            _mk_violation(
                "VCG_003",
                status="FAILED",
                details={
                    "expected_videos_considered": expected_considered,
                    "actual_videos_considered": current_considered,
                },
            )
        )

    # VCG_004: contabilizacao de missing deve fechar quando campos derivados existirem.
    videos_with_metrics = sum(
        1 for video_id in publish_video_ids if get_best(account_id, video_id, window_id, path=video_metrics_path)
    )
    videos_missing_metrics = expected_considered - videos_with_metrics
    derived_with = window_metrics.get("videos_with_metrics")
    derived_missing = window_metrics.get("videos_missing_metrics")
    if derived_with is not None or derived_missing is not None:
        actual_with = int(derived_with or 0)
        actual_missing = int(derived_missing or 0)
        if actual_with + actual_missing != current_considered:
            violations.append(
                _mk_violation(
                    "VCG_004",
                    status="FAILED",
                    details={
                        "videos_with_metrics": actual_with,
                        "videos_missing_metrics": actual_missing,
                        "videos_considered": current_considered,
                    },
                )
            )

    # VCG_005: check opcional quando ids cruzados forem fornecidos.
    scorecard_window_id = deps.get("scorecard_window_id")
    attribution_window_id = deps.get("attribution_window_id")
    if scorecard_window_id is not None and attribution_window_id is not None:
        if scorecard_window_id != attribution_window_id or scorecard_window_id != window_id:
            violations.append(
                _mk_violation(
                    "VCG_005",
                    status="FAILED",
                    details={
                        "scorecard_window_id": scorecard_window_id,
                        "attribution_window_id": attribution_window_id,
                        "expected_window_id": window_id,
                    },
                )
            )

    blocked_violations = [item for item in violations if item.action == "BLOCK" and item.status == "FAILED"]
    if blocked_violations:
        return GuardResult(
            ok=False,
            blocked=True,
            reason_code="CONSISTENCY_VIOLATION_BLOCKED",
            violations=violations,
        )

    return GuardResult(
        ok=True,
        blocked=False,
        reason_code="CONSISTENCY_OK",
        violations=violations,
    )

