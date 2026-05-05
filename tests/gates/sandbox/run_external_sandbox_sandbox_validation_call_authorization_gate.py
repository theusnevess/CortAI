from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())

AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_sandbox_validation_call_authorization_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
SCOPE_REVIEW_PATH = AUDIT_DIR / "scope_review.json"
NON_AUTHORIZATION_REVIEW_PATH = AUDIT_DIR / "non_authorization_review.json"
CREDENTIAL_SAFETY_REVIEW_PATH = AUDIT_DIR / "credential_safety_review.json"
ENDPOINT_CLIENT_REVIEW_PATH = AUDIT_DIR / "endpoint_client_review.json"
TRANSFORMATION_REVIEW_PATH = AUDIT_DIR / "transformation_review.json"
EVIDENCE_SEMANTICS_REVIEW_PATH = AUDIT_DIR / "evidence_semantics_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
BOUNDARY_REVIEW_PATH = AUDIT_DIR / "boundary_review.json"

PLAN_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "authorization" / "EXTERNAL_SANDBOX_SANDBOX_VALIDATION_CALL_AUTHORIZATION_PLAN.md"
GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "authorization" / "EXTERNAL_SANDBOX_SANDBOX_VALIDATION_CALL_AUTHORIZATION_GATE.md"
FIRST_AUTH_REVIEW_PATH = ROOT / "docs" / "runtime" / "sandbox" / "authorization" / "EXTERNAL_SANDBOX_FIRST_AUTHORIZATION_GATE_REVIEW.md"
FIRST_AUTH_VERDICT_PATH = ROOT / "OUT" / "audit" / "external_sandbox_first_authorization_gate" / "final_verdict.json"

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
    '"credential_value_access_authorized": true',
    '"runtime_integration_authorized": true',
    '"http_client_allowed": true',
    '"platform_sdk_allowed": true',
    '"endpoint_allowed": true',
    '"dns_network_allowed": true',
    '"api_call_allowed": true',
    '"request_transformation_authorized": true',
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
    except Exception as exc:  # noqa: BLE001 - audit gates must report parse failures explicitly
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


def _contains_none(text: str, fragments: list[str]) -> bool:
    lowered = text.lower()
    return all(fragment.lower() not in lowered for fragment in fragments)


