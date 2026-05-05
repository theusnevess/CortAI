from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from app.creative.agents.script.models import ScriptAgentInput
from app.creative.contracts.creative_pack import ScriptPlan


SCRIPT_HOOK_ANALYSIS_VERSION = "script_hook_analysis_v2_6"

_WORD_RE = re.compile(r"[a-z0-9']+")
_GENERIC_PHRASES = {
    "did you know",
    "this changes everything",
    "this is crazy",
    "watch until the end",
    "what happened next",
    "you need to see this",
    "you won't believe",
    "you wont believe",
}
_TENSION_TERMS = {
    "after",
    "before",
    "dead",
    "failed",
    "flagged",
    "hidden",
    "inside",
    "locked",
    "missing",
    "never",
    "second",
    "sealed",
    "unknown",
    "warning",
}
_CLAIM_TERMS = {
    "best",
    "biggest",
    "confirmed",
    "guaranteed",
    "proven",
    "scientists",
    "secret",
    "truth",
}
_SUPPORTED_CLAIM_EVIDENCE_TERMS = {
    "archive",
    "camera",
    "case",
    "evidence",
    "file",
    "log",
    "record",
    "recorder",
    "timestamp",
    "transcript",
}
_CONCRETE_TERMS = {
    "archive",
    "camera",
    "case",
    "door",
    "evidence",
    "guard",
    "lock",
    "log",
    "mirror",
    "recorder",
    "room",
    "server",
    "timestamp",
    "voice",
    "wall",
    "warning",
    "witness",
}
_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "was",
    "with",
}


@dataclass(frozen=True)
class ScriptHookAnalysisResult:
    hook_present: bool
    strength_level: str
    generic_hook_detected: bool
    unsupported_claim_detected: bool
    tension_detected: bool
    specificity_level: str
    reason_codes: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    rationale: list[str] = field(default_factory=list)
    analysis_version: str = SCRIPT_HOOK_ANALYSIS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "hook_present": self.hook_present,
            "strength_level": self.strength_level,
            "generic_hook_detected": self.generic_hook_detected,
            "unsupported_claim_detected": self.unsupported_claim_detected,
            "tension_detected": self.tension_detected,
            "specificity_level": self.specificity_level,
            "reason_codes": list(self.reason_codes),
            "evidence": dict(self.evidence),
            "rationale": list(self.rationale),
            "analysis_version": self.analysis_version,
        }


