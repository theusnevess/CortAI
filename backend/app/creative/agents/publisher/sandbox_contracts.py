from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.publisher.publish_semantics import BOUNDARY_STATEMENT


SANDBOX_TARGET_PLATFORM_ID = "SHORT_VIDEO_PLATFORM_SANDBOX_V1"
SANDBOX_TARGET_MODE = "sandbox_external_dry_run"
SANDBOX_RATE_LIMIT_POLICY_VERSION = "publisher_platform_rate_limits_v1"
SANDBOX_TRACE_VERSION = "publisher_sandbox_adapter_v1"
SANDBOX_DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"

PRODUCTION_RESIDUALS = [
    "PRODUCTION_PUBLISH_EVIDENCE_NOT_AVAILABLE_YET",
    "PLATFORM_INTEGRATION_NOT_ENABLED",
    "PUBLISH_RESULT_HISTORY_STILL_SHORT",
]

ALLOWED_CREDENTIAL_STATUSES = {"present", "missing", "invalid_shape", "not_checked"}
ALLOWED_SANDBOX_RESULT_STATUSES = {
    "not_attempted",
    "skipped",
    "blocked",
    "sandbox_validated",
    "sandbox_failed",
    "pending_sandbox",
}


@dataclass(frozen=True)
class SandboxCredentialStatus:
    credential_status: str = "present"
    credential_source: str = "environment_or_secret_manager"
    secret_values_logged: bool = False
    secret_values_persisted: bool = False
    secret_scope_class: str = "sandbox_validation_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxRateLimitStatus:
    rate_limit_policy_version: str = SANDBOX_RATE_LIMIT_POLICY_VERSION
    sandbox_validation_requests_allowed: bool = False
    upload_requests_allowed: bool = False
    publish_requests_allowed: bool = False
    max_sandbox_validation_requests_per_minute: int | None = None
    max_upload_requests_per_hour: int | None = None
    max_publish_requests_per_day: int | None = None
    burst_allowed: bool = False
    backoff_strategy: str = "deterministic_exponential_or_fixed"
    rate_limit_exceeded_behavior: str = "block_and_trace"
    rate_limit_exceeded: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxKillSwitchStatus:
    kill_switch_name: str = "PUBLISHER_PLATFORM_KILL_SWITCH"
    active_value: str = "1"
    active: bool = False
    missing: bool = False
    default_safe_state: str = "blocked"
    blocks_publish_attempt: bool = True
    blocks_external_calls: bool = True
    blocks_upload: bool = True
    blocks_scheduler: bool = True
    emits_incident_hook: bool = True
    writes_lifecycle_event: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxResultEvidence:
    result_status: str
    result_evidence_available: bool
    result_evidence_is_production: bool
    result_evidence_type: str
    result_evidence_ref: str | None
    receipt_hash: str | None
    receipt_observed_at: str | None
    external_identity_type: str
    published_url: str | None = None
    platform_content_id: str | None = None
    receipt_simulated: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SandboxAdapterInput:
    run_id: str
    content_id: str
    artifact_manifest_ref: str | None
    video_artifact_ref: str | None
    metadata_payload_ref: str | None
    qc_trace_ref: str | None
    account_health_trace_ref: str | None
    strategy_ref: str | None
    publish_eligibility_trace_ref: str | None
    metadata: dict[str, Any]
    qc_status: str | None = "APPROVE"
    qc_publishable: bool | None = True
    account_health_decision: str | None = "SAFE"
    platform_target: str = SANDBOX_TARGET_PLATFORM_ID
    platform_mode: str = SANDBOX_TARGET_MODE
    modes: list[str] = field(default_factory=lambda: [SANDBOX_TARGET_MODE])
    provider_binding: str | None = None
    credential_status: SandboxCredentialStatus = field(default_factory=SandboxCredentialStatus)
    kill_switch_status: SandboxKillSwitchStatus = field(default_factory=SandboxKillSwitchStatus)
    rate_limit_status: SandboxRateLimitStatus = field(default_factory=SandboxRateLimitStatus)
    result_status_override: str | None = None
    result_evidence_is_production_override: bool | None = None
    published_url: str | None = None
    platform_content_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


@dataclass(frozen=True)
class SandboxAdapterResult:
    trace_version: str
    target_platform_id: str
    target_mode: str
    run_id: str
    content_id: str
    publish_attempted: bool
    sandbox_validation_performed: bool
    attempt_status: str
    blocking_reasons: list[str]
    warnings: list[str]
    idempotency_key: str
    credential_status: dict[str, Any]
    kill_switch_status: dict[str, Any]
    rate_limit_status: dict[str, Any]
    result_evidence: dict[str, Any]
    incident_hooks: list[dict[str, Any]]
    lifecycle_event: dict[str, Any]
    side_effects: dict[str, bool]
    residual_monitoring: list[str]
    boundary_statement: str = BOUNDARY_STATEMENT

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
