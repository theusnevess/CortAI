from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.script_gen.models import ScriptGenerationContext
from app.content.script_gen.service import LocalScriptGeneratorService


class InferentialHookPatternTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)
        self.service = LocalScriptGeneratorService()
        os.environ["CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST"] = "1"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_detects_inferential_case_conservatively(self) -> None:
        self.assertTrue(
            self.service._is_inferential_hook_candidate(  # noqa: SLF001
                topic="archive override on server 9",
                hook="A RECOVERED TAPE MENTIONED ARCHIVE OVERRIDE ON SERVER 9.",
                setup="The audit log showed a second root session.",
                payoff="The final entry appeared before the server booted.",
            )
        )

    def test_experiential_case_remains_outside_inferential_detector(self) -> None:
        self.assertFalse(
            self.service._is_inferential_hook_candidate(  # noqa: SLF001
                topic="camera blackout in sector 4",
                hook="POLICE REOPENED CAMERA BLACKOUT IN SECTOR 4.",
                setup="The hallway camera failed before the alarm.",
                payoff="The blackout ended after the voice stopped.",
            )
        )

    def test_inferential_flag_rewrites_to_inconsistency_first(self) -> None:
        os.environ["CORTAI_EXPERIMENT_SCRIPT_HOOK_INFERENTIAL"] = "1"

        hook = self.service.generate_experimental_hook(
            context=ScriptGenerationContext(
                account_id="acc_1",
                niche="investigative",
                topic="archive override on server 9",
            ),
            hook="A RECOVERED TAPE MENTIONED ARCHIVE OVERRIDE ON SERVER 9.",
            setup="The server log contained a second admin trail.",
            payoff="The override entry predated the boot sequence.",
            narrative_mode="procedural_anomaly",
        )

        self.assertEqual(hook, "THE ARCHIVE LOG SHOWED AN UNAUTHORIZED OVERRIDE ON SERVER 9.")
        self.assertFalse(hook.startswith("A RECOVERED TAPE"))

    def test_inferential_flag_does_not_touch_experiential_case(self) -> None:
        os.environ["CORTAI_EXPERIMENT_SCRIPT_HOOK_INFERENTIAL"] = "1"

        hook = self.service.generate_experimental_hook(
            context=ScriptGenerationContext(
                account_id="acc_1",
                niche="true_crime",
                topic="camera blackout in sector 4",
            ),
            hook="POLICE REOPENED CAMERA BLACKOUT IN SECTOR 4.",
            setup="The hallway camera died before the call ended.",
            payoff="The feed returned after the voice stopped.",
            narrative_mode="procedural_anomaly",
        )

        self.assertEqual(hook, "THE CAMERA WENT DARK IN SECTOR 4.")


if __name__ == "__main__":
    unittest.main()
