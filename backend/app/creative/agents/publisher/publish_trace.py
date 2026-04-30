from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.agents.publisher.publish_semantics import (
    BOUNDARY_STATEMENT,
    DEFAULT_TRACE_TIMESTAMP,
    PUBLISH_TRACE_VERSION,
    first_blocking_reason,
    lifecycle_event_type,
    normalize_failure_reason,
    normalize_skip_reason,
    result_has_external_identity,
)


class PublishTraceValidationError(ValueError):
    """Raised when trace-only Publisher state would fabricate publish evidence."""


@dataclass(frozen=True)
class PublishIncidentHook:
    incident_type: str
    severity: str
    content_id: str
    run_id: str
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublishEligibilityTrace:
    trace_version: str
    run_id: str
    content_id: str
    eligibility_checked: bool
    eligible: bool
    qc_dependency: dict[str, Any]
    account_health_dependency: dict[str, Any]
    strategy_dependency: dict[str, Any]
    artifact_dependency: dict[str, Any]
    policy_dependency: dict[str, Any]
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublishAttemptTrace:
    attempt_id: str
    run_id: str
    content_id: str
    timestamp: str
    attempted: bool
    publish_target: str | None
    artifact_manifest_ref: str | None
    eligibility_trace_ref: str | None
    preconditions_satisfied: bool
    fallback_used: bool
    attempt_status: str
    skip_reason: str | None
    failure_reason: str | None
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublishResultTrace:
    attempt_id: str
    content_id: str
    observed_at: str
    result_status: str
    published_url: str | None
    platform_content_id: str | None
    failure_reason: str | None
    skip_reason: str | None
    result_evidence_ref: str | None
    result_evidence_available: bool
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublishLifecycleEvent:
    publish_event_id: str
    run_id: str
    content_id: str
    timestamp: str
    event_type: str
    eligibility: dict[str, Any]
    attempt: dict[str, Any]
    result: dict[str, Any]
    qc_dependency: dict[str, Any]
    account_health_dependency: dict[str, Any]
    strategy_dependency: dict[str, Any]
    artifact_refs: list[str]
    fallback_used: bool
    skip_reason: str | None
    failure_reason: str | None
    boundary_statement: str = BOUNDARY_STATEMENT

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublishTraceBundle:
    publish_eligibility_trace: PublishEligibilityTrace
    publish_attempt_trace: PublishAttemptTrace
    publish_result_trace: PublishResultTrace
    publish_lifecycle_event: PublishLifecycleEvent
    incident_hooks: list[PublishIncidentHook] = field(default_factory=list)
    boundary_statement: str = BOUNDARY_STATEMENT

    def to_dict(self) -> dict[str, Any]:
        return {
            "publish_eligibility_trace": self.publish_eligibility_trace.to_dict(),
            "publish_attempt_trace": self.publish_attempt_trace.to_dict(),
            "publish_result_trace": self.publish_result_trace.to_dict(),
            "publish_lifecycle_event": self.publish_lifecycle_event.to_dict(),
            "incident_hooks": [hook.to_dict() for hook in self.incident_hooks],
            "boundary_statement": self.boundary_statement,
        }


