from __future__ import annotations

import copy
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "publisher_governance_and_publish_trace_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"

BOUNDARY_STATEMENT = (
    "Publisher is explicit publish authority; QC evaluates artifact quality; "
    "Strategy controls creative direction; Account Health can block via HOLD."
)

ALLOWED_SKIP_REASONS = {
    "ACCOUNT_HEALTH_HOLD",
    "QC_REJECTED",
    "QC_HOLD",
    "QC_NOT_PUBLISHABLE",
    "MISSING_QC_TRACE",
    "MISSING_ARTIFACT_MANIFEST",
    "MISSING_VIDEO_ARTIFACT",
    "MISSING_STRATEGY_CONTEXT",
    "RUNTIME_POLICY_BLOCKED",
    "PUBLISH_TARGET_NOT_CONFIGURED",
    "MANUAL_APPROVAL_REQUIRED",
    "DRY_RUN_MODE",
    "UNKNOWN_PRECONDITION",
}

ALLOWED_FAILURE_REASONS = {
    "PUBLISH_TARGET_ERROR",
    "AUTHENTICATION_FAILURE",
    "UPLOAD_FAILURE",
    "PLATFORM_REJECTION",
    "ARTIFACT_READ_FAILURE",
    "METADATA_VALIDATION_FAILURE",
    "NETWORK_FAILURE",
    "RATE_LIMITED",
    "UNKNOWN_EXTERNAL_FAILURE",
    "UNKNOWN_INTERNAL_FAILURE",
}

FORBIDDEN_KEY_FRAGMENTS = {
    "predicted",
    "forecast",
    "expected_performance",
    "performance_prediction",
    "likely_to_perform",
    "future_score",
}

REQUIRED_DOCS = {
    "phase_3_plan": "docs/runtime/phase-3/PHASE_3_OPERATIONAL_GOVERNANCE_AND_MATURITY_PLAN.md",
    "runtime_evidence_plan": "docs/runtime/phase-3/monitoring/PRODUCTION_MONITORING_AND_RUNTIME_EVIDENCE_PLAN.md",
    "publisher_trace_plan": "docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_PLAN.md",
    "publisher_gate_plan": "docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE_PLAN.md",
    "publisher_gate_doc": "docs/runtime/publisher/governance/PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE.md",
}

REQUIRED_JSON_ARTIFACTS = {
    "phase_2_6_final_master_gate": "OUT/audit/phase_2_6_final_master_gate/final_verdict.json",
}


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR, ignore_errors=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:  # noqa: BLE001
        return {}, f"{type(exc).__name__}: {exc}"


def _authority_model() -> dict[str, Any]:
    return {
        "publisher": {
            "authority": "decides whether a publish attempt is made",
            "must_consume": [
                "qc_decision",
                "qc_publishable",
                "account_health_decision",
                "strategy_profile",
                "artifact_manifest",
                "runtime_policy",
            ],
            "must_emit": [
                "publish_eligibility_trace",
                "publish_attempt_trace",
                "publish_result_trace",
            ],
        },
        "video_qc": {
            "authority": "evaluates final artifact",
            "must_not": ["publish", "schedule_publish", "override_publisher", "override_account_health"],
        },
        "account_health": {
            "authority": "SAFE | CAUTION | HOLD posture",
            "hold_must_not_be_overridden_by_publisher": True,
        },
        "strategy": {
            "authority": "control layer creative strategy",
            "must_not_publish": True,
        },
    }


