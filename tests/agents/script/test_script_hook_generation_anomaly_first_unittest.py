from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.script_gen.models import ScriptGenerationContext
from app.content.script_gen.models import ScriptGenerationRequest
from app.content.script_gen.service import LocalScriptGeneratorService


class ScriptHookGenerationAnomalyFirstTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)
        self.service = LocalScriptGeneratorService()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_flag_off_preserves_baseline_hook(self) -> None:
        os.environ.pop("CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST", None)

        hook = self.service.generate_experimental_hook(
            context=ScriptGenerationContext(account_id="acc_1", niche="true_crime", topic="camera blackout in sector 4"),
            hook="POLICE REOPENED CAMERA BLACKOUT IN SECTOR 4.",
            setup="The logs showed a timestamp nobody filed.",
            payoff="The recorder captured a voice from sealed evidence.",
            narrative_mode="procedural_anomaly",
        )

        self.assertEqual(hook, "POLICE REOPENED CAMERA BLACKOUT IN SECTOR 4.")

    def test_flag_on_generates_anomaly_first_hook(self) -> None:
        os.environ["CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST"] = "1"

        hook = self.service.generate_experimental_hook(
            context=ScriptGenerationContext(account_id="acc_1", niche="true_crime", topic="camera blackout in sector 4"),
            hook="POLICE REOPENED CAMERA BLACKOUT IN SECTOR 4.",
            setup="The logs showed a timestamp nobody filed.",
            payoff="The recorder captured a voice from sealed evidence.",
            narrative_mode="procedural_anomaly",
        )

        self.assertEqual(hook, "THE CAMERA WENT DARK IN SECTOR 4.")

    def test_prompt_includes_anomaly_first_experiment_constraints_when_flag_on(self) -> None:
        os.environ["CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST"] = "1"

        prompt = self.service._build_prompt(  # noqa: SLF001
            request=ScriptGenerationRequest(
                context=ScriptGenerationContext(account_id="acc_1", niche="horror", topic="autopsy room camera desync")
            )
        )

        self.assertIn("Hook experiment active", prompt)
        self.assertIn("The hook must be anomaly-first", prompt)
        self.assertIn("Do not start the hook with mediators", prompt)

    def test_flag_on_rewrites_non_mediator_report_scaffold_when_topic_mapping_is_safe(self) -> None:
        os.environ["CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST"] = "1"

        hook = self.service.generate_experimental_hook(
            context=ScriptGenerationContext(
                account_id="acc_1",
                niche="dark_storytelling",
                topic="abandoned platform timetable",
            ),
            hook="LOCALS STILL TALK ABOUT ABANDONED PLATFORM TIMETABLE.",
            setup="The station board kept adding trains after closure.",
            payoff="The last destination had been removed for years.",
            narrative_mode="urban_legend_fragment",
        )

        self.assertEqual(hook, "THE ABANDONED PLATFORM TIMETABLE KEPT CHANGING.")


if __name__ == "__main__":
    unittest.main()
