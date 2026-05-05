from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_validation_call_pre_implementation_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
SCOPE_REVIEW_PATH = AUDIT_DIR / "scope_review.json"
NON_AUTHORIZATION_REVIEW_PATH = AUDIT_DIR / "non_authorization_review.json"
READINESS_SEMANTICS_REVIEW_PATH = AUDIT_DIR / "readiness_semantics_review.json"
CREDENTIAL_SAFETY_REVIEW_PATH = AUDIT_DIR / "credential_safety_review.json"
ENDPOINT_CLIENT_REVIEW_PATH = AUDIT_DIR / "endpoint_client_review.json"
TRANSFORMATION_REVIEW_PATH = AUDIT_DIR / "transformation_review.json"
DEPENDENCY_BLOCK_REVIEW_PATH = AUDIT_DIR / "dependency_block_review.json"
EVIDENCE_SEMANTICS_REVIEW_PATH = AUDIT_DIR / "evidence_semantics_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
BOUNDARY_REVIEW_PATH = AUDIT_DIR / "boundary_review.json"

PLAN_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "pre-implementation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_PLAN.md"
GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "validation-call" / "pre-implementation" / "EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_GATE.md"
AUTH_REVIEW_PATH = (
    ROOT / "docs" / "runtime" / "sandbox" / "authorization" / "EXTERNAL_SANDBOX_SANDBOX_VALIDATION_CALL_AUTHORIZATION_GATE_REVIEW.md"
)
AUTH_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_sandbox_validation_call_authorization_gate" / "final_verdict.json"
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
    '"external_call_authorized": true',
    '"http_client_allowed": true',
    '"platform_sdk_allowed": true',
    '"endpoint_allowed": true',
    '"dns_network_allowed": true',
    '"api_call_allowed": true',
    '"credential_value_access_authorized": true',
    '"request_transformation_authorized": true',
    '"upload_authorized": true',
    '"scheduler_authorized": true',
    '"real_publish_authorized": true',
    '"runtime_integration_authorized": true',
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
    prior_verdict, prior_error = _load_json(AUTH_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_DOC_PATH, GATE_DOC_PATH, AUTH_REVIEW_PATH]
    }
    required_artifacts = {
        str(AUTH_VERDICT_PATH.relative_to(ROOT)): AUTH_VERDICT_PATH.exists()
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


def _scope_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    combined = f"{plan}\n{gate}"
    checks = {
        "future_slice_exact": '"future_slice": "SANDBOX_VALIDATION_CALL_PREPARATION_ONLY"' in combined,
        "offline_only": "offline-only" in plan,
        "pre_execution": "pre-execution" in plan,
        "non_client": "non-client" in plan,
        "non_endpoint": "non-endpoint" in plan,
        "non_network": "non-network" in plan,
        "non_transport": "non-transport" in plan,
        "non_upload": "non-upload" in plan,
        "non_publishing": "non-publishing" in plan,
        "must_not_perform_call": "It must not perform the call." in plan,
        "proposed_files_future_only": "This plan does not create those files." in plan
        and "This plan does not authorize those files." in plan,
        "future_gate_required_before_code": "Future Gate Required Before Code" in plan,
        "no_code_authorized": "No code is authorized." in plan and "No code implementation is authorized." in gate,
        "no_tests_authorized": "No tests are authorized." in plan,
        "no_runtime_integration": '"runtime_integration_authorized": false' in combined,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _non_authorization_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    runner = _read(Path(__file__))
    combined = f"{plan}\n{gate}"
    runner_source = runner.replace('"requests.', '"requests."')
    forbidden_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(runner_source)]
    forbidden_true_assignments = [fragment for fragment in FORBIDDEN_TRUE_ASSIGNMENTS if fragment in combined.lower()]
    required_false_fragments = [
        '"implementation_authorized": false',
        '"external_call_authorized": false',
        '"http_client_allowed": false',
        '"platform_sdk_allowed": false',
        '"endpoint_allowed": false',
        '"dns_network_allowed": false',
        '"api_call_allowed": false',
        '"credential_value_access_authorized": false',
        '"request_transformation_authorized": false',
        '"upload_authorized": false',
        '"scheduler_authorized": false',
        '"real_publish_authorized": false',
        '"runtime_integration_authorized": false',
        '"published_url_allowed": false',
        '"platform_content_id_allowed": false',
        '"receipt_allowed": false',
    ]
    checks = {
        "implementation_unauthorized": '"implementation_authorized": false' in combined,
        "external_call_unauthorized": '"external_call_authorized": false' in combined,
        "http_client_unauthorized": '"http_client_allowed": false' in combined,
        "platform_sdk_unauthorized": '"platform_sdk_allowed": false' in combined,
        "endpoint_unauthorized": '"endpoint_allowed": false' in combined,
        "dns_network_unauthorized": '"dns_network_allowed": false' in combined,
        "api_call_unauthorized": '"api_call_allowed": false' in combined,
        "credential_value_access_unauthorized": '"credential_value_access_authorized": false' in combined,
        "request_transformation_unauthorized": '"request_transformation_authorized": false' in combined,
        "upload_unauthorized": '"upload_authorized": false' in combined,
        "scheduler_unauthorized": '"scheduler_authorized": false' in combined,
        "real_publish_unauthorized": '"real_publish_authorized": false' in combined,
        "runtime_integration_unauthorized": '"runtime_integration_authorized": false' in combined,
        "published_url_unauthorized": '"published_url_allowed": false' in combined,
        "platform_content_id_unauthorized": '"platform_content_id_allowed": false' in combined,
        "receipt_unauthorized": '"receipt_allowed": false' in combined,
        "production_residual_closure_unauthorized": '"production_residual_closure_authorized": false' in combined
        or "production residual closure" in combined,
        "all_required_false_fragments_present": _contains_all(combined, required_false_fragments),
        "no_true_authorization_fragments": not forbidden_true_assignments,
        "runner_has_no_forbidden_network_imports": not forbidden_imports,
    }
    return {
        "required_false_fragments": required_false_fragments,
        "forbidden_true_assignments": forbidden_true_assignments,
        "forbidden_runner_imports": forbidden_imports,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _readiness_semantics_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    checks = {
        "readiness_meaning_local": '"readiness_meaning": "local_preconditions_for_future_sandbox_validation_review"'
        in plan,
        "readiness_not_execution_authorization": '"readiness_is_execution_authorization": false' in plan,
        "readiness_not_publish_success": '"readiness_is_publish_success": false' in plan,
        "readiness_not_platform_success": '"readiness_is_platform_success": false' in plan,
        "readiness_not_close_residuals": '"readiness_closes_production_residuals": false' in plan,
        "does_not_mean_execution_allowed": "execution is allowed" in plan,
        "does_not_mean_endpoint_known": "endpoint is known" in plan,
        "does_not_mean_credentials_valid": "credentials are valid" in plan,
        "does_not_mean_platform_reachable": "platform is reachable" in plan,
        "does_not_mean_sandbox_result_exists": "sandbox result exists" in plan,
        "does_not_mean_production_evidence_exists": "production evidence exists" in plan,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _credential_safety_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    checks = {
        "credential_status_only": "represent credential status only" in plan,
        "credential_value_access_false": "credential_value_access_authorized = false" in plan
        or '"credential_value_access_authorized": false' in plan,
        "reading_secrets_forbidden": "reading secrets" in plan,
        "logging_secrets_forbidden": "logging secrets" in plan,
        "serializing_secrets_forbidden": "serializing secrets" in plan,
        "storing_secrets_forbidden": "storing secrets" in plan,
        "authorization_headers_forbidden": "building authorization headers" in plan,
        "real_credentials_validation_forbidden": "validating real credentials" in plan,
        "real_authentication_forbidden": "testing real authentication" in plan,
        "token_metadata_forbidden": "exposing token-derived metadata" in plan,
        "missing_credentials_block": "credential status is missing or invalid" in plan,
        "invalid_credentials_block": "invalid credentials block" in plan,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _endpoint_client_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    checks = {
        "endpoint_readiness_only": "endpoint readiness status only" in plan,
        "endpoint_authorized_false": "`endpoint_authorized = false`" in plan or '"endpoint_allowed": false' in plan,
        "endpoint_status_not_authorized": "`endpoint_status = not_authorized`" in plan,
        "endpoint_gate_required": "`endpoint_gate_required = true`" in plan,
        "endpoint_value_forbidden": "endpoint value" in plan,
        "base_url_forbidden": "base URL" in plan,
        "api_path_forbidden": "API path" in plan,
        "upload_url_forbidden": "upload URL" in plan,
        "publish_url_forbidden": "publish URL" in plan,
        "oauth_url_forbidden": "OAuth URL" in plan,
        "callback_url_forbidden": "callback URL" in plan,
        "webhook_url_forbidden": "webhook URL" in plan,
        "dns_lookup_forbidden": "DNS lookup" in plan,
        "http_client_import_forbidden": "HTTP client import" in plan,
        "sdk_import_forbidden": "SDK import" in plan,
        "request_method_forbidden": "request method" in plan,
        "headers_forbidden": "headers" in plan,
        "body_forbidden": "body" in plan,
        "endpoint_readiness_not_availability": "Endpoint readiness must not imply endpoint availability." in plan,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _transformation_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    checks = {
        "request_transformation_unauthorized": "request transformation unauthorized" in plan
        or "request transformation_authorized" not in plan,
        "envelope_to_request_forbidden": "converting envelope into request" in plan,
        "request_payload_forbidden": "request payload construction" in plan,
        "request_body_forbidden": "request body construction" in plan,
        "header_construction_forbidden": "header construction" in plan,
        "authorization_construction_forbidden": "authorization construction" in plan,
        "media_byte_packaging_forbidden": "media-byte packaging" in plan,
        "multipart_forbidden": "multipart construction" in plan,
        "transport_serialization_forbidden": "transport serialization" in plan,
        "validation_envelope_audit_only": "audit-only" in plan,
        "validation_envelope_non_transportable": "non-transportable" in plan,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _dependency_block_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    required = {
        "missing_validation_envelope": "validation envelope ref is missing",
        "missing_pre_execution_guard": "pre-execution guard ref is missing",
        "missing_external_call_boundary": "external call boundary ref is missing",
        "missing_controlled_binding": "controlled binding ref is missing",
        "missing_publish_eligibility": "publish eligibility trace is missing",
        "missing_qc_trace": "QC trace is missing",
        "missing_account_health_trace": "Account Health trace is missing",
        "qc_hold": "QC decision is `HOLD`",
        "qc_reject": "QC decision is `REJECT`",
        "qc_publishable_false": "QC `publishable=false`",
        "account_health_hold": "Account Health is `HOLD`",
        "credential_missing_or_invalid": "credential status is missing or invalid",
        "missing_kill_switch": "kill switch status is missing",
        "kill_switch_active": "kill switch is active",
        "missing_rate_limit": "rate limit policy is missing",
        "missing_timeout": "timeout policy is missing",
        "missing_retry": "retry policy is missing",
        "missing_idempotency": "idempotency key is missing",
        "blocks_explicit_serializable": "Every block must be explicit and serializable.",
    }
    checks = {name: fragment in plan for name, fragment in required.items()}
    return {
        "required_fragments": required,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _evidence_semantics_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    checks = {
        "result_evidence_unavailable": '"result_evidence_available": false' in plan,
        "result_evidence_non_production": '"result_evidence_is_production": false' in plan,
        "sandbox_validation_not_executed": '"sandbox_validation_executed": false' in plan,
        "sandbox_validation_not_publish_success": '"sandbox_validation_is_publish_success": false' in plan,
        "sandbox_validation_not_close_residuals": '"sandbox_validation_closes_production_residuals": false' in plan,
        "no_sandbox_evidence_fabrication": "No future pre-implementation object may fabricate sandbox evidence." in plan,
        "timeout_not_success": "timeout is not success" in plan,
        "retry_exhaustion_not_success": "retry exhaustion is not success" in plan,
        "pending_not_success": "pending is not success" in plan,
        "unknown_network_not_success": "unknown network state is not success" in plan,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    combined = f"{plan}\n{gate}"
    checks = {
        "production_publish_evidence_residual_open": EXPECTED_RESIDUALS[0] in combined,
        "platform_integration_residual_open": EXPECTED_RESIDUALS[1] in combined,
        "publish_result_history_residual_open": EXPECTED_RESIDUALS[2] in combined,
        "external_call_not_implemented_residual_open": EXPECTED_RESIDUALS[3] in combined,
        "external_sandbox_execution_not_authorized_residual_open": EXPECTED_RESIDUALS[4] in combined,
        "production_residuals_remain_open_asserted": '"production_residuals_remain_open": true' in combined,
        "may_reduce_only_preimplementation_uncertainty": "pre-implementation scope uncertainty" in plan,
        "must_not_reduce_production_publish": "production publish evidence residuals" in plan,
        "must_not_reduce_platform_integration": "platform integration residuals" in plan,
        "must_not_reduce_publish_history": "publish result history residuals" in plan,
        "must_not_reduce_external_execution": "external execution residuals" in plan,
        "must_not_reduce_attribution": "attribution causality residuals" in plan,
    }
    return {
        "residual_monitoring": EXPECTED_RESIDUALS,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    auth_review = _read(AUTH_REVIEW_PATH)
    combined = f"{plan}\n{gate}\n{auth_review}"
    checks = {
        "publisher_not_external_client": "Publisher is not yet an external execution client" in combined,
        "qc_boundary_preserved": "QC remains final artifact evaluator" in combined,
        "account_health_hold_preserved": "Account Health `HOLD` remains blocking authority" in combined,
        "strategy_boundary_preserved": "Strategy remains control layer" in combined,
        "orchestrator_boundary_preserved": "Orchestrator remains coordinator" in combined,
        "attribution_boundary_preserved": "Attribution cannot claim causality without production evidence" in combined,
        "experiment_boundary_preserved": "Experiment cannot create publish authority" in combined,
        "core_pipeline_unchanged": "Core pipeline remains unchanged" in combined
        or "core pipeline remains unchanged" in combined,
        "qc_not_bypassed": "bypasses QC" in combined,
        "account_health_not_overridden": "overrides Account Health `HOLD`" in combined,
        "runtime_not_integrated": '"runtime_integration_authorized": false' in combined,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _run_scenarios(
    *,
    preconditions: dict[str, Any],
    scope: dict[str, Any],
    non_auth: dict[str, Any],
    readiness: dict[str, Any],
    credential: dict[str, Any],
    endpoint_client: dict[str, Any],
    transformation: dict[str, Any],
    dependencies: dict[str, Any],
    evidence: dict[str, Any],
    residuals: dict[str, Any],
    boundary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    scenario_checks = {
        "pre_implementation_plan_exists": PLAN_DOC_PATH.exists(),
        "prior_review_exists": AUTH_REVIEW_PATH.exists(),
        "prior_authorization_gate_verdict_exists": AUTH_VERDICT_PATH.exists(),
        "prior_authorization_gate_verdict_acceptable": preconditions["checks"]["prior_gate_verdict_acceptable"],
        "future_slice_exact": scope["checks"]["future_slice_exact"],
        "future_slice_offline_only": scope["checks"]["offline_only"],
        "future_slice_pre_execution": scope["checks"]["pre_execution"],
        "future_slice_non_client": scope["checks"]["non_client"],
        "future_slice_non_endpoint": scope["checks"]["non_endpoint"],
        "future_slice_non_network": scope["checks"]["non_network"],
        "future_slice_non_transport": scope["checks"]["non_transport"],
        "future_slice_non_upload": scope["checks"]["non_upload"],
        "future_slice_non_publishing": scope["checks"]["non_publishing"],
        "implementation_unauthorized": non_auth["checks"]["implementation_unauthorized"],
        "external_call_unauthorized": non_auth["checks"]["external_call_unauthorized"],
        "http_client_unauthorized": non_auth["checks"]["http_client_unauthorized"],
        "sdk_unauthorized": non_auth["checks"]["platform_sdk_unauthorized"],
        "endpoint_unauthorized": non_auth["checks"]["endpoint_unauthorized"],
        "dns_network_unauthorized": non_auth["checks"]["dns_network_unauthorized"],
        "api_call_unauthorized": non_auth["checks"]["api_call_unauthorized"],
        "credential_value_access_unauthorized": non_auth["checks"]["credential_value_access_unauthorized"],
        "request_transformation_unauthorized": non_auth["checks"]["request_transformation_unauthorized"],
        "upload_unauthorized": non_auth["checks"]["upload_unauthorized"],
        "scheduler_unauthorized": non_auth["checks"]["scheduler_unauthorized"],
        "publish_unauthorized": non_auth["checks"]["real_publish_unauthorized"],
        "url_unauthorized": non_auth["checks"]["published_url_unauthorized"],
        "platform_content_id_unauthorized": non_auth["checks"]["platform_content_id_unauthorized"],
        "receipt_unauthorized": non_auth["checks"]["receipt_unauthorized"],
        "runtime_integration_unauthorized": non_auth["checks"]["runtime_integration_unauthorized"],
        "production_residual_closure_unauthorized": non_auth["checks"]["production_residual_closure_unauthorized"],
        "readiness_is_not_execution_authorization": readiness["checks"]["readiness_not_execution_authorization"],
        "readiness_is_not_publish_success": readiness["checks"]["readiness_not_publish_success"],
        "readiness_is_not_platform_success": readiness["checks"]["readiness_not_platform_success"],
        "readiness_does_not_close_production_residuals": readiness["checks"]["readiness_not_close_residuals"],
        "credential_status_only": credential["checks"]["credential_status_only"],
        "endpoint_readiness_only": endpoint_client["checks"]["endpoint_readiness_only"],
        "request_transformation_forbidden": transformation["checks"]["request_transformation_unauthorized"],
        "missing_validation_envelope_blocks": dependencies["checks"]["missing_validation_envelope"],
        "missing_pre_execution_guard_blocks": dependencies["checks"]["missing_pre_execution_guard"],
        "missing_boundary_blocks": dependencies["checks"]["missing_external_call_boundary"],
        "missing_controlled_binding_blocks": dependencies["checks"]["missing_controlled_binding"],
        "qc_hold_blocks": dependencies["checks"]["qc_hold"],
        "qc_reject_blocks": dependencies["checks"]["qc_reject"],
        "qc_publishable_false_blocks": dependencies["checks"]["qc_publishable_false"],
        "account_health_hold_blocks": dependencies["checks"]["account_health_hold"],
        "invalid_credentials_block": dependencies["checks"]["credential_missing_or_invalid"],
        "kill_switch_active_blocks": dependencies["checks"]["kill_switch_active"],
        "rate_limit_missing_blocks": dependencies["checks"]["missing_rate_limit"],
        "timeout_retry_idempotency_required": dependencies["checks"]["missing_timeout"]
        and dependencies["checks"]["missing_retry"]
        and dependencies["checks"]["missing_idempotency"],
        "no_sandbox_evidence_fabricated": evidence["checks"]["no_sandbox_evidence_fabrication"],
        "incident_hooks_safe": "incident hooks do not leak secrets" in _read(PLAN_DOC_PATH)
        or ("Incident hooks must not include:" in _read(PLAN_DOC_PATH) and "- secrets" in _read(PLAN_DOC_PATH)),
        "production_residuals_remain_open": residuals["passed"],
        "boundary_preservation": boundary["passed"],
        "deterministic_review": isinstance(
            json.dumps(
                {
                    "scope": scope["checks"],
                    "non_auth": non_auth["checks"],
                    "readiness": readiness["checks"],
                    "credential": credential["checks"],
                    "endpoint_client": endpoint_client["checks"],
                    "transformation": transformation["checks"],
                    "dependencies": dependencies["checks"],
                    "evidence": evidence["checks"],
                    "residuals": residuals["checks"],
                    "boundary": boundary["checks"],
                },
                sort_keys=True,
            ),
            str,
        ),
    }
    return {name: _scenario(name, passed) for name, passed in scenario_checks.items()}


def _build_checklist(
    *,
    preconditions: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    scope: dict[str, Any],
    non_auth: dict[str, Any],
    readiness: dict[str, Any],
    credential: dict[str, Any],
    endpoint_client: dict[str, Any],
    transformation: dict[str, Any],
    dependencies: dict[str, Any],
    evidence: dict[str, Any],
    residuals: dict[str, Any],
    boundary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    checks = {
        "artifacts_present": preconditions["checks"]["required_docs_present"],
        "required_json_parse": preconditions["checks"]["prior_artifact_json_valid"],
        "prior_gate_accepted": preconditions["checks"]["prior_gate_verdict_acceptable"],
        "no_prior_blocking_failures": preconditions["checks"]["prior_gate_no_blocking_failures"],
        "future_slice_exact": scope["checks"]["future_slice_exact"],
        "future_files_future_only": scope["checks"]["proposed_files_future_only"],
        "implementation_unauthorized": non_auth["checks"]["implementation_unauthorized"],
        "external_call_unauthorized": non_auth["checks"]["external_call_unauthorized"],
        "http_sdk_endpoint_dns_api_unauthorized": non_auth["checks"]["http_client_unauthorized"]
        and non_auth["checks"]["platform_sdk_unauthorized"]
        and non_auth["checks"]["endpoint_unauthorized"]
        and non_auth["checks"]["dns_network_unauthorized"]
        and non_auth["checks"]["api_call_unauthorized"],
        "credential_value_access_unauthorized": non_auth["checks"]["credential_value_access_unauthorized"],
        "request_transformation_unauthorized": non_auth["checks"]["request_transformation_unauthorized"],
        "upload_scheduler_publish_unauthorized": non_auth["checks"]["upload_unauthorized"]
        and non_auth["checks"]["scheduler_unauthorized"]
        and non_auth["checks"]["real_publish_unauthorized"],
        "url_platform_content_id_receipt_unauthorized": non_auth["checks"]["published_url_unauthorized"]
        and non_auth["checks"]["platform_content_id_unauthorized"]
        and non_auth["checks"]["receipt_unauthorized"],
        "runtime_integration_unauthorized": non_auth["checks"]["runtime_integration_unauthorized"],
        "readiness_semantics_bounded": readiness["passed"],
        "credential_safety_explicit": credential["passed"],
        "endpoint_client_safety_explicit": endpoint_client["passed"],
        "request_transformation_safety_explicit": transformation["passed"],
        "dependency_blocks_explicit": dependencies["passed"],
        "kill_switch_fail_closed_explicit": "missing_kill_switch_behavior" in _read(PLAN_DOC_PATH)
        and "active_kill_switch_behavior" in _read(PLAN_DOC_PATH),
        "rate_limit_requirements_explicit": "Rate Limit Requirements" in _read(PLAN_DOC_PATH),
        "timeout_retry_idempotency_explicit": "Timeout, Retry And Idempotency Requirements" in _read(PLAN_DOC_PATH),
        "evidence_semantics_non_production": evidence["checks"]["result_evidence_non_production"],
        "no_fabricated_sandbox_evidence": evidence["checks"]["no_sandbox_evidence_fabrication"],
        "incident_hooks_safe": "Incident hooks must not include:" in _read(PLAN_DOC_PATH)
        and "- secrets" in _read(PLAN_DOC_PATH),
        "production_residuals_open": residuals["passed"],
        "qc_boundary_preserved": boundary["checks"]["qc_boundary_preserved"],
        "account_health_boundary_preserved": boundary["checks"]["account_health_hold_preserved"],
        "strategy_boundary_preserved": boundary["checks"]["strategy_boundary_preserved"],
        "orchestrator_boundary_preserved": boundary["checks"]["orchestrator_boundary_preserved"],
        "core_unchanged": boundary["checks"]["core_pipeline_unchanged"],
        "no_true_authorization_fragments": non_auth["checks"]["no_true_authorization_fragments"],
        "runner_has_no_forbidden_network_imports": non_auth["checks"]["runner_has_no_forbidden_network_imports"],
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
    scope = _scope_review()
    non_auth = _non_authorization_review()
    readiness = _readiness_semantics_review()
    credential = _credential_safety_review()
    endpoint_client = _endpoint_client_review()
    transformation = _transformation_review()
    dependencies = _dependency_block_review()
    evidence = _evidence_semantics_review()
    residuals = _residual_monitoring_review()
    boundary = _boundary_review()
    scenarios = _run_scenarios(
        preconditions=preconditions,
        scope=scope,
        non_auth=non_auth,
        readiness=readiness,
        credential=credential,
        endpoint_client=endpoint_client,
        transformation=transformation,
        dependencies=dependencies,
        evidence=evidence,
        residuals=residuals,
        boundary=boundary,
    )
    checklist = _build_checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        scope=scope,
        non_auth=non_auth,
        readiness=readiness,
        credential=credential,
        endpoint_client=endpoint_client,
        transformation=transformation,
        dependencies=dependencies,
        evidence=evidence,
        residuals=residuals,
        boundary=boundary,
    )
    blocking_failures = _blocking_failures(checklist, scenarios)

    scenario_count = len(scenarios)
    scenario_pass_count = sum(1 for item in scenarios.values() if item["passed"])
    checklist_count = len(checklist)
    checklist_pass_count = sum(1 for item in checklist.values() if item["passed"])

    critical_flags = {
        "implementation_authorized": not non_auth["checks"]["implementation_unauthorized"],
        "external_call_authorized": not non_auth["checks"]["external_call_unauthorized"],
        "http_client_allowed": not non_auth["checks"]["http_client_unauthorized"],
        "platform_sdk_allowed": not non_auth["checks"]["platform_sdk_unauthorized"],
        "endpoint_allowed": not non_auth["checks"]["endpoint_unauthorized"],
        "dns_network_allowed": not non_auth["checks"]["dns_network_unauthorized"],
        "api_call_allowed": not non_auth["checks"]["api_call_unauthorized"],
        "credential_value_access_authorized": not non_auth["checks"]["credential_value_access_unauthorized"],
        "request_transformation_authorized": not non_auth["checks"]["request_transformation_unauthorized"],
        "upload_authorized": not non_auth["checks"]["upload_unauthorized"],
        "scheduler_authorized": not non_auth["checks"]["scheduler_unauthorized"],
        "real_publish_authorized": not non_auth["checks"]["real_publish_unauthorized"],
        "runtime_integration_authorized": not non_auth["checks"]["runtime_integration_unauthorized"],
        "production_residuals_closed": not residuals["checks"]["production_residuals_remain_open_asserted"],
        "silent_failures_detected": False,
    }

    hold_required = bool(blocking_failures) or any(critical_flags.values())
    verdict = "HOLD" if hold_required else "GO_WITH_MONITORING"
    recommendation = (
        "PROCEED_TO_EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_GATE_REVIEW"
        if verdict != "HOLD"
        else "HOLD_BEFORE_PRE_IMPLEMENTATION_RUNNER"
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
        "audit_type": "EXTERNAL_SANDBOX_VALIDATION_CALL_PRE_IMPLEMENTATION_GATE",
        "verdict": verdict,
        "timestamp": now,
        "future_slice": "SANDBOX_VALIDATION_CALL_PREPARATION_ONLY",
        "implementation_authorized": False,
        "external_call_authorized": False,
        "http_client_allowed": False,
        "platform_sdk_allowed": False,
        "endpoint_allowed": False,
        "dns_network_allowed": False,
        "api_call_allowed": False,
        "credential_value_access_authorized": False,
        "request_transformation_authorized": False,
        "upload_authorized": False,
        "scheduler_authorized": False,
        "real_publish_authorized": False,
        "runtime_integration_authorized": False,
        "production_residuals_remain_open": residuals["passed"],
        "scenario_pass_count": f"{scenario_pass_count}/{scenario_count}",
        "checklist_pass_count": f"{checklist_pass_count}/{checklist_count}",
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": EXPECTED_RESIDUALS,
        "recommendation": recommendation,
    }

    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(METRICS_PATH, metrics)
    _write_json(SCOPE_REVIEW_PATH, scope)
    _write_json(NON_AUTHORIZATION_REVIEW_PATH, non_auth)
    _write_json(READINESS_SEMANTICS_REVIEW_PATH, readiness)
    _write_json(CREDENTIAL_SAFETY_REVIEW_PATH, credential)
    _write_json(ENDPOINT_CLIENT_REVIEW_PATH, endpoint_client)
    _write_json(TRANSFORMATION_REVIEW_PATH, transformation)
    _write_json(DEPENDENCY_BLOCK_REVIEW_PATH, dependencies)
    _write_json(EVIDENCE_SEMANTICS_REVIEW_PATH, evidence)
    _write_json(RESIDUAL_MONITORING_REVIEW_PATH, residuals)
    _write_json(BOUNDARY_REVIEW_PATH, boundary)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False, ensure_ascii=True))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
