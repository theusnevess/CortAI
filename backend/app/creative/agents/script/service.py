from __future__ import annotations

from dataclasses import dataclass, field
import os

from app.content.script_gen.models import ScriptGenerationContext, ScriptGenerationRequest
from app.content.script_gen.service import LocalScriptGeneratorService, ScriptGenerationError
from app.content.screen_text.service import ScreenTextAdapterService
from app.creative.agents.script.confidence_calibration import ScriptConfidenceCalibrator
from app.creative.agents.script.context_governance import ScriptContextGovernanceEvaluator
from app.creative.agents.script.diversity_analysis import ScriptDiversityAnalyzer
from app.creative.agents.script.hook_analysis import ScriptHookStrengthAnalyzer
from app.creative.agents.script.models import ScriptAgentInput, ScriptAgentResult
from app.creative.agents.script.payoff_analysis import ScriptPayoffMemorabilityAnalyzer
from app.creative.agents.script.provider_fallback_trace import ScriptProviderFallbackTracer
from app.creative.agents.script.quality_rubric import ScriptQualityRubricEvaluator
from app.creative.agents.script.setup_analysis import ScriptSetupProgressionAnalyzer
from app.creative.agents.script.trace_auditability import ScriptTraceBuilder
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ScriptPlan


@dataclass
class ScriptAgentService:
    generator: LocalScriptGeneratorService = field(default_factory=LocalScriptGeneratorService)
    screen_text_adapter: ScreenTextAdapterService = field(default_factory=ScreenTextAdapterService)
    context_governance_evaluator: ScriptContextGovernanceEvaluator = field(default_factory=ScriptContextGovernanceEvaluator)
    quality_rubric_evaluator: ScriptQualityRubricEvaluator = field(default_factory=ScriptQualityRubricEvaluator)
    hook_strength_analyzer: ScriptHookStrengthAnalyzer = field(default_factory=ScriptHookStrengthAnalyzer)
    setup_progression_analyzer: ScriptSetupProgressionAnalyzer = field(default_factory=ScriptSetupProgressionAnalyzer)
    payoff_memorability_analyzer: ScriptPayoffMemorabilityAnalyzer = field(default_factory=ScriptPayoffMemorabilityAnalyzer)
    diversity_analyzer: ScriptDiversityAnalyzer = field(default_factory=ScriptDiversityAnalyzer)
    provider_fallback_tracer: ScriptProviderFallbackTracer = field(default_factory=ScriptProviderFallbackTracer)
    confidence_calibrator: ScriptConfidenceCalibrator = field(default_factory=ScriptConfidenceCalibrator)
    trace_builder: ScriptTraceBuilder = field(default_factory=ScriptTraceBuilder)

    def generate(self, data: ScriptAgentInput) -> ScriptAgentResult:
        context_governance = self.context_governance_evaluator.evaluate(data).to_dict()
        decision_trace = {"context_governance": context_governance}
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
            script_plan = ScriptPlan(
                hook=blocks.hook_text,
                setup=blocks.setup_text,
                payoff=blocks.payoff_text,
                generation_mode=generation.script_plan.generation_mode,
            )
            quality_rubric = self.quality_rubric_evaluator.evaluate(
                script_plan=script_plan,
                data=data,
                context_governance=context_governance,
            ).to_dict()
            hook_analysis = self.hook_strength_analyzer.analyze(
                script_plan=script_plan,
                data=data,
            ).to_dict()
            setup_analysis = self.setup_progression_analyzer.analyze(
                script_plan=script_plan,
                data=data,
            ).to_dict()
            payoff_analysis = self.payoff_memorability_analyzer.analyze(
                script_plan=script_plan,
                data=data,
            ).to_dict()
            diversity_analysis = self.diversity_analyzer.analyze(
                script_plan=script_plan,
                data=data,
            ).to_dict()
            provider_fallback_trace = self.provider_fallback_tracer.from_generation(
                generation=generation,
                script_plan=script_plan,
            ).to_dict()
            confidence_calibration = self.confidence_calibrator.calibrate(
                context_governance=context_governance,
                quality_rubric=quality_rubric,
                hook_analysis=hook_analysis,
                setup_analysis=setup_analysis,
                payoff_analysis=payoff_analysis,
                diversity_analysis=diversity_analysis,
                provider_fallback_trace=provider_fallback_trace,
            ).to_dict()
            decision_trace["quality_rubric"] = quality_rubric
            decision_trace["hook_analysis"] = hook_analysis
            decision_trace["setup_analysis"] = setup_analysis
            decision_trace["payoff_analysis"] = payoff_analysis
            decision_trace["diversity_analysis"] = diversity_analysis
            decision_trace["provider_fallback_trace"] = provider_fallback_trace
            decision_trace["confidence_calibration"] = confidence_calibration
            script_trace = self.trace_builder.build(
                script_plan=script_plan,
                fallback=generation.fallback,
                context_governance=context_governance,
                quality_rubric=quality_rubric,
                hook_analysis=hook_analysis,
                setup_analysis=setup_analysis,
                payoff_analysis=payoff_analysis,
                diversity_analysis=diversity_analysis,
                provider_fallback_trace=provider_fallback_trace,
                confidence_calibration=confidence_calibration,
            ).to_dict()
            decision_trace["script_trace"] = script_trace
            return ScriptAgentResult(
                script_plan=script_plan,
                fallback=generation.fallback,
                context_governance=context_governance,
                quality_rubric=quality_rubric,
                hook_analysis=hook_analysis,
                setup_analysis=setup_analysis,
                payoff_analysis=payoff_analysis,
                diversity_analysis=diversity_analysis,
                provider_fallback_trace=provider_fallback_trace,
                confidence=confidence_calibration["confidence"],
                confidence_level=confidence_calibration["confidence_level"],
                confidence_components=confidence_calibration["confidence_components"],
                confidence_rationale=confidence_calibration["confidence_rationale"],
                script_trace=script_trace,
                decision_trace=decision_trace,
            )
        except ScriptGenerationError as exc:
            fallback_plan = self._fallback_script(data)
            fallback_decision = FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="script_generation_contextual_fallback",
            )
            quality_rubric = self.quality_rubric_evaluator.evaluate(
                script_plan=fallback_plan,
                data=data,
                context_governance=context_governance,
            ).to_dict()
            hook_analysis = self.hook_strength_analyzer.analyze(
                script_plan=fallback_plan,
                data=data,
            ).to_dict()
            setup_analysis = self.setup_progression_analyzer.analyze(
                script_plan=fallback_plan,
                data=data,
            ).to_dict()
            payoff_analysis = self.payoff_memorability_analyzer.analyze(
                script_plan=fallback_plan,
                data=data,
            ).to_dict()
            diversity_analysis = self.diversity_analyzer.analyze(
                script_plan=fallback_plan,
                data=data,
            ).to_dict()
            provider_fallback_trace = self.provider_fallback_tracer.from_exception(
                exc=exc,
                fallback=fallback_decision,
                script_plan=fallback_plan,
            ).to_dict()
            confidence_calibration = self.confidence_calibrator.calibrate(
                context_governance=context_governance,
                quality_rubric=quality_rubric,
                hook_analysis=hook_analysis,
                setup_analysis=setup_analysis,
                payoff_analysis=payoff_analysis,
                diversity_analysis=diversity_analysis,
                provider_fallback_trace=provider_fallback_trace,
            ).to_dict()
            decision_trace["quality_rubric"] = quality_rubric
            decision_trace["hook_analysis"] = hook_analysis
            decision_trace["setup_analysis"] = setup_analysis
            decision_trace["payoff_analysis"] = payoff_analysis
            decision_trace["diversity_analysis"] = diversity_analysis
            decision_trace["provider_fallback_trace"] = provider_fallback_trace
            decision_trace["confidence_calibration"] = confidence_calibration
            script_trace = self.trace_builder.build(
                script_plan=fallback_plan,
                fallback=fallback_decision,
                context_governance=context_governance,
                quality_rubric=quality_rubric,
                hook_analysis=hook_analysis,
                setup_analysis=setup_analysis,
                payoff_analysis=payoff_analysis,
                diversity_analysis=diversity_analysis,
                provider_fallback_trace=provider_fallback_trace,
                confidence_calibration=confidence_calibration,
            ).to_dict()
            decision_trace["script_trace"] = script_trace
            return ScriptAgentResult(
                script_plan=fallback_plan,
                fallback=fallback_decision,
                context_governance=context_governance,
                quality_rubric=quality_rubric,
                hook_analysis=hook_analysis,
                setup_analysis=setup_analysis,
                payoff_analysis=payoff_analysis,
                diversity_analysis=diversity_analysis,
                provider_fallback_trace=provider_fallback_trace,
                confidence=confidence_calibration["confidence"],
                confidence_level=confidence_calibration["confidence_level"],
                confidence_components=confidence_calibration["confidence_components"],
                confidence_rationale=confidence_calibration["confidence_rationale"],
                script_trace=script_trace,
                decision_trace=decision_trace,
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
