from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_validation_call_offline_preparation_runtime_integration_readiness_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
NON_AUTHORIZATION_REVIEW_PATH = AUDIT_DIR / "non_authorization_review.json"
READINESS_EVIDENCE_REVIEW_PATH = AUDIT_DIR / "readiness_evidence_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
BOUNDARY_REVIEW_PATH = AUDIT_DIR / "boundary_review.json"

ACCEPTANCE_REVIEW_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "offline-preparation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_ACCEPTANCE_REVIEW.md"
)
ACCEPTANCE_RUNNER_PATH = (
    ROOT / "tests" / "run_external_sandbox_validation_call_offline_preparation_implementation_acceptance_gate.py"
)
ACCEPTANCE_VERDICT_PATH = (
    ROOT
    / "OUT"
    / "audit"
    / "external_sandbox_validation_call_offline_preparation_implementation_acceptance_gate"
    / "final_verdict.json"
)
READINESS_PLAN_PATH = (
    ROOT
    / "docs"
    / "runtime"
    / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_READINESS_PLAN.md"
)
READINESS_GATE_PATH = (
    ROOT
    / "docs"
    / "runtime"
    / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_READINESS_GATE.md"
)

EXPECTED_RESIDUALS = [
    "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
    "PLATFORM_INTEGRATION_NOT_ENABLED",
    "PUBLISH_RESULT_HISTORY_STILL_SHORT",
    "EXTERNAL_CALL_NOT_IMPLEMENTED",
    "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED",
]

