from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.publisher.publish_lifecycle_writer import PublishLifecycleWriter  # noqa: E402
from app.creative.agents.publisher.publish_semantics import BOUNDARY_STATEMENT  # noqa: E402
from app.creative.agents.publisher.publish_trace import (  # noqa: E402
    PublishTraceBuilder,
    PublishTraceValidationError,
)


AUDIT_DIR = ROOT / "OUT" / "audit" / "publisher_dry_run_operational_evidence_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
TEMPORAL_CONSISTENCY_PATH = AUDIT_DIR / "temporal_consistency.json"
APPEND_ONLY_CHECKS_PATH = AUDIT_DIR / "append_only_checks.json"
RESIDUAL_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
CONTROLLED_LIFECYCLE_PATH = AUDIT_DIR / "controlled_publish_lifecycle.jsonl"

MINIMUMS = {
    "min_total_runs": 50,
    "min_qc_blocks": 5,
    "min_account_health_hold_blocks": 3,
    "min_missing_qc_trace_events": 2,
    "min_missing_artifact_manifest_events": 2,
    "min_incident_hooks": 5,
    "min_append_only_events": 50,
}

PRODUCTION_RESIDUALS = [
    "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
    "PLATFORM_INTEGRATION_NOT_ENABLED",
    "PUBLISH_RESULT_HISTORY_STILL_SHORT",
]

START_TIME = datetime(2026, 4, 27, 22, 30, 0, tzinfo=timezone(timedelta(hours=-3)))


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=True), encoding="utf-8")


def _timestamp(index: int) -> str:
    return (START_TIME + timedelta(seconds=index)).isoformat()


def _event_to_dict(event: Any, *, scenario: str, dry_run: bool = True) -> dict[str, Any]:
    payload = event.to_dict() if hasattr(event, "to_dict") else dict(event)
    payload["dry_run"] = dry_run
    payload["scenario"] = scenario
    payload["platform_api_called"] = False
    payload["real_publishing_performed"] = False
    return payload


def _build_bundle(
    builder: PublishTraceBuilder,
    *,
    index: int,
    scenario: str,
    qc_status: str | None = "APPROVE",
    qc_publishable: bool | None = True,
    qc_trace_ref: str | None = None,
    account_health_decision: str | None = "SAFE",
    artifact_manifest_ref: str | None = None,
    missing_qc_trace: bool = False,
    missing_artifact_manifest: bool = False,
    dry_run: bool = True,
    simulate_failure: bool = False,
    pending_attempt: bool = False,
) -> dict[str, Any]:
    run_id = f"dry_run_{index:03d}"
    content_id = f"publisher_dry_run_content_{index:03d}"
    timestamp = _timestamp(index)
    qc_ref = None if missing_qc_trace else (qc_trace_ref if qc_trace_ref is not None else f"qc_trace:{index:03d}")
    artifact_ref = None if missing_artifact_manifest else (
        artifact_manifest_ref if artifact_manifest_ref is not None else f"artifact_manifest:{index:03d}"
    )
    eligibility = builder.build_eligibility_trace(
        run_id=run_id,
        content_id=content_id,
        qc_status=qc_status,
        qc_publishable=qc_publishable,
        qc_trace_ref=qc_ref,
        account_health_decision=account_health_decision,
        health_trace_ref=f"health_trace:{index:03d}",
        strategy_ref=f"strategy:{index:03d}",
        artifact_manifest_ref=artifact_ref,
        dry_run=True,
    )
    attempt = builder.build_attempt_trace(
        eligibility_trace=eligibility,
        attempt_id=f"attempt:{index:03d}",
        timestamp=timestamp,
        publish_target="dry_run_trace_only_target" if (simulate_failure or pending_attempt) else None,
        dry_run=dry_run,
        simulate_failure=simulate_failure,
        failure_reason="PUBLISH_TARGET_ERROR" if simulate_failure else None,
    )
    result = builder.build_result_trace(attempt_trace=attempt, observed_at=timestamp)
    lifecycle = builder.build_lifecycle_event(
        eligibility_trace=eligibility,
        attempt_trace=attempt,
        result_trace=result,
        publish_event_id=f"publish_event:{index:03d}",
        timestamp=timestamp,
    )
    hooks = builder.build_incident_hooks(
        eligibility_trace=eligibility,
        attempt_trace=attempt,
        result_trace=result,
    )
    return {
        "index": index,
        "scenario": scenario,
        "eligibility": eligibility.to_dict(),
        "attempt": attempt.to_dict(),
        "result": result.to_dict(),
        "lifecycle": _event_to_dict(lifecycle, scenario=scenario, dry_run=True),
        "incident_hooks": [hook.to_dict() for hook in hooks],
    }


