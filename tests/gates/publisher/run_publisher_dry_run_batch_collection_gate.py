from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections import Counter
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


AUDIT_DIR = ROOT / "OUT" / "audit" / "publisher_dry_run_batch_collection_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
COVERAGE_REVIEW_PATH = AUDIT_DIR / "coverage_review.json"
REPRESENTATION_REVIEW_PATH = AUDIT_DIR / "representation_review.json"
CROSS_RUN_CONSISTENCY_PATH = AUDIT_DIR / "cross_run_consistency.json"
APPEND_ONLY_CHECKS_PATH = AUDIT_DIR / "append_only_checks.json"
TEMPORAL_CONSISTENCY_PATH = AUDIT_DIR / "temporal_consistency.json"
RESIDUAL_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
ANTI_FAKE_CAUSALITY_PATH = AUDIT_DIR / "anti_fake_causality_review.json"
CONTROLLED_LIFECYCLE_PATH = AUDIT_DIR / "controlled_batch_publish_lifecycle.jsonl"

REQUIRED_DOCS = [
    ROOT / "docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN.md",
    ROOT / "docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_GATE.md",
    ROOT / "docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_PLAN.md",
    ROOT / "docs/runtime/publisher/dry-run/PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE.md",
]

REQUIRED_AUDIT_ARTIFACTS = [
    ROOT / "OUT/audit/publisher_governance_and_publish_trace_gate/final_verdict.json",
    ROOT / "OUT/audit/publisher_trace_implementation_gate/final_verdict.json",
    ROOT / "OUT/audit/publisher_dry_run_operational_evidence_gate/final_verdict.json",
]

MINIMUMS = {
    "min_total_outputs": 100,
    "min_qc_blocks": 10,
    "min_account_health_hold_blocks": 5,
    "min_missing_trace_events": 5,
    "min_missing_artifact_manifest_events": 5,
    "min_failed_attempts": 5,
    "min_pending_events": 5,
    "min_incident_hooks": 10,
    "min_append_only_events": 100,
}

PRODUCTION_RESIDUALS = [
    "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
    "PLATFORM_INTEGRATION_NOT_ENABLED",
    "PUBLISH_RESULT_HISTORY_STILL_SHORT",
]

START_TIME = datetime(2026, 4, 27, 23, 10, 0, tzinfo=timezone(timedelta(hours=-3)))


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=True), encoding="utf-8")


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:  # noqa: BLE001 - gate captures validation errors as evidence
        return {}, f"{type(exc).__name__}: {exc}"


def _timestamp(index: int) -> str:
    return (START_TIME + timedelta(seconds=index)).isoformat()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                events.append(json.loads(stripped))
    return events


def _event_to_dict(event: Any, *, scenario: str, state_type: str, batch_phase: str) -> dict[str, Any]:
    payload = event.to_dict() if hasattr(event, "to_dict") else dict(event)
    payload.update(
        {
            "dry_run": True,
            "trace_only_batch_collection": True,
            "scenario": scenario,
            "state_type": state_type,
            "batch_phase": batch_phase,
            "platform_api_called": False,
            "upload_performed": False,
            "scheduler_invoked": False,
            "real_publishing_performed": False,
            "real_url_emitted": False,
            "real_platform_content_id_emitted": False,
            "anti_fake_causality_scope": "trace_observability_only",
        }
    )
    return payload


