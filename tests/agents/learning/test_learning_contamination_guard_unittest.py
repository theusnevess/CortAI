from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.learning.contamination_guard import LearningContaminationGuard


def _item(status: str = "APPROVE", score: float = 0.86, *, fallback: bool = False, metadata: bool = True) -> dict:
    return {
        "status": status,
        "overall_score": score,
        "fallback_used": fallback,
        "metadata": {"source": "qc"} if metadata else {},
    }


class LearningContaminationGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = LearningContaminationGuard()

    def test_fully_clean_dataset_is_policy_safe(self) -> None:
        summary = self.guard.summarize_dataset([_item(score=0.86) for _ in range(6)])

        self.assertEqual(summary.clean_sample_size, 6)
        self.assertEqual(summary.contamination_rate, 0.0)
        self.assertTrue(summary.policy_safe)
        self.assertEqual(summary.dominant_problem, "none")

    def test_fallback_contaminated_dataset_is_not_policy_safe(self) -> None:
        summary = self.guard.summarize_dataset([_item(fallback=True) for _ in range(6)])

        self.assertEqual(summary.contamination_rate, 1.0)
        self.assertFalse(summary.policy_safe)
        self.assertEqual(summary.dominant_problem, "contamination")

    def test_partially_contaminated_dataset_preserves_clean_evidence(self) -> None:
        rows = [_item(score=0.86) for _ in range(5)] + [_item(fallback=True) for _ in range(2)]
        summary = self.guard.summarize_dataset(rows)

        self.assertEqual(summary.clean_sample_size, 5)
        self.assertLess(summary.contamination_rate, 0.4)
        self.assertTrue(summary.policy_safe)

    def test_weak_signal_dataset_is_visible(self) -> None:
        summary = self.guard.summarize_dataset([_item(score=0.62) for _ in range(6)])

        self.assertEqual(summary.weak_signal_rate, 1.0)
        self.assertFalse(summary.policy_safe)
        self.assertEqual(summary.dominant_problem, "weak_signal")

    def test_insufficient_dataset_is_not_policy_safe(self) -> None:
        summary = self.guard.summarize_dataset([{"metadata": {}} for _ in range(3)])

        self.assertEqual(summary.insufficient_rate, 1.0)
        self.assertFalse(summary.policy_safe)
        self.assertEqual(summary.dominant_problem, "insufficient")

    def test_noisy_contradictory_dataset_is_detected(self) -> None:
        rows = [
            _item("APPROVE", 0.72),
            _item("APPROVE", 0.71),
            _item("APPROVE", 0.7),
            _item("HOLD", 0.68),
            _item("REJECT", 0.69),
            _item("HOLD", 0.67),
        ]
        summary = self.guard.summarize_dataset(rows)

        self.assertGreater(summary.noise_rate, 0.35)
        self.assertFalse(summary.policy_safe)
        self.assertEqual(summary.dominant_problem, "noise")

    def test_output_is_deterministic(self) -> None:
        rows = [_item(score=0.86) for _ in range(5)] + [_item(fallback=True)]

        self.assertEqual(
            self.guard.summarize_dataset(rows).to_dict(),
            self.guard.summarize_dataset(rows).to_dict(),
        )


if __name__ == "__main__":
    unittest.main()
