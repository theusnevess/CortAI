from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.content.script_gen.models import ScriptGenerationResponse, StructuredScriptPayload
from app.creative.agents.script.models import ScriptAgentInput
from app.creative.agents.script.service import ScriptAgentService
from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan


class _MediatorGenerator:
    def generate_structured(self, request):  # noqa: ANN001
        _ = request
        return ScriptGenerationResponse(
            script_plan=ScriptPlan(
                hook="Police reopened camera blackout in sector 4.",
                setup="The logs showed a timestamp nobody filed.",
                payoff="The recorder captured a voice from sealed evidence.",
                generation_mode="groq_structured",
            ),
            payload=StructuredScriptPayload(
                hook="Police reopened camera blackout in sector 4.",
                setup="The logs showed a timestamp nobody filed.",
                payoff="The recorder captured a voice from sealed evidence.",
                narrative_mode="procedural_anomaly",
            ),
            provider_used="groq",
            model_used="test",
            prompt_used="prompt",
            raw_output="{}",
            fallback=FallbackDecision(used=False, mode="NONE", reason=""),
        )


class ScriptHookGenerationIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_flag_off_keeps_baseline_hook_and_structure(self) -> None:
        os.environ.pop("CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST", None)
        service = ScriptAgentService(generator=_MediatorGenerator())

        result = service.generate(ScriptAgentInput(account_id="acc_1", niche="true_crime", topic="camera blackout in sector 4"))

        self.assertEqual(result.script_plan.hook, "POLICE REOPENED CAMERA BLACKOUT IN SECTOR 4")
        self.assertEqual(result.script_plan.setup, "THE LOGS SHOWED A TIMESTAMP NOBODY FILED")
        self.assertEqual(result.script_plan.payoff, "THE RECORDER CAPTURED A VOICE FROM SEALED EVIDENCE")

    def test_flag_on_changes_only_hook_generation_path(self) -> None:
        os.environ["CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST"] = "1"
        service = ScriptAgentService(generator=_MediatorGenerator())

        result = service.generate(ScriptAgentInput(account_id="acc_1", niche="true_crime", topic="camera blackout in sector 4"))

        self.assertEqual(result.script_plan.hook, "THE CAMERA WENT DARK IN SECTOR 4")
        self.assertEqual(result.script_plan.setup, "THE LOGS SHOWED A TIMESTAMP NOBODY FILED")
        self.assertEqual(result.script_plan.payoff, "THE RECORDER CAPTURED A VOICE FROM SEALED EVIDENCE")
        self.assertEqual(result.script_plan.generation_mode, "groq_structured")


if __name__ == "__main__":
    unittest.main()