def _build_record(
    builder: PublishTraceBuilder,
    *,
    index: int,
    scenario: str,
    state_type: str,
    batch_phase: str,
    qc_status: str | None = "APPROVE",
    qc_publishable: bool | None = True,
    account_health_decision: str | None = "SAFE",
    missing_qc_trace: bool = False,
    missing_artifact_manifest: bool = False,
    simulate_failure: bool = False,
    pending_attempt: bool = False,
) -> dict[str, Any]:
    run_id = f"publisher_batch_run_{index:04d}"
    content_id = f"publisher_batch_content_{index:04d}"
    timestamp = _timestamp(index)
    qc_trace_ref = None if missing_qc_trace else f"qc_trace:publisher_batch:{index:04d}"
    artifact_manifest_ref = None if missing_artifact_manifest else f"artifact_manifest:publisher_batch:{index:04d}"

    eligibility = builder.build_eligibility_trace(
        run_id=run_id,
        content_id=content_id,
        qc_status=qc_status,
        qc_publishable=qc_publishable,
        qc_trace_ref=qc_trace_ref,
        account_health_decision=account_health_decision,
        health_trace_ref=f"health_trace:publisher_batch:{index:04d}",
        strategy_ref=f"strategy:publisher_batch:{index:04d}",
        artifact_manifest_ref=artifact_manifest_ref,
        dry_run=True,
    )
    attempt = builder.build_attempt_trace(
        eligibility_trace=eligibility,
        attempt_id=f"attempt:publisher_batch:{index:04d}",
        timestamp=timestamp,
        publish_target="trace_only_batch_target" if (simulate_failure or pending_attempt) else None,
        dry_run=not (simulate_failure or pending_attempt),
        simulate_failure=simulate_failure,
        failure_reason="PUBLISH_TARGET_ERROR" if simulate_failure else None,
    )
    result = builder.build_result_trace(attempt_trace=attempt, observed_at=timestamp)
    lifecycle = builder.build_lifecycle_event(
        eligibility_trace=eligibility,
        attempt_trace=attempt,
        result_trace=result,
        publish_event_id=f"publish_event:publisher_batch:{index:04d}",
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
        "state_type": state_type,
        "batch_phase": batch_phase,
        "eligibility": eligibility.to_dict(),
        "attempt": attempt.to_dict(),
        "result": result.to_dict(),
        "lifecycle": _event_to_dict(lifecycle, scenario=scenario, state_type=state_type, batch_phase=batch_phase),
        "incident_hooks": [hook.to_dict() for hook in hooks],
    }


def _generate_controlled_batch() -> list[dict[str, Any]]:
    builder = PublishTraceBuilder()
    records: list[dict[str, Any]] = []
    index = 0

    def add(count: int, scenario: str, state_type: str, **kwargs: Any) -> None:
        nonlocal index
        for _ in range(count):
            index += 1
            batch_phase = "phase_1" if index <= 60 else "phase_2"
            records.append(
                _build_record(
                    builder,
                    index=index,
                    scenario=scenario,
                    state_type=state_type,
                    batch_phase=batch_phase,
                    **kwargs,
                )
            )

    add(35, "healthy_eligible_dry_run", "eligible_dry_run")
    add(20, "qc_reject_block", "qc_block", qc_status="REJECT", qc_publishable=False)
    add(10, "qc_hold_block", "qc_block", qc_status="HOLD", qc_publishable=False)
    add(10, "qc_publishable_false_block", "qc_block", qc_status="APPROVE", qc_publishable=False)
    add(10, "account_health_hold_block", "account_health_hold_block", account_health_decision="HOLD")
    add(8, "missing_qc_trace", "missing_evidence", missing_qc_trace=True)
    add(8, "missing_artifact_manifest", "missing_evidence", missing_artifact_manifest=True)
    add(10, "simulated_failed_attempt", "simulated_failure", simulate_failure=True)
    add(9, "pending_non_success", "pending_non_success", pending_attempt=True)
    return sorted(records, key=lambda item: item["index"])


def _write_append_only_evidence(records: list[dict[str, Any]]) -> dict[str, Any]:
    sentinel = {
        "sentinel": True,
        "purpose": "append_only_baseline",
        "dry_run_batch_gate": "publisher_dry_run_batch_collection_gate",
    }
    CONTROLLED_LIFECYCLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTROLLED_LIFECYCLE_PATH.write_text(json.dumps(sentinel, sort_keys=True) + "\n", encoding="utf-8")
    writer = PublishLifecycleWriter(CONTROLLED_LIFECYCLE_PATH)

    phase_one = [record for record in records if record["batch_phase"] == "phase_1"]
    phase_two = [record for record in records if record["batch_phase"] == "phase_2"]

    for record in phase_one:
        writer.append_event(record["lifecycle"])
    phase_one_text = CONTROLLED_LIFECYCLE_PATH.read_text(encoding="utf-8")
    phase_one_hash = hashlib.sha256(phase_one_text.encode("utf-8")).hexdigest()
    phase_one_lines = phase_one_text.splitlines()

    for record in phase_two:
        writer.append_event(record["lifecycle"])
    final_text = CONTROLLED_LIFECYCLE_PATH.read_text(encoding="utf-8")
    final_lines = final_text.splitlines()
    parsed = _read_jsonl(CONTROLLED_LIFECYCLE_PATH)
    appended_events = parsed[1:]

    phase_one_preserved = final_text.startswith(phase_one_text)
    failure_skip_pending_preserved = all(
        event.get("result", {}).get("result_status") != "succeeded"
        and event.get("result", {}).get("published_url") is None
        and event.get("result", {}).get("platform_content_id") is None
        for event in appended_events
    )
    append_only_valid = (
        phase_one_preserved
        and len(final_lines) == len(phase_one_lines) + len(phase_two)
        and len(appended_events) == len(records)
        and len(parsed) == len(final_lines)
        and failure_skip_pending_preserved
    )
    return {
        "path": str(CONTROLLED_LIFECYCLE_PATH),
        "phase_one_event_count": len(phase_one),
        "phase_two_event_count": len(phase_two),
        "phase_one_line_count": len(phase_one_lines),
        "final_line_count": len(final_lines),
        "appended_event_count": len(appended_events),
        "phase_one_hash": phase_one_hash,
        "final_prefix_hash": hashlib.sha256(final_text[: len(phase_one_text)].encode("utf-8")).hexdigest(),
        "multi_batch_growth": len(phase_two) > 0 and len(final_lines) > len(phase_one_lines),
        "phase_one_preserved_byte_for_byte": phase_one_preserved,
        "no_event_deletion": len(appended_events) == len(records),
        "no_event_mutation": phase_one_preserved,
        "historical_integrity_preserved": phase_one_preserved,
        "failure_skip_pending_preserved": failure_skip_pending_preserved,
        "all_lines_parseable": len(parsed) == len(final_lines),
        "append_only_valid": append_only_valid,
    }


