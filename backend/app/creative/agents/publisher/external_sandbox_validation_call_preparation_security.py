from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SECRET_KEY_FRAGMENTS = frozenset(
    {
        "secret",
        "token",
        "access_token",
        "client_secret",
        "authorization",
        "api_key",
        "password",
        "refresh_token",
    }
)

FORBIDDEN_FIELD_NAMES = frozenset(
    {
        "endpoint",
        "url",
        "published_url",
        "platform_content_id",
        "platform_receipt",
        "receipt",
        "headers",
        "authorization_header",
        "method",
        "body",
        "payload",
        "transport_payload",
        "media_bytes",
        "upload_path",
        "upload_url",
        "scheduler_job_id",
        "request_transformation",
        "post_publish_metrics_ref",
    }
)

HTTP_LIKE_FIELD_NAMES = frozenset({"headers", "method", "body", "endpoint", "url", "authorization_header"})
TRANSPORT_FIELD_NAMES = frozenset({"payload", "transport_payload", "body", "media_bytes"})


@dataclass(frozen=True)
class SandboxValidationCallPreparationSecurityScan:
    secret_leakage_detected: bool
    forbidden_field_detected: bool
    http_like_field_detected: bool
    transport_payload_detected: bool
    secret_field_paths: tuple[str, ...] = field(default_factory=tuple)
    forbidden_field_paths: tuple[str, ...] = field(default_factory=tuple)
    http_like_field_paths: tuple[str, ...] = field(default_factory=tuple)
    transport_payload_paths: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "secret_leakage_detected": self.secret_leakage_detected,
            "forbidden_field_detected": self.forbidden_field_detected,
            "http_like_field_detected": self.http_like_field_detected,
            "transport_payload_detected": self.transport_payload_detected,
            "secret_field_paths": list(self.secret_field_paths),
            "forbidden_field_paths": list(self.forbidden_field_paths),
            "http_like_field_paths": list(self.http_like_field_paths),
            "transport_payload_paths": list(self.transport_payload_paths),
        }


def scan_preparation_input(payload: Any) -> SandboxValidationCallPreparationSecurityScan:
    secret_paths: list[str] = []
    forbidden_paths: list[str] = []
    http_like_paths: list[str] = []
    transport_paths: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for raw_key, child in value.items():
                key = str(raw_key)
                normalized = key.strip().lower()
                child_path = f"{path}.{key}" if path else key
                if any(fragment in normalized for fragment in SECRET_KEY_FRAGMENTS):
                    secret_paths.append(child_path)
                if normalized in FORBIDDEN_FIELD_NAMES:
                    forbidden_paths.append(child_path)
                if normalized in HTTP_LIKE_FIELD_NAMES:
                    http_like_paths.append(child_path)
                if normalized in TRANSPORT_FIELD_NAMES:
                    transport_paths.append(child_path)
                visit(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")
        elif isinstance(value, str):
            stripped = value.strip().lower()
            if stripped.startswith("http://") or stripped.startswith("https://"):
                forbidden_paths.append(path or "<value>")
                transport_paths.append(path or "<value>")

    visit(payload, "")
    return SandboxValidationCallPreparationSecurityScan(
        secret_leakage_detected=bool(secret_paths),
        forbidden_field_detected=bool(forbidden_paths),
        http_like_field_detected=bool(http_like_paths),
        transport_payload_detected=bool(transport_paths),
        secret_field_paths=tuple(sorted(dict.fromkeys(secret_paths))),
        forbidden_field_paths=tuple(sorted(dict.fromkeys(forbidden_paths))),
        http_like_field_paths=tuple(sorted(dict.fromkeys(http_like_paths))),
        transport_payload_paths=tuple(sorted(dict.fromkeys(transport_paths))),
    )
