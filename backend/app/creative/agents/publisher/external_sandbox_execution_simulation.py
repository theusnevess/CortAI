from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.publisher.external_sandbox_validation_envelope import (
    TARGET_MODE,
    TARGET_PLATFORM_ID,
    ExternalSandboxValidationEnvelope,
)
from app.creative.agents.publisher.sandbox_contracts import PRODUCTION_RESIDUALS


SIMULATION_VERSION = "external_sandbox_execution_simulation_v1"
SIMULATION_TYPE = "offline_misuse_and_blocking_simulation"
SIMULATION_PASSED_MEANING = "misuse_attempts_blocked_offline"
BOUNDARY_STATEMENT = "External sandbox execution simulation is offline only and cannot execute."


MISUSE_ATTEMPT_SPECS: tuple[dict[str, str], ...] = (
    {
        "attempt_id": "misuse_001_transform_envelope_into_request",
        "attempt_type": "transform_envelope_into_request",
        "attempt_description": "Attempt to reinterpret validation envelope as a request object.",
        "reason_code": "TRANSFORMATION_LAYER_NOT_AUTHORIZED",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_REQUEST_TRANSFORMATION_ATTEMPT",
    },
    {
        "attempt_id": "misuse_002_http_client_post_shape",
        "attempt_type": "http_client_post_shape",
        "attempt_description": "Attempt to model a third-party HTTP client post with envelope data.",
        "reason_code": "HTTP_CLIENT_EXECUTION_NOT_AUTHORIZED",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_REQUEST_TRANSFORMATION_ATTEMPT",
    },
    {
        "attempt_id": "misuse_003_envelope_valid_as_readiness",
        "attempt_type": "envelope_valid_as_readiness",
        "attempt_description": "Attempt to treat schema validity as execution readiness.",
        "reason_code": "ENVELOPE_VALID_IS_SCHEMA_ONLY",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_READINESS_MISINTERPRETATION",
    },
    {
        "attempt_id": "misuse_004_future_eligibility_as_permission",
        "attempt_type": "future_eligibility_as_permission",
        "attempt_description": "Attempt to treat future eligibility as permission to execute.",
        "reason_code": "FUTURE_ELIGIBILITY_IS_NOT_EXECUTION_PERMISSION",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_READINESS_MISINTERPRETATION",
    },
    {
        "attempt_id": "misuse_005_endpoint_injection",
        "attempt_type": "endpoint_injection",
        "attempt_description": "Attempt to inject endpoint-like transport configuration.",
        "reason_code": "FORBIDDEN_TRANSPORT_FIELD",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_TRANSPORT_FIELD",
    },
    {
        "attempt_id": "misuse_006_headers_injection",
        "attempt_type": "headers_injection",
        "attempt_description": "Attempt to inject header-like transport fields.",
        "reason_code": "FORBIDDEN_TRANSPORT_FIELD",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_TRANSPORT_FIELD",
    },
    {
        "attempt_id": "misuse_007_body_injection",
        "attempt_type": "body_injection",
        "attempt_description": "Attempt to inject body-like transport fields.",
        "reason_code": "FORBIDDEN_TRANSPORT_FIELD",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_TRANSPORT_FIELD",
    },
    {
        "attempt_id": "misuse_008_method_injection",
        "attempt_type": "method_injection",
        "attempt_description": "Attempt to inject method-like transport fields.",
        "reason_code": "FORBIDDEN_TRANSPORT_FIELD",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_TRANSPORT_FIELD",
    },
    {
        "attempt_id": "misuse_009_url_injection",
        "attempt_type": "url_injection",
        "attempt_description": "Attempt to inject URL-like identity or transport fields.",
        "reason_code": "FORBIDDEN_TRANSPORT_FIELD",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_TRANSPORT_FIELD",
    },
    {
        "attempt_id": "misuse_010_published_url_injection",
        "attempt_type": "published_url_injection",
        "attempt_description": "Attempt to inject a published URL as if publishing occurred.",
        "reason_code": "FORBIDDEN_PLATFORM_IDENTITY",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_PLATFORM_IDENTITY",
    },
    {
        "attempt_id": "misuse_011_platform_content_id_injection",
        "attempt_type": "platform_content_id_injection",
        "attempt_description": "Attempt to inject platform content identity.",
        "reason_code": "FORBIDDEN_PLATFORM_IDENTITY",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_PLATFORM_IDENTITY",
    },
    {
        "attempt_id": "misuse_012_production_receipt_injection",
        "attempt_type": "production_receipt_injection",
        "attempt_description": "Attempt to inject production receipt evidence.",
        "reason_code": "PRODUCTION_RECEIPT_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FAKE_RECEIPT_ATTEMPT",
    },
    {
        "attempt_id": "misuse_013_sandbox_receipt_resembles_production",
        "attempt_type": "sandbox_receipt_resembles_production",
        "attempt_description": "Attempt to represent sandbox receipt as production-like evidence.",
        "reason_code": "SANDBOX_RECEIPT_CANNOT_RESEMBLE_PRODUCTION",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FAKE_RECEIPT_ATTEMPT",
    },
    {
        "attempt_id": "misuse_014_media_bytes_injection",
        "attempt_type": "media_bytes_injection",
        "attempt_description": "Attempt to include media bytes in simulation.",
        "reason_code": "MEDIA_BYTES_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_TRANSPORT_FIELD",
    },
    {
        "attempt_id": "misuse_015_upload_url_injection",
        "attempt_type": "upload_url_injection",
        "attempt_description": "Attempt to inject upload URL.",
        "reason_code": "UPLOAD_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_TRANSPORT_FIELD",
    },
    {
        "attempt_id": "misuse_016_scheduler_job_injection",
        "attempt_type": "scheduler_job_injection",
        "attempt_description": "Attempt to inject scheduler job identity.",
        "reason_code": "SCHEDULER_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_TRANSPORT_FIELD",
    },
    {
        "attempt_id": "misuse_017_post_publish_metrics_injection",
        "attempt_type": "post_publish_metrics_injection",
        "attempt_description": "Attempt to inject post-publish metrics reference.",
        "reason_code": "POST_PUBLISH_METRICS_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_PLATFORM_IDENTITY",
    },
    {
        "attempt_id": "misuse_018_expected_performance_claim",
        "attempt_type": "expected_performance_claim",
        "attempt_description": "Attempt to turn simulation into expected performance claim.",
        "reason_code": "PERFORMANCE_PREDICTION_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_PLATFORM_IDENTITY",
    },
    {
        "attempt_id": "misuse_019_attribution_causal_claim",
        "attempt_type": "attribution_causal_claim",
        "attempt_description": "Attempt to turn simulation into attribution causality.",
        "reason_code": "ATTRIBUTION_CAUSALITY_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_PLATFORM_IDENTITY",
    },
    {
        "attempt_id": "misuse_020_residual_closure_attempt",
        "attempt_type": "residual_closure_attempt",
        "attempt_description": "Attempt to close production residuals using simulation.",
        "reason_code": "PRODUCTION_RESIDUAL_CLOSURE_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_RESIDUAL_CLOSURE_ATTEMPT",
    },
    {
        "attempt_id": "misuse_021_simulation_pass_as_publish_success",
        "attempt_type": "simulation_pass_as_publish_success",
        "attempt_description": "Attempt to treat simulation pass as publish success.",
        "reason_code": "SIMULATION_PASS_IS_NOT_SUCCESS",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_READINESS_MISINTERPRETATION",
    },
    {
        "attempt_id": "misuse_022_simulation_pass_as_platform_validation",
        "attempt_type": "simulation_pass_as_platform_validation",
        "attempt_description": "Attempt to treat simulation pass as platform validation.",
        "reason_code": "SIMULATION_PASS_IS_NOT_PLATFORM_VALIDATION",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_READINESS_MISINTERPRETATION",
    },
    {
        "attempt_id": "misuse_023_simulation_pass_as_production_evidence",
        "attempt_type": "simulation_pass_as_production_evidence",
        "attempt_description": "Attempt to treat simulation pass as production evidence.",
        "reason_code": "SIMULATION_PASS_IS_NOT_PRODUCTION_EVIDENCE",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_READINESS_MISINTERPRETATION",
    },
    {
        "attempt_id": "misuse_024_qc_non_publishable_bypass",
        "attempt_type": "qc_non_publishable_bypass",
        "attempt_description": "Attempt to bypass QC non-publishable state.",
        "reason_code": "QC_NON_PUBLISHABLE_BYPASS_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_QC_BYPASS_ATTEMPT",
    },
    {
        "attempt_id": "misuse_025_account_health_hold_bypass",
        "attempt_type": "account_health_hold_bypass",
        "attempt_description": "Attempt to bypass Account Health HOLD.",
        "reason_code": "ACCOUNT_HEALTH_HOLD_BYPASS_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_ACCOUNT_HEALTH_BYPASS_ATTEMPT",
    },
    {
        "attempt_id": "misuse_026_kill_switch_bypass",
        "attempt_type": "kill_switch_bypass",
        "attempt_description": "Attempt to bypass Publisher platform kill switch.",
        "reason_code": "KILL_SWITCH_BYPASS_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_KILL_SWITCH_BYPASS_ATTEMPT",
    },
    {
        "attempt_id": "misuse_027_rate_limit_bypass",
        "attempt_type": "rate_limit_bypass",
        "attempt_description": "Attempt to bypass disabled rate-limit policy.",
        "reason_code": "RATE_LIMIT_BYPASS_FORBIDDEN",
        "severity": "warning",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_RATE_LIMIT_BYPASS_ATTEMPT",
    },
    {
        "attempt_id": "misuse_028_implicit_provider_binding",
        "attempt_type": "implicit_provider_binding",
        "attempt_description": "Attempt to bind a provider implicitly.",
        "reason_code": "IMPLICIT_PROVIDER_BINDING_FORBIDDEN",
        "severity": "warning",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_PLATFORM_IDENTITY",
    },
    {
        "attempt_id": "misuse_029_mixed_mode",
        "attempt_type": "mixed_mode",
        "attempt_description": "Attempt to combine sandbox and production modes.",
        "reason_code": "MIXED_MODE_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_FORBIDDEN_PLATFORM_IDENTITY",
    },
    {
        "attempt_id": "misuse_030_secret_like_field",
        "attempt_type": "secret_like_field",
        "attempt_description": "Attempt to include secret-like material in simulation.",
        "reason_code": "SECRET_LEAKAGE_FORBIDDEN",
        "severity": "critical",
        "incident_type": "EXTERNAL_SANDBOX_SIMULATION_SECRET_LEAKAGE_ATTEMPT",
    },
)


