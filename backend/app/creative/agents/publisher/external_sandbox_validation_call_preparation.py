from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.publisher.external_sandbox_validation_call_preparation_security import (
    SandboxValidationCallPreparationSecurityScan,
    scan_preparation_input,
)
from app.creative.agents.publisher.sandbox_contracts import (
    PRODUCTION_RESIDUALS,
    SANDBOX_TARGET_MODE,
    SANDBOX_TARGET_PLATFORM_ID,
)


PREPARATION_VERSION = "sandbox_validation_call_preparation_v1"
TARGET_PLATFORM_ID = SANDBOX_TARGET_PLATFORM_ID
TARGET_MODE = SANDBOX_TARGET_MODE
BOUNDARY_STATEMENT = "Sandbox validation call preparation is not sandbox validation execution."
EXTENDED_RESIDUALS = list(PRODUCTION_RESIDUALS) + [
    "EXTERNAL_CALL_NOT_IMPLEMENTED",
    "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED",
]
ALLOWED_CREDENTIAL_STATUSES = {"present", "missing", "invalid_shape", "not_checked"}
ALLOWED_RATE_LIMIT_STATES = {"not_applicable", "blocked", "unknown"}


@dataclass(frozen=True)
class SandboxValidationCallPreparationInput:
    run_id: str
    content_id: str
    validation_envelope_ref: str | None
    publish_eligibility_trace_ref: str | None
    qc_trace_ref: str | None
    account_health_trace_ref: str | None
    artifact_manifest_ref: str | None
    metadata_payload_ref: str | None
    credential_status: str = "not_checked"
    kill_switch_blocking: bool = True
    rate_limit_state: str = "not_applicable"
    target_platform_id: str = TARGET_PLATFORM_ID
    target_mode: str = TARGET_MODE
    qc_publishable: bool | None = True
    qc_status: str | None = "APPROVE"
    account_health_decision: str | None = "SAFE"
    additional_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxValidationCallDependencyStatus:
    validation_envelope_ref_present: bool
    publish_eligibility_trace_ref_present: bool
    qc_trace_ref_present: bool
    account_health_trace_ref_present: bool
    artifact_manifest_ref_present: bool
    metadata_payload_ref_present: bool
    qc_publishable: bool
    qc_status: str
    account_health_decision: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxValidationCallCredentialStatus:
    credential_status: str
    credential_source: str = "status_only"
    credential_value_access_authorized: bool = False
    secret_values_logged: bool = False
    secret_values_persisted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxValidationCallPreparationIncident:
    incident_type: str
    severity: str
    run_id: str
    content_id: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxValidationCallPreparationValidation:
    preparation_valid: bool
    preparation_complete: bool
    eligible_for_future_sandbox_validation_review: bool
    blocking_reasons: list[str]
    warnings: list[str]
    security_scan: dict[str, Any]
    external_call_authorized: bool
    request_transformation_authorized: bool
    transport_payload_authorized: bool
    credential_value_access_authorized: bool
    runtime_integration_authorized: bool
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxValidationCallPreparationState:
    preparation_version: str
    run_id: str
    content_id: str
    target_platform_id: str
    target_mode: str
    preparation_complete: bool
    eligible_for_future_sandbox_validation_review: bool
    external_call_authorized: bool
    request_transformation_authorized: bool
    transport_payload_authorized: bool
    credential_value_access_authorized: bool
    runtime_integration_authorized: bool
    dependency_status: dict[str, Any]
    credential_status: dict[str, Any]
    kill_switch_blocking: bool
    rate_limit_state: str
    blocking_reasons: list[str]
    warnings: list[str]
    validation: dict[str, Any]
    incident_hooks: list[dict[str, Any]]
    residual_monitoring: list[str]
    boundary_statement: str = BOUNDARY_STATEMENT

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SandboxValidationCallPreparationBuilder:
    """Builds local preparation state without creating request, transport or execution capability."""

    def build(self, data: SandboxValidationCallPreparationInput) -> SandboxValidationCallPreparationState:
        security_scan = scan_preparation_input(data.to_dict())
        dependency_status = self._dependency_status(data)
        credential_status = self._credential_status(data.credential_status)
        blocking_reasons = self._blocking_reasons(data, dependency_status, credential_status, security_scan)
        warnings = ["SANDBOX_VALIDATION_CALL_NOT_AUTHORIZED"]
        preparation_complete = not blocking_reasons
        validation = SandboxValidationCallPreparationValidation(
            preparation_valid=bool(data.run_id and data.content_id),
            preparation_complete=preparation_complete,
            eligible_for_future_sandbox_validation_review=preparation_complete,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            security_scan=security_scan.to_dict(),
            external_call_authorized=False,
            request_transformation_authorized=False,
            transport_payload_authorized=False,
            credential_value_access_authorized=False,
            runtime_integration_authorized=False,
            rationale=self._rationale(preparation_complete, blocking_reasons),
        )
        return SandboxValidationCallPreparationState(
            preparation_version=PREPARATION_VERSION,
            run_id=data.run_id,
            content_id=data.content_id,
            target_platform_id=TARGET_PLATFORM_ID,
            target_mode=TARGET_MODE,
            preparation_complete=preparation_complete,
            eligible_for_future_sandbox_validation_review=preparation_complete,
            external_call_authorized=False,
            request_transformation_authorized=False,
            transport_payload_authorized=False,
            credential_value_access_authorized=False,
            runtime_integration_authorized=False,
            dependency_status=dependency_status.to_dict(),
            credential_status=credential_status.to_dict(),
            kill_switch_blocking=bool(data.kill_switch_blocking),
            rate_limit_state=self._normalize_rate_limit_state(data.rate_limit_state),
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            validation=validation.to_dict(),
            incident_hooks=[hook.to_dict() for hook in self._incident_hooks(data, blocking_reasons, security_scan)],
            residual_monitoring=list(EXTENDED_RESIDUALS),
            boundary_statement=BOUNDARY_STATEMENT,
        )

    def deterministic_audit_json(self, state: SandboxValidationCallPreparationState) -> str:
        return json.dumps(state.to_dict(), sort_keys=True, ensure_ascii=True, separators=(",", ":"))

    def _dependency_status(self, data: SandboxValidationCallPreparationInput) -> SandboxValidationCallDependencyStatus:
        return SandboxValidationCallDependencyStatus(
            validation_envelope_ref_present=bool(data.validation_envelope_ref),
            publish_eligibility_trace_ref_present=bool(data.publish_eligibility_trace_ref),
            qc_trace_ref_present=bool(data.qc_trace_ref),
            account_health_trace_ref_present=bool(data.account_health_trace_ref),
            artifact_manifest_ref_present=bool(data.artifact_manifest_ref),
            metadata_payload_ref_present=bool(data.metadata_payload_ref),
            qc_publishable=data.qc_publishable is True,
            qc_status=(data.qc_status or "UNKNOWN").strip().upper(),
            account_health_decision=(data.account_health_decision or "UNKNOWN").strip().upper(),
        )

    def _credential_status(self, value: str) -> SandboxValidationCallCredentialStatus:
        normalized = (value or "not_checked").strip().lower() or "not_checked"
        if normalized not in ALLOWED_CREDENTIAL_STATUSES:
            normalized = "invalid_shape"
        return SandboxValidationCallCredentialStatus(credential_status=normalized)

    def _normalize_rate_limit_state(self, value: str) -> str:
        normalized = (value or "unknown").strip().lower() or "unknown"
        return normalized if normalized in ALLOWED_RATE_LIMIT_STATES else "unknown"

    def _blocking_reasons(
        self,
        data: SandboxValidationCallPreparationInput,
        dependency_status: SandboxValidationCallDependencyStatus,
        credential_status: SandboxValidationCallCredentialStatus,
        security_scan: SandboxValidationCallPreparationSecurityScan,
    ) -> list[str]:
        reasons: list[str] = []
        if data.target_platform_id != TARGET_PLATFORM_ID:
            reasons.append("INVALID_TARGET_PLATFORM")
        if data.target_mode != TARGET_MODE:
            reasons.append("INVALID_TARGET_MODE")
        if not data.run_id:
            reasons.append("MISSING_RUN_ID")
        if not data.content_id:
            reasons.append("MISSING_CONTENT_ID")
        if not dependency_status.validation_envelope_ref_present:
            reasons.append("MISSING_VALIDATION_ENVELOPE_REF")
        if not dependency_status.publish_eligibility_trace_ref_present:
            reasons.append("MISSING_PUBLISH_ELIGIBILITY_TRACE")
        if not dependency_status.qc_trace_ref_present:
            reasons.append("MISSING_QC_TRACE")
        if not dependency_status.account_health_trace_ref_present:
            reasons.append("MISSING_ACCOUNT_HEALTH_TRACE")
        if not dependency_status.artifact_manifest_ref_present:
            reasons.append("MISSING_ARTIFACT_MANIFEST")
        if not dependency_status.metadata_payload_ref_present:
            reasons.append("MISSING_METADATA_PAYLOAD")
        if dependency_status.qc_status == "HOLD":
            reasons.append("QC_HOLD")
        if dependency_status.qc_status == "REJECT":
            reasons.append("QC_REJECTED")
        if not dependency_status.qc_publishable:
            reasons.append("QC_NOT_PUBLISHABLE")
        if dependency_status.account_health_decision == "HOLD":
            reasons.append("ACCOUNT_HEALTH_HOLD")
        if credential_status.credential_status == "missing":
            reasons.append("PUBLISHER_CREDENTIALS_MISSING")
        if credential_status.credential_status == "invalid_shape":
            reasons.append("PUBLISHER_CREDENTIAL_VALIDATION_FAILED")
        if not data.kill_switch_blocking:
            reasons.append("KILL_SWITCH_NOT_BLOCKING")
        if self._normalize_rate_limit_state(data.rate_limit_state) == "unknown":
            reasons.append("RATE_LIMIT_STATE_UNKNOWN")
        if security_scan.secret_leakage_detected:
            reasons.append("SECRET_LIKE_FIELD_DETECTED")
        if security_scan.forbidden_field_detected:
            reasons.append("FORBIDDEN_FIELD_DETECTED")
        if security_scan.http_like_field_detected:
            reasons.append("HTTP_LIKE_FIELD_DETECTED")
        if security_scan.transport_payload_detected:
            reasons.append("TRANSPORT_PAYLOAD_DETECTED")
        return list(dict.fromkeys(reasons))

    def _incident_hooks(
        self,
        data: SandboxValidationCallPreparationInput,
        blocking_reasons: list[str],
        security_scan: SandboxValidationCallPreparationSecurityScan,
    ) -> list[SandboxValidationCallPreparationIncident]:
        incident_map = {
            "SECRET_LIKE_FIELD_DETECTED": "SANDBOX_VALIDATION_CALL_PREPARATION_SECRET_FIELD",
            "FORBIDDEN_FIELD_DETECTED": "SANDBOX_VALIDATION_CALL_PREPARATION_FORBIDDEN_FIELD",
            "HTTP_LIKE_FIELD_DETECTED": "SANDBOX_VALIDATION_CALL_PREPARATION_HTTP_LIKE_FIELD",
            "TRANSPORT_PAYLOAD_DETECTED": "SANDBOX_VALIDATION_CALL_PREPARATION_TRANSPORT_PAYLOAD",
            "ACCOUNT_HEALTH_HOLD": "ACCOUNT_HEALTH_HOLD_BLOCKED_PREPARATION",
            "QC_REJECTED": "QC_BLOCKED_PREPARATION",
            "QC_HOLD": "QC_BLOCKED_PREPARATION",
            "QC_NOT_PUBLISHABLE": "QC_BLOCKED_PREPARATION",
        }
        hooks: list[SandboxValidationCallPreparationIncident] = []
        seen: set[str] = set()
        for reason in blocking_reasons:
            incident_type = incident_map.get(reason)
            if not incident_type or incident_type in seen:
                continue
            seen.add(incident_type)
            hooks.append(
                SandboxValidationCallPreparationIncident(
                    incident_type=incident_type,
                    severity="critical" if reason in {"SECRET_LIKE_FIELD_DETECTED", "FORBIDDEN_FIELD_DETECTED"} else "warning",
                    run_id=data.run_id,
                    content_id=data.content_id,
                    rationale=[self._incident_rationale(reason, security_scan)],
                )
            )
        return hooks

    def _incident_rationale(
        self,
        reason: str,
        security_scan: SandboxValidationCallPreparationSecurityScan,
    ) -> str:
        if reason == "SECRET_LIKE_FIELD_DETECTED":
            return "Secret-like field names were detected; values were not copied into preparation output."
        if reason == "FORBIDDEN_FIELD_DETECTED":
            return "Forbidden external execution or production result fields were detected."
        if reason == "HTTP_LIKE_FIELD_DETECTED":
            return "HTTP-like fields are not allowed in offline preparation."
        if reason == "TRANSPORT_PAYLOAD_DETECTED":
            return "Transport-shaped fields are not allowed in offline preparation."
        return f"{reason} blocks sandbox validation call preparation."

    def _rationale(self, preparation_complete: bool, blocking_reasons: list[str]) -> list[str]:
        rationale = [
            "Preparation is local and offline only.",
            "Preparation never authorizes external calls, transport payloads or runtime integration.",
        ]
        if preparation_complete:
            rationale.append("Local dependency and security checks passed for future review only.")
        else:
            rationale.append("Blocking reasons are explicit and preserve non-execution semantics.")
        return rationale
