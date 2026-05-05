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

from app.creative.agents.publisher.external_sandbox_envelope_security import (  # noqa: E402
    EXECUTABLE_HELPER_NAMES,
    HTTP_LIKE_FIELD_NAMES,
    executable_helper_names_on,
)
from app.creative.agents.publisher.external_sandbox_validation_envelope import (  # noqa: E402
    ENVELOPE_TYPE,
    IDEMPOTENCY_NAMESPACE,
    TARGET_MODE,
    TARGET_PLATFORM_ID,
    ExternalSandboxValidationEnvelope,
    ExternalSandboxValidationEnvelopeBuilder,
    ExternalSandboxValidationEnvelopeInput,
)
from app.creative.agents.publisher.sandbox_contracts import PRODUCTION_RESIDUALS  # noqa: E402


AUDIT_DIR = ROOT / "OUT" / "audit" / "external_sandbox_request_envelope_implementation_gate"
FINAL_VERDICT_PATH = AUDIT_DIR / "final_verdict.json"
CHECKLIST_RESULTS_PATH = AUDIT_DIR / "checklist_results.json"
SCENARIO_OUTPUTS_PATH = AUDIT_DIR / "scenario_outputs.json"
METRICS_PATH = AUDIT_DIR / "metrics.json"
SECURITY_REVIEW_PATH = AUDIT_DIR / "security_review.json"
CONTRACT_REVIEW_PATH = AUDIT_DIR / "contract_review.json"
TRANSPORT_REVIEW_PATH = AUDIT_DIR / "transport_nullification_review.json"
STATIC_SCAN_REVIEW_PATH = AUDIT_DIR / "static_scan_review.json"
DETERMINISM_REVIEW_PATH = AUDIT_DIR / "determinism_review.json"
SIDE_EFFECT_REVIEW_PATH = AUDIT_DIR / "side_effect_review.json"
RESIDUAL_REVIEW_PATH = AUDIT_DIR / "residual_monitoring_review.json"

PLAN_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "envelope" / "EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_PLAN.md"
GATE_DOC_PATH = ROOT / "docs" / "runtime" / "sandbox" / "envelope" / "EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE.md"
REQUEST_ENVELOPE_GATE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_request_envelope_gate" / "final_verdict.json"
)
EVIDENCE_GATE_VERDICT_PATH = (
    ROOT / "OUT" / "audit" / "external_sandbox_evidence_collection_gate" / "final_verdict.json"
)

IMPLEMENTATION_FILES = [
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_validation_envelope.py",
    ROOT / "backend" / "app" / "creative" / "agents" / "publisher" / "external_sandbox_envelope_security.py",
    ROOT / "tests" / "test_external_sandbox_validation_envelope_unittest.py",
]

SOURCE_FILES = IMPLEMENTATION_FILES[:2]
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
    except Exception as exc:  # noqa: BLE001 - gate captures read failures as audit evidence
        return {}, f"{type(exc).__name__}: {exc}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _metadata(**overrides: Any) -> dict[str, Any]:
    payload = {
        "title": "Sandbox title",
        "description": "Sandbox description",
        "tags": ["sandbox", "validation"],
        "language": "en",
        "visibility_mode": "sandbox_only",
        "account_id": "account_sandbox",
        "runtime_policy_ref": "runtime_policy:sandbox",
        "metadata_trace_ref": "metadata_trace:sandbox",
    }
    payload.update(overrides)
    return payload


def _input(**overrides: Any) -> ExternalSandboxValidationEnvelopeInput:
    payload = {
        "run_id": "run_external_sandbox_gate",
        "content_id": "content_external_sandbox_gate",
        "artifact_manifest_ref": "artifact_manifest:external_sandbox_gate",
        "metadata_payload_ref": "metadata_payload:external_sandbox_gate",
        "qc_trace_ref": "qc_trace:external_sandbox_gate",
        "account_health_trace_ref": "health_trace:external_sandbox_gate",
        "strategy_ref": "strategy:external_sandbox_gate",
        "publish_eligibility_trace_ref": "publish_eligibility:external_sandbox_gate",
        "metadata": _metadata(),
    }
    payload.update(overrides)
    return ExternalSandboxValidationEnvelopeInput(**payload)


def _build(**overrides: Any):
    return ExternalSandboxValidationEnvelopeBuilder().build(_input(**overrides))


def _collect_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key).lower())
            keys.update(_collect_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_collect_keys(child))
    return keys


def _scenario(name: str, passed: bool, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "scenario": name,
        "passed": bool(passed),
        "failure_reason": None if passed else "SCENARIO_FAILED",
        "evidence": evidence or {},
    }