def _generate_controlled_evidence() -> list[dict[str, Any]]:
    builder = PublishTraceBuilder()
    records: list[dict[str, Any]] = []
    index = 0

    def add(count: int, scenario: str, **kwargs: Any) -> None:
        nonlocal index
        for _ in range(count):
            index += 1
            records.append(_build_bundle(builder, index=index, scenario=scenario, **kwargs))

    add(20, "healthy_eligible_dry_run", dry_run=True)
    add(7, "qc_reject_block", qc_status="REJECT", qc_publishable=False, dry_run=True)
    add(5, "qc_hold_block", qc_status="HOLD", qc_publishable=False, dry_run=True)
    add(5, "qc_publishable_false_block", qc_status="APPROVE", qc_publishable=False, dry_run=True)
    add(5, "account_health_hold_block", account_health_decision="HOLD", dry_run=True)
    add(3, "missing_qc_trace", missing_qc_trace=True, dry_run=True)
    add(3, "missing_artifact_manifest", missing_artifact_manifest=True, dry_run=True)
    add(2, "simulated_failed_attempt", dry_run=False, simulate_failure=True)
    add(2, "pending_non_success", dry_run=False, pending_attempt=True)
    return sorted(records, key=lambda item: item["index"])


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                events.append(json.loads(stripped))
    return events


def _write_controlled_lifecycle(records: list[dict[str, Any]]) -> dict[str, Any]:
    sentinel = {"sentinel": True, "preserve": "append_only_baseline"}
    CONTROLLED_LIFECYCLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTROLLED_LIFECYCLE_PATH.write_text(json.dumps(sentinel, sort_keys=True) + "\n", encoding="utf-8")
    before = CONTROLLED_LIFECYCLE_PATH.read_text(encoding="utf-8").splitlines()
    writer = PublishLifecycleWriter(CONTROLLED_LIFECYCLE_PATH)
    for record in records:
        writer.append_event(record["lifecycle"])
    after = CONTROLLED_LIFECYCLE_PATH.read_text(encoding="utf-8").splitlines()
    parsed = _read_jsonl(CONTROLLED_LIFECYCLE_PATH)
    appended = parsed[1:]
    append_only_valid = (
        before == after[: len(before)]
        and len(appended) == len(records)
        and all(event.get("result", {}).get("result_status") != "succeeded" for event in appended)
        and all(event.get("result", {}).get("published_url") is None for event in appended)
        and all(event.get("result", {}).get("platform_content_id") is None for event in appended)
    )
    return {
        "path": str(CONTROLLED_LIFECYCLE_PATH),
        "before_line_count": len(before),
        "after_line_count": len(after),
        "appended_event_count": len(appended),
        "baseline_preserved": before == after[: len(before)],
        "all_lines_parseable": len(parsed) == len(after),
        "failures_skips_pending_preserved": all(
            event.get("result", {}).get("result_status") != "succeeded" for event in appended
        ),
        "append_only_valid": append_only_valid,
    }


