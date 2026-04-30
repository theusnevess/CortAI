from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import ScriptPlan


SCRIPT_TRACE_AUDITABILITY_VERSION = "script_trace_auditability_v2_6"


@dataclass(frozen=True)
class ScriptTraceAuditSummary:
    reconstructible: bool
    required_sections_present: bool
    context_governance_present: bool
    quality_rubric_present: bool
    hook_analysis_present: bool
    setup_analysis_present: bool
    payoff_analysis_present: bool
    diversity_analysis_present: bool
    provider_fallback_trace_present: bool
    confidence_calibration_present: bool
    fallback_visible: bool
    script_output_present: bool
    decision_trace_backward_compatible: bool
    silent_failure_indicators: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reconstructible": self.reconstructible,
            "required_sections_present": self.required_sections_present,
            "context_governance_present": self.context_governance_present,
            "quality_rubric_present": self.quality_rubric_present,
            "hook_analysis_present": self.hook_analysis_present,
            "setup_analysis_present": self.setup_analysis_present,
            "payoff_analysis_present": self.payoff_analysis_present,
            "diversity_analysis_present": self.diversity_analysis_present,
            "provider_fallback_trace_present": self.provider_fallback_trace_present,
            "confidence_calibration_present": self.confidence_calibration_present,
            "fallback_visible": self.fallback_visible,
            "script_output_present": self.script_output_present,
            "decision_trace_backward_compatible": self.decision_trace_backward_compatible,
            "silent_failure_indicators": list(self.silent_failure_indicators),
        }


@dataclass(frozen=True)
class ScriptTraceResult:
    context_governance: dict[str, Any]
    quality_rubric: dict[str, Any]
    hook_analysis: dict[str, Any]
    setup_analysis: dict[str, Any]
    payoff_analysis: dict[str, Any]
    diversity_analysis: dict[str, Any]
    provider_fallback_trace: dict[str, Any]
    confidence_calibration: dict[str, Any]
    final_script_rationale: dict[str, Any]
    missing_or_degraded_inputs: list[dict[str, Any]]
    audit_summary: dict[str, Any]
    trace_version: str = SCRIPT_TRACE_AUDITABILITY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_governance": dict(self.context_governance),
            "quality_rubric": dict(self.quality_rubric),
            "hook_analysis": dict(self.hook_analysis),
            "setup_analysis": dict(self.setup_analysis),
            "payoff_analysis": dict(self.payoff_analysis),
            "diversity_analysis": dict(self.diversity_analysis),
            "provider_fallback_trace": dict(self.provider_fallback_trace),
            "confidence_calibration": dict(self.confidence_calibration),
            "final_script_rationale": dict(self.final_script_rationale),
            "missing_or_degraded_inputs": [dict(item) for item in self.missing_or_degraded_inputs],
            "audit_summary": dict(self.audit_summary),
            "trace_version": self.trace_version,
        }


