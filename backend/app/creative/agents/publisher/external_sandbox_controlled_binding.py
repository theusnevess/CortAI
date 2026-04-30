from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.publisher.external_sandbox_validation_envelope import TARGET_MODE, TARGET_PLATFORM_ID
from app.creative.agents.publisher.sandbox_contracts import PRODUCTION_RESIDUALS, SANDBOX_RATE_LIMIT_POLICY_VERSION


BINDING_VERSION = "external_sandbox_controlled_binding_v1"
BINDING_TYPE = "pre_execution_controlled_binding"
PROVIDER_BINDING_STATUS = "planned_not_active"
PROVIDER_IDENTITY_CLASS = "abstract_sandbox_target"
BOUNDARY_STATEMENT = "Controlled binding is pre-execution and cannot call external services."
ALLOWED_CREDENTIAL_STATUSES = {"present", "missing", "invalid_shape", "not_checked"}


@dataclass(frozen=True)
class ExternalSandboxControlledBindingInput:
    run_id: str
    content_id: str
    qc_trace_ref: str | None
    account_health_trace_ref: str | None
    qc_status: str | None = "APPROVE"
    qc_publishable: bool | None = True
    account_health_decision: str | None = "SAFE"
    target_platform_id: str = TARGET_PLATFORM_ID
    target_mode: str = TARGET_MODE
    provider_binding: str | None = None
    provider_identity_class: str = PROVIDER_IDENTITY_CLASS
    credential_status: str = "present"
    credential_payload: dict[str, Any] = field(default_factory=dict)
    kill_switch_status: dict[str, Any] = field(default_factory=dict)
    rate_limit_status: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxBindingCredentialStatus:
    credential_status: str
    credential_source: str = "environment_or_secret_manager"
    secret_values_logged: bool = False
    secret_values_persisted: bool = False
    secret_values_accessed: bool = False
    secret_scope_class: str = "sandbox_binding_planning_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxBindingSafetyPolicy:
    kill_switch_required: bool = True
    kill_switch_name: str = "PUBLISHER_PLATFORM_KILL_SWITCH"
    kill_switch_active: bool = False
    kill_switch_missing: bool = False
    kill_switch_blocks_publish_attempt: bool = True
    kill_switch_blocks_external_calls: bool = True
    kill_switch_blocks_upload: bool = True
    kill_switch_blocks_scheduler: bool = True
    rate_limit_policy_required: bool = True
    rate_limit_policy_version: str = SANDBOX_RATE_LIMIT_POLICY_VERSION
    sandbox_validation_requests_allowed: bool = False
    upload_requests_allowed: bool = False
    publish_requests_allowed: bool = False
    max_sandbox_validation_requests_per_minute: int | None = None
    max_upload_requests_per_hour: int | None = None
    max_publish_requests_per_day: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxControlledBindingIncidentHook:
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
class ExternalSandboxControlledBinding:
    binding_version: str
    binding_type: str
    run_id: str
    content_id: str
    target_platform_id: str
    target_mode: str
    binding_active: bool
    execution_authority: str
    transport_authority: str
    provider_binding_status: str
    provider_identity_class: str
    credential_status_required: str
    credential_status: dict[str, Any]
    safety_policy: dict[str, Any]
    qc_dependency_required: bool
    account_health_dependency_required: bool
    qc_trace_ref: str | None
    account_health_trace_ref: str | None
    endpoint_defined: bool
    http_client_defined: bool
    platform_sdk_defined: bool
    network_access_defined: bool
    api_call_defined: bool
    upload_defined: bool
    scheduler_defined: bool
    publish_defined: bool
    receipt_defined: bool
    production_identity_defined: bool
    external_call_authorized: bool
    http_client_allowed: bool
    platform_sdk_allowed: bool
    endpoint_allowed: bool
    network_access_allowed: bool
    api_call_allowed: bool
    upload_authorized: bool
    scheduler_authorized: bool
    real_publish_authorized: bool
    url_authorized: bool
    platform_content_id_authorized: bool
    receipt_authorized: bool
    credential_value_accessed: bool
    transformation_layer_authorized: bool
    blocking_reasons: list[str]
    warnings: list[str]
    incident_hooks: list[dict[str, Any]]
    rationale: list[str]
    residual_monitoring: list[str]
    boundary_statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExternalSandboxControlledBindingBuilder:
    """Builds a non-executable Publisher sandbox binding policy object."""

    def build(self, data: ExternalSandboxControlledBindingInput) -> ExternalSandboxControlledBinding:
        credential_status = self._credential_status(data.credential_status)
        safety_policy = self._safety_policy(data.kill_switch_status, data.rate_limit_status)
        blocking_reasons = self._blocking_reasons(data, credential_status, safety_policy)
        warnings = ["CONTROLLED_BINDING_PRE_EXECUTION_ONLY"]
        return ExternalSandboxControlledBinding(
            binding_version=BINDING_VERSION,
            binding_type=BINDING_TYPE,
            run_id=data.run_id,
            content_id=data.content_id,
            target_platform_id=TARGET_PLATFORM_ID,
            target_mode=TARGET_MODE,
            binding_active=False,
            execution_authority="none",
            transport_authority="none",
            provider_binding_status=PROVIDER_BINDING_STATUS,
            provider_identity_class=PROVIDER_IDENTITY_CLASS,
            credential_status_required="present",
            credential_status=credential_status.to_dict(),
            safety_policy=safety_policy.to_dict(),
            qc_dependency_required=True,
            account_health_dependency_required=True,
            qc_trace_ref=data.qc_trace_ref,
            account_health_trace_ref=data.account_health_trace_ref,
            endpoint_defined=False,
            http_client_defined=False,
            platform_sdk_defined=False,
            network_access_defined=False,
            api_call_defined=False,
            upload_defined=False,
            scheduler_defined=False,
            publish_defined=False,
            receipt_defined=False,
            production_identity_defined=False,
            external_call_authorized=False,
            http_client_allowed=False,
            platform_sdk_allowed=False,
            endpoint_allowed=False,
            network_access_allowed=False,
            api_call_allowed=False,
            upload_authorized=False,
            scheduler_authorized=False,
            real_publish_authorized=False,
            url_authorized=False,
            platform_content_id_authorized=False,
            receipt_authorized=False,
            credential_value_accessed=False,
            transformation_layer_authorized=False,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            incident_hooks=[hook.to_dict() for hook in self._incident_hooks(data, blocking_reasons)],
            rationale=self._rationale(blocking_reasons),
            residual_monitoring=list(PRODUCTION_RESIDUALS),
            boundary_statement=BOUNDARY_STATEMENT,
        )

    def deterministic_audit_json(self, binding: ExternalSandboxControlledBinding) -> str:
        return json.dumps(binding.to_dict(), sort_keys=True, ensure_ascii=True, separators=(",", ":"))

    def _credential_status(self, status: str) -> ExternalSandboxBindingCredentialStatus:
        normalized = (status or "not_checked").strip().lower() or "not_checked"
        return ExternalSandboxBindingCredentialStatus(credential_status=normalized)

    def _safety_policy(
        self,
        kill_switch: dict[str, Any],
        rate_limit: dict[str, Any],
    ) -> ExternalSandboxBindingSafetyPolicy:
        kill = dict(kill_switch or {})
        rate = dict(rate_limit or {})
        return ExternalSandboxBindingSafetyPolicy(
            kill_switch_active=bool(kill.get("active", False)),
            kill_switch_missing=bool(kill.get("missing", False)),
            kill_switch_blocks_publish_attempt=bool(kill.get("blocks_publish_attempt", True)),
            kill_switch_blocks_external_calls=bool(kill.get("blocks_external_calls", True)),
            kill_switch_blocks_upload=bool(kill.get("blocks_upload", True)),
            kill_switch_blocks_scheduler=bool(kill.get("blocks_scheduler", True)),
            sandbox_validation_requests_allowed=bool(rate.get("sandbox_validation_requests_allowed", False)),
            upload_requests_allowed=bool(rate.get("upload_requests_allowed", False)),
            publish_requests_allowed=bool(rate.get("publish_requests_allowed", False)),
            max_sandbox_validation_requests_per_minute=rate.get("max_sandbox_validation_requests_per_minute"),
            max_upload_requests_per_hour=rate.get("max_upload_requests_per_hour"),
            max_publish_requests_per_day=rate.get("max_publish_requests_per_day"),
        )

    def _blocking_reasons(
        self,
        data: ExternalSandboxControlledBindingInput,
        credential_status: ExternalSandboxBindingCredentialStatus,
        safety_policy: ExternalSandboxBindingSafetyPolicy,
    ) -> list[str]:
        reasons: list[str] = []
        if data.target_platform_id != TARGET_PLATFORM_ID:
            reasons.append("INVALID_TARGET_PLATFORM")
        if data.target_mode != TARGET_MODE:
            reasons.append("INVALID_TARGET_MODE")
        if data.provider_binding:
            reasons.append("IMPLICIT_PROVIDER_BINDING_REJECTED")
        if data.provider_identity_class != PROVIDER_IDENTITY_CLASS:
            reasons.append("PROVIDER_IDENTITY_CLASS_NOT_ABSTRACT")
        if credential_status.credential_status not in ALLOWED_CREDENTIAL_STATUSES:
            reasons.append("PUBLISHER_CREDENTIAL_VALIDATION_FAILED")
        elif credential_status.credential_status == "missing":
            reasons.append("PUBLISHER_CREDENTIALS_MISSING")
        elif credential_status.credential_status == "invalid_shape":
            reasons.append("PUBLISHER_CREDENTIAL_VALIDATION_FAILED")
        if self._credential_payload_has_value(data.credential_payload):
            reasons.append("CREDENTIAL_VALUE_ACCESS_REJECTED")
        qc_status = (data.qc_status or "UNKNOWN").strip().upper()
        if not data.qc_trace_ref:
            reasons.append("MISSING_QC_TRACE")
        if qc_status == "HOLD":
            reasons.append("QC_HOLD")
        if qc_status == "REJECT":
            reasons.append("QC_REJECTED")
        if data.qc_publishable is not True:
            reasons.append("QC_NOT_PUBLISHABLE")
        if not data.account_health_trace_ref:
            reasons.append("MISSING_ACCOUNT_HEALTH_TRACE")
        if (data.account_health_decision or "UNKNOWN").strip().upper() == "HOLD":
            reasons.append("ACCOUNT_HEALTH_HOLD")
        if safety_policy.kill_switch_active or safety_policy.kill_switch_missing:
            reasons.append("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE")
        if not safety_policy.kill_switch_blocks_publish_attempt:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_ATTEMPT")
        if not safety_policy.kill_switch_blocks_external_calls:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_EXTERNAL_CALLS")
        if not safety_policy.kill_switch_blocks_upload:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_UPLOAD")
        if not safety_policy.kill_switch_blocks_scheduler:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_SCHEDULER")
        if (
            safety_policy.sandbox_validation_requests_allowed
            or safety_policy.upload_requests_allowed
            or safety_policy.publish_requests_allowed
        ):
            reasons.append("RATE_LIMIT_REQUESTS_NOT_AUTHORIZED")
        if (
            safety_policy.max_sandbox_validation_requests_per_minute is not None
            or safety_policy.max_upload_requests_per_hour is not None
            or safety_policy.max_publish_requests_per_day is not None
        ):
            reasons.append("RATE_LIMIT_DISABLED_STATE_AMBIGUOUS")
        return list(dict.fromkeys(reasons))

    def _credential_payload_has_value(self, payload: dict[str, Any]) -> bool:
        if not payload:
            return False
        allowed_status_keys = {"credential_status", "credential_source", "secret_scope_class"}
        return any(key not in allowed_status_keys for key in payload.keys())

    def _incident_hooks(
        self,
        data: ExternalSandboxControlledBindingInput,
        blocking_reasons: list[str],
    ) -> list[ExternalSandboxControlledBindingIncidentHook]:
        incident_map = {
            "IMPLICIT_PROVIDER_BINDING_REJECTED": "EXTERNAL_SANDBOX_BINDING_IMPLICIT_PROVIDER_REJECTED",
            "PROVIDER_IDENTITY_CLASS_NOT_ABSTRACT": "EXTERNAL_SANDBOX_BINDING_PROVIDER_IDENTITY_REJECTED",
            "PUBLISHER_CREDENTIALS_MISSING": "EXTERNAL_SANDBOX_BINDING_CREDENTIALS_MISSING",
            "PUBLISHER_CREDENTIAL_VALIDATION_FAILED": "EXTERNAL_SANDBOX_BINDING_CREDENTIALS_INVALID",
            "CREDENTIAL_VALUE_ACCESS_REJECTED": "EXTERNAL_SANDBOX_BINDING_CREDENTIAL_VALUE_ACCESS_ATTEMPT",
            "ACCOUNT_HEALTH_HOLD": "ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH",
            "QC_HOLD": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "QC_REJECTED": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "QC_NOT_PUBLISHABLE": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE": "EXTERNAL_SANDBOX_BINDING_KILL_SWITCH_BLOCK",
            "RATE_LIMIT_REQUESTS_NOT_AUTHORIZED": "EXTERNAL_SANDBOX_BINDING_RATE_LIMIT_BLOCK",
            "RATE_LIMIT_DISABLED_STATE_AMBIGUOUS": "EXTERNAL_SANDBOX_BINDING_RATE_LIMIT_BLOCK",
        }
        hooks: list[ExternalSandboxControlledBindingIncidentHook] = []
        seen: set[str] = set()
        for reason in blocking_reasons:
            incident_type = incident_map.get(reason)
            if not incident_type or incident_type in seen:
                continue
            seen.add(incident_type)
            hooks.append(
                ExternalSandboxControlledBindingIncidentHook(
                    incident_type=incident_type,
                    severity="critical" if reason in {"CREDENTIAL_VALUE_ACCESS_REJECTED"} else "warning",
                    run_id=data.run_id,
                    content_id=data.content_id,
                    target_platform_id=TARGET_PLATFORM_ID,
                    target_mode=TARGET_MODE,
                    rationale=[f"{reason} keeps controlled binding inactive."],
                )
            )
        return hooks

    def _rationale(self, blocking_reasons: list[str]) -> list[str]:
        rationale = [
            "Controlled binding is pre-execution only.",
            "Binding remains inactive and does not authorize transport or publishing.",
        ]
        if blocking_reasons:
            rationale.append("Blocking reasons are explicit and keep execution authority at none.")
        else:
            rationale.append("No dependency blockers found, but binding remains planned_not_active.")
        return rationale
