from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.publisher.external_sandbox_envelope_security import (
    ExternalSandboxEnvelopeSecurityScan,
    executable_helper_names_on,
    scan_envelope_input,
)
from app.creative.agents.publisher.sandbox_contracts import (
    PRODUCTION_RESIDUALS,
    SANDBOX_RATE_LIMIT_POLICY_VERSION,
    SANDBOX_TARGET_MODE,
    SANDBOX_TARGET_PLATFORM_ID,
)


ENVELOPE_VERSION = "external_sandbox_request_envelope_v1"
ENVELOPE_TYPE = "external_sandbox_validation_envelope"
TARGET_PLATFORM_ID = SANDBOX_TARGET_PLATFORM_ID
TARGET_MODE = SANDBOX_TARGET_MODE
METADATA_SHAPE_CLASS = "metadata_shape_only"
BOUNDARY_STATEMENT = "External sandbox validation envelope is non-executable and non-transportable."
IDEMPOTENCY_NAMESPACE = "external_sandbox_envelope_v1:"

ALLOWED_CREDENTIAL_STATUSES = {"present", "missing", "invalid_shape", "not_checked"}


@dataclass(frozen=True)
class ExternalSandboxValidationEnvelopeInput:
    run_id: str
    content_id: str
    artifact_manifest_ref: str | None
    metadata_payload_ref: str | None
    qc_trace_ref: str | None
    account_health_trace_ref: str | None
    strategy_ref: str | None
    publish_eligibility_trace_ref: str | None
    metadata: dict[str, Any]
    qc_status: str | None = "APPROVE"
    qc_publishable: bool | None = True
    account_health_decision: str | None = "SAFE"
    target_platform_id: str = TARGET_PLATFORM_ID
    target_mode: str = TARGET_MODE
    modes: list[str] = field(default_factory=lambda: [TARGET_MODE])
    provider_binding: str | None = None
    credential_status: str = "present"
    kill_switch_status: dict[str, Any] = field(default_factory=dict)
    rate_limit_status: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxMetadataProjection:
    title_present: bool
    description_present: bool
    tags_present: bool
    language_present: bool
    visibility_mode: str
    account_ref_present: bool
    content_id: str
    runtime_policy_ref: str | None
    metadata_trace_ref: str | None
    metadata_shape_valid: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxCredentialProjection:
    credential_status: str
    credential_source: str = "environment_or_secret_manager"
    secret_values_logged: bool = False
    secret_values_persisted: bool = False
    secret_scope_class: str = "sandbox_validation_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxKillSwitchProjection:
    kill_switch_name: str = "PUBLISHER_PLATFORM_KILL_SWITCH"
    default_safe_state: str = "blocked"
    active: bool = False
    missing: bool = False
    blocks_publish_attempt: bool = True
    blocks_external_calls: bool = True
    blocks_upload: bool = True
    blocks_scheduler: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxRateLimitProjection:
    rate_limit_policy_version: str = SANDBOX_RATE_LIMIT_POLICY_VERSION
    sandbox_validation_requests_allowed: bool = False
    upload_requests_allowed: bool = False
    publish_requests_allowed: bool = False
    max_sandbox_validation_requests_per_minute: int | None = None
    max_upload_requests_per_hour: int | None = None
    max_publish_requests_per_day: int | None = None
    burst_allowed: bool = False
    rate_limit_exceeded_behavior: str = "block_and_trace"
    rate_limit_exceeded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxEnvelopeIncidentHook:
    incident_type: str
    severity: str
    run_id: str
    content_id: str
    target_platform_id: str
    target_mode: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxEnvelopeValidationResult:
    envelope_valid: bool
    eligible_for_future_external_sandbox_validation: bool
    blocking_reasons: list[str]
    warnings: list[str]
    secret_leakage_detected: bool
    forbidden_field_detected: bool
    http_like_field_detected: bool
    executable_helper_detected: bool
    transport_payload_detected: bool
    external_call_authorized: bool
    platform_api_execution_authorized: bool
    upload_authorized: bool
    scheduler_authorized: bool
    real_publish_authorized: bool
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxValidationEnvelope:
    envelope_version: str
    envelope_type: str
    run_id: str
    content_id: str
    target_platform_id: str
    target_mode: str
    idempotency_key: str
    artifact_manifest_ref: str | None
    metadata_payload_ref: str | None
    qc_trace_ref: str | None
    account_health_trace_ref: str | None
    strategy_ref: str | None
    publish_eligibility_trace_ref: str | None
    credential_status: dict[str, Any]
    kill_switch_status: dict[str, Any]
    rate_limit_status: dict[str, Any]
    metadata_projection: dict[str, Any]
    metadata_shape_class: str
    execution_capability: str
    transport_capability: str
    non_transportable: bool
    media_bytes_included: bool
    public_visibility_requested: bool
    external_call_authorized: bool
    platform_api_execution_authorized: bool
    upload_authorized: bool
    scheduler_authorized: bool
    real_publish_authorized: bool
    production_identity_absent: bool
    blocking_reasons: list[str]
    warnings: list[str]
    validation_result: dict[str, Any]
    incident_hooks: list[dict[str, Any]]
    residual_monitoring: list[str]
    boundary_statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExternalSandboxValidationEnvelopeBuilder:
    """Builds an inert Publisher sandbox validation object with no transport capability."""

    def build(self, data: ExternalSandboxValidationEnvelopeInput) -> ExternalSandboxValidationEnvelope:
        security_scan = scan_envelope_input(data.to_dict())
        credential = self._credential_projection(data.credential_status)
        kill_switch = self._kill_switch_projection(data.kill_switch_status)
        rate_limit = self._rate_limit_projection(data.rate_limit_status)
        metadata = self._metadata_projection(data)
        blocking_reasons = self._blocking_reasons(data, security_scan, credential, kill_switch, rate_limit, metadata)
        warnings = ["EXTERNAL_SANDBOX_VALIDATION_NOT_AUTHORIZED"]
        validation_result = ExternalSandboxEnvelopeValidationResult(
            envelope_valid=bool(data.run_id and data.content_id),
            eligible_for_future_external_sandbox_validation=False,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            secret_leakage_detected=security_scan.secret_leakage_detected,
            forbidden_field_detected=security_scan.forbidden_field_detected,
            http_like_field_detected=security_scan.http_like_field_detected,
            executable_helper_detected=security_scan.executable_helper_detected
            or bool(executable_helper_names_on(self)),
            transport_payload_detected=security_scan.transport_payload_detected,
            external_call_authorized=False,
            platform_api_execution_authorized=False,
            upload_authorized=False,
            scheduler_authorized=False,
            real_publish_authorized=False,
            rationale=self._validation_rationale(blocking_reasons),
        )
        return ExternalSandboxValidationEnvelope(
            envelope_version=ENVELOPE_VERSION,
            envelope_type=ENVELOPE_TYPE,
            run_id=data.run_id,
            content_id=data.content_id,
            target_platform_id=TARGET_PLATFORM_ID,
            target_mode=TARGET_MODE,
            idempotency_key=self.build_idempotency_key(data),
            artifact_manifest_ref=data.artifact_manifest_ref,
            metadata_payload_ref=data.metadata_payload_ref,
            qc_trace_ref=data.qc_trace_ref,
            account_health_trace_ref=data.account_health_trace_ref,
            strategy_ref=data.strategy_ref,
            publish_eligibility_trace_ref=data.publish_eligibility_trace_ref,
            credential_status=credential.to_dict(),
            kill_switch_status=kill_switch.to_dict(),
            rate_limit_status=rate_limit.to_dict(),
            metadata_projection=metadata.to_dict(),
            metadata_shape_class=METADATA_SHAPE_CLASS,
            execution_capability="none",
            transport_capability="none",
            non_transportable=True,
            media_bytes_included=False,
            public_visibility_requested=False,
            external_call_authorized=False,
            platform_api_execution_authorized=False,
            upload_authorized=False,
            scheduler_authorized=False,
            real_publish_authorized=False,
            production_identity_absent=True,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            validation_result=validation_result.to_dict(),
            incident_hooks=[hook.to_dict() for hook in self._incident_hooks(data, blocking_reasons, security_scan)],
            residual_monitoring=list(PRODUCTION_RESIDUALS),
            boundary_statement=BOUNDARY_STATEMENT,
        )

    def build_idempotency_key(self, data: ExternalSandboxValidationEnvelopeInput) -> str:
        payload = "|".join(
            [
                data.run_id,
                data.content_id,
                str(data.artifact_manifest_ref or ""),
                TARGET_PLATFORM_ID,
                TARGET_MODE,
            ]
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
        return f"{IDEMPOTENCY_NAMESPACE}{digest}"

    def _metadata_projection(self, data: ExternalSandboxValidationEnvelopeInput) -> ExternalSandboxMetadataProjection:
        metadata = data.metadata or {}
        shape_valid = all(
            [
                bool(metadata.get("title")),
                bool(metadata.get("description")),
                bool(metadata.get("tags")),
                bool(metadata.get("language")),
                metadata.get("visibility_mode") == "sandbox_only",
                bool(metadata.get("account_id")),
                bool(metadata.get("runtime_policy_ref")),
                bool(metadata.get("metadata_trace_ref")),
            ]
        )
        return ExternalSandboxMetadataProjection(
            title_present=bool(metadata.get("title")),
            description_present=bool(metadata.get("description")),
            tags_present=bool(metadata.get("tags")),
            language_present=bool(metadata.get("language")),
            visibility_mode="sandbox_only" if metadata.get("visibility_mode") == "sandbox_only" else "invalid_or_missing",
            account_ref_present=bool(metadata.get("account_id")),
            content_id=data.content_id,
            runtime_policy_ref=str(metadata.get("runtime_policy_ref")) if metadata.get("runtime_policy_ref") else None,
            metadata_trace_ref=str(metadata.get("metadata_trace_ref")) if metadata.get("metadata_trace_ref") else None,
            metadata_shape_valid=shape_valid,
        )

    def _credential_projection(self, status: str) -> ExternalSandboxCredentialProjection:
        normalized = (status or "not_checked").strip().lower() or "not_checked"
        return ExternalSandboxCredentialProjection(credential_status=normalized)

    def _kill_switch_projection(self, payload: dict[str, Any]) -> ExternalSandboxKillSwitchProjection:
        source = dict(payload or {})
        return ExternalSandboxKillSwitchProjection(
            active=bool(source.get("active", False)),
            missing=bool(source.get("missing", False)),
            blocks_publish_attempt=bool(source.get("blocks_publish_attempt", True)),
            blocks_external_calls=bool(source.get("blocks_external_calls", True)),
            blocks_upload=bool(source.get("blocks_upload", True)),
            blocks_scheduler=bool(source.get("blocks_scheduler", True)),
        )

    def _rate_limit_projection(self, payload: dict[str, Any]) -> ExternalSandboxRateLimitProjection:
        source = dict(payload or {})
        return ExternalSandboxRateLimitProjection(
            sandbox_validation_requests_allowed=bool(source.get("sandbox_validation_requests_allowed", False)),
            upload_requests_allowed=bool(source.get("upload_requests_allowed", False)),
            publish_requests_allowed=bool(source.get("publish_requests_allowed", False)),
            max_sandbox_validation_requests_per_minute=source.get("max_sandbox_validation_requests_per_minute"),
            max_upload_requests_per_hour=source.get("max_upload_requests_per_hour"),
            max_publish_requests_per_day=source.get("max_publish_requests_per_day"),
            burst_allowed=bool(source.get("burst_allowed", False)),
            rate_limit_exceeded=bool(source.get("rate_limit_exceeded", False)),
        )

    def _blocking_reasons(
        self,
        data: ExternalSandboxValidationEnvelopeInput,
        security_scan: ExternalSandboxEnvelopeSecurityScan,
        credential: ExternalSandboxCredentialProjection,
        kill_switch: ExternalSandboxKillSwitchProjection,
        rate_limit: ExternalSandboxRateLimitProjection,
        metadata: ExternalSandboxMetadataProjection,
    ) -> list[str]:
        reasons: list[str] = []
        if data.target_platform_id != TARGET_PLATFORM_ID:
            reasons.append("INVALID_TARGET_PLATFORM")
        if data.target_mode != TARGET_MODE:
            reasons.append("INVALID_TARGET_MODE")
        if data.modes != [TARGET_MODE]:
            reasons.append("MIXED_MODE_REJECTED")
        if data.provider_binding:
            reasons.append("IMPLICIT_PROVIDER_BINDING_REJECTED")
        if not data.run_id:
            reasons.append("MISSING_RUN_ID")
        if not data.content_id:
            reasons.append("MISSING_CONTENT_ID")
        if security_scan.secret_leakage_detected:
            reasons.append("SECRET_LEAKAGE_ATTEMPT")
        if security_scan.forbidden_field_detected:
            reasons.append("FORBIDDEN_FIELD_DETECTED")
        if security_scan.http_like_field_detected:
            reasons.append("HTTP_LIKE_FIELD_DETECTED")
        if security_scan.executable_helper_detected:
            reasons.append("EXECUTABLE_HELPER_DETECTED")
        if security_scan.transport_payload_detected:
            reasons.append("TRANSPORT_PAYLOAD_SHAPE_DETECTED")
        if credential.credential_status not in ALLOWED_CREDENTIAL_STATUSES:
            reasons.append("PUBLISHER_CREDENTIAL_VALIDATION_FAILED")
        elif credential.credential_status == "missing":
            reasons.append("PUBLISHER_CREDENTIALS_MISSING")
        elif credential.credential_status == "invalid_shape":
            reasons.append("PUBLISHER_CREDENTIAL_VALIDATION_FAILED")
        if kill_switch.active or kill_switch.missing:
            reasons.append("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE")
        if not kill_switch.blocks_publish_attempt:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_ATTEMPT")
        if (
            rate_limit.sandbox_validation_requests_allowed
            or rate_limit.upload_requests_allowed
            or rate_limit.publish_requests_allowed
        ):
            reasons.append("RATE_LIMIT_REQUESTS_NOT_AUTHORIZED")
        if rate_limit.rate_limit_exceeded:
            reasons.append("PUBLISHER_RATE_LIMIT_EXCEEDED")
        if (
            rate_limit.max_sandbox_validation_requests_per_minute is not None
            or rate_limit.max_upload_requests_per_hour is not None
            or rate_limit.max_publish_requests_per_day is not None
        ):
            reasons.append("RATE_LIMIT_DISABLED_STATE_AMBIGUOUS")
        qc_status = (data.qc_status or "UNKNOWN").strip().upper()
        if not data.qc_trace_ref:
            reasons.append("MISSING_QC_TRACE")
        if qc_status == "REJECT":
            reasons.append("QC_REJECTED")
        if qc_status == "HOLD":
            reasons.append("QC_HOLD")
        if data.qc_publishable is not True:
            reasons.append("QC_NOT_PUBLISHABLE")
        if (data.account_health_decision or "UNKNOWN").strip().upper() == "HOLD":
            reasons.append("ACCOUNT_HEALTH_HOLD")
        if not data.artifact_manifest_ref:
            reasons.append("MISSING_ARTIFACT_MANIFEST")
        if not data.metadata_payload_ref:
            reasons.append("MISSING_METADATA_PAYLOAD")
        if not data.account_health_trace_ref:
            reasons.append("MISSING_ACCOUNT_HEALTH_TRACE")
        if not data.strategy_ref:
            reasons.append("MISSING_STRATEGY_CONTEXT")
        if not data.publish_eligibility_trace_ref:
            reasons.append("MISSING_PUBLISH_ELIGIBILITY_TRACE")
        if not metadata.metadata_shape_valid:
            reasons.extend(self._metadata_reasons(data.metadata or {}))
        return list(dict.fromkeys(reasons))

    def _metadata_reasons(self, metadata: dict[str, Any]) -> list[str]:
        required = {
            "title",
            "description",
            "tags",
            "language",
            "visibility_mode",
            "account_id",
            "runtime_policy_ref",
            "metadata_trace_ref",
        }
        reasons = [f"MISSING_METADATA_FIELD:{key}" for key in sorted(required - set(metadata.keys()))]
        if metadata.get("visibility_mode") != "sandbox_only":
            reasons.append("PUBLIC_VISIBILITY_FORBIDDEN")
        return reasons

    def _incident_hooks(
        self,
        data: ExternalSandboxValidationEnvelopeInput,
        blocking_reasons: list[str],
        security_scan: ExternalSandboxEnvelopeSecurityScan,
    ) -> list[ExternalSandboxEnvelopeIncidentHook]:
        incident_map = {
            "SECRET_LEAKAGE_ATTEMPT": "EXTERNAL_SANDBOX_ENVELOPE_SECRET_LEAKAGE_ATTEMPT",
            "FORBIDDEN_FIELD_DETECTED": "EXTERNAL_SANDBOX_ENVELOPE_FORBIDDEN_FIELD",
            "HTTP_LIKE_FIELD_DETECTED": "EXTERNAL_SANDBOX_ENVELOPE_HTTP_LIKE_FIELD",
            "EXECUTABLE_HELPER_DETECTED": "EXTERNAL_SANDBOX_ENVELOPE_EXECUTABLE_HELPER",
            "TRANSPORT_PAYLOAD_SHAPE_DETECTED": "EXTERNAL_SANDBOX_ENVELOPE_TRANSPORT_PAYLOAD_SHAPE",
            "MIXED_MODE_REJECTED": "EXTERNAL_SANDBOX_ENVELOPE_MIXED_MODE",
            "IMPLICIT_PROVIDER_BINDING_REJECTED": "EXTERNAL_SANDBOX_ENVELOPE_PROVIDER_BINDING",
            "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE": "EXTERNAL_SANDBOX_ENVELOPE_KILL_SWITCH_BLOCK",
            "PUBLISHER_CREDENTIALS_MISSING": "EXTERNAL_SANDBOX_ENVELOPE_CREDENTIALS_MISSING",
            "ACCOUNT_HEALTH_HOLD": "ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH",
            "QC_REJECTED": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "QC_HOLD": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "QC_NOT_PUBLISHABLE": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
        }
        hooks: list[ExternalSandboxEnvelopeIncidentHook] = []
        seen: set[str] = set()
        for reason in blocking_reasons:
            incident_type = incident_map.get(reason)
            if not incident_type or incident_type in seen:
                continue
            seen.add(incident_type)
            hooks.append(
                ExternalSandboxEnvelopeIncidentHook(
                    incident_type=incident_type,
                    severity="critical" if reason in {"SECRET_LEAKAGE_ATTEMPT", "FORBIDDEN_FIELD_DETECTED"} else "warning",
                    run_id=data.run_id,
                    content_id=data.content_id,
                    target_platform_id=TARGET_PLATFORM_ID,
                    target_mode=TARGET_MODE,
                    rationale=[self._incident_rationale(reason, security_scan)],
                )
            )
        return hooks

    def _incident_rationale(self, reason: str, security_scan: ExternalSandboxEnvelopeSecurityScan) -> str:
        if reason == "SECRET_LEAKAGE_ATTEMPT":
            return "Secret-like field names were detected and values were not copied."
        if reason == "FORBIDDEN_FIELD_DETECTED":
            return "Forbidden publish or prediction fields were detected and values were not copied."
        if reason == "HTTP_LIKE_FIELD_DETECTED":
            return "HTTP-like field names are not allowed in a non-transportable validation envelope."
        if reason == "TRANSPORT_PAYLOAD_SHAPE_DETECTED":
            return "Transport-shaped input was detected and the envelope remains non-transportable."
        return f"{reason} blocked external sandbox envelope eligibility."

    def _validation_rationale(self, blocking_reasons: list[str]) -> list[str]:
        rationale = [
            "Envelope is schema/audit validation only.",
            "External call, upload, scheduler and real publish remain unauthorized.",
        ]
        if blocking_reasons:
            rationale.append("Blocking reasons are explicit and do not authorize execution.")
        else:
            rationale.append("No dependency blockers found, but external sandbox validation remains unauthorized.")
        return rationale

    def deterministic_audit_json(self, envelope: ExternalSandboxValidationEnvelope) -> str:
        return json.dumps(envelope.to_dict(), sort_keys=True, ensure_ascii=True, separators=(",", ":"))
