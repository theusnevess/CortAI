from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.jobs.window_post_pipeline import WindowPostPipelineDeps, run_window_post_pipeline


class FakeExecutionRepo:
    def __init__(self) -> None:
        self.ops: set[str] = set()

    def has_op(self, op_key: str) -> bool:
        return op_key in self.ops

    def mark_op(self, op_key: str) -> None:
        self.ops.add(op_key)


class ServiceCallCounter:
    def __init__(self, result: dict[str, Any] | None = None, exc: Exception | None = None) -> None:
        self.result = result or {"status": "WRITTEN"}
        self.exc = exc
        self.calls = 0

    def __call__(self, *, account_id: str, window_id: str) -> dict[str, Any]:
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        return dict(self.result)


class WindowPostPipelineD10Tests(unittest.TestCase):
    def test_blocked_pula_todas_etapas(self) -> None:
        guard = ServiceCallCounter(result={"blocked": True})
        scorecard = ServiceCallCounter()
        attribution = ServiceCallCounter()
        learning = ServiceCallCounter()

        result = run_window_post_pipeline(
            account_id="acc_1",
            window_id="w_1",
            deps=WindowPostPipelineDeps(
                guard_service=guard,
                scorecard_service=scorecard,
                attribution_service=attribution,
                strategy_learning_service=learning,
                execution_repo=FakeExecutionRepo(),
            ),
        )

        self.assertEqual(result.status, "SKIPPED_BLOCKED")
        self.assertEqual(scorecard.calls, 0)
        self.assertEqual(attribution.calls, 0)
        self.assertEqual(learning.calls, 0)

    def test_happy_path_roda_scorecard_attribution_learning(self) -> None:
        result = run_window_post_pipeline(
            account_id="acc_1",
            window_id="w_1",
            deps=WindowPostPipelineDeps(
                guard_service=ServiceCallCounter(result={"blocked": False}),
                scorecard_service=ServiceCallCounter(result={"status": "WRITTEN"}),
                attribution_service=ServiceCallCounter(result={"status": "WRITTEN"}),
                strategy_learning_service=ServiceCallCounter(result={"status": "WRITTEN"}),
                execution_repo=FakeExecutionRepo(),
            ),
        )
        self.assertEqual(result.status, "FINISHED")
        self.assertEqual(result.reason_code, "PIPELINE_OK")

    def test_scorecard_noop_continua_pipeline(self) -> None:
        scorecard = ServiceCallCounter(result={"status": "NOOP"})
        attribution = ServiceCallCounter(result={"status": "WRITTEN"})
        learning = ServiceCallCounter(result={"status": "WRITTEN"})
        result = run_window_post_pipeline(
            account_id="acc_1",
            window_id="w_1",
            deps=WindowPostPipelineDeps(
                guard_service=ServiceCallCounter(result={"blocked": False}),
                scorecard_service=scorecard,
                attribution_service=attribution,
                strategy_learning_service=learning,
            ),
        )
        self.assertEqual(result.status, "FINISHED")
        self.assertEqual(attribution.calls, 1)
        self.assertEqual(learning.calls, 1)

    def test_attribution_metrics_missing_pula_learning(self) -> None:
        learning = ServiceCallCounter(result={"status": "WRITTEN"})
        result = run_window_post_pipeline(
            account_id="acc_1",
            window_id="w_1",
            deps=WindowPostPipelineDeps(
                guard_service=ServiceCallCounter(result={"blocked": False}),
                scorecard_service=ServiceCallCounter(result={"status": "WRITTEN"}),
                attribution_service=ServiceCallCounter(exc=ValueError("ATTRIBUTION_METRICS_MISSING")),
                strategy_learning_service=learning,
            ),
        )
        self.assertEqual(result.status, "SKIPPED_ATTRIBUTION_MISSING")
        self.assertEqual(learning.calls, 0)

    def test_learning_noop_pipeline_ok(self) -> None:
        result = run_window_post_pipeline(
            account_id="acc_1",
            window_id="w_1",
            deps=WindowPostPipelineDeps(
                guard_service=ServiceCallCounter(result={"blocked": False}),
                scorecard_service=ServiceCallCounter(result={"status": "WRITTEN"}),
                attribution_service=ServiceCallCounter(result={"status": "WRITTEN"}),
                strategy_learning_service=ServiceCallCounter(result={"status": "NOOP"}),
            ),
        )
        self.assertEqual(result.status, "FINISHED")

    def test_learning_conflict_retorna_finished_conflict(self) -> None:
        result = run_window_post_pipeline(
            account_id="acc_1",
            window_id="w_1",
            deps=WindowPostPipelineDeps(
                guard_service=ServiceCallCounter(result={"blocked": False}),
                scorecard_service=ServiceCallCounter(result={"status": "WRITTEN"}),
                attribution_service=ServiceCallCounter(result={"status": "WRITTEN"}),
                strategy_learning_service=ServiceCallCounter(result={"status": "CONFLICT"}),
            ),
        )
        self.assertEqual(result.status, "FINISHED_CONFLICT")
        self.assertEqual(result.reason_code, "STRATEGY_PATCH_CONFLICT")

    def test_idempotencia_op_key_segunda_execucao_noop(self) -> None:
        execution_repo = FakeExecutionRepo()
        deps = WindowPostPipelineDeps(
            guard_service=ServiceCallCounter(result={"blocked": False}),
            scorecard_service=ServiceCallCounter(result={"status": "WRITTEN"}),
            attribution_service=ServiceCallCounter(result={"status": "WRITTEN"}),
            strategy_learning_service=ServiceCallCounter(result={"status": "WRITTEN"}),
            execution_repo=execution_repo,
        )
        first = run_window_post_pipeline(account_id="acc_1", window_id="w_1", deps=deps)
        second = run_window_post_pipeline(account_id="acc_1", window_id="w_1", deps=deps)

        self.assertEqual(first.status, "FINISHED")
        self.assertEqual(second.status, "NOOP_EXECUTION")


if __name__ == "__main__":
    unittest.main()