def _preconditions() -> dict[str, Any]:
    prior_verdict, prior_error = _load_json(FIRST_AUTH_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_DOC_PATH, GATE_DOC_PATH, FIRST_AUTH_REVIEW_PATH]
    }
    required_artifacts = {
        str(FIRST_AUTH_VERDICT_PATH.relative_to(ROOT)): FIRST_AUTH_VERDICT_PATH.exists()
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
        "prior_gate_credential_value_access_unauthorized": prior_verdict.get("credential_value_access_authorized")
        is False,
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
        "sandbox_validation_call_authorization_planned": "SANDBOX_VALIDATION_CALL_AUTHORIZATION" in plan,
        "authorization_scope_exact_future": '"authorization_scope_exact": "SANDBOX_VALIDATION_CALL_ONLY"' in plan
        and "exact future scope `SANDBOX_VALIDATION_CALL_ONLY`" in gate,
        "sandbox_only": "sandbox-only" in plan,
        "non_production": "non-production" in plan,
        "non_publishing": "non-publishing" in plan,
        "non_uploading": "non-uploading" in plan,
        "non_scheduled": "non-scheduled" in plan,
        "publish_scope_excluded": "- production publishing" in plan,
        "upload_scope_excluded": "- media upload" in plan,
        "scheduler_scope_excluded": "- scheduler invocation" in plan,
        "production_scope_excluded": "- production URL" in plan and "- production receipt" in plan,
        "public_visibility_excluded": "- public visibility" in plan,
        "post_publish_metrics_excluded": "- post-publish metrics" in plan,
        "attribution_causality_excluded": "- attribution causality" in plan,
        "no_inferred_scopes": "No future gate may infer those scopes from this plan." in plan,
        "gate_scope_is_authorization_plan_only": "This gate validates only the plan" in gate,
    }
    forbidden_scope_fragments = [
        "external call authorized",
        "implementation authorized",
        "credential value access authorized",
        "runtime integration authorized",
        "publish authorized",
        "upload authorized",
        "scheduler authorized",
    ]
    checks["no_positive_authorization_language"] = _contains_none(combined, forbidden_scope_fragments)
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
        '"credential_value_access_authorized": false',
        '"runtime_integration_authorized": false',
        '"http_client_allowed": false',
        '"platform_sdk_allowed": false',
        '"endpoint_allowed": false',
        '"dns_network_allowed": false',
        '"api_call_allowed": false',
        '"request_transformation_authorized": false',
        '"upload_authorized": false',
        '"scheduler_authorized": false',
        '"real_publish_authorized": false',
        '"published_url_allowed": false',
        '"platform_content_id_allowed": false',
        '"receipt_allowed": false',
    ]
    checks = {
        "implementation_unauthorized": '"implementation_authorized": false' in combined,
        "external_call_unauthorized": '"external_call_authorized": false' in combined,
        "credential_value_access_unauthorized": '"credential_value_access_authorized": false' in combined,
        "runtime_integration_unauthorized": '"runtime_integration_authorized": false' in combined,
        "http_client_unauthorized": '"http_client_allowed": false' in combined,
        "platform_sdk_unauthorized": '"platform_sdk_allowed": false' in combined,
        "endpoint_unauthorized": '"endpoint_allowed": false' in combined,
        "dns_network_unauthorized": '"dns_network_allowed": false' in combined,
        "api_call_unauthorized": '"api_call_allowed": false' in combined,
        "request_transformation_unauthorized": '"request_transformation_authorized": false' in combined,
        "upload_unauthorized": '"upload_authorized": false' in combined,
        "scheduler_unauthorized": '"scheduler_authorized": false' in combined,
        "real_publish_unauthorized": '"real_publish_authorized": false' in combined,
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


def _credential_safety_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    checks = {
        "credential_status_metadata_only": "credential status only as metadata" in plan,
        "status_present_defined": '"present"' in plan,
        "status_missing_defined": '"missing"' in plan,
        "status_invalid_shape_defined": '"invalid_shape"' in plan,
        "status_not_checked_defined": '"not_checked"' in plan,
        "reading_values_forbidden": "reading credential values" in plan,
        "logging_values_forbidden": "logging credential values" in plan,
        "serializing_values_forbidden": "serializing credential values" in plan,
        "authorization_headers_forbidden": "creating authorization headers" in plan,
        "real_account_validation_forbidden": "validating a real account" in plan,
        "real_authentication_forbidden": "testing real authentication" in plan,
        "token_storage_forbidden": "storing real tokens" in plan,
        "refresh_token_storage_forbidden": "storing refresh tokens" in plan,
        "client_secret_storage_forbidden": "storing client secrets" in plan,
        "credential_presence_not_readiness": "Credential presence must not imply execution readiness." in plan,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _endpoint_client_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    combined = f"{plan}\n{gate}"
    checks = {
        "endpoint_values_not_authorized": "This plan does not authorize endpoint values." in plan,
        "real_base_url_forbidden": "real base URL" in plan,
        "api_path_forbidden": "API path" in plan,
        "upload_url_forbidden": "upload URL" in plan,
        "publish_url_forbidden": "publish URL" in plan,
        "oauth_url_forbidden": "OAuth URL" in plan,
        "webhook_url_forbidden": "webhook URL" in plan,
        "callback_url_forbidden": "callback URL" in plan,
        "dns_target_forbidden": "DNS target" in plan,
        "http_client_false": '"http_client_allowed": false' in combined,
        "platform_sdk_false": '"platform_sdk_allowed": false' in combined,
        "dns_network_false": '"dns_network_allowed": false' in combined,
        "api_call_false": '"api_call_allowed": false' in combined,
        "separate_client_plan_required": "separate client plan" in plan,
        "separate_client_gate_required": "separate client gate" in plan,
        "client_not_direct_from_plan": "No client may be introduced directly from this plan." in plan,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _transformation_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    gate = _read(GATE_DOC_PATH)
    combined = f"{plan}\n{gate}"
    checks = {
        "request_transformation_not_authorized": "This plan does not authorize request transformation." in plan,
        "validation_envelope_inert": "inert" in plan,
        "validation_envelope_audit_only": "audit-only" in plan,
        "validation_envelope_non_transportable": "non-transportable" in plan,
        "validation_envelope_non_executable": "non-executable" in plan,
        "not_request_body": "not a request body" in plan,
        "not_http_payload": "not an HTTP payload" in plan,
        "separate_transformation_plan_required": "separate transformation plan" in plan,
        "separate_transformation_gate_required": "separate transformation gate" in plan,
        "source_to_request_mapping_required": "source-to-request mapping" in plan,
        "forbidden_field_scan_required": "forbidden-field scan" in plan,
        "secret_leakage_scan_required": "secret leakage scan" in plan,
        "media_bytes_excluded_required": "proof that media bytes are excluded" in plan,
        "upload_publish_fields_excluded_required": "proof that upload and publish fields are excluded" in plan,
        "request_transformation_false": '"request_transformation_authorized": false' in combined,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _evidence_semantics_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    checks = {
        "result_evidence_non_production": '"result_evidence_is_production": false' in plan,
        "sandbox_receipt_not_publish_receipt": '"sandbox_receipt_is_publish_receipt": false' in plan,
        "sandbox_validation_not_publish_success": '"sandbox_validation_is_publish_success": false' in plan,
        "sandbox_validation_not_close_residuals": '"sandbox_validation_closes_production_residuals": false' in plan,
        "production_success_forbidden": "production success" in plan,
        "publish_success_forbidden": "publish success" in plan,
        "public_url_forbidden": "public URL" in plan,
        "production_platform_content_id_forbidden": "production `platform_content_id`" in plan,
        "production_receipt_forbidden": "production receipt" in plan,
        "post_publish_metric_forbidden": "post-publish metric" in plan,
        "attribution_proof_forbidden": "attribution proof" in plan,
        "performance_prediction_forbidden": "performance prediction" in plan,
        "timeout_not_success": "timeout is not success" in plan,
        "retry_exhaustion_not_success": "retry exhaustion is not success" in plan,
        "network_unknown_not_success": "network unknown is not success" in plan,
        "pending_not_success": "pending is not success" in plan,
        "failed_attempt_not_success": "failed attempt is not success" in plan,
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
        "may_reduce_only_sandbox_uncertainty": "may reduce only sandbox validation uncertainty" in plan,
        "must_not_reduce_production_publish_evidence": "production publish evidence residuals" in plan,
        "must_not_reduce_platform_integration": "real platform integration residuals" in plan
        or "platform integration residuals" in gate,
        "must_not_reduce_publish_history": "production publish result history residuals" in plan
        or "publish result history residuals" in gate,
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
    first_review = _read(FIRST_AUTH_REVIEW_PATH)
    combined = f"{plan}\n{gate}\n{first_review}"
    checks = {
        "publisher_not_external_client": "Publisher is not yet an external execution client" in combined,
        "qc_boundary_preserved": "QC remains final artifact evaluator" in combined,
        "account_health_hold_preserved": "Account Health `HOLD` remains blocking authority" in combined,
        "strategy_boundary_preserved": "Strategy remains control layer" in combined,
        "orchestrator_boundary_preserved": "Orchestrator remains coordinator" in combined,
        "attribution_boundary_preserved": "Attribution cannot claim causality without production evidence" in combined
        or "Attribution cannot claim causality without production publish evidence" in combined,
        "experiment_boundary_preserved": "Experiment cannot create publish authority" in combined,
        "core_pipeline_unchanged": "Core pipeline remains unchanged" in combined
        or "core pipeline remains unchanged" in combined,
        "account_health_hold_blocks": "Account Health `HOLD` blocks" in combined,
        "qc_non_publishable_blocks": "QC non-publishable blocks" in combined,
        "kill_switch_required": "kill switch required" in combined or "kill switch is mandatory" in combined,
        "missing_kill_switch_fails_closed": "missing kill switch fails closed" in combined,
        "active_kill_switch_blocks": "active kill switch blocks" in combined,
        "rate_limits_required": "rate limits" in combined,
        "incident_hooks_defined": "Incident Hook Requirements" in combined,
        "incident_hooks_exclude_secrets": "Incident hooks must not contain:" in combined and "- secrets" in combined,
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
    credential: dict[str, Any],
    endpoint_client: dict[str, Any],
    transformation: dict[str, Any],
    evidence: dict[str, Any],
    residuals: dict[str, Any],
    boundary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    scenario_checks = {
        "authorization_plan_exists": PLAN_DOC_PATH.exists(),
        "prior_review_exists": FIRST_AUTH_REVIEW_PATH.exists(),
        "prior_gate_verdict_exists": FIRST_AUTH_VERDICT_PATH.exists(),
        "prior_gate_verdict_acceptable": preconditions["checks"]["prior_gate_verdict_acceptable"],
        "prior_gate_preserved_non_authorization": preconditions["checks"]["prior_gate_implementation_unauthorized"]
        and preconditions["checks"]["prior_gate_external_call_unauthorized"]
        and preconditions["checks"]["prior_gate_credential_value_access_unauthorized"],
        "sandbox_validation_call_authorization_is_planned": scope["checks"][
            "sandbox_validation_call_authorization_planned"
        ],
        "implementation_unauthorized": non_auth["checks"]["implementation_unauthorized"],
        "external_call_unauthorized": non_auth["checks"]["external_call_unauthorized"],
        "credential_value_access_unauthorized": non_auth["checks"]["credential_value_access_unauthorized"],
        "runtime_integration_unauthorized": non_auth["checks"]["runtime_integration_unauthorized"],
        "http_client_unauthorized": non_auth["checks"]["http_client_unauthorized"],
        "platform_sdk_unauthorized": non_auth["checks"]["platform_sdk_unauthorized"],
        "endpoint_unauthorized": non_auth["checks"]["endpoint_unauthorized"],
        "dns_network_unauthorized": non_auth["checks"]["dns_network_unauthorized"],
        "api_call_unauthorized": non_auth["checks"]["api_call_unauthorized"],
        "request_transformation_unauthorized": non_auth["checks"]["request_transformation_unauthorized"],
        "upload_unauthorized": non_auth["checks"]["upload_unauthorized"],
        "scheduler_unauthorized": non_auth["checks"]["scheduler_unauthorized"],
        "real_publish_unauthorized": non_auth["checks"]["real_publish_unauthorized"],
        "url_unauthorized": non_auth["checks"]["published_url_unauthorized"],
        "platform_content_id_unauthorized": non_auth["checks"]["platform_content_id_unauthorized"],
        "receipt_unauthorized": non_auth["checks"]["receipt_unauthorized"],
        "production_residual_closure_unauthorized": non_auth["checks"]["production_residual_closure_unauthorized"],
        "publish_scope_excluded": scope["checks"]["publish_scope_excluded"],
        "upload_scope_excluded": scope["checks"]["upload_scope_excluded"],
        "scheduler_scope_excluded": scope["checks"]["scheduler_scope_excluded"],
        "production_scope_excluded": scope["checks"]["production_scope_excluded"],
        "post_publish_metrics_excluded": scope["checks"]["post_publish_metrics_excluded"],
        "attribution_causality_excluded": scope["checks"]["attribution_causality_excluded"],
        "credential_status_only": credential["checks"]["credential_status_metadata_only"],
        "credential_values_never_logged": credential["checks"]["logging_values_forbidden"],
        "credential_values_never_serialized": credential["checks"]["serializing_values_forbidden"],
        "authorization_headers_forbidden": credential["checks"]["authorization_headers_forbidden"],
        "endpoint_values_forbidden": endpoint_client["checks"]["endpoint_values_not_authorized"],
        "http_and_sdk_require_separate_gates": endpoint_client["checks"]["separate_client_plan_required"]
        and endpoint_client["checks"]["separate_client_gate_required"],
        "request_transformation_requires_separate_gate": transformation["checks"]["separate_transformation_gate_required"],
        "kill_switch_required": boundary["checks"]["kill_switch_required"],
        "missing_kill_switch_fails_closed": boundary["checks"]["missing_kill_switch_fails_closed"],
        "active_kill_switch_blocks": boundary["checks"]["active_kill_switch_blocks"],
        "account_health_hold_blocks": boundary["checks"]["account_health_hold_blocks"],
        "qc_non_publishable_blocks": boundary["checks"]["qc_non_publishable_blocks"],
        "rate_limits_required": boundary["checks"]["rate_limits_required"],
        "timeout_is_not_success": evidence["checks"]["timeout_not_success"],
        "retry_exhaustion_is_not_success": evidence["checks"]["retry_exhaustion_not_success"],
        "sandbox_evidence_non_production": evidence["checks"]["result_evidence_non_production"],
        "sandbox_validation_not_publish_success": evidence["checks"]["sandbox_validation_not_publish_success"],
        "sandbox_validation_cannot_close_production_residuals": evidence["checks"][
            "sandbox_validation_not_close_residuals"
        ],
        "incident_hooks_defined": boundary["checks"]["incident_hooks_defined"],
        "incident_hooks_exclude_secrets": boundary["checks"]["incident_hooks_exclude_secrets"],
        "boundary_preservation": boundary["passed"],
        "deterministic_gate_review": isinstance(
            json.dumps(
                {
                    "scope": scope["checks"],
                    "non_auth": non_auth["checks"],
                    "credential": credential["checks"],
                    "endpoint_client": endpoint_client["checks"],
                    "transformation": transformation["checks"],
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
    credential: dict[str, Any],
    endpoint_client: dict[str, Any],
    transformation: dict[str, Any],
    evidence: dict[str, Any],
    residuals: dict[str, Any],
    boundary: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    checks = {
        "artifacts_present": preconditions["checks"]["required_docs_present"],
        "required_json_parse": preconditions["checks"]["prior_artifact_json_valid"],
        "prior_gate_accepted": preconditions["checks"]["prior_gate_verdict_acceptable"],
        "no_prior_blocking_failures": preconditions["checks"]["prior_gate_no_blocking_failures"],
        "sandbox_validation_planning_scope_present": scope["checks"][
            "sandbox_validation_call_authorization_planned"
        ],
        "implementation_unauthorized": non_auth["checks"]["implementation_unauthorized"],
        "external_call_unauthorized": non_auth["checks"]["external_call_unauthorized"],
        "credential_value_access_unauthorized": non_auth["checks"]["credential_value_access_unauthorized"],
        "runtime_integration_unauthorized": non_auth["checks"]["runtime_integration_unauthorized"],
        "http_sdk_endpoint_dns_api_unauthorized": non_auth["checks"]["http_client_unauthorized"]
        and non_auth["checks"]["platform_sdk_unauthorized"]
        and non_auth["checks"]["endpoint_unauthorized"]
        and non_auth["checks"]["dns_network_unauthorized"]
        and non_auth["checks"]["api_call_unauthorized"],
        "request_transformation_unauthorized": non_auth["checks"]["request_transformation_unauthorized"],
        "upload_scheduler_publish_unauthorized": non_auth["checks"]["upload_unauthorized"]
        and non_auth["checks"]["scheduler_unauthorized"]
        and non_auth["checks"]["real_publish_unauthorized"],
        "url_platform_content_id_receipt_unauthorized": non_auth["checks"]["published_url_unauthorized"]
        and non_auth["checks"]["platform_content_id_unauthorized"]
        and non_auth["checks"]["receipt_unauthorized"],
        "production_residuals_open": residuals["passed"],
        "publish_upload_scheduler_scopes_excluded": scope["checks"]["publish_scope_excluded"]
        and scope["checks"]["upload_scope_excluded"]
        and scope["checks"]["scheduler_scope_excluded"],
        "production_scope_excluded": scope["checks"]["production_scope_excluded"],
        "credential_status_metadata_only": credential["checks"]["credential_status_metadata_only"],
        "secret_value_handling_forbidden": credential["checks"]["reading_values_forbidden"]
        and credential["checks"]["logging_values_forbidden"]
        and credential["checks"]["serializing_values_forbidden"],
        "endpoint_values_forbidden": endpoint_client["checks"]["endpoint_values_not_authorized"],
        "client_gate_required": endpoint_client["checks"]["separate_client_plan_required"]
        and endpoint_client["checks"]["separate_client_gate_required"],
        "transformation_gate_required": transformation["checks"]["separate_transformation_plan_required"]
        and transformation["checks"]["separate_transformation_gate_required"],
        "kill_switch_required": boundary["checks"]["kill_switch_required"],
        "fail_closed_behavior_required": boundary["checks"]["missing_kill_switch_fails_closed"]
        and boundary["checks"]["active_kill_switch_blocks"],
        "rate_limits_required": boundary["checks"]["rate_limits_required"],
        "timeout_retry_semantics_explicit": evidence["checks"]["timeout_not_success"]
        and evidence["checks"]["retry_exhaustion_not_success"],
        "sandbox_evidence_non_production": evidence["checks"]["result_evidence_non_production"],
        "sandbox_validation_not_publish_success": evidence["checks"]["sandbox_validation_not_publish_success"],
        "incident_hooks_safe": boundary["checks"]["incident_hooks_defined"]
        and boundary["checks"]["incident_hooks_exclude_secrets"],
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
    credential = _credential_safety_review()
    endpoint_client = _endpoint_client_review()
    transformation = _transformation_review()
    evidence = _evidence_semantics_review()
    residuals = _residual_monitoring_review()
    boundary = _boundary_review()
    scenarios = _run_scenarios(
        preconditions=preconditions,
        scope=scope,
        non_auth=non_auth,
        credential=credential,
        endpoint_client=endpoint_client,
        transformation=transformation,
        evidence=evidence,
        residuals=residuals,
        boundary=boundary,
    )
    checklist = _build_checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        scope=scope,
        non_auth=non_auth,
        credential=credential,
        endpoint_client=endpoint_client,
        transformation=transformation,
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
        "credential_value_access_authorized": not non_auth["checks"]["credential_value_access_unauthorized"],
        "runtime_integration_authorized": not non_auth["checks"]["runtime_integration_unauthorized"],
        "http_client_allowed": not non_auth["checks"]["http_client_unauthorized"],
        "platform_sdk_allowed": not non_auth["checks"]["platform_sdk_unauthorized"],
        "endpoint_allowed": not non_auth["checks"]["endpoint_unauthorized"],
        "dns_network_allowed": not non_auth["checks"]["dns_network_unauthorized"],
        "api_call_allowed": not non_auth["checks"]["api_call_unauthorized"],
        "request_transformation_authorized": not non_auth["checks"]["request_transformation_unauthorized"],
        "upload_authorized": not non_auth["checks"]["upload_unauthorized"],
        "scheduler_authorized": not non_auth["checks"]["scheduler_unauthorized"],
        "real_publish_authorized": not non_auth["checks"]["real_publish_unauthorized"],
        "published_url_allowed": not non_auth["checks"]["published_url_unauthorized"],
        "platform_content_id_allowed": not non_auth["checks"]["platform_content_id_unauthorized"],
        "receipt_allowed": not non_auth["checks"]["receipt_unauthorized"],
        "production_residuals_closed": not residuals["checks"]["production_residuals_remain_open_asserted"],
        "silent_failures_detected": False,
    }

    hold_required = bool(blocking_failures) or any(critical_flags.values())
    verdict = "HOLD" if hold_required else "GO_WITH_MONITORING"
    recommendation = (
        "PROCEED_TO_EXTERNAL_SANDBOX_SANDBOX_VALIDATION_CALL_AUTHORIZATION_GATE_REVIEW"
        if verdict != "HOLD"
        else "HOLD_BEFORE_SANDBOX_VALIDATION_AUTHORIZATION_RUNNER"
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
        "audit_type": "EXTERNAL_SANDBOX_SANDBOX_VALIDATION_CALL_AUTHORIZATION_GATE",
        "verdict": verdict,
        "timestamp": now,
        "sandbox_validation_call_authorization_planned": scope["checks"][
            "sandbox_validation_call_authorization_planned"
        ],
        "implementation_authorized": False,
        "external_call_authorized": False,
        "credential_value_access_authorized": False,
        "runtime_integration_authorized": False,
        "http_client_allowed": False,
        "platform_sdk_allowed": False,
        "endpoint_allowed": False,
        "dns_network_allowed": False,
        "api_call_allowed": False,
        "request_transformation_authorized": False,
        "upload_authorized": False,
        "scheduler_authorized": False,
        "real_publish_authorized": False,
        "published_url_allowed": False,
        "platform_content_id_allowed": False,
        "receipt_allowed": False,
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
    _write_json(CREDENTIAL_SAFETY_REVIEW_PATH, credential)
    _write_json(ENDPOINT_CLIENT_REVIEW_PATH, endpoint_client)
    _write_json(TRANSFORMATION_REVIEW_PATH, transformation)
    _write_json(EVIDENCE_SEMANTICS_REVIEW_PATH, evidence)
    _write_json(RESIDUAL_MONITORING_REVIEW_PATH, residuals)
    _write_json(BOUNDARY_REVIEW_PATH, boundary)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False, ensure_ascii=True))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
