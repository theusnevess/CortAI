from __future__ import annotations

from typing import Any

ALLOWED_PLATFORMS = {"tiktok", "youtube_shorts", "instagram_reels"}
ALLOWED_PUBLISH_MODES = {"auto", "manual", "replay"}
ALLOWED_STATUS = {"posted", "failed", "blocked"}

REQUIRED_FIELDS = (
    "publish_id",
    "account_id",
    "job_id",
    "video_id",
    "platform",
    "publish_mode",
    "status",
    "published_at",
    "created_at",
)


class PublishRecordValidationError(ValueError):
    """Contract error for publish_record schema violations."""


def validate_publish_record(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise PublishRecordValidationError("ContractViolation: record must be an object")

    for field in REQUIRED_FIELDS:
        if field not in record:
            raise PublishRecordValidationError(f"ContractViolation: missing required field '{field}'")

    normalized = dict(record)
    for field in REQUIRED_FIELDS:
        value = normalized.get(field)
        if not isinstance(value, str) or not value.strip():
            raise PublishRecordValidationError(f"ContractViolation: invalid required field '{field}'")
        normalized[field] = value.strip()

    if normalized["platform"] not in ALLOWED_PLATFORMS:
        raise PublishRecordValidationError("ContractViolation: invalid platform")
    if normalized["publish_mode"] not in ALLOWED_PUBLISH_MODES:
        raise PublishRecordValidationError("ContractViolation: invalid publish_mode")
    if normalized["status"] not in ALLOWED_STATUS:
        raise PublishRecordValidationError("ContractViolation: invalid status")

    metadata = normalized.get("metadata")
    if metadata is None:
        normalized["metadata"] = {}
    elif not isinstance(metadata, dict):
        raise PublishRecordValidationError("ContractViolation: metadata must be an object")

    return normalized
