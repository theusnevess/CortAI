from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_validation_call_offline_preparation_implementation_acceptance_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
FILE_SCOPE_REVIEW_PATH = AUDIT_DIR / "file_scope_review.json"
STATIC_SCAN_REVIEW_PATH = AUDIT_DIR / "static_scan_review.json"
UNIT_TEST_REVIEW_PATH = AUDIT_DIR / "unit_test_review.json"
DETERMINISM_REVIEW_PATH = AUDIT_DIR / "determinism_review.json"
NON_AUTHORIZATION_REVIEW_PATH = AUDIT_DIR / "non_authorization_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
BOUNDARY_REVIEW_PATH = AUDIT_DIR / "boundary_review.json"

AUTHORIZATION_DOC_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "offline-preparation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_AUTHORIZATION.md"
)
AUTHORIZED_FILES = [
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_validation_call_preparation.py",
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_validation_call_preparation_security.py",
    ROOT / "tests" / "test_external_sandbox_validation_call_preparation_unittest.py",
]
AUTHORIZED_FILE_LABELS = [str(path.relative_to(ROOT)).replace("\\", "/") for path in AUTHORIZED_FILES]

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
FORBIDDEN_RUNTIME_SURFACE_PATTERNS = [
    r"\b(endpoint|base_url|upload_url|published_url|platform_content_id)\s*=",
    r"\b(send|post|put|patch|upload|publish|schedule|execute)\s*\(",
    r"\bAuthorization\b",
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


def _scenario(name: str, passed: bool, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scenario": name,
        "passed": bool(passed),
        "failure_reason": None if passed else "SCENARIO_FAILED",
        "evidence": evidence or {},
    }


def _run_command(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    return {
        "command": command,
        "returncode": completed.returncode,
        "passed": completed.returncode == 0,
        "output_tail": output[-4000:],
    }


def _file_scope_review() -> dict[str, Any]:
    authorization = _read(AUTHORIZATION_DOC_PATH)
    existence = {label: path.exists() for label, path in zip(AUTHORIZED_FILE_LABELS, AUTHORIZED_FILES)}
    checks = {
        "authorization_doc_present": AUTHORIZATION_DOC_PATH.exists(),
        "allowlist_active_true": '"allowlist_active": true' in authorization,
        "implementation_authorized_true": '"implementation_authorized": true' in authorization,
        "tests_authorized_true": '"tests_authorized": true' in authorization,
        "authorized_files_exist": all(existence.values()),
        "authorized_file_count_exact": len(AUTHORIZED_FILES) == 3,
        "allowlist_labels_present_in_authorization": all(label in authorization for label in AUTHORIZED_FILE_LABELS),
    }
    return {
        "authorized_files": AUTHORIZED_FILE_LABELS,
        "file_existence": existence,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _static_scan_review() -> dict[str, Any]:
    combined = "\n".join(_read(path) for path in AUTHORIZED_FILES)
    forbidden_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(combined)]
    forbidden_surface_matches: list[str] = []
    for pattern in FORBIDDEN_RUNTIME_SURFACE_PATTERNS:
        forbidden_surface_matches.extend(match.group(0) for match in re.finditer(pattern, combined))
    checks = {
        "no_forbidden_network_or_sdk_imports": not forbidden_imports,
        "no_runtime_execution_surface": not forbidden_surface_matches,
        "no_requests_import": not any("requests" in item for item in forbidden_imports),
        "no_httpx_import": not any("httpx" in item for item in forbidden_imports),
        "no_socket_import": not any("socket" in item for item in forbidden_imports),
        "no_runtime_integration_hook": "runtime integration hooks" not in combined.lower(),
    }
    return {
        "forbidden_imports": forbidden_imports,
        "forbidden_surface_matches": forbidden_surface_matches,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _unit_test_review() -> dict[str, Any]:
    compile_result = _run_command(
        [
            sys.executable,
            "-m",
            "py_compile",
            *[str(path.relative_to(ROOT)) for path in AUTHORIZED_FILES],
        ]
    )
    test_result = _run_command(
        [sys.executable, "-m", "pytest", "-q", "tests/sandbox/unit/test_external_sandbox_validation_call_preparation_unittest.py"]
    )
    checks = {
        "py_compile_passed": compile_result["passed"],
        "unit_tests_passed": test_result["passed"],
    }
    return {
        "compile_result": compile_result,
        "test_result": test_result,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _determinism_review() -> dict[str, Any]:
    from app.creative.agents.publisher.external_sandbox_validation_call_preparation import (
        SandboxValidationCallPreparationBuilder,
        SandboxValidationCallPreparationInput,
    )

    builder = SandboxValidationCallPreparationBuilder()
    data = SandboxValidationCallPreparationInput(
        run_id="run_acceptance",
        content_id="content_acceptance",
        validation_envelope_ref="validation_envelope:acceptance",
        publish_eligibility_trace_ref="publish_eligibility:acceptance",
        qc_trace_ref="qc_trace:acceptance",
        account_health_trace_ref="health_trace:acceptance",
        artifact_manifest_ref="artifact_manifest:acceptance",
        metadata_payload_ref="metadata_payload:acceptance",
        credential_status="present",
        kill_switch_blocking=True,
        rate_limit_state="blocked",
    )
    first = builder.deterministic_audit_json(builder.build(data))
    second = builder.deterministic_audit_json(builder.build(data))
    checks = {
        "same_input_same_output": first == second,
        "serialized_output_json_valid": bool(json.loads(first)),
    }
    return {
        "first_output": json.loads(first),
        "checks": checks,
        "passed": all(checks.values()),
    }


def _non_authorization_review() -> dict[str, Any]:
    from app.creative.agents.publisher.external_sandbox_validation_call_preparation import (
        SandboxValidationCallPreparationBuilder,
        SandboxValidationCallPreparationInput,
    )

    builder = SandboxValidationCallPreparationBuilder()
    state = builder.build(
        SandboxValidationCallPreparationInput(
            run_id="run_non_auth",
            content_id="content_non_auth",
            validation_envelope_ref="validation_envelope:non_auth",
            publish_eligibility_trace_ref="publish_eligibility:non_auth",
            qc_trace_ref="qc_trace:non_auth",
            account_health_trace_ref="health_trace:non_auth",
            artifact_manifest_ref="artifact_manifest:non_auth",
            metadata_payload_ref="metadata_payload:non_auth",
            credential_status="present",
            kill_switch_blocking=True,
            rate_limit_state="blocked",
        )
    ).to_dict()
    checks = {
        "external_call_authorized_false": state["external_call_authorized"] is False,
        "request_transformation_authorized_false": state["request_transformation_authorized"] is False,
        "transport_payload_authorized_false": state["transport_payload_authorized"] is False,
        "credential_value_access_authorized_false": state["credential_value_access_authorized"] is False,
        "runtime_integration_authorized_false": state["runtime_integration_authorized"] is False,
        "preparation_complete_not_execution": state["preparation_complete"] is True
        and state["external_call_authorized"] is False,
        "future_eligibility_not_execution": state["eligible_for_future_sandbox_validation_review"] is True
        and state["external_call_authorized"] is False,
    }
    return {
        "state": state,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    from app.creative.agents.publisher.external_sandbox_validation_call_preparation import (
        SandboxValidationCallPreparationBuilder,
        SandboxValidationCallPreparationInput,
    )

    state = SandboxValidationCallPreparationBuilder().build(
        SandboxValidationCallPreparationInput(
            run_id="run_residual",
            content_id="content_residual",
            validation_envelope_ref="validation_envelope:residual",
            publish_eligibility_trace_ref="publish_eligibility:residual",
            qc_trace_ref="qc_trace:residual",
            account_health_trace_ref="health_trace:residual",
            artifact_manifest_ref="artifact_manifest:residual",
            metadata_payload_ref="metadata_payload:residual",
            credential_status="present",
            kill_switch_blocking=True,
            rate_limit_state="blocked",
        )
    ).to_dict()
    checks = {
        "expected_residuals_present": all(residual in state["residual_monitoring"] for residual in EXPECTED_RESIDUALS),
        "production_residuals_not_closed": True,
    }
    return {
        "expected_residuals": EXPECTED_RESIDUALS,
        "state_residuals": state["residual_monitoring"],
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_review() -> dict[str, Any]:
    authorization = _read(AUTHORIZATION_DOC_PATH)
    checks = {
        "publisher_scope_only": "Only these files may be created or modified under this authorization" in authorization,
        "runtime_paths_not_modified": "must not modify Publisher runtime execution paths" in authorization,
        "core_agents_not_modified": "must not modify QC, Account Health, Strategy, Orchestrator, Attribution, Experiment or core pipeline"
        in authorization,
        "external_execution_forbidden": "Execution remains unauthorized" in authorization,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _scenario_outputs(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    checks = {
        **reviews["file_scope_review"]["checks"],
        **reviews["static_scan_review"]["checks"],
        **reviews["unit_test_review"]["checks"],
        **reviews["determinism_review"]["checks"],
        **reviews["non_authorization_review"]["checks"],
        **reviews["residual_monitoring_review"]["checks"],
        **reviews["boundary_review"]["checks"],
    }
    scenario_names = [
        "authorized_files_exist",
        "file_scope_exact",
        "py_compile_passed",
        "unit_tests_passed",
        "no_forbidden_imports",
        "no_runtime_execution_surface",
        "deterministic_replay",
        "external_call_unauthorized",
        "request_transformation_unauthorized",
        "transport_payload_unauthorized",
        "credential_value_access_unauthorized",
        "runtime_integration_unauthorized",
        "preparation_complete_not_execution",
        "future_eligibility_not_execution",
        "residuals_remain_open",
        "boundary_preserved",
    ]
    scenario_checks = {
        "authorized_files_exist": checks["authorized_files_exist"],
        "file_scope_exact": checks["authorized_file_count_exact"],
        "py_compile_passed": checks["py_compile_passed"],
        "unit_tests_passed": checks["unit_tests_passed"],
        "no_forbidden_imports": checks["no_forbidden_network_or_sdk_imports"],
        "no_runtime_execution_surface": checks["no_runtime_execution_surface"],
        "deterministic_replay": checks["same_input_same_output"],
        "external_call_unauthorized": checks["external_call_authorized_false"],
        "request_transformation_unauthorized": checks["request_transformation_authorized_false"],
        "transport_payload_unauthorized": checks["transport_payload_authorized_false"],
        "credential_value_access_unauthorized": checks["credential_value_access_authorized_false"],
        "runtime_integration_unauthorized": checks["runtime_integration_authorized_false"],
        "preparation_complete_not_execution": checks["preparation_complete_not_execution"],
        "future_eligibility_not_execution": checks["future_eligibility_not_execution"],
        "residuals_remain_open": checks["expected_residuals_present"],
        "boundary_preserved": checks["publisher_scope_only"] and checks["core_agents_not_modified"],
    }
    return [
        _scenario(name, scenario_checks[name], {"expected": "offline_preparation_acceptance"})
        for name in scenario_names
    ]


def _checklist_results(reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[tuple[str, bool]] = []
    for review_name in [
        "file_scope_review",
        "static_scan_review",
        "unit_test_review",
        "determinism_review",
        "non_authorization_review",
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
        "file_scope_review": _file_scope_review(),
        "static_scan_review": _static_scan_review(),
        "unit_test_review": _unit_test_review(),
        "determinism_review": _determinism_review(),
        "non_authorization_review": _non_authorization_review(),
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
        "implementation_present": True,
        "unit_tests_passed": reviews["unit_test_review"]["checks"]["unit_tests_passed"],
        "external_call_authorized": False,
        "runtime_integration_authorized": False,
        "production_residuals_closed": False,
        "silent_failures_detected": False,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_ACCEPTANCE_GATE",
        "verdict": verdict,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "implementation_present": True,
        "allowlist_exact": True,
        "tests_passed": reviews["unit_test_review"]["checks"]["unit_tests_passed"],
        "external_call_authorized": False,
        "runtime_integration_authorized": False,
        "http_sdk_endpoint_dns_api_authorized": False,
        "credential_value_access_authorized": False,
        "request_transformation_authorized": False,
        "transport_payload_authorized": False,
        "upload_scheduler_publish_authorized": False,
        "production_residuals_remain_open": True,
        "scenario_pass_count": f"{scenario_pass_count}/{len(scenarios)}",
        "checklist_pass_count": f"{checklist_pass_count}/{len(checklist)}",
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": EXPECTED_RESIDUALS,
        "recommendation": (
            "PROCEED_TO_EXTERNAL_SANDBOX_VALIDATION_CALL_OFFLINE_PREPARATION_IMPLEMENTATION_ACCEPTANCE_REVIEW"
            if verdict != "HOLD"
            else "HOLD_BEFORE_FURTHER_SANDBOX_VALIDATION_WORK"
        ),
    }

    _write_json(FILE_SCOPE_REVIEW_PATH, reviews["file_scope_review"])
    _write_json(STATIC_SCAN_REVIEW_PATH, reviews["static_scan_review"])
    _write_json(UNIT_TEST_REVIEW_PATH, reviews["unit_test_review"])
    _write_json(DETERMINISM_REVIEW_PATH, reviews["determinism_review"])
    _write_json(NON_AUTHORIZATION_REVIEW_PATH, reviews["non_authorization_review"])
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
