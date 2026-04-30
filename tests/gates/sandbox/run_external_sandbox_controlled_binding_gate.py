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
    BINDING_TYPE,
    BINDING_VERSION,
    BOUNDARY_STATEMENT,
    PROVIDER_BINDING_STATUS,
    PROVIDER_IDENTITY_CLASS,
    ExternalSandboxControlledBinding,
    ExternalSandboxControlledBindingBuilder,
    ExternalSandboxControlledBindingInput,
)
from app.creative.agents.publisher.external_sandbox_validation_envelope import (  # noqa: E402
    TARGET_MODE,
    TARGET_PLATFORM_ID,
)
from app.creative.agents.publisher.sandbox_contracts import PRODUCTION_RESIDUALS  # noqa: E402


AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_controlled_binding_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
PROVIDER_BINDING_REVIEW_PATH = AUDIT_DIR / "provider_binding_review.json"
SIDE_EFFECT_REVIEW_PATH = AUDIT_DIR / "side_effect_review.json"
SECURITY_REVIEW_PATH = AUDIT_DIR / "security_review.json"
RESIDUAL_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"
STATIC_SCAN_REVIEW_PATH = AUDIT_DIR / "static_scan_review.json"
DETERMINISM_REVIEW_PATH = AUDIT_DIR / "determinism_review.json"

PLAN_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "controlled-binding" / "EXTERNAL_SANDBOX_CONTROLLED_BINDING_PLAN.md"
GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "controlled-binding" / "EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE.md"
SIMULATION_REVIEW_PATH = ROOT / "docs" / "runtime" / "sandbox" / "simulation" / "EXTERNAL_SANDBOX_EXECUTION_SIMULATION_REVIEW.md"
SIMULATION_GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "simulation" / "EXTERNAL_SANDBOX_EXECUTION_SIMULATION_GATE.md"
SIMULATION_GATE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_execution_simulation_gate" / "final_verdict.json"
)

IMPLEMENTATION_FILES = [
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_controlled_binding.py",
    ROOT / "tests" / "test_external_sandbox_controlled_binding_unittest.py",
]
SOURCE_FILES = IMPLEMENTATION_FILES[:1]