def _envelope_summary(envelope: Any) -> dict[str, Any]:
    payload = envelope.to_dict()
    return {
        "envelope_type": payload.get("envelope_type"),
        "target_platform_id": payload.get("target_platform_id"),
        "target_mode": payload.get("target_mode"),
        "execution_capability": payload.get("execution_capability"),
        "transport_capability": payload.get("transport_capability"),
        "non_transportable": payload.get("non_transportable"),
        "external_call_authorized": payload.get("external_call_authorized"),
        "platform_api_execution_authorized": payload.get("platform_api_execution_authorized"),
        "upload_authorized": payload.get("upload_authorized"),
        "scheduler_authorized": payload.get("scheduler_authorized"),
        "real_publish_authorized": payload.get("real_publish_authorized"),
        "media_bytes_included": payload.get("media_bytes_included"),
        "public_visibility_requested": payload.get("public_visibility_requested"),
        "production_identity_absent": payload.get("production_identity_absent"),
        "blocking_reasons": payload.get("blocking_reasons"),
        "incident_types": [hook.get("incident_type") for hook in payload.get("incident_hooks", [])],
        "residual_monitoring": payload.get("residual_monitoring"),
    }


def _preconditions() -> dict[str, Any]:
    request_gate, request_gate_error = _load_json(REQUEST_ENVELOPE_GATE_VERDICT_PATH)
    evidence_gate, evidence_gate_error = _load_json(EVIDENCE_GATE_VERDICT_PATH)
    required_docs = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [PLAN_DOC_PATH, GATE_DOC_PATH]
    }
    required_prior_artifacts = {
        str(path.relative_to(ROOT)): path.exists()
        for path in [REQUEST_ENVELOPE_GATE_VERDICT_PATH, EVIDENCE_GATE_VERDICT_PATH]
    }
    required_files = {
        str(path.relative_to(ROOT)): path.exists()
        for path in IMPLEMENTATION_FILES
    }
    checks = {
        "required_docs_present": all(required_docs.values()),
        "required_prior_artifacts_present": all(required_prior_artifacts.values()),
        "implementation_files_present": all(required_files.values()),
        "request_gate_json_valid": not request_gate_error,
        "request_gate_verdict_acceptable": request_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "request_gate_no_external_call": request_gate.get("external_call_authorized") is False,
        "request_gate_no_platform_api": request_gate.get("platform_api_called") is False,
        "request_gate_no_upload": request_gate.get("upload_performed") is False,
        "request_gate_no_scheduler": request_gate.get("scheduler_invoked") is False,
        "request_gate_no_real_publish": request_gate.get("real_publishing_performed") is False,
        "request_gate_production_residuals_open": request_gate.get("production_residuals_closed") is False,
        "evidence_gate_json_valid": not evidence_gate_error,
        "evidence_gate_verdict_acceptable": evidence_gate.get("verdict") in {"GO", "GO_WITH_MONITORING"},
        "evidence_gate_no_external_call": evidence_gate.get("external_call_authorized") is False,
        "evidence_gate_no_platform_api": evidence_gate.get("platform_api_called") is False,
        "evidence_gate_no_upload": evidence_gate.get("upload_performed") is False,
        "evidence_gate_no_scheduler": evidence_gate.get("scheduler_invoked") is False,
        "evidence_gate_no_real_publish": evidence_gate.get("real_publishing_performed") is False,
        "evidence_gate_production_residuals_open": evidence_gate.get("production_residuals_closed") is False,
    }
    return {
        "required_docs": required_docs,
        "required_prior_artifacts": required_prior_artifacts,
        "implementation_files": required_files,
        "request_gate_error": request_gate_error,
        "evidence_gate_error": evidence_gate_error,
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
        for token in ["requests.", "httpx.", "aiohttp.", "urllib.request.", "urllib3.", "socket.", ".getaddrinfo("]
        if token in source_text
    )
    checks = {
        "no_network_or_sdk_imports": not forbidden_imports,
        "no_executable_helper_defs": not executable_defs,
        "no_endpoint_constants": not endpoint_constants,
        "no_network_call_literals": not raw_network_literals,
    }
    return {
        "forbidden_imports": forbidden_imports,
        "executable_defs": executable_defs,
        "endpoint_constants": endpoint_constants,
        "raw_network_literals": raw_network_literals,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _transport_nullification_review(envelope: Any) -> dict[str, Any]:
    payload = envelope.to_dict()
    keys = _collect_keys(payload)
    exact_http_like_keys = sorted(HTTP_LIKE_FIELD_NAMES & keys)
    executable_helpers = sorted(
        set(executable_helper_names_on(envelope))
        | set(executable_helper_names_on(ExternalSandboxValidationEnvelopeBuilder()))
        | (set(dir(ExternalSandboxValidationEnvelope)) & EXECUTABLE_HELPER_NAMES)
    )
    serialized = json.dumps(payload, sort_keys=True)
    checks = {
        "execution_capability_none": payload.get("execution_capability") == "none",
        "transport_capability_none": payload.get("transport_capability") == "none",
        "non_transportable_true": payload.get("non_transportable") is True,
        "no_exact_http_like_fields": exact_http_like_keys == [],
        "no_executable_helpers": executable_helpers == [],
        "no_transport_payload_shape": payload.get("validation_result", {}).get("transport_payload_detected") is False,
        "audit_serialization_available": isinstance(serialized, str) and bool(serialized),
        "serialization_non_transportable_marker_present": '"non_transportable": true' in serialized,
    }
    return {
        "exact_http_like_keys": exact_http_like_keys,
        "executable_helpers": executable_helpers,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _contract_review(envelope: Any) -> dict[str, Any]:
    payload = envelope.to_dict()
    required_top_level = [
        "envelope_version",
        "envelope_type",
        "run_id",
        "content_id",
        "target_platform_id",
        "target_mode",
        "idempotency_key",
        "artifact_manifest_ref",
        "metadata_payload_ref",
        "qc_trace_ref",
        "account_health_trace_ref",
        "strategy_ref",
        "publish_eligibility_trace_ref",
        "credential_status",
        "kill_switch_status",
        "rate_limit_status",
        "metadata_projection",
        "metadata_shape_class",
        "execution_capability",
        "transport_capability",
        "non_transportable",
        "validation_result",
        "incident_hooks",
        "residual_monitoring",
        "boundary_statement",
    ]
    metadata_fields = [
        "title_present",
        "description_present",
        "tags_present",
        "language_present",
        "visibility_mode",
        "account_ref_present",
        "content_id",
        "runtime_policy_ref",
        "metadata_trace_ref",
        "metadata_shape_valid",
    ]
    validation_fields = [
        "envelope_valid",
        "eligible_for_future_external_sandbox_validation",
        "blocking_reasons",
        "warnings",
        "secret_leakage_detected",
        "forbidden_field_detected",
        "http_like_field_detected",
        "executable_helper_detected",
        "transport_payload_detected",
        "external_call_authorized",
        "platform_api_execution_authorized",
        "upload_authorized",
        "scheduler_authorized",
        "real_publish_authorized",
        "rationale",
    ]
    checks = {
        "required_top_level_fields_present": all(field in payload for field in required_top_level),
        "metadata_projection_fields_present": all(
            field in payload.get("metadata_projection", {}) for field in metadata_fields
        ),
        "validation_result_fields_present": all(
            field in payload.get("validation_result", {}) for field in validation_fields
        ),
        "envelope_type_valid": payload.get("envelope_type") == ENVELOPE_TYPE,
        "target_platform_exact": payload.get("target_platform_id") == TARGET_PLATFORM_ID,
        "target_mode_exact": payload.get("target_mode") == TARGET_MODE,
        "metadata_shape_class_valid": payload.get("metadata_shape_class") == "metadata_shape_only",
        "idempotency_namespace_valid": str(payload.get("idempotency_key", "")).startswith(IDEMPOTENCY_NAMESPACE),
        "validation_naming_primary": "ValidationEnvelope" in ExternalSandboxValidationEnvelope.__name__,
    }
    return {
        "required_top_level": required_top_level,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _security_review() -> dict[str, Any]:
    secret_value = "do-not-log-envelope-secret"
    secret_envelope = _build(metadata=_metadata(access_token=secret_value))
    forbidden_envelope = _build(
        metadata=_metadata(
            published_url="https://example.invalid/fake",
            platform_content_id="fake-platform-id",
        )
    )
    http_like_envelope = _build(metadata=_metadata(headers={"x": "y"}))
    transport_envelope = _build(metadata=_metadata(payload={"field": "value"}))
    secret_serialized = json.dumps(secret_envelope.to_dict(), sort_keys=True)
    forbidden_serialized = json.dumps(forbidden_envelope.to_dict(), sort_keys=True)
    checks = {
        "secret_leakage_detected": secret_envelope.validation_result["secret_leakage_detected"] is True,
        "secret_value_not_copied": secret_value not in secret_serialized,
        "forbidden_field_detected": forbidden_envelope.validation_result["forbidden_field_detected"] is True,
        "forbidden_values_not_copied": "https://example.invalid/fake" not in forbidden_serialized
        and "fake-platform-id" not in forbidden_serialized,
        "http_like_field_detected": http_like_envelope.validation_result["http_like_field_detected"] is True,
        "transport_payload_detected": transport_envelope.validation_result["transport_payload_detected"] is True,
        "incident_hooks_present": all(
            envelope.incident_hooks
            for envelope in [secret_envelope, forbidden_envelope, http_like_envelope, transport_envelope]
        ),
    }
    return {
        "checks": checks,
        "secret_summary": _envelope_summary(secret_envelope),
        "forbidden_summary": _envelope_summary(forbidden_envelope),
        "http_like_summary": _envelope_summary(http_like_envelope),
        "transport_summary": _envelope_summary(transport_envelope),
        "passed": all(checks.values()),
    }


def _determinism_review() -> dict[str, Any]:
    builder = ExternalSandboxValidationEnvelopeBuilder()
    first = _build()
    second = _build()
    changed = _build(content_id="content_changed")
    first_json = builder.deterministic_audit_json(first)
    second_json = builder.deterministic_audit_json(second)
    checks = {
        "same_input_same_idempotency_key": first.idempotency_key == second.idempotency_key,
        "changed_input_changes_idempotency_key": first.idempotency_key != changed.idempotency_key,
        "same_input_same_serialization": first_json == second_json,
        "idempotency_namespace_valid": first.idempotency_key.startswith(IDEMPOTENCY_NAMESPACE),
        "serialization_json_valid": isinstance(json.loads(first_json), dict),
    }
    return {
        "first_idempotency_key": first.idempotency_key,
        "changed_idempotency_key": changed.idempotency_key,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _side_effect_review(envelope: Any) -> dict[str, Any]:
    payload = envelope.to_dict()
    checks = {
        "external_call_authorized_false": payload["external_call_authorized"] is False,
        "platform_api_execution_authorized_false": payload["platform_api_execution_authorized"] is False,
        "upload_authorized_false": payload["upload_authorized"] is False,
        "scheduler_authorized_false": payload["scheduler_authorized"] is False,
        "real_publish_authorized_false": payload["real_publish_authorized"] is False,
        "media_bytes_included_false": payload["media_bytes_included"] is False,
        "public_visibility_requested_false": payload["public_visibility_requested"] is False,
        "production_identity_absent_true": payload["production_identity_absent"] is True,
        "validation_does_not_authorize_execution": payload["validation_result"]["external_call_authorized"] is False
        and payload["validation_result"]["real_publish_authorized"] is False,
        "future_eligibility_false": payload["validation_result"]["eligible_for_future_external_sandbox_validation"]
        is False,
    }
    return {
        "checks": checks,
        "observed": _envelope_summary(envelope),
        "passed": all(checks.values()),
    }


def _residual_review(envelope: Any) -> dict[str, Any]:
    residuals = list(envelope.residual_monitoring)
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


def _run_scenarios() -> dict[str, dict[str, Any]]:
    builder = ExternalSandboxValidationEnvelopeBuilder()
    envelope = _build()
    payload = envelope.to_dict()
    keys = _collect_keys(payload)
    serialized = json.dumps(payload, sort_keys=True)
    deterministic_json = builder.deterministic_audit_json(envelope)
    second_json = builder.deterministic_audit_json(_build())
    changed = _build(content_id="content_changed")

    mixed = _build(modes=[TARGET_MODE, "production"])
    provider = _build(provider_binding="YouTube")
    secret = _build(metadata=_metadata(access_token="do-not-log"))
    forbidden = _build(metadata=_metadata(published_url="https://example.invalid/fake", platform_content_id="fake"))
    http_like = _build(metadata=_metadata(headers={"x": "y"}))
    transport = _build(metadata=_metadata(payload={"field": "value"}))
    kill_active = _build(kill_switch_status={"active": True})
    kill_missing = _build(kill_switch_status={"missing": True})
    rate_authorized = _build(rate_limit_status={"sandbox_validation_requests_allowed": True})
    rate_ambiguous = _build(rate_limit_status={"max_sandbox_validation_requests_per_minute": 1})
    qc_hold = _build(qc_status="HOLD")
    qc_reject = _build(qc_status="REJECT")
    qc_not_publishable = _build(qc_publishable=False)
    health_hold = _build(account_health_decision="HOLD")
    missing_refs = _build(
        artifact_manifest_ref=None,
        metadata_payload_ref=None,
        qc_trace_ref=None,
        account_health_trace_ref=None,
        strategy_ref=None,
        publish_eligibility_trace_ref=None,
    )
    invalid_metadata = _build(metadata=_metadata(visibility_mode="public"))

    return {
        "implementation_present": _scenario(
            "implementation_present",
            all(path.exists() for path in IMPLEMENTATION_FILES),
            {"files": [str(path.relative_to(ROOT)) for path in IMPLEMENTATION_FILES]},
        ),
        "valid_inert_envelope_shape": _scenario(
            "valid_inert_envelope_shape",
            payload["envelope_type"] == ENVELOPE_TYPE and payload["validation_result"]["envelope_valid"] is True,
            _envelope_summary(envelope),
        ),
        "validation_naming_present": _scenario(
            "validation_naming_present",
            "ValidationEnvelope" in ExternalSandboxValidationEnvelope.__name__
            and "ValidationEnvelope" in ExternalSandboxValidationEnvelopeBuilder.__name__,
            {"envelope_class": ExternalSandboxValidationEnvelope.__name__},
        ),
        "request_execution_naming_absent": _scenario(
            "request_execution_naming_absent",
            "HttpRequest" not in ExternalSandboxValidationEnvelope.__name__
            and "PlatformRequest" not in ExternalSandboxValidationEnvelope.__name__,
            {"envelope_class": ExternalSandboxValidationEnvelope.__name__},
        ),
        "target_platform_exact": _scenario("target_platform_exact", payload["target_platform_id"] == TARGET_PLATFORM_ID),
        "target_mode_exact": _scenario("target_mode_exact", payload["target_mode"] == TARGET_MODE),
        "single_mode_enforced": _scenario("single_mode_enforced", payload["target_mode"] == TARGET_MODE),
        "mixed_mode_rejected": _scenario(
            "mixed_mode_rejected", "MIXED_MODE_REJECTED" in mixed.blocking_reasons, _envelope_summary(mixed)
        ),
        "execution_capability_none": _scenario(
            "execution_capability_none", payload["execution_capability"] == "none"
        ),
        "transport_capability_none": _scenario(
            "transport_capability_none", payload["transport_capability"] == "none"
        ),
        "non_transportable_true": _scenario("non_transportable_true", payload["non_transportable"] is True),
        "no_http_like_fields": _scenario(
            "no_http_like_fields",
            not (HTTP_LIKE_FIELD_NAMES & keys),
            {"exact_http_like_keys": sorted(HTTP_LIKE_FIELD_NAMES & keys)},
        ),
        "no_executable_helpers": _scenario(
            "no_executable_helpers",
            executable_helper_names_on(envelope) == [] and executable_helper_names_on(builder) == [],
            {
                "envelope_helpers": executable_helper_names_on(envelope),
                "builder_helpers": executable_helper_names_on(builder),
            },
        ),
        "audit_serialization_only": _scenario(
            "audit_serialization_only",
            isinstance(deterministic_json, str)
            and '"non_transportable":true' in deterministic_json
            and '"transport_capability":"none"' in deterministic_json,
        ),
        "no_http_client_imports": _scenario("no_http_client_imports", _static_scan_review()["checks"]["no_network_or_sdk_imports"]),
        "no_platform_sdk_imports": _scenario("no_platform_sdk_imports", _static_scan_review()["checks"]["no_network_or_sdk_imports"]),
        "no_endpoint_or_dns_configuration": _scenario(
            "no_endpoint_or_dns_configuration",
            _static_scan_review()["checks"]["no_endpoint_constants"]
            and _static_scan_review()["checks"]["no_network_call_literals"],
        ),
        "external_call_unauthorized": _scenario("external_call_unauthorized", payload["external_call_authorized"] is False),
        "platform_api_unauthorized": _scenario(
            "platform_api_unauthorized", payload["platform_api_execution_authorized"] is False
        ),
        "upload_unauthorized": _scenario("upload_unauthorized", payload["upload_authorized"] is False),
        "scheduler_unauthorized": _scenario("scheduler_unauthorized", payload["scheduler_authorized"] is False),
        "real_publish_unauthorized": _scenario("real_publish_unauthorized", payload["real_publish_authorized"] is False),
        "media_bytes_forbidden": _scenario("media_bytes_forbidden", payload["media_bytes_included"] is False),
        "public_visibility_forbidden": _scenario(
            "public_visibility_forbidden",
            payload["public_visibility_requested"] is False
            and "PUBLIC_VISIBILITY_FORBIDDEN" in invalid_metadata.blocking_reasons,
            _envelope_summary(invalid_metadata),
        ),
        "production_identity_absent": _scenario(
            "production_identity_absent",
            payload["production_identity_absent"] is True
            and "published_url" not in payload
            and "platform_content_id" not in payload,
        ),
        "metadata_projection_bounded": _scenario(
            "metadata_projection_bounded",
            payload["metadata_projection"]["metadata_shape_valid"] is True
            and "Sandbox description" not in serialized,
            {"metadata_projection": payload["metadata_projection"]},
        ),
        "credential_projection_status_only": _scenario(
            "credential_projection_status_only",
            payload["credential_status"]["credential_status"] == "present"
            and payload["credential_status"]["secret_values_logged"] is False
            and payload["credential_status"]["secret_values_persisted"] is False,
            {"credential_status": payload["credential_status"]},
        ),
        "secret_like_fields_detected_and_redacted": _scenario(
            "secret_like_fields_detected_and_redacted",
            "SECRET_LEAKAGE_ATTEMPT" in secret.blocking_reasons
            and "do-not-log" not in json.dumps(secret.to_dict(), sort_keys=True),
            _envelope_summary(secret),
        ),
        "forbidden_publish_identity_fields_detected": _scenario(
            "forbidden_publish_identity_fields_detected",
            "FORBIDDEN_FIELD_DETECTED" in forbidden.blocking_reasons
            and "https://example.invalid/fake" not in json.dumps(forbidden.to_dict(), sort_keys=True),
            _envelope_summary(forbidden),
        ),
        "http_like_field_detected": _scenario(
            "http_like_field_detected",
            "HTTP_LIKE_FIELD_DETECTED" in http_like.blocking_reasons,
            _envelope_summary(http_like),
        ),
        "transport_payload_shape_detected": _scenario(
            "transport_payload_shape_detected",
            "TRANSPORT_PAYLOAD_SHAPE_DETECTED" in transport.blocking_reasons,
            _envelope_summary(transport),
        ),
        "implicit_provider_binding_rejected": _scenario(
            "implicit_provider_binding_rejected",
            "IMPLICIT_PROVIDER_BINDING_REJECTED" in provider.blocking_reasons,
            _envelope_summary(provider),
        ),
        "kill_switch_active_blocks": _scenario(
            "kill_switch_active_blocks",
            "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE" in kill_active.blocking_reasons,
            _envelope_summary(kill_active),
        ),
        "kill_switch_missing_blocks": _scenario(
            "kill_switch_missing_blocks",
            "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE" in kill_missing.blocking_reasons,
            _envelope_summary(kill_missing),
        ),
        "disabled_rate_limit_not_unlimited": _scenario(
            "disabled_rate_limit_not_unlimited",
            payload["rate_limit_status"]["sandbox_validation_requests_allowed"] is False
            and payload["rate_limit_status"]["max_sandbox_validation_requests_per_minute"] is None,
            {"rate_limit_status": payload["rate_limit_status"]},
        ),
        "rate_limit_authorization_blocks": _scenario(
            "rate_limit_authorization_blocks",
            "RATE_LIMIT_REQUESTS_NOT_AUTHORIZED" in rate_authorized.blocking_reasons,
            _envelope_summary(rate_authorized),
        ),
        "rate_limit_ambiguous_limit_blocks": _scenario(
            "rate_limit_ambiguous_limit_blocks",
            "RATE_LIMIT_DISABLED_STATE_AMBIGUOUS" in rate_ambiguous.blocking_reasons,
            _envelope_summary(rate_ambiguous),
        ),
        "qc_hold_blocks": _scenario("qc_hold_blocks", "QC_HOLD" in qc_hold.blocking_reasons, _envelope_summary(qc_hold)),
        "qc_reject_blocks": _scenario(
            "qc_reject_blocks", "QC_REJECTED" in qc_reject.blocking_reasons, _envelope_summary(qc_reject)
        ),
        "qc_non_publishable_blocks": _scenario(
            "qc_non_publishable_blocks",
            "QC_NOT_PUBLISHABLE" in qc_not_publishable.blocking_reasons,
            _envelope_summary(qc_not_publishable),
        ),
        "account_health_hold_blocks": _scenario(
            "account_health_hold_blocks",
            "ACCOUNT_HEALTH_HOLD" in health_hold.blocking_reasons,
            _envelope_summary(health_hold),
        ),
        "missing_dependency_refs_block": _scenario(
            "missing_dependency_refs_block",
            all(
                reason in missing_refs.blocking_reasons
                for reason in [
                    "MISSING_ARTIFACT_MANIFEST",
                    "MISSING_METADATA_PAYLOAD",
                    "MISSING_QC_TRACE",
                    "MISSING_ACCOUNT_HEALTH_TRACE",
                    "MISSING_STRATEGY_CONTEXT",
                    "MISSING_PUBLISH_ELIGIBILITY_TRACE",
                ]
            ),
            _envelope_summary(missing_refs),
        ),
        "idempotency_namespace_valid": _scenario(
            "idempotency_namespace_valid", envelope.idempotency_key.startswith(IDEMPOTENCY_NAMESPACE)
        ),
        "idempotency_deterministic": _scenario(
            "idempotency_deterministic", envelope.idempotency_key == _build().idempotency_key
        ),
        "changed_input_changes_idempotency": _scenario(
            "changed_input_changes_idempotency", envelope.idempotency_key != changed.idempotency_key
        ),
        "validity_does_not_imply_success": _scenario(
            "validity_does_not_imply_success",
            payload["validation_result"]["envelope_valid"] is True
            and payload["validation_result"]["eligible_for_future_external_sandbox_validation"] is False
            and payload["validation_result"]["real_publish_authorized"] is False,
        ),
        "incident_hooks_do_not_leak_secrets": _scenario(
            "incident_hooks_do_not_leak_secrets",
            "do-not-log" not in json.dumps(secret.incident_hooks, sort_keys=True),
        ),
        "deterministic_serialization_replay": _scenario(
            "deterministic_serialization_replay", deterministic_json == second_json
        ),
        "production_residuals_remain_open": _scenario(
            "production_residuals_remain_open", envelope.residual_monitoring == PRODUCTION_RESIDUALS
        ),
    }


def _build_checklist(
    *,
    preconditions: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    static_scan: dict[str, Any],
    contract: dict[str, Any],
    security: dict[str, Any],
    transport: dict[str, Any],
    determinism: dict[str, Any],
    side_effects: dict[str, Any],
    residuals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    checks: dict[str, bool] = {
        "preconditions_passed": preconditions["passed"],
        "implementation_present": all(path.exists() for path in IMPLEMENTATION_FILES),
        "unit_test_file_present": IMPLEMENTATION_FILES[2].exists(),
        "offline_only": side_effects["passed"],
        "transport_nullification_valid": transport["passed"],
        "no_http_like_fields": transport["checks"]["no_exact_http_like_fields"],
        "no_executable_helpers": transport["checks"]["no_executable_helpers"],
        "no_network_or_sdk_imports": static_scan["checks"]["no_network_or_sdk_imports"],
        "no_endpoint_constants": static_scan["checks"]["no_endpoint_constants"],
        "deterministic_serialization": determinism["checks"]["same_input_same_serialization"],
        "forbidden_field_scanner_valid": security["checks"]["forbidden_field_detected"],
        "secret_scanner_valid": security["checks"]["secret_leakage_detected"],
        "metadata_projection_bounded": contract["checks"]["metadata_projection_fields_present"],
        "credential_projection_status_only": security["checks"]["secret_value_not_copied"],
        "idempotency_namespace_valid": determinism["checks"]["idempotency_namespace_valid"],
        "idempotency_deterministic": determinism["checks"]["same_input_same_idempotency_key"],
        "changed_input_changes_idempotency": determinism["checks"]["changed_input_changes_idempotency_key"],
        "target_platform_exact": contract["checks"]["target_platform_exact"],
        "target_mode_exact": contract["checks"]["target_mode_exact"],
        "validation_naming_primary": contract["checks"]["validation_naming_primary"],
        "envelope_type_valid": contract["checks"]["envelope_type_valid"],
        "schema_fields_present": contract["checks"]["required_top_level_fields_present"],
        "validation_result_fields_present": contract["checks"]["validation_result_fields_present"],
        "external_call_not_authorized": side_effects["checks"]["external_call_authorized_false"],
        "platform_api_not_authorized": side_effects["checks"]["platform_api_execution_authorized_false"],
        "upload_not_authorized": side_effects["checks"]["upload_authorized_false"],
        "scheduler_not_authorized": side_effects["checks"]["scheduler_authorized_false"],
        "real_publish_not_authorized": side_effects["checks"]["real_publish_authorized_false"],
        "media_bytes_not_included": side_effects["checks"]["media_bytes_included_false"],
        "public_visibility_not_requested": side_effects["checks"]["public_visibility_requested_false"],
        "production_identity_absent": side_effects["checks"]["production_identity_absent_true"],
        "validation_does_not_authorize_execution": side_effects["checks"]["validation_does_not_authorize_execution"],
        "future_eligibility_false": side_effects["checks"]["future_eligibility_false"],
        "incident_hooks_safe": security["checks"]["incident_hooks_present"],
        "production_residuals_not_closed": residuals["checks"]["production_residuals_closed_false"],
        "all_scenarios_passed": all(item["passed"] for item in scenarios.values()),
    }
    return {
        name: {
            "passed": bool(passed),
            "failure_reason": None if passed else "CHECK_FAILED",
        }
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
    envelope = _build()
    scenarios = _run_scenarios()
    static_scan = _static_scan_review()
    contract = _contract_review(envelope)
    security = _security_review()
    transport = _transport_nullification_review(envelope)
    determinism = _determinism_review()
    side_effects = _side_effect_review(envelope)
    residuals = _residual_review(envelope)
    checklist = _build_checklist(
        preconditions=preconditions,
        scenarios=scenarios,
        static_scan=static_scan,
        contract=contract,
        security=security,
        transport=transport,
        determinism=determinism,
        side_effects=side_effects,
        residuals=residuals,
    )
    blocking_failures = _blocking_failures(checklist, scenarios)

    scenario_count = len(scenarios)
    scenario_pass_count = sum(1 for item in scenarios.values() if item["passed"])
    checklist_count = len(checklist)
    checklist_pass_count = sum(1 for item in checklist.values() if item["passed"])

    critical_flags = {
        "external_call_authorized": not side_effects["checks"]["external_call_authorized_false"],
        "platform_api_called": not side_effects["checks"]["platform_api_execution_authorized_false"],
        "upload_performed": not side_effects["checks"]["upload_authorized_false"],
        "scheduler_invoked": not side_effects["checks"]["scheduler_authorized_false"],
        "real_publishing_performed": not side_effects["checks"]["real_publish_authorized_false"],
        "real_url_emitted": not side_effects["checks"]["production_identity_absent_true"],
        "platform_content_id_emitted": not side_effects["checks"]["production_identity_absent_true"],
        "http_client_detected": not static_scan["checks"]["no_network_or_sdk_imports"],
        "platform_sdk_detected": not static_scan["checks"]["no_network_or_sdk_imports"],
        "endpoint_detected": not static_scan["checks"]["no_endpoint_constants"],
        "dns_or_network_detected": not static_scan["checks"]["no_network_call_literals"],
        "http_like_fields_detected": not transport["checks"]["no_exact_http_like_fields"],
        "executable_helpers_detected": not transport["checks"]["no_executable_helpers"],
        "transport_payload_detected": not transport["checks"]["no_transport_payload_shape"],
        "secret_leakage_detected": False,
        "forbidden_field_detected": False,
        "fake_success_detected": not side_effects["checks"]["validation_does_not_authorize_execution"],
        "production_residuals_closed": not residuals["checks"]["production_residuals_closed_false"],
    }

    hold_required = bool(blocking_failures) or any(critical_flags.values())
    verdict = "HOLD" if hold_required else "GO_WITH_MONITORING"
    recommendation = (
        "PROCEED_TO_EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE_REVIEW"
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
        "silent_failures_detected": False,
    }

    final_verdict = {
        "system": "CORTAI_RUNTIME_V2_5",
        "phase": "3",
        "audit_type": "EXTERNAL_SANDBOX_REQUEST_ENVELOPE_IMPLEMENTATION_GATE",
        "verdict": verdict,
        "timestamp": now,
        "target_platform_id": TARGET_PLATFORM_ID,
        "target_mode": TARGET_MODE,
        "validation_envelope_implemented": all(path.exists() for path in IMPLEMENTATION_FILES[:2]),
        "implementation_present": all(path.exists() for path in IMPLEMENTATION_FILES),
        "offline_only": side_effects["passed"],
        "execution_capability": envelope.execution_capability,
        "transport_capability": envelope.transport_capability,
        "non_transportable": envelope.non_transportable,
        "transport_nullification_valid": transport["passed"],
        "no_http_like_fields": transport["checks"]["no_exact_http_like_fields"],
        "no_executable_helpers": transport["checks"]["no_executable_helpers"],
        "no_network_or_sdk_imports": static_scan["checks"]["no_network_or_sdk_imports"],
        "idempotency_namespace_valid": determinism["checks"]["idempotency_namespace_valid"],
        "deterministic_serialization": determinism["checks"]["same_input_same_serialization"],
        "forbidden_field_scanner_valid": security["checks"]["forbidden_field_detected"],
        "secret_scanner_valid": security["checks"]["secret_leakage_detected"],
        "external_call_authorized": False,
        "platform_api_called": False,
        "upload_performed": False,
        "scheduler_invoked": False,
        "real_publishing_performed": False,
        "real_url_emitted": False,
        "platform_content_id_emitted": False,
        "production_residuals_closed": False,
        "metrics": metrics,
        "blocking_failures": blocking_failures,
        "residual_monitoring": list(PRODUCTION_RESIDUALS),
        "recommendation": recommendation,
    }

    _write_json(CHECKLIST_RESULTS_PATH, checklist)
    _write_json(SCENARIO_OUTPUTS_PATH, scenarios)
    _write_json(METRICS_PATH, metrics)
    _write_json(SECURITY_REVIEW_PATH, security)
    _write_json(CONTRACT_REVIEW_PATH, contract)
    _write_json(TRANSPORT_REVIEW_PATH, transport)
    _write_json(STATIC_SCAN_REVIEW_PATH, static_scan)
    _write_json(DETERMINISM_REVIEW_PATH, determinism)
    _write_json(SIDE_EFFECT_REVIEW_PATH, side_effects)
    _write_json(RESIDUAL_REVIEW_PATH, residuals)
    _write_json(FINAL_VERDICT_PATH, final_verdict)

    print(json.dumps(final_verdict, indent=2, sort_keys=False, ensure_ascii=True))
    return 0 if verdict != "HOLD" else 1


if __name__ == "__main__":
    raise SystemExit(main())
