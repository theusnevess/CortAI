from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass


@dataclass(frozen=True)
class SigningPolicy:
    """Politica de assinatura de cursor (Profile A/B)."""

    enabled: bool
    secret: bytes


def sign_cursor_payload(payload_json: str, secret: bytes) -> str:
    """Assina payload canonico com HMAC-SHA256 e retorna base64url sem padding."""
    digest = hmac.new(secret, payload_json.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def verify_cursor_signature(payload_json: str, sig: str, secret: bytes) -> bool:
    """Valida assinatura HMAC de forma segura contra timing attacks."""
    expected = sign_cursor_payload(payload_json, secret)
    return hmac.compare_digest(expected, sig)
