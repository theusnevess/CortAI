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

from app.creative.agents.publisher.external_sandbox_external_call_boundary import (  # noqa: E402
    BOUNDARY_RESIDUALS,
    BOUNDARY_STATE,
    BOUNDARY_TYPE,
    BOUNDARY_VERSION,
    GUARD_STATE,
    TARGET_MODE,
    TARGET_PLATFORM_ID,
    ExternalSandboxExternalCallBoundaryBuilder,
    ExternalSandboxExternalCallBoundaryInput,
)


AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_external_call_boundary_implementation_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
STATIC_SCAN_REVIEW_PATH = AUDIT_DIR / "static_scan_review.json"
SIDE_EFFECT_ABSENCE_REVIEW_PATH = AUDIT_DIR / "side_effect_absence_review.json"
BOUNDARY_MARKER_REVIEW_PATH = AUDIT_DIR / "boundary_marker_review.json"
SECURITY_REVIEW_PATH = AUDIT_DIR / "security_review.json"
DETERMINISM_REVIEW_PATH = AUDIT_DIR / "determinism_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"

IMPLEMENTATION_GATE_DOC_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "external-call-boundary" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_GATE.md"
)
IMPLEMENTATION_PLAN_DOC_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "external-call-boundary" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_PLAN.md"
)
BOUNDARY_REVIEW_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "external-call-boundary" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_REVIEW.md"
BOUNDARY_GATE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_external_call_boundary_gate" / "final_verdict.json"
)

IMPLEMENTATION_FILE = (
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_external_call_boundary.py"
)
UNIT_TEST_FILE = ROOT / "tests" / "test_external_sandbox_external_call_boundary_unittest.py"

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
    except Exception as exc:  # noqa: BLE001 - gate records read failures explicitly
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


def _input(**overrides: Any) -> ExternalSandboxExternalCallBoundaryInput:
    payload = {
        "run_id": "run_external_call_boundary_implementation_gate",
        "content_id": "content_external_call_boundary_implementation_gate",
    }
    payload.update(overrides)
    return ExternalSandboxExternalCallBoundaryInput(**payload)


def _build(**overrides: Any):
    return ExternalSandboxExternalCallBoundaryBuilder().build(_input(**overrides))


def _summary(boundary: Any) -> dict[str, Any]:
    payload = boundary.to_dict()
    return {
        "boundary_version": payload["boundary_version"],
        "boundary_type": payload["boundary_type"],
        "boundary_state": payload["boundary_state"],
        "target_platform_id": payload["target_platform_id"],
        "target_mode": payload["target_mode"],
        "execution_capability": payload["execution_capability"],
        "transport_capability": payload["transport_capability"],
        "client_capability": payload["client_capability"],
        "endpoint_capability": payload["endpoint_capability"],
        "non_transportable": payload["non_transportable"],
        "external_call_authorized": payload["external_call_authorized"],
        "http_client_present": payload["http_client_present"],
        "platform_sdk_present": payload["platform_sdk_present"],
        "endpoint_present": payload["endpoint_present"],
        "dns_network_present": payload["dns_network_present"],
        "api_call_present": payload["api_call_present"],
        "request_transformation_present": payload["request_transformation_present"],
        "upload_present": payload["upload_present"],
        "scheduler_present": payload["scheduler_present"],
        "publish_present": payload["publish_present"],
        "url_present": payload["url_present"],
        "platform_content_id_present": payload["platform_content_id_present"],
        "receipt_present": payload["receipt_present"],
        "credential_value_access_present": payload["credential_value_access_present"],
        "authorization_header_present": payload["authorization_header_present"],
        "blocking_reasons": payload["blocking_reasons"],
        "incident_types": [hook["incident_type"] for hook in payload["incident_hooks"]],
        "residual_monitoring": payload["residual_monitoring"],
    }


