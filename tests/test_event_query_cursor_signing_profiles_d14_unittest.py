from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.observability.event_query.cursor import CursorLast, SeekCursor, decode_cursor, encode_cursor, validate_cursor_signature
from app.observability.event_query.cursor_signing import SigningPolicy
from app.observability.event_query.errors import CursorSignatureInvalidError
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters
from app.observability.event_query.query_service import EventQueryService


class EventQueryCursorSigningProfilesD14Tests(unittest.TestCase):
    def _filters(self) -> EventQueryFilters:
        return EventQueryFilters(
            start_ts="2026-03-05T00:00:00Z",
            end_ts="2026-03-06T00:00:00Z",
            account_id="acc_001",
            event_type="PIPE/D10_FINISHED",
        )

    def _service(self, policy: SigningPolicy) -> EventQueryService:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "OUT"
        for name in ["events", "audit", "data"]:
            (out / name).mkdir(parents=True, exist_ok=True)
        return EventQueryService(indexer=EventIndexer(base_dir=out), cursor_signing_policy=policy)

    def _cursor_no_sig(self, filters_hash: str = "sha256:x") -> str:
        return encode_cursor(
            SeekCursor(
                v="1",
                filters_hash=filters_hash,
                last=CursorLast(ts="2026-03-05T10:00:00Z", event_id="evt_001"),
                issued_at="2026-03-05T10:01:00Z",
            ),
            signing=SigningPolicy(enabled=False, secret=b""),
        )

    def _cursor_with_sig(self, filters_hash: str = "sha256:x", secret: bytes = b"secret") -> str:
        return encode_cursor(
            SeekCursor(
                v="1",
                filters_hash=filters_hash,
                last=CursorLast(ts="2026-03-05T10:00:00Z", event_id="evt_001"),
                issued_at="2026-03-05T10:01:00Z",
            ),
            signing=SigningPolicy(enabled=True, secret=secret),
        )

    def test_profile_a_off_cursor_sem_sig_ok(self) -> None:
        policy = SigningPolicy(enabled=False, secret=b"dev")
        cursor_obj = decode_cursor(self._cursor_no_sig())
        validate_cursor_signature(cursor_obj, policy)

    def test_profile_a_off_sig_invalida_ok(self) -> None:
        cursor_obj = SeekCursor(
            v="1",
            filters_hash="sha256:x",
            last=CursorLast(ts="2026-03-05T10:00:00Z", event_id="evt_001"),
            issued_at="2026-03-05T10:01:00Z",
            sig="invalid",
        )
        validate_cursor_signature(cursor_obj, SigningPolicy(enabled=False, secret=b"dev"))

    def test_profile_b_on_sem_sig_invalida(self) -> None:
        cursor_obj = decode_cursor(self._cursor_no_sig())
        with self.assertRaises(CursorSignatureInvalidError):
            validate_cursor_signature(cursor_obj, SigningPolicy(enabled=True, secret=b"secret"))

    def test_profile_b_on_sig_invalida(self) -> None:
        cursor_obj = SeekCursor(
            v="1",
            filters_hash="sha256:x",
            last=CursorLast(ts="2026-03-05T10:00:00Z", event_id="evt_001"),
            issued_at="2026-03-05T10:01:00Z",
            sig="invalid",
        )
        with self.assertRaises(CursorSignatureInvalidError):
            validate_cursor_signature(cursor_obj, SigningPolicy(enabled=True, secret=b"secret"))

    def test_profile_b_on_sig_valida_ok(self) -> None:
        token = self._cursor_with_sig(secret=b"secret")
        cursor_obj = decode_cursor(token)
        validate_cursor_signature(cursor_obj, SigningPolicy(enabled=True, secret=b"secret"))

    def test_cursor_adulterado_gera_signature_invalid(self) -> None:
        token = self._cursor_with_sig(secret=b"secret")
        cursor_obj = decode_cursor(token)
        tampered = SeekCursor(
            v=cursor_obj.v,
            filters_hash=cursor_obj.filters_hash,
            last=CursorLast(ts=cursor_obj.last.ts, event_id="evt_999"),
            issued_at=cursor_obj.issued_at,
            sig=cursor_obj.sig,
        )
        with self.assertRaises(CursorSignatureInvalidError):
            validate_cursor_signature(tampered, SigningPolicy(enabled=True, secret=b"secret"))

    def test_query_service_profile_b_enforcement(self) -> None:
        policy = SigningPolicy(enabled=True, secret=b"secret")
        service = self._service(policy)
        filters = self._filters()
        token = self._cursor_no_sig(filters_hash="sha256:any")
        with self.assertRaises(CursorSignatureInvalidError):
            service.get_events(filters, cursor=token)


if __name__ == "__main__":
    unittest.main()
