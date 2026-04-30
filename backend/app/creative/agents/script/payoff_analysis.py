from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from app.creative.agents.script.models import ScriptAgentInput
from app.creative.contracts.creative_pack import ScriptPlan


SCRIPT_PAYOFF_ANALYSIS_VERSION = "script_payoff_analysis_v2_6"

_WORD_RE = re.compile(r"[a-z0-9']+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "before",
    "by",
    "for",
    "from",
    "in",
    "inside",
    "into",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "was",
    "with",
}
_GENERIC_PAYOFF_PHRASES = {
    "and everything changed",
    "it was all a lie",
    "nobody expected it",
    "that was the truth",
    "the truth was revealed",
    "this changes everything",
    "what happened next was shocking",
}
_MOTIVATIONAL_VAGUE_TERMS = {
    "amazing",
    "awesome",
    "believe",
    "believe",
    "crazy",
    "dream",
    "incredible",
    "inspire",
    "life",
    "mindset",
    "motivation",
    "shocking",
    "success",
    "truth",
    "unbelievable",
}
_CONCRETE_TERMS = {
    "archive",
    "camera",
    "case",
    "door",
    "evidence",
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
_RESOLUTION_TERMS = {
    "behind",
    "dead",
    "final",
    "found",
    "identified",
    "inside",
    "led",
    "named",
    "revealed",
    "signed",
    "timestamped",
}
_REFRAME_TERMS = {
    "before",
    "dead",
    "different",
    "final",
    "inside",
    "next",
    "second",
    "tomorrow",
    "years",
}


@dataclass(frozen=True)
class ScriptPayoffAnalysisResult:
    payoff_present: bool
    memorability_level: str
    specificity_level: str
    generic_payoff_detected: bool
    vague_motivational_detected: bool
    resolves_or_reframes_hook: bool
    resolution_mode: str
    reason_codes: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    rationale: list[str] = field(default_factory=list)
    analysis_version: str = SCRIPT_PAYOFF_ANALYSIS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "payoff_present": self.payoff_present,
            "memorability_level": self.memorability_level,
            "specificity_level": self.specificity_level,
            "generic_payoff_detected": self.generic_payoff_detected,
            "vague_motivational_detected": self.vague_motivational_detected,
            "resolves_or_reframes_hook": self.resolves_or_reframes_hook,
            "resolution_mode": self.resolution_mode,
            "reason_codes": list(self.reason_codes),
            "evidence": dict(self.evidence),
            "rationale": list(self.rationale),
            "analysis_version": self.analysis_version,
        }


