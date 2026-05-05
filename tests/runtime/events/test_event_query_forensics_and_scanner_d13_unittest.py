from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.observability.event_query.errors import (
    ForensicsBlockedByPolicyError,
    InsufficientFiltersError,
)
from app.observability.event_query.indexer import EventIndexer
from app.observability.event_query.models import EventQueryFilters, QueryProfile
from app.observability.event_query.query_service import EventQueryService


class EventQueryForensicsAndScannerD13Tests(unittest.TestCase):
    def _write_fixture(self, base_out: Path) -> None:
        (base_out / "events").mkdir(parents=True, exist_ok=True)
        (base_out / "audit").mkdir(parents=True, exist_ok=True)
        (base_out / "data").mkdir(parents=True, exist_ok=True)

        events_rows = [
            {
                "event_id": "evt_001",
                "ts": "2026-03-05T10:00:00Z",
                "event_type": "PIPE/D10_STARTED",
                "account_id": "acc_001",
                "window_id": "w_001",
                "job_id": "job_001",
                "publish_id": "pub_001",
                "op_key": "AGG:acc_001:w_001",
                "severity": "INFO",
                "details": {"reason_code": "PIPELINE_STARTED", "token": "secret"},
            },
            {
                "event_id": "evt_002",
                "ts": "2026-03-05T10:01:00Z",
                "event_type": "LOCK/lease_expired",
                "account_id": "acc_001",
                "window_id": "w_001",
                "op_key": "AGG:acc_001:w_001",
                "severity": "ERROR",
                "action_taken": "RETRY",
                "details": {"reason_code": "LEASE_EXPIRED", "stack": "internal"},
            },
            {
                "event_id": "evt_003",
                "ts": "2026-03-05T10:01:00Z",
                "event_type": "IDEMPOTENCY/op_reserved",
                "account_id": "acc_001",
                "window_id": "w_001",
                "op_key": "AGG:acc_001:w_001",
                "severity": "INFO",
                "details": {"reason_code": "IDEMPOTENCY_RESERVED", "huge_blob": "x" * 1000},
            },
        ]
        with (base_out / "events" / "events.jsonl").open("w", encoding="utf-8") as f:
            for row in events_rows:
                f.write(json.dumps(row) + "\n")
            f.write("{invalid_json}\n")
            f.write(json.dumps(["invalid_shape_array"]) + "\n")

        with (base_out / "audit" / "audit.jsonl").open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "event_id": "evt_004",
                "ts": "2026-03-05T09:59:00Z",
                "event_type": "REG/update_done",
                "account_id": "acc_001",
                "window_id": "w_001",
                "details": {"reason_code": "REGISTRY_UPDATED"},
            }) + "\n")

        with (base_out / "data" / "scorecards.jsonl").open("w", encoding="utf-8") as f:
            f.write(json.dumps({
                "event_id": "evt_005",
                "ts": "2026-03-05T10:02:00Z",
                "event_type": "SC/generated",
                "account_id": "acc_001",
                "window_id": "w_001",
                "details": {"reason_code": "SC_OK"},
            }) + "\n")

    def _service(self, base_out: Path, *, enabled: bool = False, allowlist: set[str] | None = None) -> EventQueryService:
        indexer = EventIndexer(base_dir=base_out)
        return EventQueryService(
            indexer=indexer,
            forensics_enabled=enabled,
            forensics_writer_allowlist=allowlist or {"admin", "ci"},
        )

    def _filters(self, **kwargs) -> EventQueryFilters:
        base = {
            "start_ts": "2026-03-05T00:00:00Z",
            "end_ts": "2026-03-06T00:00:00Z",
            "account_id": "acc_001",
        }
        base.update(kwargs)
        return EventQueryFilters(**base)

    def test_forensics_bloqueado_por_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_out = Path(tmp_dir) / "OUT"
            self._write_fixture(base_out)
            service = self._service(base_out, enabled=False)
            with self.assertRaises(ForensicsBlockedByPolicyError):
                service.get_events(
                    self._filters(),
                    profile=QueryProfile.FORENSICS,
                    writer_id="admin",
                )

    def test_forensics_habilitado_com_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_out = Path(tmp_dir) / "OUT"
            self._write_fixture(base_out)
            service = self._service(base_out, enabled=True, allowlist={"admin"})
            result = service.get_events(
                self._filters(),
                profile=QueryProfile.FORENSICS,
                writer_id="admin",
            )
            self.assertGreaterEqual(len(result.items), 1)

    def test_scanner_integration_contadores_e_ordenacao(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_out = Path(tmp_dir) / "OUT"
            self._write_fixture(base_out)
            service = self._service(base_out, enabled=False)
            result = service.get_events(self._filters(), limit=50)

            self.assertEqual(result.stats.invalid_jsonl_lines, 1)
            self.assertEqual(result.stats.invalid_shape_lines, 1)
            self.assertGreaterEqual(len(result.items), 4)

            ordered = sorted(result.items, key=lambda item: (item.ts, item.event_id or ""), reverse=True)
            self.assertEqual([i.event_id for i in result.items], [i.event_id for i in ordered])

    def test_operational_insufficient_filters_com_apenas_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_out = Path(tmp_dir) / "OUT"
            self._write_fixture(base_out)
            service = self._service(base_out, enabled=False)
            filters = EventQueryFilters(
                start_ts="2026-03-05T00:00:00Z",
                end_ts="2026-03-06T00:00:00Z",
                event_type_prefix="PIPE/",
            )
            with self.assertRaises(InsufficientFiltersError):
                service.get_events(filters)

    def test_redaction_obrigatoria_na_saida_publica(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_out = Path(tmp_dir) / "OUT"
            self._write_fixture(base_out)
            service = self._service(base_out, enabled=True, allowlist={"admin"})
            result = service.get_events(
                self._filters(),
                profile=QueryProfile.FORENSICS,
                writer_id="admin",
            )

            by_id = {item.event_id: item for item in result.items}
            details = by_id["evt_001"].details or {}
            self.assertIn("reason_code", details)
            self.assertNotIn("token", details)


if __name__ == "__main__":
    unittest.main()
