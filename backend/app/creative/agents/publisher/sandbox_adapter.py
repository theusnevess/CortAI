from __future__ import annotations

import hashlib
import json
from typing import Any

from app.creative.agents.publisher.publish_semantics import BOUNDARY_STATEMENT
from app.creative.agents.publisher.sandbox_contracts import (
    ALLOWED_CREDENTIAL_STATUSES,
    ALLOWED_SANDBOX_RESULT_STATUSES,
    PRODUCTION_RESIDUALS,
    SANDBOX_DEFAULT_TIMESTAMP,
    SANDBOX_TARGET_MODE,
    SANDBOX_TARGET_PLATFORM_ID,
    SANDBOX_TRACE_VERSION,
    SandboxAdapterInput,
    SandboxAdapterResult,
    SandboxResultEvidence,
)
from app.creative.agents.publisher.sandbox_security import (
    contains_secret_material,
    no_external_side_effects,
)


class SandboxAdapterValidationError(ValueError):
    """Raised when sandbox adapter input would cross the no-side-effect boundary."""


class SandboxAdapter:
    """Sandbox-only Publisher adapter that validates contracts without external side effects."""

    def evaluate(self, request: SandboxAdapterInput) -> SandboxAdapterResult:
        blocking_reasons = self._blocking_reasons(request)
        warnings = ["SANDBOX_ADAPTER_NO_EXTERNAL_SIDE_EFFECTS"]
        idempotency_key = self.build_idempotency_key(request)
        publish_attempted = False
        sandbox_validation_performed = not blocking_reasons
        attempt_status = "sandbox_validated" if sandbox_validation_performed else "blocked"
        result_status = "sandbox_validated" if sandbox_validation_performed else "blocked"
        evidence = self._result_evidence(
            request=request,
            idempotency_key=idempotency_key,
            result_status=result_status,
            evidence_available=sandbox_validation_performed,
        )
        incident_hooks = self._incident_hooks(request, blocking_reasons)
        side_effects = no_external_side_effects()
        lifecycle_event = self._lifecycle_event(
            request=request,
            publish_attempted=publish_attempted,
            sandbox_validation_performed=sandbox_validation_performed,
            attempt_status=attempt_status,
            blocking_reasons=blocking_reasons,
            idempotency_key=idempotency_key,
            evidence=evidence,
            incident_hooks=incident_hooks,
            side_effects=side_effects,
        )
        return SandboxAdapterResult(
            trace_version=SANDBOX_TRACE_VERSION,
            target_platform_id=SANDBOX_TARGET_PLATFORM_ID,
            target_mode=SANDBOX_TARGET_MODE,
            run_id=request.run_id,
            content_id=request.content_id,
            publish_attempted=publish_attempted,
            sandbox_validation_performed=sandbox_validation_performed,
            attempt_status=attempt_status,
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            idempotency_key=idempotency_key,
            credential_status=request.credential_status.to_dict(),
            kill_switch_status=request.kill_switch_status.to_dict(),
            rate_limit_status=request.rate_limit_status.to_dict(),
            result_evidence=evidence.to_dict(),
            incident_hooks=incident_hooks,
            lifecycle_event=lifecycle_event,
            side_effects=side_effects,
            residual_monitoring=list(PRODUCTION_RESIDUALS),
        )

    def build_idempotency_key(self, request: SandboxAdapterInput) -> str:
        payload = "|".join(
            [
                request.run_id,
                request.content_id,
                str(request.artifact_manifest_ref or ""),
                request.platform_target,
                request.platform_mode,
            ]
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]
        return f"sandbox_idempotency:{digest}"

    def _blocking_reasons(self, request: SandboxAdapterInput) -> list[str]:
        reasons: list[str] = []
        if request.platform_target != SANDBOX_TARGET_PLATFORM_ID:
            reasons.append("INVALID_TARGET_PLATFORM")
        if request.platform_mode != SANDBOX_TARGET_MODE:
            reasons.append("INVALID_TARGET_MODE")
        if request.modes != [SANDBOX_TARGET_MODE]:
            reasons.append("MIXED_MODE_REJECTED")
        if request.provider_binding:
            reasons.append("IMPLICIT_PROVIDER_BINDING_REJECTED")
        if contains_secret_material(request.metadata):
            reasons.append("SECRET_MATERIAL_IN_METADATA")

        credential_status = request.credential_status.credential_status
        if credential_status not in ALLOWED_CREDENTIAL_STATUSES:
            reasons.append("PUBLISHER_CREDENTIAL_VALIDATION_FAILED")
        elif credential_status == "missing":
            reasons.append("PUBLISHER_CREDENTIALS_MISSING")
        elif credential_status == "invalid_shape":
            reasons.append("PUBLISHER_CREDENTIAL_VALIDATION_FAILED")

        if request.kill_switch_status.active or request.kill_switch_status.missing:
            reasons.append("PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE")
        if not request.kill_switch_status.blocks_publish_attempt:
            reasons.append("KILL_SWITCH_DOES_NOT_BLOCK_ATTEMPT")

        rate = request.rate_limit_status
        if rate.sandbox_validation_requests_allowed or rate.upload_requests_allowed or rate.publish_requests_allowed:
            reasons.append("RATE_LIMIT_REQUESTS_NOT_AUTHORIZED")
        if rate.rate_limit_exceeded:
            reasons.append("PUBLISHER_RATE_LIMIT_EXCEEDED")
        if (
            rate.max_sandbox_validation_requests_per_minute is not None
            or rate.max_upload_requests_per_hour is not None
            or rate.max_publish_requests_per_day is not None
        ):
            reasons.append("RATE_LIMIT_DISABLED_STATE_AMBIGUOUS")

        qc_status = (request.qc_status or "UNKNOWN").strip().upper()
        if not request.qc_trace_ref:
            reasons.append("MISSING_QC_TRACE")
        if qc_status == "REJECT":
            reasons.append("QC_REJECTED")
        if qc_status == "HOLD":
            reasons.append("QC_HOLD")
        if request.qc_publishable is not True:
            reasons.append("QC_NOT_PUBLISHABLE")
        if (request.account_health_decision or "UNKNOWN").strip().upper() == "HOLD":
            reasons.append("ACCOUNT_HEALTH_HOLD")
        if not request.artifact_manifest_ref:
            reasons.append("MISSING_ARTIFACT_MANIFEST")
        if not request.video_artifact_ref:
            reasons.append("MISSING_VIDEO_ARTIFACT")
        if not request.metadata_payload_ref:
            reasons.append("MISSING_METADATA_PAYLOAD")
        if not request.account_health_trace_ref:
            reasons.append("MISSING_ACCOUNT_HEALTH_TRACE")
        if not request.strategy_ref:
            reasons.append("MISSING_STRATEGY_CONTEXT")
        if not request.publish_eligibility_trace_ref:
            reasons.append("MISSING_PUBLISH_ELIGIBILITY_TRACE")
        reasons.extend(self._metadata_reasons(request.metadata))
        reasons.extend(self._forged_result_reasons(request))
        return list(dict.fromkeys(reasons))

    def _metadata_reasons(self, metadata: dict[str, Any]) -> list[str]:
        required = {
            "title",
            "description",
            "tags",
            "language",
            "visibility_mode",
            "account_id",
            "content_id",
            "runtime_policy_ref",
            "metadata_trace_ref",
        }
        reasons = [f"MISSING_METADATA_FIELD:{key}" for key in sorted(required - set(metadata.keys()))]
        if metadata.get("visibility_mode") != "sandbox_only":
            reasons.append("PUBLIC_VISIBILITY_FORBIDDEN")
        serialized = json.dumps(metadata, sort_keys=True, ensure_ascii=True).lower()
        for token in ["expected_performance", "forecast", "predicted", "platform_content_id", "published_url"]:
            if token in serialized:
                reasons.append("FORBIDDEN_METADATA_CLAIM")
                break
        return reasons

    def _forged_result_reasons(self, request: SandboxAdapterInput) -> list[str]:
        reasons: list[str] = []
        if request.result_status_override:
            if request.result_status_override not in ALLOWED_SANDBOX_RESULT_STATUSES:
                reasons.append("INVALID_SANDBOX_RESULT_STATUS")
            if request.result_status_override in {"succeeded", "published", "production_published"}:
                reasons.append("PUBLISH_SUCCESS_FORBIDDEN")
        if request.result_evidence_is_production_override is True:
            reasons.append("PRODUCTION_EVIDENCE_FORBIDDEN")
        if request.published_url:
            reasons.append("FAKE_URL_REJECTED")
        if request.platform_content_id:
            reasons.append("FAKE_PLATFORM_CONTENT_ID_REJECTED")
        return reasons

    def _result_evidence(
        self,
        *,
        request: SandboxAdapterInput,
        idempotency_key: str,
        result_status: str,
        evidence_available: bool,
    ) -> SandboxResultEvidence:
        receipt_hash = hashlib.sha256(
            f"{request.run_id}|{request.content_id}|{idempotency_key}|{result_status}".encode("utf-8")
        ).hexdigest()[:32]
        return SandboxResultEvidence(
            result_status=result_status,
            result_evidence_available=bool(evidence_available),
            result_evidence_is_production=False,
            result_evidence_type="sandbox_receipt" if evidence_available else "none",
            result_evidence_ref=f"sandbox_receipt:{receipt_hash}" if evidence_available else None,
            receipt_hash=receipt_hash if evidence_available else None,
            receipt_observed_at=SANDBOX_DEFAULT_TIMESTAMP if evidence_available else None,
            external_identity_type="sandbox_receipt_id" if evidence_available else "none",
            published_url=None,
            platform_content_id=None,
            receipt_simulated=True,
        )

    def _incident_hooks(self, request: SandboxAdapterInput, blocking_reasons: list[str]) -> list[dict[str, Any]]:
        incident_map = {
            "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE": "PUBLISHER_PLATFORM_KILL_SWITCH_ACTIVE",
            "PUBLISHER_CREDENTIALS_MISSING": "PUBLISHER_CREDENTIALS_MISSING",
            "PUBLISHER_CREDENTIAL_VALIDATION_FAILED": "PUBLISHER_CREDENTIAL_VALIDATION_FAILED",
            "PUBLISHER_RATE_LIMIT_EXCEEDED": "PUBLISHER_RATE_LIMIT_EXCEEDED",
            "ACCOUNT_HEALTH_HOLD": "ACCOUNT_HEALTH_HOLD_BLOCKED_PUBLISH",
            "QC_REJECTED": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "QC_HOLD": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "QC_NOT_PUBLISHABLE": "QC_NON_PUBLISHABLE_BLOCKED_PUBLISH",
            "FAKE_URL_REJECTED": "PUBLISHER_FAKE_URL_OR_PLATFORM_ID_ATTEMPT",
            "FAKE_PLATFORM_CONTENT_ID_REJECTED": "PUBLISHER_FAKE_URL_OR_PLATFORM_ID_ATTEMPT",
            "PUBLISH_SUCCESS_FORBIDDEN": "PUBLISHER_FAKE_SUCCESS_ATTEMPT",
            "PRODUCTION_EVIDENCE_FORBIDDEN": "PUBLISHER_FAKE_SUCCESS_ATTEMPT",
        }
        hooks: list[dict[str, Any]] = []
        seen: set[str] = set()
        for reason in blocking_reasons:
            incident_type = incident_map.get(reason)
            if not incident_type or incident_type in seen:
                continue
            seen.add(incident_type)
            hooks.append(
                {
                    "incident_type": incident_type,
                    "severity": "critical" if "FAKE" in incident_type else "warning",
                    "run_id": request.run_id,
                    "content_id": request.content_id,
                    "platform_target": SANDBOX_TARGET_PLATFORM_ID,
                    "mode": SANDBOX_TARGET_MODE,
                    "evidence_ref": None,
                    "rationale": [f"{incident_type} emitted by sandbox adapter validation."],
                }
            )
        return hooks

    def _lifecycle_event(
        self,
        *,
        request: SandboxAdapterInput,
        publish_attempted: bool,
        sandbox_validation_performed: bool,
        attempt_status: str,
        blocking_reasons: list[str],
        idempotency_key: str,
        evidence: SandboxResultEvidence,
        incident_hooks: list[dict[str, Any]],
        side_effects: dict[str, bool],
    ) -> dict[str, Any]:
        return {
            "publish_event_id": f"sandbox_event:{request.content_id}",
            "run_id": request.run_id,
            "content_id": request.content_id,
            "timestamp": SANDBOX_DEFAULT_TIMESTAMP,
            "platform_target": SANDBOX_TARGET_PLATFORM_ID,
            "platform_mode": SANDBOX_TARGET_MODE,
            "publish_attempted": publish_attempted,
            "sandbox_validation_performed": sandbox_validation_performed,
            "attempt_status": attempt_status,
            "blocking_reasons": list(blocking_reasons),
            "idempotency_key": idempotency_key,
            "credential_status": request.credential_status.to_dict(),
            "kill_switch_status": request.kill_switch_status.to_dict(),
            "rate_limit_status": request.rate_limit_status.to_dict(),
            "result": evidence.to_dict(),
            "incident_hooks": list(incident_hooks),
            "side_effects": dict(side_effects),
            "boundary_statement": BOUNDARY_STATEMENT,
        }