def _scenario_config(name: str) -> dict[str, Any]:
    base = {
        "scenario": name,
        "run_id": "publisher_gate_run",
        "content_id": "publisher_gate_content",
        "qc_status": "APPROVE",
        "qc_publishable": True,
        "qc_trace_available": True,
        "account_health_decision": "SAFE",
        "strategy_available": True,
        "artifact_manifest_available": True,
        "video_available": True,
        "metadata_available": True,
        "policy_allows_publish": True,
        "dry_run": False,
        "simulate_failure": False,
        "simulate_pending": False,
        "mutations": {},
    }
    overrides = {
        "blocked_by_account_health_hold": {"account_health_decision": "HOLD"},
        "blocked_by_qc_reject": {"qc_status": "REJECT", "qc_publishable": False},
        "blocked_by_qc_hold": {"qc_status": "HOLD", "qc_publishable": False},
        "blocked_by_qc_not_publishable": {"qc_status": "APPROVE", "qc_publishable": False},
        "missing_qc_trace": {"qc_trace_available": False, "qc_status": "UNKNOWN", "qc_publishable": False},
        "missing_artifact_manifest": {"artifact_manifest_available": False},
        "dry_run_skipped": {"dry_run": True},
        "publish_attempt_failed": {"simulate_failure": True},
        "publish_result_pending": {"simulate_pending": True},
        "fake_success_without_evidence_must_fail": {
            "mutations": {
                "result_status": "succeeded",
                "result_evidence_available": False,
                "published_url": None,
                "platform_content_id": None,
            }
        },
        "fake_url_without_evidence_must_fail": {
            "mutations": {
                "result_status": "pending",
                "result_evidence_available": False,
                "published_url": "https://example.invalid/fake",
                "platform_content_id": "fake-platform-id",
            }
        },
    }
    base.update(overrides.get(name, {}))
    return base


def _skip_reason(config: dict[str, Any]) -> str | None:
    if config["account_health_decision"] == "HOLD":
        return "ACCOUNT_HEALTH_HOLD"
    if not config["qc_trace_available"]:
        return "MISSING_QC_TRACE"
    if config["qc_status"] == "REJECT":
        return "QC_REJECTED"
    if config["qc_status"] == "HOLD":
        return "QC_HOLD"
    if config["qc_status"] == "APPROVE" and not config["qc_publishable"]:
        return "QC_NOT_PUBLISHABLE"
    if not config["artifact_manifest_available"]:
        return "MISSING_ARTIFACT_MANIFEST"
    if not config["video_available"]:
        return "MISSING_VIDEO_ARTIFACT"
    if not config["strategy_available"]:
        return "MISSING_STRATEGY_CONTEXT"
    if not config["policy_allows_publish"]:
        return "RUNTIME_POLICY_BLOCKED"
    if config["dry_run"]:
        return "DRY_RUN_MODE"
    return None


