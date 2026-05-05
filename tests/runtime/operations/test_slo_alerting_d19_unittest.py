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

from app.ops.alerts.generator import generate_alerts
from app.ops.alerts.store_jsonl import persist_alert_bundle
from app.ops.slo.evaluator import evaluate_slos, metrics_from_load_results


class SloAlertingD19Tests(unittest.TestCase):
    def _healthy_metrics(self) -> dict[str, float]:
        return {
            "event_query_p95_ms": 120.0,
            "event_query_error_rate": 0.001,
            "event_query_fallback_rate": 0.02,
            "window_pipeline_success_rate": 0.995,
            "window_post_pipeline_success_rate": 0.992,
            "lease_denied_rate": 0.01,
            "strategy_patch_conflict_rate": 0.005,
            "double_apply_count": 0.0,
            "snapshot_partial_count": 0.0,
        }

    def test_tudo_dentro_do_limite_sem_alerta_critico(self) -> None:
        evaluation = evaluate_slos(self._healthy_metrics())
        alerts = generate_alerts(evaluation)

        self.assertEqual(evaluation.overall_status, "PASS")
        self.assertEqual(alerts, [])

    def test_p95_acima_do_limite_gera_alerta(self) -> None:
        metrics = self._healthy_metrics()
        metrics["event_query_p95_ms"] = 520.0

        evaluation = evaluate_slos(metrics)
        alerts = generate_alerts(evaluation)

        self.assertEqual(evaluation.overall_status, "CRITICAL")
        self.assertTrue(any(alert.metric_name == "event_query_p95_ms" for alert in alerts))

    def test_fallback_rate_alto_gera_alerta(self) -> None:
        metrics = self._healthy_metrics()
        metrics["event_query_fallback_rate"] = 0.20

        alerts = generate_alerts(evaluate_slos(metrics))
        self.assertTrue(any(alert.metric_name == "event_query_fallback_rate" for alert in alerts))

    def test_conflict_rate_alto_gera_alerta(self) -> None:
        metrics = self._healthy_metrics()
        metrics["strategy_patch_conflict_rate"] = 0.04

        alerts = generate_alerts(evaluate_slos(metrics))
        self.assertTrue(any(alert.metric_name == "strategy_patch_conflict_rate" for alert in alerts))

    def test_double_apply_maior_que_zero_gera_critical(self) -> None:
        metrics = self._healthy_metrics()
        metrics["double_apply_count"] = 1.0

        evaluation = evaluate_slos(metrics)
        alerts = generate_alerts(evaluation)

        self.assertEqual(evaluation.overall_status, "CRITICAL")
        self.assertTrue(any(alert.metric_name == "double_apply_count" and alert.severity == "CRITICAL" for alert in alerts))

    def test_budget_consumido_gera_alerta_persistente(self) -> None:
        metrics = self._healthy_metrics()
        metrics["event_query_error_rate"] = 0.02

        evaluation = evaluate_slos(metrics)
        alerts = generate_alerts(evaluation)
        self.assertTrue(any(alert.alert_code == "BUDGET_EVENT_QUERY_ERROR_RATE" for alert in alerts))

        with tempfile.TemporaryDirectory() as tmp_dir:
            alerts_path, status_path = persist_alert_bundle(
                alerts=alerts,
                evaluation=evaluation,
                output_dir=Path(tmp_dir) / "OUT" / "ops",
            )
            self.assertTrue(alerts_path.exists())
            self.assertTrue(status_path.exists())
            payload = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["overall_status"], "WARN")

    def test_metrics_from_load_results_agrega_relatorio_d18(self) -> None:
        report = {
            "scenarios": [
                {
                    "total_ops": 30,
                    "error_count": 0,
                    "success_count": 30,
                    "fallback_hit_rate": 0.1,
                    "lease_contention_rate": 0.0,
                    "idempotency_conflict_rate": 0.0,
                    "latency": {"event_query_latency_ms": {"p95_ms": 140.0}},
                },
                {
                    "total_ops": 70,
                    "error_count": 2,
                    "success_count": 68,
                    "fallback_hit_rate": 0.2,
                    "lease_contention_rate": 0.05,
                    "idempotency_conflict_rate": 0.01,
                    "latency": {"event_query_latency_ms": {"p95_ms": 220.0}},
                },
            ]
        }
        metrics = metrics_from_load_results(report)

        self.assertEqual(metrics["event_query_p95_ms"], 220.0)
        self.assertEqual(metrics["event_query_error_rate"], 0.02)
        self.assertEqual(metrics["event_query_fallback_rate"], 0.17)


if __name__ == "__main__":
    unittest.main()
