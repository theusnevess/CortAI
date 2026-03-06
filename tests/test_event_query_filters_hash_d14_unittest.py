from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.observability.event_query.models import EventQueryFilters
from app.observability.event_query.query_filters import build_filters_hash


class EventQueryFiltersHashD14Tests(unittest.TestCase):
    def test_mesmo_conteudo_ordem_diferente_mesmo_hash(self) -> None:
        filters_a = {
            "end_ts": "2026-03-06T00:00:00Z",
            "start_ts": "2026-03-05T00:00:00Z",
            "account_id": "acc_001",
            "event_type": "PIPE/D10_FINISHED",
        }
        filters_b = {
            "account_id": "acc_001",
            "event_type": "PIPE/D10_FINISHED",
            "start_ts": "2026-03-05T00:00:00Z",
            "end_ts": "2026-03-06T00:00:00Z",
        }
        self.assertEqual(build_filters_hash(filters_a), build_filters_hash(filters_b))

    def test_lista_em_ordem_diferente_mesmo_hash(self) -> None:
        filters_a = {
            "start_ts": "2026-03-05T00:00:00Z",
            "end_ts": "2026-03-06T00:00:00Z",
            "account_id": "acc_001",
            "families": ["LOCK", "PIPE", "ATTR"],
        }
        filters_b = {
            "start_ts": "2026-03-05T00:00:00Z",
            "end_ts": "2026-03-06T00:00:00Z",
            "account_id": "acc_001",
            "families": ["ATTR", "LOCK", "PIPE"],
        }
        self.assertEqual(build_filters_hash(filters_a), build_filters_hash(filters_b))

    def test_mudanca_de_filtro_muda_hash(self) -> None:
        base = EventQueryFilters(
            start_ts="2026-03-05T00:00:00Z",
            end_ts="2026-03-06T00:00:00Z",
            account_id="acc_001",
            event_type="PIPE/D10_FINISHED",
        )
        changed = EventQueryFilters(
            start_ts="2026-03-05T00:00:00Z",
            end_ts="2026-03-06T00:00:00Z",
            account_id="acc_002",
            event_type="PIPE/D10_FINISHED",
        )
        self.assertNotEqual(build_filters_hash(base), build_filters_hash(changed))

    def test_limit_nao_altera_hash(self) -> None:
        base = {
            "start_ts": "2026-03-05T00:00:00Z",
            "end_ts": "2026-03-06T00:00:00Z",
            "account_id": "acc_001",
            "event_type": "PIPE/D10_FINISHED",
            "limit": 50,
        }
        changed_limit = dict(base)
        changed_limit["limit"] = 200
        self.assertEqual(build_filters_hash(base), build_filters_hash(changed_limit))


if __name__ == "__main__":
    unittest.main()
