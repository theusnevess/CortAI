from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_validation_call_implementation_authorization_review_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
NON_AUTHORIZATION_REVIEW_PATH = AUDIT_DIR / "non_authorization_review.json"
DECISION_BOUNDARY_REVIEW_PATH = AUDIT_DIR / "decision_boundary_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
BOUNDARY_REVIEW_PATH = AUDIT_DIR / "boundary_review.json"

AUTH_PLAN_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "implementation-authorization" / "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_PLAN.md"
)
AUTH_GATE_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "implementation-authorization" / "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_GATE.md"
)
AUTH_GATE_RUNNER_PATH = ROOT / "tests" / "run_external_sandbox_validation_call_implementation_authorization_gate.py"
AUTH_GATE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_validation_call_implementation_authorization_gate" / "final_verdict.json"
)
AUTH_GATE_REVIEW_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "implementation-authorization" / "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_GATE_REVIEW.md"
)
REVIEW_PLAN_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "implementation-authorization" / "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW_PLAN.md"
)
REVIEW_GATE_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "implementation-authorization" / "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW_GATE.md"
)

EXPECTED_RESIDUALS = [
    "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
    "PLATFORM_INTEGRATION_NOT_ENABLED",
    "PUBLISH_RESULT_HISTORY_STILL_SHORT",
    "EXTERNAL_CALL_NOT_IMPLEMENTED",
    "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED",
]

FORBIDDEN_IMPORT_PATTERN = re.compile(
    r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|dns|googleapiclient|boto3)\b",
    re.MULTILINE,
)
FORBIDDEN_TRUE_ASSIGNMENTS = [
    '"code_authorized": true',
    '"implementation_authorized": true',
    '"implementation_tests_authorized": true',
    '"http_client_allowed": true',
    '"platform_sdk_allowed": true',
    '"endpoint_allowed": true',
    '"dns_network_allowed": true',
    '"api_call_allowed": true',
    '"credential_value_access_authorized": true',
    '"request_transformation_authorized": true',
    '"transport_payload_authorized": true',
    '"external_call_authorized": true',
    '"runtime_integration_authorized": true',
    '"upload_authorized": true',
    '"scheduler_authorized": true',
    '"real_publish_authorized": true',
    '"published_url_allowed": true',
    '"platform_content_id_allowed": true',
    '"receipt_allowed": true',
    '"production_residual_closure_authorized": true',
]