@dataclass(frozen=True)
class ExternalSandboxExecutionSimulationInput:
    envelope: ExternalSandboxValidationEnvelope | dict[str, Any]
    envelope_ref: str = "external_sandbox_validation_envelope:local"

    def to_dict(self) -> dict[str, Any]:
        envelope_payload = self.envelope.to_dict() if hasattr(self.envelope, "to_dict") else dict(self.envelope)
        return {"envelope": envelope_payload, "envelope_ref": self.envelope_ref}


@dataclass(frozen=True)
class ExternalSandboxMisuseAttempt:
    attempt_id: str
    attempt_type: str
    attempt_description: str
    blocked: bool
    reason_code: str
    severity: str
    external_call_authorized: bool
    upload_authorized: bool
    scheduler_authorized: bool
    real_publish_authorized: bool
    result_evidence_is_production: bool
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExternalSandboxSimulationIncidentHook:
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
class ExternalSandboxExecutionSimulationResult:
    simulation_version: str
    simulation_type: str
    simulation_only: bool
    run_id: str
    content_id: str
    target_platform_id: str
    target_mode: str
    envelope_ref: str
    misuse_attempts: list[dict[str, Any]]
    blocked_attempts_count: int
    unblocked_attempts_count: int
    simulation_passed: bool
    simulation_passed_meaning: str
    external_call_authorized: bool
    http_client_allowed: bool
    platform_sdk_allowed: bool
    endpoint_allowed: bool
    network_access_allowed: bool
    upload_authorized: bool
    scheduler_authorized: bool
    real_publish_authorized: bool
    transformation_layer_authorized: bool
    simulated_receipt_generated: bool
    production_receipt_generated: bool
    published_url: str | None
    platform_content_id: str | None
    result_evidence_is_production: bool
    production_residuals_closed: bool
    incident_hooks: list[dict[str, Any]]
    rationale: list[str]
    residual_monitoring: list[str]
    boundary_statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExternalSandboxExecutionSimulation:
    """Offline-only misuse simulation for Publisher sandbox safety boundaries."""

    def simulate(self, data: ExternalSandboxExecutionSimulationInput) -> ExternalSandboxExecutionSimulationResult:
        envelope_payload = self._envelope_payload(data.envelope)
        attempts = [self._blocked_attempt(spec) for spec in MISUSE_ATTEMPT_SPECS]
        unblocked_count = sum(1 for attempt in attempts if not attempt.blocked)
        hooks = self._incident_hooks(envelope_payload=envelope_payload, attempts=attempts)
        return ExternalSandboxExecutionSimulationResult(
            simulation_version=SIMULATION_VERSION,
            simulation_type=SIMULATION_TYPE,
            simulation_only=True,
            run_id=str(envelope_payload.get("run_id") or ""),
            content_id=str(envelope_payload.get("content_id") or ""),
            target_platform_id=TARGET_PLATFORM_ID,
            target_mode=TARGET_MODE,
            envelope_ref=data.envelope_ref,
            misuse_attempts=[attempt.to_dict() for attempt in attempts],
            blocked_attempts_count=len(attempts) - unblocked_count,
            unblocked_attempts_count=unblocked_count,
            simulation_passed=unblocked_count == 0,
            simulation_passed_meaning=SIMULATION_PASSED_MEANING,
            external_call_authorized=False,
            http_client_allowed=False,
            platform_sdk_allowed=False,
            endpoint_allowed=False,
            network_access_allowed=False,
            upload_authorized=False,
            scheduler_authorized=False,
            real_publish_authorized=False,
            transformation_layer_authorized=False,
            simulated_receipt_generated=False,
            production_receipt_generated=False,
            published_url=None,
            platform_content_id=None,
            result_evidence_is_production=False,
            production_residuals_closed=False,
            incident_hooks=[hook.to_dict() for hook in hooks],
            rationale=[
                "Simulation is offline-only and models blocked misuse attempts.",
                "simulation_passed means misuse_attempts_blocked_offline only.",
                "External calls, upload, scheduler and real publishing remain unauthorized.",
            ],
            residual_monitoring=list(PRODUCTION_RESIDUALS),
            boundary_statement=BOUNDARY_STATEMENT,
        )

    def deterministic_audit_json(self, result: ExternalSandboxExecutionSimulationResult) -> str:
        return json.dumps(result.to_dict(), sort_keys=True, ensure_ascii=True, separators=(",", ":"))

    def _envelope_payload(self, envelope: ExternalSandboxValidationEnvelope | dict[str, Any]) -> dict[str, Any]:
        return envelope.to_dict() if hasattr(envelope, "to_dict") else dict(envelope)

    def _blocked_attempt(self, spec: dict[str, str]) -> ExternalSandboxMisuseAttempt:
        return ExternalSandboxMisuseAttempt(
            attempt_id=spec["attempt_id"],
            attempt_type=spec["attempt_type"],
            attempt_description=spec["attempt_description"],
            blocked=True,
            reason_code=spec["reason_code"],
            severity=spec["severity"],
            external_call_authorized=False,
            upload_authorized=False,
            scheduler_authorized=False,
            real_publish_authorized=False,
            result_evidence_is_production=False,
            rationale=[
                f"{spec['reason_code']} blocks this misuse attempt.",
                "Simulation records the block without constructing transport or execution.",
            ],
        )

    def _incident_hooks(
        self,
        *,
        envelope_payload: dict[str, Any],
        attempts: list[ExternalSandboxMisuseAttempt],
    ) -> list[ExternalSandboxSimulationIncidentHook]:
        hooks: list[ExternalSandboxSimulationIncidentHook] = []
        seen: set[str] = set()
        incident_by_attempt = {spec["attempt_type"]: spec["incident_type"] for spec in MISUSE_ATTEMPT_SPECS}
        for attempt in attempts:
            incident_type = incident_by_attempt.get(attempt.attempt_type)
            if not incident_type or incident_type in seen:
                continue
            seen.add(incident_type)
            hooks.append(
                ExternalSandboxSimulationIncidentHook(
                    incident_type=incident_type,
                    severity=attempt.severity,
                    run_id=str(envelope_payload.get("run_id") or ""),
                    content_id=str(envelope_payload.get("content_id") or ""),
                    target_platform_id=TARGET_PLATFORM_ID,
                    target_mode=TARGET_MODE,
                    rationale=[f"{incident_type} emitted for blocked offline simulation misuse."],
                )
            )
        return hooks
