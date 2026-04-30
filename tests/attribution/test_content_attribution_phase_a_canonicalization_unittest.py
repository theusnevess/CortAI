from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.attribution as legacy_attribution
import app.product.attribution as canonical_attribution


class ContentAttributionPhaseACanonicalizationTests(unittest.TestCase):
    def test_product_attribution_is_explicitly_canonical(self) -> None:
        self.assertIn("canonical", (canonical_attribution.__doc__ or "").lower())
        self.assertEqual(canonical_attribution.build_attribution.__module__, "app.product.attribution.builder")
        self.assertEqual(canonical_attribution.save_if_absent.__module__, "app.product.attribution.repo")

    def test_legacy_attribution_is_explicitly_non_canonical(self) -> None:
        self.assertIn("legacy analytical", (legacy_attribution.__doc__ or "").lower())
        self.assertEqual(legacy_attribution.AdvancedAttributionService.__module__, "app.attribution.service")


if __name__ == "__main__":
    unittest.main()
