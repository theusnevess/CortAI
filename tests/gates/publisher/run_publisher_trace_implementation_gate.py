from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime
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


AUDIT_DIR = ROOT / "OUT" / "audit" / "publisher_trace_implementation_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"


REQUIRED_DOCS = [
    ROOT / "docs/runtime/phase-3/PHASE_3_OPERATIONAL_GOVERNANCE_AND_MATURITY_PLAN.md",
    ROOT / "docs/runtime/phase-3/monitoring/PRODUCTION_MONITORING_AND_RUNTIME_EVIDENCE_PLAN.md",
    ROOT / "docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN.md",
    ROOT / "docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE.md",
    ROOT / "docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_PLAN.md",
    ROOT / "docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_GATE_PLAN.md",
    ROOT / "docs/runtime/publisher/trace/PUBLISHER_TRACE_IMPLEMENTATION_GATE.md",
]

REQUIRED_TRACE_KEYS = {
    "publish_eligibility_trace",
    "publish_attempt_trace",
    "publish_result_trace",
    "publish_lifecycle_event",
    "incident_hooks",
    "boundary_statement",
}


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=True), encoding="utf-8")


def _base_bundle(builder: PublishTraceBuilder, *, content_id: str = "content_gate", dry_run: bool = True):
    return builder.build_trace_bundle(
        run_id="publisher_trace_gate_run",
        content_id=content_id,
        qc_status="APPROVE",
        qc_publishable=True,
        qc_trace_ref="qc_trace:publisher_trace_gate",
        account_health_decision="SAFE",
        health_trace_ref="health_trace:publisher_trace_gate",
        strategy_ref="strategy:publisher_trace_gate",
        artifact_manifest_ref="artifact_manifest:publisher_trace_gate",
        dry_run=dry_run,
    )


def _scenario_result(name: str, passed: bool, **extra: Any) -> dict[str, Any]:
    return {"scenario": name, "passed": passed, **extra}


def _safe_call(func):
    try:
        return True, func(), None
    except Exception as exc:  # noqa: BLE001 - gate captures failure as evidence
        return False, None, f"{type(exc).__name__}: {exc}"


