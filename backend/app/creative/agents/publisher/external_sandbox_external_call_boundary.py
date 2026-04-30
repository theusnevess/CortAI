from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.publisher.sandbox_contracts import (
    PRODUCTION_RESIDUALS,
    SANDBOX_TARGET_MODE,
    SANDBOX_TARGET_PLATFORM_ID,
)


BOUNDARY_VERSION = "external_sandbox_external_call_boundary_v1"
BOUNDARY_TYPE = "pre_execution_external_call_boundary"
BOUNDARY_STATE = "external_call_absent"
TARGET_PLATFORM_ID = SANDBOX_TARGET_PLATFORM_ID
TARGET_MODE = SANDBOX_TARGET_MODE
BOUNDARY_STATEMENT = "External sandbox external-call boundary is a pre-execution guard only."
GUARD_CONTRACT_VERSION = "external_sandbox_external_call_guard_v1"
GUARD_STATE = "blocking_only"
ALLOWED_CREDENTIAL_STATUSES = {"present", "missing", "invalid_shape", "not_checked"}
BOUNDARY_RESIDUALS = [
    *PRODUCTION_RESIDUALS,
    "EXTERNAL_CALL_NOT_IMPLEMENTED",
    "EXTERNAL_SANDBOX_EXECUTION_NOT_AUTHORIZED",
]


