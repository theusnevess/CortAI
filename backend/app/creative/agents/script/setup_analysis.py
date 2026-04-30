from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from app.creative.agents.script.models import ScriptAgentInput
from app.creative.contracts.creative_pack import ScriptPlan


SCRIPT_SETUP_ANALYSIS_VERSION = "script_setup_analysis_v2_6"

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
_SUPPORTED_CONTEXT_TERMS = {
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
_UNSUPPORTED_CONTEXT_MARKERS = {
    "alien",
    "celebrity",
    "government",
    "guaranteed",
    "president",
    "scientists",
    "viral",
}
_PROGRESSION_TERMS = {
    "after",
    "before",
    "each",
    "every",
    "first",
    "second",
    "then",
    "until",
    "when",
}


@dataclass(frozen=True)
class ScriptSetupAnalysisResult:
    setup_present: bool
    progression_level: str
    connects_hook_to_payoff: bool
    repetition_detected: bool
    unsupported_context_detected: bool
    hook_connection_level: str
    payoff_connection_level: str
    reason_codes: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    rationale: list[str] = field(default_factory=list)
    analysis_version: str = SCRIPT_SETUP_ANALYSIS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "setup_present": self.setup_present,
            "progression_level": self.progression_level,
            "connects_hook_to_payoff": self.connects_hook_to_payoff,
            "repetition_detected": self.repetition_detected,
            "unsupported_context_detected": self.unsupported_context_detected,
            "hook_connection_level": self.hook_connection_level,
            "payoff_connection_level": self.payoff_connection_level,
            "reason_codes": list(self.reason_codes),
            "evidence": dict(self.evidence),
            "rationale": list(self.rationale),
            "analysis_version": self.analysis_version,
        }


