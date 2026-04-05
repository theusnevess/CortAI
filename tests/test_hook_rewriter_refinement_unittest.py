from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.pipeline.hook_rewriter import HookRewriter


class HookRewriterRefinementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rewriter = HookRewriter()

    def test_provenance_remains_visible_after_rewrite(self) -> None:
        result = self.rewriter.rewrite("A WITNESS SAW AUTOPSY ROOM CAMERA DESYNC")

        self.assertTrue(result.transformed)
        self.assertIn("A WITNESS SAID", result.rewritten)
        self.assertTrue(result.rewritten.startswith("THE AUTOPSY ROOM CAMERA FELL OUT OF SYNC"))

    def test_anti_passive_bias_prefers_dynamic_form_when_safe(self) -> None:
        result = self.rewriter.rewrite("POLICE REOPENED CAMERA BLACKOUT IN SECTOR 4")

        self.assertEqual(result.rewritten, "THE CAMERA WENT DARK IN SECTOR 4, POLICE RECORDS SHOW")
        self.assertNotIn("WAS", result.rewritten)

    def test_records_style_source_is_reattached_after_anomaly(self) -> None:
        result = self.rewriter.rewrite("RECORDS INDICATE NIGHT WATCH LOG WITH FUTURE DATE")

        self.assertEqual(result.rewritten, "THE NIGHT WATCH LOG CARRIED A FUTURE DATE, RECORDS SHOW")


if __name__ == "__main__":
    unittest.main()