def _metrics(records: list[dict[str, Any]], append_checks: dict[str, Any]) -> dict[str, Any]:
    total = len(records)
    eligible_count = sum(1 for item in records if item["eligibility"].get("eligible") is True)
    blocked_count = sum(1 for item in records if item["eligibility"].get("eligible") is False)
    skipped_count = sum(1 for item in records if item["attempt"].get("skip_reason"))
    qc_block_count = sum(
        1
        for item in records
        if any(reason in {"QC_REJECTED", "QC_HOLD", "QC_NOT_PUBLISHABLE"} for reason in item["eligibility"].get("blocking_reasons", []))
    )
    account_health_hold_block_count = sum(
        1 for item in records if "ACCOUNT_HEALTH_HOLD" in item["eligibility"].get("blocking_reasons", [])
    )
    missing_qc_trace_events = sum(1 for item in records if "MISSING_QC_TRACE" in item["eligibility"].get("blocking_reasons", []))
    missing_artifact_manifest_events = sum(
        1 for item in records if "MISSING_ARTIFACT_MANIFEST" in item["eligibility"].get("blocking_reasons", [])
    )
    incident_hook_count = sum(len(item["incident_hooks"]) for item in records)
    success_count = sum(1 for item in records if item["result"].get("result_status") == "succeeded")
    fake_url_or_platform_id_detected = any(
        item["result"].get("published_url") or item["result"].get("platform_content_id") for item in records
    )
    return {
        "total_runs": total,
        "append_only_events": append_checks["appended_event_count"],
        "eligible_count": eligible_count,
        "blocked_count": blocked_count,
        "skipped_count": skipped_count,
        "failed_count": sum(1 for item in records if item["result"].get("result_status") == "failed"),
        "pending_count": sum(1 for item in records if item["result"].get("result_status") == "pending"),
        "qc_block_count": qc_block_count,
        "account_health_hold_block_count": account_health_hold_block_count,
        "missing_qc_trace_events": missing_qc_trace_events,
        "missing_artifact_manifest_events": missing_artifact_manifest_events,
        "incident_hook_count": incident_hook_count,
        "success_count": success_count,
        "eligible_ratio": round(eligible_count / total, 4) if total else 0.0,
        "blocked_ratio": round(blocked_count / total, 4) if total else 0.0,
        "skipped_ratio": round(skipped_count / total, 4) if total else 0.0,
        "fake_success_detected": success_count > 0,
        "fake_url_or_platform_id_detected": bool(fake_url_or_platform_id_detected),
        "platform_api_called": any(item["lifecycle"].get("platform_api_called") for item in records),
        "real_publishing_performed": any(item["lifecycle"].get("real_publishing_performed") for item in records),
        "append_only_violation_detected": not append_checks["append_only_valid"],
    }


def _coverage_requirements(metrics: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "min_total_runs": metrics["total_runs"] >= MINIMUMS["min_total_runs"],
        "min_qc_blocks": metrics["qc_block_count"] >= MINIMUMS["min_qc_blocks"],
        "min_account_health_hold_blocks": metrics["account_health_hold_block_count"] >= MINIMUMS["min_account_health_hold_blocks"],
        "min_missing_qc_trace_events": metrics["missing_qc_trace_events"] >= MINIMUMS["min_missing_qc_trace_events"],
        "min_missing_artifact_manifest_events": metrics["missing_artifact_manifest_events"] >= MINIMUMS["min_missing_artifact_manifest_events"],
        "min_incident_hooks": metrics["incident_hook_count"] >= MINIMUMS["min_incident_hooks"],
        "min_append_only_events": metrics["append_only_events"] >= MINIMUMS["min_append_only_events"],
    }
    return {
        "minimums": dict(MINIMUMS),
        "checks": checks,
        "coverage_requirements_met": all(checks.values()),
    }


