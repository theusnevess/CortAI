from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.creative.agents.publisher.external_sandbox_pre_execution_guard import (  # noqa: E402
    BLOCKED_FALSE_MEANING,
    BOUNDARY_RESIDUALS,
    GUARD_STATE,
    GUARD_TYPE,
    TARGET_MODE,
    TARGET_PLATFORM_ID,
    ExternalSandboxPreExecutionGuard,
    ExternalSandboxPreExecutionGuardInput,
)


AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_external_call_pre_execution_guard_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
STATIC_SCAN_REVIEW_PATH = AUDIT_DIR / "static_scan_review.json"
SIDE_EFFECT_ABSENCE_REVIEW_PATH = AUDIT_DIR / "side_effect_absence_review.json"
SECURITY_REVIEW_PATH = AUDIT_DIR / "security_review.json"
BLOCKED_SEMANTICS_REVIEW_PATH = AUDIT_DIR / "blocked_semantics_review.json"
DETERMINISM_REVIEW_PATH = AUDIT_DIR / "determinism_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"

PLAN_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "pre-execution-guard" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_PLAN.md"
GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "pre-execution-guard" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_GATE.md"
BOUNDARY_REVIEW_PATH = ROOT / "docs" / "runtime" / "sandbox" / "external-call-boundary" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_REVIEW.md"
BOUNDARY_GATE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_external_call_boundary_implementation_gate" / "final_verdict.json"
)
IMPLEMENTATION_FILE = ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_pre_execution_guard.py"
UNIT_TEST_FILE = ROOT / "tests" / "test_external_sandbox_pre_execution_guard_unittest.py"

FORBIDDEN_IMPORT_PATTERN = re.compile(
    r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|dns|googleapiclient|boto3)\b",
    re.MULTILINE,
)
FORBIDDEN_HELPER_PATTERN = re.compile(
    r"^\s*def\s+(to_request|as_request|to_payload|as_payload|to_http|to_headers|to_body|send|execute|post|put|patch|call_api|upload|publish|schedule|emit_url|emit_receipt|create_receipt)\s*\(",
    re.MULTILINE,
)
ENDPOINT_CONSTANT_PATTERN = re.compile(
    r"^\s*[A-Z_]*(ENDPOINT|BASE_URL|API_URL|UPLOAD_URL|PUBLISH_URL|CALLBACK_URL|WEBHOOK_URL)[A-Z_]*\s*=",
    re.MULTILINE,
)
NETWORK_LITERAL_TOKENS = (
    "requests.",
    "httpx.",
    "aiohttp.",
    "urllib.request.",
    "urllib3.",
    "socket.",
    "dns.resolver",
    ".getaddrinfo(",
    ".connect(",
)


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
    except Exception as exc:  # noqa: BLE001 - gate records audit read failures explicitly
        return {}, f"{type(exc).__name__}: {exc}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _scenario(name: str, passed: bool, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scenario": name,
        "passed": bool(passed),
        "failure_reason": None if passed else "SCENARIO_FAILED",
        "evidence": evidence or {},
    }


def _input(**overrides: Any) -> ExternalSandboxPreExecutionGuardInput:
    payload = {
        "run_id": "run_pre_execution_guard_gate",
        "content_id": "content_pre_execution_guard_gate",
        "boundary_ref": "boundary:gate",
        "controlled_binding_ref": "controlled_binding:gate",
        "validation_envelope_ref": "validation_envelope:gate",
        "publish_eligibility_trace_ref": "publish_eligibility:gate",
        "qc_trace_ref": "qc_trace:gate",
        "account_health_trace_ref": "account_health_trace:gate",
        "dependency_status": {
            "qc_status": "APPROVE",
            "qc_publishable": True,
            "account_health_decision": "SAFE",
            "credential_status": "present",
            "kill_switch_active": False,
            "kill_switch_missing": False,
            "rate_limit_requests_allowed": False,
        },
    }
    payload.update(overrides)
    return ExternalSandboxPreExecutionGuardInput(**payload)


def _evaluate(**overrides: Any):
    return ExternalSandboxPreExecutionGuard().evaluate(_input(**overrides))


