from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.observability.event_query.cursor import CursorLast, SeekCursor, encode_cursor
from app.observability.event_query.errors import CursorFiltersMismatchError
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters
from app.observability.event_query.query_filters import build_filters_hash
from app.observability.event_query.query_service import EventQueryService


class EventQueryCursorFiltersMismatchD14Tests(unittest.TestCase):
    def _filters_a(self) -> EventQueryFilters:
        return EventQueryFilters(
            start_ts="2026-03-05T00:00:00Z",
            end_ts="2026-03-06T00:00:00Z",
            account_id="acc_001",
            event_type="PIPE/D10_FINISHED",
        )

    def _filters_b(self) -> EventQueryFilters:
        return EventQueryFilters(
            start_ts="2026-03-05T00:00:00Z",
            end_ts="2026-03-06T00:00:00Z",
            account_id="acc_002",
            event_type="PIPE/D10_FINISHED",
        )

    def _cursor_for_filters(self, filters: EventQueryFilters) -> str:
        return encode_cursor(
            SeekCursor(
                v="1",
                filters_hash=build_filters_hash(filters),
                last=CursorLast(ts="2026-03-05T10:00:00Z", event_id="evt_001"),
                issued_at="2026-03-05T10:00:01Z",
            )
        )

    def _service(self) -> EventQueryService:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name) / "OUT"
        for name in ["events", "audit", "data"]:
            (out / name).mkdir(parents=True, exist_ok=True)
        return EventQueryService(indexer=EventIndexer(base_dir=out))

    def test_cursor_com_filtros_iguais_ok(self) -> None:
        service = self._service()
        filters = self._filters_a()
        cursor = self._cursor_for_filters(filters)
        result = service.get_events(filters, cursor=cursor)
        self.assertEqual(len(result.items), 0)

    def test_cursor_com_filtros_diferentes_mismatch(self) -> None:
        service = self._service()
        cursor = self._cursor_for_filters(self._filters_a())
        with self.assertRaises(CursorFiltersMismatchError):
            service.get_events(self._filters_b(), cursor=cursor)


if __name__ == "__main__":
    unittest.main()
