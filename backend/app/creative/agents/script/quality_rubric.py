from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from app.creative.agents.script.models import ScriptAgentInput
from app.creative.contracts.creative_pack import ScriptPlan


SCRIPT_QUALITY_RUBRIC_VERSION = "script_quality_rubric_v2_6"

_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "after",
    "at",
    "before",
    "by",
    "for",
    "from",
    "in",
    "inside",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "with",
}
_GENERIC_PHRASES = {
    "you won't believe",
    "you wont believe",
    "watch until the end",
    "this changes everything",
    "what happened next",
    "you need to see this",
    "the truth will shock you",
    "this is crazy",
    "did you know",
}
_WEAK_PAYOFF_TERMS = {
    "amazing",
    "awesome",
    "crazy",
    "insane",
    "shocking",
    "unbelievable",
    "wild",
}
_CONCRETE_TERMS = {
    "archive",
    "camera",
    "case",
    "door",
    "evidence",
    "floorplan",
    "guard",
    "key",
    "lock",
    "log",
    "mirror",
    "recorder",
    "room",
    "server",
    "signature",
    "timestamp",
    "voice",
    "wall",
    "warning",
    "witness",
}


@dataclass(frozen=True)
class ScriptRubricComponent:
    name: str
    score: float
    level: str
    reason_code: str
    evidence: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScriptQualityRubricResult:
    rubric_version: str
    overall_score: float
    overall_level: str
    components: dict[str, dict[str, Any]]
    strong_components: list[str]
    weak_components: list[str]
    missing_components: list[str]
    boundary_statement: str
    rubric_meaning: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rubric_version": self.rubric_version,
            "overall_score": self.overall_score,
            "overall_level": self.overall_level,
            "components": {key: dict(value) for key, value in self.components.items()},
            "strong_components": list(self.strong_components),
            "weak_components": list(self.weak_components),
            "missing_components": list(self.missing_components),
            "boundary_statement": self.boundary_statement,
            "rubric_meaning": self.rubric_meaning,
            "rationale": list(self.rationale),
        }


