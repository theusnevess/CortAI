from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.learning.confidence_calibrator import LearningConfidenceCalibrator


class LearningConfidenceCalibratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calibrator = LearningConfidenceCalibrator()

    def test_small_sample_stays_low_confidence(self) -> None:
        result = self.calibrator.calibrate_policy_confidence(
            sample_size=3,
            clean_sample_size=3,
            contamination_rate=0.0,
            recency_weight=0.7,
            signal_consistency=0.9,
            signal_strength=0.8,
            evidence_source_mix={"runtime_history": 3},
            evidence_variety=2,
            cluster_distribution={"APPROVE": 3},
        )

        self.assertLess(result.confidence, 0.35)
        self.assertEqual(result.policy_strength, "weak")
        self.assertEqual(result.bootstrap_bias_risk, "high")

    def test_high_contamination_stays_low_confidence(self) -> None:
        result = self.calibrator.calibrate_policy_confidence(
            sample_size=12,
            clean_sample_size=5,
            contamination_rate=0.58,
            recency_weight=0.8,
            signal_consistency=0.8,
            signal_strength=0.7,
            evidence_source_mix={"runtime_history": 12},
            evidence_variety=4,
            cluster_distribution={"APPROVE": 8, "HOLD": 4},
        )

        self.assertLess(result.confidence, 0.35)
        self.assertEqual(result.policy_strength, "weak")
        self.assertEqual(result.confidence_rationale["contamination_rate"], 0.58)

    def test_strong_clean_runtime_cluster_can_reach_higher_confidence(self) -> None:
        result = self.calibrator.calibrate_policy_confidence(
            sample_size=24,
            clean_sample_size=24,
            contamination_rate=0.0,
            recency_weight=0.9,
            signal_consistency=0.82,
            signal_strength=0.78,
            evidence_source_mix={"qc_derived": 12, "runtime_history": 10, "post_publish_metrics": 2},
            evidence_variety=5,
            cluster_distribution={"APPROVE": 18, "HOLD": 4, "REJECT": 2},
        )

        self.assertGreaterEqual(result.confidence, 0.7)
        self.assertEqual(result.policy_strength, "strong")
        self.assertEqual(result.bootstrap_bias_risk, "low")

    def test_mixed_contradictory_signal_reduces_confidence(self) -> None:
        result = self.calibrator.calibrate_policy_confidence(
            sample_size=18,
            clean_sample_size=18,
            contamination_rate=0.0,
            recency_weight=0.8,
            signal_consistency=0.38,
            signal_strength=0.2,
            evidence_source_mix={"runtime_history": 18},
            evidence_variety=4,
            cluster_distribution={"APPROVE": 6, "HOLD": 6, "REJECT": 6},
        )

        self.assertLessEqual(result.confidence, 0.35)
        self.assertEqual(result.policy_strength, "weak")

    def test_controlled_validation_dominance_is_penalized(self) -> None:
        result = self.calibrator.calibrate_policy_confidence(
            sample_size=20,
            clean_sample_size=20,
            contamination_rate=0.0,
            recency_weight=0.8,
            signal_consistency=0.82,
            signal_strength=0.74,
            evidence_source_mix={"controlled_validation": 16, "runtime_history": 4},
            evidence_variety=5,
            cluster_distribution={"APPROVE": 14, "HOLD": 4, "REJECT": 2},
        )

        self.assertTrue(result.controlled_validation_dominance)
        self.assertLess(result.confidence, 0.7)
        self.assertIn("controlled_validation_penalty", result.confidence_components)

    def test_same_input_produces_same_confidence(self) -> None:
        kwargs = {
            "sample_size": 14,
            "clean_sample_size": 12,
            "contamination_rate": 0.14,
            "recency_weight": 0.75,
            "signal_consistency": 0.72,
            "signal_strength": 0.62,
            "evidence_source_mix": {"qc_derived": 8, "runtime_history": 6},
            "evidence_variety": 4,
            "cluster_distribution": {"APPROVE": 9, "HOLD": 3, "REJECT": 2},
        }

        self.assertEqual(
            self.calibrator.calibrate_policy_confidence(**kwargs).to_dict(),
            self.calibrator.calibrate_policy_confidence(**kwargs).to_dict(),
        )

    def test_temporal_pattern_modifies_confidence_conservatively(self) -> None:
        base_kwargs = {
            "sample_size": 20,
            "clean_sample_size": 20,
            "contamination_rate": 0.0,
            "recency_weight": 0.8,
            "signal_consistency": 0.8,
            "signal_strength": 0.72,
            "evidence_source_mix": {"qc_derived": 10, "runtime_history": 10},
            "evidence_variety": 4,
            "cluster_distribution": {"APPROVE": 14, "HOLD": 4, "REJECT": 2},
        }

        durable = self.calibrator.calibrate_policy_confidence(
            **base_kwargs,
            temporal_pattern_type="durable_pattern",
        )
        volatile = self.calibrator.calibrate_policy_confidence(
            **base_kwargs,
            temporal_pattern_type="volatile",
        )
        stale = self.calibrator.calibrate_policy_confidence(
            **base_kwargs,
            temporal_pattern_type="stale_signal",
        )
        spike = self.calibrator.calibrate_policy_confidence(
            **base_kwargs,
            temporal_pattern_type="recent_spike",
        )

        self.assertGreater(durable.confidence, volatile.confidence)
        self.assertLessEqual(volatile.confidence, 0.5)
        self.assertLessEqual(stale.confidence, 0.48)
        self.assertLessEqual(spike.confidence, 0.6)
        self.assertEqual(durable.confidence_rationale["temporal_pattern_type"], "durable_pattern")

    def test_contamination_and_noise_reduce_confidence(self) -> None:
        base_kwargs = {
            "sample_size": 20,
            "clean_sample_size": 20,
            "contamination_rate": 0.0,
            "recency_weight": 0.8,
            "signal_consistency": 0.82,
            "signal_strength": 0.74,
            "evidence_source_mix": {"qc_derived": 10, "runtime_history": 10},
            "evidence_variety": 4,
            "cluster_distribution": {"APPROVE": 14, "HOLD": 4, "REJECT": 2},
            "temporal_pattern_type": "durable_pattern",
        }
        clean = self.calibrator.calibrate_policy_confidence(
            **base_kwargs,
            contamination_summary={
                "policy_safe": True,
                "dominant_problem": "none",
                "confidence_penalty": 0.0,
            },
        )
        noisy = self.calibrator.calibrate_policy_confidence(
            **base_kwargs,
            contamination_summary={
                "policy_safe": False,
                "dominant_problem": "noise",
                "noise_rate": 0.6,
                "confidence_penalty": 0.32,
            },
        )

        self.assertGreater(clean.confidence, noisy.confidence)
        self.assertEqual(noisy.policy_strength, "weak")
        self.assertEqual(noisy.confidence_rationale["dominant_problem"], "noise")


if __name__ == "__main__":
    unittest.main()
