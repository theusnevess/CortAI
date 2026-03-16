from __future__ import annotations

from dataclasses import dataclass, field

from app.content.script_gen.service import LocalScriptGeneratorService, ScriptGenerationError
from app.content.screen_text.service import ScreenTextAdapterService
from app.creative.agents.script.models import ScriptAgentResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ScriptPlan


@dataclass
class ScriptAgentService:
    generator: LocalScriptGeneratorService = field(default_factory=LocalScriptGeneratorService)
    screen_text_adapter: ScreenTextAdapterService = field(default_factory=ScreenTextAdapterService)

    def generate(self, *, account_id: str, niche: str, topic: str) -> ScriptAgentResult:
        try:
            script_text = self.generator.generate(
                theme=niche,
                angle=topic,
                hook_hint=f"{topic} should not be happening",
                account_id=account_id,
            )
            blocks = self.screen_text_adapter.adapt(script_text)
            return ScriptAgentResult(
                script_plan=ScriptPlan(
                    hook=blocks.hook_text,
                    setup=blocks.setup_text,
                    payoff=blocks.payoff_text,
                    generation_mode="contextual",
                ),
                fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            )
        except ScriptGenerationError:
            fallback_plan = self._fallback_script(niche=niche, topic=topic)
            return ScriptAgentResult(
                script_plan=fallback_plan,
                fallback=FallbackDecision(
                    used=True,
                    mode=FallbackMode.SAFE_DEFAULT.value,
                    reason="script_generation_fallback_used",
                ),
            )

    def _fallback_script(self, *, niche: str, topic: str) -> ScriptPlan:
        topic_text = (topic or niche or "THIS STORY").strip().upper()
        topic_text = " ".join(topic_text.split())[:72].strip()
        if not topic_text:
            topic_text = "THIS PLACE"
        return ScriptPlan(
            hook=f"{topic_text} SHOULDN'T EXIST",
            setup="NOBODY COULD EXPLAIN IT",
            payoff="THEN IT MOVED ON ITS OWN",
            generation_mode="fallback",
        )
