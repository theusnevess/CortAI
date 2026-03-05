from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.observability.event_query.models import (
    EventQueryResult,
    EventQueryStats,
    EventRecord,
    TraceRequest,
)
from app.observability.event_query.trace_builder import TraceBuilder


class FakeQueryService:
    def __init__(self, items: list[EventRecord]) -> None:
        self.items = items

    def get_events(self, filters, limit: int = 500) -> EventQueryResult:  # noqa: ANN001
        selected = sorted(self.items, key=lambda ev: (ev.ts, ev.event_id or ""), reverse=True)[:limit]
        return EventQueryResult(items=selected, stats=EventQueryStats())


def _event(
    event_id: str,
    ts: str,
    event_type: str,
    *,
    severity: str | None = "INFO",
    action_taken: str | None = "OBSERVE",
    details: dict | None = None,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        ts=ts,
        event_type=event_type,
        severity=severity,
        action_taken=action_taken,
        account_id="acc_001",
        window_id="w_001",
        job_id="job_001",
        publish_id="pub_001",
        op_key="AGG:acc_001:w_001",
        details=details,
    )


class EventQueryTraceBuilderD13Tests(unittest.TestCase):
    def test_happy_path_ok(self) -> None:
        items = [
            _event("e1", "2026-03-05T10:00:00Z", "SC/generated", details={"reason_code": "SC_OK"}),
            _event("e2", "2026-03-05T10:01:00Z", "ATTR/written", details={"reason_code": "ATTR_OK"}),
            _event("e3", "2026-03-05T10:02:00Z", "SL/patch_written", details={"reason_code": "SL_OK"}),
        ]
        trace = TraceBuilder(FakeQueryService(items)).build_trace(TraceRequest(job_id="job_001"))

        self.assertEqual(trace.summary.final_status, "OK")
        self.assertEqual(trace.summary.last_event_id, "e3")
        self.assertEqual(len(trace.timeline), 3)

    def test_blocked_por_guard(self) -> None:
        items = [
            _event(
                "e1",
                "2026-03-05T10:00:00Z",
                "GUARD/consistency_blocked",
                action_taken="BLOCK",
                details={"reason_code": "CONSISTENCY_VIOLATION_BLOCKED"},
            ),
            _event("e2", "2026-03-05T10:00:10Z", "PIPE/D10_SKIPPED_BLOCKED"),
        ]
        trace = TraceBuilder(FakeQueryService(items)).build_trace(TraceRequest(window_id="w_001"))

        self.assertEqual(trace.summary.final_status, "BLOCKED")
        self.assertEqual(trace.summary.dominant_reason_code, "CONSISTENCY_VIOLATION_BLOCKED")
        self.assertEqual(trace.summary.first_failure_event_id, "e1")

    def test_failed_por_lock_expiry(self) -> None:
        items = [
            _event(
                "e1",
                "2026-03-05T10:00:00Z",
                "LOCK/lease_expired",
                severity="ERROR",
                action_taken="RETRY",
                details={"reason_code": "LEASE_EXPIRED"},
            )
        ]
        trace = TraceBuilder(FakeQueryService(items)).build_trace(TraceRequest(publish_id="pub_001"))

        self.assertEqual(trace.summary.final_status, "FAILED")
        self.assertEqual(trace.summary.dominant_reason_code, "LEASE_EXPIRED")

    def test_unknown_sem_evento_classificavel(self) -> None:
        items = [_event("e1", "2026-03-05T10:00:00Z", "GOV/context_injected", details=None)]
        trace = TraceBuilder(FakeQueryService(items)).build_trace(TraceRequest(job_id="job_001"))

        self.assertEqual(trace.summary.final_status, "UNKNOWN")

    def test_stats_por_family_e_severity(self) -> None:
        items = [
            _event("e1", "2026-03-05T10:00:00Z", "SC/generated", severity="INFO"),
            _event("e2", "2026-03-05T10:01:00Z", "SC/generated", severity="WARN", action_taken="DEGRADE"),
            _event("e3", "2026-03-05T10:02:00Z", "ATTR/written", severity="INFO"),
        ]
        trace = TraceBuilder(FakeQueryService(items)).build_trace(TraceRequest(window_id="w_001"))

        self.assertEqual(trace.stats["family"]["SC"], 2)
        self.assertEqual(trace.stats["family"]["ATTR"], 1)
        self.assertEqual(trace.stats["severity"]["INFO"], 2)
        self.assertEqual(trace.stats["severity"]["WARN"], 1)


if __name__ == "__main__":
    unittest.main()