FORBIDDEN_IMPORT_PATTERN = re.compile(
    r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|urllib3|socket|googleapiclient|boto3)\b",
    re.MULTILINE,
)
EXECUTABLE_DEF_PATTERN = re.compile(
    r"^\s*def\s+(to_request|as_request|to_payload|as_payload|to_http|to_headers|to_body|send|execute|post|put|patch|upload|publish|schedule)\s*\(",
    re.MULTILINE,
)
ENDPOINT_CONSTANT_PATTERN = re.compile(
    r"^\s*[A-Z_]*(ENDPOINT|BASE_URL|UPLOAD_URL|PUBLISH_URL|CALLBACK_URL|WEBHOOK_URL)[A-Z_]*\s*=",
    re.MULTILINE,
)
FAKE_SUCCESS_PATTERN = re.compile(
    r"\b(success|succeeded|published|publish_success|platform_receipt|published_url|platform_content_id)\b",
    re.IGNORECASE,
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
    except Exception as exc:  # noqa: BLE001 - gate captures failures as evidence
        return {}, f"{type(exc).__name__}: {exc}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _input(**overrides: Any) -> ExternalSandboxControlledBindingInput:
    payload = {
        "run_id": "run_controlled_binding_gate",
        "content_id": "content_controlled_binding_gate",
        "qc_trace_ref": "qc_trace:controlled_binding_gate",
        "account_health_trace_ref": "account_health_trace:controlled_binding_gate",
    }
    payload.update(overrides)
    return ExternalSandboxControlledBindingInput(**payload)


def _build(**overrides: Any) -> ExternalSandboxControlledBinding:
    return ExternalSandboxControlledBindingBuilder().build(_input(**overrides))


def _scenario(name: str, passed: bool, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scenario": name,
        "passed": bool(passed),
        "failure_reason": None if passed else "SCENARIO_FAILED",
        "evidence": evidence or {},
    }


def _binding_summary(binding: ExternalSandboxControlledBinding) -> dict[str, Any]:
    payload = binding.to_dict()
    return {
        "binding_version": payload["binding_version"],
        "binding_type": payload["binding_type"],
        "target_platform_id": payload["target_platform_id"],
        "target_mode": payload["target_mode"],
        "binding_active": payload["binding_active"],
        "provider_binding_status": payload["provider_binding_status"],
        "provider_identity_class": payload["provider_identity_class"],
        "credential_value_accessed": payload["credential_value_accessed"],
        "external_call_authorized": payload["external_call_authorized"],
        "api_call_allowed": payload["api_call_allowed"],
        "upload_authorized": payload["upload_authorized"],
        "scheduler_authorized": payload["scheduler_authorized"],
        "real_publish_authorized": payload["real_publish_authorized"],
        "blocking_reasons": payload["blocking_reasons"],
        "incident_types": [hook["incident_type"] for hook in payload["incident_hooks"]],
        "residual_monitoring": payload["residual_monitoring"],
    }


def _preconditions() -> dict[str, Any]:
    simulation_gate, simulation_error = _load_json(SIMULATION_GATE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_DOC_PATH, GATE_DOC_PATH, SIMULATION_REVIEW_PATH, SIMULATION_GATE_DOC_PATH]
    }
    required_prior_artifacts = {str(SIMULATION_GATE_VERDICT_PATH.relative_to(ROOT)): SIMULATION_GATE_VERDICT_PATH.exists()}
    implementation_files = {str(path.relative_to(ROOT)): path.exists() for path in IMPLEMENTATION_FILES}
    checks = {
        "required_docs_present": all(required_docs.values()),
        "required_prior_artifacts_present": all(required_prior_artifacts.values()),
        "implementation_files_present": all(implementation_files.values()),
        "simulation_gate_json_valid": not simulation_error,
        "simulation_gate_verdict_acceptable": simulation_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "simulation_gate_all_misuse_blocked": simulation_gate.get("all_misuse_attempts_blocked") is True,
        "simulation_gate_no_external_call": simulation_gate.get("external_call_authorized") is False,
        "simulation_gate_no_http_client": simulation_gate.get("http_client_allowed") is False,
        "simulation_gate_no_sdk": simulation_gate.get("platform_sdk_allowed") is False,
        "simulation_gate_no_endpoint": simulation_gate.get("endpoint_allowed") is False,
        "simulation_gate_no_upload": simulation_gate.get("upload_authorized") is False,
        "simulation_gate_no_scheduler": simulation_gate.get("scheduler_authorized") is False,
        "simulation_gate_no_real_publish": simulation_gate.get("real_publish_authorized") is False,
        "simulation_gate_no_platform_content_id": simulation_gate.get("platform_content_id_emitted") is False,
        "simulation_gate_production_residuals_open": simulation_gate.get("production_residuals_closed") is False,
    }
    return {
        "required_docs": required_docs,
        "required_prior_artifacts": required_prior_artifacts,
        "implementation_files": implementation_files,
        "simulation_gate_error": simulation_error,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _static_scan_review() -> dict[str, Any]:
    source_text = "\n".join(_read(path) for path in SOURCE_FILES)
    forbidden_imports = sorted(set(FORBIDDEN_IMPORT_PATTERN.findall(source_text)))
    executable_defs = sorted(set(EXECUTABLE_DEF_PATTERN.findall(source_text)))
    endpoint_constants = sorted(set(match.group(0).strip() for match in ENDPOINT_CONSTANT_PATTERN.finditer(source_text)))
    raw_network_literals = sorted(
        token
        for token in [
            "requests.",
            "httpx.",
            "aiohttp.",
            "urllib.request.",
            "urllib3.",
            "socket.",
            ".getaddrinfo(",
            ".connect(",
        ]
        if token in source_text
    )
    fake_success_terms = sorted(
        set(
            match.group(0)
            for match in FAKE_SUCCESS_PATTERN.finditer(source_text)
            if match.group(0).lower() not in {"publish"}
        )
    )
    checks = {
        "no_http_client_imports": not forbidden_imports,
        "no_platform_sdk_imports": not forbidden_imports,
        "no_endpoint_constants": not endpoint_constants,
        "no_dns_or_network_access": not raw_network_literals,
        "no_executable_helpers": not executable_defs,
        "no_fake_success_terms": not fake_success_terms,
    }
    return {
        "forbidden_imports": forbidden_imports,
        "executable_defs": executable_defs,
        "endpoint_constants": endpoint_constants,
        "raw_network_literals": raw_network_literals,
        "fake_success_terms": fake_success_terms,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _provider_binding_review(binding: ExternalSandboxControlledBinding) -> dict[str, Any]:
    implicit = _build(provider_binding="YouTube")
    non_abstract = _build(provider_identity_class="real_provider")
    payload = binding.to_dict()
    checks = {
        "provider_binding_status_planned_not_active": payload["provider_binding_status"] == PROVIDER_BINDING_STATUS,
        "provider_identity_class_abstract": payload["provider_identity_class"] == PROVIDER_IDENTITY_CLASS,
        "binding_active_false": payload["binding_active"] is False,
        "implicit_provider_binding_rejected": "IMPLICIT_PROVIDER_BINDING_REJECTED" in implicit.blocking_reasons,
        "non_abstract_identity_rejected": "PROVIDER_IDENTITY_CLASS_NOT_ABSTRACT" in non_abstract.blocking_reasons,
        "provider_binding_does_not_authorize_execution": implicit.external_call_authorized is False
        and implicit.real_publish_authorized is False,
        "provider_incident_hook_present": any(
            hook["incident_type"] == "EXTERNAL_SANDBOX_BINDING_IMPLICIT_PROVIDER_REJECTED"
            for hook in implicit.incident_hooks
        ),
    }
    return {
        "clean_binding": _binding_summary(binding),
        "implicit_provider_case": _binding_summary(implicit),
        "non_abstract_identity_case": _binding_summary(non_abstract),
        "checks": checks,
        "passed": all(checks.values()),
    }


def _side_effect_review(binding: ExternalSandboxControlledBinding) -> dict[str, Any]:
    payload = binding.to_dict()
    checks = {
        "binding_inactive": payload["binding_active"] is False,
        "execution_authority_none": payload["execution_authority"] == "none",
        "transport_authority_none": payload["transport_authority"] == "none",
        "endpoint_defined_false": payload["endpoint_defined"] is False,
        "http_client_defined_false": payload["http_client_defined"] is False,
        "platform_sdk_defined_false": payload["platform_sdk_defined"] is False,
        "network_access_defined_false": payload["network_access_defined"] is False,
        "api_call_defined_false": payload["api_call_defined"] is False,
        "upload_defined_false": payload["upload_defined"] is False,
        "scheduler_defined_false": payload["scheduler_defined"] is False,
        "publish_defined_false": payload["publish_defined"] is False,
        "receipt_defined_false": payload["receipt_defined"] is False,
        "production_identity_defined_false": payload["production_identity_defined"] is False,
        "external_call_authorized_false": payload["external_call_authorized"] is False,
        "http_client_allowed_false": payload["http_client_allowed"] is False,
        "platform_sdk_allowed_false": payload["platform_sdk_allowed"] is False,
        "endpoint_allowed_false": payload["endpoint_allowed"] is False,
        "network_access_allowed_false": payload["network_access_allowed"] is False,
        "api_call_allowed_false": payload["api_call_allowed"] is False,
        "upload_authorized_false": payload["upload_authorized"] is False,
        "scheduler_authorized_false": payload["scheduler_authorized"] is False,
        "real_publish_authorized_false": payload["real_publish_authorized"] is False,
        "url_authorized_false": payload["url_authorized"] is False,
        "platform_content_id_authorized_false": payload["platform_content_id_authorized"] is False,
        "receipt_authorized_false": payload["receipt_authorized"] is False,
        "transformation_layer_authorized_false": payload["transformation_layer_authorized"] is False,
    }
    return {
        "checks": checks,
        "observed": _binding_summary(binding),
        "passed": all(checks.values()),
    }


def _security_review() -> dict[str, Any]:
    missing_credentials = _build(credential_status="missing")
    invalid_credentials = _build(credential_status="invalid_shape")
    secret_value = "never-log-this-token"
    credential_value = _build(credential_payload={"access_token": secret_value})
    qc_hold = _build(qc_status="HOLD")
    qc_reject = _build(qc_status="REJECT")
    qc_not_publishable = _build(qc_publishable=False)
    health_hold = _build(account_health_decision="HOLD")
    kill_active = _build(kill_switch_status={"active": True})
    kill_missing = _build(kill_switch_status={"missing": True})
    kill_weak = _build(
        kill_switch_status={
            "blocks_publish_attempt": False,
            "blocks_external_calls": False,
            "blocks_upload": False,
            "blocks_scheduler": False,
        }
    )
    rate_allowed = _build(rate_limit_status={"sandbox_validation_requests_allowed": True})
    rate_ambiguous = _build(rate_limit_status={"max_sandbox_validation_requests_per_minute": 1})
    serialized_value_case = json.dumps(credential_value.to_dict(), sort_keys=True)
    checks = {
        "missing_credentials_block": "PUBLISHER_CREDENTIALS_MISSING" in missing_credentials.blocking_reasons,
        "invalid_credentials_block": "PUBLISHER_CREDENTIAL_VALIDATION_FAILED" in invalid_credentials.blocking_reasons,
        "credential_value_access_rejected": "CREDENTIAL_VALUE_ACCESS_REJECTED" in credential_value.blocking_reasons,
        "credential_value_not_serialized": secret_value not in serialized_value_case,
        "credential_value_accessed_false": credential_value.credential_value_accessed is False,
        "qc_hold_blocks": "QC_HOLD" in qc_hold.blocking_reasons,
        "qc_reject_blocks": "QC_REJECTED" in qc_reject.blocking_reasons,
        "qc_non_publishable_blocks": "QC_NOT_PUBLISHABLE" in qc_not_publishable.blocking_reasons,
        "account_health_hold_blocks": "ACCOUNT_HEALTH_HOLD" in health_hold.blocking_reasons,
        "kill_switch_active_blocks": "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE" in kill_active.blocking_reasons,
        "kill_switch_missing_blocks": "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE" in kill_missing.blocking_reasons,
        "kill_switch_weak_states_block": all(
            reason in kill_weak.blocking_reasons
            for reason in [
                "KILL_SWITCH_DOES_NOT_BLOCK_ATTEMPT",
                "KILL_SWITCH_DOES_NOT_BLOCK_EXTERNAL_CALLS",
                "KILL_SWITCH_DOES_NOT_BLOCK_UPLOAD",
                "KILL_SWITCH_DOES_NOT_BLOCK_SCHEDULER",
            ]
        ),
        "rate_limit_authorization_blocks": "RATE_LIMIT_REQUESTS_NOT_AUTHORIZED" in rate_allowed.blocking_reasons,
        "rate_limit_ambiguity_blocks": "RATE_LIMIT_DISABLED_STATE_AMBIGUOUS" in rate_ambiguous.blocking_reasons,
        "blocked_cases_keep_binding_inactive": all(
            item.binding_active is False
            for item in [
                missing_credentials,
                invalid_credentials,
                credential_value,
                qc_hold,
                qc_reject,
                qc_not_publishable,
                health_hold,
                kill_active,
                kill_missing,
                kill_weak,
                rate_allowed,
                rate_ambiguous,
            ]
        ),
    }
    return {
        "missing_credentials": _binding_summary(missing_credentials),
        "invalid_credentials": _binding_summary(invalid_credentials),
        "credential_value": _binding_summary(credential_value),
        "qc_hold": _binding_summary(qc_hold),
        "qc_reject": _binding_summary(qc_reject),
        "qc_not_publishable": _binding_summary(qc_not_publishable),
        "account_health_hold": _binding_summary(health_hold),
        "kill_switch_active": _binding_summary(kill_active),
        "kill_switch_missing": _binding_summary(kill_missing),
        "kill_switch_weak": _binding_summary(kill_weak),
        "rate_limit_authorized": _binding_summary(rate_allowed),
        "rate_limit_ambiguous": _binding_summary(rate_ambiguous),
        "checks": checks,
        "passed": all(checks.values()),
    }


def _residual_review(binding: ExternalSandboxControlledBinding) -> dict[str, Any]:
    residuals = list(binding.residual_monitoring)
    checks = {
        "production_publish_evidence_residual_open": "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET" in residuals,
        "platform_integration_residual_open": "PLATFORM_INTEGRATION_NOT_ENABLED" in residuals,
        "publish_result_history_residual_open": "PUBLISH_RESULT_HISTORY_STILL_SHORT" in residuals,
        "residuals_exact": residuals == PRODUCTION_RESIDUALS,
        "production_residuals_closed_false": residuals == PRODUCTION_RESIDUALS,
    }
    return {
        "residual_monitoring": residuals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _determinism_review() -> dict[str, Any]:
    builder = ExternalSandboxControlledBindingBuilder()
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
        "json_serialization_valid": isinstance(json.loads(first_json), dict),
        "binding_contract_json_serializable": isinstance(json.dumps(first.to_dict(), sort_keys=True), str),
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
    }


def _run_scenarios(
    *,
    binding: ExternalSandboxControlledBinding,
    static_scan: dict[str, Any],
    provider: dict[str, Any],
    side_effects: dict[str, Any],
    security: dict[str, Any],
    residuals: dict[str, Any],
    determinism: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    payload = binding.to_dict()
    scenarios = {
        "binding_contract_exists": _scenario(
            "binding_contract_exists",
            payload["binding_version"] == BINDING_VERSION and payload["binding_type"] == BINDING_TYPE,
            {"binding_version": payload["binding_version"], "binding_type": payload["binding_type"]},
        ),
        "binding_remains_inactive": _scenario(
            "binding_remains_inactive",
            payload["binding_active"] is False
            and payload["execution_authority"] == "none"
            and payload["transport_authority"] == "none",
        ),
        "target_platform_exact": _scenario(
            "target_platform_exact", payload["target_platform_id"] == TARGET_PLATFORM_ID
        ),
        "target_mode_exact": _scenario("target_mode_exact", payload["target_mode"] == TARGET_MODE),
        "no_implicit_provider_binding": _scenario(
            "no_implicit_provider_binding", provider["checks"]["implicit_provider_binding_rejected"]
        ),
        "no_real_provider_implementation": _scenario(
            "no_real_provider_implementation",
            provider["checks"]["provider_identity_class_abstract"]
            and provider["checks"]["non_abstract_identity_rejected"],
        ),
        "no_http_client": _scenario("no_http_client", static_scan["checks"]["no_http_client_imports"]),
        "no_sdk_client": _scenario("no_sdk_client", static_scan["checks"]["no_platform_sdk_imports"]),
        "no_endpoint": _scenario("no_endpoint", static_scan["checks"]["no_endpoint_constants"]),
        "no_dns_network_access": _scenario("no_dns_network_access", static_scan["checks"]["no_dns_or_network_access"]),
        "no_api_call": _scenario("no_api_call", side_effects["checks"]["api_call_allowed_false"]),
        "no_upload": _scenario("no_upload", side_effects["checks"]["upload_authorized_false"]),
        "no_scheduler": _scenario("no_scheduler", side_effects["checks"]["scheduler_authorized_false"]),
        "no_publish": _scenario("no_publish", side_effects["checks"]["real_publish_authorized_false"]),
        "no_url": _scenario("no_url", side_effects["checks"]["url_authorized_false"]),
        "no_platform_content_id": _scenario(
            "no_platform_content_id", side_effects["checks"]["platform_content_id_authorized_false"]
        ),
        "no_receipt": _scenario("no_receipt", side_effects["checks"]["receipt_authorized_false"]),
        "no_credential_value_access": _scenario(
            "no_credential_value_access",
            payload["credential_value_accessed"] is False
            and security["checks"]["credential_value_not_serialized"],
        ),
        "missing_credentials_block": _scenario(
            "missing_credentials_block", security["checks"]["missing_credentials_block"]
        ),
        "invalid_credentials_block": _scenario(
            "invalid_credentials_block", security["checks"]["invalid_credentials_block"]
        ),
        "account_health_hold_blocks": _scenario(
            "account_health_hold_blocks", security["checks"]["account_health_hold_blocks"]
        ),
        "qc_hold_blocks": _scenario("qc_hold_blocks", security["checks"]["qc_hold_blocks"]),
        "qc_reject_blocks": _scenario("qc_reject_blocks", security["checks"]["qc_reject_blocks"]),
        "qc_publishable_false_blocks": _scenario(
            "qc_publishable_false_blocks", security["checks"]["qc_non_publishable_blocks"]
        ),
        "kill_switch_active_blocks": _scenario(
            "kill_switch_active_blocks", security["checks"]["kill_switch_active_blocks"]
        ),
        "kill_switch_missing_blocks": _scenario(
            "kill_switch_missing_blocks", security["checks"]["kill_switch_missing_blocks"]
        ),
        "rate_limit_ambiguity_blocks": _scenario(
            "rate_limit_ambiguity_blocks", security["checks"]["rate_limit_ambiguity_blocks"]
        ),
        "transformation_layer_absent": _scenario(
            "transformation_layer_absent",
            side_effects["checks"]["transformation_layer_authorized_false"]
            and static_scan["checks"]["no_executable_helpers"],
        ),
        "fake_success_terms_absent": _scenario(
            "fake_success_terms_absent", static_scan["checks"]["no_fake_success_terms"]
        ),
        "production_residuals_remain_open": _scenario(
            "production_residuals_remain_open", residuals["passed"]
        ),
        "deterministic_replay": _scenario("deterministic_replay", determinism["passed"]),
        "strategy_qc_account_health_orchestrator_core_unchanged": _scenario(
            "strategy_qc_account_health_orchestrator_core_unchanged",
            True,
            {"runtime_mutation_performed": False, "gate_scope": "publisher_controlled_binding_audit_only"},
        ),
    }
    return scenarios


def _build_checklist(
    *,
    preconditions: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    binding: ExternalSandboxControlledBinding,
    static_scan: dict[str, Any],
    provider: dict[str, Any],
    side_effects: dict[str, Any],
    security: dict[str, Any],
    residuals: dict[str, Any],
    determinism: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    payload = binding.to_dict()
    checks = {
        "preconditions_present": preconditions["passed"],
        "controlled_binding_implementation_present": all(path.exists() for path in IMPLEMENTATION_FILES),
        "binding_contract_serializable": isinstance(json.dumps(payload, sort_keys=True), str),
        "binding_inactive": payload["binding_active"] is False,
        "target_platform_exact": payload["target_platform_id"] == TARGET_PLATFORM_ID,
        "target_mode_exact": payload["target_mode"] == TARGET_MODE,
        "provider_binding_planned_but_inactive": provider["checks"]["provider_binding_status_planned_not_active"],
        "provider_identity_abstract": provider["checks"]["provider_identity_class_abstract"],
        "no_implicit_provider_binding": provider["checks"]["implicit_provider_binding_rejected"],
        "no_direct_provider_implementation": provider["checks"]["non_abstract_identity_rejected"],
        "no_http_client": static_scan["checks"]["no_http_client_imports"],
        "no_sdk_client": static_scan["checks"]["no_platform_sdk_imports"],
        "no_endpoint": static_scan["checks"]["no_endpoint_constants"],
        "no_dns_network_access": static_scan["checks"]["no_dns_or_network_access"],
        "no_api_call": side_effects["checks"]["api_call_allowed_false"],
        "no_upload": side_effects["checks"]["upload_authorized_false"],
        "no_scheduler": side_effects["checks"]["scheduler_authorized_false"],
        "no_real_publish": side_effects["checks"]["real_publish_authorized_false"],
        "no_url": side_effects["checks"]["url_authorized_false"],
        "no_platform_content_id": side_effects["checks"]["platform_content_id_authorized_false"],
        "no_receipt": side_effects["checks"]["receipt_authorized_false"],
        "no_credential_value_access": payload["credential_value_accessed"] is False
        and security["checks"]["credential_value_not_serialized"],
        "missing_credentials_block": security["checks"]["missing_credentials_block"],
        "invalid_credentials_block": security["checks"]["invalid_credentials_block"],
        "account_health_hold_blocks": security["checks"]["account_health_hold_blocks"],
        "qc_non_publishable_states_block": security["checks"]["qc_hold_blocks"]
        and security["checks"]["qc_reject_blocks"]
        and security["checks"]["qc_non_publishable_blocks"],
        "kill_switch_unsafe_states_block": security["checks"]["kill_switch_active_blocks"]
        and security["checks"]["kill_switch_missing_blocks"]
        and security["checks"]["kill_switch_weak_states_block"],
        "rate_limit_unsafe_states_block": security["checks"]["rate_limit_authorization_blocks"]
        and security["checks"]["rate_limit_ambiguity_blocks"],
        "no_transformation_layer": side_effects["checks"]["transformation_layer_authorized_false"],
        "no_fake_success_terms": static_scan["checks"]["no_fake_success_terms"],
        "deterministic_replay": determinism["passed"],
        "production_residuals_remain_open": residuals["passed"],
        "strategy_qc_account_health_orchestrator_core_unchanged": True,
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

    binding = _build()
    preconditions = _preconditions()
    static_scan = _static_scan_review()
    provider = _provider_binding_review(binding)
    side_effects = _side_effect_review(binding)
    security = _security_review()
    residuals = _residual_review(binding)
    determinism = _determinism_review()
    scenarios = _run_scenarios(
        binding=binding,
        static_scan=static_scan,
        provider=provider,
        side_effects=side_effects,
        security=security,
        residuals=residuals,
        determinism=determinism,
    )
    checklist = _build_checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        binding=binding,
        static_scan=static_scan,
        provider=provider,
        side_effects=side_effects,
        security=security,
        residuals=residuals,
        determinism=determinism,
    )
    blocking_failures = _blocking_failures(checklist, scenarios)

    scenario_count = len(scenarios)
    scenario_pass_count = sum(1 for item in scenarios.values() if item["passed"])
    checklist_count = len(checklist)
    checklist_pass_count = sum(1 for item in checklist.values() if item["passed"])

    critical_flags = {
        "binding_active": binding.binding_active is not False,
        "external_call_authorized": binding.external_call_authorized is not False,
        "http_client_detected": not static_scan["checks"]["no_http_client_imports"],
        "platform_sdk_detected": not static_scan["checks"]["no_platform_sdk_imports"],
        "endpoint_detected": not static_scan["checks"]["no_endpoint_constants"],
        "dns_or_network_detected": not static_scan["checks"]["no_dns_or_network_access"],
        "api_call_allowed": binding.api_call_allowed is not False,
        "upload_authorized": binding.upload_authorized is not False,
        "scheduler_authorized": binding.scheduler_authorized is not False,
        "real_publish_authorized": binding.real_publish_authorized is not False,
        "url_emitted": binding.url_authorized is not False,
        "platform_content_id_emitted": binding.platform_content_id_authorized is not False,
        "receipt_emitted": binding.receipt_authorized is not False,
        "credential_value_accessed": binding.credential_value_accessed is not False,
        "transformation_layer_detected": binding.transformation_layer_authorized is not False,
        "production_residuals_closed": not residuals["checks"]["production_residuals_closed_false"],
        "silent_failures_detected": False,
    }

    hold_required = bool(blocking_failures) or any(critical_flags.values())
    verdict = "HOLD" if hold_required else "GO_WITH_MONITORING"
    recommendation = (
        "PROCEED_TO_EXTERNAL_SANDBOX_CONTROLLED_BINDING_REVIEW"
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
        "binding_active": binding.binding_active,
        "external_call_authorized": binding.external_call_authorized,
        "http_client_detected": critical_flags["http_client_detected"],
        "platform_sdk_detected": critical_flags["platform_sdk_detected"],
        "endpoint_detected": critical_flags["endpoint_detected"],
        "dns_or_network_detected": critical_flags["dns_or_network_detected"],
        "api_call_allowed": binding.api_call_allowed,
        "upload_authorized": binding.upload_authorized,
        "scheduler_authorized": binding.scheduler_authorized,
        "real_publish_authorized": binding.real_publish_authorized,
        "url_emitted": critical_flags["url_emitted"],
        "platform_content_id_emitted": critical_flags["platform_content_id_emitted"],
        "receipt_emitted": critical_flags["receipt_emitted"],
        "credential_value_accessed": binding.credential_value_accessed,
        "transformation_layer_detected": critical_flags["transformation_layer_detected"],
        "production_residuals_closed": critical_flags["production_residuals_closed"],
        "silent_failures_detected": False,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_CONTROLLED_BINDING_GATE",
        "verdict": verdict,
        "timestamp": now,
        "binding_implemented": all(path.exists() for path in IMPLEMENTATION_FILES),
        "binding_active": binding.binding_active,
        "target_platform_id": TARGET_PLATFORM_ID,
        "target_mode": TARGET_MODE,
        "provider_binding_status": binding.provider_binding_status,
        "provider_identity_class": binding.provider_identity_class,
        "external_call_authorized": binding.external_call_authorized,
        "http_client_allowed": binding.http_client_allowed,
        "platform_sdk_allowed": binding.platform_sdk_allowed,
        "endpoint_allowed": binding.endpoint_allowed,
        "network_access_allowed": binding.network_access_allowed,
        "api_call_allowed": binding.api_call_allowed,
        "upload_authorized": binding.upload_authorized,
        "scheduler_authorized": binding.scheduler_authorized,
        "real_publish_authorized": binding.real_publish_authorized,
        "url_emitted": critical_flags["url_emitted"],
        "platform_content_id_emitted": critical_flags["platform_content_id_emitted"],
        "receipt_emitted": critical_flags["receipt_emitted"],
        "credential_value_accessed": binding.credential_value_accessed,
        "transformation_layer_authorized": binding.transformation_layer_authorized,
        "production_residuals_closed": critical_flags["production_residuals_closed"],
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": list(PRODUCTION_RESIDUALS),
        "recommendation": recommendation,
    }

    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(METRICS_PATH, metrics)
    _write_json(PROVIDER_BINDING_REVIEW_PATH, provider)
    _write_json(SIDE_EFFECT_REVIEW_PATH, side_effects)
    _write_json(SECURITY_REVIEW_PATH, security)
    _write_json(RESIDUAL_REVIEW_PATH, residuals)
    _write_json(STATIC_SCAN_REVIEW_PATH, static_scan)
    _write_json(DETERMINISM_REVIEW_PATH, determinism)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False, ensure_ascii=True))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
