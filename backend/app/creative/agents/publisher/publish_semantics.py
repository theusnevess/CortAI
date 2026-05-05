from __future__ import annotations

from typing import Any


PUBLISH_TRACE_VERSION = "publisher_governance_v1"
DEFAULT_TRACE_TIMESTAMP = "1970-01-01T00:00:00Z"
BOUNDARY_STATEMENT = (
    "Publisher is explicit publish authority; QC evaluates artifact quality; Strategy controls creative direction; "
    "Account Health can block via HOLD."
)

ALLOWED_SKIP_REASONS = {
    "ACCOUNT_HEALTH_HOLD",
    "QC_REJECTED",
    "QC_HOLD",
    "QC_NOT_PUBLISHABLE",
    "MISSING_QC_TRACE",
    "MISSING_ARTIFACT_MANIFEST",
    "MISSING_VIDEO_ARTIFACT",
    "MISSING_STRATEGY_CONTEXT",
    "RUNTIME_POLICY_BLOCKED",
    "PUBLISH_TARGET_NOT_CONFIGURED",
    "MANUAL_APPROVAL_REQUIRED",
    "DRY_RUN_MODE",
    "UNKNOWN_PRECONDITION",
}

ALLOWED_FAILURE_REASONS = {
    "PUBLISH_TARGET_ERROR",
    "AUTHENTICATION_FAILURE",
    "UPLOAD_FAILURE",
    "PLATFORM_REJECTION",
    "ARTIFACT_READ_FAILURE",
    "METADATA_VALIDATION_FAILURE",
    "NETWORK_FAILURE",
    "RATE_LIMITED",
    "UNKNOWN_EXTERNAL_FAILURE",
    "UNKNOWN_INTERNAL_FAILURE",
}

RESULT_STATUSES = {"not_attempted", "succeeded", "failed", "skipped", "pending", "unknown"}
ATTEMPT_STATUSES = {"not_attempted", "attempted", "failed", "succeeded", "unknown"}
QC_BLOCKING_STATUSES = {"HOLD", "REJECT"}


def normalize_skip_reason(reason: str | None) -> str | None:
    if reason is None:
        return None
    normalized = str(reason).strip().upper()
    if not normalized:
        return None
    return normalized if normalized in ALLOWED_SKIP_REASONS else "UNKNOWN_PRECONDITION"


def normalize_failure_reason(reason: str | None) -> str | None:
    if reason is None:
        return None
    normalized = str(reason).strip().upper()
    if not normalized:
        return None
    return normalized if normalized in ALLOWED_FAILURE_REASONS else "UNKNOWN_INTERNAL_FAILURE"


def lifecycle_event_type(result_status: str) -> str:
    status = str(result_status or "unknown")
    if status == "succeeded":
        return "PUBLISH_SUCCEEDED"
    if status == "failed":
        return "PUBLISH_FAILED"
    if status == "skipped":
        return "PUBLISH_SKIPPED"
    if status == "pending":
        return "PUBLISH_ATTEMPTED"
    return "PUBLISH_ELIGIBILITY_CHECKED"


def first_blocking_reason(blocking_reasons: list[str]) -> str | None:
    if not blocking_reasons:
        return None
    return normalize_skip_reason(blocking_reasons[0])


def result_has_external_identity(result: dict[str, Any]) -> bool:
    return bool(result.get("published_url") or result.get("platform_content_id"))
