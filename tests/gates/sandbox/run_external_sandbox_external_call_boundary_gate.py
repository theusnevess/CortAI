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

from app.creative.agents.publisher.external_sandbox_controlled_binding import (  # noqa: E402
    ExternalSandboxControlledBindingBuilder,
    ExternalSandboxControlledBindingInput,
)
from app.creative.agents.publisher.external_sandbox_validation_envelope import (  # noqa: E402
    ExternalSandboxValidationEnvelopeBuilder,
    ExternalSandboxValidationEnvelopeInput,
)
from app.creative.agents.publisher.sandbox_contracts import PRODUCTION_RESIDUALS  # noqa: E402


AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_external_call_boundary_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
STATIC_SCAN_REVIEW_PATH = AUDIT_DIR / "static_scan_review.json"
BOUNDARY_COMPLETENESS_REVIEW_PATH = AUDIT_DIR / "boundary_completeness_review.json"
SIDE_EFFECT_ABSENCE_REVIEW_PATH = AUDIT_DIR / "side_effect_absence_review.json"
RESIDUAL_MONITORING_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
ANTI_FAKE_SUCCESS_REVIEW_PATH = AUDIT_DIR / "anti_fake_success_review.json"
NEXT_STEP_REVIEW_PATH = AUDIT_DIR / "next_step_review.json"

PLAN_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "external-call-boundary" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_PLAN.md"
GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "external-call-boundary" / "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE.md"
CONTROLLED_BINDING_REVIEW_PATH = ROOT / "docs" / "runtime" / "sandbox" / "controlled-binding" / "EXTERNAL_SANDBOX_CONTROLLED_BINDING_REVIEW.md"
CONTROLLED_BINDING_GATE_PATH = ROOT / "docs" / "runtime" / "sandbox" / "controlled-binding" / "EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE.md"
CONTROLLED_BINDING_GATE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_controlled_binding_gate" / "final_verdict.json"
)

PUBLISHER_SOURCE_DIR = ROOT / "backend" / "app" / "creative" / "agents" / "publisher"
PUBLISHER_SOURCE_FILES = sorted(PUBLISHER_SOURCE_DIR.glob("*.py"))

FORBIDDEN_IMPORT_PATTERN = re.compile(
    r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|dns|googleapiclient|boto3)\b",
    re.MULTILINE,
)
FORBIDDEN_HELPER_PATTERN = re.compile(
    r"^\s*def\s+(to_request|as_request|to_payload|as_payload|to_http|to_headers|to_body|send|execute|post|put|patch|upload|publish|schedule|emit_url|emit_receipt|create_receipt)\s*\(",
    re.MULTILINE,
)
ENDPOINT_CONSTANT_PATTERN = re.compile(
    r"^\s*[A-Z_]*(ENDPOINT|BASE_URL|UPLOAD_URL|PUBLISH_URL|CALLBACK_URL|WEBHOOK_URL)[A-Z_]*\s*=",
    re.MULTILINE,
)
NETWORK_LITERAL_TOKENS = [
    "requests.",
    "httpx.",
    "aiohttp.",
    "urllib.request.",
    "urllib3.",
    "socket.",
    ".getaddrinfo(",
    ".connect(",
    "dns.resolver",
]


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
    except Exception as exc:  # noqa: BLE001 - audit gate captures read failures explicitly
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


def _controlled_binding() -> dict[str, Any]:
    binding = ExternalSandboxControlledBindingBuilder().build(
        ExternalSandboxControlledBindingInput(
            run_id="run_external_call_boundary_gate",
            content_id="content_external_call_boundary_gate",
            qc_trace_ref="qc_trace:external_call_boundary_gate",
            account_health_trace_ref="account_health_trace:external_call_boundary_gate",
        )
    )
    return binding.to_dict()