class ScriptHookStrengthAnalyzer:
    """Analyzes emitted hook strength without rewriting or optimizing the hook."""

    def analyze(self, *, script_plan: ScriptPlan, data: ScriptAgentInput) -> ScriptHookAnalysisResult:
        hook = str(script_plan.hook or "").strip()
        tokens = self._tokens(hook)
        content_tokens = self._content_tokens(hook)
        hook_present = bool(tokens)

        if not hook_present:
            return ScriptHookAnalysisResult(
                hook_present=False,
                strength_level="low",
                generic_hook_detected=False,
                unsupported_claim_detected=False,
                tension_detected=False,
                specificity_level="low",
                reason_codes=["HOOK_MISSING"],
                evidence={"word_count": 0},
                rationale=["Hook is missing; Script cannot audit hook strength beyond absence."],
            )

        generic_phrases = sorted(phrase for phrase in _GENERIC_PHRASES if phrase in self._normalized(hook))
        topic_overlap = sorted(set(content_tokens) & set(self._content_tokens(data.topic)))
        concrete_terms = sorted(
            token for token in set(content_tokens) if token in _CONCRETE_TERMS or any(char.isdigit() for char in token)
        )
        tension_terms = sorted(set(content_tokens) & _TENSION_TERMS)
        claim_terms = sorted(set(content_tokens) & _CLAIM_TERMS)
        supported_claim_terms = sorted(set(content_tokens) & _SUPPORTED_CLAIM_EVIDENCE_TERMS)

        generic_hook_detected = bool(generic_phrases)
        tension_detected = bool(tension_terms)
        unsupported_claim_detected = bool(claim_terms and not supported_claim_terms and not topic_overlap)

        specificity_level = self._specificity_level(
            generic=generic_hook_detected,
            concrete_count=len(concrete_terms),
            topic_overlap_count=len(topic_overlap),
        )
        strength_level = self._strength_level(
            hook_present=hook_present,
            generic=generic_hook_detected,
            unsupported_claim=unsupported_claim_detected,
            tension=tension_detected,
            specificity_level=specificity_level,
            word_count=len(tokens),
        )

        reason_codes = self._reason_codes(
            generic=generic_hook_detected,
            unsupported_claim=unsupported_claim_detected,
            tension=tension_detected,
            specificity_level=specificity_level,
            word_count=len(tokens),
        )
        rationale = self._rationale(
            strength_level=strength_level,
            generic=generic_hook_detected,
            unsupported_claim=unsupported_claim_detected,
            tension=tension_detected,
            specificity_level=specificity_level,
        )

        return ScriptHookAnalysisResult(
            hook_present=True,
            strength_level=strength_level,
            generic_hook_detected=generic_hook_detected,
            unsupported_claim_detected=unsupported_claim_detected,
            tension_detected=tension_detected,
            specificity_level=specificity_level,
            reason_codes=reason_codes,
            evidence={
                "word_count": len(tokens),
                "topic_overlap": topic_overlap,
                "concrete_terms": concrete_terms,
                "tension_terms": tension_terms,
                "generic_phrases": generic_phrases,
                "claim_terms": claim_terms,
                "supported_claim_evidence_terms": supported_claim_terms,
            },
            rationale=rationale,
        )

    def _specificity_level(self, *, generic: bool, concrete_count: int, topic_overlap_count: int) -> str:
        if generic:
            return "low"
        if concrete_count >= 2 or topic_overlap_count >= 2:
            return "high"
        if concrete_count >= 1 or topic_overlap_count >= 1:
            return "medium"
        return "low"

    def _strength_level(
        self,
        *,
        hook_present: bool,
        generic: bool,
        unsupported_claim: bool,
        tension: bool,
        specificity_level: str,
        word_count: int,
    ) -> str:
        if not hook_present or generic or unsupported_claim:
            return "low"
        length_ok = 3 <= word_count <= 14
        if tension and specificity_level == "high" and length_ok:
            return "high"
        if tension or specificity_level in {"medium", "high"}:
            return "medium"
        return "low"

    def _reason_codes(
        self,
        *,
        generic: bool,
        unsupported_claim: bool,
        tension: bool,
        specificity_level: str,
        word_count: int,
    ) -> list[str]:
        reason_codes: list[str] = []
        if generic:
            reason_codes.append("GENERIC_HOOK_DETECTED")
        if unsupported_claim:
            reason_codes.append("UNSUPPORTED_CLAIM_DETECTED")
        if tension:
            reason_codes.append("HOOK_TENSION_PRESENT")
        else:
            reason_codes.append("HOOK_TENSION_WEAK")
        if specificity_level == "high":
            reason_codes.append("HOOK_SPECIFICITY_HIGH")
        elif specificity_level == "medium":
            reason_codes.append("HOOK_SPECIFICITY_MEDIUM")
        else:
            reason_codes.append("HOOK_SPECIFICITY_LOW")
        if word_count < 3:
            reason_codes.append("HOOK_TOO_SHORT")
        elif word_count > 14:
            reason_codes.append("HOOK_LONG")
        else:
            reason_codes.append("HOOK_LENGTH_BOUNDED")
        return reason_codes

    def _rationale(
        self,
        *,
        strength_level: str,
        generic: bool,
        unsupported_claim: bool,
        tension: bool,
        specificity_level: str,
    ) -> list[str]:
        rationale = [
            f"Hook strength classified as {strength_level} from emitted hook text only.",
            "Hook analysis is audit-only and does not rewrite or optimize the hook.",
        ]
        if generic:
            rationale.append("Generic hook phrasing reduces hook strength.")
        if unsupported_claim:
            rationale.append("Unsupported claim wording is present without direct topic or evidence support.")
        if tension:
            rationale.append("Hook contains a configured tension cue.")
        else:
            rationale.append("Hook lacks a configured tension cue.")
        rationale.append(f"Hook specificity classified as {specificity_level}.")
        return rationale

    def _tokens(self, text: str) -> list[str]:
        return _WORD_RE.findall(str(text or "").lower())

    def _content_tokens(self, text: str) -> list[str]:
        return [token for token in self._tokens(text) if token not in _STOPWORDS]

    def _normalized(self, text: str) -> str:
        return " ".join(self._tokens(text))
