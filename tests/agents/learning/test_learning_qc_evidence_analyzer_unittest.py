from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.learning.qc_evidence_analyzer import QCEvidenceAnalyzer


def _qc_row(
    *,
    status: str,
    overall: float,
    hook: float,
    payoff: float,
    product: float,
    hook_type: str = "story_opening",
    payoff_specificity: str = "specific",
    fallback_used: bool = False,
) -> dict:
    return {
        "status": status,
        "publishable": status == "APPROVE",
        "overall_score": overall,
        "hook_score": hook,
        "payoff_score": payoff,
        "product_score": product,
        "technical_valid": True,
        "script_metadata": {
            "hook_type": hook_type,
            "payoff_specificity": payoff_specificity,
            "fallback_used": fallback_used,
        },
        "asset_metadata": {"visual_family": "map_blueprint", "fallback_used": False},
        "voice_metadata": {"voice_style": "ominous_minimal", "fallback_used": False},
        "fallback_used": fallback_used,
        "timestamp": "2026-04-05T00:00:00Z",
    }


class QCEvidenceAnalyzerTests(unittest.TestCase):
    def test_high_approve_cluster_produces_bounded_patterns(self) -> None:
        rows = [
            _qc_row(status="APPROVE", overall=0.9, hook=0.9, payoff=0.88, product=0.91, hook_type="story_opening"),
            _qc_row(status="APPROVE", overall=0.88, hook=0.91, payoff=0.86, product=0.9, hook_type="story_opening"),
            _qc_row(status="APPROVE", overall=0.89, hook=0.89, payoff=0.85, product=0.88, hook_type="story_opening"),
            _qc_row(status="APPROVE", overall=0.87, hook=0.88, payoff=0.84, product=0.87, hook_type="story_opening"),
            _qc_row(status="HOLD", overall=0.55, hook=0.52, payoff=0.45, product=0.5, hook_type="question"),
            _qc_row(status="HOLD", overall=0.54, hook=0.5, payoff=0.44, product=0.49, hook_type="question"),
        ]

        analysis = QCEvidenceAnalyzer().analyze(rows)

        self.assertEqual(analysis.sample_size, 6)
        self.assertEqual(analysis.clean_sample_size, 6)
        self.assertEqual(analysis.contamination_rate, 0.0)
        self.assertGreater(analysis.approve_rate, analysis.hold_rate)
        self.assertTrue(any(pattern.type == "hook_type" for pattern in analysis.patterns))
        self.assertTrue(all(0.0 <= pattern.confidence <= 1.0 for pattern in analysis.patterns))

    def test_mixed_approve_reject_does_not_inflate_confidence(self) -> None:
        rows = [
            _qc_row(status="APPROVE", overall=0.82, hook=0.8, payoff=0.8, product=0.82, hook_type="story_opening"),
            _qc_row(status="REJECT", overall=0.32, hook=0.4, payoff=0.3, product=0.28, hook_type="story_opening"),
            _qc_row(status="APPROVE", overall=0.81, hook=0.78, payoff=0.79, product=0.8, hook_type="question"),
            _qc_row(status="REJECT", overall=0.31, hook=0.36, payoff=0.28, product=0.27, hook_type="question"),
            _qc_row(status="HOLD", overall=0.52, hook=0.51, payoff=0.47, product=0.48, hook_type="shock_statement"),
            _qc_row(status="APPROVE", overall=0.79, hook=0.75, payoff=0.76, product=0.78, hook_type="shock_statement"),
        ]

        analysis = QCEvidenceAnalyzer().analyze(rows)

        self.assertLessEqual(analysis.confidence_summary["adjusted_confidence"], 0.2)
        self.assertEqual([pattern for pattern in analysis.patterns if pattern.type == "hook_type"], [])

    def test_mostly_reject_cluster_detects_quality_driver(self) -> None:
        rows = [
            _qc_row(status="REJECT", overall=0.3, hook=0.42, payoff=0.31, product=0.25, hook_type="question"),
            _qc_row(status="REJECT", overall=0.35, hook=0.45, payoff=0.33, product=0.28, hook_type="question"),
            _qc_row(status="HOLD", overall=0.5, hook=0.5, payoff=0.44, product=0.43, hook_type="question"),
            _qc_row(status="HOLD", overall=0.52, hook=0.52, payoff=0.46, product=0.48, hook_type="question"),
            _qc_row(status="APPROVE", overall=0.84, hook=0.84, payoff=0.8, product=0.82, hook_type="story_opening"),
            _qc_row(status="APPROVE", overall=0.86, hook=0.85, payoff=0.82, product=0.83, hook_type="story_opening"),
        ]

        analysis = QCEvidenceAnalyzer().analyze(rows)

        self.assertTrue(any(pattern.type == "quality_driver" for pattern in analysis.patterns))
        self.assertGreater(analysis.reject_rate + analysis.hold_rate, 0.5)

    def test_small_sample_does_not_emit_noise_patterns(self) -> None:
        rows = [
            _qc_row(status="APPROVE", overall=0.9, hook=0.9, payoff=0.9, product=0.9),
            _qc_row(status="APPROVE", overall=0.88, hook=0.89, payoff=0.88, product=0.88),
            _qc_row(status="APPROVE", overall=0.87, hook=0.88, payoff=0.87, product=0.87),
        ]

        analysis = QCEvidenceAnalyzer().analyze(rows)

        self.assertEqual(analysis.patterns, [])
        self.assertLess(analysis.confidence_summary["adjusted_confidence"], 0.1)

    def test_contaminated_data_is_visible_and_downgrades_confidence(self) -> None:
        rows = [
            _qc_row(status="APPROVE", overall=0.9, hook=0.9, payoff=0.9, product=0.9, fallback_used=True),
            _qc_row(status="APPROVE", overall=0.91, hook=0.91, payoff=0.9, product=0.91, fallback_used=True),
            _qc_row(status="APPROVE", overall=0.92, hook=0.92, payoff=0.91, product=0.92, fallback_used=True),
            _qc_row(status="APPROVE", overall=0.89, hook=0.89, payoff=0.88, product=0.89, fallback_used=True),
            _qc_row(status="APPROVE", overall=0.88, hook=0.88, payoff=0.87, product=0.88, fallback_used=True),
        ]

        analysis = QCEvidenceAnalyzer().analyze(rows)

        self.assertEqual(analysis.clean_sample_size, 0)
        self.assertEqual(analysis.contamination_rate, 1.0)
        self.assertEqual(analysis.patterns, [])
        self.assertEqual(analysis.confidence_summary["adjusted_confidence"], 0.0)
        self.assertEqual(len(analysis.contaminated_evidence), 5)

    def test_output_is_deterministic_for_same_input(self) -> None:
        rows = [
            _qc_row(status="APPROVE", overall=0.9, hook=0.9, payoff=0.9, product=0.9),
            _qc_row(status="HOLD", overall=0.52, hook=0.51, payoff=0.45, product=0.48),
            _qc_row(status="REJECT", overall=0.31, hook=0.35, payoff=0.3, product=0.25),
            _qc_row(status="APPROVE", overall=0.88, hook=0.89, payoff=0.88, product=0.88),
            _qc_row(status="APPROVE", overall=0.87, hook=0.88, payoff=0.86, product=0.87),
        ]
        analyzer = QCEvidenceAnalyzer()

        self.assertEqual(analyzer.analyze(rows).to_dict(), analyzer.analyze(rows).to_dict())


if __name__ == "__main__":
    unittest.main()
