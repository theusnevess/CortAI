from __future__ import annotations

from dataclasses import dataclass, field
import os

from app.content.script_gen.models import ScriptGenerationContext, ScriptGenerationRequest
from app.content.script_gen.service import LocalScriptGeneratorService, ScriptGenerationError
from app.content.screen_text.service import ScreenTextAdapterService
from app.creative.agents.script.models import ScriptAgentInput, ScriptAgentResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ScriptPlan


@dataclass
class ScriptAgentService:
    generator: LocalScriptGeneratorService = field(default_factory=LocalScriptGeneratorService)
    screen_text_adapter: ScreenTextAdapterService = field(default_factory=ScreenTextAdapterService)

    def generate(self, data: ScriptAgentInput) -> ScriptAgentResult:
        try:
            context = ScriptGenerationContext(
                account_id=data.account_id,
                niche=data.niche,
                topic=data.topic,
                account_health_status=data.account_health_status,
                strategy_profile=data.strategy_profile,
                trend_profile=data.trend_profile,
                learning_insights=data.learning_insights,
                experiment_plan=data.experiment_plan,
            )
            generation = self.generator.generate_structured(
                ScriptGenerationRequest(
                    context=context
                )
            )
            hook = generation.script_plan.hook
            if self._hook_experiment_enabled():
                hook = self._generate_experimental_hook(
                    context=context,
                    hook=generation.script_plan.hook,
                    setup=generation.script_plan.setup,
                    payoff=generation.script_plan.payoff,
                    narrative_mode=generation.payload.narrative_mode,
                )
            blocks = self.screen_text_adapter.adapt_structured_blocks(
                hook=hook,
                setup=generation.script_plan.setup,
                payoff=generation.script_plan.payoff,
            )
            return ScriptAgentResult(
                script_plan=ScriptPlan(
                    hook=blocks.hook_text,
                    setup=blocks.setup_text,
                    payoff=blocks.payoff_text,
                    generation_mode=generation.script_plan.generation_mode,
                ),
                fallback=generation.fallback,
            )
        except ScriptGenerationError:
            fallback_plan = self._fallback_script(data)
            return ScriptAgentResult(
                script_plan=fallback_plan,
                fallback=FallbackDecision(
                    used=True,
                    mode=FallbackMode.SAFE_DEFAULT.value,
                    reason="script_generation_contextual_fallback",
                ),
            )

    def _fallback_script(self, data: ScriptAgentInput) -> ScriptPlan:
        niche = (data.niche or "").strip().lower()
        variant = (
            ""
            if data.experiment_plan is None
            else str(data.experiment_plan.variant_params.get("narrative_mode") or data.experiment_plan.variant_id or "")
        ).strip().lower()

        if niche in {"true_crime", "crime"}:
            hook = "CASE NOTES FLAGGED A LOCKED EVIDENCE ROOM"
            setup = "OFFICERS HEARD A RECORDER START AFTER SEIZURE"
            payoff = "THE VOICE IDENTIFIED SOMEONE DEAD FOR YEARS"
        elif niche in {"history", "ancient_history", "facts"}:
            hook = "THE ARCHIVE KEPT CHANGING ONE MISSING ENTRY"
            setup = "EACH COPY ERASED A DIFFERENT WITNESS NAME"
            payoff = "THE FINAL VERSION DATED THE EVENT NEXT YEAR"
        elif variant == "official_warning":
            hook = "THE WARNING WAS POSTED AFTER THE BUILDING CLOSED"
            setup = "EVERY CAMERA FAILED BEFORE THE SECOND KNOCK"
            payoff = "THE EXIT ROUTE LED STRAIGHT INTO SOLID CONCRETE"
        else:
            hook = "A SEALED PLACE STARTED ANSWERING FROM INSIDE"
            setup = "THE SECOND SOUND CAME FROM BEHIND THE WALL"
            payoff = "BY DAWN THE DOOR HANDLE WAS WARM TO TOUCH"

        if self._hook_experiment_enabled():
            hook = self._generate_experimental_hook(
                context=ScriptGenerationContext(
                    account_id=data.account_id,
                    niche=data.niche,
                    topic=data.topic,
                    account_health_status=data.account_health_status,
                    strategy_profile=data.strategy_profile,
                    trend_profile=data.trend_profile,
                    learning_insights=data.learning_insights,
                    experiment_plan=data.experiment_plan,
                ),
                hook=hook,
                setup=setup,
                payoff=payoff,
                narrative_mode=variant or "fallback_contextual",
            )

        blocks = self.screen_text_adapter.adapt_structured_blocks(hook=hook, setup=setup, payoff=payoff)
        return ScriptPlan(
            hook=blocks.hook_text,
            setup=blocks.setup_text,
            payoff=blocks.payoff_text,
            generation_mode="fallback_contextual",
        )

    def _hook_experiment_enabled(self) -> bool:
        return os.getenv("CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST", "0") == "1"

    def _generate_experimental_hook(
        self,
        *,
        context: ScriptGenerationContext,
        hook: str,
        setup: str,
        payoff: str,
        narrative_mode: str,
    ) -> str:
        generator = self.generator
        if hasattr(generator, "generate_experimental_hook"):
            return generator.generate_experimental_hook(
                context=context,
                hook=hook,
                setup=setup,
                payoff=payoff,
                narrative_mode=narrative_mode,
            )
        return LocalScriptGeneratorService().generate_experimental_hook(
            context=context,
            hook=hook,
            setup=setup,
            payoff=payoff,
            narrative_mode=narrative_mode,
        )
