from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.publisher.external_sandbox_external_call_boundary import BOUNDARY_RESIDUALS
from app.creative.agents.publisher.sandbox_contracts import SANDBOX_TARGET_MODE, SANDBOX_TARGET_PLATFORM_ID


GUARD_VERSION = "external_sandbox_pre_execution_guard_v1"
GUARD_TYPE = "external_call_pre_execution_blocker"
GUARD_STATE = "blocking_only"
TARGET_PLATFORM_ID = SANDBOX_TARGET_PLATFORM_ID
TARGET_MODE = SANDBOX_TARGET_MODE
BOUNDARY_STATEMENT = "Pre-execution guard blocks crossing attempts and does not create execution capability."
BLOCKED_FALSE_MEANING = "no_local_guard_block_found"
BLOCKED_TRUE_MEANING = "crossing_attempt_or_dependency_block_prevented"
ALLOWED_CREDENTIAL_STATUSES = {"present", "missing", "invalid_shape", "not_checked"}

CAPABILITY_REASON_CODES = {
    "external_call": "EXTERNAL_CALL_ATTEMPT_BLOCKED",
    "http_client": "HTTP_CLIENT_ATTEMPT_BLOCKED",
    "platform_sdk": "PLATFORM_SDK_ATTEMPT_BLOCKED",
    "endpoint": "ENDPOINT_ATTEMPT_BLOCKED",
    "dns_network": "DNS_NETWORK_ATTEMPT_BLOCKED",
    "api_call": "API_CALL_ATTEMPT_BLOCKED",
    "request_transformation": "REQUEST_TRANSFORMATION_ATTEMPT_BLOCKED",
    "upload": "UPLOAD_ATTEMPT_BLOCKED",
    "scheduler": "SCHEDULER_ATTEMPT_BLOCKED",
    "publish": "PUBLISH_ATTEMPT_BLOCKED",
    "url": "URL_EMISSION_ATTEMPT_BLOCKED",
    "platform_content_id": "PLATFORM_CONTENT_ID_ATTEMPT_BLOCKED",
    "receipt": "RECEIPT_ATTEMPT_BLOCKED",
    "credential_value_access": "CREDENTIAL_VALUE_ACCESS_ATTEMPT_BLOCKED",
    "authorization_header": "AUTHORIZATION_HEADER_ATTEMPT_BLOCKED",
    "fake_success": "FAKE_SUCCESS_ATTEMPT_BLOCKED",
}

CAPABILITY_INCIDENT_TYPES = {
    "external_call": "EXTERNAL_SANDBOX_PRE_EXECUTION_EXTERNAL_CALL_ATTEMPT",
    "http_client": "EXTERNAL_SANDBOX_PRE_EXECUTION_HTTP_CLIENT_ATTEMPT",
    "platform_sdk": "EXTERNAL_SANDBOX_PRE_EXECUTION_SDK_ATTEMPT",
    "endpoint": "EXTERNAL_SANDBOX_PRE_EXECUTION_ENDPOINT_ATTEMPT",
    "dns_network": "EXTERNAL_SANDBOX_PRE_EXECUTION_DNS_NETWORK_ATTEMPT",
    "api_call": "EXTERNAL_SANDBOX_PRE_EXECUTION_API_CALL_ATTEMPT",
    "request_transformation": "EXTERNAL_SANDBOX_PRE_EXECUTION_REQUEST_TRANSFORMATION_ATTEMPT",
    "upload": "EXTERNAL_SANDBOX_PRE_EXECUTION_UPLOAD_ATTEMPT",
    "scheduler": "EXTERNAL_SANDBOX_PRE_EXECUTION_SCHEDULER_ATTEMPT",
    "publish": "EXTERNAL_SANDBOX_PRE_EXECUTION_PUBLISH_ATTEMPT",
    "url": "EXTERNAL_SANDBOX_PRE_EXECUTION_URL_ATTEMPT",
    "platform_content_id": "EXTERNAL_SANDBOX_PRE_EXECUTION_PLATFORM_CONTENT_ID_ATTEMPT",
    "receipt": "EXTERNAL_SANDBOX_PRE_EXECUTION_RECEIPT_ATTEMPT",
    "credential_value_access": "EXTERNAL_SANDBOX_PRE_EXECUTION_CREDENTIAL_VALUE_ACCESS_ATTEMPT",
    "authorization_header": "EXTERNAL_SANDBOX_PRE_EXECUTION_AUTHORIZATION_HEADER_ATTEMPT",
    "fake_success": "EXTERNAL_SANDBOX_PRE_EXECUTION_FAKE_SUCCESS_ATTEMPT",
}