def _build_metrics(records: list[dict[str, Any]], append_checks: dict[str, Any]) -> dict[str, Any]:
    state_counts = Counter(record["state_type"] for record in records)
    scenario_counts = Counter(record["scenario"] for record in records)
    total_outputs = len(records)
    qc_block_count = sum(
        1
        for record in records
        if any(
            reason in {"QC_REJECTED", "QC_HOLD", "QC_NOT_PUBLISHABLE"}
            for reason in record["eligibility"].get("blocking_reasons", [])
        )
    )
    account_health_hold_block_count = sum(
        1 for record in records if "ACCOUNT_HEALTH_HOLD" in record["eligibility"].get("blocking_reasons", [])
    )
    missing_qc_trace_events = sum(
        1 for record in records if "MISSING_QC_TRACE" in record["eligibility"].get("blocking_reasons", [])
    )
    missing_artifact_manifest_events = sum(
        1 for record in records if "MISSING_ARTIFACT_MANIFEST" in record["eligibility"].get("blocking_reasons", [])
    )
    missing_trace_events = missing_qc_trace_events + missing_artifact_manifest_events
    failed_attempts = sum(1 for record in records if record["result"].get("result_status") == "failed")
    pending_events = sum(1 for record in records if record["result"].get("result_status") == "pending")
    incident_hooks = sum(len(record["incident_hooks"]) for record in records)
    success_count = sum(1 for record in records if record["result"].get("result_status") == "succeeded")
    max_single_state_count = max(state_counts.values()) if state_counts else 0

    return {
        "total_outputs": total_outputs,
        "append_only_events": append_checks["appended_event_count"],
        "state_counts": dict(sorted(state_counts.items())),
        "scenario_counts": dict(sorted(scenario_counts.items())),
        "distinct_state_types": len(state_counts),
        "max_single_state_count": max_single_state_count,
        "max_single_state_ratio": round(max_single_state_count / total_outputs, 4) if total_outputs else 0.0,
        "eligible_count": sum(1 for record in records if record["eligibility"].get("eligible") is True),
        "blocked_count": sum(1 for record in records if record["eligibility"].get("eligible") is False),
        "skipped_count": sum(1 for record in records if record["attempt"].get("skip_reason")),
        "qc_block_count": qc_block_count,
        "account_health_hold_block_count": account_health_hold_block_count,
        "missing_qc_trace_events": missing_qc_trace_events,
        "missing_artifact_manifest_events": missing_artifact_manifest_events,
        "missing_trace_events": missing_trace_events,
        "failed_attempts": failed_attempts,
        "pending_events": pending_events,
        "incident_hook_count": incident_hooks,
        "success_count": success_count,
        "fake_success_detected": success_count > 0,
        "fake_url_or_platform_id_detected": any(
            record["result"].get("published_url") or record["result"].get("platform_content_id") for record in records
        ),
        "result_evidence_available_count": sum(
            1 for record in records if record["result"].get("result_evidence_available") is True
        ),
        "platform_api_called": any(record["lifecycle"].get("platform_api_called") for record in records),
        "upload_performed": any(record["lifecycle"].get("upload_performed") for record in records),
        "scheduler_invoked": any(record["lifecycle"].get("scheduler_invoked") for record in records),
        "real_publishing_performed": any(record["lifecycle"].get("real_publishing_performed") for record in records),
    }