class ScriptTraceBuilder:
    """Consolidates Script v2.6 audit layers without changing generation behavior."""

    REQUIRED_SECTIONS: tuple[str, ...] = (
        "context_governance",
        "quality_rubric",
        "hook_analysis",
        "setup_analysis",
        "payoff_analysis",
        "diversity_analysis",
        "provider_fallback_trace",
        "confidence_calibration",
    )

    def build(
        self,
        *,
        script_plan: ScriptPlan,
        fallback: FallbackDecision,
        context_governance: dict[str, Any],
        quality_rubric: dict[str, Any],
        hook_analysis: dict[str, Any],
        setup_analysis: dict[str, Any],
        payoff_analysis: dict[str, Any],
        diversity_analysis: dict[str, Any],
        provider_fallback_trace: dict[str, Any],
        confidence_calibration: dict[str, Any],
    ) -> ScriptTraceResult:
        sections = {
            "context_governance": context_governance,
            "quality_rubric": quality_rubric,
            "hook_analysis": hook_analysis,
            "setup_analysis": setup_analysis,
            "payoff_analysis": payoff_analysis,
            "diversity_analysis": diversity_analysis,
            "provider_fallback_trace": provider_fallback_trace,
            "confidence_calibration": confidence_calibration,
        }
        final_rationale = self._final_script_rationale(
            script_plan=script_plan,
            fallback=fallback,
            context_governance=context_governance,
            quality_rubric=quality_rubric,
            hook_analysis=hook_analysis,
            setup_analysis=setup_analysis,
            payoff_analysis=payoff_analysis,
            diversity_analysis=diversity_analysis,
            provider_fallback_trace=provider_fallback_trace,
            confidence_calibration=confidence_calibration,
        )
        missing_or_degraded = self._missing_or_degraded_inputs(
            context_governance=context_governance,
            quality_rubric=quality_rubric,
            hook_analysis=hook_analysis,
            setup_analysis=setup_analysis,
            payoff_analysis=payoff_analysis,
            diversity_analysis=diversity_analysis,
            provider_fallback_trace=provider_fallback_trace,
        )
        audit_summary = self._audit_summary(
            sections=sections,
            script_plan=script_plan,
            fallback=fallback,
            final_script_rationale=final_rationale,
        ).to_dict()
        return ScriptTraceResult(
            context_governance=context_governance,
            quality_rubric=quality_rubric,
            hook_analysis=hook_analysis,
            setup_analysis=setup_analysis,
            payoff_analysis=payoff_analysis,
            diversity_analysis=diversity_analysis,
            provider_fallback_trace=provider_fallback_trace,
            confidence_calibration=confidence_calibration,
            final_script_rationale=final_rationale,
            missing_or_degraded_inputs=missing_or_degraded,
            audit_summary=audit_summary,
        )

    def _final_script_rationale(
        self,
        *,
        script_plan: ScriptPlan,
        fallback: FallbackDecision,
        context_governance: dict[str, Any],
        quality_rubric: dict[str, Any],
        hook_analysis: dict[str, Any],
        setup_analysis: dict[str, Any],
        payoff_analysis: dict[str, Any],
        diversity_analysis: dict[str, Any],
        provider_fallback_trace: dict[str, Any],
        confidence_calibration: dict[str, Any],
    ) -> dict[str, Any]:
        fallback_used = bool(provider_fallback_trace.get("fallback_used", fallback.used))
        provider_used = str(provider_fallback_trace.get("provider_used") or "")
        confidence_level = str(
            confidence_calibration.get("confidence_level")
            or (confidence_calibration.get("confidence_rationale") or {}).get("confidence_level")
            or ""
        )
        reason_codes = self._dominant_reason_codes(
            hook_analysis=hook_analysis,
            setup_analysis=setup_analysis,
            payoff_analysis=payoff_analysis,
            diversity_analysis=diversity_analysis,
            quality_rubric=quality_rubric,
        )
        rationale = [
            "ScriptPlan was emitted from the existing generator or fallback path without trace-time rewriting.",
            f"Provider path resolved to {provider_used or 'unknown provider metadata'}.",
            f"Construction confidence is {confidence_level or 'unknown'} and means trust in script construction.",
        ]
        if fallback_used:
            rationale.append("Fallback is visible and included in the reconstruction trace.")
        if context_governance.get("degraded_context"):
            rationale.append("Degraded upstream context is visible in context governance.")
        if quality_rubric.get("weak_components"):
            rationale.append("Weak rubric components are visible and did not trigger hidden rewriting.")

        return {
            "script_emitted": self._script_output_present(script_plan),
            "generation_mode": str(script_plan.generation_mode or ""),
            "fallback_used": fallback_used,
            "fallback_mode": provider_fallback_trace.get("fallback_mode", fallback.mode),
            "fallback_reason": provider_fallback_trace.get("fallback_reason", fallback.reason),
            "fallback_type": str(provider_fallback_trace.get("fallback_type") or ""),
            "provider_used": provider_used,
            "provider_success": bool(provider_fallback_trace.get("provider_success")),
            "confidence": confidence_calibration.get("confidence"),
            "confidence_level": confidence_level,
            "quality_overall_score": quality_rubric.get("overall_score"),
            "quality_overall_level": quality_rubric.get("overall_level"),
            "hook_strength_level": hook_analysis.get("strength_level"),
            "setup_progression_level": setup_analysis.get("progression_level"),
            "payoff_memorability_level": payoff_analysis.get("memorability_level"),
            "cliche_risk_level": diversity_analysis.get("cliche_risk_level"),
            "repetition_risk_level": diversity_analysis.get("repetition_risk_level"),
            "context_policy_respected": bool(context_governance.get("policy_respected", False)),
            "dominant_reason_codes": reason_codes,
            "boundary_statement": "Script trace explains construction only; Strategy and QC retain their own authority.",
            "rationale": rationale,
        }

    def _dominant_reason_codes(
        self,
        *,
        hook_analysis: dict[str, Any],
        setup_analysis: dict[str, Any],
        payoff_analysis: dict[str, Any],
        diversity_analysis: dict[str, Any],
        quality_rubric: dict[str, Any],
    ) -> list[str]:
        reason_codes: list[str] = []
        for analysis in (hook_analysis, setup_analysis, payoff_analysis, diversity_analysis):
            for code in analysis.get("reason_codes") or []:
                reason_codes.append(str(code))
        components = dict(quality_rubric.get("components") or {})
        for name in sorted(quality_rubric.get("weak_components") or []):
            component = dict(components.get(name) or {})
            reason = str(component.get("reason_code") or "")
            if reason:
                reason_codes.append(reason)
        return self._unique(reason_codes)

    def _missing_or_degraded_inputs(
        self,
        *,
        context_governance: dict[str, Any],
        quality_rubric: dict[str, Any],
        hook_analysis: dict[str, Any],
        setup_analysis: dict[str, Any],
        payoff_analysis: dict[str, Any],
        diversity_analysis: dict[str, Any],
        provider_fallback_trace: dict[str, Any],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for key in context_governance.get("missing_context") or []:
            items.append(
                self._item(
                    kind="missing_context",
                    identifier=str(key),
                    impact="context_governance",
                    rationale=f"{key} was not available to Script context intake.",
                )
            )
        for key in context_governance.get("degraded_context") or []:
            items.append(
                self._item(
                    kind="degraded_context",
                    identifier=str(key),
                    impact="context_governance",
                    rationale=f"{key} was available but marked degraded.",
                )
            )
        components = dict(quality_rubric.get("components") or {})
        for key in quality_rubric.get("missing_components") or []:
            items.append(
                self._item(
                    kind="missing_rubric_component",
                    identifier=str(key),
                    impact="quality_rubric",
                    rationale=f"{key} has missing or neutral audit evidence in the rubric.",
                )
            )
        for key in quality_rubric.get("weak_components") or []:
            component = dict(components.get(key) or {})
            items.append(
                self._item(
                    kind="weak_component",
                    identifier=str(key),
                    impact="quality_rubric",
                    rationale=str(component.get("rationale") or f"{key} was classified low by the rubric."),
                )
            )
        if hook_analysis.get("generic_hook_detected"):
            items.append(
                self._item(
                    kind="generic_hook",
                    identifier="hook",
                    impact="hook_analysis",
                    rationale="Generic hook phrasing was detected.",
                )
            )
        if hook_analysis.get("unsupported_claim_detected"):
            items.append(
                self._item(
                    kind="unsupported_hook_claim",
                    identifier="hook",
                    impact="hook_analysis",
                    rationale="Hook claim wording lacks direct topic or evidence support.",
                )
            )
        if str(hook_analysis.get("strength_level") or "") == "low":
            items.append(
                self._item(
                    kind="low_hook_strength",
                    identifier="hook",
                    impact="hook_analysis",
                    rationale="Hook strength was classified low.",
                )
            )
        if setup_analysis.get("repetition_detected"):
            items.append(
                self._item(
                    kind="setup_repetition",
                    identifier="setup",
                    impact="setup_analysis",
                    rationale="Setup repeats a neighboring script block too closely.",
                )
            )
        if setup_analysis.get("unsupported_context_detected"):
            items.append(
                self._item(
                    kind="unsupported_setup_context",
                    identifier="setup",
                    impact="setup_analysis",
                    rationale="Setup introduces unsupported context.",
                )
            )
        if str(setup_analysis.get("progression_level") or "") == "low":
            items.append(
                self._item(
                    kind="low_setup_progression",
                    identifier="setup",
                    impact="setup_analysis",
                    rationale="Setup progression was classified low.",
                )
            )
        if payoff_analysis.get("generic_payoff_detected"):
            items.append(
                self._item(
                    kind="generic_payoff",
                    identifier="payoff",
                    impact="payoff_analysis",
                    rationale="Generic payoff phrasing was detected.",
                )
            )
        if payoff_analysis.get("vague_motivational_detected"):
            items.append(
                self._item(
                    kind="vague_payoff",
                    identifier="payoff",
                    impact="payoff_analysis",
                    rationale="Vague motivational payoff language was detected without concrete support.",
                )
            )
        if str(payoff_analysis.get("memorability_level") or "") == "low":
            items.append(
                self._item(
                    kind="low_payoff_memorability",
                    identifier="payoff",
                    impact="payoff_analysis",
                    rationale="Payoff memorability was classified low.",
                )
            )
        if str(diversity_analysis.get("cliche_risk_level") or "") == "high":
            items.append(
                self._item(
                    kind="high_cliche_risk",
                    identifier="script",
                    impact="diversity_analysis",
                    rationale="High cliche risk was detected in the emitted script.",
                )
            )
        if str(diversity_analysis.get("repetition_risk_level") or "") == "high":
            items.append(
                self._item(
                    kind="high_repetition_risk",
                    identifier="script",
                    impact="diversity_analysis",
                    rationale="High repetition risk was detected in the emitted script.",
                )
            )
        for failure in provider_fallback_trace.get("provider_failures") or []:
            items.append(
                self._item(
                    kind="provider_failure",
                    identifier=str(failure),
                    impact="provider_fallback_trace",
                    rationale="Provider failure was reported by generator metadata.",
                )
            )
        if provider_fallback_trace.get("fallback_used"):
            items.append(
                self._item(
                    kind="fallback",
                    identifier=str(provider_fallback_trace.get("fallback_type") or "fallback"),
                    impact="provider_fallback_trace",
                    rationale="Script fallback was used and is visible in trace.",
                )
            )
        if provider_fallback_trace.get("repair_status") == "not_reported_by_generator":
            items.append(
                self._item(
                    kind="repair_status_unknown",
                    identifier="repair_status",
                    impact="provider_fallback_trace",
                    rationale="The current generator contract does not report repair status.",
                )
            )
        return items

    def _audit_summary(
        self,
        *,
        sections: dict[str, dict[str, Any]],
        script_plan: ScriptPlan,
        fallback: FallbackDecision,
        final_script_rationale: dict[str, Any],
    ) -> ScriptTraceAuditSummary:
        present = {key: bool(sections.get(key)) for key in self.REQUIRED_SECTIONS}
        indicators: list[str] = []
        for section, is_present in present.items():
            if not is_present:
                indicators.append(f"MISSING_SECTION:{section}")
        script_output_present = self._script_output_present(script_plan)
        if not script_output_present:
            indicators.append("SCRIPT_OUTPUT_MISSING")
        fallback_visible = self._fallback_visible(fallback=fallback, provider_fallback_trace=sections.get("provider_fallback_trace") or {})
        if not fallback_visible:
            indicators.append("FALLBACK_STATUS_NOT_VISIBLE")
        if not final_script_rationale:
            indicators.append("FINAL_SCRIPT_RATIONALE_MISSING")
        required_sections_present = all(present.values())
        reconstructible = required_sections_present and script_output_present and fallback_visible and bool(final_script_rationale)
        return ScriptTraceAuditSummary(
            reconstructible=reconstructible,
            required_sections_present=required_sections_present,
            context_governance_present=present["context_governance"],
            quality_rubric_present=present["quality_rubric"],
            hook_analysis_present=present["hook_analysis"],
            setup_analysis_present=present["setup_analysis"],
            payoff_analysis_present=present["payoff_analysis"],
            diversity_analysis_present=present["diversity_analysis"],
            provider_fallback_trace_present=present["provider_fallback_trace"],
            confidence_calibration_present=present["confidence_calibration"],
            fallback_visible=fallback_visible,
            script_output_present=script_output_present,
            decision_trace_backward_compatible=True,
            silent_failure_indicators=indicators,
        )

    def _fallback_visible(self, *, fallback: FallbackDecision, provider_fallback_trace: dict[str, Any]) -> bool:
        if "fallback_used" in provider_fallback_trace:
            return True
        return fallback.used is not None and fallback.mode is not None

    def _script_output_present(self, script_plan: ScriptPlan) -> bool:
        return bool(
            str(script_plan.hook or "").strip()
            and str(script_plan.setup or "").strip()
            and str(script_plan.payoff or "").strip()
        )

    def _item(self, *, kind: str, identifier: str, impact: str, rationale: str) -> dict[str, Any]:
        return {
            "kind": kind,
            "identifier": identifier,
            "impact": impact,
            "rationale": rationale,
        }

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_values: list[str] = []
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            unique_values.append(value)
        return unique_values