FORBIDDEN_TRUE_ASSIGNMENTS = [
    '"runtime_integration_authorized": true',
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
    '"production_residual_closure_authorized": true',
]
FORBIDDEN_IMPORT_PATTERN = re.compile(
    r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|dns|googleapiclient|boto3)\b",
    re.MULTILINE,
)


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
    acceptance_verdict, acceptance_error = _load_json(ACCEPTANCE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [ACCEPTANCE_REVIEW_PATH, READINESS_PLAN_PATH, READINESS_GATE_PATH]
    }
    required_artifacts = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [ACCEPTANCE_RUNNER_PATH, ACCEPTANCE_VERDICT_PATH]
    }
    checks = {
        "required_docs_present": all(required_docs.values()),
        "required_artifacts_present": all(required_artifacts.values()),
        "acceptance_artifact_json_valid": not acceptance_error,
        "prior_acceptance_gate_verdict_acceptable": acceptance_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "prior_acceptance_no_blocking_failures": acceptance_verdict.get("blocking_failures") == [],
        "prior_acceptance_no_critical_failures": acceptance_verdict.get("metrics", {}).get("critical_failures", 1) == 0,
        "prior_acceptance_implementation_present": acceptance_verdict.get("implementation_present") is True,
        "prior_acceptance_external_call_unauthorized": acceptance_verdict.get("external_call_authorized") is False,
        "prior_acceptance_runtime_integration_unauthorized": acceptance_verdict.get("runtime_integration_authorized")
        is False,
        "prior_acceptance_production_residuals_open": acceptance_verdict.get("production_residuals_remain_open") is True,
    }
    return {
        "required_docs": required_docs,
        "required_artifacts": required_artifacts,
        "acceptance_artifact_error": acceptance_error,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _non_authorization_review() -> dict[str, Any]:
    plan = _read(READINESS_PLAN_PATH)
    gate = _read(READINESS_GATE_PATH)
    runner = _read(Path(__file__))
    combined = f"{plan}\n{gate}"
    forbidden_true_assignments = [fragment for fragment in FORBIDDEN_TRUE_ASSIGNMENTS if fragment in combined.lower()]
    forbidden_runner_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(runner)]
    required_false_fragments = [
        '"runtime_integration_authorized": false',
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
        '"production_residual_closure_authorized": false',
    ]
    checks = {
        "all_required_false_fragments_present": _contains_all(combined, required_false_fragments),
        "no_true_authorization_fragments": not forbidden_true_assignments,
        "runner_has_no_forbidden_network_imports": not forbidden_runner_imports,
        "plan_says_no_runtime_integration": "It must not authorize runtime integration." in plan,
        "plan_says_no_external_call": "It must not authorize external calls." in plan,
        "gate_says_no_runtime_integration": "It must not authorize runtime integration." in gate,
        "gate_says_no_external_call": "It must not authorize external calls." in gate,
        "next_possible_step_readiness_gate_only": '"next_possible_step": "READINESS_GATE_ONLY"' in plan
        and '"next_possible_step": "READINESS_GATE_ONLY"' in gate,
    }
    return {
        "required_false_fragments": required_false_fragments,
        "forbidden_true_assignments": forbidden_true_assignments,
        "forbidden_runner_imports": forbidden_runner_imports,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _readiness_evidence_review() -> dict[str, Any]:
    plan = _read(READINESS_PLAN_PATH)
    required_evidence = [
        "unit_tests_pass",
        "acceptance_gate_verdict",
        "deterministic_replay",
        "forbidden_imports_detected",
        "runtime_wiring_detected",
        "external_call_authorized",
        "runtime_integration_authorized",
        "production_residuals_remain_open",
    ]
    required_dimensions = [
        "file scope stability",
        "deterministic behavior",
        "test stability",
        "static forbidden-surface scan",
        "non-authorization fields",
        "dependency blocking semantics",
        "incident hook safety",
        "residual monitoring state",
        "boundary preservation",
        "handoff contract clarity",
        "no hidden runtime wiring",
    ]
    required_handoff = [
        "Which runtime component would call the preparation builder?",
        "Which exact inputs would be passed?",
        "Which output fields would be consumed?",
        "Where would preparation traces be stored?",
        "How would blocking reasons be surfaced?",
        "How would `preparation_complete=true` be prevented from becoming execution authorization?",
        "How would Account Health `HOLD` remain blocking?",
        "How would QC non-publishable remain blocking?",
        "How would Strategy remain control layer?",
        "How would Orchestrator remain coordinator only?",
    ]
    checks = {
        "readiness_plan_created_true": '"readiness_plan_created": true' in plan,
        "readiness_evidence_required": _contains_all(plan, required_evidence),
        "readiness_dimensions_present": _contains_all(plan, required_dimensions),
        "handoff_questions_required": _contains_all(plan, required_handoff),
        "runtime_integration_plan_is_future_only": "That future plan may discuss runtime integration design." in plan
        and "It must not implement runtime integration." in plan,
        "local_preparation_not_execution_readiness": "Runtime integration readiness is not runtime integration." in plan
        and "Offline preparation remains offline." in plan,
    }
    return {
        "required_evidence": required_evidence,
        "required_dimensions": required_dimensions,
        "required_handoff_questions": required_handoff,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    plan = _read(READINESS_PLAN_PATH)
    gate = _read(READINESS_GATE_PATH)
    acceptance_verdict, _ = _load_json(ACCEPTANCE_VERDICT_PATH)
    combined = f"{plan}\n{gate}"
    residuals_in_docs = [residual for residual in EXPECTED_RESIDUALS if residual in combined]
    acceptance_residuals = acceptance_verdict.get("residual_monitoring", [])
    checks = {
        "expected_residuals_present_in_docs": residuals_in_docs == EXPECTED_RESIDUALS,
        "expected_residuals_present_in_acceptance_verdict": all(
            residual in acceptance_residuals for residual in EXPECTED_RESIDUALS
        ),
        "production_residuals_remain_open": "production residuals remain open" in combined,
        "offline_maturity_cannot_close_production_residuals": "Offline preparation maturity cannot close production residuals."
        in plan,
    }
    return {
        "expected_residuals": EXPECTED_RESIDUALS,
        "residuals_in_docs": residuals_in_docs,
        "acceptance_residuals": acceptance_residuals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_review() -> dict[str, Any]:
    plan = _read(READINESS_PLAN_PATH)
    gate = _read(READINESS_GATE_PATH)
    combined = f"{plan}\n{gate}"
    checks = {
        "qc_non_publishable_preserved": "QC non-publishable" in combined,
        "account_health_hold_preserved": "Account Health `HOLD`" in combined,
        "strategy_boundary_preserved": "Strategy remains control layer" in plan
        or "Strategy remains the control layer" in gate,
        "orchestrator_boundary_preserved": "Orchestrator remains coordinator" in plan
        or "Orchestrator remains a coordinator" in gate,
        "publisher_not_external_execution_client": "Publisher may govern publication, but is not an external execution client."
        in gate,
        "core_pipeline_unchanged": "Core pipeline remains unchanged." in gate,
        "no_runtime_wiring_authorized": "No runtime wiring may be created." in gate,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _scenario_outputs(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    checks = {
        **reviews["preconditions"]["checks"],
        **reviews["non_authorization_review"]["checks"],
        **reviews["readiness_evidence_review"]["checks"],
        **reviews["residual_monitoring_review"]["checks"],
        **reviews["boundary_review"]["checks"],
    }
    scenario_names = [
        "readiness_plan_exists",
        "prior_acceptance_gate_verdict_acceptable",
        "readiness_plan_created_true",
        "runtime_integration_authorized_false",
        "external_call_authorized_false",
        "next_possible_step_readiness_gate_only",
        "http_sdk_endpoint_dns_api_unauthorized",
        "credential_value_access_unauthorized",
        "request_transformation_unauthorized",
        "transport_payload_unauthorized",
        "upload_scheduler_publish_unauthorized",
        "production_residuals_remain_open",
        "readiness_evidence_required",
        "handoff_questions_required",
        "runtime_integration_plan_is_future_only",
        "no_runtime_wiring_authorized",
        "local_preparation_not_execution_readiness",
        "boundary_preserved",
    ]
    scenario_checks = {
        "readiness_plan_exists": checks["required_docs_present"],
        "prior_acceptance_gate_verdict_acceptable": checks["prior_acceptance_gate_verdict_acceptable"],
        "readiness_plan_created_true": checks["readiness_plan_created_true"],
        "runtime_integration_authorized_false": checks["all_required_false_fragments_present"],
        "external_call_authorized_false": checks["all_required_false_fragments_present"],
        "next_possible_step_readiness_gate_only": checks["next_possible_step_readiness_gate_only"],
        "http_sdk_endpoint_dns_api_unauthorized": checks["all_required_false_fragments_present"],
        "credential_value_access_unauthorized": checks["all_required_false_fragments_present"],
        "request_transformation_unauthorized": checks["all_required_false_fragments_present"],
        "transport_payload_unauthorized": checks["all_required_false_fragments_present"],
        "upload_scheduler_publish_unauthorized": checks["all_required_false_fragments_present"],
        "production_residuals_remain_open": checks["production_residuals_remain_open"],
        "readiness_evidence_required": checks["readiness_evidence_required"],
        "handoff_questions_required": checks["handoff_questions_required"],
        "runtime_integration_plan_is_future_only": checks["runtime_integration_plan_is_future_only"],
        "no_runtime_wiring_authorized": checks["no_runtime_wiring_authorized"],
        "local_preparation_not_execution_readiness": checks["local_preparation_not_execution_readiness"],
        "boundary_preserved": checks["qc_non_publishable_preserved"]
        and checks["account_health_hold_preserved"]
        and checks["strategy_boundary_preserved"]
        and checks["orchestrator_boundary_preserved"],
    }
    return [
        _scenario(name, scenario_checks[name], {"expected": "readiness_plan_audit_only"})
        for name in scenario_names
    ]


def _checklist_results(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[tuple[str, bool]] = []
    for review_name in [
        "preconditions",
        "non_authorization_review",
        "readiness_evidence_review",
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
        "readiness_evidence_review": _readiness_evidence_review(),
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
        "readiness_plan_created": True,
        "runtime_integration_authorized": False,
        "external_call_authorized": False,
        "production_residuals_closed": False,
        "silent_failures_detected": False,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_READINESS_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "readiness_plan_created": True,
        "runtime_integration_authorized": False,
        "external_call_authorized": False,
        "next_possible_step": "READINESS_GATE_ONLY",
        "production_residuals_remain_open": True,
        "scenario_pass_count": f"{scenario_pass_count}/{len(scenarios)}",
        "checklist_pass_count": f"{checklist_pass_count}/{len(checklist)}",
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": EXPECTED_RESIDUALS,
        "recommendation": (
            "PROCEED_TO_RUNTIME_INTEGRATION_READINESS_GATE_REVIEW"
            if verdict != "HOLD"
            else "HOLD_BEFORE_RUNTIME_INTEGRATION_READINESS"
        ),
    }

    _write_json(NON_AUTHORIZATION_REVIEW_PATH, reviews["non_authorization_review"])
    _write_json(READINESS_EVIDENCE_REVIEW_PATH, reviews["readiness_evidence_review"])
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