class ScriptSetupProgressionAnalyzer:
    """Analyzes emitted setup progression without rewriting script text."""

    def analyze(self, *, script_plan: ScriptPlan, data: ScriptAgentInput) -> ScriptSetupAnalysisResult:
        setup = str(script_plan.setup or "").strip()
        setup_tokens = self._tokens(setup)
        if not setup_tokens:
            return ScriptSetupAnalysisResult(
                setup_present=False,
                progression_level="low",
                connects_hook_to_payoff=False,
                repetition_detected=False,
                unsupported_context_detected=False,
                hook_connection_level="none",
                payoff_connection_level="none",
                reason_codes=["SETUP_MISSING"],
                evidence={"word_count": 0},
                rationale=["Setup is missing; progression cannot be established."],
            )

        hook_tokens = set(self._content_tokens(script_plan.hook))
        setup_content_tokens = set(self._content_tokens(setup))
        payoff_tokens = set(self._content_tokens(script_plan.payoff))
        topic_tokens = set(self._content_tokens(data.topic))

        hook_overlap = sorted(setup_content_tokens & hook_tokens)
        payoff_overlap = sorted(setup_content_tokens & payoff_tokens)
        topic_overlap = sorted(setup_content_tokens & topic_tokens)
        supported_terms = sorted(setup_content_tokens & _SUPPORTED_CONTEXT_TERMS)
        unsupported_terms = sorted(setup_content_tokens & _UNSUPPORTED_CONTEXT_MARKERS)
        progression_terms = sorted(setup_content_tokens & _PROGRESSION_TERMS)
        hook_duplicate_ratio = self._duplicate_ratio(script_plan.hook, setup)
        payoff_duplicate_ratio = self._duplicate_ratio(script_plan.payoff, setup)

        repetition_detected = hook_duplicate_ratio >= 0.75 or payoff_duplicate_ratio >= 0.75
        unsupported_context_detected = bool(
            unsupported_terms
            and not topic_overlap
            and not (setup_content_tokens & hook_tokens)
            and not (setup_content_tokens & payoff_tokens)
        )
        hook_connection_level = self._connection_level(hook_overlap)
        payoff_connection_level = self._connection_level(payoff_overlap)
        connects_hook_to_payoff = self._connects_hook_to_payoff(
            hook_overlap=hook_overlap,
            payoff_overlap=payoff_overlap,
            hook_connection_level=hook_connection_level,
            payoff_connection_level=payoff_connection_level,
        )
        progression_level = self._progression_level(
            connects_hook_to_payoff=connects_hook_to_payoff,
            repetition_detected=repetition_detected,
            unsupported_context_detected=unsupported_context_detected,
            progression_terms=progression_terms,
            hook_connection_level=hook_connection_level,
            payoff_connection_level=payoff_connection_level,
        )
        reason_codes = self._reason_codes(
            connects_hook_to_payoff=connects_hook_to_payoff,
            repetition_detected=repetition_detected,
            unsupported_context_detected=unsupported_context_detected,
            progression_level=progression_level,
            progression_terms=progression_terms,
        )

        return ScriptSetupAnalysisResult(
            setup_present=True,
            progression_level=progression_level,
            connects_hook_to_payoff=connects_hook_to_payoff,
            repetition_detected=repetition_detected,
            unsupported_context_detected=unsupported_context_detected,
            hook_connection_level=hook_connection_level,
            payoff_connection_level=payoff_connection_level,
            reason_codes=reason_codes,
            evidence={
                "word_count": len(setup_tokens),
                "hook_overlap": hook_overlap,
                "payoff_overlap": payoff_overlap,
                "topic_overlap": topic_overlap,
                "supported_context_terms": supported_terms,
                "unsupported_context_terms": unsupported_terms,
                "progression_terms": progression_terms,
                "hook_duplicate_ratio": hook_duplicate_ratio,
                "payoff_duplicate_ratio": payoff_duplicate_ratio,
            },
            rationale=self._rationale(
                progression_level=progression_level,
                connects_hook_to_payoff=connects_hook_to_payoff,
                repetition_detected=repetition_detected,
                unsupported_context_detected=unsupported_context_detected,
            ),
        )

    def _progression_level(
        self,
        *,
        connects_hook_to_payoff: bool,
        repetition_detected: bool,
        unsupported_context_detected: bool,
        progression_terms: list[str],
        hook_connection_level: str,
        payoff_connection_level: str,
    ) -> str:
        if repetition_detected or unsupported_context_detected:
            return "low"
        if (
            connects_hook_to_payoff
            and progression_terms
            and (hook_connection_level == "strong" or payoff_connection_level == "strong")
        ):
            return "high"
        if hook_connection_level != "none" or payoff_connection_level != "none":
            return "medium"
        return "low"

    def _connection_level(self, overlap: list[str]) -> str:
        if len(overlap) >= 2:
            return "strong"
        if len(overlap) == 1:
            return "partial"
        return "none"

    def _connects_hook_to_payoff(
        self,
        *,
        hook_overlap: list[str],
        payoff_overlap: list[str],
        hook_connection_level: str,
        payoff_connection_level: str,
    ) -> bool:
        if hook_connection_level == "none" or payoff_connection_level == "none":
            return False
        if hook_connection_level == "strong" or payoff_connection_level == "strong":
            return True
        return set(hook_overlap) != set(payoff_overlap)

    def _reason_codes(
        self,
        *,
        connects_hook_to_payoff: bool,
        repetition_detected: bool,
        unsupported_context_detected: bool,
        progression_level: str,
        progression_terms: list[str],
    ) -> list[str]:
        reason_codes: list[str] = []
        if connects_hook_to_payoff:
            reason_codes.append("SETUP_CONNECTS_HOOK_TO_PAYOFF")
        else:
            reason_codes.append("SETUP_CONNECTION_INCOMPLETE")
        if repetition_detected:
            reason_codes.append("SETUP_REPETITION_DETECTED")
        else:
            reason_codes.append("SETUP_REPETITION_NOT_DETECTED")
        if unsupported_context_detected:
            reason_codes.append("SETUP_UNSUPPORTED_CONTEXT_DETECTED")
        else:
            reason_codes.append("SETUP_UNSUPPORTED_CONTEXT_NOT_DETECTED")
        if progression_terms:
            reason_codes.append("SETUP_TEMPORAL_PROGRESSION_CUE_PRESENT")
        else:
            reason_codes.append("SETUP_TEMPORAL_PROGRESSION_CUE_WEAK")
        reason_codes.append(f"SETUP_PROGRESSION_{progression_level.upper()}")
        return reason_codes

    def _rationale(
        self,
        *,
        progression_level: str,
        connects_hook_to_payoff: bool,
        repetition_detected: bool,
        unsupported_context_detected: bool,
    ) -> list[str]:
        rationale = [
            f"Setup progression classified as {progression_level} from emitted setup text only.",
            "Setup analysis is audit-only and does not rewrite or optimize setup text.",
        ]
        if connects_hook_to_payoff:
            rationale.append("Setup shares concrete context with both hook and payoff.")
        else:
            rationale.append("Setup does not fully connect hook to payoff through shared concrete context.")
        if repetition_detected:
            rationale.append("Setup repeats a neighboring script block too closely.")
        if unsupported_context_detected:
            rationale.append("Setup introduces configured unsupported context not grounded in topic, hook, or payoff.")
        return rationale

    def _tokens(self, text: str) -> list[str]:
        return _WORD_RE.findall(str(text or "").lower())

    def _content_tokens(self, text: str) -> list[str]:
        return [token for token in self._tokens(text) if token not in _STOPWORDS]

    def _duplicate_ratio(self, left: str, right: str) -> float:
        left_tokens = set(self._content_tokens(left))
        right_tokens = set(self._content_tokens(right))
        if not left_tokens or not right_tokens:
            return 0.0
        return round(len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens)), 4)