def _run_scenarios() -> dict[str, dict[str, Any]]:
    builder = PublishTraceBuilder()
    scenarios: dict[str, dict[str, Any]] = {}

    bundle = _base_bundle(builder)
    payload = bundle.to_dict()
    valid, failures = builder.validate_trace_bundle(bundle)
    scenarios["eligible_dry_run_trace_created"] = _scenario_result(
        "eligible_dry_run_trace_created",
        valid
        and not failures
        and payload["publish_eligibility_trace"]["eligible"] is True
        and payload["publish_attempt_trace"]["attempted"] is False
        and payload["publish_attempt_trace"]["skip_reason"] == "DRY_RUN_MODE"
        and payload["publish_result_trace"]["result_status"] == "not_attempted",
        trace=payload,
        validation_failures=failures,
    )

    hold = builder.build_eligibility_trace(
        run_id="run_hold",
        content_id="content_hold",
        qc_status="APPROVE",
        qc_publishable=True,
        qc_trace_ref="qc_trace:hold",
        account_health_decision="HOLD",
        health_trace_ref="health_trace:hold",
        strategy_ref="strategy:hold",
        artifact_manifest_ref="artifact_manifest:hold",
    )
    hold_attempt = builder.build_attempt_trace(eligibility_trace=hold, attempt_id="attempt:hold")
    scenarios["account_health_hold_blocks_eligibility"] = _scenario_result(
        "account_health_hold_blocks_eligibility",
        hold.eligible is False
        and "ACCOUNT_HEALTH_HOLD" in hold.blocking_reasons
        and hold_attempt.attempted is False,
        eligibility=hold.to_dict(),
        attempt=hold_attempt.to_dict(),
    )

    for scenario_name, qc_status, publishable, reason in [
        ("qc_reject_blocks_eligibility", "REJECT", False, "QC_REJECTED"),
        ("qc_hold_blocks_eligibility", "HOLD", False, "QC_HOLD"),
        ("qc_not_publishable_blocks_eligibility", "APPROVE", False, "QC_NOT_PUBLISHABLE"),
    ]:
        trace = builder.build_eligibility_trace(
            run_id=f"run_{scenario_name}",
            content_id=f"content_{scenario_name}",
            qc_status=qc_status,
            qc_publishable=publishable,
            qc_trace_ref=f"qc_trace:{scenario_name}",
            account_health_decision="SAFE",
            health_trace_ref=f"health_trace:{scenario_name}",
            strategy_ref=f"strategy:{scenario_name}",
            artifact_manifest_ref=f"artifact_manifest:{scenario_name}",
        )
        attempt = builder.build_attempt_trace(eligibility_trace=trace, attempt_id=f"attempt:{scenario_name}")
        scenarios[scenario_name] = _scenario_result(
            scenario_name,
            trace.eligible is False and reason in trace.blocking_reasons and attempt.attempted is False,
            eligibility=trace.to_dict(),
            attempt=attempt.to_dict(),
        )

    missing_qc = builder.build_eligibility_trace(
        run_id="run_missing_qc",
        content_id="content_missing_qc",
        qc_status="APPROVE",
        qc_publishable=True,
        qc_trace_ref=None,
        account_health_decision="SAFE",
        health_trace_ref="health_trace:missing_qc",
        strategy_ref="strategy:missing_qc",
        artifact_manifest_ref="artifact_manifest:missing_qc",
    )
    missing_qc_hooks = builder.build_incident_hooks(
        eligibility_trace=missing_qc,
        attempt_trace=builder.build_attempt_trace(eligibility_trace=missing_qc, attempt_id="attempt:missing_qc"),
        result_trace=builder.build_result_trace(
            attempt_trace=builder.build_attempt_trace(eligibility_trace=missing_qc, attempt_id="attempt:missing_qc")
        ),
    )
    scenarios["missing_qc_trace_blocks_or_degrades"] = _scenario_result(
        "missing_qc_trace_blocks_or_degrades",
        missing_qc.eligible is False
        and "MISSING_QC_TRACE" in missing_qc.blocking_reasons
        and "MISSING_QC_TRACE" in {hook.incident_type for hook in missing_qc_hooks},
        eligibility=missing_qc.to_dict(),
        incident_hooks=[hook.to_dict() for hook in missing_qc_hooks],
    )

    missing_artifact = builder.build_eligibility_trace(
        run_id="run_missing_artifact",
        content_id="content_missing_artifact",
        qc_status="APPROVE",
        qc_publishable=True,
        qc_trace_ref="qc_trace:missing_artifact",
        account_health_decision="SAFE",
        health_trace_ref="health_trace:missing_artifact",
        strategy_ref="strategy:missing_artifact",
        artifact_manifest_ref=None,
    )
    missing_artifact_attempt = builder.build_attempt_trace(
        eligibility_trace=missing_artifact,
        attempt_id="attempt:missing_artifact",
    )
    missing_artifact_result = builder.build_result_trace(attempt_trace=missing_artifact_attempt)
    missing_artifact_hooks = builder.build_incident_hooks(
        eligibility_trace=missing_artifact,
        attempt_trace=missing_artifact_attempt,
        result_trace=missing_artifact_result,
    )
    scenarios["missing_artifact_manifest_blocks_eligibility"] = _scenario_result(
        "missing_artifact_manifest_blocks_eligibility",
        missing_artifact.eligible is False
        and "MISSING_ARTIFACT_MANIFEST" in missing_artifact.blocking_reasons
        and "MISSING_ARTIFACT_MANIFEST" in {hook.incident_type for hook in missing_artifact_hooks},
        eligibility=missing_artifact.to_dict(),
        incident_hooks=[hook.to_dict() for hook in missing_artifact_hooks],
    )

    dry_run = _base_bundle(builder, content_id="content_dry_run", dry_run=True).to_dict()
    scenarios["dry_run_does_not_publish"] = _scenario_result(
        "dry_run_does_not_publish",
        dry_run["publish_attempt_trace"]["attempted"] is False
        and dry_run["publish_attempt_trace"]["publish_target"] is None
        and dry_run["publish_result_trace"]["result_status"] != "succeeded"
        and dry_run["publish_result_trace"]["published_url"] is None
        and dry_run["publish_result_trace"]["platform_content_id"] is None,
        trace=dry_run,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "nested" / "publish_lifecycle.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{"sentinel": true}\n', encoding="utf-8")
        writer = PublishLifecycleWriter(target)
        writer.append_event(bundle.publish_lifecycle_event)
        writer.append_event(_base_bundle(builder, content_id="content_gate_2").publish_lifecycle_event)
        lines = target.read_text(encoding="utf-8").splitlines()
        events = [json.loads(line) for line in lines]
        scenarios["append_only_writer_preserves_existing_events"] = _scenario_result(
            "append_only_writer_preserves_existing_events",
            len(events) == 3
            and events[0] == {"sentinel": True}
            and all(isinstance(event, dict) for event in events),
            line_count=len(events),
            events=events,
        )

    eligibility_failed = builder.build_eligibility_trace(
        run_id="run_failed_attempt",
        content_id="content_failed_attempt",
        qc_status="APPROVE",
        qc_publishable=True,
        qc_trace_ref="qc_trace:failed_attempt",
        account_health_decision="SAFE",
        health_trace_ref="health_trace:failed_attempt",
        strategy_ref="strategy:failed_attempt",
        artifact_manifest_ref="artifact_manifest:failed_attempt",
        dry_run=False,
    )
    attempt_failed = builder.build_attempt_trace(
        eligibility_trace=eligibility_failed,
        attempt_id="attempt:failed_attempt",
        dry_run=False,
        simulate_failure=True,
    )
    result_failed = builder.build_result_trace(attempt_trace=attempt_failed)
    failed_hooks = builder.build_incident_hooks(
        eligibility_trace=eligibility_failed,
        attempt_trace=attempt_failed,
        result_trace=result_failed,
    )
    scenarios["publish_attempt_failed_emits_incident_hook"] = _scenario_result(
        "publish_attempt_failed_emits_incident_hook",
        result_failed.result_status == "failed"
        and "PUBLISH_ATTEMPT_FAILED" in {hook.incident_type for hook in failed_hooks},
        result=result_failed.to_dict(),
        incident_hooks=[hook.to_dict() for hook in failed_hooks],
    )

    ok, _, error = _safe_call(lambda: builder.build_result_trace(
        attempt_trace=bundle.publish_attempt_trace,
        result_status="succeeded",
        result_evidence_available=False,
    ))
    scenarios["fake_success_without_evidence_rejected"] = _scenario_result(
        "fake_success_without_evidence_rejected",
        ok is False and "PUBLISH_SUCCESS_REQUIRES_RESULT_EVIDENCE" in str(error),
        error=error,
    )

    ok, _, error = _safe_call(lambda: builder.build_result_trace(
        attempt_trace=bundle.publish_attempt_trace,
        result_status="pending",
        published_url="https://example.invalid/fake",
        result_evidence_available=False,
    ))
    scenarios["fake_url_without_evidence_rejected"] = _scenario_result(
        "fake_url_without_evidence_rejected",
        ok is False and "PUBLISH_EXTERNAL_IDENTITY_REQUIRES_RESULT_EVIDENCE" in str(error),
        error=error,
    )

    ok, _, error = _safe_call(lambda: builder.build_result_trace(
        attempt_trace=bundle.publish_attempt_trace,
        result_status="pending",
        platform_content_id="fake-platform-id",
        result_evidence_available=False,
    ))
    scenarios["fake_platform_id_without_evidence_rejected"] = _scenario_result(
        "fake_platform_id_without_evidence_rejected",
        ok is False and "PUBLISH_EXTERNAL_IDENTITY_REQUIRES_RESULT_EVIDENCE" in str(error),
        error=error,
    )

    non_dry_run_attempt = builder.build_attempt_trace(
        eligibility_trace=eligibility_failed,
        attempt_id="attempt:pending",
        dry_run=False,
        simulate_failure=False,
    )
    pending_result = builder.build_result_trace(attempt_trace=non_dry_run_attempt)
    scenarios["pending_result_not_treated_as_success"] = _scenario_result(
        "pending_result_not_treated_as_success",
        pending_result.result_status == "pending"
        and pending_result.result_evidence_available is False
        and pending_result.published_url is None
        and pending_result.platform_content_id is None,
        result=pending_result.to_dict(),
    )

    normalized_attempt = builder.build_attempt_trace(
        eligibility_trace=eligibility_failed,
        attempt_id="attempt:normalize",
        dry_run=False,
        simulate_failure=True,
        failure_reason="unexpected_reason",
    )
    scenarios["skip_failure_reason_normalization"] = _scenario_result(
        "skip_failure_reason_normalization",
        normalized_attempt.failure_reason == "UNKNOWN_INTERNAL_FAILURE",
        attempt=normalized_attempt.to_dict(),
    )

    first = _base_bundle(builder, content_id="content_det").to_dict()
    second = _base_bundle(builder, content_id="content_det").to_dict()
    scenarios["determinism_replay"] = _scenario_result(
        "determinism_replay",
        first == second,
        first=first,
        second=second,
    )

    scenarios["backward_compatibility"] = _scenario_result(
        "backward_compatibility",
        all(path.exists() for path in REQUIRED_DOCS)
        and REQUIRED_TRACE_KEYS.issubset(set(payload.keys())),
        required_docs={str(path.relative_to(ROOT)): path.exists() for path in REQUIRED_DOCS},
        trace_keys=sorted(payload.keys()),
    )
    return scenarios


def _checklist(scenarios: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    builder = PublishTraceBuilder()
    bundle = _base_bundle(builder)
    payload = bundle.to_dict()
    valid, failures = builder.validate_trace_bundle(bundle)
    serialized = json.dumps(payload, sort_keys=True)

    return {
        "trace_builders_present": {
            "passed": callable(getattr(builder, "build_trace_bundle", None))
            and callable(getattr(builder, "build_eligibility_trace", None))
            and callable(getattr(builder, "build_attempt_trace", None))
            and callable(getattr(builder, "build_result_trace", None)),
        },
        "eligibility_trace_complete": {
            "passed": not _missing(payload["publish_eligibility_trace"], {
                "trace_version",
                "run_id",
                "content_id",
                "eligibility_checked",
                "eligible",
                "qc_dependency",
                "account_health_dependency",
                "strategy_dependency",
                "artifact_dependency",
                "policy_dependency",
                "blocking_reasons",
                "rationale",
            }),
        },
        "attempt_trace_complete": {
            "passed": not _missing(payload["publish_attempt_trace"], {
                "attempt_id",
                "run_id",
                "content_id",
                "attempted",
                "attempt_status",
                "preconditions_satisfied",
                "skip_reason",
                "failure_reason",
            }),
        },
        "result_trace_complete": {
            "passed": not _missing(payload["publish_result_trace"], {
                "attempt_id",
                "content_id",
                "result_status",
                "published_url",
                "platform_content_id",
                "result_evidence_available",
                "rationale",
            }),
        },
        "lifecycle_event_complete": {
            "passed": not _missing(payload["publish_lifecycle_event"], {
                "publish_event_id",
                "event_type",
                "eligibility",
                "attempt",
                "result",
                "boundary_statement",
            }),
        },
        "lifecycle_writer_append_only": {
            "passed": scenarios["append_only_writer_preserves_existing_events"]["passed"] is True,
        },
        "dry_run_has_no_publish_side_effects": {
            "passed": scenarios["dry_run_does_not_publish"]["passed"] is True,
        },
        "account_health_hold_blocks_eligibility": {
            "passed": scenarios["account_health_hold_blocks_eligibility"]["passed"] is True,
        },
        "qc_reject_blocks_eligibility": {
            "passed": scenarios["qc_reject_blocks_eligibility"]["passed"] is True,
        },
        "qc_hold_blocks_eligibility": {
            "passed": scenarios["qc_hold_blocks_eligibility"]["passed"] is True,
        },
        "qc_non_publishable_blocks_eligibility": {
            "passed": scenarios["qc_not_publishable_blocks_eligibility"]["passed"] is True,
        },
        "missing_evidence_not_success": {
            "passed": scenarios["fake_success_without_evidence_rejected"]["passed"] is True
            and scenarios["pending_result_not_treated_as_success"]["passed"] is True,
        },
        "fake_success_rejected": {
            "passed": scenarios["fake_success_without_evidence_rejected"]["passed"] is True,
        },
        "fake_url_or_platform_id_rejected": {
            "passed": scenarios["fake_url_without_evidence_rejected"]["passed"] is True
            and scenarios["fake_platform_id_without_evidence_rejected"]["passed"] is True,
        },
        "incident_hooks_present": {
            "passed": scenarios["publish_attempt_failed_emits_incident_hook"]["passed"] is True
            and scenarios["missing_qc_trace_blocks_or_degrades"]["passed"] is True
            and scenarios["missing_artifact_manifest_blocks_eligibility"]["passed"] is True,
        },
        "skip_failure_normalization_valid": {
            "passed": scenarios["skip_failure_reason_normalization"]["passed"] is True,
        },
        "determinism_where_required": {
            "passed": scenarios["determinism_replay"]["passed"] is True,
        },
        "boundary_preserved": {
            "passed": payload["boundary_statement"] == BOUNDARY_STATEMENT
            and payload["publish_lifecycle_event"]["boundary_statement"] == BOUNDARY_STATEMENT,
        },
        "no_core_or_upstream_mutation": {
            "passed": "app.content.pipeline.publish" not in serialized
            and "strategy_override" not in serialized
            and "qc_override" not in serialized,
        },
        "trace_bundle_valid": {
            "passed": valid and not failures,
            "validation_failures": failures,
        },
        "no_performance_prediction_authority": {
            "passed": not any(term in serialized for term in ["expected_performance", "forecast", "predicted"]),
        },
    }


def _missing(payload: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(key for key in required if key not in payload)


def _blocking_failures(scenarios: dict[str, dict[str, Any]], checklist: dict[str, dict[str, Any]]) -> list[str]:
    failures = [f"scenario:{name}" for name, result in scenarios.items() if result.get("passed") is not True]
    failures.extend(f"checklist:{name}" for name, result in checklist.items() if result.get("passed") is not True)
    return list(dict.fromkeys(failures))


def _metrics(scenarios: dict[str, dict[str, Any]], checklist: dict[str, dict[str, Any]], blocking: list[str]) -> dict[str, Any]:
    return {
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(1 for result in scenarios.values() if result.get("passed") is True),
        "checklist_count": len(checklist),
        "checklist_pass_count": sum(1 for result in checklist.values() if result.get("passed") is True),
        "critical_failures": len(blocking),
        "blocking_failures_count": len(blocking),
        "silent_failures_detected": bool(blocking),
        "fake_success_accepted": scenarios["fake_success_without_evidence_rejected"]["passed"] is not True,
        "fake_url_or_platform_id_accepted": (
            scenarios["fake_url_without_evidence_rejected"]["passed"] is not True
            or scenarios["fake_platform_id_without_evidence_rejected"]["passed"] is not True
        ),
        "account_health_hold_override_detected": scenarios["account_health_hold_blocks_eligibility"]["passed"] is not True,
        "qc_bypass_detected": (
            scenarios["qc_reject_blocks_eligibility"]["passed"] is not True
            or scenarios["qc_hold_blocks_eligibility"]["passed"] is not True
            or scenarios["qc_not_publishable_blocks_eligibility"]["passed"] is not True
        ),
        "non_determinism_detected": scenarios["determinism_replay"]["passed"] is not True,
    }


def _derive_verdict(blocking: list[str], residuals: list[str]) -> str:
    if blocking:
        return "HOLD"
    if residuals:
        return "GO_WITH_MONITORING"
    return "GO"


def _dimensions(checklist: dict[str, dict[str, Any]]) -> dict[str, Any]:
    dimension_names = [
        "trace_builders_present",
        "eligibility_trace_complete",
        "attempt_trace_complete",
        "result_trace_complete",
        "lifecycle_event_complete",
        "lifecycle_writer_append_only",
        "dry_run_has_no_publish_side_effects",
        "account_health_hold_blocks_eligibility",
        "qc_non_publishable_blocks_eligibility",
        "missing_evidence_not_success",
        "fake_success_rejected",
        "fake_url_or_platform_id_rejected",
        "incident_hooks_present",
        "determinism_where_required",
        "boundary_preserved",
    ]
    return {name: checklist.get(name, {}).get("passed") is True for name in dimension_names}


def main() -> int:
    _reset_audit_dir()
    scenarios = _run_scenarios()
    checklist = _checklist(scenarios)
    blocking = _blocking_failures(scenarios, checklist)
    residuals = [] if blocking else [
        "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
        "PLATFORM_INTEGRATION_NOT_ENABLED",
        "PUBLISH_RESULT_HISTORY_STILL_SHORT",
        "PUBLISH_INCIDENT_HISTORY_STILL_SHORT",
    ]
    verdict = _derive_verdict(blocking, residuals)
    metrics = _metrics(scenarios, checklist, blocking)
    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "PUBLISHER_TRACE_IMPLEMENTATION_GATE",
        "timestamp": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "verdict": verdict,
        **_dimensions(checklist),
        "silent_failures_detected": metrics["silent_failures_detected"],
        "scenario_results": {
            name: {
                "passed": result.get("passed"),
                "summary": {
                    key: value
                    for key, value in result.items()
                    if key not in {"scenario", "passed", "trace", "first", "second", "events"}
                },
            }
            for name, result in scenarios.items()
        },
        "checklist_results": checklist,
        "metrics": metrics,
        "blocking_failures": blocking,
        "residual_monitoring": residuals,
        "recommendation": (
            "PROCEED_TO_PUBLISHER_DRY_RUN_OPERATIONAL_EVIDENCE_PLAN"
            if verdict in {"GO", "GO_WITH_MONITORING"}
            else "HOLD_BEFORE_PUBLISHER_TRACE_USAGE"
        ),
    }

    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)
    print(json.dumps({
        "verdict": verdict,
        "scenarios": f"{metrics['scenario_pass_count']}/{metrics['scenario_count']}",
        "checklist": f"{metrics['checklist_pass_count']}/{metrics['checklist_count']}",
        "blocking_failures": blocking,
        "residual_monitoring": residuals,
        "recommendation": final_verdict["recommendation"],
        "final_verdict": str(FINAL_VERDICT_PATH),
    }, indent=2))
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