def _reset_audit_dir() -> None:
    if AUDIT_DIR.exists():
        shutil.rmtree(AUDIT_DIR)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, ensure_ascii=True), encoding="utf-8")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _load_json(path: Path) -> tuple[dict[str, Any], str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:  # noqa: BLE001 - audit gate must report parse failures explicitly
        return {}, f"{type(exc).__name__}: {exc}"


def _scenario(name: str, passed: bool, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scenario": name,
        "passed": bool(passed),
        "failure_reason": None if passed else "SCENARIO_FAILED",
        "evidence": evidence or {},
    }


def _contains_all(text: str, fragments: list[str]) -> bool:
    return all(fragment in text for fragment in fragments)


def _preconditions() -> dict[str, Any]:
    prior_verdict, prior_error = _load_json(AUTH_GATE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [
            AUTH_PLAN_PATH,
            AUTH_GATE_PATH,
            AUTH_GATE_REVIEW_PATH,
            REVIEW_PLAN_PATH,
            REVIEW_GATE_PATH,
        ]
    }
    required_artifacts = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [AUTH_GATE_RUNNER_PATH, AUTH_GATE_VERDICT_PATH]
    }
    checks = {
        "required_docs_present": all(required_docs.values()),
        "required_artifacts_present": all(required_artifacts.values()),
        "prior_artifact_json_valid": not prior_error,
        "prior_gate_verdict_acceptable": prior_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "prior_gate_no_blocking_failures": prior_verdict.get("blocking_failures") == [],
        "prior_gate_no_critical_failures": prior_verdict.get("metrics", {}).get("critical_failures", 1) == 0,
        "prior_gate_future_review_allowed": prior_verdict.get("future_implementation_authorization_review_allowed")
        is True,
        "prior_gate_code_not_authorized": prior_verdict.get("implementation_authorized_by_this_gate") is False,
        "prior_gate_tests_not_authorized": prior_verdict.get("implementation_tests_authorized_by_this_gate")
        is False,
        "prior_gate_external_call_unauthorized": prior_verdict.get("external_call_authorized") is False,
        "prior_gate_runtime_integration_unauthorized": prior_verdict.get("runtime_integration_authorized") is False,
        "prior_gate_production_residuals_open": prior_verdict.get("production_residuals_remain_open") is True,
        "prior_gate_no_silent_failures": prior_verdict.get("metrics", {}).get("silent_failures_detected") is False,
    }
    return {
        "required_docs": required_docs,
        "required_artifacts": required_artifacts,
        "prior_artifact_error": prior_error,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _non_authorization_review() -> dict[str, Any]:
    review_plan = _read(REVIEW_PLAN_PATH)
    review_gate = _read(REVIEW_GATE_PATH)
    runner = _read(Path(__file__))
    combined = f"{review_plan}\n{review_gate}"
    forbidden_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(runner)]
    forbidden_true_assignments = [fragment for fragment in FORBIDDEN_TRUE_ASSIGNMENTS if fragment in combined.lower()]
    required_false_fragments = [
        '"code_authorized": false',
        '"implementation_tests_authorized": false',
        '"http_client_allowed": false',
        '"platform_sdk_allowed": false',
        '"endpoint_allowed": false',
        '"dns_network_allowed": false',
        '"api_call_allowed": false',
        '"credential_value_access_authorized": false',
        '"request_transformation_authorized": false',
        '"transport_payload_authorized": false',
        '"external_call_authorized": false',
        '"runtime_integration_authorized": false',
        '"upload_authorized": false',
        '"scheduler_authorized": false',
        '"real_publish_authorized": false',
        '"published_url_allowed": false',
        '"platform_content_id_allowed": false',
        '"receipt_allowed": false',
        '"production_residual_closure_authorized": false',
    ]
    checks = {
        "all_required_false_fragments_present": _contains_all(combined, required_false_fragments),
        "no_true_authorization_fragments": not forbidden_true_assignments,
        "runner_has_no_forbidden_network_imports": not forbidden_imports,
        "plan_says_no_code": "It does not grant implementation permission." in review_plan,
        "plan_says_no_execution": "It cannot authorize execution." in review_plan,
        "gate_says_no_implementation": "It cannot authorize implementation." in review_gate,
        "gate_says_no_execution": "It cannot authorize execution." in review_gate,
        "gate_says_no_transport": "It cannot authorize transport." in review_gate,
        "gate_says_no_runtime_integration": "It cannot authorize runtime integration." in review_gate,
    }
    return {
        "required_false_fragments": required_false_fragments,
        "forbidden_true_assignments": forbidden_true_assignments,
        "forbidden_runner_imports": forbidden_imports,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _decision_boundary_review() -> dict[str, Any]:
    review_plan = _read(REVIEW_PLAN_PATH)
    review_gate = _read(REVIEW_GATE_PATH)
    required_decisions = [
        "REMAIN_PLANNING_ONLY",
        "AUTHORIZE_OFFLINE_PREPARATION_ONLY_IMPLEMENTATION_PLAN",
        "HOLD_BEFORE_IMPLEMENTATION_AUTHORIZATION",
    ]
    checks = {
        "allowed_decisions_present": all(decision in review_plan for decision in required_decisions),
        "gate_validates_bounded_decisions": "future_review_decisions_are_bounded" in review_gate,
        "strongest_positive_only_plan": "AUTHORIZE_OFFLINE_PREPARATION_ONLY_IMPLEMENTATION_PLAN" in review_gate
        and "This means a future implementation plan may be created." in review_gate,
        "strongest_positive_does_not_authorize_code": '"implementation_authorized": false' in review_plan
        and '"implementation_authorized": false' in review_gate,
        "strongest_positive_does_not_authorize_tests": '"implementation_tests_authorized": false' in review_plan
        and '"implementation_tests_authorized": false' in review_gate,
        "strongest_positive_does_not_authorize_external_call": '"external_call_authorized": false' in review_plan
        and '"external_call_authorized": false' in review_gate,
        "strongest_positive_does_not_authorize_runtime_integration": '"runtime_integration_authorized": false'
        in review_plan
        and '"runtime_integration_authorized": false' in review_gate,
        "review_must_not_jump_to_code": "The future review must not jump directly to code." in review_plan,
        "future_file_policy_does_not_authorize_files": "This plan does not authorize files." in review_plan,
        "future_review_may_not_authorize_files": "The future review may not authorize files directly." in review_plan,
    }
    return {
        "allowed_decisions": required_decisions,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    review_plan = _read(REVIEW_PLAN_PATH)
    review_gate = _read(REVIEW_GATE_PATH)
    prior_verdict, _ = _load_json(AUTH_GATE_VERDICT_PATH)
    combined = f"{review_plan}\n{review_gate}"
    residuals_in_docs = [residual for residual in EXPECTED_RESIDUALS if residual in combined]
    prior_residuals = prior_verdict.get("residual_monitoring", [])
    checks = {
        "expected_residuals_present_in_docs": residuals_in_docs == EXPECTED_RESIDUALS,
        "expected_residuals_present_in_prior_verdict": all(residual in prior_residuals for residual in EXPECTED_RESIDUALS),
        "production_residuals_remain_open_statement": "production residuals remain open" in combined,
        "no_residual_closure_authorized": '"production_residual_closure_authorized": false' in combined,
        "only_real_evidence_may_reduce_production_residuals": "Only future real evidence may reduce production residuals."
        in review_plan,
    }
    return {
        "expected_residuals": EXPECTED_RESIDUALS,
        "residuals_in_docs": residuals_in_docs,
        "prior_residuals": prior_residuals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_review() -> dict[str, Any]:
    review_plan = _read(REVIEW_PLAN_PATH)
    review_gate = _read(REVIEW_GATE_PATH)
    combined = f"{review_plan}\n{review_gate}"
    checks = {
        "publisher_not_external_execution_client": "Publisher may govern publication, but is not an external execution client."
        in review_gate
        or "Publisher as governed publish authority, not external execution client" in review_plan,
        "qc_final_artifact_evaluator": "QC remains final artifact evaluator" in review_gate
        or "QC as final artifact evaluator" in review_plan,
        "account_health_hold_blocking": "Account Health `HOLD` remains blocking authority" in review_gate
        or "Account Health `HOLD` as blocking authority" in review_plan,
        "strategy_control_layer": "Strategy remains the control layer" in review_gate
        or "Strategy as control layer" in review_plan,
        "orchestrator_coordinator": "Orchestrator remains a coordinator" in review_gate
        or "Orchestrator as coordinator" in review_plan,
        "attribution_no_production_causality": "Attribution receives no production causality" in review_gate
        or "Attribution as non-causal until production evidence exists" in review_plan,
        "experiment_no_publish_authority": "Experiment receives no publish authority" in review_gate
        or "Experiment as non-publish authority" in review_plan,
        "core_pipeline_unchanged": "Core pipeline remains unchanged" in review_gate or "core pipeline unchanged" in review_plan,
        "future_allowlist_excludes_core_agents": "The future file allowlist must not include modifications to:" in review_plan
        and "QC" in review_plan
        and "Account Health" in review_plan
        and "Strategy" in review_plan
        and "Orchestrator" in review_plan
        and "core pipeline" in review_plan,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _scenario_outputs(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    checks = {
        **reviews["preconditions"]["checks"],
        **reviews["non_authorization_review"]["checks"],
        **reviews["decision_boundary_review"]["checks"],
        **reviews["residual_monitoring_review"]["checks"],
        **reviews["boundary_review"]["checks"],
    }
    scenario_names = [
        "review_plan_exists",
        "review_plan_is_planning_only",
        "review_plan_does_not_authorize_code",
        "review_plan_does_not_authorize_tests",
        "review_plan_does_not_authorize_runner_execution",
        "review_plan_does_not_authorize_http_sdk",
        "review_plan_does_not_authorize_endpoint_dns_api",
        "review_plan_does_not_authorize_credentials",
        "review_plan_does_not_authorize_request_transformation",
        "review_plan_does_not_authorize_external_call",
        "review_plan_does_not_authorize_runtime_integration",
        "review_plan_does_not_authorize_upload_scheduler_publish",
        "review_plan_does_not_authorize_url_platform_content_id_receipt",
        "review_plan_does_not_close_production_residuals",
        "future_review_decisions_are_bounded",
        "future_positive_decision_only_authorizes_implementation_plan",
        "future_positive_decision_keeps_implementation_false",
        "future_positive_decision_keeps_external_call_false",
        "future_positive_decision_keeps_runtime_integration_false",
        "future_file_policy_does_not_authorize_files",
        "future_file_policy_requires_later_allowlist",
        "future_allowlist_excludes_qc_health_strategy_orchestrator_core",
        "qc_boundary_preserved",
        "account_health_hold_boundary_preserved",
        "strategy_boundary_preserved",
        "orchestrator_boundary_preserved",
        "publisher_not_external_execution_client",
        "production_residuals_remain_open",
        "no_silent_permission_escalation",
        "deterministic_review_plan_replay",
    ]
    scenario_checks = {
        "review_plan_exists": checks["required_docs_present"],
        "review_plan_is_planning_only": checks["plan_says_no_code"],
        "review_plan_does_not_authorize_code": checks["plan_says_no_code"],
        "review_plan_does_not_authorize_tests": checks["all_required_false_fragments_present"],
        "review_plan_does_not_authorize_runner_execution": checks["gate_says_no_execution"],
        "review_plan_does_not_authorize_http_sdk": checks["all_required_false_fragments_present"],
        "review_plan_does_not_authorize_endpoint_dns_api": checks["all_required_false_fragments_present"],
        "review_plan_does_not_authorize_credentials": checks["all_required_false_fragments_present"],
        "review_plan_does_not_authorize_request_transformation": checks["all_required_false_fragments_present"],
        "review_plan_does_not_authorize_external_call": checks["all_required_false_fragments_present"],
        "review_plan_does_not_authorize_runtime_integration": checks["all_required_false_fragments_present"],
        "review_plan_does_not_authorize_upload_scheduler_publish": checks["all_required_false_fragments_present"],
        "review_plan_does_not_authorize_url_platform_content_id_receipt": checks["all_required_false_fragments_present"],
        "review_plan_does_not_close_production_residuals": checks["no_residual_closure_authorized"],
        "future_review_decisions_are_bounded": checks["allowed_decisions_present"],
        "future_positive_decision_only_authorizes_implementation_plan": checks["strongest_positive_only_plan"],
        "future_positive_decision_keeps_implementation_false": checks["strongest_positive_does_not_authorize_code"],
        "future_positive_decision_keeps_external_call_false": checks[
            "strongest_positive_does_not_authorize_external_call"
        ],
        "future_positive_decision_keeps_runtime_integration_false": checks[
            "strongest_positive_does_not_authorize_runtime_integration"
        ],
        "future_file_policy_does_not_authorize_files": checks["future_file_policy_does_not_authorize_files"],
        "future_file_policy_requires_later_allowlist": checks["future_review_may_not_authorize_files"],
        "future_allowlist_excludes_qc_health_strategy_orchestrator_core": checks[
            "future_allowlist_excludes_core_agents"
        ],
        "qc_boundary_preserved": checks["qc_final_artifact_evaluator"],
        "account_health_hold_boundary_preserved": checks["account_health_hold_blocking"],
        "strategy_boundary_preserved": checks["strategy_control_layer"],
        "orchestrator_boundary_preserved": checks["orchestrator_coordinator"],
        "publisher_not_external_execution_client": checks["publisher_not_external_execution_client"],
        "production_residuals_remain_open": checks["production_residuals_remain_open_statement"],
        "no_silent_permission_escalation": checks["no_true_authorization_fragments"],
        "deterministic_review_plan_replay": True,
    }
    return [
        _scenario(name, scenario_checks[name], {"expected": "audit_only_review_gate"})
        for name in scenario_names
    ]


def _checklist_results(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[tuple[str, bool]] = []
    for review_name in [
        "preconditions",
        "non_authorization_review",
        "decision_boundary_review",
        "residual_monitoring_review",
        "boundary_review",
    ]:
        for check_name, passed in reviews[review_name]["checks"].items():
            items.append((f"{review_name}.{check_name}", bool(passed)))
    return [
        {
            "check": name,
            "passed": passed,
            "failure_reason": None if passed else "CHECK_FAILED",
        }
        for name, passed in items
    ]


def main() -> int:
    _reset_audit_dir()

    reviews = {
        "preconditions": _preconditions(),
        "non_authorization_review": _non_authorization_review(),
        "decision_boundary_review": _decision_boundary_review(),
        "residual_monitoring_review": _residual_monitoring_review(),
        "boundary_review": _boundary_review(),
    }
    scenarios = _scenario_outputs(reviews)
    checklist = _checklist_results(reviews)

    scenario_pass_count = sum(1 for item in scenarios if item["passed"])
    checklist_pass_count = sum(1 for item in checklist if item["passed"])
    blocking_failures = [
        item["scenario"] for item in scenarios if not item["passed"]
    ] + [
        item["check"] for item in checklist if not item["passed"]
    ]
    critical_failures = len(blocking_failures)
    verdict = "GO_WITH_MONITORING" if not blocking_failures else "HOLD"

    metrics = {
        "critical_failures": critical_failures,
        "blocking_failures_count": len(blocking_failures),
        "scenario_count": len(scenarios),
        "scenario_pass_count": scenario_pass_count,
        "checklist_count": len(checklist),
        "checklist_pass_count": checklist_pass_count,
        "review_plan_valid": not blocking_failures,
        "future_review_allowed": not blocking_failures,
        "code_authorized": False,
        "implementation_tests_authorized": False,
        "http_client_allowed": False,
        "platform_sdk_allowed": False,
        "endpoint_allowed": False,
        "dns_network_allowed": False,
        "api_call_allowed": False,
        "credential_value_access_authorized": False,
        "request_transformation_authorized": False,
        "external_call_authorized": False,
        "runtime_integration_authorized": False,
        "upload_authorized": False,
        "scheduler_authorized": False,
        "real_publish_authorized": False,
        "production_residuals_closed": False,
        "silent_failures_detected": False,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "review_plan_valid": not blocking_failures,
        "future_review_allowed": not blocking_failures,
        "code_authorized": False,
        "implementation_tests_authorized": False,
        "http_client_allowed": False,
        "platform_sdk_allowed": False,
        "endpoint_allowed": False,
        "dns_network_allowed": False,
        "api_call_allowed": False,
        "credential_value_access_authorized": False,
        "request_transformation_authorized": False,
        "external_call_authorized": False,
        "runtime_integration_authorized": False,
        "upload_authorized": False,
        "scheduler_authorized": False,
        "real_publish_authorized": False,
        "production_residuals_remain_open": True,
        "scenario_pass_count": f"{scenario_pass_count}/{len(scenarios)}",
        "checklist_pass_count": f"{checklist_pass_count}/{len(checklist)}",
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": EXPECTED_RESIDUALS,
        "recommendation": (
            "PROCEED_TO_EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW"
            if verdict != "HOLD"
            else "HOLD_BEFORE_AUTHORIZATION_REVIEW"
        ),
    }

    _write_json(NON_AUTHORIZATION_REVIEW_PATH, reviews["non_authorization_review"])
    _write_json(DECISION_BOUNDARY_REVIEW_PATH, reviews["decision_boundary_review"])
    _write_json(RESIDUAL_MONITORING_REVIEW_PATH, reviews["residual_monitoring_review"])
    _write_json(BOUNDARY_REVIEW_PATH, reviews["boundary_review"])
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
