from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_validation_call_offline_preparation_implementation_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
ALLOWLIST_REVIEW_PATH = AUDIT_DIR / "allowlist_review.json"
NON_AUTHORIZATION_REVIEW_PATH = AUDIT_DIR / "non_authorization_review.json"
FORBIDDEN_SURFACE_REVIEW_PATH = AUDIT_DIR / "forbidden_surface_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
BOUNDARY_REVIEW_PATH = AUDIT_DIR / "boundary_review.json"

AUTH_REVIEW_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "implementation-authorization" / "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW.md"
)
AUTH_REVIEW_GATE_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "implementation-authorization" / "EXTERNAL_SANDBOX_VALIDATION_CALL_IMPLEMENTATION_AUTHORIZATION_REVIEW_GATE.md"
)
AUTH_REVIEW_GATE_RUNNER_PATH = (
    ROOT / "tests" / "run_external_sandbox_validation_call_implementation_authorization_review_gate.py"
)
AUTH_REVIEW_GATE_VERDICT_PATH = (
    ROOT
    / "OUT"
    / "audit"
    / "external_sandbox_validation_call_implementation_authorization_review_gate"
    / "final_verdict.json"
)
IMPLEMENTATION_PLAN_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "offline-preparation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_PLAN.md"
)
IMPLEMENTATION_GATE_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "offline-preparation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE.md"
)

