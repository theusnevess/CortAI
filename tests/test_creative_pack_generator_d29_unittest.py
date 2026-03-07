from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.creative_pack.service import CreativePackGeneratorService


class CreativePackGeneratorD29Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "OUT" / "content" / "creative_packs" / "creative_packs.jsonl"
        self.service = CreativePackGeneratorService(output_path=self.path)

    def _rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as reader:
            return [json.loads(line) for line in reader if line.strip()]

    def test_happy_path_generate_creative_packs(self) -> None:
        result = self.service.generate(
            theme="crime real",
            account_id="acc_001",
            policy_stage="GROWTH",
            variation_count=3,
            generated_at="2026-03-07T12:00:00Z",
        )
        self.assertEqual(result.status, "WRITTEN")
        self.assertEqual(len(result.creative_packs), 3)
        self.assertEqual(len(self._rows()), 3)
        self.assertTrue(all(pack.title for pack in result.creative_packs))

    def test_same_request_is_noop(self) -> None:
        first = self.service.generate(
            theme="crime real",
            account_id="acc_001",
            policy_stage="GROWTH",
            variation_count=2,
            generated_at="2026-03-07T12:00:00Z",
        )
        second = self.service.generate(
            theme="crime real",
            account_id="acc_001",
            policy_stage="GROWTH",
            variation_count=2,
            generated_at="2026-03-07T12:00:00Z",
        )
        self.assertEqual(first.status, "WRITTEN")
        self.assertEqual(second.status, "NOOP")
        self.assertEqual(len(self._rows()), 2)

    def test_variations_are_distinct_and_stable(self) -> None:
        result = self.service.generate(
            theme="misterio urbano",
            account_id="acc_002",
            policy_stage="GROWTH",
            variation_count=3,
            generated_at="2026-03-07T12:00:00Z",
        )
        ids = [pack.creative_pack_id for pack in result.creative_packs]
        self.assertEqual(len(ids), len(set(ids)))
        rerun = self.service.generate(
            theme="misterio urbano",
            account_id="acc_002",
            policy_stage="GROWTH",
            variation_count=3,
            generated_at="2026-03-07T12:00:00Z",
        )
        self.assertEqual([pack.creative_pack_id for pack in rerun.creative_packs], ids)

    def test_strategy_and_policy_influence_output(self) -> None:
        result = self.service.generate(
            theme="investigacao fria",
            account_id="acc_003",
            policy_stage="GROWTH",
            account_policy={
                "stage": "GROWTH",
                "config": {
                    "a1_prefs_override": {"prefer_angles": ["evidence_gap"], "niches_boost": ["truecrime", "coldcase"]},
                },
            },
            strategy_patch={
                "patch_id": "sp_001",
                "active": True,
                "overrides": {
                    "a4_defaults_override": {
                        "force_number": True,
                        "increase_tension": True,
                        "hook_style": "listicle",
                    },
                    "a5_rewrite_defaults_override": {"cta_style": "follow_prompt"},
                },
            },
            variation_count=1,
            generated_at="2026-03-07T12:00:00Z",
        )
        pack = result.creative_packs[0]
        self.assertTrue(pack.title.startswith("1. "))
        self.assertEqual(pack.angle, "evidence_gap")
        self.assertIn("#truecrime", pack.hashtags)
        self.assertIn("#coldcase", pack.hashtags)
        self.assertIn("segue", pack.cta)
        self.assertTrue(any(hook.startswith("3 sinais") or hook.startswith("2 pistas") for hook in pack.hook_candidates))

    def test_inactive_patch_does_not_override_policy(self) -> None:
        result = self.service.generate(
            theme="arquivo proibido",
            account_id="acc_004",
            policy_stage="GROWTH",
            account_policy={"stage": "GROWTH", "config": {"a4_defaults_override": {"hook_style": "story_arc"}}},
            strategy_patch={
                "patch_id": "sp_002",
                "active": False,
                "overrides": {"a4_defaults_override": {"hook_style": "listicle", "force_number": True}},
            },
            variation_count=1,
            generated_at="2026-03-07T12:00:00Z",
        )
        pack = result.creative_packs[0]
        self.assertFalse(pack.title.startswith("1. "))
        self.assertTrue(any("parecia so mais um caso" in hook for hook in pack.hook_candidates))

    def test_invalid_policy_stage_fails_explicitly(self) -> None:
        with self.assertRaisesRegex(ValueError, "CREATIVE_PACK_POLICY_STAGE_INVALID"):
            self.service.generate(
                theme="arquivo proibido",
                account_id="acc_004",
                policy_stage="INVALID",
            )


if __name__ == "__main__":
    unittest.main()