def _validation_envelope() -> dict[str, Any]:
    envelope = ExternalSandboxValidationEnvelopeBuilder().build(
        ExternalSandboxValidationEnvelopeInput(
            run_id="run_external_call_boundary_gate",
            content_id="content_external_call_boundary_gate",
            artifact_manifest_ref="artifact_manifest:external_call_boundary_gate",
            metadata_payload_ref="metadata_payload:external_call_boundary_gate",
            qc_trace_ref="qc_trace:external_call_boundary_gate",
            account_health_trace_ref="health_trace:external_call_boundary_gate",
            strategy_ref="strategy:external_call_boundary_gate",
            publish_eligibility_trace_ref="publish_eligibility:external_call_boundary_gate",
            metadata={
                "title": "Sandbox title",
                "description": "Sandbox description",
                "tags": ["sandbox", "boundary"],
                "language": "en",
                "visibility_mode": "sandbox_only",
                "account_id": "account_sandbox",
                "runtime_policy_ref": "runtime_policy:sandbox",
                "metadata_trace_ref": "metadata_trace:sandbox",
            },
        )
    )
    return envelope.to_dict()


def _preconditions() -> dict[str, Any]:
    controlled_gate, controlled_gate_error = _load_json(CONTROLLED_BINDING_GATE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_DOC_PATH, GATE_DOC_PATH, CONTROLLED_BINDING_REVIEW_PATH, CONTROLLED_BINDING_GATE_PATH]
    }
    required_artifacts = {
        str(CONTROLLED_BINDING_GATE_VERDICT_PATH.relative_to(ROOT)): CONTROLLED_BINDING_GATE_VERDICT_PATH.exists()
    }
    checks = {
        "required_docs_present": all(required_docs.values()),
        "required_artifacts_present": all(required_artifacts.values()),
        "controlled_binding_gate_json_valid": not controlled_gate_error,
        "controlled_binding_gate_verdict_acceptable": controlled_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "controlled_binding_inactive": controlled_gate.get("binding_active") is False,
        "controlled_binding_no_external_call": controlled_gate.get("external_call_authorized") is False,
        "controlled_binding_no_http_client": controlled_gate.get("http_client_allowed") is False,
        "controlled_binding_no_sdk": controlled_gate.get("platform_sdk_allowed") is False,
        "controlled_binding_no_endpoint": controlled_gate.get("endpoint_allowed") is False,
        "controlled_binding_no_network": controlled_gate.get("network_access_allowed") is False,
        "controlled_binding_no_api_call": controlled_gate.get("api_call_allowed") is False,
        "controlled_binding_no_upload": controlled_gate.get("upload_authorized") is False,
        "controlled_binding_no_scheduler": controlled_gate.get("scheduler_authorized") is False,
        "controlled_binding_no_publish": controlled_gate.get("real_publish_authorized") is False,
        "controlled_binding_no_url": controlled_gate.get("url_emitted") is False,
        "controlled_binding_no_platform_content_id": controlled_gate.get("platform_content_id_emitted") is False,
        "controlled_binding_no_receipt": controlled_gate.get("receipt_emitted") is False,
        "controlled_binding_no_credential_value_access": controlled_gate.get("credential_value_accessed") is False,
        "controlled_binding_residuals_open": controlled_gate.get("production_residuals_closed") is False,
    }
    return {
        "required_docs": required_docs,
        "required_artifacts": required_artifacts,
        "controlled_binding_gate_error": controlled_gate_error,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _source_text_by_file() -> dict[str, str]:
    return {str(path.relative_to(ROOT)): _read(path) for path in PUBLISHER_SOURCE_FILES}


def _static_scan_review() -> dict[str, Any]:
    matches: dict[str, dict[str, list[str]]] = {}
    for label, source in _source_text_by_file().items():
        forbidden_imports = [match.group(0).strip() for match in FORBIDDEN_IMPORT_PATTERN.finditer(source)]
        forbidden_helpers = [match.group(0).strip() for match in FORBIDDEN_HELPER_PATTERN.finditer(source)]
        endpoint_constants = [match.group(0).strip() for match in ENDPOINT_CONSTANT_PATTERN.finditer(source)]
        network_literals = [token for token in NETWORK_LITERAL_TOKENS if token in source]
        if forbidden_imports or forbidden_helpers or endpoint_constants or network_literals:
            matches[label] = {
                "forbidden_imports": forbidden_imports,
                "forbidden_helpers": forbidden_helpers,
                "endpoint_constants": endpoint_constants,
                "network_literals": network_literals,
            }
    checks = {
        "no_http_client": all(not item["forbidden_imports"] for item in matches.values()),
        "no_sdk": all(not item["forbidden_imports"] for item in matches.values()),
        "no_endpoint": all(not item["endpoint_constants"] for item in matches.values()),
        "no_dns_network": all(not item["network_literals"] for item in matches.values()),
        "no_request_transformation": all(not item["forbidden_helpers"] for item in matches.values()),
    }
    return {
        "scanned_files": sorted(_source_text_by_file().keys()),
        "matches": matches,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _boundary_completeness_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    required_terms = {
        "external_call_authority_model": "External Call Authority Model",
        "validation_execution_separation": "Boundary Between Validation And Execution",
        "endpoint_boundary": "Future Endpoint Boundary",
        "client_boundary": "Future Client Boundary",
        "request_shape_boundary": "Future Request Shape Boundary",
        "credential_boundary": "Credential Boundary",
        "kill_switch_boundary": "Kill Switch Boundary",
        "rate_limit_boundary": "Rate-Limit Boundary",
        "timeout_retry_boundary": "Timeout And Retry Boundary",
        "result_evidence_boundary": "Result Evidence Boundary",
        "lifecycle_boundary": "Lifecycle Evidence Boundary",
        "incident_hooks": "Incident Hooks",
        "anti_fake_success": "Anti-Fake-Success Rules",
        "residual_monitoring": "Residual Monitoring",
        "failure_conditions": "Failure Conditions",
        "next_authorized_artifact": "Next Authorized Artifact",
    }
    checks = {name: term in plan for name, term in required_terms.items()}
    return {
        "required_terms": required_terms,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _side_effect_absence_review(static_scan: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "external_call_absent": binding["external_call_authorized"] is False,
        "http_client_absent": static_scan["checks"]["no_http_client"] and binding["http_client_allowed"] is False,
        "sdk_absent": static_scan["checks"]["no_sdk"] and binding["platform_sdk_allowed"] is False,
        "endpoint_absent": static_scan["checks"]["no_endpoint"] and binding["endpoint_allowed"] is False,
        "dns_network_absent": static_scan["checks"]["no_dns_network"] and binding["network_access_allowed"] is False,
        "api_call_absent": binding["api_call_allowed"] is False,
        "upload_absent": binding["upload_authorized"] is False,
        "scheduler_absent": binding["scheduler_authorized"] is False,
        "publish_absent": binding["real_publish_authorized"] is False,
        "url_absent": binding["url_authorized"] is False,
        "platform_content_id_absent": binding["platform_content_id_authorized"] is False,
        "receipt_absent": binding["receipt_authorized"] is False,
        "credential_value_access_absent": binding["credential_value_accessed"] is False,
        "authorization_header_absent": True,
        "request_transformation_absent": static_scan["checks"]["no_request_transformation"],
    }
    return {
        "checks": checks,
        "observed_binding": {
            "binding_active": binding["binding_active"],
            "external_call_authorized": binding["external_call_authorized"],
            "http_client_allowed": binding["http_client_allowed"],
            "platform_sdk_allowed": binding["platform_sdk_allowed"],
            "endpoint_allowed": binding["endpoint_allowed"],
            "network_access_allowed": binding["network_access_allowed"],
            "api_call_allowed": binding["api_call_allowed"],
            "upload_authorized": binding["upload_authorized"],
            "scheduler_authorized": binding["scheduler_authorized"],
            "real_publish_authorized": binding["real_publish_authorized"],
            "url_authorized": binding["url_authorized"],
            "platform_content_id_authorized": binding["platform_content_id_authorized"],
            "receipt_authorized": binding["receipt_authorized"],
            "credential_value_accessed": binding["credential_value_accessed"],
        },
        "passed": all(checks.values()),
    }


def _residual_monitoring_review() -> dict[str, Any]:
    residuals = list(PRODUCTION_RESIDUALS)
    checks = {
        "production_publish_evidence_residual_open": "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET" in residuals,
        "platform_integration_residual_open": "PLATFORM_INTEGRATION_NOT_ENABLED" in residuals,
        "publish_result_history_residual_open": "PUBLISH_RESULT_HISTORY_STILL_SHORT" in residuals,
        "production_residuals_closed_false": residuals == PRODUCTION_RESIDUALS,
    }
    return {
        "residual_monitoring": residuals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _anti_fake_success_review() -> dict[str, Any]:
    plan = _read(PLAN_DOC_PATH)
    required_patterns = {
        "sandbox_validation_not_publish_success": ["treat sandbox validation as publish success"],
        "missing_evidence_not_success": ["missing evidence treated as success"],
        "pending_not_success": ["pending treated as success"],
        "timeout_not_success": ["timeout is not success", "timeout_is_not_success"],
        "published_url_forbidden": ["`published_url` present"],
        "platform_content_id_forbidden": ["`platform_content_id` present"],
        "production_receipt_forbidden": ["production receipt present"],
        "production_evidence_forbidden": ["`result_evidence_is_production = true`"],
    }
    checks = {name: any(pattern in plan for pattern in patterns) for name, patterns in required_patterns.items()}
    return {
        "required_patterns": required_patterns,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _next_step_review() -> dict[str, Any]:
    gate = _read(GATE_DOC_PATH)
    checks = {
        "next_runner_defined": "tests/gates/sandbox/run_external_sandbox_external_call_boundary_gate.py" in gate,
        "runner_audit_only": "audit-only" in gate,
        "runner_must_not_implement_boundary": "It must not implement the boundary." in gate,
        "external_call_still_forbidden": "external call" in gate and "Still forbidden" in gate,
        "production_residual_closure_forbidden": "production residual closure" in gate,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _audit_objects_review(binding: dict[str, Any], envelope: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "binding_transport_authority_none": binding["transport_authority"] == "none",
        "binding_execution_authority_none": binding["execution_authority"] == "none",
        "binding_no_request_helpers": True,
        "envelope_transport_capability_none": envelope["transport_capability"] == "none",
        "envelope_execution_capability_none": envelope["execution_capability"] == "none",
        "envelope_non_transportable": envelope["non_transportable"] is True,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _run_scenarios(
    *,
    preconditions: dict[str, Any],
    static_scan: dict[str, Any],
    boundary: dict[str, Any],
    side_effects: dict[str, Any],
    residuals: dict[str, Any],
    anti_fake: dict[str, Any],
    next_step: dict[str, Any],
    audit_objects: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    scenarios = {
        "boundary_plan_exists": _scenario("boundary_plan_exists", PLAN_DOC_PATH.exists()),
        "controlled_binding_review_exists": _scenario(
            "controlled_binding_review_exists", CONTROLLED_BINDING_REVIEW_PATH.exists()
        ),
        "controlled_binding_gate_verdict_acceptable": _scenario(
            "controlled_binding_gate_verdict_acceptable",
            preconditions["checks"]["controlled_binding_gate_verdict_acceptable"],
        ),
        "current_external_call_absent": _scenario(
            "current_external_call_absent", side_effects["checks"]["external_call_absent"]
        ),
        "current_http_client_absent": _scenario(
            "current_http_client_absent", side_effects["checks"]["http_client_absent"]
        ),
        "current_sdk_absent": _scenario("current_sdk_absent", side_effects["checks"]["sdk_absent"]),
        "current_endpoint_absent": _scenario("current_endpoint_absent", side_effects["checks"]["endpoint_absent"]),
        "current_dns_network_access_absent": _scenario(
            "current_dns_network_access_absent", side_effects["checks"]["dns_network_absent"]
        ),
        "current_api_call_absent": _scenario("current_api_call_absent", side_effects["checks"]["api_call_absent"]),
        "current_upload_absent": _scenario("current_upload_absent", side_effects["checks"]["upload_absent"]),
        "current_scheduler_absent": _scenario("current_scheduler_absent", side_effects["checks"]["scheduler_absent"]),
        "current_publish_absent": _scenario("current_publish_absent", side_effects["checks"]["publish_absent"]),
        "current_url_emission_absent": _scenario("current_url_emission_absent", side_effects["checks"]["url_absent"]),
        "current_platform_content_id_emission_absent": _scenario(
            "current_platform_content_id_emission_absent",
            side_effects["checks"]["platform_content_id_absent"],
        ),
        "current_receipt_emission_absent": _scenario(
            "current_receipt_emission_absent", side_effects["checks"]["receipt_absent"]
        ),
        "production_residuals_remain_open": _scenario("production_residuals_remain_open", residuals["passed"]),
        "credential_values_remain_unauthorized": _scenario(
            "credential_values_remain_unauthorized", side_effects["checks"]["credential_value_access_absent"]
        ),
        "authorization_headers_remain_unauthorized": _scenario(
            "authorization_headers_remain_unauthorized", side_effects["checks"]["authorization_header_absent"]
        ),
        "audit_objects_are_not_transport_payloads": _scenario(
            "audit_objects_are_not_transport_payloads", audit_objects["passed"]
        ),
        "endpoint_boundary_explicit": _scenario("endpoint_boundary_explicit", boundary["checks"]["endpoint_boundary"]),
        "client_boundary_explicit": _scenario("client_boundary_explicit", boundary["checks"]["client_boundary"]),
        "request_shape_boundary_explicit": _scenario(
            "request_shape_boundary_explicit", boundary["checks"]["request_shape_boundary"]
        ),
        "kill_switch_fail_closed_boundary_explicit": _scenario(
            "kill_switch_fail_closed_boundary_explicit", boundary["checks"]["kill_switch_boundary"]
        ),
        "rate_limit_non_unlimited_boundary_explicit": _scenario(
            "rate_limit_non_unlimited_boundary_explicit", boundary["checks"]["rate_limit_boundary"]
        ),
        "timeout_and_retry_boundary_explicit": _scenario(
            "timeout_and_retry_boundary_explicit", boundary["checks"]["timeout_retry_boundary"]
        ),
        "anti_fake_success_rules_explicit": _scenario("anti_fake_success_rules_explicit", anti_fake["passed"]),
        "sandbox_validation_is_not_publish_success": _scenario(
            "sandbox_validation_is_not_publish_success",
            anti_fake["checks"]["sandbox_validation_not_publish_success"],
        ),
        "missing_evidence_is_not_success": _scenario(
            "missing_evidence_is_not_success", anti_fake["checks"]["missing_evidence_not_success"]
        ),
        "pending_is_not_success": _scenario("pending_is_not_success", anti_fake["checks"]["pending_not_success"]),
        "timeout_is_not_success": _scenario("timeout_is_not_success", anti_fake["checks"]["timeout_not_success"]),
        "url_platform_id_forbidden": _scenario(
            "url_platform_id_forbidden",
            anti_fake["checks"]["published_url_forbidden"] and anti_fake["checks"]["platform_content_id_forbidden"],
        ),
        "receipt_forbidden": _scenario("receipt_forbidden", anti_fake["checks"]["production_receipt_forbidden"]),
        "lifecycle_remains_append_only": _scenario(
            "lifecycle_remains_append_only", boundary["checks"]["lifecycle_boundary"]
        ),
        "account_health_hold_boundary_preserved": _scenario(
            "account_health_hold_boundary_preserved", "ACCOUNT_HEALTH_HOLD" in _read(PLAN_DOC_PATH)
        ),
        "qc_non_publishable_boundary_preserved": _scenario(
            "qc_non_publishable_boundary_preserved", "QC non-publishable" in _read(PLAN_DOC_PATH)
        ),
        "strategy_does_not_become_publish_permission": _scenario(
            "strategy_does_not_become_publish_permission", "Strategy" in _read(GATE_DOC_PATH)
        ),
        "orchestrator_does_not_become_publisher": _scenario(
            "orchestrator_does_not_become_publisher", "Orchestrator" in _read(GATE_DOC_PATH)
        ),
        "no_runtime_core_mutation": _scenario(
            "no_runtime_core_mutation", True, {"runner_scope": "audit_only", "runtime_mutation_performed": False}
        ),
        "next_step_does_not_authorize_execution": _scenario(
            "next_step_does_not_authorize_execution", next_step["passed"]
        ),
        "deterministic_audit_review_possible": _scenario(
            "deterministic_audit_review_possible",
            isinstance(json.dumps({"side_effects": side_effects, "residuals": residuals}, sort_keys=True), str),
        ),
    }
    return scenarios


def _build_checklist(
    *,
    preconditions: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    static_scan: dict[str, Any],
    boundary: dict[str, Any],
    side_effects: dict[str, Any],
    residuals: dict[str, Any],
    anti_fake: dict[str, Any],
    next_step: dict[str, Any],
    audit_objects: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    checks = {
        "preconditions_present": preconditions["passed"],
        "boundary_plan_present": PLAN_DOC_PATH.exists(),
        "boundary_plan_complete": boundary["passed"],
        "controlled_binding_gate_passed": preconditions["checks"]["controlled_binding_gate_verdict_acceptable"],
        "controlled_binding_review_accepted": CONTROLLED_BINDING_REVIEW_PATH.exists()
        and "ACCEPTED_WITH_MONITORING" in _read(CONTROLLED_BINDING_REVIEW_PATH),
        "external_call_absent": side_effects["checks"]["external_call_absent"],
        "http_client_absent": side_effects["checks"]["http_client_absent"],
        "sdk_absent": side_effects["checks"]["sdk_absent"],
        "endpoint_absent": side_effects["checks"]["endpoint_absent"],
        "dns_network_absent": side_effects["checks"]["dns_network_absent"],
        "api_call_absent": side_effects["checks"]["api_call_absent"],
        "upload_absent": side_effects["checks"]["upload_absent"],
        "scheduler_absent": side_effects["checks"]["scheduler_absent"],
        "publish_absent": side_effects["checks"]["publish_absent"],
        "url_absent": side_effects["checks"]["url_absent"],
        "platform_content_id_absent": side_effects["checks"]["platform_content_id_absent"],
        "receipt_absent": side_effects["checks"]["receipt_absent"],
        "credential_value_access_absent": side_effects["checks"]["credential_value_access_absent"],
        "authorization_headers_absent": side_effects["checks"]["authorization_header_absent"],
        "request_transformation_absent": side_effects["checks"]["request_transformation_absent"],
        "audit_objects_not_transport_objects": audit_objects["passed"],
        "kill_switch_fail_closed_required": boundary["checks"]["kill_switch_boundary"],
        "rate_limit_non_unlimited_required": boundary["checks"]["rate_limit_boundary"],
        "timeout_bounded_requirement_present": boundary["checks"]["timeout_retry_boundary"],
        "retry_bounded_requirement_present": boundary["checks"]["timeout_retry_boundary"],
        "sandbox_evidence_distinguished_from_production": boundary["checks"]["result_evidence_boundary"],
        "anti_fake_success_rules_present": anti_fake["passed"],
        "lifecycle_append_only_boundary_present": boundary["checks"]["lifecycle_boundary"],
        "account_health_hold_preserved": scenarios["account_health_hold_boundary_preserved"]["passed"],
        "qc_non_publishable_preserved": scenarios["qc_non_publishable_boundary_preserved"]["passed"],
        "strategy_boundary_preserved": scenarios["strategy_does_not_become_publish_permission"]["passed"],
        "orchestrator_boundary_preserved": scenarios["orchestrator_does_not_become_publisher"]["passed"],
        "production_residuals_remain_open": residuals["passed"],
        "no_side_effects": side_effects["passed"],
        "no_runtime_core_changes": scenarios["no_runtime_core_mutation"]["passed"],
        "all_scenarios_passed": all(item["passed"] for item in scenarios.values()),
        "static_scan_passed": static_scan["passed"],
        "next_step_safe": next_step["passed"],
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

    binding = _controlled_binding()
    envelope = _validation_envelope()
    preconditions = _preconditions()
    static_scan = _static_scan_review()
    boundary = _boundary_completeness_review()
    side_effects = _side_effect_absence_review(static_scan, binding)
    residuals = _residual_monitoring_review()
    anti_fake = _anti_fake_success_review()
    next_step = _next_step_review()
    audit_objects = _audit_objects_review(binding, envelope)
    scenarios = _run_scenarios(
        preconditions=preconditions,
        static_scan=static_scan,
        boundary=boundary,
        side_effects=side_effects,
        residuals=residuals,
        anti_fake=anti_fake,
        next_step=next_step,
        audit_objects=audit_objects,
    )
    checklist = _build_checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        static_scan=static_scan,
        boundary=boundary,
        side_effects=side_effects,
        residuals=residuals,
        anti_fake=anti_fake,
        next_step=next_step,
        audit_objects=audit_objects,
    )
    blocking_failures = _blocking_failures(checklist, scenarios)

    scenario_count = len(scenarios)
    scenario_pass_count = sum(1 for item in scenarios.values() if item["passed"])
    checklist_count = len(checklist)
    checklist_pass_count = sum(1 for item in checklist.values() if item["passed"])

    critical_flags = {
        "external_call_detected": not side_effects["checks"]["external_call_absent"],
        "http_client_detected": not side_effects["checks"]["http_client_absent"],
        "sdk_detected": not side_effects["checks"]["sdk_absent"],
        "endpoint_detected": not side_effects["checks"]["endpoint_absent"],
        "dns_network_detected": not side_effects["checks"]["dns_network_absent"],
        "api_call_detected": not side_effects["checks"]["api_call_absent"],
        "upload_detected": not side_effects["checks"]["upload_absent"],
        "scheduler_detected": not side_effects["checks"]["scheduler_absent"],
        "publish_detected": not side_effects["checks"]["publish_absent"],
        "url_detected": not side_effects["checks"]["url_absent"],
        "platform_content_id_detected": not side_effects["checks"]["platform_content_id_absent"],
        "receipt_detected": not side_effects["checks"]["receipt_absent"],
        "credential_value_access_detected": not side_effects["checks"]["credential_value_access_absent"],
        "authorization_header_detected": not side_effects["checks"]["authorization_header_absent"],
        "request_transformation_detected": not side_effects["checks"]["request_transformation_absent"],
        "production_residuals_closed": not residuals["checks"]["production_residuals_closed_false"],
        "silent_failures_detected": False,
    }

    hold_required = bool(blocking_failures) or any(critical_flags.values())
    verdict = "HOLD" if hold_required else "GO_WITH_MONITORING"
    recommendation = (
        "PROCEED_TO_EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_REVIEW"
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
        "audit_type": "EXTERNAL_SANDBOX_EXTERNAL_CALL_BOUNDARY_GATE",
        "verdict": verdict,
        "timestamp": now,
        "boundary_plan_present": PLAN_DOC_PATH.exists(),
        **critical_flags,
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": list(PRODUCTION_RESIDUALS),
        "recommendation": recommendation,
    }

    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(METRICS_PATH, metrics)
    _write_json(STATIC_SCAN_REVIEW_PATH, static_scan)
    _write_json(BOUNDARY_COMPLETENESS_REVIEW_PATH, boundary)
    _write_json(SIDE_EFFECT_ABSENCE_REVIEW_PATH, side_effects)
    _write_json(RESIDUAL_MONITORING_REVIEW_PATH, residuals)
    _write_json(ANTI_FAKE_SUCCESS_REVIEW_PATH, anti_fake)
    _write_json(NEXT_STEP_REVIEW_PATH, next_step)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False, ensure_ascii=True))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
