from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.runtime.scheduler.candidate_universe import expand_candidate_universe, summarize_expanded_pool


class CandidateUniverseExpansionUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_flag = os.environ.get("CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION")
        os.environ["CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION"] = "1"

    def tearDown(self) -> None:
        if self.original_flag is None:
            os.environ.pop("CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION", None)
            return
        os.environ["CORTAI_EXPERIMENT_CANDIDATE_UNIVERSE_EXPANSION"] = self.original_flag

    def test_expands_inferential_supply_for_documentary_inconsistency(self) -> None:
        rows = [
            {
                "video_id": "v1",
                "hook_text": "THE BUNKER MAP WAS MISSING A CORRIDOR",
                "hook_type": "experiential",
                "visual_anchor": "document",
            }
        ]

        expanded, note = expand_candidate_universe(rows)

        self.assertEqual(expanded[0]["hook_type"], "inferential")
        self.assertTrue(note["expansion_applied"])

    def test_keeps_clearly_experiential_case_unchanged(self) -> None:
        rows = [
            {
                "video_id": "v1",
                "hook_text": "THE CAMERA WENT DARK IN SECTOR 4",
                "hook_type": "experiential",
                "visual_anchor": "device",
            }
        ]

        expanded, note = expand_candidate_universe(rows)

        self.assertEqual(expanded[0]["hook_type"], "experiential")
        self.assertEqual(note["inferential_expansions"], 0)

    def test_subtypes_document_visual_anchor(self) -> None:
        rows = [
            {
                "video_id": "v1",
                "hook_text": "THE SEALED CALL TRANSCRIPT DID NOT MATCH THE AUDIO",
                "hook_type": "inferential",
                "visual_anchor": "document",
            }
        ]

        expanded, note = expand_candidate_universe(rows)
        summary = summarize_expanded_pool(expanded)

        self.assertEqual(expanded[0]["visual_anchor"], "transcript_sheet")
        self.assertEqual(summary["document_subtype_distribution"], {"transcript_sheet": 1})
        self.assertTrue(note["expansion_applied"])
