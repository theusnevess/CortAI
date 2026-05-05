from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.script.service import ScriptAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan


class _InferentialGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="A RECOVERED TAPE MENTIONED ARCHIVE OVERRIDE ON SERVER 9.",
                setup="The second login appeared before the machine rebooted.",
                payoff="The override was timestamped before the server existed.",
                generation_mode="groq_structured",
            ),
            payload=StructuredScriptPayload(
                hook="A RECOVERED TAPE MENTIONED ARCHIVE OVERRIDE ON SERVER 9.",
                setup="The second login appeared before the machine rebooted.",
                payoff="The override was timestamped before the server existed.",
                narrative_mode="procedural_anomaly",
            ),
            provider_used="groq",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class InferentialHookIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)
        os.environ["CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST"] = "1"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_inferential_flag_off_keeps_current_anomaly_first_baseline(self) -> None:
        os.environ.pop("CORTAI_EXPERIMENT_SCRIPT_HOOK_INFERENTIAL", None)
        service = ScriptAgentService(generator=_InferentialGenerator())

        result = service.generate(
            ScriptAgentInput(account_id="acc_1", niche="investigative", topic="archive override on server 9")
        )

        self.assertEqual(result.script_plan.hook, "SERVER 9 SHOWED AN ARCHIVE OVERRIDE")
        self.assertEqual(result.script_plan.setup, "THE SECOND LOGIN APPEARED BEFORE THE MACHINE REBOOTED")
        self.assertEqual(result.script_plan.payoff, "THE OVERRIDE WAS TIMESTAMPED BEFORE THE SERVER EXISTED")

    def test_inferential_flag_on_uses_inferential_dialect_only_for_hook(self) -> None:
        os.environ["CORTAI_EXPERIMENT_SCRIPT_HOOK_INFERENTIAL"] = "1"
        service = ScriptAgentService(generator=_InferentialGenerator())

        result = service.generate(
            ScriptAgentInput(account_id="acc_1", niche="investigative", topic="archive override on server 9")
        )

        self.assertEqual(result.script_plan.hook, "THE ARCHIVE LOG SHOWED AN UNAUTHORIZED OVERRIDE ON SERVER 9")
        self.assertEqual(result.script_plan.setup, "THE SECOND LOGIN APPEARED BEFORE THE MACHINE REBOOTED")
        self.assertEqual(result.script_plan.payoff, "THE OVERRIDE WAS TIMESTAMPED BEFORE THE SERVER EXISTED")
        self.assertEqual(result.script_plan.generation_mode, "groq_structured")


if __name__ == "__main__":
    unittest.main()
