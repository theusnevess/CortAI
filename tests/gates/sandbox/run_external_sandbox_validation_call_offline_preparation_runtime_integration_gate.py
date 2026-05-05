from __future__ import annotations

import ast
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_validation_call_offline_preparation_runtime_integration_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
NON_AUTHORIZATION_REVIEW_PATH = AUDIT_DIR / "non_authorization_review.json"
REFERENCE_HANDOFF_REVIEW_PATH = AUDIT_DIR / "reference_handoff_review.json"
BOUNDARY_REVIEW_PATH = AUDIT_DIR / "boundary_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
STATIC_REVIEW_PATH = AUDIT_DIR / "static_review.json"

ACCEPTANCE_REVIEW_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "offline-preparation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_ACCEPTANCE_REVIEW.md"
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
READINESS_GATE_RUNNER_PATH = (
    ROOT / "tests" / "run_external_sandbox_validation_call_offline_preparation_runtime_integration_readiness_gate.py"
)
READINESS_VERDICT_PATH = (
    ROOT
    / "OUT"
    / "audit"
    / "external_sandbox_validation_call_offline_preparation_runtime_integration_readiness_gate"
    / "final_verdict.json"
)
READINESS_REVIEW_PATH = (
    ROOT
    / "docs"
    / "runtime"
    / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_READINESS_GATE_REVIEW.md"
)
RUNTIME_INTEGRATION_PLAN_PATH = (
    ROOT
    / "docs"
    / "runtime"
    / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_PLAN.md"
)
RUNTIME_INTEGRATION_GATE_PATH = (
    ROOT
    / "docs"
    / "runtime"
    / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_GATE.md"
)
OFFLINE_PREPARATION_FILES = [
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_validation_call_preparation.py",
    ROOT
    / "backend"
    / "app"
    / "creative"
    / "agents"
    / "publisher"
    / "external_sandbox_validation_call_preparation_security.py",
]

EXPECTED_RESIDUALS = [
    "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
    "PLATFORM_INTEGRATION_NOT_ENABLED",
    "PUBLISH_RESULT_HISTORY_STILL_SHORT",
    "EXTERNAL_CALL_NOT_IMPLEMENTED",
    "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED",
]

