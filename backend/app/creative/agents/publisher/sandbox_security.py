from __future__ import annotations

from typing import Any

from app.creative.agents.publisher.sandbox_contracts import (
    SandboxCredentialStatus,
    SandboxKillSwitchStatus,
    SandboxRateLimitStatus,
)


SECRET_KEY_FRAGMENTS = {
    "secret",
    "token",
    "access_token",
    "client_secret",
    "authorization",
    "api_key",
    "password",
}


def build_credential_status(status: str = "present") -> SandboxCredentialStatus:
    normalized = (status or "not_checked").strip().lower() or "not_checked"
    return SandboxCredentialStatus(credential_status=normalized)


def build_kill_switch_status(active: bool = False, missing: bool = False) -> SandboxKillSwitchStatus:
    return SandboxKillSwitchStatus(active=bool(active), missing=bool(missing))


def build_rate_limit_status(
    *,
    sandbox_validation_requests_allowed: bool = False,
    upload_requests_allowed: bool = False,
    publish_requests_allowed: bool = False,
    rate_limit_exceeded: bool = False,
) -> SandboxRateLimitStatus:
    return SandboxRateLimitStatus(
        sandbox_validation_requests_allowed=bool(sandbox_validation_requests_allowed),
        upload_requests_allowed=bool(upload_requests_allowed),
        publish_requests_allowed=bool(publish_requests_allowed),
        rate_limit_exceeded=bool(rate_limit_exceeded),
    )


def contains_secret_material(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in SECRET_KEY_FRAGMENTS):
                return True
            if contains_secret_material(value):
                return True
    elif isinstance(payload, list):
        return any(contains_secret_material(item) for item in payload)
    return False


def no_external_side_effects() -> dict[str, bool]:
    return {
        "platform_api_called": False,
        "upload_performed": False,
        "scheduler_invoked": False,
        "real_publishing_performed": False,
        "real_url_emitted": False,
        "platform_content_id_emitted": False,
    }
