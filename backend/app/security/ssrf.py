from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit, urlunsplit


ALLOWED_SCHEMES = {"http", "https"}
LOCALHOST_NAMES = {"localhost", "localhost.localdomain"}


class SSRFValidationError(ValueError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Unsafe external URL: {reason}")


@dataclass(frozen=True)
class SSRFValidationResult:
    normalized_url: str
    hostname: str
    scheme: str


def validate_external_fetch_url(value: str) -> SSRFValidationResult:
    if not isinstance(value, str) or not value.strip():
        raise SSRFValidationError("missing_url")

    raw_url = value.strip()
    try:
        parts = urlsplit(raw_url)
        hostname = parts.hostname
        _ = parts.port
    except ValueError as exc:
        raise SSRFValidationError("invalid_url") from exc

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise SSRFValidationError("unsupported_scheme")
    if not hostname:
        raise SSRFValidationError("missing_hostname")
    if parts.username or parts.password:
        raise SSRFValidationError("userinfo_not_allowed")

    normalized_host = _normalize_hostname(hostname)
    _validate_hostname(normalized_host)

    normalized_parts = SplitResult(
        scheme=scheme,
        netloc=_normalized_netloc(parts, normalized_host),
        path=parts.path or "",
        query=parts.query or "",
        fragment="",
    )
    return SSRFValidationResult(
        normalized_url=urlunsplit(normalized_parts),
        hostname=normalized_host,
        scheme=scheme,
    )


def redact_url_for_log(value: object) -> str:
    if not isinstance(value, str):
        return "<invalid-url>"
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return "<invalid-url>"
    if not parts.scheme or not parts.netloc:
        return "<invalid-url>"
    host = parts.hostname or "<invalid-host>"
    try:
        port = parts.port
    except ValueError:
        port = None
    netloc = f"{host}:{port}" if port is not None else host
    return urlunsplit((parts.scheme, netloc, parts.path or "", "", ""))


def _normalize_hostname(hostname: str) -> str:
    host = hostname.rstrip(".").lower()
    try:
        return host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise SSRFValidationError("invalid_hostname") from exc


def _validate_hostname(hostname: str) -> None:
    if not hostname:
        raise SSRFValidationError("missing_hostname")
    if hostname in LOCALHOST_NAMES or hostname.endswith(".localhost"):
        raise SSRFValidationError("localhost_not_allowed")
    if "." not in hostname and not _is_ip_literal(hostname):
        raise SSRFValidationError("dotless_hostname_not_allowed")
    if "\\" in hostname or "/" in hostname or "@" in hostname:
        raise SSRFValidationError("ambiguous_hostname")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return

    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped

    if not address.is_global:
        raise SSRFValidationError("non_global_ip_not_allowed")


def _is_ip_literal(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def _normalized_netloc(parts: SplitResult, hostname: str) -> str:
    host = f"[{hostname}]" if ":" in hostname and not hostname.startswith("[") else hostname
    if parts.port is not None:
        return f"{host}:{parts.port}"
    return host
