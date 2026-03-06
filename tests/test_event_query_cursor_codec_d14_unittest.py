from __future__ import annotations

import base64
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.observability.event_query.cursor import (
    CursorLast,
    SeekCursor,
    decode_cursor,
    encode_cursor,
    validate_cursor_filters_hash,
    validate_cursor_signature,
)
from app.observability.event_query.cursor_signing import SigningPolicy
from app.observability.event_query.errors import (
    CursorFiltersMismatchError,
    CursorInvalidEncodingError,
    CursorInvalidJSONError,
    CursorMissingFieldsError,
    CursorSignatureInvalidError,
    CursorUnsupportedVersionError,
)


class EventQueryCursorCodecD14Tests(unittest.TestCase):
    def test_roundtrip_encode_decode(self) -> None:
        cursor = SeekCursor(
            v="1",
            filters_hash="sha256:abc123",
            last=CursorLast(ts="2026-03-05T10:00:00Z", event_id="evt_001"),
            issued_at="2026-03-05T10:01:00Z",
        )
        encoded = encode_cursor(cursor)
        decoded = decode_cursor(encoded)
        self.assertEqual(decoded, cursor)

    def test_cursor_invalid_encoding(self) -> None:
        with self.assertRaises(CursorInvalidEncodingError):
            decode_cursor("***not-base64url***")

    def test_cursor_invalid_json(self) -> None:
        bad = base64.urlsafe_b64encode(b"not-json").decode("ascii").rstrip("=")
        with self.assertRaises(CursorInvalidJSONError):
            decode_cursor(bad)

    def test_cursor_unsupported_version(self) -> None:
        payload = {
            "v": "2",
            "filters_hash": "sha256:abc",
            "last": {"ts": "2026-03-05T10:00:00Z", "event_id": "evt_1"},
            "issued_at": "2026-03-05T10:00:01Z",
        }
        raw = json.dumps(payload).encode("utf-8")
        token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        with self.assertRaises(CursorUnsupportedVersionError):
            decode_cursor(token)

    def test_cursor_missing_fields(self) -> None:
        payload = {
            "v": "1",
            "filters_hash": "sha256:abc",
            "last": {"ts": "2026-03-05T10:00:00Z"},
            "issued_at": "2026-03-05T10:00:01Z",
        }
        raw = json.dumps(payload).encode("utf-8")
        token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
        with self.assertRaises(CursorMissingFieldsError):
            decode_cursor(token)

    def test_cursor_filters_mismatch(self) -> None:
        cursor = SeekCursor(
            v="1",
            filters_hash="sha256:expected",
            last=CursorLast(ts="2026-03-05T10:00:00Z", event_id="evt_001"),
            issued_at="2026-03-05T10:01:00Z",
        )
        with self.assertRaises(CursorFiltersMismatchError):
            validate_cursor_filters_hash(cursor, "sha256:other")

    def test_validate_signature_profile_b_sem_sig_invalida(self) -> None:
        cursor = SeekCursor(
            v="1",
            filters_hash="sha256:expected",
            last=CursorLast(ts="2026-03-05T10:00:00Z", event_id="evt_001"),
            issued_at="2026-03-05T10:01:00Z",
            sig=None,
        )
        with self.assertRaises(CursorSignatureInvalidError):
            validate_cursor_signature(cursor, SigningPolicy(enabled=True, secret=b"secret"))


if __name__ == "__main__":
    unittest.main()