class ScriptPayoffMemorabilityAnalyzer:
    """Analyzes emitted payoff memorability without rewriting or predicting performance."""

    def analyze(self, *, script_plan: ScriptPlan, data: ScriptAgentInput) -> ScriptPayoffAnalysisResult:
        payoff = str(script_plan.payoff or "").strip()
        payoff_tokens = self._tokens(payoff)
        if not payoff_tokens:
            return ScriptPayoffAnalysisResult(
                payoff_present=False,
                memorability_level="low",
                specificity_level="low",
                generic_payoff_detected=False,
                vague_motivational_detected=False,
                resolves_or_reframes_hook=False,
                resolution_mode="none",
                reason_codes=["PAYOFF_MISSING"],
                evidence={"word_count": 0},
                rationale=["Payoff is missing; memorability cannot be established."],
            )

        payoff_content = set(self._content_tokens(payoff))
        hook_content = set(self._content_tokens(script_plan.hook))
        setup_content = set(self._content_tokens(script_plan.setup))
        topic_content = set(self._content_tokens(data.topic))

        generic_phrases = sorted(phrase for phrase in _GENERIC_PAYOFF_PHRASES if phrase in self._normalized(payoff))
        vague_terms = sorted(payoff_content & _MOTIVATIONAL_VAGUE_TERMS)
        concrete_terms = sorted(token for token in payoff_content if token in _CONCRETE_TERMS or any(char.isdigit() for char in token))
        topic_overlap = sorted(payoff_content & topic_content)
        hook_overlap = sorted(payoff_content & hook_content)
        setup_overlap = sorted(payoff_content & setup_content)
        resolution_terms = sorted(payoff_content & _RESOLUTION_TERMS)
        reframe_terms = sorted(payoff_content & _REFRAME_TERMS)
        duplicate_hook_ratio = self._duplicate_ratio(script_plan.hook, payoff)

        generic_payoff_detected = bool(generic_phrases)
        vague_motivational_detected = bool(vague_terms and not concrete_terms and not topic_overlap)
        specificity_level = self._specificity_level(
            generic=generic_payoff_detected,
            vague=vague_motivational_detected,
            concrete_count=len(concrete_terms),
            topic_overlap_count=len(topic_overlap),
        )
        resolution_mode = self._resolution_mode(
            hook_overlap=hook_overlap,
            setup_overlap=setup_overlap,
            resolution_terms=resolution_terms,
            reframe_terms=reframe_terms,
            duplicate_hook_ratio=duplicate_hook_ratio,
        )
        resolves_or_reframes_hook = resolution_mode in {"resolve", "reframe", "resolve_and_reframe"}
        memorability_level = self._memorability_level(
            generic=generic_payoff_detected,
            vague=vague_motivational_detected,
            duplicate_hook_ratio=duplicate_hook_ratio,
            specificity_level=specificity_level,
            resolves_or_reframes_hook=resolves_or_reframes_hook,
            resolution_terms=resolution_terms,
            reframe_terms=reframe_terms,
        )

        return ScriptPayoffAnalysisResult(
            payoff_present=True,
            memorability_level=memorability_level,
            specificity_level=specificity_level,
            generic_payoff_detected=generic_payoff_detected,
            vague_motivational_detected=vague_motivational_detected,
            resolves_or_reframes_hook=resolves_or_reframes_hook,
            resolution_mode=resolution_mode,
            reason_codes=self._reason_codes(
                memorability_level=memorability_level,
                specificity_level=specificity_level,
                generic=generic_payoff_detected,
                vague=vague_motivational_detected,
                resolves_or_reframes_hook=resolves_or_reframes_hook,
                duplicate_hook_ratio=duplicate_hook_ratio,
            ),
            evidence={
                "word_count": len(payoff_tokens),
                "generic_phrases": generic_phrases,
                "vague_motivational_terms": vague_terms,
                "concrete_terms": concrete_terms,
                "topic_overlap": topic_overlap,
                "hook_overlap": hook_overlap,
                "setup_overlap": setup_overlap,
                "resolution_terms": resolution_terms,
                "reframe_terms": reframe_terms,
                "duplicate_hook_ratio": duplicate_hook_ratio,
            },
            rationale=self._rationale(
                memorability_level=memorability_level,
                specificity_level=specificity_level,
                generic=generic_payoff_detected,
                vague=vague_motivational_detected,
                resolves_or_reframes_hook=resolves_or_reframes_hook,
            ),
        )

    def _specificity_level(
        self,
        *,
        generic: bool,
        vague: bool,
        concrete_count: int,
        topic_overlap_count: int,
    ) -> str:
        if generic or vague:
            return "low"
        if concrete_count >= 2 or topic_overlap_count >= 2:
            return "high"
        if concrete_count >= 1 or topic_overlap_count >= 1:
            return "medium"
        return "low"

    def _resolution_mode(
        self,
        *,
        hook_overlap: list[str],
        setup_overlap: list[str],
        resolution_terms: list[str],
        reframe_terms: list[str],
        duplicate_hook_ratio: float,
    ) -> str:
        if duplicate_hook_ratio >= 0.75:
            return "repeats_hook"
        resolves = bool((hook_overlap or setup_overlap) and resolution_terms)
        reframes = bool((hook_overlap or setup_overlap) and reframe_terms)
        if resolves and reframes:
            return "resolve_and_reframe"
        if resolves:
            return "resolve"
        if reframes:
            return "reframe"
        return "none"

    def _memorability_level(
        self,
        *,
        generic: bool,
        vague: bool,
        duplicate_hook_ratio: float,
        specificity_level: str,
        resolves_or_reframes_hook: bool,
        resolution_terms: list[str],
        reframe_terms: list[str],
    ) -> str:
        if generic or vague or duplicate_hook_ratio >= 0.75:
            return "low"
        if specificity_level == "high" and resolves_or_reframes_hook and (resolution_terms or reframe_terms):
            return "high"
        if specificity_level in {"medium", "high"} or resolves_or_reframes_hook:
            return "medium"
        return "low"

    def _reason_codes(
        self,
        *,
        memorability_level: str,
        specificity_level: str,
        generic: bool,
        vague: bool,
        resolves_or_reframes_hook: bool,
        duplicate_hook_ratio: float,
    ) -> list[str]:
        reason_codes: list[str] = []
        if generic:
            reason_codes.append("GENERIC_PAYOFF_DETECTED")
        else:
            reason_codes.append("GENERIC_PAYOFF_NOT_DETECTED")
        if vague:
            reason_codes.append("VAGUE_MOTIVATIONAL_PAYOFF_DETECTED")
        else:
            reason_codes.append("VAGUE_MOTIVATIONAL_PAYOFF_NOT_DETECTED")
        if resolves_or_reframes_hook:
            reason_codes.append("PAYOFF_RESOLVES_OR_REFRAMES_HOOK")
        else:
            reason_codes.append("PAYOFF_RESOLUTION_WEAK")
        if duplicate_hook_ratio >= 0.75:
            reason_codes.append("PAYOFF_REPEATS_HOOK")
        reason_codes.append(f"PAYOFF_SPECIFICITY_{specificity_level.upper()}")
        reason_codes.append(f"PAYOFF_MEMORABILITY_{memorability_level.upper()}")
        return reason_codes

    def _rationale(
        self,
        *,
        memorability_level: str,
        specificity_level: str,
        generic: bool,
        vague: bool,
        resolves_or_reframes_hook: bool,
    ) -> list[str]:
        rationale = [
            f"Payoff memorability classified as {memorability_level} from emitted payoff text only.",
            "Payoff analysis is audit-only and does not rewrite payoff text or predict performance.",
            f"Payoff specificity classified as {specificity_level}.",
        ]
        if generic:
            rationale.append("Generic payoff phrasing reduces memorability.")
        if vague:
            rationale.append("Vague motivational language is present without concrete support.")
        if resolves_or_reframes_hook:
            rationale.append("Payoff resolves or reframes context from the hook/setup.")
        else:
            rationale.append("Payoff does not clearly resolve or reframe the hook/setup.")
        return rationale

    def _tokens(self, text: str) -> list[str]:
        return _WORD_RE.findall(str(text or "").lower())

    def _content_tokens(self, text: str) -> list[str]:
        return [token for token in self._tokens(text) if token not in _STOPWORDS]

    def _normalized(self, text: str) -> str:
        return " ".join(self._tokens(text))

    def _duplicate_ratio(self, left: str, right: str) -> float:
        left_tokens = set(self._content_tokens(left))
        right_tokens = set(self._content_tokens(right))
        if not left_tokens or not right_tokens:
            return 0.0
        return round(len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens)), 4)