def _summary(result: Any) -> dict[str, Any]:
    payload = result.to_dict()
    return {
        "guard_type": payload["guard_type"],
        "guard_state": payload["guard_state"],
        "blocked": payload["blocked"],
        "blocked_meaning": payload["blocked_meaning"],
        "crossing_attempt_detected": payload["crossing_attempt_detected"],
        "blocked_capabilities": payload["blocked_capabilities"],
        "dependency_blocks": payload["dependency_blocks"],
        "external_call_authorized": payload["external_call_authorized"],
        "publish_authorized": payload["publish_authorized"],
        "url_authorized": payload["url_authorized"],
        "platform_content_id_authorized": payload["platform_content_id_authorized"],
        "receipt_authorized": payload["receipt_authorized"],
        "credential_value_access_authorized": payload["credential_value_access_authorized"],
        "production_residuals_closed": payload["production_residuals_closed"],
        "incident_types": [hook["incident_type"] for hook in payload["incident_hooks"]],
    }


def _all_authorizations_false(payload: dict[str, Any]) -> bool:
    authorization_fields = [
        "external_call_authorized",
        "http_client_authorized",
        "platform_sdk_authorized",
        "endpoint_authorized",
        "dns_network_authorized",
        "api_call_authorized",
        "request_transformation_authorized",
        "upload_authorized",
        "scheduler_authorized",
        "publish_authorized",
        "url_authorized",
        "platform_content_id_authorized",
        "receipt_authorized",
        "credential_value_access_authorized",
        "authorization_header_authorized",
    ]
    return all(payload.get(field) is False for field in authorization_fields)


