from __future__ import annotations

from pathlib import Path

from app.analysis.consistency.models import ConsistencyCheckResult, ConsistencySummary


def check_publish_record_has_video_metrics(
    publish_records: list[dict],
    video_metrics: list[dict],
) -> ConsistencyCheckResult:
    publish_ids = {str(item.get("publish_id") or "") for item in publish_records if item.get("publish_id")}
    metric_publish_ids = {str(item.get("publish_id") or "") for item in video_metrics if item.get("publish_id")}
    matched = publish_ids & metric_publish_ids
    missing = publish_ids - metric_publish_ids
    return ConsistencyCheckResult(
        check_id="publish_record_has_video_metrics",
        status="OK" if not missing else "FAIL",
        expected=len(publish_ids),
        found=len(matched),
        missing_count=len(missing),
        details=None if not missing else f"missing metrics for publish_ids: {sorted(missing)}",
    )


def check_video_metrics_reference_publish_record(
    publish_records: list[dict],
    video_metrics: list[dict],
) -> ConsistencyCheckResult:
    publish_ids = {str(item.get("publish_id") or "") for item in publish_records if item.get("publish_id")}
    metric_publish_ids = {str(item.get("publish_id") or "") for item in video_metrics if item.get("publish_id")}
    orphans = metric_publish_ids - publish_ids
    return ConsistencyCheckResult(
        check_id="video_metrics_reference_publish_record",
        status="OK" if not orphans else "FAIL",
        expected=len(metric_publish_ids),
        found=len(metric_publish_ids - orphans),
        missing_count=len(orphans),
        details=None if not orphans else f"orphan metric publish_ids: {sorted(orphans)}",
    )


def check_assignment_references_experiment(
    experiments: list[dict],
    assignments: list[dict],
) -> ConsistencyCheckResult:
    experiment_ids = {str(item.get("experiment_id") or "") for item in experiments if item.get("experiment_id")}
    assignment_experiment_ids = {
        str(item.get("experiment_id") or "") for item in assignments if item.get("experiment_id")
    }
    missing = assignment_experiment_ids - experiment_ids
    return ConsistencyCheckResult(
        check_id="experiment_assignment_references_experiment",
        status="OK" if not missing else "FAIL",
        expected=len(assignment_experiment_ids),
        found=len(assignment_experiment_ids - missing),
        missing_count=len(missing),
        details=None if not missing else f"orphan assignment experiment_ids: {sorted(missing)}",
    )


def check_result_references_assignment(
    assignments: list[dict],
    results: list[dict],
) -> ConsistencyCheckResult:
    assignment_ids = {str(item.get("assignment_id") or "") for item in assignments if item.get("assignment_id")}
    result_assignment_ids = {
        str(item.get("assignment_id") or "") for item in results if item.get("assignment_id")
    }
    missing = result_assignment_ids - assignment_ids
    return ConsistencyCheckResult(
        check_id="experiment_result_references_assignment",
        status="OK" if not missing else "FAIL",
        expected=len(result_assignment_ids),
        found=len(result_assignment_ids - missing),
        missing_count=len(missing),
        details=None if not missing else f"orphan result assignment_ids: {sorted(missing)}",
    )


def check_publish_metadata_creative_pack_exists(
    publish_records: list[dict],
    creative_packs: list[dict],
) -> ConsistencyCheckResult:
    creative_pack_ids = {
        str(item.get("creative_pack_id") or "") for item in creative_packs if item.get("creative_pack_id")
    }
    referenced_ids: set[str] = set()
    for record in publish_records:
        metadata = record.get("metadata")
        if isinstance(metadata, dict):
            creative_pack_id = metadata.get("creative_pack_id")
            if creative_pack_id:
                referenced_ids.add(str(creative_pack_id))
    missing = referenced_ids - creative_pack_ids
    return ConsistencyCheckResult(
        check_id="publish_record_metadata_creative_pack_exists",
        status="OK" if not missing else "FAIL",
        expected=len(referenced_ids),
        found=len(referenced_ids - missing),
        missing_count=len(missing),
        details=None if not missing else f"missing creative_pack_ids: {sorted(missing)}",
    )


def check_analysis_outputs_derivable_from_inputs(
    *,
    analysis_dir: Path,
    publish_records: list[dict],
    video_metrics: list[dict],
    experiments: list[dict],
    assignments: list[dict],
    hook_performance: list[dict],
    safety_events: list[dict],
    account_health: list[dict],
    risk_profiles: list[dict],
) -> ConsistencyCheckResult:
    requirements = {
        "pilot_metrics_summary.json": bool(publish_records) and bool(video_metrics),
        "experiment_winners.json": bool(experiments) and bool(assignments) and bool(video_metrics),
        "hook_performance_summary.json": bool(hook_performance),
        "account_health_summary.json": bool(safety_events) or bool(account_health) or bool(risk_profiles),
    }
    existing_outputs = [name for name in requirements if (analysis_dir / name).exists()]
    failed_outputs = [name for name in existing_outputs if not requirements[name]]
    return ConsistencyCheckResult(
        check_id="analysis_outputs_derivable_from_inputs",
        status="OK" if not failed_outputs else "FAIL",
        expected=len(existing_outputs),
        found=len(existing_outputs) - len(failed_outputs),
        missing_count=len(failed_outputs),
        details=None if not failed_outputs else f"outputs without minimal inputs: {sorted(failed_outputs)}",
    )


def run_consistency_checks(
    *,
    generated_at: str,
    analysis_dir: Path,
    publish_records: list[dict],
    video_metrics: list[dict],
    experiments: list[dict],
    assignments: list[dict],
    results: list[dict],
    creative_packs: list[dict],
    hook_performance: list[dict],
    safety_events: list[dict],
    account_health: list[dict],
    risk_profiles: list[dict],
) -> ConsistencySummary:
    checks = [
        check_publish_record_has_video_metrics(publish_records, video_metrics),
        check_video_metrics_reference_publish_record(publish_records, video_metrics),
        check_assignment_references_experiment(experiments, assignments),
        check_result_references_assignment(assignments, results),
        check_publish_metadata_creative_pack_exists(publish_records, creative_packs),
        check_analysis_outputs_derivable_from_inputs(
            analysis_dir=analysis_dir,
            publish_records=publish_records,
            video_metrics=video_metrics,
            experiments=experiments,
            assignments=assignments,
            hook_performance=hook_performance,
            safety_events=safety_events,
            account_health=account_health,
            risk_profiles=risk_profiles,
        ),
    ]
    checks_failed = sum(1 for item in checks if item.status == "FAIL")
    return ConsistencySummary(
        status="FAIL" if checks_failed else "OK",
        generated_at=generated_at,
        checks_run=len(checks),
        checks_failed=checks_failed,
        checks=checks,
    )

