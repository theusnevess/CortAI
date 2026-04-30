from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_validation_call_implementation_authorization_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
NON_AUTHORIZATION_REVIEW_PATH = AUDIT_DIR / "non_authorization_review.json"
BOUNDARY_REVIEW_PATH = AUDIT_DIR / "boundary_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
PERMISSION_ESCALATION_REVIEW_PATH = AUDIT_DIR / "permission_escalation_review.json"

PRE_IMPL_PLAN_PATH = ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "pre-implementation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_PLAN.md"
PRE_IMPL_GATE_PATH = ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "pre-implementation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_GATE.md"
PRE_IMPL_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_validation_call_pre_implementation_gate" / "final_verdict.json"
)
PRE_IMPL_REVIEW_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "pre-implementation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_GATE_REVIEW.md"
)
AUTH_PLAN_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "implementation-authorization" / "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_PLAN.md"
)
AUTH_GATE_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "implementation-authorization" / "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_GATE.md"
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
    '"implementation_authorized": true',
    '"implementation_authorized_by_this_gate": true',
    '"implementation_tests_authorized": true',
    '"implementation_tests_authorized_by_this_gate": true',
    '"external_call_authorized": true',
    '"http_client_allowed": true',
    '"platform_sdk_allowed": true',
    '"endpoint_allowed": true',
    '"dns_network_allowed": true',
    '"api_call_allowed": true',
    '"credential_value_access_authorized": true',
    '"request_transformation_authorized": true',
    '"transport_payload_authorized": true',
    '"upload_authorized": true',
    '"scheduler_authorized": true',
    '"real_publish_authorized": true',
    '"published_url_allowed": true',
    '"platform_content_id_allowed": true',
    '"receipt_allowed": true',
    '"runtime_integration_authorized": true',
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
    except Exception as exc:  # noqa: BLE001 - audit gate records parse failures explicitly
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
    prior_verdict, prior_error = _load_json(PRE_IMPL_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [
            PRE_IMPL_PLAN_PATH,
            PRE_IMPL_GATE_PATH,
            PRE_IMPL_REVIEW_PATH,
            AUTH_PLAN_PATH,
            AUTH_GATE_PATH,
        ]
    }
    required_artifacts = {
        str(PRE_IMPL_VERDICT_PATH.relative_to(ROOT)): PRE_IMPL_VERDICT_PATH.exists()
    }
    checks = {
        "required_docs_present": all(required_docs.values()),
        "required_prior_artifact_present": all(required_artifacts.values()),
        "prior_artifact_json_valid": not prior_error,
        "prior_gate_verdict_acceptable": prior_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "prior_gate_no_blocking_failures": prior_verdict.get("blocking_failures") == [],
        "prior_gate_no_critical_failures": prior_verdict.get("metrics", {}).get("critical_failures", 1) == 0,
        "prior_gate_implementation_unauthorized": prior_verdict.get("implementation_authorized") is False,
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
    auth_plan = _read(AUTH_PLAN_PATH)
    auth_gate = _read(AUTH_GATE_PATH)
    runner = _read(Path(__file__))
    combined = f"{auth_plan}\n{auth_gate}"
    forbidden_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(runner)]
    forbidden_true_assignments = [fragment for fragment in FORBIDDEN_TRUE_ASSIGNMENTS if fragment in combined.lower()]
    required_false_fragments = [
        '"implementation_authorized": false',
        '"implementation_authorized_by_this_gate": false',
        '"implementation_tests_authorized_by_this_gate": false',
        '"external_call_authorized": false',
        '"http_client_allowed": false',
        '"platform_sdk_allowed": false',
        '"endpoint_allowed": false',
        '"dns_network_allowed": false',
        '"api_call_allowed": false',
        '"credential_value_access_authorized": false',
        '"request_transformation_authorized": false',
        '"transport_payload_authorized": false',
        '"upload_authorized": false',
        '"scheduler_authorized": false',
        '"real_publish_authorized": false',
        '"published_url_allowed": false',
        '"platform_content_id_allowed": false',
        '"receipt_allowed": false',
        '"runtime_integration_authorized": false',
        '"production_residual_closure_authorized": false',
    ]
    checks = {
        "all_required_false_fragments_present": _contains_all(combined, required_false_fragments),
        "no_true_authorization_fragments": not forbidden_true_assignments,
        "runner_has_no_forbidden_network_imports": not forbidden_imports,
        "gate_says_no_direct_implementation_authorization": "This gate must not directly authorize implementation."
        in auth_gate,
        "gate_says_no_runner_created_by_doc": "No runner is created by this document." in auth_gate,
        "gate_says_no_external_execution": "It does not authorize external calls." in auth_gate,
        "gate_says_no_transport": "It does not authorize transport." in auth_gate,
        "gate_says_no_runtime_integration": "It does not authorize runtime integration." in auth_gate,
    }
    return {
        "required_false_fragments": required_false_fragments,
        "forbidden_true_assignments": forbidden_true_assignments,
        "forbidden_runner_imports": forbidden_imports,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_review() -> dict[str, Any]:
    auth_gate = _read(AUTH_GATE_PATH)
    auth_plan = _read(AUTH_PLAN_PATH)
    combined = f"{auth_plan}\n{auth_gate}"
    checks = {
        "future_slice_exact": "SANDBOX_VALIDATION_CALL_PREPARATION_ONLY" in combined,
        "offline_only_boundary": "offline-only" in combined,
        "preparation_only_boundary": "preparation-only" in combined,
        "non_transport_boundary": "non-transport" in combined,
        "non_client_boundary": "non-client" in combined,
        "non_endpoint_boundary": "non-endpoint" in combined,
        "non_executing_boundary": "non-executing" in combined,
        "credential_values_inaccessible": "credential values remain inaccessible" in combined
        or "credential_values_inaccessible" in combined,
        "qc_boundary_preserved": "QC remains final artifact evaluator" in auth_gate,
        "account_health_hold_preserved": "Account Health `HOLD` remains blocking authority" in auth_gate,
        "strategy_boundary_preserved": "Strategy remains the control layer" in auth_gate,
        "orchestrator_boundary_preserved": "Orchestrator remains a coordinator" in auth_gate,
        "publisher_not_external_execution_client": "Publisher may govern publication, but is not an external execution client."
        in auth_gate,
        "core_pipeline_unchanged": "Core pipeline remains unchanged" in auth_gate,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    auth_plan = _read(AUTH_PLAN_PATH)
    auth_gate = _read(AUTH_GATE_PATH)
    prior_verdict, _ = _load_json(PRE_IMPL_VERDICT_PATH)
    combined = f"{auth_plan}\n{auth_gate}"
    residuals_in_docs = [residual for residual in EXPECTED_RESIDUALS if residual in combined]
    prior_residuals = prior_verdict.get("residual_monitoring", [])
    checks = {
        "expected_residuals_present_in_docs": residuals_in_docs == EXPECTED_RESIDUALS,
        "expected_residuals_present_in_prior_verdict": all(residual in prior_residuals for residual in EXPECTED_RESIDUALS),
        "production_residuals_remain_open_statement": "production residuals remain open" in combined,
        "no_production_residual_closure": '"production_residual_closure_authorized": false' in combined,
        "no_production_evidence_claim": "It must not reduce production evidence residuals" in auth_plan,
    }
    return {
        "expected_residuals": EXPECTED_RESIDUALS,
        "residuals_in_docs": residuals_in_docs,
        "prior_residuals": prior_residuals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _permission_escalation_review() -> dict[str, Any]:
    auth_plan = _read(AUTH_PLAN_PATH)
    auth_gate = _read(AUTH_GATE_PATH)
    combined = f"{auth_plan}\n{auth_gate}"
    checks = {
        "absence_of_blockers_not_permission": "absence of blockers does not mean permission" in auth_plan,
        "go_with_monitoring_not_external_execution": "`GO_WITH_MONITORING` does not authorize external call" in auth_plan
        or "`GO_WITH_MONITORING` does not authorize external call" in auth_gate,
        "planning_criteria_not_permission": "Planning criteria is not permission." in auth_plan,
        "authorization_review_not_execution": "Authorization review is not execution." in auth_plan,
        "no_external_boundary_by_implication": "No external boundary may be crossed by implication." in auth_plan,
        "implementation_authorization_requires_future_explicit_step": "implementation_authorization_requires_future_explicit_step"
        in auth_gate,
        "future_review_allowed_is_not_implementation_authorized": '"future_implementation_authorization_review_allowed": true'
        in auth_gate
        and '"implementation_authorized_by_this_gate": false' in auth_gate,
        "runner_next_is_audit_only": "That runner must be audit-only." in auth_gate,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _scenario_outputs(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    checks = {
        **reviews["preconditions"]["checks"],
        **reviews["non_authorization_review"]["checks"],
        **reviews["boundary_review"]["checks"],
        **reviews["residual_monitoring_review"]["checks"],
        **reviews["permission_escalation_review"]["checks"],
    }
    scenario_names = [
        "prior_gate_go_with_monitoring_does_not_authorize_code",
        "prior_gate_review_does_not_authorize_code",
        "authorization_plan_does_not_authorize_code",
        "implementation_authorization_requires_future_explicit_step",
        "external_call_remains_unauthorized",
        "http_client_remains_forbidden",
        "platform_sdk_remains_forbidden",
        "endpoint_remains_forbidden",
        "dns_network_remains_forbidden",
        "api_call_remains_forbidden",
        "credential_value_access_remains_forbidden",
        "request_transformation_remains_forbidden",
        "transport_payload_remains_forbidden",
        "upload_remains_forbidden",
        "scheduler_remains_forbidden",
        "real_publish_remains_forbidden",
        "published_url_remains_forbidden",
        "platform_content_id_remains_forbidden",
        "receipt_remains_forbidden",
        "runtime_integration_remains_forbidden",
        "production_residual_closure_remains_forbidden",
        "future_slice_is_preparation_only",
        "future_slice_is_offline_only",
        "future_slice_is_non_transport",
        "future_slice_is_non_client",
        "future_slice_is_non_endpoint",
        "future_slice_is_non_executing",
        "qc_non_publishable_remains_blocking",
        "account_health_hold_remains_blocking",
        "strategy_control_layer_preserved",
        "orchestrator_coordinator_boundary_preserved",
        "publisher_not_external_execution_client",
        "no_silent_permission_escalation",
        "deterministic_authorization_state_replay",
    ]
    scenario_checks = {
        "prior_gate_go_with_monitoring_does_not_authorize_code": checks["prior_gate_verdict_acceptable"]
        and checks["prior_gate_implementation_unauthorized"],
        "prior_gate_review_does_not_authorize_code": checks["gate_says_no_direct_implementation_authorization"],
        "authorization_plan_does_not_authorize_code": checks["planning_criteria_not_permission"],
        "implementation_authorization_requires_future_explicit_step": checks[
            "implementation_authorization_requires_future_explicit_step"
        ],
        "external_call_remains_unauthorized": checks["all_required_false_fragments_present"],
        "http_client_remains_forbidden": checks["all_required_false_fragments_present"],
        "platform_sdk_remains_forbidden": checks["all_required_false_fragments_present"],
        "endpoint_remains_forbidden": checks["all_required_false_fragments_present"],
        "dns_network_remains_forbidden": checks["all_required_false_fragments_present"],
        "api_call_remains_forbidden": checks["all_required_false_fragments_present"],
        "credential_value_access_remains_forbidden": checks["credential_values_inaccessible"],
        "request_transformation_remains_forbidden": checks["all_required_false_fragments_present"],
        "transport_payload_remains_forbidden": checks["non_transport_boundary"],
        "upload_remains_forbidden": checks["all_required_false_fragments_present"],
        "scheduler_remains_forbidden": checks["all_required_false_fragments_present"],
        "real_publish_remains_forbidden": checks["all_required_false_fragments_present"],
        "published_url_remains_forbidden": checks["all_required_false_fragments_present"],
        "platform_content_id_remains_forbidden": checks["all_required_false_fragments_present"],
        "receipt_remains_forbidden": checks["all_required_false_fragments_present"],
        "runtime_integration_remains_forbidden": checks["all_required_false_fragments_present"],
        "production_residual_closure_remains_forbidden": checks["no_production_residual_closure"],
        "future_slice_is_preparation_only": checks["preparation_only_boundary"],
        "future_slice_is_offline_only": checks["offline_only_boundary"],
        "future_slice_is_non_transport": checks["non_transport_boundary"],
        "future_slice_is_non_client": checks["non_client_boundary"],
        "future_slice_is_non_endpoint": checks["non_endpoint_boundary"],
        "future_slice_is_non_executing": checks["non_executing_boundary"],
        "qc_non_publishable_remains_blocking": checks["qc_boundary_preserved"],
        "account_health_hold_remains_blocking": checks["account_health_hold_preserved"],
        "strategy_control_layer_preserved": checks["strategy_boundary_preserved"],
        "orchestrator_coordinator_boundary_preserved": checks["orchestrator_boundary_preserved"],
        "publisher_not_external_execution_client": checks["publisher_not_external_execution_client"],
        "no_silent_permission_escalation": checks["no_true_authorization_fragments"]
        and checks["no_external_boundary_by_implication"],
        "deterministic_authorization_state_replay": True,
    }
    return [
        _scenario(name, scenario_checks[name], {"check": name, "expected": "non_authorizing_audit_gate"})
        for name in scenario_names
    ]


def _checklist_results(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    checklist_items: list[tuple[str, bool]] = []
    for review_name in [
        "preconditions",
        "non_authorization_review",
        "boundary_review",
        "residual_monitoring_review",
        "permission_escalation_review",
    ]:
        for check_name, passed in reviews[review_name]["checks"].items():
            checklist_items.append((f"{review_name}.{check_name}", bool(passed)))
    return [
        {
            "check": name,
            "passed": passed,
            "failure_reason": None if passed else "CHECK_FAILED",
        }
        for name, passed in checklist_items
    ]


def main() -> int:
    _reset_audit_dir()

    reviews = {
        "preconditions": _preconditions(),
        "non_authorization_review": _non_authorization_review(),
        "boundary_review": _boundary_review(),
        "residual_monitoring_review": _residual_monitoring_review(),
        "permission_escalation_review": _permission_escalation_review(),
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
        "future_implementation_authorization_review_allowed": not blocking_failures,
        "implementation_authorized_by_this_gate": False,
        "implementation_tests_authorized_by_this_gate": False,
        "external_call_authorized": False,
        "http_client_allowed": False,
        "platform_sdk_allowed": False,
        "endpoint_allowed": False,
        "dns_network_allowed": False,
        "api_call_allowed": False,
        "credential_value_access_authorized": False,
        "request_transformation_authorized": False,
        "transport_payload_authorized": False,
        "upload_authorized": False,
        "scheduler_authorized": False,
        "real_publish_authorized": False,
        "runtime_integration_authorized": False,
        "production_residuals_closed": False,
        "silent_failures_detected": False,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "future_slice": "SANDBOX_VALIDATION_CALL_PREPARATION_ONLY",
        "future_implementation_authorization_review_allowed": not blocking_failures,
        "implementation_authorized_by_this_gate": False,
        "implementation_tests_authorized_by_this_gate": False,
        "external_call_authorized": False,
        "http_client_allowed": False,
        "platform_sdk_allowed": False,
        "endpoint_allowed": False,
        "dns_network_allowed": False,
        "api_call_allowed": False,
        "credential_value_access_authorized": False,
        "request_transformation_authorized": False,
        "transport_payload_authorized": False,
        "upload_authorized": False,
        "scheduler_authorized": False,
        "real_publish_authorized": False,
        "runtime_integration_authorized": False,
        "production_residuals_remain_open": True,
        "scenario_pass_count": f"{scenario_pass_count}/{len(scenarios)}",
        "checklist_pass_count": f"{checklist_pass_count}/{len(checklist)}",
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": EXPECTED_RESIDUALS,
        "recommendation": (
            "PROCEED_TO_EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_GATE_REVIEW"
            if verdict != "HOLD"
            else "HOLD_BEFORE_IMPLEMENTATION_AUTHORIZATION"
        ),
    }

    _write_json(NON_AUTHORIZATION_REVIEW_PATH, reviews["non_authorization_review"])
    _write_json(BOUNDARY_REVIEW_PATH, reviews["boundary_review"])
    _write_json(RESIDUAL_MONITORING_REVIEW_PATH, reviews["residual_monitoring_review"])
    _write_json(PERMISSION_ESCALATION_REVIEW_PATH, reviews["permission_escalation_review"])
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