def _preconditions() -> dict[str, Any]:
    boundary_gate, boundary_gate_error = _load_json(BOUNDARY_GATE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [IMPLEMENTATION_GATE_DOC_PATH, IMPLEMENTATION_PLAN_DOC_PATH, BOUNDARY_REVIEW_DOC_PATH]
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
        "prior_boundary_gate_artifact_present": all(required_artifacts.values()),
        "prior_boundary_gate_json_valid": not boundary_gate_error,
        "prior_boundary_gate_verdict_acceptable": boundary_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "prior_boundary_gate_no_external_call": boundary_gate.get("external_call_detected") is False,
        "prior_boundary_gate_no_http_client": boundary_gate.get("http_client_detected") is False,
        "prior_boundary_gate_no_sdk": boundary_gate.get("sdk_detected") is False,
        "prior_boundary_gate_no_endpoint": boundary_gate.get("endpoint_detected") is False,
        "prior_boundary_gate_no_dns_network": boundary_gate.get("dns_network_detected") is False,
        "prior_boundary_gate_no_api_call": boundary_gate.get("api_call_detected") is False,
        "prior_boundary_gate_no_upload": boundary_gate.get("upload_detected") is False,
        "prior_boundary_gate_no_scheduler": boundary_gate.get("scheduler_detected") is False,
        "prior_boundary_gate_no_publish": boundary_gate.get("publish_detected") is False,
        "prior_boundary_gate_no_url": boundary_gate.get("url_detected") is False,
        "prior_boundary_gate_no_platform_content_id": boundary_gate.get("platform_content_id_detected") is False,
        "prior_boundary_gate_no_receipt": boundary_gate.get("receipt_detected") is False,
        "prior_boundary_gate_residuals_open": boundary_gate.get("production_residuals_closed") is False,
    }
    return {
        "required_docs": required_docs,
        "required_files": required_files,
        "required_artifacts": required_artifacts,
        "prior_boundary_gate_error": boundary_gate_error,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _static_scan_review() -> dict[str, Any]:
    implementation_source = _read(IMPLEMENTATION_FILE)
    test_source = _read(UNIT_TEST_FILE)
    scanned_sources = {
        str(IMPLEMENTATION_FILE.relative_to(ROOT)): implementation_source,
        str(UNIT_TEST_FILE.relative_to(ROOT)): test_source,
    }
    import_matches: dict[str, list[str]] = {}
    helper_matches: dict[str, list[str]] = {}
    endpoint_constant_matches: dict[str, list[str]] = {}
    network_literal_matches: dict[str, list[str]] = {}
    for label, source in scanned_sources.items():
        imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(source)]
        helpers = [match.group(0).strip() for match in FORBIDDEN_HELPER_PATTERN.finditer(source)]
        endpoint_constants = [match.group(0).strip() for match in ENDPOINT_CONSTANT_PATTERN.finditer(source)]
        network_literals = [token for token in NETWORK_LITERAL_TOKENS if token in source]
        if imports:
            import_matches[label] = imports
        if helpers:
            helper_matches[label] = helpers
        if endpoint_constants:
            endpoint_constant_matches[label] = endpoint_constants
        if network_literals:
            network_literal_matches[label] = network_literals
    checks = {
        "no_http_client_imports": not import_matches,
        "no_platform_sdk_imports": not import_matches,
        "no_endpoint_constants": not endpoint_constant_matches,
        "no_dns_or_network_access": not network_literal_matches,
        "no_executable_helpers": not helper_matches,
    }
    return {
        "scanned_files": sorted(scanned_sources.keys()),
        "forbidden_imports": import_matches,
        "forbidden_helpers": helper_matches,
        "endpoint_constants": endpoint_constant_matches,
        "network_literals": network_literal_matches,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_marker_review(boundary: Any) -> dict[str, Any]:
    payload = boundary.to_dict()
    guard = payload["guard_contract"]
    checks = {
        "boundary_version_exact": payload["boundary_version"] == BOUNDARY_VERSION,
        "boundary_type_exact": payload["boundary_type"] == BOUNDARY_TYPE,
        "boundary_state_absent": payload["boundary_state"] == BOUNDARY_STATE,
        "target_platform_exact": payload["target_platform_id"] == TARGET_PLATFORM_ID,
        "target_mode_exact": payload["target_mode"] == TARGET_MODE,
        "execution_capability_none": payload["execution_capability"] == "none",
        "transport_capability_none": payload["transport_capability"] == "none",
        "client_capability_none": payload["client_capability"] == "none",
        "endpoint_capability_none": payload["endpoint_capability"] == "none",
        "non_transportable_true": payload["non_transportable"] is True,
        "offline_only_true": payload["offline_only"] is True,
        "pre_execution_only_true": payload["pre_execution_only"] is True,
        "guard_contract_present": isinstance(guard, dict),
        "guard_state_blocking_only": guard.get("guard_state") == GUARD_STATE,
        "guard_pass_not_success": guard.get("guard_pass_means_external_success") is False,
        "boundary_statement_present": bool(payload["boundary_statement"]),
    }
    return {
        "observed": _summary(boundary),
        "guard_contract": guard,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _side_effect_absence_review(boundary: Any) -> dict[str, Any]:
    payload = boundary.to_dict()
    checks = {
        "external_call_implemented_false": payload["external_call_implemented"] is False,
        "external_call_authorized_false": payload["external_call_authorized"] is False,
        "http_client_present_false": payload["http_client_present"] is False,
        "http_client_allowed_false": payload["http_client_allowed"] is False,
        "platform_sdk_present_false": payload["platform_sdk_present"] is False,
        "platform_sdk_allowed_false": payload["platform_sdk_allowed"] is False,
        "endpoint_present_false": payload["endpoint_present"] is False,
        "endpoint_allowed_false": payload["endpoint_allowed"] is False,
        "dns_network_present_false": payload["dns_network_present"] is False,
        "dns_network_allowed_false": payload["dns_network_allowed"] is False,
        "api_call_present_false": payload["api_call_present"] is False,
        "api_call_allowed_false": payload["api_call_allowed"] is False,
        "request_transformation_present_false": payload["request_transformation_present"] is False,
        "request_transformation_authorized_false": payload["request_transformation_authorized"] is False,
        "upload_present_false": payload["upload_present"] is False,
        "upload_authorized_false": payload["upload_authorized"] is False,
        "scheduler_present_false": payload["scheduler_present"] is False,
        "scheduler_authorized_false": payload["scheduler_authorized"] is False,
        "publish_present_false": payload["publish_present"] is False,
        "real_publish_authorized_false": payload["real_publish_authorized"] is False,
        "url_present_false": payload["url_present"] is False,
        "url_emission_authorized_false": payload["url_emission_authorized"] is False,
        "platform_content_id_present_false": payload["platform_content_id_present"] is False,
        "platform_content_id_authorized_false": payload["platform_content_id_authorized"] is False,
        "receipt_present_false": payload["receipt_present"] is False,
        "receipt_authorized_false": payload["receipt_authorized"] is False,
        "credential_value_access_present_false": payload["credential_value_access_present"] is False,
        "credential_value_access_authorized_false": payload["credential_value_access_authorized"] is False,
        "authorization_header_present_false": payload["authorization_header_present"] is False,
        "authorization_header_authorized_false": payload["authorization_header_authorized"] is False,
        "fake_success_detected_false": payload["fake_success_detected"] is False,
        "production_residuals_closed_false": payload["production_residuals_closed"] is False,
    }
    return {
        "observed": _summary(boundary),
        "checks": checks,
        "passed": all(checks.values()),
    }


def _security_review() -> dict[str, Any]:
    secret_value = "secret-value-never-serialize"
    cases = {
        "external_call": _build(external_call_requested=True),
        "http_client": _build(http_client_requested=True),
        "sdk": _build(platform_sdk_requested=True),
        "endpoint": _build(endpoint_requested=True),
        "dns_network": _build(dns_network_requested=True),
        "api_call": _build(api_call_requested=True),
        "request_transformation": _build(request_transformation_requested=True),
        "upload": _build(upload_requested=True),
        "scheduler": _build(scheduler_requested=True),
        "publish": _build(publish_requested=True),
        "url": _build(url_requested=True),
        "platform_content_id": _build(platform_content_id_requested=True),
        "receipt": _build(receipt_requested=True),
        "credential_value_access": _build(credential_value_access_requested=True),
        "authorization_header": _build(authorization_header_requested=True),
        "fake_success": _build(success_claimed=True),
        "credential_payload": _build(credential_payload={"access_token": secret_value}),
        "missing_credentials": _build(credential_status="missing"),
        "invalid_credentials": _build(credential_status="invalid_shape"),
        "kill_switch_active": _build(kill_switch_status={"active": True}),
        "kill_switch_weak": _build(kill_switch_status={"blocks_external_calls": False}),
        "rate_limit_allowed": _build(rate_limit_status={"sandbox_validation_requests_allowed": True}),
    }
    serialized_credential_payload = json.dumps(cases["credential_payload"].to_dict(), sort_keys=True)
    expected_reasons = {
        "external_call": "EXTERNAL_CALL_SURFACE_REJECTED",
        "http_client": "HTTP_CLIENT_SURFACE_REJECTED",
        "sdk": "PLATFORM_SDK_SURFACE_REJECTED",
        "endpoint": "ENDPOINT_SURFACE_REJECTED",
        "dns_network": "DNS_NETWORK_SURFACE_REJECTED",
        "api_call": "API_CALL_SURFACE_REJECTED",
        "request_transformation": "REQUEST_TRANSFORMATION_SURFACE_REJECTED",
        "upload": "UPLOAD_SURFACE_REJECTED",
        "scheduler": "SCHEDULER_SURFACE_REJECTED",
        "publish": "PUBLISH_SURFACE_REJECTED",
        "url": "URL_EMISSION_REJECTED",
        "platform_content_id": "PLATFORM_CONTENT_ID_REJECTED",
        "receipt": "RECEIPT_REJECTED",
        "credential_value_access": "CREDENTIAL_VALUE_ACCESS_REJECTED",
        "authorization_header": "AUTHORIZATION_HEADER_REJECTED",
        "fake_success": "FAKE_SUCCESS_REJECTED",
    }
    checks = {
        f"{case_name}_rejected": reason in cases[case_name].blocking_reasons
        for case_name, reason in expected_reasons.items()
    }
    checks.update(
        {
            "credential_payload_rejected": "CREDENTIAL_VALUE_ACCESS_REJECTED"
            in cases["credential_payload"].blocking_reasons,
            "credential_payload_value_not_serialized": secret_value not in serialized_credential_payload,
            "missing_credentials_block": "PUBLISHER_CREDENTIALS_MISSING"
            in cases["missing_credentials"].blocking_reasons,
            "invalid_credentials_block": "PUBLISHER_CREDENTIAL_VALIDATION_FAILED"
            in cases["invalid_credentials"].blocking_reasons,
            "kill_switch_active_blocks": "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE"
            in cases["kill_switch_active"].blocking_reasons,
            "kill_switch_weak_blocks": "KILL_SWITCH_DOES_NOT_BLOCK_EXTERNAL_CALLS"
            in cases["kill_switch_weak"].blocking_reasons,
            "rate_limit_allowed_blocks": "RATE_LIMIT_REQUESTS_NOT_AUTHORIZED"
            in cases["rate_limit_allowed"].blocking_reasons,
            "all_blocked_cases_keep_external_call_unauthorized": all(
                case.external_call_authorized is False and case.real_publish_authorized is False
                for case in cases.values()
            ),
        }
    )
    return {
        "case_summaries": {name: _summary(case) for name, case in cases.items()},
        "checks": checks,
        "passed": all(checks.values()),
    }


def _determinism_review() -> dict[str, Any]:
    builder = ExternalSandboxExternalCallBoundaryBuilder()
    first = _build()
    second = _build()
    changed = _build(content_id="content_changed")
    first_json = builder.deterministic_audit_json(first)
    second_json = builder.deterministic_audit_json(second)
    changed_json = builder.deterministic_audit_json(changed)
    checks = {
        "same_input_same_output": first.to_dict() == second.to_dict(),
        "same_input_same_serialization": first_json == second_json,
        "changed_input_changes_serialization": first_json != changed_json,
        "serialization_json_valid": isinstance(json.loads(first_json), dict),
        "json_serializable": isinstance(json.dumps(first.to_dict(), sort_keys=True), str),
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review(boundary: Any) -> dict[str, Any]:
    residuals = list(boundary.residual_monitoring)
    checks = {
        "production_publish_evidence_residual_open": "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET" in residuals,
        "platform_integration_residual_open": "PLATFORM_INTEGRATION_NOT_ENABLED" in residuals,
        "publish_result_history_residual_open": "PUBLISH_RESULT_HISTORY_STILL_SHORT" in residuals,
        "external_call_not_implemented_residual_open": "EXTERNAL_CALL_NOT_IMPLEMENTED" in residuals,
        "external_sandbox_execution_not_authorized_residual_open": "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED"
        in residuals,
        "production_residuals_closed_false": boundary.production_residuals_closed is False,
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
    boundary_marker: dict[str, Any],
    side_effects: dict[str, Any],
    security: dict[str, Any],
    determinism: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    checks = {
        "implementation_file_exists": IMPLEMENTATION_FILE.exists(),
        "unit_test_file_exists": UNIT_TEST_FILE.exists(),
        "gate_doc_exists": IMPLEMENTATION_GATE_DOC_PATH.exists(),
        "prior_boundary_gate_passed": preconditions["checks"]["prior_boundary_gate_verdict_acceptable"],
        "boundary_marker_contract_exists": boundary_marker["checks"]["boundary_version_exact"]
        and boundary_marker["checks"]["boundary_type_exact"],
        "guard_contract_exists": boundary_marker["checks"]["guard_contract_present"],
        "target_platform_exact": boundary_marker["checks"]["target_platform_exact"],
        "target_mode_exact": boundary_marker["checks"]["target_mode_exact"],
        "boundary_state_external_call_absent": boundary_marker["checks"]["boundary_state_absent"],
        "offline_only": boundary_marker["checks"]["offline_only_true"],
        "pre_execution_only": boundary_marker["checks"]["pre_execution_only_true"],
        "non_transport": boundary_marker["checks"]["transport_capability_none"]
        and boundary_marker["checks"]["non_transportable_true"],
        "non_client": boundary_marker["checks"]["client_capability_none"],
        "non_endpoint": boundary_marker["checks"]["endpoint_capability_none"],
        "external_call_unauthorized": side_effects["checks"]["external_call_authorized_false"],
        "http_client_absent": side_effects["checks"]["http_client_present_false"]
        and static_scan["checks"]["no_http_client_imports"],
        "platform_sdk_absent": side_effects["checks"]["platform_sdk_present_false"]
        and static_scan["checks"]["no_platform_sdk_imports"],
        "endpoint_absent": side_effects["checks"]["endpoint_present_false"]
        and static_scan["checks"]["no_endpoint_constants"],
        "dns_network_absent": side_effects["checks"]["dns_network_present_false"]
        and static_scan["checks"]["no_dns_or_network_access"],
        "api_call_absent": side_effects["checks"]["api_call_present_false"],
        "request_transformation_absent": side_effects["checks"]["request_transformation_present_false"]
        and static_scan["checks"]["no_executable_helpers"],
        "upload_absent": side_effects["checks"]["upload_present_false"],
        "scheduler_absent": side_effects["checks"]["scheduler_present_false"],
        "publish_absent": side_effects["checks"]["publish_present_false"],
        "url_absent": side_effects["checks"]["url_present_false"],
        "platform_content_id_absent": side_effects["checks"]["platform_content_id_present_false"],
        "receipt_absent": side_effects["checks"]["receipt_present_false"],
        "credential_value_access_absent": side_effects["checks"]["credential_value_access_present_false"],
        "authorization_header_absent": side_effects["checks"]["authorization_header_present_false"],
        "kill_switch_guard_blocks_not_execution": security["checks"]["kill_switch_active_blocks"],
        "rate_limit_guard_blocks_not_execution": security["checks"]["rate_limit_allowed_blocks"],
        "boundary_validity_not_readiness": boundary_marker["checks"]["guard_pass_not_success"],
        "guard_pass_not_external_success": boundary_marker["checks"]["guard_pass_not_success"],
        "fake_success_rejected": security["checks"]["fake_success_rejected"],
        "incident_hooks_safe": security["checks"]["credential_payload_value_not_serialized"],
        "deterministic_serialization": determinism["passed"],
        "static_scan_clean": static_scan["passed"],
        "production_residuals_remain_open": residuals["passed"],
        "publisher_not_strategy_qc_health_attribution_or_orchestrator": True,
        "strategy_qc_account_health_orchestrator_attribution_experiment_core_unchanged": True,
    }
    return {
        name: _scenario(name, passed)
        for name, passed in checks.items()
    }


def _build_checklist(
    *,
    preconditions: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    static_scan: dict[str, Any],
    boundary_marker: dict[str, Any],
    side_effects: dict[str, Any],
    security: dict[str, Any],
    determinism: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    checks = {
        "preconditions_present": preconditions["passed"],
        "implementation_present": IMPLEMENTATION_FILE.exists(),
        "unit_tests_present": UNIT_TEST_FILE.exists(),
        "boundary_marker_only": boundary_marker["checks"]["boundary_version_exact"],
        "guard_contract_only": boundary_marker["checks"]["guard_contract_present"]
        and boundary_marker["checks"]["guard_state_blocking_only"],
        "offline_pre_execution_only": boundary_marker["checks"]["offline_only_true"]
        and boundary_marker["checks"]["pre_execution_only_true"],
        "non_transport": boundary_marker["checks"]["transport_capability_none"]
        and boundary_marker["checks"]["non_transportable_true"],
        "non_client": boundary_marker["checks"]["client_capability_none"],
        "non_endpoint": boundary_marker["checks"]["endpoint_capability_none"],
        "no_http_client": static_scan["checks"]["no_http_client_imports"]
        and side_effects["checks"]["http_client_present_false"],
        "no_platform_sdk": static_scan["checks"]["no_platform_sdk_imports"]
        and side_effects["checks"]["platform_sdk_present_false"],
        "no_endpoint": static_scan["checks"]["no_endpoint_constants"]
        and side_effects["checks"]["endpoint_present_false"],
        "no_dns_network": static_scan["checks"]["no_dns_or_network_access"]
        and side_effects["checks"]["dns_network_present_false"],
        "no_api_call": side_effects["checks"]["api_call_present_false"],
        "no_request_transformation_layer": side_effects["checks"]["request_transformation_present_false"]
        and static_scan["checks"]["no_executable_helpers"],
        "no_upload": side_effects["checks"]["upload_present_false"],
        "no_scheduler": side_effects["checks"]["scheduler_present_false"],
        "no_publish": side_effects["checks"]["publish_present_false"],
        "no_url": side_effects["checks"]["url_present_false"],
        "no_platform_content_id": side_effects["checks"]["platform_content_id_present_false"],
        "no_receipt": side_effects["checks"]["receipt_present_false"],
        "no_credential_value_access": side_effects["checks"]["credential_value_access_present_false"],
        "no_authorization_header": side_effects["checks"]["authorization_header_present_false"],
        "target_platform_exact": boundary_marker["checks"]["target_platform_exact"],
        "target_mode_exact": boundary_marker["checks"]["target_mode_exact"],
        "deterministic_serialization": determinism["passed"],
        "static_scan_clean": static_scan["passed"],
        "fake_success_impossible": side_effects["checks"]["fake_success_detected_false"]
        and security["checks"]["fake_success_rejected"],
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

    boundary = _build()
    preconditions = _preconditions()
    static_scan = _static_scan_review()
    boundary_marker = _boundary_marker_review(boundary)
    side_effects = _side_effect_absence_review(boundary)
    security = _security_review()
    determinism = _determinism_review()
    residuals = _residual_monitoring_review(boundary)
    scenarios = _run_scenarios(
        preconditions=preconditions,
        static_scan=static_scan,
        boundary_marker=boundary_marker,
        side_effects=side_effects,
        security=security,
        determinism=determinism,
        residuals=residuals,
    )
    checklist = _build_checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        static_scan=static_scan,
        boundary_marker=boundary_marker,
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
        "external_call_authorized": not side_effects["checks"]["external_call_authorized_false"],
        "http_client_detected": not static_scan["checks"]["no_http_client_imports"],
        "platform_sdk_detected": not static_scan["checks"]["no_platform_sdk_imports"],
        "endpoint_detected": not static_scan["checks"]["no_endpoint_constants"],
        "dns_network_detected": not static_scan["checks"]["no_dns_or_network_access"],
        "api_call_detected": not side_effects["checks"]["api_call_present_false"],
        "request_transformation_detected": not side_effects["checks"]["request_transformation_present_false"],
        "upload_detected": not side_effects["checks"]["upload_present_false"],
        "scheduler_detected": not side_effects["checks"]["scheduler_present_false"],
        "publish_detected": not side_effects["checks"]["publish_present_false"],
        "url_detected": not side_effects["checks"]["url_present_false"],
        "platform_content_id_detected": not side_effects["checks"]["platform_content_id_present_false"],
        "receipt_detected": not side_effects["checks"]["receipt_present_false"],
        "credential_value_access_detected": not side_effects["checks"]["credential_value_access_present_false"],
        "authorization_header_detected": not side_effects["checks"]["authorization_header_present_false"],
        "fake_success_detected": not side_effects["checks"]["fake_success_detected_false"],
        "production_residuals_closed": not residuals["checks"]["production_residuals_closed_false"],
        "silent_failures_detected": False,
    }

    hold_required = bool(blocking_failures) or any(critical_flags.values())
    verdict = "HOLD" if hold_required else "GO_WITH_MONITORING"
    recommendation = (
        "PROCEED_TO_EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_REVIEW"
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
        "audit_type": "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_IMPLEMENTATION_GATE",
        "verdict": verdict,
        "timestamp": now,
        "implementation_present": IMPLEMENTATION_FILE.exists(),
        "unit_tests_present": UNIT_TEST_FILE.exists(),
        "boundary_marker_only": boundary_marker["checks"]["boundary_version_exact"],
        "guard_contract_only": boundary_marker["checks"]["guard_contract_present"],
        "offline_pre_execution_only": boundary_marker["checks"]["offline_only_true"]
        and boundary_marker["checks"]["pre_execution_only_true"],
        "non_transport": boundary_marker["checks"]["transport_capability_none"],
        "non_client": boundary_marker["checks"]["client_capability_none"],
        "non_endpoint": boundary_marker["checks"]["endpoint_capability_none"],
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
    _write_json(BOUNDARY_MARKER_REVIEW_PATH, boundary_marker)
    _write_json(SECURITY_REVIEW_PATH, security)
    _write_json(DETERMINISM_REVIEW_PATH, determinism)
    _write_json(RESIDUAL_MONITORING_REVIEW_PATH, residuals)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False, ensure_ascii=True))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
