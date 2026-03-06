from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


CollectorErrorType = Literal[
    "invalid_input",
    "http_4xx",
    "http_5xx",
    "ssl_cert_verify_failed",
    "dns_failed",
    "timeout",
    "upstream_blocked",
    "unknown",
]


@dataclass(frozen=True)
class CollectorError(Exception):
    """Representa uma falha classificada do coletor de midia."""

    error_type: CollectorErrorType
    message: str
    http_status: Optional[int] = None
    retryable: bool = False
    cause: Optional[str] = None

    def to_dict(self) -> dict:
        """Retorna uma representacao serializavel da falha."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "http_status": self.http_status,
            "retryable": self.retryable,
            "cause": self.cause,
        }