@dataclass(frozen=True)
class ExternalSandboxPreExecutionGuardInput:
    run_id: str
    content_id: str
    boundary_ref: str | None
    controlled_binding_ref: str | None
    validation_envelope_ref: str | None
    publish_eligibility_trace_ref: str | None
    qc_trace_ref: str | None
    account_health_trace_ref: str | None
    target_platform_id: str = TARGET_PLATFORM_ID
    target_mode: str = TARGET_MODE
    attempted_capabilities: dict[str, bool] = field(default_factory=dict)
    dependency_status: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxPreExecutionIncidentHook:
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
class ExternalSandboxPreExecutionGuardTrace:
    boundary_ref: str | None
    crossing_attempt_detected: bool
    blocked_capabilities: list[str]
    dependency_blocks: list[str]
    authorization_summary: dict[str, bool]
    incident_hooks: list[dict[str, Any]]
    residual_monitoring: list[str]
    boundary_statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxPreExecutionGuardResult:
    guard_version: str
    guard_type: str
    guard_state: str
    run_id: str
    content_id: str
    target_platform_id: str
    target_mode: str
    crossing_attempt_detected: bool
    blocked: bool
    blocked_meaning: str
    block_level: str
    blocked_capabilities: list[str]
    dependency_blocks: list[str]
    external_call_authorized: bool
    http_client_authorized: bool
    platform_sdk_authorized: bool
    endpoint_authorized: bool
    dns_network_authorized: bool
    api_call_authorized: bool
    request_transformation_authorized: bool
    upload_authorized: bool
    scheduler_authorized: bool
    publish_authorized: bool
    url_authorized: bool
    platform_content_id_authorized: bool
    receipt_authorized: bool
    credential_value_access_authorized: bool
    authorization_header_authorized: bool
    blocked_false_does_not_authorize: bool
    guard_pass_does_not_mean_success: bool
    production_residuals_closed: bool
    incident_hooks: list[dict[str, Any]]
    pre_execution_guard_trace: dict[str, Any]
    rationale: list[str]
    residual_monitoring: list[str]
    boundary_statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExternalSandboxPreExecutionGuard:
    """Blocks external-call boundary crossing attempts without creating execution capability."""

    def evaluate(self, data: ExternalSandboxPreExecutionGuardInput) -> ExternalSandboxPreExecutionGuardResult:
        blocked_capabilities = self._blocked_capabilities(data.attempted_capabilities)
        dependency_blocks = self._dependency_blocks(data)
        crossing_attempt_detected = bool(blocked_capabilities)
        blocked = crossing_attempt_detected or bool(dependency_blocks)
        block_level = self._block_level(blocked_capabilities, dependency_blocks)
        incident_hooks = self._incident_hooks(data, blocked_capabilities, dependency_blocks)
        auth_summary = self._authorization_summary()
        trace = ExternalSandboxPreExecutionGuardTrace(
            boundary_ref=data.boundary_ref,
            crossing_attempt_detected=crossing_attempt_detected,
            blocked_capabilities=blocked_capabilities,
            dependency_blocks=dependency_blocks,
            authorization_summary=auth_summary,
            incident_hooks=[hook.to_dict() for hook in incident_hooks],
            residual_monitoring=list(BOUNDARY_RESIDUALS),
            boundary_statement=BOUNDARY_STATEMENT,
        )
        return ExternalSandboxPreExecutionGuardResult(
            guard_version=GUARD_VERSION,
            guard_type=GUARD_TYPE,
            guard_state=GUARD_STATE,
            run_id=data.run_id,
            content_id=data.content_id,
            target_platform_id=TARGET_PLATFORM_ID,
            target_mode=TARGET_MODE,
            crossing_attempt_detected=crossing_attempt_detected,
            blocked=blocked,
            blocked_meaning=BLOCKED_TRUE_MEANING if blocked else BLOCKED_FALSE_MEANING,
            block_level=block_level,
            blocked_capabilities=blocked_capabilities,
            dependency_blocks=dependency_blocks,
            external_call_authorized=False,
            http_client_authorized=False,
            platform_sdk_authorized=False,
            endpoint_authorized=False,
            dns_network_authorized=False,
            api_call_authorized=False,
            request_transformation_authorized=False,
            upload_authorized=False,
            scheduler_authorized=False,
            publish_authorized=False,
            url_authorized=False,
            platform_content_id_authorized=False,
            receipt_authorized=False,
            credential_value_access_authorized=False,
            authorization_header_authorized=False,
            blocked_false_does_not_authorize=True,
            guard_pass_does_not_mean_success=True,
            production_residuals_closed=False,
            incident_hooks=[hook.to_dict() for hook in incident_hooks],
            pre_execution_guard_trace=trace.to_dict(),
            rationale=self._rationale(blocked, blocked_capabilities, dependency_blocks),
            residual_monitoring=list(BOUNDARY_RESIDUALS),
            boundary_statement=BOUNDARY_STATEMENT,
        )

    def deterministic_audit_json(self, result: ExternalSandboxPreExecutionGuardResult) -> str:
        return json.dumps(result.to_dict(), sort_keys=True, ensure_ascii=True, separators=(",", ":"))

    def _blocked_capabilities(self, attempted: dict[str, bool]) -> list[str]:
        attempted = dict(attempted or {})
        return [
            CAPABILITY_REASON_CODES[name]
            for name in CAPABILITY_REASON_CODES
            if bool(attempted.get(name, False))
        ]

    def _dependency_blocks(self, data: ExternalSandboxPreExecutionGuardInput) -> list[str]:
        status = dict(data.dependency_status or {})
        reasons: list[str] = []
        if not data.boundary_ref:
            reasons.append("MISSING_BOUNDARY_REF")
        if not data.controlled_binding_ref:
            reasons.append("MISSING_CONTROLLED_BINDING_REF")
        if not data.validation_envelope_ref:
            reasons.append("MISSING_VALIDATION_ENVELOPE_REF")
        if not data.publish_eligibility_trace_ref:
            reasons.append("MISSING_PUBLISH_ELIGIBILITY_TRACE")
        if not data.qc_trace_ref:
            reasons.append("MISSING_QC_TRACE")
        if not data.account_health_trace_ref:
            reasons.append("MISSING_ACCOUNT_HEALTH_TRACE")
        qc_status = str(status.get("qc_status", "UNKNOWN")).strip().upper()
        if qc_status == "HOLD":
            reasons.append("QC_HOLD")
        if qc_status == "REJECT":
            reasons.append("QC_REJECTED")
        if status.get("qc_publishable", True) is not True:
            reasons.append("QC_NOT_PUBLISHABLE")
        if str(status.get("account_health_decision", "UNKNOWN")).strip().upper() == "HOLD":
            reasons.append("ACCOUNT_HEALTH_HOLD")
        credential_status = str(status.get("credential_status", "not_checked")).strip().lower() or "not_checked"
        if credential_status not in ALLOWED_CREDENTIAL_STATUSES or credential_status == "invalid_shape":
            reasons.append("PUBLISHER_CREDENTIAL_VALIDATION_FAILED")
        if credential_status == "missing":
            reasons.append("PUBLISHER_CREDENTIALS_MISSING")
        if bool(status.get("kill_switch_active", False)):
            reasons.append("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE")
        if bool(status.get("kill_switch_missing", False)):
            reasons.append("PUBLISHER_PLATFORM_KILL_SWITCH_MISSING")
        if status.get("kill_switch_blocks_external_calls", True) is not True:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_EXTERNAL_CALLS")
        if status.get("kill_switch_blocks_upload", True) is not True:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_UPLOAD")
        if status.get("kill_switch_blocks_scheduler", True) is not True:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_SCHEDULER")
        if bool(status.get("rate_limit_requests_allowed", False)):
            reasons.append("RATE_LIMIT_REQUESTS_NOT_AUTHORIZED")
        if data.target_platform_id != TARGET_PLATFORM_ID:
            reasons.append("INVALID_TARGET_PLATFORM")
        if data.target_mode != TARGET_MODE:
            reasons.append("INVALID_TARGET_MODE")
        return list(dict.fromkeys(reasons))

    def _authorization_summary(self) -> dict[str, bool]:
        return {
            "external_call_authorized": False,
            "http_client_authorized": False,
            "platform_sdk_authorized": False,
            "endpoint_authorized": False,
            "dns_network_authorized": False,
            "api_call_authorized": False,
            "request_transformation_authorized": False,
            "upload_authorized": False,
            "scheduler_authorized": False,
            "publish_authorized": False,
            "url_authorized": False,
            "platform_content_id_authorized": False,
            "receipt_authorized": False,
            "credential_value_access_authorized": False,
            "authorization_header_authorized": False,
        }

    def _block_level(self, blocked_capabilities: list[str], dependency_blocks: list[str]) -> str:
        if any(
            reason in blocked_capabilities
            for reason in {
                "EXTERNAL_CALL_ATTEMPT_BLOCKED",
                "HTTP_CLIENT_ATTEMPT_BLOCKED",
                "PLATFORM_SDK_ATTEMPT_BLOCKED",
                "ENDPOINT_ATTEMPT_BLOCKED",
                "API_CALL_ATTEMPT_BLOCKED",
                "PUBLISH_ATTEMPT_BLOCKED",
                "FAKE_SUCCESS_ATTEMPT_BLOCKED",
            }
        ):
            return "critical"
        if blocked_capabilities or dependency_blocks:
            return "warning"
        return "none"

    def _incident_hooks(
        self,
        data: ExternalSandboxPreExecutionGuardInput,
        blocked_capabilities: list[str],
        dependency_blocks: list[str],
    ) -> list[ExternalSandboxPreExecutionIncidentHook]:
        hooks: list[ExternalSandboxPreExecutionIncidentHook] = []
        incident_by_reason = {reason: CAPABILITY_INCIDENT_TYPES[name] for name, reason in CAPABILITY_REASON_CODES.items()}
        dependency_incidents = {
            "QC_HOLD": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "QC_REJECTED": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "QC_NOT_PUBLISHABLE": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "ACCOUNT_HEALTH_HOLD": "ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH",
            "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE": "EXTERNAL_SANDBOX_PRE_EXECUTION_KILL_SWITCH_BLOCK",
            "PUBLISHER_PLATFORM_KILL_SWITCH_MISSING": "EXTERNAL_SANDBOX_PRE_EXECUTION_KILL_SWITCH_BLOCK",
            "PUBLISHER_CREDENTIALS_MISSING": "EXTERNAL_SANDBOX_PRE_EXECUTION_CREDENTIALS_MISSING",
            "PUBLISHER_CREDENTIAL_VALIDATION_FAILED": "EXTERNAL_SANDBOX_PRE_EXECUTION_CREDENTIALS_INVALID",
            "RATE_LIMIT_REQUESTS_NOT_AUTHORIZED": "EXTERNAL_SANDBOX_PRE_EXECUTION_RATE_LIMIT_BLOCK",
        }
        seen: set[str] = set()
        for reason in [*blocked_capabilities, *dependency_blocks]:
            incident_type = incident_by_reason.get(reason) or dependency_incidents.get(reason)
            if not incident_type or incident_type in seen:
                continue
            seen.add(incident_type)
            hooks.append(
                ExternalSandboxPreExecutionIncidentHook(
                    incident_type=incident_type,
                    severity="critical" if "ATTEMPT" in incident_type or "HOLD" in reason else "warning",
                    run_id=data.run_id,
                    content_id=data.content_id,
                    target_platform_id=TARGET_PLATFORM_ID,
                    target_mode=TARGET_MODE,
                    rationale=[f"{reason} blocked before external execution."],
                )
            )
        return hooks

    def _rationale(
        self,
        blocked: bool,
        blocked_capabilities: list[str],
        dependency_blocks: list[str],
    ) -> list[str]:
        rationale = [
            "Pre-execution guard is blocking-only.",
            "Guard output never authorizes external call, publish, URL, platform ID or receipt.",
            "blocked=false means no local guard block found, not permission.",
        ]
        if blocked:
            rationale.append("Blocked capabilities or dependency blocks prevent crossing the external-call boundary.")
        if blocked_capabilities:
            rationale.append("Crossing attempts are classified and blocked before execution.")
        if dependency_blocks:
            rationale.append("Dependency blocks are explicit and do not create execution permission.")
        return rationale