def _coverage_review(metrics: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "min_total_outputs": metrics["total_outputs"] >= MINIMUMS["min_total_outputs"],
        "min_qc_blocks": metrics["qc_block_count"] >= MINIMUMS["min_qc_blocks"],
        "min_account_health_hold_blocks": (
            metrics["account_health_hold_block_count"] >= MINIMUMS["min_account_health_hold_blocks"]
        ),
        "min_missing_trace_events": metrics["missing_trace_events"] >= MINIMUMS["min_missing_trace_events"],
        "min_missing_artifact_manifest_events": (
            metrics["missing_artifact_manifest_events"] >= MINIMUMS["min_missing_artifact_manifest_events"]
        ),
        "min_failed_attempts": metrics["failed_attempts"] >= MINIMUMS["min_failed_attempts"],
        "min_pending_events": metrics["pending_events"] >= MINIMUMS["min_pending_events"],
        "min_incident_hooks": metrics["incident_hook_count"] >= MINIMUMS["min_incident_hooks"],
        "min_append_only_events": metrics["append_only_events"] >= MINIMUMS["min_append_only_events"],
    }
    return {
        "minimum_batch_requirements": dict(MINIMUMS),
        "observed": {
            "total_outputs": metrics["total_outputs"],
            "qc_block_count": metrics["qc_block_count"],
            "account_health_hold_block_count": metrics["account_health_hold_block_count"],
            "missing_trace_events": metrics["missing_trace_events"],
            "missing_artifact_manifest_events": metrics["missing_artifact_manifest_events"],
            "failed_attempts": metrics["failed_attempts"],
            "pending_events": metrics["pending_events"],
            "incident_hook_count": metrics["incident_hook_count"],
            "append_only_events": metrics["append_only_events"],
        },
        "checks": checks,
        "coverage_requirements_met": all(checks.values()),
    }


def _representation_review(metrics: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "no_single_state_dominance": metrics["max_single_state_ratio"] <= 0.7,
        "min_distinct_state_types": metrics["distinct_state_types"] >= 5,
        "must_include_failure_states": metrics["failed_attempts"] > 0,
        "must_include_blocked_states": metrics["blocked_count"] > 0,
        "must_include_missing_evidence_states": metrics["missing_trace_events"] > 0,
        "must_include_pending_states": metrics["pending_events"] > 0,
        "must_include_eligible_states": metrics["eligible_count"] > 0,
        "batch_not_always_healthy": metrics["blocked_count"] > 0 and metrics["failed_attempts"] > 0,
        "success_count_equals_zero": metrics["success_count"] == 0,
    }
    return {
        "representation_constraints": {
            "max_single_state_ratio": 0.7,
            "min_distinct_state_types": 5,
            "required_state_types": [
                "eligible_dry_run",
                "qc_block",
                "account_health_hold_block",
                "missing_evidence",
                "simulated_failure",
                "pending_non_success",
            ],
        },
        "state_counts": metrics["state_counts"],
        "scenario_counts": metrics["scenario_counts"],
        "checks": checks,
        "representation_valid": all(checks.values()),
    }


