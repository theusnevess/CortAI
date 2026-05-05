from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.learning.temporal_weighting import EvidenceItem, TemporalWeightingEngine


class TemporalWeightingEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = TemporalWeightingEngine()

    def test_classifies_evidence_windows(self) -> None:
        self.assertEqual(self.engine.classify_evidence_window(0), "recent")
        self.assertEqual(self.engine.classify_evidence_window(7), "recent")
        self.assertEqual(self.engine.classify_evidence_window(8), "mid_term")
        self.assertEqual(self.engine.classify_evidence_window(30), "mid_term")
        self.assertEqual(self.engine.classify_evidence_window(31), "long_term")

    def test_recent_spike_when_recent_cluster_has_no_history(self) -> None:
        result = self.engine.apply_weighting(
            [
                EvidenceItem(raw_value=0.91, age_days=0),
                EvidenceItem(raw_value=0.88, age_days=2),
                EvidenceItem(raw_value=0.9, age_days=4),
            ]
        )

        self.assertEqual(result.pattern_type, "recent_spike")
        self.assertEqual(result.dominant_window, "recent")
        self.assertGreater(result.recent_weight, 0.9)

    def test_durable_pattern_when_signal_is_consistent_across_windows(self) -> None:
        result = self.engine.apply_weighting(
            [
                EvidenceItem(raw_value=0.9, age_days=1),
                EvidenceItem(raw_value=0.86, age_days=12),
                EvidenceItem(raw_value=0.84, age_days=36),
                EvidenceItem(raw_value=0.82, age_days=44),
            ]
        )

        self.assertEqual(result.pattern_type, "durable_pattern")
        self.assertFalse(result.volatility_detected)
        self.assertGreater(result.weighted_consistency, 0.7)

    def test_volatile_when_recent_contradicts_history(self) -> None:
        result = self.engine.apply_weighting(
            [
                EvidenceItem(raw_value=0.9, age_days=1),
                EvidenceItem(raw_value=0.42, age_days=13),
                EvidenceItem(raw_value=0.38, age_days=40),
            ]
        )

        self.assertEqual(result.pattern_type, "volatile")
        self.assertTrue(result.volatility_detected)

    def test_stale_signal_when_only_old_data_exists(self) -> None:
        result = self.engine.apply_weighting(
            [
                EvidenceItem(raw_value=0.82, age_days=45),
                EvidenceItem(raw_value=0.8, age_days=55),
                EvidenceItem(raw_value=0.78, age_days=70),
            ]
        )

        self.assertEqual(result.pattern_type, "stale_signal")
        self.assertTrue(result.staleness_detected)
        self.assertEqual(result.dominant_window, "long_term")

    def test_recency_weighting_affects_aggregated_metrics(self) -> None:
        recent = self.engine.compute_recency_weight(3)
        long_term = self.engine.compute_recency_weight(50)
        result = self.engine.apply_weighting(
            [
                EvidenceItem(raw_value=0.9, age_days=3),
                EvidenceItem(raw_value=0.9, age_days=50),
            ]
        )

        self.assertGreater(recent, long_term)
        self.assertLess(result.weighted_sample_size, 2.0)
        self.assertGreater(result.recent_weight, result.long_term_weight)

    def test_output_is_deterministic(self) -> None:
        rows = [
            EvidenceItem(raw_value=0.9, age_days=1),
            EvidenceItem(raw_value=0.85, age_days=12),
            EvidenceItem(raw_value=0.82, age_days=40),
        ]

        self.assertEqual(self.engine.apply_weighting(rows).to_dict(), self.engine.apply_weighting(rows).to_dict())


if __name__ == "__main__":
    unittest.main()