@dataclass(frozen=True)
class ExternalSandboxExternalCallBoundaryInput:
    run_id: str
    content_id: str
    target_platform_id: str = TARGET_PLATFORM_ID
    target_mode: str = TARGET_MODE
    credential_status: str = "not_checked"
    credential_payload: dict[str, Any] = field(default_factory=dict)
    kill_switch_status: dict[str, Any] = field(default_factory=dict)
    rate_limit_status: dict[str, Any] = field(default_factory=dict)
    external_call_requested: bool = False
    http_client_requested: bool = False
    platform_sdk_requested: bool = False
    endpoint_requested: bool = False
    dns_network_requested: bool = False
    api_call_requested: bool = False
    request_transformation_requested: bool = False
    upload_requested: bool = False
    scheduler_requested: bool = False
    publish_requested: bool = False
    url_requested: bool = False
    platform_content_id_requested: bool = False
    receipt_requested: bool = False
    credential_value_access_requested: bool = False
    authorization_header_requested: bool = False
    success_claimed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxExternalCallGuardContract:
    guard_contract_version: str
    guard_state: str
    kill_switch_required: bool
    kill_switch_active: bool
    kill_switch_missing: bool
    kill_switch_blocks_publish_attempt: bool
    kill_switch_blocks_external_calls: bool
    kill_switch_blocks_upload: bool
    kill_switch_blocks_scheduler: bool
    rate_limit_required: bool
    sandbox_validation_requests_allowed: bool
    upload_requests_allowed: bool
    publish_requests_allowed: bool
    disabled_rate_limits_mean_not_authorized: bool
    external_call_authorized: bool
    guard_pass_means_external_success: bool
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxExternalCallBoundaryIncidentHook:
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
class ExternalSandboxExternalCallBoundary:
    boundary_version: str
    boundary_type: str
    boundary_state: str
    run_id: str
    content_id: str
    target_platform_id: str
    target_mode: str
    execution_capability: str
    transport_capability: str
    client_capability: str
    endpoint_capability: str
    non_transportable: bool
    offline_only: bool
    pre_execution_only: bool
    external_call_implemented: bool
    external_call_authorized: bool
    http_client_present: bool
    http_client_allowed: bool
    platform_sdk_present: bool
    platform_sdk_allowed: bool
    endpoint_present: bool
    endpoint_allowed: bool
    dns_network_present: bool
    dns_network_allowed: bool
    api_call_present: bool
    api_call_allowed: bool
    request_transformation_present: bool
    request_transformation_authorized: bool
    upload_present: bool
    upload_authorized: bool
    scheduler_present: bool
    scheduler_authorized: bool
    publish_present: bool
    real_publish_authorized: bool
    url_present: bool
    url_emission_authorized: bool
    platform_content_id_present: bool
    platform_content_id_authorized: bool
    receipt_present: bool
    receipt_authorized: bool
    credential_value_access_present: bool
    credential_value_access_authorized: bool
    authorization_header_present: bool
    authorization_header_authorized: bool
    fake_success_detected: bool
    production_residuals_closed: bool
    credential_status: str
    guard_contract: dict[str, Any]
    blocking_reasons: list[str]
    warnings: list[str]
    incident_hooks: list[dict[str, Any]]
    residual_monitoring: list[str]
    rationale: list[str]
    boundary_statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExternalSandboxExternalCallBoundaryBuilder:
    """Builds a non-executable boundary marker for the external-call edge."""

    _SURFACE_BLOCKS: tuple[tuple[str, str, str], ...] = (
        ("external_call_requested", "EXTERNAL_CALL_SURFACE_REJECTED", "EXTERNAL_SANDBOX_EXTERNAL_CALL_ATTEMPT"),
        ("http_client_requested", "HTTP_CLIENT_SURFACE_REJECTED", "EXTERNAL_SANDBOX_HTTP_CLIENT_ATTEMPT"),
        ("platform_sdk_requested", "PLATFORM_SDK_SURFACE_REJECTED", "EXTERNAL_SANDBOX_PLATFORM_SDK_ATTEMPT"),
        ("endpoint_requested", "ENDPOINT_SURFACE_REJECTED", "EXTERNAL_SANDBOX_ENDPOINT_ATTEMPT"),
        ("dns_network_requested", "DNS_NETWORK_SURFACE_REJECTED", "EXTERNAL_SANDBOX_NETWORK_ATTEMPT"),
        ("api_call_requested", "API_CALL_SURFACE_REJECTED", "EXTERNAL_SANDBOX_API_CALL_ATTEMPT"),
        (
            "request_transformation_requested",
            "REQUEST_TRANSFORMATION_SURFACE_REJECTED",
            "EXTERNAL_SANDBOX_REQUEST_TRANSFORMATION_ATTEMPT",
        ),
        ("upload_requested", "UPLOAD_SURFACE_REJECTED", "EXTERNAL_SANDBOX_UPLOAD_ATTEMPT"),
        ("scheduler_requested", "SCHEDULER_SURFACE_REJECTED", "EXTERNAL_SANDBOX_SCHEDULER_ATTEMPT"),
        ("publish_requested", "PUBLISH_SURFACE_REJECTED", "EXTERNAL_SANDBOX_PUBLISH_ATTEMPT"),
        ("url_requested", "URL_EMISSION_REJECTED", "EXTERNAL_SANDBOX_URL_ATTEMPT"),
        (
            "platform_content_id_requested",
            "PLATFORM_CONTENT_ID_REJECTED",
            "EXTERNAL_SANDBOX_PLATFORM_CONTENT_ID_ATTEMPT",
        ),
        ("receipt_requested", "RECEIPT_REJECTED", "EXTERNAL_SANDBOX_RECEIPT_ATTEMPT"),
        (
            "credential_value_access_requested",
            "CREDENTIAL_VALUE_ACCESS_REJECTED",
            "EXTERNAL_SANDBOX_CREDENTIAL_VALUE_ACCESS_ATTEMPT",
        ),
        (
            "authorization_header_requested",
            "AUTHORIZATION_HEADER_REJECTED",
            "EXTERNAL_SANDBOX_AUTHORIZATION_HEADER_ATTEMPT",
        ),
        ("success_claimed", "FAKE_SUCCESS_REJECTED", "EXTERNAL_SANDBOX_FAKE_SUCCESS_ATTEMPT"),
    )

    def build(self, data: ExternalSandboxExternalCallBoundaryInput) -> ExternalSandboxExternalCallBoundary:
        guard_contract = self._guard_contract(data)
        blocking_reasons = self._blocking_reasons(data, guard_contract)
        return ExternalSandboxExternalCallBoundary(
            boundary_version=BOUNDARY_VERSION,
            boundary_type=BOUNDARY_TYPE,
            boundary_state=BOUNDARY_STATE,
            run_id=data.run_id,
            content_id=data.content_id,
            target_platform_id=TARGET_PLATFORM_ID,
            target_mode=TARGET_MODE,
            execution_capability="none",
            transport_capability="none",
            client_capability="none",
            endpoint_capability="none",
            non_transportable=True,
            offline_only=True,
            pre_execution_only=True,
            external_call_implemented=False,
            external_call_authorized=False,
            http_client_present=False,
            http_client_allowed=False,
            platform_sdk_present=False,
            platform_sdk_allowed=False,
            endpoint_present=False,
            endpoint_allowed=False,
            dns_network_present=False,
            dns_network_allowed=False,
            api_call_present=False,
            api_call_allowed=False,
            request_transformation_present=False,
            request_transformation_authorized=False,
            upload_present=False,
            upload_authorized=False,
            scheduler_present=False,
            scheduler_authorized=False,
            publish_present=False,
            real_publish_authorized=False,
            url_present=False,
            url_emission_authorized=False,
            platform_content_id_present=False,
            platform_content_id_authorized=False,
            receipt_present=False,
            receipt_authorized=False,
            credential_value_access_present=False,
            credential_value_access_authorized=False,
            authorization_header_present=False,
            authorization_header_authorized=False,
            fake_success_detected=False,
            production_residuals_closed=False,
            credential_status=self._credential_status(data.credential_status),
            guard_contract=guard_contract.to_dict(),
            blocking_reasons=blocking_reasons,
            warnings=["EXTERNAL_CALL_BOUNDARY_PRE_EXECUTION_ONLY"],
            incident_hooks=[hook.to_dict() for hook in self._incident_hooks(data, blocking_reasons)],
            residual_monitoring=list(BOUNDARY_RESIDUALS),
            rationale=self._rationale(blocking_reasons),
            boundary_statement=BOUNDARY_STATEMENT,
        )

    def deterministic_audit_json(self, boundary: ExternalSandboxExternalCallBoundary) -> str:
        return json.dumps(boundary.to_dict(), sort_keys=True, ensure_ascii=True, separators=(",", ":"))

    def _credential_status(self, status: str) -> str:
        normalized = (status or "not_checked").strip().lower() or "not_checked"
        return normalized if normalized in ALLOWED_CREDENTIAL_STATUSES else "invalid_shape"

    def _guard_contract(
        self,
        data: ExternalSandboxExternalCallBoundaryInput,
    ) -> ExternalSandboxExternalCallGuardContract:
        kill = dict(data.kill_switch_status or {})
        rate = dict(data.rate_limit_status or {})
        return ExternalSandboxExternalCallGuardContract(
            guard_contract_version=GUARD_CONTRACT_VERSION,
            guard_state=GUARD_STATE,
            kill_switch_required=True,
            kill_switch_active=bool(kill.get("active", False)),
            kill_switch_missing=bool(kill.get("missing", False)),
            kill_switch_blocks_publish_attempt=bool(kill.get("blocks_publish_attempt", True)),
            kill_switch_blocks_external_calls=bool(kill.get("blocks_external_calls", True)),
            kill_switch_blocks_upload=bool(kill.get("blocks_upload", True)),
            kill_switch_blocks_scheduler=bool(kill.get("blocks_scheduler", True)),
            rate_limit_required=True,
            sandbox_validation_requests_allowed=bool(rate.get("sandbox_validation_requests_allowed", False)),
            upload_requests_allowed=bool(rate.get("upload_requests_allowed", False)),
            publish_requests_allowed=bool(rate.get("publish_requests_allowed", False)),
            disabled_rate_limits_mean_not_authorized=True,
            external_call_authorized=False,
            guard_pass_means_external_success=False,
            rationale=[
                "Guard contract records blocking policy only.",
                "Passing guard checks does not create an external-call permission.",
            ],
        )

    def _blocking_reasons(
        self,
        data: ExternalSandboxExternalCallBoundaryInput,
        guard_contract: ExternalSandboxExternalCallGuardContract,
    ) -> list[str]:
        reasons: list[str] = []
        if data.target_platform_id != TARGET_PLATFORM_ID:
            reasons.append("INVALID_TARGET_PLATFORM")
        if data.target_mode != TARGET_MODE:
            reasons.append("INVALID_TARGET_MODE")
        credential_status = self._credential_status(data.credential_status)
        if credential_status == "missing":
            reasons.append("PUBLISHER_CREDENTIALS_MISSING")
        if credential_status == "invalid_shape":
            reasons.append("PUBLISHER_CREDENTIAL_VALIDATION_FAILED")
        if self._credential_payload_has_value(data.credential_payload):
            reasons.append("CREDENTIAL_VALUE_ACCESS_REJECTED")
        if guard_contract.kill_switch_active or guard_contract.kill_switch_missing:
            reasons.append("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE")
        if not guard_contract.kill_switch_blocks_publish_attempt:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_ATTEMPT")
        if not guard_contract.kill_switch_blocks_external_calls:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_EXTERNAL_CALLS")
        if not guard_contract.kill_switch_blocks_upload:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_UPLOAD")
        if not guard_contract.kill_switch_blocks_scheduler:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_SCHEDULER")
        if (
            guard_contract.sandbox_validation_requests_allowed
            or guard_contract.upload_requests_allowed
            or guard_contract.publish_requests_allowed
        ):
            reasons.append("RATE_LIMIT_REQUESTS_NOT_AUTHORIZED")
        for field_name, reason, _incident_type in self._SURFACE_BLOCKS:
            if bool(getattr(data, field_name)):
                reasons.append(reason)
        return list(dict.fromkeys(reasons))

    def _credential_payload_has_value(self, payload: dict[str, Any]) -> bool:
        if not payload:
            return False
        allowed_status_keys = {"credential_status", "credential_source", "secret_scope_class"}
        return any(key not in allowed_status_keys for key in payload.keys())

    def _incident_hooks(
        self,
        data: ExternalSandboxExternalCallBoundaryInput,
        blocking_reasons: list[str],
    ) -> list[ExternalSandboxExternalCallBoundaryIncidentHook]:
        incident_by_reason = {reason: incident_type for _field, reason, incident_type in self._SURFACE_BLOCKS}
        incident_by_reason.update(
            {
                "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE": "EXTERNAL_SANDBOX_EXTERNAL_CALL_KILL_SWITCH_BLOCK",
                "PUBLISHER_CREDENTIALS_MISSING": "EXTERNAL_SANDBOX_EXTERNAL_CALL_CREDENTIALS_MISSING",
                "PUBLISHER_CREDENTIAL_VALIDATION_FAILED": "EXTERNAL_SANDBOX_EXTERNAL_CALL_CREDENTIALS_INVALID",
                "CREDENTIAL_VALUE_ACCESS_REJECTED": "EXTERNAL_SANDBOX_CREDENTIAL_VALUE_ACCESS_ATTEMPT",
                "RATE_LIMIT_REQUESTS_NOT_AUTHORIZED": "EXTERNAL_SANDBOX_EXTERNAL_CALL_RATE_LIMIT_BLOCK",
            }
        )
        hooks: list[ExternalSandboxExternalCallBoundaryIncidentHook] = []
        seen: set[str] = set()
        for reason in blocking_reasons:
            incident_type = incident_by_reason.get(reason)
            if not incident_type or incident_type in seen:
                continue
            seen.add(incident_type)
            hooks.append(
                ExternalSandboxExternalCallBoundaryIncidentHook(
                    incident_type=incident_type,
                    severity="critical" if reason.endswith("REJECTED") or "FAKE_SUCCESS" in reason else "warning",
                    run_id=data.run_id,
                    content_id=data.content_id,
                    target_platform_id=TARGET_PLATFORM_ID,
                    target_mode=TARGET_MODE,
                    rationale=[f"{reason} keeps the external-call boundary non-executing."],
                )
            )
        return hooks

    def _rationale(self, blocking_reasons: list[str]) -> list[str]:
        rationale = [
            "Boundary marker is offline, pre-execution and non-transportable.",
            "No client, endpoint, API call, upload, scheduler, publish, URL, platform ID or receipt is created.",
        ]
        if blocking_reasons:
            rationale.append("Blocking reasons are explicit and do not authorize external execution.")
        else:
            rationale.append("No local blockers found, but external execution remains absent and unauthorized.")
        return rationale
