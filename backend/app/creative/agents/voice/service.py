from __future__ import annotations

from dataclasses import dataclass, field

from app.content.pipeline.kokoro_adapter import DEFAULT_KOKORO_VOICE
from app.creative.agents.voice.audio_validation_linkage import VoiceAudioValidationLinker
from app.creative.agents.voice.confidence_calibration import VoiceConfidenceCalibrator
from app.creative.agents.voice.delivery_semantics import VoiceDeliverySemanticsMapper
from app.creative.agents.voice.interpreter import VoiceInterpreter
from app.creative.agents.voice.models import VoiceAgentInput, VoiceAgentResult
from app.creative.agents.voice.monotony_contrast import VoiceMonotonyContrastAnalyzer
from app.creative.agents.voice.provider_fallback_honesty import VoiceProviderFallbackHonestyReporter
from app.creative.agents.voice.segment_timing import VoiceSegmentTimingAnalyzer
from app.creative.agents.voice.trace_auditability import VoiceTraceBuilder
from app.creative.agents.voice.voice_plan_governance import VoicePlanGovernanceEvaluator
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ScriptPlan, VoicePlan, VoiceRuntimeConstraints


@dataclass
class VoiceAgentService:
    interpreter: VoiceInterpreter = field(default_factory=VoiceInterpreter)
    voice_plan_governance_evaluator: VoicePlanGovernanceEvaluator = field(default_factory=VoicePlanGovernanceEvaluator)
    delivery_semantics_mapper: VoiceDeliverySemanticsMapper = field(default_factory=VoiceDeliverySemanticsMapper)
    segment_timing_analyzer: VoiceSegmentTimingAnalyzer = field(default_factory=VoiceSegmentTimingAnalyzer)
    monotony_contrast_analyzer: VoiceMonotonyContrastAnalyzer = field(default_factory=VoiceMonotonyContrastAnalyzer)
    provider_fallback_honesty_reporter: VoiceProviderFallbackHonestyReporter = field(default_factory=VoiceProviderFallbackHonestyReporter)
    audio_validation_linker: VoiceAudioValidationLinker = field(default_factory=VoiceAudioValidationLinker)
    confidence_calibrator: VoiceConfidenceCalibrator = field(default_factory=VoiceConfidenceCalibrator)
    trace_builder: VoiceTraceBuilder = field(default_factory=VoiceTraceBuilder)

    def resolve(
        self,
        *,
        account_id: str,
        niche: str,
        script_plan: ScriptPlan | None = None,
        strategy_profile=None,
    ) -> VoiceAgentResult:
        return self.resolve_for_input(
            VoiceAgentInput(
                account_id=account_id,
                niche=niche,
                script_plan=script_plan,
                strategy_profile=strategy_profile,
            )
        )

    def resolve_for_input(self, request: VoiceAgentInput) -> VoiceAgentResult:
        interpretation = self.interpreter.interpret(
            niche=request.niche,
            script_plan=request.script_plan or self._default_script_plan(),
            strategy_profile=request.strategy_profile,
        )
        voice_plan = VoicePlan(
            provider="kokoro",
            voice_id=DEFAULT_KOKORO_VOICE,
            style=interpretation.style,
            fallback_used=False,
            delivery_profile=interpretation.delivery_profile,
            segments=interpretation.segments,
            runtime_constraints=VoiceRuntimeConstraints(
                allow_provider_fallback=True,
                fallback_order=["kokoro", "piper"],
            ),
        )
        voice_plan_governance = self.voice_plan_governance_evaluator.evaluate(
            voice_plan=voice_plan,
            request=request,
        ).to_dict()
        delivery_semantics = self.delivery_semantics_mapper.map(
            voice_plan=voice_plan,
            script_plan=request.script_plan or self._default_script_plan(),
            voice_plan_governance=voice_plan_governance,
        ).to_dict()
        segment_timing = self.segment_timing_analyzer.analyze(
            voice_plan=voice_plan,
            delivery_semantics=delivery_semantics,
        ).to_dict()
        monotony_contrast_analysis = self.monotony_contrast_analyzer.analyze(
            voice_plan=voice_plan,
            segment_timing=segment_timing,
            delivery_semantics=delivery_semantics,
        ).to_dict()
        fallback_decision = FallbackDecision(
            used=False,
            mode=FallbackMode.NONE.value,
            reason="",
        )
        provider_fallback_honesty = self.provider_fallback_honesty_reporter.report(
            voice_plan=voice_plan,
            voice_agent_fallback=fallback_decision,
            voice_plan_governance=voice_plan_governance,
        ).to_dict()
        audio_validation_linkage = self.audio_validation_linker.link(
            voice_plan=voice_plan,
        ).to_dict()
        confidence_calibration = self.confidence_calibrator.calibrate(
            voice_plan_governance=voice_plan_governance,
            delivery_semantics=delivery_semantics,
            segment_timing=segment_timing,
            monotony_contrast_analysis=monotony_contrast_analysis,
            provider_fallback_honesty=provider_fallback_honesty,
            audio_validation_linkage=audio_validation_linkage,
        ).to_dict()
        voice_trace = self.trace_builder.build(
            voice_plan=voice_plan,
            fallback=fallback_decision,
            voice_plan_governance=voice_plan_governance,
            delivery_semantics=delivery_semantics,
            segment_timing=segment_timing,
            monotony_contrast_analysis=monotony_contrast_analysis,
            provider_fallback_honesty=provider_fallback_honesty,
            audio_validation_linkage=audio_validation_linkage,
            confidence_calibration=confidence_calibration,
        ).to_dict()
        return VoiceAgentResult(
            voice_plan=voice_plan,
            fallback=fallback_decision,
            voice_plan_governance=voice_plan_governance,
            delivery_semantics=delivery_semantics,
            segment_timing=segment_timing,
            monotony_contrast_analysis=monotony_contrast_analysis,
            provider_fallback_honesty=provider_fallback_honesty,
            audio_validation_linkage=audio_validation_linkage,
            confidence=confidence_calibration["confidence"],
            confidence_level=confidence_calibration["confidence_level"],
            confidence_components=confidence_calibration["confidence_components"],
            confidence_rationale=confidence_calibration["confidence_rationale"],
            confidence_calibration=confidence_calibration,
            voice_trace=voice_trace,
        )

    def _default_script_plan(self) -> ScriptPlan:
        return ScriptPlan(hook="", setup="", payoff="", generation_mode="voice_default")
