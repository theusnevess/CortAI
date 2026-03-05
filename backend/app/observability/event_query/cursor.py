from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from app.observability.event_query.errors import (
    CursorFiltersMismatchError,
    CursorInvalidEncodingError,
    CursorInvalidJSONError,
    CursorMissingFieldsError,
    CursorUnsupportedVersionError,
)
from app.observability.event_query.models import parse_iso_utc

CURSOR_VERSION = "1"


@dataclass(frozen=True)
class CursorLast:
    """Marcador do ultimo item da pagina atual para seek."""

    ts: str
    event_id: str


@dataclass(frozen=True)
class SeekCursor:
    """Shape canonico do cursor v1.0 usado na paginacao keyset."""

    v: str
    filters_hash: str
    last: CursorLast
    issued_at: str
    sig: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "v": self.v,
            "filters_hash": self.filters_hash,
            "last": {"ts": self.last.ts, "event_id": self.last.event_id},
            "issued_at": self.issued_at,
        }
        if self.sig is not None:
            payload["sig"] = self.sig
        return payload


def encode_cursor(cursor: SeekCursor) -> str:
    """Codifica cursor em JSON canonico + base64url sem padding."""
    payload = validate_cursor_payload(cursor.to_payload())
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _b64url_encode(raw)


def decode_cursor(encoded: str) -> SeekCursor:
    """Decodifica cursor base64url e valida shape/version obrigatorios."""
    try:
        raw = _b64url_decode(encoded)
    except Exception as exc:  # noqa: BLE001
        raise CursorInvalidEncodingError() from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise CursorInvalidEncodingError() from exc
    except json.JSONDecodeError as exc:
        raise CursorInvalidJSONError() from exc

    payload = validate_cursor_payload(payload)
    last = payload["last"]
    return SeekCursor(
        v=payload["v"],
        filters_hash=payload["filters_hash"],
        last=CursorLast(ts=last["ts"], event_id=last["event_id"]),
        issued_at=payload["issued_at"],
        sig=payload.get("sig"),
    )


def validate_cursor_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Valida campos obrigatorios do cursor e normaliza payload."""
    if not isinstance(payload, dict):
        raise CursorInvalidJSONError()

    required_fields = ("v", "filters_hash", "last", "issued_at")
    if any(field not in payload for field in required_fields):
        raise CursorMissingFieldsError()

    if payload.get("v") != CURSOR_VERSION:
        raise CursorUnsupportedVersionError()

    filters_hash = payload.get("filters_hash")
    issued_at = payload.get("issued_at")
    last = payload.get("last")

    if not isinstance(filters_hash, str) or not filters_hash:
        raise CursorMissingFieldsError()
    if not isinstance(issued_at, str) or not issued_at:
        raise CursorMissingFieldsError()
    if not isinstance(last, dict):
        raise CursorMissingFieldsError()

    last_ts = last.get("ts")
    last_event_id = last.get("event_id")
    if not isinstance(last_ts, str) or not last_ts:
        raise CursorMissingFieldsError()
    if not isinstance(last_event_id, str) or not last_event_id:
        raise CursorMissingFieldsError()

    # Valida timestamp para falhar cedo em cursores malformados.
    parse_iso_utc(issued_at)
    parse_iso_utc(last_ts)

    normalized: dict[str, Any] = {
        "v": CURSOR_VERSION,
        "filters_hash": filters_hash,
        "last": {"ts": last_ts, "event_id": last_event_id},
        "issued_at": issued_at,
    }
    if "sig" in payload and payload["sig"] is not None:
        if not isinstance(payload["sig"], str) or not payload["sig"]:
            raise CursorMissingFieldsError()
        normalized["sig"] = payload["sig"]
    return normalized


def validate_cursor_filters_hash(cursor: SeekCursor, current_filters_hash: str) -> None:
    """Garante bind entre cursor e filtros atuais da consulta."""
    if cursor.filters_hash != current_filters_hash:
        raise CursorFiltersMismatchError()


def _b64url_encode(data: bytes) -> str:
    encoded = base64.urlsafe_b64encode(data).decode("ascii")
    return encoded.rstrip("=")


def _b64url_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value.strip():
        raise CursorInvalidEncodingError()
    cleaned = value.strip()
    pad = "=" * ((4 - (len(cleaned) % 4)) % 4)
    return base64.urlsafe_b64decode((cleaned + pad).encode("ascii"))