def _build_trace(config: dict[str, Any]) -> dict[str, Any]:
    reason = _skip_reason(config)
    eligible = reason is None
    eligibility = {
        "trace_version": "publisher_governance_v1",
        "run_id": config["run_id"],
        "content_id": config["content_id"],
        "eligibility_checked": True,
        "eligible": eligible,
        "qc_dependency": {
            "qc_status": config["qc_status"],
            "qc_publishable": config["qc_publishable"],
            "qc_trace_ref": "qc_trace:publisher_gate" if config["qc_trace_available"] else None,
            "qc_dependency_satisfied": config["qc_trace_available"] and config["qc_status"] == "APPROVE" and config["qc_publishable"],
        },
        "account_health_dependency": {
            "decision": config["account_health_decision"],
            "hold_detected": config["account_health_decision"] == "HOLD",
            "health_trace_ref": "health_trace:publisher_gate",
            "hold_blocks_publish": True,
        },
        "strategy_dependency": {
            "strategy_ref": "strategy:publisher_gate" if config["strategy_available"] else None,
            "strategy_available": config["strategy_available"],
        },
        "artifact_dependency": {
            "artifact_manifest_ref": "artifact_manifest:publisher_gate" if config["artifact_manifest_available"] else None,
            "video_available": config["video_available"],
            "metadata_available": config["metadata_available"],
        },
        "policy_dependency": {
            "runtime_policy_ref": "runtime_policy:publisher_gate",
            "policy_allows_publish": config["policy_allows_publish"],
        },
        "blocking_reasons": [] if eligible else [reason],
        "warnings": ["PUBLISHER_GATE_IS_DRY_RUN_ONLY"],
        "rationale": ["Eligibility is derived from QC, Account Health, Strategy, artifact and policy dependencies."],
    }
    attempted = eligible and not config["dry_run"]
    attempt_status = "attempted" if attempted else "not_attempted"
    failure_reason = None
    if config["simulate_failure"]:
        attempted = True
        attempt_status = "failed"
        failure_reason = "PUBLISH_TARGET_ERROR"
    attempt = {
        "attempt_id": "attempt:publisher_gate",
        "run_id": config["run_id"],
        "content_id": config["content_id"],
        "timestamp": "2026-04-27T00:00:00-03:00",
        "attempted": attempted,
        "publish_target": "dry_run_target" if attempted else None,
        "artifact_manifest_ref": eligibility["artifact_dependency"]["artifact_manifest_ref"],
        "eligibility_trace_ref": "publish_eligibility_trace:publisher_gate",
        "preconditions_satisfied": eligible,
        "fallback_used": False,
        "attempt_status": attempt_status,
        "skip_reason": "DRY_RUN_MODE" if config["dry_run"] else (None if eligible else reason),
        "failure_reason": failure_reason,
        "rationale": ["Publisher attempt state is represented without executing publication."],
    }
    result_status = "not_attempted"
    result_evidence_available = False
    published_url = None
    platform_content_id = None
    result_failure_reason = None
    result_skip_reason = attempt["skip_reason"]
    if config["simulate_failure"]:
        result_status = "failed"
        result_failure_reason = failure_reason
        result_skip_reason = None
    elif config["simulate_pending"]:
        result_status = "pending"
        result_skip_reason = None
    elif attempted:
        result_status = "pending"
        result_skip_reason = None
    result = {
        "attempt_id": attempt["attempt_id"],
        "content_id": config["content_id"],
        "observed_at": "2026-04-27T00:00:00-03:00",
        "result_status": result_status,
        "published_url": published_url,
        "platform_content_id": platform_content_id,
        "failure_reason": result_failure_reason,
        "skip_reason": result_skip_reason,
        "result_evidence_ref": None,
        "result_evidence_available": result_evidence_available,
        "rationale": ["Publish result is not treated as success without explicit result evidence."],
    }
    for key, value in config.get("mutations", {}).items():
        result[key] = value
    lifecycle = {
        "publish_event_id": "publish_event:publisher_gate",
        "run_id": config["run_id"],
        "content_id": config["content_id"],
        "timestamp": "2026-04-27T00:00:00-03:00",
        "event_type": _event_type(result),
        "eligibility": eligibility,
        "attempt": attempt,
        "result": result,
        "qc_dependency": eligibility["qc_dependency"],
        "account_health_dependency": eligibility["account_health_dependency"],
        "strategy_dependency": eligibility["strategy_dependency"],
        "artifact_refs": [eligibility["artifact_dependency"]["artifact_manifest_ref"]] if eligibility["artifact_dependency"]["artifact_manifest_ref"] else [],
        "fallback_used": False,
        "skip_reason": attempt["skip_reason"] or result["skip_reason"],
        "failure_reason": attempt["failure_reason"] or result["failure_reason"],
        "boundary_statement": BOUNDARY_STATEMENT,
    }
    incident_hooks = _incident_hooks(lifecycle)
    return {
        "publisher_authority_model": _authority_model(),
        "publish_eligibility_trace": eligibility,
        "publish_attempt_trace": attempt,
        "publish_result_trace": result,
        "publish_lifecycle_event": lifecycle,
        "incident_hooks": incident_hooks,
        "boundary_statement": BOUNDARY_STATEMENT,
    }


def _event_type(result: dict[str, Any]) -> str:
    status = result.get("result_status")
    if status == "succeeded":
        return "PUBLISH_SUCCEEDED"
    if status == "failed":
        return "PUBLISH_FAILED"
    if status == "pending":
        return "PUBLISH_ATTEMPTED"
    if status == "skipped":
        return "PUBLISH_SKIPPED"
    return "PUBLISH_ELIGIBILITY_CHECKED"


