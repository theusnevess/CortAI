from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.hook_rewriter import HookRewriter, rewrite_hook


class HookRewriterUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rewriter = HookRewriter()

    def test_rewrites_mediator_first_hook_into_anomaly_first_form(self) -> None:
        result = self.rewriter.rewrite("A WITNESS SAW RAIL TUNNEL WARNING")

        self.assertTrue(result.transformed)
        self.assertEqual(result.rule, "witness_observed")
        self.assertTrue(result.provenance_preserved)
        self.assertEqual(result.rewritten, "THE RAIL TUNNEL DISPLAYED A WARNING, A WITNESS SAID")

    def test_police_reopened_hook_preserves_core_event_and_source(self) -> None:
        rewritten = rewrite_hook("POLICE REOPENED DISPATCHER TAPE REOPENED")

        self.assertEqual(rewritten, "POLICE REOPENED DISPATCHER TAPE REOPENED")

    def test_recovered_tape_hook_reattaches_provenance_after_anomaly(self) -> None:
        rewritten = rewrite_hook("A RECOVERED TAPE MENTIONED HOSPITAL WING SEALED AFTER 3 AM")

        self.assertEqual(
            rewritten,
            "AFTER 3 AM THE HOSPITAL WING WAS SEALED, ON TAPE",
        )

    def test_hook_already_anomaly_first_is_left_unchanged(self) -> None:
        result = self.rewriter.rewrite("THE DOOR LOCKED ITSELF FROM THE INSIDE")

        self.assertFalse(result.transformed)
        self.assertEqual(result.rewritten, "THE DOOR LOCKED ITSELF FROM THE INSIDE")

    def test_non_mandated_mediator_pattern_is_not_forced(self) -> None:
        result = self.rewriter.rewrite("CASE NOTES FLAGGED SEALED CALL TRANSCRIPT DISCREPANCY")

        self.assertFalse(result.transformed)
        self.assertEqual(result.rewritten, "CASE NOTES FLAGGED SEALED CALL TRANSCRIPT DISCREPANCY")

    def test_ambiguous_hook_is_left_unchanged_when_rewrite_would_be_risky(self) -> None:
        result = self.rewriter.rewrite("A WITNESS SAW MIDNIGHT CHAPEL LEDGER")

        self.assertFalse(result.transformed)
        self.assertEqual(result.rewritten, "A WITNESS SAW MIDNIGHT CHAPEL LEDGER")


if __name__ == "__main__":
    unittest.main()
