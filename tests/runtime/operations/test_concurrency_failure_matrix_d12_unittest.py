from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.concurrency.idempotency import IdempotencyManager
from app.concurrency.lease import LeaseManager
from app.jobs.window_pipeline import WindowPipelineD12Deps, run_window_pipeline_after_aggregation
from app.jobs.window_post_pipeline import WindowPostPipelineDeps


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class CallCounter:
    def __init__(self, result: dict[str, Any] | None = None) -> None:
        self.result = result or {"status": "WRITTEN"}
        self.calls = 0

    def __call__(self, *, account_id: str, window_id: str) -> dict[str, Any]:
        self.calls += 1
        return dict(self.result)


class WindowPipelineD12FailureMatrixTests(unittest.TestCase):
    def _deps(self) -> tuple[WindowPostPipelineDeps, CallCounter, CallCounter, CallCounter]:
        guard = CallCounter(result={"blocked": False})
        scorecard = CallCounter(result={"status": "WRITTEN"})
        attribution = CallCounter(result={"status": "WRITTEN"})
        learning = CallCounter(result={"status": "WRITTEN"})
        deps = WindowPostPipelineDeps(
            guard_service=guard,
            scorecard_service=scorecard,
            attribution_service=attribution,
            strategy_learning_service=learning,
        )
        return deps, scorecard, attribution, learning

    def test_double_apply_payload_diferente_retorna_conflict_block(self) -> None:
        clock = FakeClock()
        lease_manager = LeaseManager(clock=clock, event_sink=lambda _: None)
        events: list[dict[str, Any]] = []
        idempotency = IdempotencyManager(event_sink=events.append, event_source=lambda: list(events), clock=clock)

        deps, _, _, _ = self._deps()
        snapshot_kwargs = {
            "publish_ids": ["pub_1"],
            "video_ids": ["vid_1"],
            "captured_range": {"start": "2026-03-01T00:00:00Z", "end": "2026-03-04T00:00:00Z"},
            "source_refs": {"publish_records": "sha256:a", "video_metrics": "sha256:b"},
        }

        first = run_window_pipeline_after_aggregation(
            account_id="acc_1",
            window_id="w_1",
            deps=deps,
            window_metrics_persisted=True,
            d12_deps=WindowPipelineD12Deps(
                lease_manager=lease_manager,
                idempotency_manager=idempotency,
                snapshot_service=lambda **_: {"status": "WRITTEN", "snapshot": {}},
                owner_id="owner-1",
                agg_payload_hash="hash-a",
                snapshot_kwargs=snapshot_kwargs,
            ),
        )
        second = run_window_pipeline_after_aggregation(
            account_id="acc_1",
            window_id="w_1",
            deps=deps,
            window_metrics_persisted=True,
            d12_deps=WindowPipelineD12Deps(
                lease_manager=lease_manager,
                idempotency_manager=idempotency,
                snapshot_service=lambda **_: {"status": "WRITTEN", "snapshot": {}},
                owner_id="owner-1",
                agg_payload_hash="hash-b",
                snapshot_kwargs=snapshot_kwargs,
            ),
        )

        self.assertEqual(first.status, "FINISHED")
        self.assertEqual(second.status, "SKIPPED_BLOCKED_CONFLICT")
        self.assertEqual(second.reason_code, "IDEMPOTENCY_CONFLICT")

    def test_lease_expiry_no_meio_aborta_sem_executar_d10(self) -> None:
        clock = FakeClock()
        lease_manager = LeaseManager(clock=clock, event_sink=lambda _: None)
        events: list[dict[str, Any]] = []
        idempotency = IdempotencyManager(event_sink=events.append, event_source=lambda: list(events), clock=clock)
        deps, scorecard, attribution, learning = self._deps()

        def snapshot_service(**_: Any) -> dict[str, Any]:
            clock.advance(200)
            return {"status": "WRITTEN", "snapshot": {}}

        result = run_window_pipeline_after_aggregation(
            account_id="acc_1",
            window_id="w_1",
            deps=deps,
            window_metrics_persisted=True,
            d12_deps=WindowPipelineD12Deps(
                lease_manager=lease_manager,
                idempotency_manager=idempotency,
                snapshot_service=snapshot_service,
                owner_id="owner-1",
                agg_payload_hash="hash-a",
                snapshot_kwargs={
                    "publish_ids": ["pub_1"],
                    "video_ids": ["vid_1"],
                    "captured_range": {"start": "2026-03-01T00:00:00Z", "end": "2026-03-04T00:00:00Z"},
                    "source_refs": {"publish_records": "sha256:a", "video_metrics": "sha256:b"},
                },
            ),
        )

        self.assertEqual(result.status, "SKIPPED_BLOCKED_LEASE_EXPIRED")
        self.assertEqual(scorecard.calls, 0)
        self.assertEqual(attribution.calls, 0)
        self.assertEqual(learning.calls, 0)

    def test_snapshot_parcial_bloqueia_pipeline(self) -> None:
        clock = FakeClock()
        lease_manager = LeaseManager(clock=clock, event_sink=lambda _: None)
        events: list[dict[str, Any]] = []
        idempotency = IdempotencyManager(event_sink=events.append, event_source=lambda: list(events), clock=clock)
        deps, scorecard, _, _ = self._deps()

        result = run_window_pipeline_after_aggregation(
            account_id="acc_1",
            window_id="w_1",
            deps=deps,
            window_metrics_persisted=True,
            d12_deps=WindowPipelineD12Deps(
                lease_manager=lease_manager,
                idempotency_manager=idempotency,
                snapshot_service=lambda **_: {"status": "PARTIAL", "snapshot": {}},
                owner_id="owner-1",
                agg_payload_hash="hash-a",
                snapshot_kwargs={
                    "publish_ids": ["pub_1"],
                    "video_ids": ["vid_1"],
                    "captured_range": {"start": "2026-03-01T00:00:00Z", "end": "2026-03-04T00:00:00Z"},
                    "source_refs": {"publish_records": "sha256:a", "video_metrics": "sha256:b"},
                },
            ),
        )

        self.assertEqual(result.status, "SKIPPED_BLOCKED_SNAPSHOT")
        self.assertEqual(result.reason_code, "SNAPSHOT_MISSING")
        self.assertEqual(scorecard.calls, 0)


if __name__ == "__main__":
    unittest.main()