REQUIRED_FALSE_FRAGMENTS = [
    '"implementation_authorized": false',
    '"runtime_integration_authorized": false',
    '"runtime_wiring_authorized": false',
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

FORBIDDEN_TRUE_ASSIGNMENTS = [fragment.replace(": false", ": true") for fragment in REQUIRED_FALSE_FRAGMENTS]
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


def _contains_all(text: str, fragments: list[str]) -> bool:
    return all(fragment in text for fragment in fragments)


def _scenario(name: str, passed: bool, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scenario": name,
        "passed": bool(passed),
        "failure_reason": None if passed else "SCENARIO_FAILED",
        "evidence": evidence or {},
    }


def _imported_modules(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ["<syntax-error>"]
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return sorted(dict.fromkeys(modules))


def _preconditions() -> dict[str, Any]:
    readiness_verdict, readiness_error = _load_json(READINESS_VERDICT_PATH)
    required_artifacts = {
        str(path.relative_to(ROOT)).replace("\\", "/"): path.exists()
        for path in [
            ACCEPTANCE_REVIEW_PATH,
            READINESS_PLAN_PATH,
            READINESS_GATE_PATH,
            READINESS_GATE_RUNNER_PATH,
            READINESS_VERDICT_PATH,
            READINESS_REVIEW_PATH,
            RUNTIME_INTEGRATION_PLAN_PATH,
            RUNTIME_INTEGRATION_GATE_PATH,
        ]
    }
    checks = {
        "required_artifacts_present": all(required_artifacts.values()),
        "readiness_final_verdict_json_valid": not readiness_error,
        "readiness_verdict_acceptable": readiness_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "readiness_no_blocking_failures": readiness_verdict.get("blocking_failures") == [],
        "readiness_no_critical_failures": readiness_verdict.get("metrics", {}).get("critical_failures", 1) == 0,
        "readiness_scenario_count_expected": readiness_verdict.get("scenario_pass_count") == "18/18",
        "readiness_checklist_count_expected": readiness_verdict.get("checklist_pass_count") == "35/35",
        "readiness_runtime_integration_unauthorized": readiness_verdict.get("runtime_integration_authorized") is False,
        "readiness_external_call_unauthorized": readiness_verdict.get("external_call_authorized") is False,
        "readiness_production_residuals_open": readiness_verdict.get("production_residuals_remain_open") is True,
    }
    return {
        "required_artifacts": required_artifacts,
        "readiness_artifact_error": readiness_error,
        "readiness_verdict": readiness_verdict,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _non_authorization_review() -> dict[str, Any]:
    plan = _read(RUNTIME_INTEGRATION_PLAN_PATH)
    gate = _read(RUNTIME_INTEGRATION_GATE_PATH)
    combined = f"{plan}\n{gate}"
    combined_lower = combined.lower()
    forbidden_true_assignments = [fragment for fragment in FORBIDDEN_TRUE_ASSIGNMENTS if fragment in combined_lower]
    checks = {
        "all_required_false_fragments_present": _contains_all(combined_lower, REQUIRED_FALSE_FRAGMENTS),
        "no_true_authorization_fragments": not forbidden_true_assignments,
        "plan_says_planning_only": "This is a planning artifact only." in plan,
        "gate_says_audit_only": "This is an audit-only gate specification." in gate,
        "plan_says_no_runtime_integration": "It does not authorize runtime integration" in plan,
        "plan_says_no_runtime_wiring": "runtime_wiring_authorized" in plan and "false" in plan,
        "plan_says_no_external_call": "It must not authorize external calls." in plan
        or "external calls" in plan and "does not authorize" in plan,
        "gate_says_no_implementation": "It does not authorize implementation" in gate,
        "gate_says_no_external_call": "external calls" in gate and "does not authorize" in gate,
    }
    return {
        "required_false_fragments": REQUIRED_FALSE_FRAGMENTS,
        "forbidden_true_assignments": forbidden_true_assignments,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _reference_handoff_review() -> dict[str, Any]:
    plan = _read(RUNTIME_INTEGRATION_PLAN_PATH)
    gate = _read(RUNTIME_INTEGRATION_GATE_PATH)
    combined = f"{plan}\n{gate}"
    allowed_refs = [
        "artifact_manifest_ref",
        "metadata_payload_ref",
        "qc_trace_ref",
        "account_health_trace_ref",
        "strategy_ref",
        "publish_eligibility_trace_ref",
        "preparation_trace_ref",
        "validation_summary_ref",
    ]
    forbidden_payload_terms = [
        "endpoint",
        "HTTP method",
        "request headers",
        "authorization headers",
        "request body",
        "transport payload",
        "media bytes",
        "upload URL",
        "publish URL",
        "scheduler job ID",
        "production receipt",
        "production URL",
        "production `platform_content_id`",
        "post-publish metrics",
        "expected performance",
        "forecast",
        "causal claim",
    ]
    checks = {
        "allowed_reference_labels_present": _contains_all(combined, allowed_refs),
        "forbidden_payload_terms_called_out": _contains_all(gate, forbidden_payload_terms),
        "references_do_not_become_payloads_invariant_present": '"references_do_not_become_payloads": true' in gate,
        "reference_to_payload_is_hold": "turns a reference into an executable payload" in gate
        and "the verdict must be `HOLD`" in gate,
        "runtime_effect_trace_append_only": '"runtime_effect": "local_trace_append_only"' in plan
        and '"runtime_effect_allowed": "local_trace_append_only"' in gate,
        "external_effect_none": '"external_effect": "none"' in plan and '"external_effect_allowed": "none"' in gate,
        "trace_shape_does_not_authorize_execution": "Runtime integration of offline preparation does not authorize external execution."
        in plan,
    }
    return {
        "allowed_refs": allowed_refs,
        "forbidden_payload_terms": forbidden_payload_terms,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_review() -> dict[str, Any]:
    plan = _read(RUNTIME_INTEGRATION_PLAN_PATH)
    gate = _read(RUNTIME_INTEGRATION_GATE_PATH)
    combined = f"{plan}\n{gate}"
    checks = {
        "publisher_not_external_execution_client": "not an external execution client" in combined,
        "qc_boundary_preserved": "QC remains final artifact evaluator" in combined,
        "account_health_hold_preserved": "Account Health `HOLD`" in combined,
        "strategy_boundary_preserved": "Strategy remains control layer" in combined
        or "Strategy remains the control layer" in combined,
        "orchestrator_boundary_preserved": "Orchestrator remains coordinator" in combined
        or "Orchestrator remains a coordinator" in combined,
        "no_hidden_runtime_step": "no_hidden_runtime_step" in gate
        and "hidden new runtime step" in gate,
        "attribution_boundary_preserved": "Attribution receives no production causal evidence" in combined,
        "experiment_boundary_preserved": "Experiment receives no publish authority" in combined,
        "core_pipeline_preserved": "Core pipeline remains unchanged" in gate
        or "Core pipeline remains frozen" in plan,
        "missing_evidence_not_success": "Missing runtime evidence does not become success." in gate
        or "missing runtime evidence as success" in plan,
        "missing_refs_fail_closed": "Missing references fail closed." in gate
        or "fail closed when required references are absent" in plan,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    plan = _read(RUNTIME_INTEGRATION_PLAN_PATH)
    gate = _read(RUNTIME_INTEGRATION_GATE_PATH)
    readiness_verdict, _ = _load_json(READINESS_VERDICT_PATH)
    combined = f"{plan}\n{gate}"
    residuals_in_docs = [residual for residual in EXPECTED_RESIDUALS if residual in combined]
    readiness_residuals = readiness_verdict.get("residual_monitoring", [])
    checks = {
        "expected_residuals_present_in_docs": residuals_in_docs == EXPECTED_RESIDUALS,
        "expected_residuals_present_in_readiness_verdict": all(
            residual in readiness_residuals for residual in EXPECTED_RESIDUALS
        ),
        "production_residuals_remain_open": "production residuals remain open" in combined.lower()
        or "production_residuals_remain_open" in combined,
        "plan_does_not_reduce_production_residuals": "It must not reduce:" in plan
        and "production publish evidence residual" in plan,
        "gate_hold_on_residual_closure": "closes production residuals" in gate,
    }
    return {
        "expected_residuals": EXPECTED_RESIDUALS,
        "residuals_in_docs": residuals_in_docs,
        "readiness_residuals": readiness_residuals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _static_review() -> dict[str, Any]:
    runner_source = _read(Path(__file__))
    offline_sources = "\n".join(_read(path) for path in OFFLINE_PREPARATION_FILES)
    runner_imports = _imported_modules(runner_source)
    offline_imports = _imported_modules(offline_sources)
    runtime_integration_candidates = sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in (ROOT / "backend" / "app" / "creative" / "agents" / "publisher").glob("*runtime_integration*.py")
    )
    runner_forbidden_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(runner_source)]
    offline_forbidden_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(offline_sources)]
    runner_runtime_imports = [module for module in runner_imports if module.startswith("app.creative")]
    checks = {
        "runner_has_no_forbidden_network_imports": not runner_forbidden_imports,
        "offline_preparation_has_no_forbidden_network_imports": not offline_forbidden_imports,
        "no_runtime_integration_code_files_exist": not runtime_integration_candidates,
        "runner_does_not_import_runtime_modules": not runner_runtime_imports,
        "runner_is_read_only_gate": "subprocess" not in runner_imports and "pytest" not in runner_imports,
    }
    return {
        "runner_imports": runner_imports,
        "offline_imports": offline_imports,
        "runner_runtime_imports": runner_runtime_imports,
        "runner_forbidden_imports": runner_forbidden_imports,
        "offline_forbidden_imports": offline_forbidden_imports,
        "runtime_integration_candidate_files": runtime_integration_candidates,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _scenario_outputs(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    scenario_checks = {
        "runtime_integration_plan_exists": RUNTIME_INTEGRATION_PLAN_PATH.exists(),
        "readiness_gate_review_exists": READINESS_REVIEW_PATH.exists(),
        "readiness_gate_verdict_acceptable": reviews["preconditions"]["checks"]["readiness_verdict_acceptable"],
        "runtime_integration_authorized_false": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "runtime_wiring_authorized_false": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "implementation_authorized_false": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "external_call_authorized_false": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "http_sdk_endpoint_dns_api_unauthorized": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "credential_value_access_unauthorized": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "request_transformation_unauthorized": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "transport_payload_unauthorized": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "upload_scheduler_publish_unauthorized": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "production_url_platform_content_id_receipt_unauthorized": reviews["non_authorization_review"]["checks"][
            "all_required_false_fragments_present"
        ],
        "production_residuals_remain_open": reviews["residual_monitoring_review"]["checks"][
            "production_residuals_remain_open"
        ],
        "integration_mode_trace_only": "trace_only" in _read(RUNTIME_INTEGRATION_GATE_PATH),
        "offline_only_preserved": "offline-only" in _read(RUNTIME_INTEGRATION_GATE_PATH),
        "runtime_effect_local_trace_append_only": reviews["reference_handoff_review"]["checks"][
            "runtime_effect_trace_append_only"
        ],
        "external_effect_none": reviews["reference_handoff_review"]["checks"]["external_effect_none"],
        "reference_only_handoff": reviews["reference_handoff_review"]["checks"]["allowed_reference_labels_present"],
        "payload_like_fields_forbidden": reviews["reference_handoff_review"]["checks"][
            "forbidden_payload_terms_called_out"
        ],
        "headers_body_endpoint_forbidden": reviews["reference_handoff_review"]["checks"][
            "forbidden_payload_terms_called_out"
        ],
        "media_bytes_forbidden": reviews["reference_handoff_review"]["checks"]["forbidden_payload_terms_called_out"],
        "no_hidden_runtime_step": reviews["boundary_review"]["checks"]["no_hidden_runtime_step"],
        "orchestrator_boundary_preserved": reviews["boundary_review"]["checks"]["orchestrator_boundary_preserved"],
        "publisher_not_external_execution_client": reviews["boundary_review"]["checks"][
            "publisher_not_external_execution_client"
        ],
        "qc_boundary_preserved": reviews["boundary_review"]["checks"]["qc_boundary_preserved"],
        "account_health_hold_preserved": reviews["boundary_review"]["checks"]["account_health_hold_preserved"],
        "strategy_boundary_preserved": reviews["boundary_review"]["checks"]["strategy_boundary_preserved"],
        "missing_references_fail_closed": reviews["boundary_review"]["checks"]["missing_refs_fail_closed"],
        "trace_not_success": "trace_not_success" in _read(RUNTIME_INTEGRATION_GATE_PATH),
        "eligibility_not_publish_authorization": "eligibility_not_publish_authorization" in _read(
            RUNTIME_INTEGRATION_GATE_PATH
        ),
        "runtime_integration_plan_does_not_authorize_code": reviews["non_authorization_review"]["checks"][
            "plan_says_planning_only"
        ]
        and reviews["non_authorization_review"]["checks"]["gate_says_no_implementation"],
        "boundary_statement_present": "Runtime integration of offline preparation does not authorize external execution."
        in _read(RUNTIME_INTEGRATION_PLAN_PATH),
        "next_step_gate_runner_only": "tests/gates/sandbox/run_external_sandbox_validation_call_offline_preparation_runtime_integration_gate.py"
        in _read(RUNTIME_INTEGRATION_GATE_PATH),
    }
    return [
        _scenario(name, passed, {"expected": "runtime_integration_gate_audit_only"})
        for name, passed in scenario_checks.items()
    ]


def _checklist_results(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    plan = _read(RUNTIME_INTEGRATION_PLAN_PATH)
    gate = _read(RUNTIME_INTEGRATION_GATE_PATH)
    readiness_verdict, _ = _load_json(READINESS_VERDICT_PATH)
    checklist = {
        "runtime_integration_plan_exists": RUNTIME_INTEGRATION_PLAN_PATH.exists(),
        "readiness_gate_review_exists": READINESS_REVIEW_PATH.exists(),
        "readiness_final_verdict_exists": READINESS_VERDICT_PATH.exists(),
        "readiness_verdict_acceptable": readiness_verdict.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "readiness_blocking_failures_empty": readiness_verdict.get("blocking_failures") == [],
        "plan_says_planning_only": "This is a planning artifact only." in plan,
        "plan_says_implementation_not_authorized": '"implementation_authorized": false' in plan,
        "plan_says_runtime_integration_not_authorized": '"runtime_integration_authorized": false' in plan,
        "plan_says_runtime_wiring_not_authorized": '"runtime_wiring_authorized": false' in plan,
        "plan_says_external_calls_not_authorized": '"external_call_authorized": false' in plan,
        "plan_says_request_transformation_not_authorized": '"request_transformation_authorized": false' in plan,
        "plan_says_transport_payload_not_authorized": '"transport_payload_authorized": false' in plan,
        "plan_says_http_clients_not_allowed": '"http_client_allowed": false' in plan,
        "plan_says_platform_sdks_not_allowed": '"platform_sdk_allowed": false' in plan,
        "plan_says_endpoints_not_allowed": '"endpoint_allowed": false' in plan,
        "plan_says_dns_not_allowed": '"dns_network_allowed": false' in plan,
        "plan_says_credential_value_access_not_authorized": '"credential_value_access_authorized": false' in plan,
        "plan_says_upload_not_authorized": '"upload_authorized": false' in plan,
        "plan_says_scheduler_not_authorized": '"scheduler_authorized": false' in plan,
        "plan_says_real_publish_not_authorized": '"real_publish_authorized": false' in plan,
        "plan_keeps_production_residuals_open": "These residuals remain open:" in plan,
        "plan_defines_reference_only_handoff": "Candidate runtime handoff" in plan
        and reviews["reference_handoff_review"]["checks"]["allowed_reference_labels_present"],
        "plan_forbids_endpoint_body_header_payload_fields": reviews["reference_handoff_review"]["checks"][
            "forbidden_payload_terms_called_out"
        ],
        "plan_preserves_trace_only_integration": "trace-only" in plan or "trace_only" in gate,
        "plan_preserves_offline_only_integration": "offline-only" in plan or "offline-only" in gate,
        "plan_defines_local_trace_append_only": '"runtime_effect": "local_trace_append_only"' in plan,
        "plan_defines_external_effect_none": '"external_effect": "none"' in plan,
        "plan_preserves_qc_boundary": reviews["boundary_review"]["checks"]["qc_boundary_preserved"],
        "plan_preserves_account_health_hold": reviews["boundary_review"]["checks"]["account_health_hold_preserved"],
        "plan_preserves_strategy_boundary": reviews["boundary_review"]["checks"]["strategy_boundary_preserved"],
        "plan_preserves_orchestrator_boundary": reviews["boundary_review"]["checks"]["orchestrator_boundary_preserved"],
        "plan_forbids_hidden_runtime_steps": "hidden runtime step" in gate or "hidden new runtime step" in gate,
        "plan_preserves_attribution_boundary": reviews["boundary_review"]["checks"]["attribution_boundary_preserved"],
        "plan_preserves_experiment_boundary": reviews["boundary_review"]["checks"]["experiment_boundary_preserved"],
        "plan_preserves_core_pipeline_boundary": reviews["boundary_review"]["checks"]["core_pipeline_preserved"],
    }
    return [
        {
            "check": name,
            "passed": bool(passed),
            "failure_reason": None if passed else "CHECK_FAILED",
        }
        for name, passed in checklist.items()
    ]


def main() -> int:
    _reset_audit_dir()

    reviews = {
        "preconditions": _preconditions(),
        "non_authorization_review": _non_authorization_review(),
        "reference_handoff_review": _reference_handoff_review(),
        "boundary_review": _boundary_review(),
        "residual_monitoring_review": _residual_monitoring_review(),
        "static_review": _static_review(),
    }
    scenarios = _scenario_outputs(reviews)
    checklist = _checklist_results(reviews)

    scenario_pass_count = sum(1 for item in scenarios if item["passed"])
    checklist_pass_count = sum(1 for item in checklist if item["passed"])
    blocking_failures = [item["scenario"] for item in scenarios if not item["passed"]] + [
        item["check"] for item in checklist if not item["passed"]
    ]
    for review_name, review in reviews.items():
        if not review["passed"]:
            blocking_failures.append(review_name)
    blocking_failures = sorted(dict.fromkeys(blocking_failures))
    critical_failures = len(blocking_failures)
    verdict = "GO_WITH_MONITORING" if not blocking_failures else "HOLD"

    metrics = {
        "critical_failures": critical_failures,
        "blocking_failures_count": len(blocking_failures),
        "scenario_count": len(scenarios),
        "scenario_pass_count": scenario_pass_count,
        "checklist_count": len(checklist),
        "checklist_pass_count": checklist_pass_count,
        "runtime_integration_plan_created": RUNTIME_INTEGRATION_PLAN_PATH.exists(),
        "runtime_integration_authorized": False,
        "runtime_wiring_authorized": False,
        "implementation_authorized": False,
        "external_call_authorized": False,
        "request_transformation_authorized": False,
        "transport_payload_authorized": False,
        "reference_handoff_valid": reviews["reference_handoff_review"]["passed"],
        "no_hidden_runtime_step": reviews["boundary_review"]["checks"]["no_hidden_runtime_step"],
        "production_residuals_closed": False,
        "silent_failures_detected": False,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_RUNTIME_INTEGRATION_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_integration_plan_created": RUNTIME_INTEGRATION_PLAN_PATH.exists(),
        "runtime_integration_authorized": False,
        "runtime_wiring_authorized": False,
        "implementation_authorized": False,
        "external_call_authorized": False,
        "request_transformation_authorized": False,
        "transport_payload_authorized": False,
        "reference_handoff_valid": reviews["reference_handoff_review"]["passed"],
        "no_hidden_runtime_step": reviews["boundary_review"]["checks"]["no_hidden_runtime_step"],
        "production_residuals_remain_open": True,
        "scenario_pass_count": f"{scenario_pass_count}/{len(scenarios)}",
        "checklist_pass_count": f"{checklist_pass_count}/{len(checklist)}",
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": EXPECTED_RESIDUALS,
        "recommendation": (
            "PROCEED_TO_RUNTIME_INTEGRATION_GATE_REVIEW"
            if verdict != "HOLD"
            else "HOLD_BEFORE_RUNTIME_INTEGRATION_REVIEW"
        ),
    }

    _write_json(NON_AUTHORIZATION_REVIEW_PATH, reviews["non_authorization_review"])
    _write_json(REFERENCE_HANDOFF_REVIEW_PATH, reviews["reference_handoff_review"])
    _write_json(BOUNDARY_REVIEW_PATH, reviews["boundary_review"])
    _write_json(RESIDUAL_MONITORING_REVIEW_PATH, reviews["residual_monitoring_review"])
    _write_json(STATIC_REVIEW_PATH, reviews["static_review"])
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(METRICS_PATH, metrics)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