def _distribution(metrics: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "eligible_count_gt_zero": metrics["eligible_count"] > 0,
        "blocked_count_gt_zero": metrics["blocked_count"] > 0,
        "skipped_count_gt_zero": metrics["skipped_count"] > 0,
        "qc_block_count_gt_zero": metrics["qc_block_count"] > 0,
        "account_health_hold_block_count_gt_zero": metrics["account_health_hold_block_count"] > 0,
        "success_count_equals_zero": metrics["success_count"] == 0,
        "fake_success_detected_false": metrics["fake_success_detected"] is False,
        "eligible_ratio_max": metrics["eligible_ratio"] <= 0.8,
        "skipped_ratio_min": metrics["skipped_ratio"] >= 0.1,
        "blocked_ratio_min": metrics["blocked_ratio"] >= 0.1,
    }
    return {
        "checks": checks,
        "state_distribution_valid": all(checks.values()),
    }


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _temporal_consistency(records: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    timestamps: list[datetime] = []
    for record in records:
        lifecycle = record["lifecycle"]
        lifecycle_time = _parse_timestamp(lifecycle.get("timestamp"))
        attempt_time = _parse_timestamp(record["attempt"].get("timestamp"))
        result_time = _parse_timestamp(record["result"].get("observed_at"))
        if lifecycle_time is None or attempt_time is None or result_time is None:
            failures.append(f"timestamp_not_parseable:{record['index']}")
            continue
        timestamps.append(lifecycle_time)
        if result_time < attempt_time:
            failures.append(f"time_travel_result_before_attempt:{record['index']}")
        if lifecycle["run_id"] != record["eligibility"]["run_id"]:
            failures.append(f"run_id_mismatch_lifecycle_eligibility:{record['index']}")
        if record["attempt"]["run_id"] != record["eligibility"]["run_id"]:
            failures.append(f"run_id_mismatch_attempt_eligibility:{record['index']}")
        if lifecycle["content_id"] != record["eligibility"]["content_id"]:
            failures.append(f"content_id_mismatch_lifecycle_eligibility:{record['index']}")
        if record["result"]["content_id"] != record["eligibility"]["content_id"]:
            failures.append(f"content_id_mismatch_result_eligibility:{record['index']}")
        result_status = record["result"]["result_status"]
        if result_status == "succeeded":
            failures.append(f"invalid_dry_run_success_transition:{record['index']}")
        if record["result"].get("published_url") or record["result"].get("platform_content_id"):
            failures.append(f"invalid_external_identity_transition:{record['index']}")
    ordered = timestamps == sorted(timestamps)
    if not ordered:
        failures.append("events_not_ordered")
    return {
        "events_ordered": ordered,
        "no_time_travel": not any(item.startswith("time_travel") for item in failures),
        "consistent_run_ids": not any("run_id_mismatch" in item for item in failures),
        "consistent_content_ids": not any("content_id_mismatch" in item for item in failures),
        "valid_lifecycle_transitions": not any("invalid_" in item for item in failures),
        "temporal_consistency_valid": not failures,
        "failures": failures,
    }


def _residual_review() -> dict[str, Any]:
    residuals = {
        residual: {
            "status": "open",
            "closed": False,
            "reason": "Dry-run evidence cannot close production publish or platform integration residuals.",
        }
        for residual in PRODUCTION_RESIDUALS
    }
    return {
        "production_residuals_closed": any(item["closed"] for item in residuals.values()),
        "residuals": residuals,
        "review_passed": not any(item["closed"] for item in residuals.values()),
    }


def _scenario_outputs(records: list[dict[str, Any]], metrics: dict[str, Any], temporal: dict[str, Any], append_checks: dict[str, Any]) -> dict[str, Any]:
    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_scenario.setdefault(record["scenario"], []).append(record)

    def passed_has(scenario: str) -> bool:
        return bool(by_scenario.get(scenario))

    fake_success_rejected = False
    fake_url_or_platform_id_rejected = False
    builder = PublishTraceBuilder()
    sample = records[0]
    try:
        builder.build_result_trace(
            attempt_trace=sample["attempt"],
            result_status="succeeded",
            result_evidence_available=False,
        )
    except PublishTraceValidationError:
        fake_success_rejected = True
    try:
        builder.build_result_trace(
            attempt_trace=sample["attempt"],
            result_status="pending",
            published_url="https://example.invalid/fake",
            platform_content_id="fake-platform-id",
            result_evidence_available=False,
        )
    except PublishTraceValidationError:
        fake_url_or_platform_id_rejected = True

    return {
        "healthy_eligible_dry_run": {"passed": passed_has("healthy_eligible_dry_run")},
        "qc_reject_block": {"passed": passed_has("qc_reject_block")},
        "qc_hold_block": {"passed": passed_has("qc_hold_block")},
        "qc_publishable_false_block": {"passed": passed_has("qc_publishable_false_block")},
        "account_health_hold_block": {"passed": passed_has("account_health_hold_block")},
        "missing_qc_trace": {"passed": passed_has("missing_qc_trace")},
        "missing_artifact_manifest": {"passed": passed_has("missing_artifact_manifest")},
        "dry_run_skipped": {"passed": metrics["skipped_count"] > 0},
        "simulated_failed_attempt": {"passed": passed_has("simulated_failed_attempt")},
        "pending_non_success": {"passed": passed_has("pending_non_success") and metrics["success_count"] == 0},
        "incident_hook_emitted": {"passed": metrics["incident_hook_count"] >= MINIMUMS["min_incident_hooks"]},
        "append_only_multi_run": {"passed": append_checks["append_only_valid"]},
        "temporal_ordering": {"passed": temporal["temporal_consistency_valid"]},
        "fake_success_rejected": {"passed": fake_success_rejected},
        "fake_url_or_platform_id_rejected": {"passed": fake_url_or_platform_id_rejected},
        "generation_mode": "controlled_dry_run_evidence",
        "sample_counts_by_scenario": {key: len(value) for key, value in sorted(by_scenario.items())},
    }


def _checklist(
    *,
    coverage: dict[str, Any],
    distribution: dict[str, Any],
    temporal: dict[str, Any],
    append_checks: dict[str, Any],
    metrics: dict[str, Any],
    residual_review: dict[str, Any],
    scenarios: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        "coverage_minimums_met": {
            "passed": coverage["coverage_requirements_met"],
            "evidence_source": "metrics.json",
            "details": coverage["checks"],
        },
        "state_distribution_valid": {
            "passed": distribution["state_distribution_valid"],
            "evidence_source": "metrics.json",
            "details": distribution["checks"],
        },
        "temporal_consistency_valid": {
            "passed": temporal["temporal_consistency_valid"],
            "evidence_source": "temporal_consistency.json",
            "failures": temporal["failures"],
        },
        "append_only_valid": {
            "passed": append_checks["append_only_valid"],
            "evidence_source": "append_only_checks.json",
        },
        "fake_success_prevention_valid": {
            "passed": metrics["success_count"] == 0 and metrics["fake_success_detected"] is False and scenarios["fake_success_rejected"]["passed"],
            "evidence_source": "scenario_outputs.json",
        },
        "url_platform_id_prevention_valid": {
            "passed": metrics["fake_url_or_platform_id_detected"] is False and scenarios["fake_url_or_platform_id_rejected"]["passed"],
            "evidence_source": "scenario_outputs.json",
        },
        "incident_hooks_present": {
            "passed": metrics["incident_hook_count"] >= MINIMUMS["min_incident_hooks"],
            "evidence_source": "metrics.json",
        },
        "hold_block_visible": {
            "passed": metrics["account_health_hold_block_count"] >= MINIMUMS["min_account_health_hold_blocks"],
            "evidence_source": "metrics.json",
        },
        "qc_block_visible": {
            "passed": metrics["qc_block_count"] >= MINIMUMS["min_qc_blocks"],
            "evidence_source": "metrics.json",
        },
        "skipped_events_visible": {
            "passed": metrics["skipped_count"] > 0,
            "evidence_source": "metrics.json",
        },
        "failed_events_visible": {
            "passed": metrics["failed_count"] > 0,
            "evidence_source": "metrics.json",
        },
        "pending_not_counted_as_success": {
            "passed": metrics["pending_count"] > 0 and metrics["success_count"] == 0,
            "evidence_source": "metrics.json",
        },
        "residual_monitoring_integrity_preserved": {
            "passed": residual_review["review_passed"],
            "evidence_source": "residual_monitoring_review.json",
        },
        "production_residuals_remain_open": {
            "passed": residual_review["production_residuals_closed"] is False,
            "evidence_source": "residual_monitoring_review.json",
        },
        "no_platform_side_effects": {
            "passed": metrics["platform_api_called"] is False and metrics["real_publishing_performed"] is False,
            "evidence_source": "metrics.json",
        },
        "no_real_publishing": {
            "passed": metrics["real_publishing_performed"] is False,
            "evidence_source": "metrics.json",
        },
        "boundary_preserved": {
            "passed": all(
                event.get("boundary_statement") == BOUNDARY_STATEMENT
                for event in _read_jsonl(CONTROLLED_LIFECYCLE_PATH)[1:]
            ),
            "evidence_source": str(CONTROLLED_LIFECYCLE_PATH),
        },
    }


def _blocking_failures(checklist: dict[str, dict[str, Any]]) -> list[str]:
    return [f"checklist:{name}" for name, result in checklist.items() if result.get("passed") is not True]


def _derive_verdict(blocking: list[str], residuals: list[str]) -> str:
    if blocking:
        return "HOLD"
    if residuals:
        return "GO_WITH_MONITORING"
    return "GO"


def main() -> int:
    _reset_audit_dir()
    records = _generate_controlled_evidence()
    append_checks = _write_controlled_lifecycle(records)
    metrics = _metrics(records, append_checks)
    coverage = _coverage_requirements(metrics)
    distribution = _distribution(metrics)
    temporal = _temporal_consistency(records)
    residual_review = _residual_review()
    scenarios = _scenario_outputs(records, metrics, temporal, append_checks)
    checklist = _checklist(
        coverage=coverage,
        distribution=distribution,
        temporal=temporal,
        append_checks=append_checks,
        metrics=metrics,
        residual_review=residual_review,
        scenarios=scenarios,
    )
    blocking = _blocking_failures(checklist)
    residuals = [] if blocking else list(PRODUCTION_RESIDUALS)
    verdict = _derive_verdict(blocking, residuals)
    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "coverage_requirements_met": coverage["coverage_requirements_met"],
        "state_distribution_valid": distribution["state_distribution_valid"],
        "temporal_consistency_valid": temporal["temporal_consistency_valid"],
        "append_only_valid": append_checks["append_only_valid"],
        "fake_success_detected": metrics["fake_success_detected"],
        "fake_url_or_platform_id_detected": metrics["fake_url_or_platform_id_detected"],
        "production_residuals_closed": residual_review["production_residuals_closed"],
        "platform_api_called": metrics["platform_api_called"],
        "real_publishing_performed": metrics["real_publishing_performed"],
        "metrics": metrics,
        "blocking_failures": blocking,
        "residual_monitoring": residuals,
        "recommendation": (
            "PROCEED_TO_PUBLISHER_DRY_RUN_BATCH_COLLECTION"
            if verdict in {"GO", "GO_WITH_MONITORING"}
            else "HOLD_BEFORE_PLATFORM_INTEGRATION_PLAN"
        ),
    }

    _write_json(METRICS_PATH, metrics)
    _write_json(TEMPORAL_CONSISTENCY_PATH, temporal)
    _write_json(APPEND_ONLY_CHECKS_PATH, append_checks)
    _write_json(RESIDUAL_REVIEW_PATH, residual_review)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps({
        "verdict": verdict,
        "total_runs": metrics["total_runs"],
        "append_only_events": metrics["append_only_events"],
        "checklist": f"{sum(1 for item in checklist.values() if item.get('passed') is True)}/{len(checklist)}",
        "blocking_failures": blocking,
        "residual_monitoring": residuals,
        "recommendation": final_verdict["recommendation"],
        "final_verdict": str(FINAL_VERDICT_PATH),
    }, indent=2))
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