def _incident_hooks(lifecycle: dict[str, Any]) -> list[dict[str, Any]]:
    hooks: list[dict[str, Any]] = []
    eligibility = lifecycle["eligibility"]
    attempt = lifecycle["attempt"]
    result = lifecycle["result"]
    if eligibility["account_health_dependency"]["hold_detected"] and attempt["attempted"]:
        hooks.append({"incident_type": "ACCOUNT_HEALTH_HOLD_OVERRIDE_ATTEMPT", "severity": "critical"})
    if not eligibility["qc_dependency"]["qc_dependency_satisfied"] and attempt["attempted"]:
        hooks.append({"incident_type": "QC_BYPASS_ATTEMPT", "severity": "critical"})
    if result["result_status"] == "failed":
        hooks.append({"incident_type": "PUBLISH_ATTEMPT_FAILED", "severity": "warning"})
    if result["result_status"] == "succeeded" and not result["result_evidence_available"]:
        hooks.append({"incident_type": "PUBLISH_SUCCESS_WITHOUT_EVIDENCE", "severity": "critical"})
    if result["result_status"] != "succeeded" and (result.get("published_url") or result.get("platform_content_id")):
        hooks.append({"incident_type": "FAKE_URL_OR_PLATFORM_ID", "severity": "critical"})
    return hooks


def _missing_keys(payload: dict[str, Any], keys: set[str]) -> list[str]:
    return sorted(key for key in keys if key not in payload)