EXPECTED_ALLOWLIST = [
    "backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation.py",
    "backend/app/creative/agents/publisher/external_sandbox_validation_call_preparation_security.py",
    "tests/sandbox/unit/test_external_sandbox_validation_call_preparation_unittest.py",
]

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
    '"allowlist_active": true',
    '"implementation_authorized": true',
    '"tests_authorized": true',
    '"implementation_tests_authorized": true',
    '"external_call_authorized": true',
    '"runtime_integration_authorized": true',
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
    '"production_residual_closure_authorized": true',
]
FORBIDDEN_SURFACE_TERMS = [
    "`requests`",
    "`httpx`",
    "`aiohttp`",
    "`urllib.request`",
    "`urllib3`",
    "`socket`",
    "DNS libraries",
    "platform SDK imports",
    "endpoint constants",
    "base URL constants",
    "HTTP method constants",
    "header builders",
    "authorization header builders",
    "request body builders",
    "upload helpers",
    "scheduler helpers",
    "publish helpers",
    "receipt generation",
    "production URL generation",
    "`platform_content_id` generation",
    "credential value reads",
    "environment secret value reads",
    "request transformation functions",
    "transport payload serializers",
    "runtime integration hooks",
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


def _extract_allowlist(plan_text: str) -> list[str]:
    match = re.search(
        r"This plan proposes, but does not authorize, this future file allowlist:\s*```text\s*(.*?)\s*```",
        plan_text,
        re.DOTALL,
    )
    if not match:
        return []
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def _preconditions() -> dict[str, Any]:
    prior_verdict, prior_error = _load_json(AUTH_REVIEW_GATE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [AUTH_REVIEW_PATH, AUTH_REVIEW_GATE_PATH, IMPLEMENTATION_PLAN_PATH, IMPLEMENTATION_GATE_PATH]
    }
    required_artifacts = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [AUTH_REVIEW_GATE_RUNNER_PATH, AUTH_REVIEW_GATE_VERDICT_PATH]
    }
    checks = {
        "required_docs_present": all(required_docs.values()),
        "required_artifacts_present": all(required_artifacts.values()),
        "prior_artifact_json_valid": not prior_error,
        "prior_gate_verdict_acceptable": prior_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "prior_gate_no_blocking_failures": prior_verdict.get("blocking_failures") == [],
        "prior_gate_no_critical_failures": prior_verdict.get("metrics", {}).get("critical_failures", 1) == 0,
        "prior_gate_review_plan_valid": prior_verdict.get("review_plan_valid") is True,
        "prior_gate_future_review_allowed": prior_verdict.get("future_review_allowed") is True,
        "prior_gate_code_unauthorized": prior_verdict.get("code_authorized") is False,
        "prior_gate_tests_unauthorized": prior_verdict.get("implementation_tests_authorized") is False,
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


def _allowlist_review() -> dict[str, Any]:
    plan = _read(IMPLEMENTATION_PLAN_PATH)
    gate = _read(IMPLEMENTATION_GATE_PATH)
    extracted = _extract_allowlist(plan)
    file_existence = {path: (ROOT / path).exists() for path in EXPECTED_ALLOWLIST}
    checks = {
        "allowlist_proposed": "This plan proposes, but does not authorize, this future file allowlist:" in plan,
        "allowlist_exact": extracted == EXPECTED_ALLOWLIST,
        "allowlist_has_three_files": len(extracted) == 3,
        "allowlist_has_publisher_preparation_file": EXPECTED_ALLOWLIST[0] in extracted,
        "allowlist_has_publisher_security_file": EXPECTED_ALLOWLIST[1] in extracted,
        "allowlist_has_unit_test_file": EXPECTED_ALLOWLIST[2] in extracted,
        "allowlist_has_no_extra_files": set(extracted) == set(EXPECTED_ALLOWLIST),
        "allowlist_active_false": "The allowlist is not active." in plan and '"allowlist_active": false' in gate,
        "allowlisted_files_not_created": not any(file_existence.values()),
        "implementation_authorized_false": '"implementation_authorized": false' in plan
        and '"implementation_authorized": false' in gate,
        "tests_authorized_false": '"tests_authorized": false' in gate
        and '"implementation_tests_authorized": false' in plan,
        "gate_required_before_code_true": '"gate_required_before_code": true' in plan
        and '"gate_required_before_code": true' in gate,
    }
    return {
        "expected_allowlist": EXPECTED_ALLOWLIST,
        "extracted_allowlist": extracted,
        "file_existence": file_existence,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _non_authorization_review() -> dict[str, Any]:
    plan = _read(IMPLEMENTATION_PLAN_PATH)
    gate = _read(IMPLEMENTATION_GATE_PATH)
    runner = _read(Path(__file__))
    combined = f"{plan}\n{gate}"
    forbidden_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(runner)]
    forbidden_true_assignments = [fragment for fragment in FORBIDDEN_TRUE_ASSIGNMENTS if fragment in combined.lower()]
    required_false_fragments = [
        '"allowlist_active": false',
        '"implementation_authorized": false',
        '"tests_authorized": false',
        '"implementation_tests_authorized": false',
        '"external_call_authorized": false',
        '"runtime_integration_authorized": false',
        '"request_transformation_authorized": false',
        '"transport_payload_authorized": false',
        '"credential_value_access_authorized": false',
    ]
    checks = {
        "all_required_false_fragments_present": _contains_all(combined, required_false_fragments),
        "no_true_authorization_fragments": not forbidden_true_assignments,
        "runner_has_no_forbidden_network_imports": not forbidden_imports,
        "plan_says_no_code": "It cannot authorize code." in plan,
        "plan_says_no_tests": "It cannot authorize tests." in plan,
        "plan_says_no_execution": "It cannot authorize execution." in plan,
        "gate_says_cannot_authorize_code": "It cannot authorize code." in gate,
        "gate_says_cannot_authorize_tests": "It cannot authorize tests." in gate,
        "gate_says_cannot_authorize_execution": "It cannot authorize execution." in gate,
    }
    return {
        "required_false_fragments": required_false_fragments,
        "forbidden_true_assignments": forbidden_true_assignments,
        "forbidden_runner_imports": forbidden_imports,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _forbidden_surface_review() -> dict[str, Any]:
    plan = _read(IMPLEMENTATION_PLAN_PATH)
    gate = _read(IMPLEMENTATION_GATE_PATH)
    checks = {
        "forbidden_surface_terms_present_in_plan": _contains_all(plan, FORBIDDEN_SURFACE_TERMS),
        "forbidden_surface_terms_present_in_gate": _contains_all(gate, FORBIDDEN_SURFACE_TERMS),
        "http_sdk_forbidden": "`requests`" in gate and "platform SDK imports" in gate,
        "endpoint_dns_forbidden": "endpoint constants" in gate and "DNS libraries" in gate,
        "request_transformation_forbidden": "request transformation functions" in gate,
        "transport_payload_forbidden": "transport payload serializers" in gate,
        "upload_scheduler_publish_forbidden": "upload helpers" in gate
        and "scheduler helpers" in gate
        and "publish helpers" in gate,
        "url_platform_content_id_receipt_forbidden": "production URL generation" in gate
        and "`platform_content_id` generation" in gate
        and "receipt generation" in gate,
        "credential_values_forbidden": "credential value reads" in gate
        and "environment secret value reads" in gate,
        "runtime_integration_forbidden": "runtime integration hooks" in gate,
    }
    return {
        "forbidden_surface_terms": FORBIDDEN_SURFACE_TERMS,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    plan = _read(IMPLEMENTATION_PLAN_PATH)
    gate = _read(IMPLEMENTATION_GATE_PATH)
    prior_verdict, _ = _load_json(AUTH_REVIEW_GATE_VERDICT_PATH)
    combined = f"{plan}\n{gate}"
    residuals_in_docs = [residual for residual in EXPECTED_RESIDUALS if residual in combined]
    prior_residuals = prior_verdict.get("residual_monitoring", [])
    checks = {
        "expected_residuals_present_in_docs": residuals_in_docs == EXPECTED_RESIDUALS,
        "expected_residuals_present_in_prior_verdict": all(residual in prior_residuals for residual in EXPECTED_RESIDUALS),
        "production_residuals_remain_open_statement": "production residuals remain open" in combined,
        "no_production_residual_closure": "This plan does not reduce residuals." in plan
        and "production residual closure" in gate,
    }
    return {
        "expected_residuals": EXPECTED_RESIDUALS,
        "residuals_in_docs": residuals_in_docs,
        "prior_residuals": prior_residuals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_review() -> dict[str, Any]:
    plan = _read(IMPLEMENTATION_PLAN_PATH)
    gate = _read(IMPLEMENTATION_GATE_PATH)
    combined = f"{plan}\n{gate}"
    checks = {
        "offline_only_boundary_present": "offline-only" in combined,
        "preparation_only_boundary_present": "preparation-only" in combined,
        "non_transport_boundary_present": "non_transport" in combined or "non-transport" in combined,
        "non_client_boundary_present": "non_client" in combined or "non-client" in combined,
        "non_endpoint_boundary_present": "non_endpoint" in combined or "non-endpoint" in combined,
        "non_network_boundary_present": "non_network" in combined or "non-network" in combined,
        "non_executing_boundary_present": "non_executing" in combined or "non-executing" in combined,
        "credential_values_inaccessible": "credential_values_inaccessible" in combined
        or "credential values inaccessible" in combined,
        "qc_health_strategy_orchestrator_core_unchanged": "QC" in plan
        and "Account Health" in plan
        and "Strategy" in plan
        and "Orchestrator" in plan
        and "core pipeline" in plan,
        "publisher_not_external_execution_client": "Publisher may govern publication, but is not an external execution client."
        in gate,
        "core_pipeline_unchanged": "Core pipeline remains unchanged." in gate or "core pipeline" in plan,
        "no_runtime_import_required": "importing runtime modules" in gate and "Out of scope" in gate,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _scenario_outputs(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    checks = {
        **reviews["preconditions"]["checks"],
        **reviews["allowlist_review"]["checks"],
        **reviews["non_authorization_review"]["checks"],
        **reviews["forbidden_surface_review"]["checks"],
        **reviews["residual_monitoring_review"]["checks"],
        **reviews["boundary_review"]["checks"],
    }
    scenario_names = [
        "implementation_plan_exists",
        "prior_review_gate_verdict_acceptable",
        "allowlist_exact",
        "allowlist_has_three_files",
        "allowlist_has_publisher_preparation_file",
        "allowlist_has_publisher_security_file",
        "allowlist_has_unit_test_file",
        "allowlist_has_no_extra_files",
        "allowlist_active_false",
        "implementation_authorized_false",
        "tests_authorized_false",
        "external_call_authorized_false",
        "runtime_integration_authorized_false",
        "gate_required_before_code_true",
        "offline_only_boundary_present",
        "preparation_only_boundary_present",
        "non_transport_boundary_present",
        "non_client_boundary_present",
        "non_endpoint_boundary_present",
        "non_network_boundary_present",
        "non_executing_boundary_present",
        "credential_values_inaccessible",
        "request_transformation_forbidden",
        "transport_payload_forbidden",
        "http_sdk_forbidden",
        "endpoint_dns_forbidden",
        "upload_scheduler_publish_forbidden",
        "url_platform_content_id_receipt_forbidden",
        "production_residuals_remain_open",
        "qc_health_strategy_orchestrator_core_unchanged",
        "no_runtime_import_required",
        "no_silent_permission_escalation",
    ]
    scenario_checks = {
        "implementation_plan_exists": checks["required_docs_present"],
        "prior_review_gate_verdict_acceptable": checks["prior_gate_verdict_acceptable"],
        "allowlist_exact": checks["allowlist_exact"],
        "allowlist_has_three_files": checks["allowlist_has_three_files"],
        "allowlist_has_publisher_preparation_file": checks["allowlist_has_publisher_preparation_file"],
        "allowlist_has_publisher_security_file": checks["allowlist_has_publisher_security_file"],
        "allowlist_has_unit_test_file": checks["allowlist_has_unit_test_file"],
        "allowlist_has_no_extra_files": checks["allowlist_has_no_extra_files"],
        "allowlist_active_false": checks["allowlist_active_false"],
        "implementation_authorized_false": checks["implementation_authorized_false"],
        "tests_authorized_false": checks["tests_authorized_false"],
        "external_call_authorized_false": checks["prior_gate_external_call_unauthorized"]
        and checks["all_required_false_fragments_present"],
        "runtime_integration_authorized_false": checks["prior_gate_runtime_integration_unauthorized"]
        and checks["all_required_false_fragments_present"],
        "gate_required_before_code_true": checks["gate_required_before_code_true"],
        "offline_only_boundary_present": checks["offline_only_boundary_present"],
        "preparation_only_boundary_present": checks["preparation_only_boundary_present"],
        "non_transport_boundary_present": checks["non_transport_boundary_present"],
        "non_client_boundary_present": checks["non_client_boundary_present"],
        "non_endpoint_boundary_present": checks["non_endpoint_boundary_present"],
        "non_network_boundary_present": checks["non_network_boundary_present"],
        "non_executing_boundary_present": checks["non_executing_boundary_present"],
        "credential_values_inaccessible": checks["credential_values_inaccessible"],
        "request_transformation_forbidden": checks["request_transformation_forbidden"],
        "transport_payload_forbidden": checks["transport_payload_forbidden"],
        "http_sdk_forbidden": checks["http_sdk_forbidden"],
        "endpoint_dns_forbidden": checks["endpoint_dns_forbidden"],
        "upload_scheduler_publish_forbidden": checks["upload_scheduler_publish_forbidden"],
        "url_platform_content_id_receipt_forbidden": checks["url_platform_content_id_receipt_forbidden"],
        "production_residuals_remain_open": checks["production_residuals_remain_open_statement"],
        "qc_health_strategy_orchestrator_core_unchanged": checks["qc_health_strategy_orchestrator_core_unchanged"],
        "no_runtime_import_required": checks["no_runtime_import_required"],
        "no_silent_permission_escalation": checks["no_true_authorization_fragments"],
    }
    return [
        _scenario(name, scenario_checks[name], {"expected": "inactive_allowlist_audit_gate"})
        for name in scenario_names
    ]


def _checklist_results(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[tuple[str, bool]] = []
    for review_name in [
        "preconditions",
        "allowlist_review",
        "non_authorization_review",
        "forbidden_surface_review",
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
        "allowlist_review": _allowlist_review(),
        "non_authorization_review": _non_authorization_review(),
        "forbidden_surface_review": _forbidden_surface_review(),
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
        "allowlist_exact": not blocking_failures and reviews["allowlist_review"]["checks"]["allowlist_exact"],
        "allowlist_active": False,
        "implementation_authorized": False,
        "tests_authorized": False,
        "external_call_authorized": False,
        "runtime_integration_authorized": False,
        "gate_required_before_code": True,
        "production_residuals_closed": False,
        "silent_failures_detected": False,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "allowlist_exact": not blocking_failures and reviews["allowlist_review"]["checks"]["allowlist_exact"],
        "allowlist_active": False,
        "implementation_authorized": False,
        "tests_authorized": False,
        "external_call_authorized": False,
        "runtime_integration_authorized": False,
        "gate_required_before_code": True,
        "production_residuals_remain_open": True,
        "scenario_pass_count": f"{scenario_pass_count}/{len(scenarios)}",
        "checklist_pass_count": f"{checklist_pass_count}/{len(checklist)}",
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": EXPECTED_RESIDUALS,
        "recommendation": (
            "PROCEED_TO_EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_GATE_REVIEW"
            if verdict != "HOLD"
            else "HOLD_BEFORE_OFFLINE_PREPARATION_IMPLEMENTATION"
        ),
    }

    _write_json(ALLOWLIST_REVIEW_PATH, reviews["allowlist_review"])
    _write_json(NON_AUTHORIZATION_REVIEW_PATH, reviews["non_authorization_review"])
    _write_json(FORBIDDEN_SURFACE_REVIEW_PATH, reviews["forbidden_surface_review"])
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