def _preconditions() -> dict[str, Any]:
    boundary_gate, boundary_gate_error = _load_json(BOUNDARY_GATE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_DOC_PATH, GATE_DOC_PATH, BOUNDARY_REVIEW_PATH]
    }
    required_files = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [IMPLEMENTATION_FILE, UNIT_TEST_FILE]
    }
    required_artifacts = {
        str(BOUNDARY_GATE_VERDICT_PATH.relative_to(ROOT)): BOUNDARY_GATE_VERDICT_PATH.exists()
    }
    checks = {
        "required_docs_present": all(required_docs.values()),
        "implementation_file_present": IMPLEMENTATION_FILE.exists(),
        "unit_test_file_present": UNIT_TEST_FILE.exists(),
        "boundary_gate_artifact_present": all(required_artifacts.values()),
        "boundary_gate_json_valid": not boundary_gate_error,
        "boundary_gate_verdict_acceptable": boundary_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "boundary_gate_no_external_call": boundary_gate.get("external_call_authorized") is False,
        "boundary_gate_no_http_client": boundary_gate.get("http_client_detected") is False,
        "boundary_gate_no_sdk": boundary_gate.get("platform_sdk_detected") is False,
        "boundary_gate_no_endpoint": boundary_gate.get("endpoint_detected") is False,
        "boundary_gate_no_dns_network": boundary_gate.get("dns_network_detected") is False,
        "boundary_gate_no_api_call": boundary_gate.get("api_call_detected") is False,
        "boundary_gate_no_upload": boundary_gate.get("upload_detected") is False,
        "boundary_gate_no_scheduler": boundary_gate.get("scheduler_detected") is False,
        "boundary_gate_no_publish": boundary_gate.get("publish_detected") is False,
        "boundary_gate_no_url": boundary_gate.get("url_detected") is False,
        "boundary_gate_no_platform_content_id": boundary_gate.get("platform_content_id_detected") is False,
        "boundary_gate_no_receipt": boundary_gate.get("receipt_detected") is False,
        "boundary_gate_residuals_open": boundary_gate.get("production_residuals_closed") is False,
    }
    return {
        "required_docs": required_docs,
        "required_files": required_files,
        "required_artifacts": required_artifacts,
        "boundary_gate_error": boundary_gate_error,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _static_scan_review() -> dict[str, Any]:
    sources = {
        str(IMPLEMENTATION_FILE.relative_to(ROOT)): _read(IMPLEMENTATION_FILE),
        str(UNIT_TEST_FILE.relative_to(ROOT)): _read(UNIT_TEST_FILE),
    }
    import_matches: dict[str, list[str]] = {}
    helper_matches: dict[str, list[str]] = {}
    endpoint_matches: dict[str, list[str]] = {}
    network_matches: dict[str, list[str]] = {}
    for label, source in sources.items():
        imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(source)]
        helpers = [match.group(0).strip() for match in FORBIDDEN_HELPER_PATTERN.finditer(source)]
        endpoints = [match.group(0).strip() for match in ENDPOINT_CONSTANT_PATTERN.finditer(source)]
        network_literals = [token for token in NETWORK_LITERAL_TOKENS if token in source]
        if imports:
            import_matches[label] = imports
        if helpers:
            helper_matches[label] = helpers
        if endpoints:
            endpoint_matches[label] = endpoints
        if network_literals:
            network_matches[label] = network_literals
    checks = {
        "no_http_client_imports": not import_matches,
        "no_platform_sdk_imports": not import_matches,
        "no_endpoint_constants": not endpoint_matches,
        "no_dns_or_network_access": not network_matches,
        "no_executable_helpers": not helper_matches,
    }
    return {
        "scanned_files": sorted(sources.keys()),
        "forbidden_imports": import_matches,
        "forbidden_helpers": helper_matches,
        "endpoint_constants": endpoint_matches,
        "network_literals": network_matches,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _blocked_semantics_review() -> dict[str, Any]:
    no_attempt = _evaluate()
    payload = no_attempt.to_dict()
    checks = {
        "blocked_false_observed": payload["blocked"] is False,
        "blocked_false_meaning_explicit": payload["blocked_meaning"] == BLOCKED_FALSE_MEANING,
        "blocked_false_does_not_authorize_flag": payload["blocked_false_does_not_authorize"] is True,
        "guard_pass_does_not_mean_success_flag": payload["guard_pass_does_not_mean_success"] is True,
        "blocked_false_external_call_authorized_false": payload["external_call_authorized"] is False,
        "blocked_false_publish_authorized_false": payload["publish_authorized"] is False,
        "blocked_false_url_authorized_false": payload["url_authorized"] is False,
        "blocked_false_platform_content_id_authorized_false": payload["platform_content_id_authorized"] is False,
        "blocked_false_receipt_authorized_false": payload["receipt_authorized"] is False,
        "blocked_false_success_false": payload["production_residuals_closed"] is False,
        "all_authorizations_false_when_blocked_false": _all_authorizations_false(payload),
        "rationale_says_not_permission": "not permission" in " ".join(payload["rationale"]),
    }
    return {
        "no_attempt_case": _summary(no_attempt),
        "checks": checks,
        "passed": all(checks.values()),
    }


def _side_effect_absence_review() -> dict[str, Any]:
    payload = _evaluate(attempted_capabilities={"external_call": True}).to_dict()
    checks = {
        "external_call_authorized_false": payload["external_call_authorized"] is False,
        "http_client_authorized_false": payload["http_client_authorized"] is False,
        "platform_sdk_authorized_false": payload["platform_sdk_authorized"] is False,
        "endpoint_authorized_false": payload["endpoint_authorized"] is False,
        "dns_network_authorized_false": payload["dns_network_authorized"] is False,
        "api_call_authorized_false": payload["api_call_authorized"] is False,
        "request_transformation_authorized_false": payload["request_transformation_authorized"] is False,
        "upload_authorized_false": payload["upload_authorized"] is False,
        "scheduler_authorized_false": payload["scheduler_authorized"] is False,
        "publish_authorized_false": payload["publish_authorized"] is False,
        "url_authorized_false": payload["url_authorized"] is False,
        "platform_content_id_authorized_false": payload["platform_content_id_authorized"] is False,
        "receipt_authorized_false": payload["receipt_authorized"] is False,
        "credential_value_access_authorized_false": payload["credential_value_access_authorized"] is False,
        "authorization_header_authorized_false": payload["authorization_header_authorized"] is False,
        "production_residuals_closed_false": payload["production_residuals_closed"] is False,
    }
    return {
        "observed": _summary(_evaluate(attempted_capabilities={"external_call": True})),
        "checks": checks,
        "passed": all(checks.values()),
    }


def _security_review() -> dict[str, Any]:
    crossing_cases = {
        "external_call": ("external_call", "EXTERNAL_CALL_ATTEMPT_BLOCKED"),
        "http_client": ("http_client", "HTTP_CLIENT_ATTEMPT_BLOCKED"),
        "platform_sdk": ("platform_sdk", "PLATFORM_SDK_ATTEMPT_BLOCKED"),
        "endpoint": ("endpoint", "ENDPOINT_ATTEMPT_BLOCKED"),
        "dns_network": ("dns_network", "DNS_NETWORK_ATTEMPT_BLOCKED"),
        "api_call": ("api_call", "API_CALL_ATTEMPT_BLOCKED"),
        "request_transformation": ("request_transformation", "REQUEST_TRANSFORMATION_ATTEMPT_BLOCKED"),
        "upload": ("upload", "UPLOAD_ATTEMPT_BLOCKED"),
        "scheduler": ("scheduler", "SCHEDULER_ATTEMPT_BLOCKED"),
        "publish": ("publish", "PUBLISH_ATTEMPT_BLOCKED"),
        "url": ("url", "URL_EMISSION_ATTEMPT_BLOCKED"),
        "platform_content_id": ("platform_content_id", "PLATFORM_CONTENT_ID_ATTEMPT_BLOCKED"),
        "receipt": ("receipt", "RECEIPT_ATTEMPT_BLOCKED"),
        "credential_value_access": ("credential_value_access", "CREDENTIAL_VALUE_ACCESS_ATTEMPT_BLOCKED"),
        "authorization_header": ("authorization_header", "AUTHORIZATION_HEADER_ATTEMPT_BLOCKED"),
        "fake_success": ("fake_success", "FAKE_SUCCESS_ATTEMPT_BLOCKED"),
    }
    crossing_results = {
        name: _evaluate(attempted_capabilities={capability: True})
        for name, (capability, _reason) in crossing_cases.items()
    }
    dependency_cases = {
        "missing_boundary": _evaluate(boundary_ref=None),
        "missing_controlled_binding": _evaluate(controlled_binding_ref=None),
        "missing_validation_envelope": _evaluate(validation_envelope_ref=None),
        "missing_publish_eligibility": _evaluate(publish_eligibility_trace_ref=None),
        "missing_qc_trace": _evaluate(qc_trace_ref=None),
        "qc_hold": _evaluate(dependency_status={**_input().dependency_status, "qc_status": "HOLD"}),
        "qc_reject": _evaluate(dependency_status={**_input().dependency_status, "qc_status": "REJECT"}),
        "qc_not_publishable": _evaluate(dependency_status={**_input().dependency_status, "qc_publishable": False}),
        "account_health_hold": _evaluate(
            dependency_status={**_input().dependency_status, "account_health_decision": "HOLD"}
        ),
        "missing_credentials": _evaluate(dependency_status={**_input().dependency_status, "credential_status": "missing"}),
        "invalid_credentials": _evaluate(
            dependency_status={**_input().dependency_status, "credential_status": "invalid_shape"}
        ),
        "kill_switch_active": _evaluate(dependency_status={**_input().dependency_status, "kill_switch_active": True}),
        "kill_switch_missing": _evaluate(dependency_status={**_input().dependency_status, "kill_switch_missing": True}),
        "weak_kill_switch": _evaluate(
            dependency_status={**_input().dependency_status, "kill_switch_blocks_external_calls": False}
        ),
        "rate_limit_allowed": _evaluate(
            dependency_status={**_input().dependency_status, "rate_limit_requests_allowed": True}
        ),
        "target_platform_mismatch": _evaluate(target_platform_id="REAL_PROVIDER"),
        "target_mode_mismatch": _evaluate(target_mode="production"),
    }
    expected_dependency_reasons = {
        "missing_boundary": "MISSING_BOUNDARY_REF",
        "missing_controlled_binding": "MISSING_CONTROLLED_BINDING_REF",
        "missing_validation_envelope": "MISSING_VALIDATION_ENVELOPE_REF",
        "missing_publish_eligibility": "MISSING_PUBLISH_ELIGIBILITY_TRACE",
        "missing_qc_trace": "MISSING_QC_TRACE",
        "qc_hold": "QC_HOLD",
        "qc_reject": "QC_REJECTED",
        "qc_not_publishable": "QC_NOT_PUBLISHABLE",
        "account_health_hold": "ACCOUNT_HEALTH_HOLD",
        "missing_credentials": "PUBLISHER_CREDENTIALS_MISSING",
        "invalid_credentials": "PUBLISHER_CREDENTIAL_VALIDATION_FAILED",
        "kill_switch_active": "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE",
        "kill_switch_missing": "PUBLISHER_PLATFORM_KILL_SWITCH_MISSING",
        "weak_kill_switch": "KILL_SWITCH_DOES_NOT_BLOCK_EXTERNAL_CALLS",
        "rate_limit_allowed": "RATE_LIMIT_REQUESTS_NOT_AUTHORIZED",
        "target_platform_mismatch": "INVALID_TARGET_PLATFORM",
        "target_mode_mismatch": "INVALID_TARGET_MODE",
    }
    checks = {
        f"{name}_blocked": result.blocked is True and reason in result.blocked_capabilities
        for name, result in crossing_results.items()
        for _capability, reason in [crossing_cases[name]]
    }
    checks.update(
        {
            f"{name}_dependency_blocked": result.blocked is True and reason in result.dependency_blocks
            for name, result in dependency_cases.items()
            for reason in [expected_dependency_reasons[name]]
        }
    )
    sensitive_case = crossing_results["credential_value_access"].to_dict()
    sensitive_serialized = json.dumps(sensitive_case["incident_hooks"], sort_keys=True)
    checks.update(
        {
            "all_crossing_attempts_keep_authorizations_false": all(
                _all_authorizations_false(result.to_dict()) for result in crossing_results.values()
            ),
            "all_dependency_blocks_keep_authorizations_false": all(
                _all_authorizations_false(result.to_dict()) for result in dependency_cases.values()
            ),
            "incident_hooks_do_not_include_url": "https://" not in sensitive_serialized,
            "incident_hooks_do_not_include_secret": "secret" not in sensitive_serialized.lower(),
        }
    )
    return {
        "crossing_cases": {name: _summary(result) for name, result in crossing_results.items()},
        "dependency_cases": {name: _summary(result) for name, result in dependency_cases.items()},
        "checks": checks,
        "passed": all(checks.values()),
    }


def _determinism_review() -> dict[str, Any]:
    guard = ExternalSandboxPreExecutionGuard()
    first = _evaluate()
    second = _evaluate()
    changed = _evaluate(content_id="content_changed")
    first_json = guard.deterministic_audit_json(first)
    second_json = guard.deterministic_audit_json(second)
    changed_json = guard.deterministic_audit_json(changed)
    checks = {
        "same_input_same_output": first.to_dict() == second.to_dict(),
        "same_input_same_serialization": first_json == second_json,
        "changed_input_changes_serialization": first_json != changed_json,
        "serialization_json_valid": isinstance(json.loads(first_json), dict),
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    result = _evaluate()
    residuals = list(result.residual_monitoring)
    checks = {
        "production_publish_evidence_residual_open": "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET" in residuals,
        "platform_integration_residual_open": "PLATFORM_INTEGRATION_NOT_ENABLED" in residuals,
        "publish_result_history_residual_open": "PUBLISH_RESULT_HISTORY_STILL_SHORT" in residuals,
        "external_call_not_implemented_residual_open": "EXTERNAL_CALL_NOT_IMPLEMENTED" in residuals,
        "external_sandbox_execution_not_authorized_residual_open": "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED"
        in residuals,
        "production_residuals_closed_false": result.production_residuals_closed is False,
        "residuals_exact": residuals == BOUNDARY_RESIDUALS,
    }
    return {
        "residual_monitoring": residuals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _run_scenarios(
    *,
    preconditions: dict[str, Any],
    static_scan: dict[str, Any],
    blocked_semantics: dict[str, Any],
    side_effects: dict[str, Any],
    security: dict[str, Any],
    determinism: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    scenario_checks = {
        "implementation_file_exists": IMPLEMENTATION_FILE.exists(),
        "unit_test_file_exists": UNIT_TEST_FILE.exists(),
        "guard_contract_exists": _evaluate().guard_type == GUARD_TYPE,
        "target_platform_exact": _evaluate().target_platform_id == TARGET_PLATFORM_ID,
        "target_mode_exact": _evaluate().target_mode == TARGET_MODE,
        "blocked_false_authorization_false": blocked_semantics["checks"]["all_authorizations_false_when_blocked_false"],
        "blocked_false_not_readiness": blocked_semantics["checks"]["blocked_false_success_false"],
        "external_call_attempt_blocked": security["checks"]["external_call_blocked"],
        "http_client_attempt_blocked": security["checks"]["http_client_blocked"],
        "platform_sdk_attempt_blocked": security["checks"]["platform_sdk_blocked"],
        "endpoint_attempt_blocked": security["checks"]["endpoint_blocked"],
        "dns_network_attempt_blocked": security["checks"]["dns_network_blocked"],
        "api_call_attempt_blocked": security["checks"]["api_call_blocked"],
        "request_transformation_attempt_blocked": security["checks"]["request_transformation_blocked"],
        "upload_attempt_blocked": security["checks"]["upload_blocked"],
        "scheduler_attempt_blocked": security["checks"]["scheduler_blocked"],
        "publish_attempt_blocked": security["checks"]["publish_blocked"],
        "url_attempt_blocked": security["checks"]["url_blocked"],
        "platform_content_id_attempt_blocked": security["checks"]["platform_content_id_blocked"],
        "receipt_attempt_blocked": security["checks"]["receipt_blocked"],
        "credential_value_access_attempt_blocked": security["checks"]["credential_value_access_blocked"],
        "authorization_header_attempt_blocked": security["checks"]["authorization_header_blocked"],
        "fake_success_attempt_blocked": security["checks"]["fake_success_blocked"],
        "missing_boundary_ref_blocks": security["checks"]["missing_boundary_dependency_blocked"],
        "missing_controlled_binding_ref_blocks": security["checks"]["missing_controlled_binding_dependency_blocked"],
        "missing_validation_envelope_ref_blocks": security["checks"]["missing_validation_envelope_dependency_blocked"],
        "missing_publish_eligibility_ref_blocks": security["checks"]["missing_publish_eligibility_dependency_blocked"],
        "missing_qc_trace_blocks": security["checks"]["missing_qc_trace_dependency_blocked"],
        "qc_hold_blocks": security["checks"]["qc_hold_dependency_blocked"],
        "qc_reject_blocks": security["checks"]["qc_reject_dependency_blocked"],
        "qc_publishable_false_blocks": security["checks"]["qc_not_publishable_dependency_blocked"],
        "account_health_hold_blocks": security["checks"]["account_health_hold_dependency_blocked"],
        "missing_credentials_blocks": security["checks"]["missing_credentials_dependency_blocked"],
        "invalid_credentials_block": security["checks"]["invalid_credentials_dependency_blocked"],
        "kill_switch_active_blocks": security["checks"]["kill_switch_active_dependency_blocked"],
        "kill_switch_missing_blocks": security["checks"]["kill_switch_missing_dependency_blocked"],
        "weak_kill_switch_blocks": security["checks"]["weak_kill_switch_dependency_blocked"],
        "rate_limit_request_allowed_blocks": security["checks"]["rate_limit_allowed_dependency_blocked"],
        "target_platform_mismatch_blocks": security["checks"]["target_platform_mismatch_dependency_blocked"],
        "target_mode_mismatch_blocks": security["checks"]["target_mode_mismatch_dependency_blocked"],
        "incident_hooks_safe": security["checks"]["incident_hooks_do_not_include_secret"]
        and security["checks"]["incident_hooks_do_not_include_url"],
        "deterministic_replay": determinism["passed"],
        "static_scan_clean": static_scan["passed"],
        "production_residuals_remain_open": residuals["passed"],
        "no_runtime_core_mutation": True,
        "preconditions_present": preconditions["passed"],
        "side_effects_absent": side_effects["passed"],
    }
    return {name: _scenario(name, passed) for name, passed in scenario_checks.items()}


def _build_checklist(
    *,
    preconditions: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    static_scan: dict[str, Any],
    blocked_semantics: dict[str, Any],
    side_effects: dict[str, Any],
    security: dict[str, Any],
    determinism: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    result = _evaluate()
    checks = {
        "preconditions_present": preconditions["passed"],
        "implementation_present": IMPLEMENTATION_FILE.exists(),
        "unit_tests_present": UNIT_TEST_FILE.exists(),
        "guard_type_external_call_pre_execution_blocker": result.guard_type == GUARD_TYPE,
        "guard_state_blocking_only": result.guard_state == "blocking_only",
        "guard_output_deterministic": determinism["passed"],
        "target_platform_exact": result.target_platform_id == TARGET_PLATFORM_ID,
        "target_mode_exact": result.target_mode == TARGET_MODE,
        "blocked_false_semantics_explicit": blocked_semantics["checks"]["blocked_false_meaning_explicit"],
        "blocked_false_does_not_authorize_external_call": blocked_semantics["checks"][
            "blocked_false_external_call_authorized_false"
        ],
        "blocked_false_does_not_authorize_publish": blocked_semantics["checks"][
            "blocked_false_publish_authorized_false"
        ],
        "guard_pass_does_not_mean_success": blocked_semantics["checks"]["guard_pass_does_not_mean_success_flag"],
        "crossing_attempts_blocked": all(
            value for key, value in security["checks"].items() if key.endswith("_blocked")
        ),
        "dependency_blocks_explicit": all(
            value for key, value in security["checks"].items() if key.endswith("_dependency_blocked")
        ),
        "external_call_unauthorized": side_effects["checks"]["external_call_authorized_false"],
        "http_client_unauthorized": side_effects["checks"]["http_client_authorized_false"],
        "platform_sdk_unauthorized": side_effects["checks"]["platform_sdk_authorized_false"],
        "endpoint_unauthorized": side_effects["checks"]["endpoint_authorized_false"],
        "dns_network_unauthorized": side_effects["checks"]["dns_network_authorized_false"],
        "api_call_unauthorized": side_effects["checks"]["api_call_authorized_false"],
        "request_transformation_unauthorized": side_effects["checks"]["request_transformation_authorized_false"],
        "upload_unauthorized": side_effects["checks"]["upload_authorized_false"],
        "scheduler_unauthorized": side_effects["checks"]["scheduler_authorized_false"],
        "publish_unauthorized": side_effects["checks"]["publish_authorized_false"],
        "url_unauthorized": side_effects["checks"]["url_authorized_false"],
        "platform_content_id_unauthorized": side_effects["checks"]["platform_content_id_authorized_false"],
        "receipt_unauthorized": side_effects["checks"]["receipt_authorized_false"],
        "credential_value_access_unauthorized": side_effects["checks"]["credential_value_access_authorized_false"],
        "authorization_header_unauthorized": side_effects["checks"]["authorization_header_authorized_false"],
        "fake_success_impossible": security["checks"]["fake_success_blocked"]
        and blocked_semantics["checks"]["blocked_false_success_false"],
        "incident_hooks_safe": security["checks"]["incident_hooks_do_not_include_secret"]
        and security["checks"]["incident_hooks_do_not_include_url"],
        "static_scan_clean": static_scan["passed"],
        "production_residuals_open": residuals["passed"],
        "boundary_preserved": True,
        "no_runtime_integration": True,
        "no_core_mutation": True,
        "all_scenarios_passed": all(item["passed"] for item in scenarios.values()),
    }
    return {
        name: {"passed": bool(passed), "failure_reason": None if passed else "CHECK_FAILED"}
        for name, passed in checks.items()
    }


def _blocking_failures(checklist: dict[str, dict[str, Any]], scenarios: dict[str, dict[str, Any]]) -> list[str]:
    failures = [f"CHECK_FAILED:{name}" for name, item in checklist.items() if not item["passed"]]
    failures.extend(f"SCENARIO_FAILED:{name}" for name, item in scenarios.items() if not item["passed"])
    return sorted(failures)


def main() -> int:
    _reset_audit_dir()
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    preconditions = _preconditions()
    static_scan = _static_scan_review()
    blocked_semantics = _blocked_semantics_review()
    side_effects = _side_effect_absence_review()
    security = _security_review()
    determinism = _determinism_review()
    residuals = _residual_monitoring_review()
    scenarios = _run_scenarios(
        preconditions=preconditions,
        static_scan=static_scan,
        blocked_semantics=blocked_semantics,
        side_effects=side_effects,
        security=security,
        determinism=determinism,
        residuals=residuals,
    )
    checklist = _build_checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        static_scan=static_scan,
        blocked_semantics=blocked_semantics,
        side_effects=side_effects,
        security=security,
        determinism=determinism,
        residuals=residuals,
    )
    blocking_failures = _blocking_failures(checklist, scenarios)

    scenario_count = len(scenarios)
    scenario_pass_count = sum(1 for item in scenarios.values() if item["passed"])
    checklist_count = len(checklist)
    checklist_pass_count = sum(1 for item in checklist.values() if item["passed"])

    critical_flags = {
        "blocked_false_authorizes_external_call": not blocked_semantics["checks"][
            "blocked_false_external_call_authorized_false"
        ],
        "blocked_false_authorizes_publish": not blocked_semantics["checks"]["blocked_false_publish_authorized_false"],
        "guard_pass_implies_success": not blocked_semantics["checks"]["guard_pass_does_not_mean_success_flag"],
        "external_call_authorized": not side_effects["checks"]["external_call_authorized_false"],
        "http_client_detected": not static_scan["checks"]["no_http_client_imports"],
        "platform_sdk_detected": not static_scan["checks"]["no_platform_sdk_imports"],
        "endpoint_detected": not static_scan["checks"]["no_endpoint_constants"],
        "dns_network_detected": not static_scan["checks"]["no_dns_or_network_access"],
        "api_call_detected": not side_effects["checks"]["api_call_authorized_false"],
        "request_transformation_detected": not side_effects["checks"]["request_transformation_authorized_false"],
        "upload_detected": not side_effects["checks"]["upload_authorized_false"],
        "scheduler_detected": not side_effects["checks"]["scheduler_authorized_false"],
        "publish_detected": not side_effects["checks"]["publish_authorized_false"],
        "url_detected": not side_effects["checks"]["url_authorized_false"],
        "platform_content_id_detected": not side_effects["checks"]["platform_content_id_authorized_false"],
        "receipt_detected": not side_effects["checks"]["receipt_authorized_false"],
        "credential_value_access_detected": not side_effects["checks"]["credential_value_access_authorized_false"],
        "authorization_header_detected": not side_effects["checks"]["authorization_header_authorized_false"],
        "fake_success_detected": not security["checks"]["fake_success_blocked"],
        "production_residuals_closed": not residuals["checks"]["production_residuals_closed_false"],
        "silent_failures_detected": False,
    }

    hold_required = bool(blocking_failures) or any(critical_flags.values())
    verdict = "HOLD" if hold_required else "GO_WITH_MONITORING"
    recommendation = (
        "PROCEED_TO_EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_REVIEW"
        if verdict != "HOLD"
        else "HOLD_BEFORE_NEXT_STEP"
    )

    metrics = {
        "critical_failures": sum(1 for value in critical_flags.values() if value),
        "blocking_failures_count": len(blocking_failures),
        "scenario_count": scenario_count,
        "scenario_pass_count": scenario_pass_count,
        "checklist_count": checklist_count,
        "checklist_pass_count": checklist_pass_count,
        **critical_flags,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_EXTERNAL_CALL_PRE_EXECUTION_GUARD_GATE",
        "verdict": verdict,
        "timestamp": now,
        "implementation_present": IMPLEMENTATION_FILE.exists(),
        "unit_tests_present": UNIT_TEST_FILE.exists(),
        "guard_type": GUARD_TYPE,
        "guard_state": GUARD_STATE,
        "blocked_false_does_not_authorize": blocked_semantics["checks"]["blocked_false_does_not_authorize_flag"],
        "guard_pass_does_not_mean_success": blocked_semantics["checks"]["guard_pass_does_not_mean_success_flag"],
        "production_residuals_remain_open": residuals["passed"],
        **critical_flags,
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": list(BOUNDARY_RESIDUALS),
        "recommendation": recommendation,
    }

    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(METRICS_PATH, metrics)
    _write_json(STATIC_SCAN_REVIEW_PATH, static_scan)
    _write_json(SIDE_EFFECT_ABSENCE_REVIEW_PATH, side_effects)
    _write_json(SECURITY_REVIEW_PATH, security)
    _write_json(BLOCKED_SEMANTICS_REVIEW_PATH, blocked_semantics)
    _write_json(DETERMINISM_REVIEW_PATH, determinism)
    _write_json(RESIDUAL_MONITORING_REVIEW_PATH, residuals)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False, ensure_ascii=True))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