def _validate_trace(trace: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    eligibility = trace.get("publish_eligibility_trace", {})
    attempt = trace.get("publish_attempt_trace", {})
    result = trace.get("publish_result_trace", {})
    lifecycle = trace.get("publish_lifecycle_event", {})
    failures.extend(f"eligibility_missing:{key}" for key in _missing_keys(eligibility, {
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
        "warnings",
        "rationale",
    }))
    failures.extend(f"attempt_missing:{key}" for key in _missing_keys(attempt, {
        "attempt_id",
        "run_id",
        "content_id",
        "timestamp",
        "attempted",
        "publish_target",
        "artifact_manifest_ref",
        "eligibility_trace_ref",
        "preconditions_satisfied",
        "fallback_used",
        "attempt_status",
        "skip_reason",
        "failure_reason",
        "rationale",
    }))
    failures.extend(f"result_missing:{key}" for key in _missing_keys(result, {
        "attempt_id",
        "content_id",
        "observed_at",
        "result_status",
        "published_url",
        "platform_content_id",
        "failure_reason",
        "skip_reason",
        "result_evidence_ref",
        "result_evidence_available",
        "rationale",
    }))
    failures.extend(f"lifecycle_missing:{key}" for key in _missing_keys(lifecycle, {
        "publish_event_id",
        "run_id",
        "content_id",
        "timestamp",
        "event_type",
        "eligibility",
        "attempt",
        "result",
        "qc_dependency",
        "account_health_dependency",
        "strategy_dependency",
        "artifact_refs",
        "fallback_used",
        "skip_reason",
        "failure_reason",
        "boundary_statement",
    }))
    failures.extend(_semantic_failures(trace))
    return not failures, failures


def _semantic_failures(trace: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    eligibility = trace["publish_eligibility_trace"]
    attempt = trace["publish_attempt_trace"]
    result = trace["publish_result_trace"]
    lifecycle = trace["publish_lifecycle_event"]
    skip_reason = attempt.get("skip_reason") or result.get("skip_reason") or lifecycle.get("skip_reason")
    failure_reason = attempt.get("failure_reason") or result.get("failure_reason") or lifecycle.get("failure_reason")
    if skip_reason and skip_reason not in ALLOWED_SKIP_REASONS:
        failures.append(f"invalid_skip_reason:{skip_reason}")
    if failure_reason and failure_reason not in ALLOWED_FAILURE_REASONS:
        failures.append(f"invalid_failure_reason:{failure_reason}")
    if eligibility["account_health_dependency"]["hold_detected"] and attempt["attempted"]:
        failures.append("account_health_hold_override")
    if not eligibility["qc_dependency"]["qc_dependency_satisfied"] and attempt["attempted"]:
        failures.append("qc_dependency_bypass")
    if not eligibility["eligible"] and attempt["attempted"]:
        failures.append("hidden_publish_bypass")
    if result["result_status"] == "succeeded" and not result["result_evidence_available"]:
        failures.append("fabricated_publish_success")
    if result["result_status"] != "succeeded" and (result.get("published_url") or result.get("platform_content_id")):
        failures.append("fake_url_or_platform_id")
    if result["result_status"] in {"pending", "unknown", "not_attempted"} and result.get("result_evidence_available"):
        failures.append("missing_or_pending_evidence_marked_available")
    if lifecycle.get("boundary_statement") != BOUNDARY_STATEMENT:
        failures.append("boundary_statement_missing_or_incomplete")
    if _forbidden_keys(trace):
        failures.append("performance_prediction_authority_detected")
    return failures


def _forbidden_keys(payload: Any) -> list[str]:
    found: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in FORBIDDEN_KEY_FRAGMENTS):
                found.append(str(key))
            found.extend(_forbidden_keys(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_forbidden_keys(item))
    return found


def _scenario_expectation(name: str) -> str:
    if name in {"fake_success_without_evidence_must_fail", "fake_url_without_evidence_must_fail"}:
        return "must_be_rejected"
    return "must_be_valid"


def _run_scenario(name: str) -> dict[str, Any]:
    trace = _build_trace(_scenario_config(name))
    valid, failures = _validate_trace(trace)
    expectation = _scenario_expectation(name)
    passed = valid if expectation == "must_be_valid" else not valid
    return {
        "scenario": name,
        "passed": passed,
        "expectation": expectation,
        "trace_valid": valid,
        "validation_failures": failures,
        "summary": {
            "eligible": trace["publish_eligibility_trace"]["eligible"],
            "attempted": trace["publish_attempt_trace"]["attempted"],
            "attempt_status": trace["publish_attempt_trace"]["attempt_status"],
            "result_status": trace["publish_result_trace"]["result_status"],
            "skip_reason": trace["publish_attempt_trace"]["skip_reason"] or trace["publish_result_trace"]["skip_reason"],
            "failure_reason": trace["publish_attempt_trace"]["failure_reason"] or trace["publish_result_trace"]["failure_reason"],
            "incident_hooks": trace["incident_hooks"],
        },
        "trace": trace,
    }


def _run_scenarios() -> dict[str, Any]:
    scenario_names = [
        "eligible_publish_candidate",
        "blocked_by_account_health_hold",
        "blocked_by_qc_reject",
        "blocked_by_qc_hold",
        "blocked_by_qc_not_publishable",
        "missing_qc_trace",
        "missing_artifact_manifest",
        "dry_run_skipped",
        "publish_attempt_failed",
        "publish_result_pending",
        "fake_success_without_evidence_must_fail",
        "fake_url_without_evidence_must_fail",
    ]
    scenarios = {name: _run_scenario(name) for name in scenario_names}
    replay_one = _run_scenario("eligible_publish_candidate")
    replay_two = _run_scenario("eligible_publish_candidate")
    scenarios["determinism_replay"] = {
        "scenario": "determinism_replay",
        "passed": replay_one["trace"] == replay_two["trace"],
        "first_summary": replay_one["summary"],
        "second_summary": replay_two["summary"],
    }
    scenarios["backward_compatibility"] = {
        "scenario": "backward_compatibility",
        "passed": _all_serializable(scenarios) and _preconditions_present()[0],
        "summary": {
            "controlled_trace_only": True,
            "publishing_implemented": False,
            "runtime_mutated": False,
        },
    }
    return scenarios


def _all_serializable(payload: Any) -> bool:
    try:
        json.dumps(payload)
        return True
    except TypeError:
        return False


def _preconditions_present() -> tuple[bool, dict[str, Any]]:
    doc_status = {name: (ROOT / path).exists() for name, path in REQUIRED_DOCS.items()}
    artifact_status: dict[str, Any] = {}
    json_errors: dict[str, str] = {}
    for name, rel_path in REQUIRED_JSON_ARTIFACTS.items():
        path = ROOT / rel_path
        exists = path.exists()
        artifact_status[name] = exists
        if exists:
            _, error = _load_json(path)
            if error:
                json_errors[name] = error
    return all(doc_status.values()) and all(artifact_status.values()) and not json_errors, {
        "docs": doc_status,
        "artifacts": artifact_status,
        "json_errors": json_errors,
    }


def _checklist(scenarios: dict[str, Any]) -> dict[str, dict[str, Any]]:
    representative = scenarios["eligible_publish_candidate"]["trace"]
    eligibility = representative["publish_eligibility_trace"]
    attempt = representative["publish_attempt_trace"]
    result = representative["publish_result_trace"]
    lifecycle = representative["publish_lifecycle_event"]
    authority = representative["publisher_authority_model"]
    all_passed = all(item.get("passed") is True for item in scenarios.values())
    publish_failure_incidents = {
        hook.get("incident_type")
        for hook in scenarios["publish_attempt_failed"]["summary"].get("incident_hooks", [])
    }
    fake_success_incidents = {
        hook.get("incident_type")
        for hook in scenarios["fake_success_without_evidence_must_fail"]["summary"].get("incident_hooks", [])
    }
    fake_url_incidents = {
        hook.get("incident_type")
        for hook in scenarios["fake_url_without_evidence_must_fail"]["summary"].get("incident_hooks", [])
    }
    checklist = {
        "publisher_authority_model_valid": {
            "passed": authority["publisher"]["authority"] == "decides whether a publish attempt is made"
            and "publish" in authority["video_qc"]["must_not"]
            and authority["account_health"]["hold_must_not_be_overridden_by_publisher"] is True,
        },
        "publish_eligibility_trace_complete": {
            "passed": not _missing_keys(eligibility, {
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
            }),
        },
        "publish_attempt_trace_complete": {
            "passed": not _missing_keys(attempt, {
                "attempt_id",
                "attempted",
                "attempt_status",
                "preconditions_satisfied",
                "skip_reason",
                "failure_reason",
            }),
        },
        "publish_result_trace_complete": {
            "passed": not _missing_keys(result, {
                "attempt_id",
                "result_status",
                "published_url",
                "platform_content_id",
                "result_evidence_available",
            }),
        },
        "skip_reason_semantics_valid": {
            "passed": all(
                (scenario["summary"].get("skip_reason") in ALLOWED_SKIP_REASONS or scenario["summary"].get("skip_reason") is None)
                for scenario in scenarios.values()
                if "summary" in scenario
            ),
        },
        "failure_reason_semantics_valid": {
            "passed": all(
                (scenario["summary"].get("failure_reason") in ALLOWED_FAILURE_REASONS or scenario["summary"].get("failure_reason") is None)
                for scenario in scenarios.values()
                if "summary" in scenario
            ),
        },
        "qc_dependency_visible": {
            "passed": "qc_dependency" in eligibility and "qc_dependency" in lifecycle,
        },
        "account_health_hold_visible": {
            "passed": scenarios["blocked_by_account_health_hold"]["summary"]["skip_reason"] == "ACCOUNT_HEALTH_HOLD",
        },
        "publisher_boundary_statement_present": {
            "passed": lifecycle.get("boundary_statement") == BOUNDARY_STATEMENT,
        },
        "publish_lifecycle_schema_valid": {
            "passed": not _missing_keys(lifecycle, {
                "publish_event_id",
                "event_type",
                "eligibility",
                "attempt",
                "result",
                "boundary_statement",
            }),
        },
        "incident_hooks_defined": {
            "passed": (
                "PUBLISH_ATTEMPT_FAILED" in publish_failure_incidents
                and "PUBLISH_SUCCESS_WITHOUT_EVIDENCE" in fake_success_incidents
                and "FAKE_URL_OR_PLATFORM_ID" in fake_url_incidents
            ),
        },
        "no_hidden_publish_bypass": {
            "passed": all_passed and scenarios["blocked_by_account_health_hold"]["summary"]["attempted"] is False,
        },
        "no_qc_as_publisher_behavior": {
            "passed": "publish" in authority["video_qc"]["must_not"],
        },
        "no_account_health_hold_override": {
            "passed": scenarios["blocked_by_account_health_hold"]["summary"]["attempted"] is False,
        },
        "no_fabricated_publish_success": {
            "passed": scenarios["fake_success_without_evidence_must_fail"]["passed"] is True,
        },
        "no_fake_url_or_platform_id": {
            "passed": scenarios["fake_url_without_evidence_must_fail"]["passed"] is True,
        },
        "no_performance_prediction_authority": {
            "passed": not _forbidden_keys(scenarios),
        },
    }
    return checklist


def _dimension_results(checklist: dict[str, dict[str, Any]]) -> dict[str, bool]:
    return {name: result.get("passed") is True for name, result in checklist.items()}


def _blocking_failures(scenarios: dict[str, Any], checklist: dict[str, dict[str, Any]]) -> list[str]:
    failures = [
        f"scenario:{name}"
        for name, result in scenarios.items()
        if result.get("passed") is not True
    ]
    failures.extend(
        f"checklist:{name}"
        for name, result in checklist.items()
        if result.get("passed") is not True
    )
    return list(dict.fromkeys(failures))


def _metrics(scenarios: dict[str, Any], checklist: dict[str, dict[str, Any]], blocking_failures: list[str]) -> dict[str, Any]:
    return {
        "scenario_count": len(scenarios),
        "scenario_pass_count": sum(1 for result in scenarios.values() if result.get("passed") is True),
        "checklist_count": len(checklist),
        "checklist_pass_count": sum(1 for result in checklist.values() if result.get("passed") is True),
        "critical_failures": len(blocking_failures),
        "blocking_failures_count": len(blocking_failures),
        "silent_failures_detected": bool(blocking_failures),
        "fake_success_accepted": scenarios["fake_success_without_evidence_must_fail"]["passed"] is not True,
        "fake_url_or_platform_id_accepted": scenarios["fake_url_without_evidence_must_fail"]["passed"] is not True,
        "account_health_hold_override_detected": scenarios["blocked_by_account_health_hold"]["summary"]["attempted"] is True,
        "qc_as_publisher_detected": checklist["no_qc_as_publisher_behavior"]["passed"] is not True,
        "performance_prediction_authority_detected": checklist["no_performance_prediction_authority"]["passed"] is not True,
    }


def _derive_verdict(blocking_failures: list[str], residuals: list[str]) -> str:
    if blocking_failures:
        return "HOLD"
    if residuals:
        return "GO_WITH_MONITORING"
    return "GO"


def main() -> int:
    _reset_audit_dir()
    scenarios = _run_scenarios()
    checklist = _checklist(scenarios)
    blocking_failures = _blocking_failures(scenarios, checklist)
    residuals = [] if blocking_failures else [
        "PUBLISHER_RUNTIME_IMPLEMENTATION_NOT_STARTED",
        "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
    ]
    verdict = _derive_verdict(blocking_failures, residuals)
    metrics = _metrics(scenarios, checklist, blocking_failures)
    dimensions = _dimension_results(checklist)
    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "PUBLISHER_GOVERNANCE_AND_PUBLISH_TRACE_GATE",
        "timestamp": datetime.now().astimezone().replace(microsecond=0).isoformat(),
        "verdict": verdict,
        **dimensions,
        "scenario_results": {
            name: {
                "passed": result.get("passed"),
                "expectation": result.get("expectation"),
                "summary": result.get("summary", {}),
                "validation_failures": result.get("validation_failures", []),
            }
            for name, result in scenarios.items()
        },
        "checklist_results": checklist,
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": residuals,
        "recommendation": "PROCEED_TO_PUBLISHER_TRACE_IMPLEMENTATION_PLAN" if verdict in {"GO", "GO_WITH_MONITORING"} else "HOLD_BEFORE_PUBLISHER_TRACE_IMPLEMENTATION",
    }
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)
    print(json.dumps({
        "verdict": verdict,
        "scenarios": f"{metrics['scenario_pass_count']}/{metrics['scenario_count']}",
        "checklist": f"{metrics['checklist_pass_count']}/{metrics['checklist_count']}",
        "blocking_failures": blocking_failures,
        "residual_monitoring": residuals,
        "recommendation": final_verdict["recommendation"],
        "final_verdict": str(FINAL_VERDICT_PATH),
    }, indent=2))
    return 0 if verdict in {"GO", "GO_WITH_MONITORING"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