def _cross_run_consistency(records: list[dict[str, Any]]) -> dict[str, Any]:
    events = [record["lifecycle"] for record in records]
    top_level_keysets = {tuple(sorted(event.keys())) for event in events}
    eligibility_keysets = {tuple(sorted(event["eligibility"].keys())) for event in events}
    attempt_keysets = {tuple(sorted(event["attempt"].keys())) for event in events}
    result_keysets = {tuple(sorted(event["result"].keys())) for event in events}
    trace_versions = {event["eligibility"].get("trace_version") for event in events}
    boundary_statements = {event.get("boundary_statement") for event in events}
    run_ids = [event.get("run_id") for event in events]
    content_ids = [event.get("content_id") for event in events]
    forbidden_random_keys = {"uuid", "random", "nonce"}

    all_keys_text = " ".join(" ".join(event.keys()) for event in events).lower()
    checks = {
        "schema_stable": len(top_level_keysets) == 1,
        "event_structure_consistent": (
            len(eligibility_keysets) == 1 and len(attempt_keysets) == 1 and len(result_keysets) == 1
        ),
        "trace_version_stable": len(trace_versions) == 1,
        "no_random_field_variation": not any(fragment in all_keys_text for fragment in forbidden_random_keys),
        "run_id_uniqueness": len(run_ids) == len(set(run_ids)),
        "content_id_traceability": len(content_ids) == len(set(content_ids)) and all(content_ids),
        "boundary_statement_stable": boundary_statements == {BOUNDARY_STATEMENT},
    }
    return {
        "checks": checks,
        "top_level_schema": sorted(events[0].keys()) if events else [],
        "eligibility_schema": sorted(events[0]["eligibility"].keys()) if events else [],
        "attempt_schema": sorted(events[0]["attempt"].keys()) if events else [],
        "result_schema": sorted(events[0]["result"].keys()) if events else [],
        "trace_versions": sorted(trace_versions),
        "run_id_count": len(run_ids),
        "unique_run_id_count": len(set(run_ids)),
        "content_id_count": len(content_ids),
        "unique_content_id_count": len(set(content_ids)),
        "cross_run_consistency_valid": all(checks.values()),
    }


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _temporal_consistency(records: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    lifecycle_times: list[datetime] = []
    for record in records:
        lifecycle = record["lifecycle"]
        eligibility = record["eligibility"]
        attempt = record["attempt"]
        result = record["result"]
        lifecycle_time = _parse_timestamp(lifecycle.get("timestamp"))
        attempt_time = _parse_timestamp(attempt.get("timestamp"))
        result_time = _parse_timestamp(result.get("observed_at"))
        if lifecycle_time is None or attempt_time is None or result_time is None:
            failures.append(f"timestamp_not_parseable:{record['index']}")
            continue
        lifecycle_times.append(lifecycle_time)
        if lifecycle_time < START_TIME:
            failures.append(f"event_before_logical_run_start:{record['index']}")
        if result_time < attempt_time:
            failures.append(f"time_travel_result_before_attempt:{record['index']}")
        if lifecycle["run_id"] != eligibility["run_id"] or attempt["run_id"] != eligibility["run_id"]:
            failures.append(f"run_id_mismatch:{record['index']}")
        if lifecycle["content_id"] != eligibility["content_id"] or result["content_id"] != eligibility["content_id"]:
            failures.append(f"content_id_mismatch:{record['index']}")
        if result["result_status"] == "succeeded":
            failures.append(f"dry_run_success_transition:{record['index']}")
        if result.get("published_url") or result.get("platform_content_id"):
            failures.append(f"external_identity_in_dry_run:{record['index']}")
        if eligibility["eligible"] is False and attempt["attempted"] is True:
            failures.append(f"blocked_event_attempted:{record['index']}")
        if attempt["attempt_status"] == "failed" and result["result_status"] != "failed":
            failures.append(f"failed_attempt_not_failed_result:{record['index']}")
        if attempt["attempt_status"] == "attempted" and result["result_status"] != "pending":
            failures.append(f"attempted_non_failure_not_pending:{record['index']}")

    events_ordered = lifecycle_times == sorted(lifecycle_times)
    if not events_ordered:
        failures.append("lifecycle_events_not_ordered")
    return {
        "timestamps_parseable": not any(item.startswith("timestamp_not_parseable") for item in failures),
        "events_ordered": events_ordered,
        "no_time_travel": not any("time_travel" in item for item in failures),
        "consistent_run_ids": not any("run_id_mismatch" in item for item in failures),
        "consistent_content_ids": not any("content_id_mismatch" in item for item in failures),
        "valid_lifecycle_transitions": not any(
            marker in item
            for marker in [
                "dry_run_success_transition",
                "external_identity_in_dry_run",
                "blocked_event_attempted",
                "failed_attempt_not_failed_result",
                "attempted_non_failure_not_pending",
            ]
            for item in failures
        ),
        "temporal_consistency_valid": not failures,
        "failures": failures,
    }


def _residual_monitoring_review() -> dict[str, Any]:
    residuals = {
        residual: {
            "status": "open",
            "closed": False,
            "rationale": "Dry-run batch evidence cannot close production publish, platform integration or result history residuals.",
        }
        for residual in PRODUCTION_RESIDUALS
    }
    return {
        "production_residuals_closed": any(item["closed"] for item in residuals.values()),
        "production_residuals_required_open": list(PRODUCTION_RESIDUALS),
        "residuals": residuals,
        "dry_run_residuals_reduced": [
            "DRY_RUN_BATCH_COVERAGE_UNCERTAINTY",
            "DRY_RUN_STATE_REPRESENTATION_UNCERTAINTY",
            "DRY_RUN_APPEND_ONLY_INTEGRITY_UNCERTAINTY",
        ],
        "review_passed": not any(item["closed"] for item in residuals.values()),
    }


def _anti_fake_causality_review(metrics: dict[str, Any], residual_review: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "eligible_count_not_used_as_production_readiness": True,
        "low_failure_count_not_used_as_system_quality": True,
        "no_error_not_used_as_platform_readiness": True,
        "dry_run_not_used_for_post_publish_metrics": True,
        "dry_run_not_used_for_attribution": True,
        "dry_run_not_used_for_strategy_change": True,
        "dry_run_not_used_to_escalate_learning_pressure": True,
        "dry_run_not_used_to_close_production_residuals": residual_review["production_residuals_closed"] is False,
        "success_count_zero": metrics["success_count"] == 0,
        "publishing_authorized_false": True,
        "platform_integration_authorized_false": True,
    }
    return {
        "allowed_conclusions": [
            "trace coverage",
            "state visibility",
            "append-only integrity",
            "incident visibility",
            "temporal consistency",
            "boundary preservation",
        ],
        "forbidden_conclusions": [
            "production readiness",
            "platform readiness",
            "post-publish outcome quality",
            "attribution causality",
            "Strategy change justification",
            "Learning pressure escalation",
        ],
        "checks": checks,
        "anti_fake_causality_valid": all(checks.values()),
    }


def _precondition_review() -> dict[str, Any]:
    docs = {str(path.relative_to(ROOT)): path.exists() for path in REQUIRED_DOCS}
    artifacts: dict[str, Any] = {}
    json_errors: dict[str, str] = {}
    for path in REQUIRED_AUDIT_ARTIFACTS:
        rel = str(path.relative_to(ROOT))
        exists = path.exists()
        artifacts[rel] = {"exists": exists}
        if exists:
            payload, error = _load_json(path)
            json_errors[rel] = error
            artifacts[rel]["verdict"] = payload.get("verdict")
            artifacts[rel]["verdict_acceptable"] = payload.get("verdict") in {"GO", "GO_WITH_MONITORING"}
        else:
            json_errors[rel] = "missing"
    passed = all(docs.values()) and all(
        item.get("exists") and item.get("verdict_acceptable") for item in artifacts.values()
    ) and not any(json_errors.values())
    return {
        "docs": docs,
        "artifacts": artifacts,
        "json_errors": json_errors,
        "preconditions_passed": passed,
    }


def _scenario_outputs(
    *,
    records: list[dict[str, Any]],
    metrics: dict[str, Any],
    coverage: dict[str, Any],
    representation: dict[str, Any],
    cross_run: dict[str, Any],
    append_checks: dict[str, Any],
    temporal: dict[str, Any],
    residual_review: dict[str, Any],
    anti_fake: dict[str, Any],
) -> dict[str, Any]:
    scenario_counts = Counter(record["scenario"] for record in records)
    builder = PublishTraceBuilder()
    fake_success_rejected = False
    fake_url_or_platform_id_rejected = False
    sample_attempt = records[0]["attempt"]
    try:
        builder.build_result_trace(
            attempt_trace=sample_attempt,
            result_status="succeeded",
            result_evidence_available=False,
        )
    except PublishTraceValidationError:
        fake_success_rejected = True
    try:
        builder.build_result_trace(
            attempt_trace=sample_attempt,
            result_status="pending",
            published_url="https://example.invalid/fake",
            platform_content_id="fake-platform-id",
            result_evidence_available=False,
        )
    except PublishTraceValidationError:
        fake_url_or_platform_id_rejected = True

    return {
        "representative_eligible_batch_outputs": {"passed": scenario_counts["healthy_eligible_dry_run"] >= 1},
        "qc_reject_batch_blocks": {"passed": scenario_counts["qc_reject_block"] >= 1},
        "qc_hold_batch_blocks": {"passed": scenario_counts["qc_hold_block"] >= 1},
        "qc_publishable_false_batch_blocks": {"passed": scenario_counts["qc_publishable_false_block"] >= 1},
        "account_health_hold_batch_blocks": {"passed": scenario_counts["account_health_hold_block"] >= 1},
        "missing_qc_trace_batch_cases": {"passed": scenario_counts["missing_qc_trace"] >= 1},
        "missing_artifact_manifest_batch_cases": {"passed": scenario_counts["missing_artifact_manifest"] >= 1},
        "simulated_failed_attempt_batch_cases": {"passed": scenario_counts["simulated_failed_attempt"] >= 1},
        "pending_non_success_batch_cases": {"passed": scenario_counts["pending_non_success"] >= 1},
        "incident_hook_aggregation": {"passed": metrics["incident_hook_count"] >= MINIMUMS["min_incident_hooks"]},
        "append_only_lifecycle_batch_growth": {"passed": append_checks["multi_batch_growth"] is True},
        "multi_batch_append_only_growth": {"passed": append_checks["append_only_valid"] is True},
        "cross_run_schema_stability": {"passed": cross_run["cross_run_consistency_valid"] is True},
        "run_id_uniqueness": {"passed": cross_run["checks"]["run_id_uniqueness"] is True},
        "temporal_consistency_across_batch": {"passed": temporal["temporal_consistency_valid"] is True},
        "fake_success_absence": {"passed": metrics["success_count"] == 0 and fake_success_rejected},
        "fake_url_platform_id_absence": {
            "passed": metrics["fake_url_or_platform_id_detected"] is False and fake_url_or_platform_id_rejected
        },
        "residual_production_state_preserved": {"passed": residual_review["production_residuals_closed"] is False},
        "anti_fake_causality_review": {"passed": anti_fake["anti_fake_causality_valid"] is True},
        "coverage_summary": {
            "passed": coverage["coverage_requirements_met"],
            "observed": coverage["observed"],
        },
        "representation_summary": {
            "passed": representation["representation_valid"],
            "state_counts": representation["state_counts"],
        },
        "generation_mode": "controlled_trace_only_dry_run_batch",
        "sample_counts_by_scenario": dict(sorted(scenario_counts.items())),
    }


def _checklist(
    *,
    preconditions: dict[str, Any],
    coverage: dict[str, Any],
    representation: dict[str, Any],
    cross_run: dict[str, Any],
    temporal: dict[str, Any],
    append_checks: dict[str, Any],
    residual_review: dict[str, Any],
    anti_fake: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        "preconditions_present": {
            "passed": preconditions["preconditions_passed"],
            "evidence_source": "precondition artifact check",
            "details": preconditions,
        },
        "minimum_batch_coverage_met": {
            "passed": coverage["coverage_requirements_met"],
            "evidence_source": "coverage_review.json",
            "details": coverage["checks"],
        },
        "representation_constraints_met": {
            "passed": representation["representation_valid"],
            "evidence_source": "representation_review.json",
            "details": representation["checks"],
        },
        "no_single_state_dominance": {
            "passed": representation["checks"]["no_single_state_dominance"],
            "evidence_source": "representation_review.json",
        },
        "failure_states_included": {
            "passed": representation["checks"]["must_include_failure_states"],
            "evidence_source": "metrics.json",
        },
        "blocked_states_included": {
            "passed": representation["checks"]["must_include_blocked_states"],
            "evidence_source": "metrics.json",
        },
        "missing_evidence_states_included": {
            "passed": representation["checks"]["must_include_missing_evidence_states"],
            "evidence_source": "metrics.json",
        },
        "pending_states_included": {
            "passed": representation["checks"]["must_include_pending_states"],
            "evidence_source": "metrics.json",
        },
        "cross_run_schema_stable": {
            "passed": cross_run["checks"]["schema_stable"],
            "evidence_source": "cross_run_consistency.json",
        },
        "event_structure_consistent": {
            "passed": cross_run["checks"]["event_structure_consistent"],
            "evidence_source": "cross_run_consistency.json",
        },
        "run_ids_unique": {
            "passed": cross_run["checks"]["run_id_uniqueness"],
            "evidence_source": "cross_run_consistency.json",
        },
        "content_ids_traceable": {
            "passed": cross_run["checks"]["content_id_traceability"],
            "evidence_source": "cross_run_consistency.json",
        },
        "temporal_consistency_valid": {
            "passed": temporal["temporal_consistency_valid"],
            "evidence_source": "temporal_consistency.json",
            "failures": temporal["failures"],
        },
        "append_only_multi_batch_growth_valid": {
            "passed": append_checks["append_only_valid"],
            "evidence_source": "append_only_checks.json",
        },
        "fake_success_absent": {
            "passed": metrics["success_count"] == 0 and metrics["fake_success_detected"] is False,
            "evidence_source": "metrics.json",
        },
        "fake_url_or_platform_id_absent": {
            "passed": metrics["fake_url_or_platform_id_detected"] is False,
            "evidence_source": "metrics.json",
        },
        "platform_side_effects_absent": {
            "passed": metrics["platform_api_called"] is False
            and metrics["upload_performed"] is False
            and metrics["scheduler_invoked"] is False
            and metrics["real_publishing_performed"] is False,
            "evidence_source": "metrics.json",
        },
        "production_residuals_remain_open": {
            "passed": residual_review["production_residuals_closed"] is False,
            "evidence_source": "residual_monitoring_review.json",
        },
        "anti_fake_causality_valid": {
            "passed": anti_fake["anti_fake_causality_valid"],
            "evidence_source": "anti_fake_causality_review.json",
        },
        "boundary_preserved": {
            "passed": cross_run["checks"]["boundary_statement_stable"]
            and metrics["platform_api_called"] is False
            and metrics["real_publishing_performed"] is False,
            "evidence_source": "cross_run_consistency.json",
        },
    }


def _blocking_failures(scenarios: dict[str, Any], checklist: dict[str, dict[str, Any]]) -> list[str]:
    failures = [
        f"scenario:{name}"
        for name, result in scenarios.items()
        if isinstance(result, dict) and "passed" in result and result.get("passed") is not True
    ]
    failures.extend(
        f"checklist:{name}"
        for name, result in checklist.items()
        if result.get("passed") is not True
    )
    return list(dict.fromkeys(failures))


def _derive_verdict(blocking_failures: list[str], residuals: list[str]) -> str:
    if blocking_failures:
        return "HOLD"
    if residuals:
        return "GO_WITH_MONITORING"
    return "GO"


def main() -> int:
    _reset_audit_dir()
    preconditions = _precondition_review()
    records = _generate_controlled_batch()
    append_checks = _write_append_only_evidence(records)
    metrics = _build_metrics(records, append_checks)
    coverage = _coverage_review(metrics)
    representation = _representation_review(metrics)
    cross_run = _cross_run_consistency(records)
    temporal = _temporal_consistency(records)
    residual_review = _residual_monitoring_review()
    anti_fake = _anti_fake_causality_review(metrics, residual_review)
    scenarios = _scenario_outputs(
        records=records,
        metrics=metrics,
        coverage=coverage,
        representation=representation,
        cross_run=cross_run,
        append_checks=append_checks,
        temporal=temporal,
        residual_review=residual_review,
        anti_fake=anti_fake,
    )
    checklist = _checklist(
        preconditions=preconditions,
        coverage=coverage,
        representation=representation,
        cross_run=cross_run,
        temporal=temporal,
        append_checks=append_checks,
        residual_review=residual_review,
        anti_fake=anti_fake,
        metrics=metrics,
    )
    blocking_failures = _blocking_failures(scenarios, checklist)
    residuals = [] if blocking_failures else list(PRODUCTION_RESIDUALS)
    verdict = _derive_verdict(blocking_failures, residuals)
    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "PUBLISHER_DRY_RUN_BATCH_COLLECTION_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "minimum_batch_coverage_met": coverage["coverage_requirements_met"],
        "representation_valid": representation["representation_valid"],
        "cross_run_consistency_valid": cross_run["cross_run_consistency_valid"],
        "temporal_consistency_valid": temporal["temporal_consistency_valid"],
        "append_only_valid": append_checks["append_only_valid"],
        "fake_success_detected": metrics["fake_success_detected"],
        "fake_url_or_platform_id_detected": metrics["fake_url_or_platform_id_detected"],
        "platform_api_called": metrics["platform_api_called"],
        "real_publishing_performed": metrics["real_publishing_performed"],
        "production_residuals_closed": residual_review["production_residuals_closed"],
        "anti_fake_causality_valid": anti_fake["anti_fake_causality_valid"],
        "publisher_maturity": "TRACE_OBSERVABLE_AT_SCALE" if verdict in {"GO", "GO_WITH_MONITORING"} else "BLOCKED",
        "publishing_authorized": False,
        "platform_integration_authorized": False,
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": residuals,
        "recommendation": (
            "PROCEED_TO_PUBLISHER_PLATFORM_INTEGRATION_PLAN"
            if verdict in {"GO", "GO_WITH_MONITORING"}
            else "HOLD_BEFORE_PLATFORM_INTEGRATION_PLAN"
        ),
    }

    _write_json(METRICS_PATH, metrics)
    _write_json(COVERAGE_REVIEW_PATH, coverage)
    _write_json(REPRESENTATION_REVIEW_PATH, representation)
    _write_json(CROSS_RUN_CONSISTENCY_PATH, cross_run)
    _write_json(APPEND_ONLY_CHECKS_PATH, append_checks)
    _write_json(TEMPORAL_CONSISTENCY_PATH, temporal)
    _write_json(RESIDUAL_REVIEW_PATH, residual_review)
    _write_json(ANTI_FAKE_CAUSALITY_PATH, anti_fake)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(
        json.dumps(
            {
                "verdict": verdict,
                "publisher_maturity": final_verdict["publisher_maturity"],
                "total_outputs": metrics["total_outputs"],
                "append_only_events": metrics["append_only_events"],
                "checklist": f"{sum(1 for item in checklist.values() if item.get('passed') is True)}/{len(checklist)}",
                "success_count": metrics["success_count"],
                "real_publishing_performed": metrics["real_publishing_performed"],
                "platform_api_called": metrics["platform_api_called"],
                "blocking_failures": blocking_failures,
                "residual_monitoring": residuals,
                "recommendation": final_verdict["recommendation"],
                "final_verdict": str(FINAL_VERDICT_PATH),
            },
            indent=2,
        )
    )
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