class PublishTraceBuilder:
    """Builds trace-only Publisher artifacts without executing publication."""

    def build_eligibility_trace(
        self,
        *,
        run_id: str,
        content_id: str,
        qc_status: str | None,
        qc_publishable: bool | None,
        qc_trace_ref: str | None,
        account_health_decision: str | None,
        health_trace_ref: str | None,
        strategy_ref: str | None,
        artifact_manifest_ref: str | None,
        video_available: bool = True,
        metadata_available: bool = True,
        runtime_policy_ref: str | None = "runtime_policy:default",
        policy_allows_publish: bool = True,
        dry_run: bool = True,
    ) -> PublishEligibilityTrace:
        qc_status_normalized = (qc_status or "UNKNOWN").strip().upper() or "UNKNOWN"
        health_decision = (account_health_decision or "UNKNOWN").strip().upper() or "UNKNOWN"
        blocking_reasons: list[str] = []
        warnings: list[str] = []

        qc_dependency_satisfied = bool(qc_trace_ref) and qc_status_normalized == "APPROVE" and qc_publishable is True
        if not qc_trace_ref:
            blocking_reasons.append("MISSING_QC_TRACE")
        elif qc_status_normalized == "REJECT":
            blocking_reasons.append("QC_REJECTED")
        elif qc_status_normalized == "HOLD":
            blocking_reasons.append("QC_HOLD")
        elif qc_publishable is not True:
            blocking_reasons.append("QC_NOT_PUBLISHABLE")

        hold_detected = health_decision == "HOLD"
        if hold_detected:
            blocking_reasons.append("ACCOUNT_HEALTH_HOLD")

        if not strategy_ref:
            blocking_reasons.append("MISSING_STRATEGY_CONTEXT")
        if not artifact_manifest_ref:
            blocking_reasons.append("MISSING_ARTIFACT_MANIFEST")
        if not video_available:
            blocking_reasons.append("MISSING_VIDEO_ARTIFACT")
        if not policy_allows_publish:
            blocking_reasons.append("RUNTIME_POLICY_BLOCKED")
        if dry_run:
            warnings.append("PUBLISHER_TRACE_DRY_RUN_ONLY")

        blocking_reasons = list(dict.fromkeys(blocking_reasons))
        eligible = not blocking_reasons
        return PublishEligibilityTrace(
            trace_version=PUBLISH_TRACE_VERSION,
            run_id=run_id,
            content_id=content_id,
            eligibility_checked=True,
            eligible=eligible,
            qc_dependency={
                "qc_status": qc_status_normalized,
                "qc_publishable": qc_publishable,
                "qc_trace_ref": qc_trace_ref,
                "qc_dependency_satisfied": qc_dependency_satisfied,
            },
            account_health_dependency={
                "decision": health_decision,
                "hold_detected": hold_detected,
                "health_trace_ref": health_trace_ref,
                "hold_blocks_publish": True,
            },
            strategy_dependency={
                "strategy_ref": strategy_ref,
                "strategy_available": bool(strategy_ref),
            },
            artifact_dependency={
                "artifact_manifest_ref": artifact_manifest_ref,
                "video_available": bool(video_available),
                "metadata_available": bool(metadata_available),
            },
            policy_dependency={
                "runtime_policy_ref": runtime_policy_ref,
                "policy_allows_publish": bool(policy_allows_publish),
            },
            blocking_reasons=blocking_reasons,
            warnings=warnings,
            rationale=[
                "Eligibility is derived from QC, Account Health, Strategy, artifact and runtime policy evidence.",
                "Missing evidence blocks or degrades eligibility; it is never converted into publish success.",
            ],
        )

    def build_attempt_trace(
        self,
        *,
        eligibility_trace: PublishEligibilityTrace | dict[str, Any],
        attempt_id: str,
        timestamp: str = DEFAULT_TRACE_TIMESTAMP,
        publish_target: str | None = None,
        dry_run: bool = True,
        simulate_failure: bool = False,
        failure_reason: str | None = None,
    ) -> PublishAttemptTrace:
        eligibility = self._as_dict(eligibility_trace)
        eligible = bool(eligibility.get("eligible"))
        blocking_reasons = list(eligibility.get("blocking_reasons") or [])
        skip_reason = first_blocking_reason(blocking_reasons)
        artifact_ref = (eligibility.get("artifact_dependency") or {}).get("artifact_manifest_ref")

        if not eligible:
            return PublishAttemptTrace(
                attempt_id=attempt_id,
                run_id=str(eligibility.get("run_id") or ""),
                content_id=str(eligibility.get("content_id") or ""),
                timestamp=timestamp,
                attempted=False,
                publish_target=None,
                artifact_manifest_ref=artifact_ref,
                eligibility_trace_ref=f"publish_eligibility_trace:{eligibility.get('content_id')}",
                preconditions_satisfied=False,
                fallback_used=False,
                attempt_status="not_attempted",
                skip_reason=skip_reason,
                failure_reason=None,
                rationale=["Publish attempt was blocked by eligibility trace."],
            )

        if dry_run:
            return PublishAttemptTrace(
                attempt_id=attempt_id,
                run_id=str(eligibility.get("run_id") or ""),
                content_id=str(eligibility.get("content_id") or ""),
                timestamp=timestamp,
                attempted=False,
                publish_target=None,
                artifact_manifest_ref=artifact_ref,
                eligibility_trace_ref=f"publish_eligibility_trace:{eligibility.get('content_id')}",
                preconditions_satisfied=True,
                fallback_used=False,
                attempt_status="not_attempted",
                skip_reason="DRY_RUN_MODE",
                failure_reason=None,
                rationale=["Dry-run mode records publish intent without executing publication."],
            )

        normalized_failure = normalize_failure_reason(failure_reason or "PUBLISH_TARGET_ERROR")
        return PublishAttemptTrace(
            attempt_id=attempt_id,
            run_id=str(eligibility.get("run_id") or ""),
            content_id=str(eligibility.get("content_id") or ""),
            timestamp=timestamp,
            attempted=True,
            publish_target=publish_target or "trace_only_target",
            artifact_manifest_ref=artifact_ref,
            eligibility_trace_ref=f"publish_eligibility_trace:{eligibility.get('content_id')}",
            preconditions_satisfied=True,
            fallback_used=False,
            attempt_status="failed" if simulate_failure else "attempted",
            skip_reason=None,
            failure_reason=normalized_failure if simulate_failure else None,
            rationale=["Publisher attempt trace was recorded without invoking external platform APIs."],
        )

    def build_result_trace(
        self,
        *,
        attempt_trace: PublishAttemptTrace | dict[str, Any],
        observed_at: str = DEFAULT_TRACE_TIMESTAMP,
        result_status: str | None = None,
        published_url: str | None = None,
        platform_content_id: str | None = None,
        failure_reason: str | None = None,
        skip_reason: str | None = None,
        result_evidence_ref: str | None = None,
        result_evidence_available: bool = False,
    ) -> PublishResultTrace:
        attempt = self._as_dict(attempt_trace)
        status = result_status or self._default_result_status(attempt)
        normalized_failure = normalize_failure_reason(failure_reason or attempt.get("failure_reason"))
        normalized_skip = normalize_skip_reason(skip_reason or attempt.get("skip_reason"))
        payload = {
            "result_status": status,
            "published_url": published_url,
            "platform_content_id": platform_content_id,
            "result_evidence_ref": result_evidence_ref,
            "result_evidence_available": bool(result_evidence_available),
        }
        self._raise_on_fabricated_result(payload)
        return PublishResultTrace(
            attempt_id=str(attempt.get("attempt_id") or ""),
            content_id=str(attempt.get("content_id") or ""),
            observed_at=observed_at,
            result_status=status,
            published_url=published_url,
            platform_content_id=platform_content_id,
            failure_reason=normalized_failure if status == "failed" else None,
            skip_reason=normalized_skip if status in {"not_attempted", "skipped"} else None,
            result_evidence_ref=result_evidence_ref,
            result_evidence_available=bool(result_evidence_available),
            rationale=[
                "Publish result is represented from explicit evidence only.",
                "Pending, skipped, failed, unknown and not_attempted are not publish success.",
            ],
        )

    def build_lifecycle_event(
        self,
        *,
        eligibility_trace: PublishEligibilityTrace | dict[str, Any],
        attempt_trace: PublishAttemptTrace | dict[str, Any],
        result_trace: PublishResultTrace | dict[str, Any],
        publish_event_id: str,
        timestamp: str = DEFAULT_TRACE_TIMESTAMP,
    ) -> PublishLifecycleEvent:
        eligibility = self._as_dict(eligibility_trace)
        attempt = self._as_dict(attempt_trace)
        result = self._as_dict(result_trace)
        artifact_ref = (eligibility.get("artifact_dependency") or {}).get("artifact_manifest_ref")
        return PublishLifecycleEvent(
            publish_event_id=publish_event_id,
            run_id=str(eligibility.get("run_id") or ""),
            content_id=str(eligibility.get("content_id") or ""),
            timestamp=timestamp,
            event_type=lifecycle_event_type(str(result.get("result_status") or "unknown")),
            eligibility=eligibility,
            attempt=attempt,
            result=result,
            qc_dependency=dict(eligibility.get("qc_dependency") or {}),
            account_health_dependency=dict(eligibility.get("account_health_dependency") or {}),
            strategy_dependency=dict(eligibility.get("strategy_dependency") or {}),
            artifact_refs=[artifact_ref] if artifact_ref else [],
            fallback_used=bool(attempt.get("fallback_used")),
            skip_reason=normalize_skip_reason(result.get("skip_reason") or attempt.get("skip_reason")),
            failure_reason=normalize_failure_reason(result.get("failure_reason") or attempt.get("failure_reason")),
            boundary_statement=BOUNDARY_STATEMENT,
        )

    def build_trace_bundle(
        self,
        *,
        run_id: str,
        content_id: str,
        qc_status: str | None,
        qc_publishable: bool | None,
        qc_trace_ref: str | None,
        account_health_decision: str | None,
        health_trace_ref: str | None,
        strategy_ref: str | None,
        artifact_manifest_ref: str | None,
        video_available: bool = True,
        metadata_available: bool = True,
        runtime_policy_ref: str | None = "runtime_policy:default",
        policy_allows_publish: bool = True,
        dry_run: bool = True,
        timestamp: str = DEFAULT_TRACE_TIMESTAMP,
    ) -> PublishTraceBundle:
        eligibility = self.build_eligibility_trace(
            run_id=run_id,
            content_id=content_id,
            qc_status=qc_status,
            qc_publishable=qc_publishable,
            qc_trace_ref=qc_trace_ref,
            account_health_decision=account_health_decision,
            health_trace_ref=health_trace_ref,
            strategy_ref=strategy_ref,
            artifact_manifest_ref=artifact_manifest_ref,
            video_available=video_available,
            metadata_available=metadata_available,
            runtime_policy_ref=runtime_policy_ref,
            policy_allows_publish=policy_allows_publish,
            dry_run=dry_run,
        )
        attempt = self.build_attempt_trace(
            eligibility_trace=eligibility,
            attempt_id=f"attempt:{content_id}",
            timestamp=timestamp,
            dry_run=dry_run,
        )
        result = self.build_result_trace(attempt_trace=attempt, observed_at=timestamp)
        lifecycle = self.build_lifecycle_event(
            eligibility_trace=eligibility,
            attempt_trace=attempt,
            result_trace=result,
            publish_event_id=f"publish_event:{content_id}",
            timestamp=timestamp,
        )
        incidents = self.build_incident_hooks(
            eligibility_trace=eligibility,
            attempt_trace=attempt,
            result_trace=result,
        )
        return PublishTraceBundle(
            publish_eligibility_trace=eligibility,
            publish_attempt_trace=attempt,
            publish_result_trace=result,
            publish_lifecycle_event=lifecycle,
            incident_hooks=incidents,
        )

    def build_incident_hooks(
        self,
        *,
        eligibility_trace: PublishEligibilityTrace | dict[str, Any],
        attempt_trace: PublishAttemptTrace | dict[str, Any],
        result_trace: PublishResultTrace | dict[str, Any],
    ) -> list[PublishIncidentHook]:
        eligibility = self._as_dict(eligibility_trace)
        attempt = self._as_dict(attempt_trace)
        result = self._as_dict(result_trace)
        run_id = str(eligibility.get("run_id") or attempt.get("run_id") or "")
        content_id = str(eligibility.get("content_id") or attempt.get("content_id") or result.get("content_id") or "")
        hooks: list[PublishIncidentHook] = []
        hold_detected = bool((eligibility.get("account_health_dependency") or {}).get("hold_detected"))
        qc_satisfied = bool((eligibility.get("qc_dependency") or {}).get("qc_dependency_satisfied"))
        if hold_detected and attempt.get("attempted"):
            hooks.append(self._incident("ACCOUNT_HEALTH_HOLD_OVERRIDE_ATTEMPT", "critical", run_id, content_id))
        if not qc_satisfied and attempt.get("attempted"):
            hooks.append(self._incident("QC_BYPASS_ATTEMPT", "critical", run_id, content_id))
        if "MISSING_QC_TRACE" in eligibility.get("blocking_reasons", []):
            hooks.append(self._incident("MISSING_QC_TRACE", "warning", run_id, content_id))
        if "MISSING_ARTIFACT_MANIFEST" in eligibility.get("blocking_reasons", []):
            hooks.append(self._incident("MISSING_ARTIFACT_MANIFEST", "warning", run_id, content_id))
        if result.get("result_status") == "failed":
            hooks.append(self._incident("PUBLISH_ATTEMPT_FAILED", "warning", run_id, content_id))
        if result.get("result_status") == "succeeded" and not result.get("result_evidence_available"):
            hooks.append(self._incident("PUBLISH_SUCCESS_WITHOUT_EVIDENCE", "critical", run_id, content_id))
        if result_has_external_identity(result) and not result.get("result_evidence_available"):
            hooks.append(self._incident("FAKE_URL_OR_PLATFORM_ID", "critical", run_id, content_id))
        return hooks

    def validate_trace_bundle(self, bundle: PublishTraceBundle | dict[str, Any]) -> tuple[bool, list[str]]:
        payload = bundle.to_dict() if isinstance(bundle, PublishTraceBundle) else dict(bundle)
        eligibility = dict(payload.get("publish_eligibility_trace") or {})
        attempt = dict(payload.get("publish_attempt_trace") or {})
        result = dict(payload.get("publish_result_trace") or {})
        lifecycle = dict(payload.get("publish_lifecycle_event") or {})
        failures: list[str] = []
        failures.extend(f"eligibility_missing:{key}" for key in self._missing(eligibility, {
            "trace_version",
            "run_id",
            "content_id",
            "eligibility_checked",
            "eligible",
            "qc_dependency",
            "account_health_dependency",
            "strategy_dependency",
            "artifact_dependency",
            "policy_dependency",
            "blocking_reasons",
            "rationale",
        }))
        failures.extend(f"attempt_missing:{key}" for key in self._missing(attempt, {
            "attempt_id",
            "attempted",
            "attempt_status",
            "preconditions_satisfied",
            "skip_reason",
            "failure_reason",
        }))
        failures.extend(f"result_missing:{key}" for key in self._missing(result, {
            "attempt_id",
            "result_status",
            "published_url",
            "platform_content_id",
            "result_evidence_available",
        }))
        failures.extend(f"lifecycle_missing:{key}" for key in self._missing(lifecycle, {
            "publish_event_id",
            "event_type",
            "eligibility",
            "attempt",
            "result",
            "boundary_statement",
        }))
        if lifecycle.get("boundary_statement") != BOUNDARY_STATEMENT:
            failures.append("boundary_statement_missing_or_invalid")
        if (eligibility.get("account_health_dependency") or {}).get("hold_detected") and attempt.get("attempted"):
            failures.append("account_health_hold_override")
        if not (eligibility.get("qc_dependency") or {}).get("qc_dependency_satisfied") and attempt.get("attempted"):
            failures.append("qc_bypass_attempt")
        if result.get("result_status") == "succeeded" and not result.get("result_evidence_available"):
            failures.append("fabricated_publish_success")
        if result_has_external_identity(result) and not result.get("result_evidence_available"):
            failures.append("fake_url_or_platform_id")
        return not failures, failures

    def _default_result_status(self, attempt: dict[str, Any]) -> str:
        if not attempt.get("attempted"):
            return "not_attempted"
        if attempt.get("attempt_status") == "failed":
            return "failed"
        if attempt.get("attempt_status") == "succeeded":
            return "succeeded"
        return "pending"

    def _raise_on_fabricated_result(self, result: dict[str, Any]) -> None:
        if result.get("result_status") == "succeeded" and not result.get("result_evidence_available"):
            raise PublishTraceValidationError("PUBLISH_SUCCESS_REQUIRES_RESULT_EVIDENCE")
        if result_has_external_identity(result) and not result.get("result_evidence_available"):
            raise PublishTraceValidationError("PUBLISH_EXTERNAL_IDENTITY_REQUIRES_RESULT_EVIDENCE")

    def _incident(self, incident_type: str, severity: str, run_id: str, content_id: str) -> PublishIncidentHook:
        return PublishIncidentHook(
            incident_type=incident_type,
            severity=severity,
            run_id=run_id,
            content_id=content_id,
            rationale=[f"{incident_type} was detected by Publisher trace-only validation."],
        )

    def _as_dict(self, payload: Any) -> dict[str, Any]:
        if hasattr(payload, "to_dict"):
            return payload.to_dict()
        return dict(payload or {})

    def _missing(self, payload: dict[str, Any], required: set[str]) -> list[str]:
        return sorted(key for key in required if key not in payload)