class ScriptQualityRubricEvaluator:
    """Scores script construction quality without changing the script or acting as QC."""

    COMPONENT_WEIGHTS: dict[str, float] = {
        "hook_clarity": 0.12,
        "hook_specificity": 0.12,
        "setup_coherence": 0.10,
        "setup_progression": 0.10,
        "payoff_specificity": 0.13,
        "payoff_memorability": 0.12,
        "cta_fit": 0.05,
        "trend_alignment": 0.08,
        "strategy_alignment": 0.08,
        "repetition_risk": 0.05,
        "cliche_risk": 0.05,
    }

    def evaluate(
        self,
        *,
        script_plan: ScriptPlan,
        data: ScriptAgentInput,
        context_governance: dict[str, Any] | None = None,
    ) -> ScriptQualityRubricResult:
        del context_governance
        components = {
            "hook_clarity": self._hook_clarity(script_plan.hook),
            "hook_specificity": self._hook_specificity(script_plan.hook, data.topic),
            "setup_coherence": self._setup_coherence(script_plan.hook, script_plan.setup, script_plan.payoff),
            "setup_progression": self._setup_progression(script_plan.hook, script_plan.setup, script_plan.payoff),
            "payoff_specificity": self._payoff_specificity(script_plan.payoff, data.topic),
            "payoff_memorability": self._payoff_memorability(script_plan.hook, script_plan.payoff),
            "cta_fit": self._cta_fit(script_plan),
            "trend_alignment": self._trend_alignment(script_plan, data),
            "strategy_alignment": self._strategy_alignment(script_plan, data),
            "repetition_risk": self._repetition_risk(script_plan),
            "cliche_risk": self._cliche_risk(script_plan),
        }

        overall = 0.0
        for name, component in components.items():
            overall += component.score * self.COMPONENT_WEIGHTS[name]
        overall_score = round(min(max(overall, 0.0), 1.0), 4)
        component_payload = {name: component.to_dict() for name, component in components.items()}

        weak_components = [name for name, component in components.items() if component.level == "low"]
        strong_components = [name for name, component in components.items() if component.level == "high"]
        missing_components = [
            name
            for name, component in components.items()
            if str(component.reason_code).endswith("_MISSING") or component.reason_code == "CTA_FIELD_NOT_PRESENT"
        ]
        rationale = [
            "Rubric evaluates script construction only; it does not decide publishability.",
            "Scores are deterministic and based on emitted hook/setup/payoff plus available upstream context.",
        ]
        if weak_components:
            rationale.append("Weak construction components detected: " + ", ".join(weak_components))
        else:
            rationale.append("No low-level construction components detected.")

        return ScriptQualityRubricResult(
            rubric_version=SCRIPT_QUALITY_RUBRIC_VERSION,
            overall_score=overall_score,
            overall_level=self._level(overall_score),
            components=component_payload,
            strong_components=strong_components,
            weak_components=weak_components,
            missing_components=missing_components,
            boundary_statement="Script rubric explains narrative construction; QC remains the product quality authority.",
            rubric_meaning="script_construction_quality_not_publishability",
            rationale=rationale,
        )

    def _hook_clarity(self, hook: str) -> ScriptRubricComponent:
        tokens = self._tokens(hook)
        if not tokens:
            return self._component("hook_clarity", 0.0, "HOOK_MISSING", {"word_count": 0}, "Hook is missing.")
        word_count = len(tokens)
        if 3 <= word_count <= 14:
            score = 1.0
            reason = "HOOK_CLEAR_LENGTH"
            rationale = "Hook is present and concise enough for short-form narration."
        elif 15 <= word_count <= 22:
            score = 0.62
            reason = "HOOK_LONG_BUT_READABLE"
            rationale = "Hook is present but longer than ideal."
        else:
            score = 0.35
            reason = "HOOK_LENGTH_WEAK"
            rationale = "Hook length is outside the preferred range."
        return self._component("hook_clarity", score, reason, {"word_count": word_count}, rationale)

    def _hook_specificity(self, hook: str, topic: str) -> ScriptRubricComponent:
        hook_tokens = set(self._content_tokens(hook))
        topic_tokens = set(self._content_tokens(topic))
        overlap = sorted(hook_tokens & topic_tokens)
        concrete = sorted(token for token in hook_tokens if token in _CONCRETE_TERMS or any(char.isdigit() for char in token))
        generic = self._contains_generic_phrase(hook)
        if not hook_tokens:
            return self._component("hook_specificity", 0.0, "HOOK_MISSING", {"topic_overlap": [], "concrete_terms": []}, "Hook is missing.")
        if generic:
            score = 0.2
            reason = "HOOK_GENERIC_PHRASE"
            rationale = "Hook uses a generic engagement phrase instead of specific story evidence."
        elif len(overlap) >= 2 or len(concrete) >= 2:
            score = 1.0
            reason = "HOOK_SPECIFIC_EVIDENCE_PRESENT"
            rationale = "Hook includes concrete terms or topic-specific evidence."
        elif overlap or concrete:
            score = 0.65
            reason = "HOOK_PARTIALLY_SPECIFIC"
            rationale = "Hook includes some specific evidence but could be more concrete."
        else:
            score = 0.3
            reason = "HOOK_LOW_SPECIFICITY"
            rationale = "Hook lacks concrete topic linkage."
        return self._component(
            "hook_specificity",
            score,
            reason,
            {"topic_overlap": overlap, "concrete_terms": concrete, "generic_phrase_detected": generic},
            rationale,
        )

    def _setup_coherence(self, hook: str, setup: str, payoff: str) -> ScriptRubricComponent:
        setup_tokens = self._tokens(setup)
        if not setup_tokens:
            return self._component("setup_coherence", 0.0, "SETUP_MISSING", {"word_count": 0}, "Setup is missing.")
        duplicate = self._normalized(setup) in {self._normalized(hook), self._normalized(payoff)}
        if duplicate:
            score = 0.2
            reason = "SETUP_DUPLICATES_OTHER_BLOCK"
            rationale = "Setup duplicates another script block instead of developing the story."
        elif 4 <= len(setup_tokens) <= 18:
            score = 1.0
            reason = "SETUP_COHERENT_LENGTH"
            rationale = "Setup is present and appropriately concise."
        else:
            score = 0.58
            reason = "SETUP_LENGTH_PARTIAL"
            rationale = "Setup is present but its length is less ideal."
        return self._component(
            "setup_coherence",
            score,
            reason,
            {"word_count": len(setup_tokens), "duplicate_block": duplicate},
            rationale,
        )

    def _setup_progression(self, hook: str, setup: str, payoff: str) -> ScriptRubricComponent:
        hook_tokens = set(self._content_tokens(hook))
        setup_tokens = set(self._content_tokens(setup))
        payoff_tokens = set(self._content_tokens(payoff))
        if not setup_tokens:
            return self._component("setup_progression", 0.0, "SETUP_MISSING", {}, "Setup is missing.")
        hook_overlap = sorted(setup_tokens & hook_tokens)
        payoff_overlap = sorted(setup_tokens & payoff_tokens)
        duplicate_ratio = self._duplicate_ratio(hook, setup)
        if duplicate_ratio >= 0.75:
            score = 0.2
            reason = "SETUP_REPEATS_HOOK"
            rationale = "Setup repeats the hook too closely."
        elif hook_overlap or payoff_overlap:
            score = 0.86
            reason = "SETUP_CONNECTS_SCRIPT_BLOCKS"
            rationale = "Setup connects at least one neighboring script block while adding development."
        else:
            score = 0.5
            reason = "SETUP_CONNECTION_WEAK"
            rationale = "Setup is present but its connection to hook or payoff is weak."
        return self._component(
            "setup_progression",
            score,
            reason,
            {
                "hook_overlap": hook_overlap,
                "payoff_overlap": payoff_overlap,
                "duplicate_ratio": duplicate_ratio,
            },
            rationale,
        )

    def _payoff_specificity(self, payoff: str, topic: str) -> ScriptRubricComponent:
        payoff_tokens = set(self._content_tokens(payoff))
        topic_tokens = set(self._content_tokens(topic))
        overlap = sorted(payoff_tokens & topic_tokens)
        concrete = sorted(token for token in payoff_tokens if token in _CONCRETE_TERMS or any(char.isdigit() for char in token))
        weak_terms = sorted(token for token in payoff_tokens if token in _WEAK_PAYOFF_TERMS)
        if not payoff_tokens:
            return self._component("payoff_specificity", 0.0, "PAYOFF_MISSING", {}, "Payoff is missing.")
        if weak_terms and not concrete and not overlap:
            score = 0.18
            reason = "PAYOFF_GENERIC_WEAK_TERMS"
            rationale = "Payoff relies on generic intensity terms without concrete story evidence."
        elif len(concrete) >= 2 or len(overlap) >= 2:
            score = 1.0
            reason = "PAYOFF_SPECIFIC_EVIDENCE_PRESENT"
            rationale = "Payoff includes concrete or topic-specific evidence."
        elif concrete or overlap:
            score = 0.68
            reason = "PAYOFF_PARTIALLY_SPECIFIC"
            rationale = "Payoff has some concrete support."
        else:
            score = 0.34
            reason = "PAYOFF_LOW_SPECIFICITY"
            rationale = "Payoff lacks concrete story evidence."
        return self._component(
            "payoff_specificity",
            score,
            reason,
            {"topic_overlap": overlap, "concrete_terms": concrete, "weak_terms": weak_terms},
            rationale,
        )

    def _payoff_memorability(self, hook: str, payoff: str) -> ScriptRubricComponent:
        payoff_tokens = set(self._content_tokens(payoff))
        hook_tokens = set(self._content_tokens(hook))
        if not payoff_tokens:
            return self._component("payoff_memorability", 0.0, "PAYOFF_MISSING", {}, "Payoff is missing.")
        reversal_terms = sorted(payoff_tokens & {"before", "inside", "behind", "dead", "tomorrow", "years", "final", "second"})
        duplicate_ratio = self._duplicate_ratio(hook, payoff)
        if duplicate_ratio >= 0.75:
            score = 0.2
            reason = "PAYOFF_REPEATS_HOOK"
            rationale = "Payoff repeats the hook instead of resolving or reframing it."
        elif reversal_terms:
            score = 0.92
            reason = "PAYOFF_MEMORABLE_REVERSAL"
            rationale = "Payoff includes a concrete reversal or reveal cue."
        elif len(payoff_tokens) >= 5:
            score = 0.62
            reason = "PAYOFF_COMPLETE_BUT_LOW_TWIST"
            rationale = "Payoff is complete but has limited memorability cues."
        else:
            score = 0.32
            reason = "PAYOFF_TOO_THIN"
            rationale = "Payoff is too thin to be memorable."
        return self._component(
            "payoff_memorability",
            score,
            reason,
            {"reversal_terms": reversal_terms, "duplicate_ratio": duplicate_ratio},
            rationale,
        )

    def _cta_fit(self, script_plan: ScriptPlan) -> ScriptRubricComponent:
        has_cta = bool(getattr(script_plan, "cta", ""))
        if not has_cta:
            return self._component(
                "cta_fit",
                0.5,
                "CTA_FIELD_NOT_PRESENT",
                {"cta_present": False},
                "Current ScriptPlan contract does not expose a CTA field; rubric records neutral audit status.",
            )
        return self._component(
            "cta_fit",
            0.8,
            "CTA_PRESENT",
            {"cta_present": True},
            "CTA is present in the script contract.",
        )

    def _trend_alignment(self, script_plan: ScriptPlan, data: ScriptAgentInput) -> ScriptRubricComponent:
        trend = data.trend_profile
        if trend is None:
            return self._component(
                "trend_alignment",
                0.5,
                "TREND_CONTEXT_MISSING",
                {"trend_present": False},
                "Trend context is unavailable; neutral score preserves backward compatibility.",
            )
        script_tokens = set(self._content_tokens(self._script_text(script_plan)))
        hook_tokens = set()
        for hook in trend.dominant_hooks:
            hook_tokens.update(self._content_tokens(hook))
        overlap = sorted(script_tokens & hook_tokens)
        if overlap:
            score = 0.85
            reason = "TREND_ALIGNMENT_VISIBLE"
            rationale = "Script text overlaps with governed trend hook context."
        elif trend.dominant_hooks:
            score = 0.45
            reason = "TREND_ALIGNMENT_WEAK"
            rationale = "Trend context exists but no direct alignment is visible in emitted script text."
        else:
            score = 0.55
            reason = "TREND_CONTEXT_NO_DOMINANT_HOOKS"
            rationale = "Trend context is present but has no dominant hooks to compare."
        return self._component(
            "trend_alignment",
            score,
            reason,
            {"trend_present": True, "dominant_hooks": list(trend.dominant_hooks), "overlap": overlap},
            rationale,
        )

    def _strategy_alignment(self, script_plan: ScriptPlan, data: ScriptAgentInput) -> ScriptRubricComponent:
        strategy = data.strategy_profile
        if strategy is None:
            return self._component(
                "strategy_alignment",
                0.5,
                "STRATEGY_CONTEXT_MISSING",
                {"strategy_present": False},
                "Strategy context is unavailable; neutral score preserves Script boundary.",
            )
        hook_words = len(self._tokens(script_plan.hook))
        target = str(strategy.hook_aggressiveness or "").lower()
        if target == "high" and hook_words >= 4:
            score = 0.82
            reason = "STRATEGY_HOOK_AGGRESSIVENESS_ALIGNED"
            rationale = "High hook aggressiveness is compatible with a concrete present hook."
        elif target in {"low", "medium"}:
            score = 0.75
            reason = "STRATEGY_ALIGNMENT_BOUNDED"
            rationale = "Script remains compatible with bounded Strategy direction."
        else:
            score = 0.58
            reason = "STRATEGY_ALIGNMENT_PARTIAL"
            rationale = "Strategy context is present but alignment is only partially observable."
        return self._component(
            "strategy_alignment",
            score,
            reason,
            {"strategy_present": True, "hook_aggressiveness": target, "hook_word_count": hook_words},
            rationale,
        )

    def _repetition_risk(self, script_plan: ScriptPlan) -> ScriptRubricComponent:
        blocks = [script_plan.hook, script_plan.setup, script_plan.payoff]
        normalized_blocks = [self._normalized(block) for block in blocks if self._normalized(block)]
        duplicate_blocks = len(normalized_blocks) - len(set(normalized_blocks))
        all_tokens = self._content_tokens(" ".join(blocks))
        repeated_tokens = sorted({token for token in all_tokens if all_tokens.count(token) >= 3})
        if duplicate_blocks > 0:
            score = 0.15
            reason = "REPETITION_BLOCK_DUPLICATE"
            rationale = "At least one script block duplicates another block."
        elif repeated_tokens:
            score = 0.55
            reason = "REPETITION_TOKEN_CLUSTER"
            rationale = "Repeated content terms are visible across script blocks."
        else:
            score = 0.9
            reason = "REPETITION_RISK_LOW"
            rationale = "No material block repetition detected."
        return self._component(
            "repetition_risk",
            score,
            reason,
            {"duplicate_blocks": duplicate_blocks, "repeated_tokens": repeated_tokens},
            rationale,
        )

    def _cliche_risk(self, script_plan: ScriptPlan) -> ScriptRubricComponent:
        text = self._script_text(script_plan)
        phrases = sorted(phrase for phrase in _GENERIC_PHRASES if phrase in self._normalized(text))
        weak_terms = sorted({token for token in self._content_tokens(text) if token in _WEAK_PAYOFF_TERMS})
        if phrases:
            score = 0.15
            reason = "CLICHE_PHRASE_DETECTED"
            rationale = "Script contains generic short-form cliche phrasing."
        elif len(weak_terms) >= 2:
            score = 0.42
            reason = "CLICHE_WEAK_INTENSITY_TERMS"
            rationale = "Script uses repeated generic intensity terms."
        else:
            score = 0.9
            reason = "CLICHE_RISK_LOW"
            rationale = "No configured cliche phrase detected."
        return self._component(
            "cliche_risk",
            score,
            reason,
            {"generic_phrases": phrases, "weak_terms": weak_terms},
            rationale,
        )

    def _component(
        self,
        name: str,
        score: float,
        reason_code: str,
        evidence: dict[str, Any],
        rationale: str,
    ) -> ScriptRubricComponent:
        normalized_score = round(min(max(score, 0.0), 1.0), 4)
        return ScriptRubricComponent(
            name=name,
            score=normalized_score,
            level=self._level(normalized_score),
            reason_code=reason_code,
            evidence=evidence,
            rationale=rationale,
        )

    def _level(self, score: float) -> str:
        if score < 0.35:
            return "low"
        if score < 0.7:
            return "medium"
        return "high"

    def _script_text(self, script_plan: ScriptPlan) -> str:
        return " ".join([script_plan.hook or "", script_plan.setup or "", script_plan.payoff or ""])

    def _normalized(self, text: str) -> str:
        return " ".join(self._tokens(text))

    def _tokens(self, text: str) -> list[str]:
        return _WORD_RE.findall(str(text or "").lower())

    def _content_tokens(self, text: str) -> list[str]:
        return [token for token in self._tokens(text) if token not in _STOPWORDS]

    def _contains_generic_phrase(self, text: str) -> bool:
        normalized = self._normalized(text)
        return any(phrase in normalized for phrase in _GENERIC_PHRASES)

    def _duplicate_ratio(self, left: str, right: str) -> float:
        left_tokens = set(self._content_tokens(left))
        right_tokens = set(self._content_tokens(right))
        if not left_tokens or not right_tokens:
            return 0.0
        return round(len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens)), 4)
