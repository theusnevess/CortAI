from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from app.creative.agents.script.models import ScriptAgentInput
from app.creative.contracts.creative_pack import ScriptPlan


SCRIPT_DIVERSITY_ANALYSIS_VERSION = "script_diversity_analysis_v2_6"

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
_GENERIC_PHRASES = {
    "and everything changed",
    "did you know",
    "it was all a lie",
    "nobody expected it",
    "the truth was revealed",
    "this changes everything",
    "this is crazy",
    "watch until the end",
    "what happened next",
    "you need to see this",
    "you won't believe",
    "you wont believe",
}
_GENERIC_CTA_PHRASES = {
    "comment below",
    "follow for more",
    "like and subscribe",
    "save this post",
    "share this video",
    "tap follow",
}
_CLICHE_STRUCTURE_PATTERNS = {
    "question_bait": ("did", "you", "know"),
    "truth_reveal": ("truth", "revealed"),
    "watch_to_end": ("watch", "end"),
    "everything_changed": ("everything", "changed"),
}


@dataclass(frozen=True)
class ScriptDiversityAnalysisResult:
    cliche_risk_level: str
    repetition_risk_level: str
    generic_phrase_detected: bool
    structural_repetition_detected: bool
    generic_cta_detected: bool
    detected_patterns: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    rationale: list[str] = field(default_factory=list)
    analysis_version: str = SCRIPT_DIVERSITY_ANALYSIS_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "cliche_risk_level": self.cliche_risk_level,
            "repetition_risk_level": self.repetition_risk_level,
            "generic_phrase_detected": self.generic_phrase_detected,
            "structural_repetition_detected": self.structural_repetition_detected,
            "generic_cta_detected": self.generic_cta_detected,
            "detected_patterns": list(self.detected_patterns),
            "reason_codes": list(self.reason_codes),
            "evidence": dict(self.evidence),
            "rationale": list(self.rationale),
            "analysis_version": self.analysis_version,
        }


class ScriptDiversityAnalyzer:
    """Detects local cliche and repetition patterns without external memory or randomness."""

    def analyze(self, *, script_plan: ScriptPlan, data: ScriptAgentInput) -> ScriptDiversityAnalysisResult:
        del data
        blocks = {
            "hook": str(script_plan.hook or ""),
            "setup": str(script_plan.setup or ""),
            "payoff": str(script_plan.payoff or ""),
        }
        text = " ".join(blocks.values())
        normalized = self._normalized(text)
        content_tokens = self._content_tokens(text)

        generic_phrases = sorted(phrase for phrase in _GENERIC_PHRASES if phrase in normalized)
        generic_cta_phrases = sorted(phrase for phrase in _GENERIC_CTA_PHRASES if phrase in normalized)
        duplicate_blocks = self._duplicate_blocks(blocks)
        repeated_tokens = sorted({token for token in content_tokens if content_tokens.count(token) >= 3})
        repeated_openings = self._repeated_openings(blocks)
        cliche_structures = self._cliche_structures(content_tokens)

        generic_phrase_detected = bool(generic_phrases)
        generic_cta_detected = bool(generic_cta_phrases)
        structural_repetition_detected = bool(duplicate_blocks or repeated_openings or repeated_tokens)
        detected_patterns = sorted(
            set(generic_phrases + generic_cta_phrases + duplicate_blocks + repeated_openings + cliche_structures)
        )
        cliche_risk_level = self._cliche_risk_level(
            generic_phrase_detected=generic_phrase_detected,
            generic_cta_detected=generic_cta_detected,
            cliche_structure_count=len(cliche_structures),
        )
        repetition_risk_level = self._repetition_risk_level(
            duplicate_count=len(duplicate_blocks),
            repeated_opening_count=len(repeated_openings),
            repeated_token_count=len(repeated_tokens),
        )

        return ScriptDiversityAnalysisResult(
            cliche_risk_level=cliche_risk_level,
            repetition_risk_level=repetition_risk_level,
            generic_phrase_detected=generic_phrase_detected,
            structural_repetition_detected=structural_repetition_detected,
            generic_cta_detected=generic_cta_detected,
            detected_patterns=detected_patterns,
            reason_codes=self._reason_codes(
                cliche_risk_level=cliche_risk_level,
                repetition_risk_level=repetition_risk_level,
                generic_phrase_detected=generic_phrase_detected,
                generic_cta_detected=generic_cta_detected,
                structural_repetition_detected=structural_repetition_detected,
            ),
            evidence={
                "generic_phrases": generic_phrases,
                "generic_cta_phrases": generic_cta_phrases,
                "duplicate_blocks": duplicate_blocks,
                "repeated_openings": repeated_openings,
                "repeated_tokens": repeated_tokens,
                "cliche_structures": cliche_structures,
                "analysis_scope": "current_script_only",
            },
            rationale=self._rationale(
                cliche_risk_level=cliche_risk_level,
                repetition_risk_level=repetition_risk_level,
                generic_phrase_detected=generic_phrase_detected,
                generic_cta_detected=generic_cta_detected,
                structural_repetition_detected=structural_repetition_detected,
            ),
        )

    def _cliche_risk_level(
        self,
        *,
        generic_phrase_detected: bool,
        generic_cta_detected: bool,
        cliche_structure_count: int,
    ) -> str:
        if generic_phrase_detected or generic_cta_detected:
            return "high"
        if cliche_structure_count > 0:
            return "medium"
        return "low"

    def _repetition_risk_level(
        self,
        *,
        duplicate_count: int,
        repeated_opening_count: int,
        repeated_token_count: int,
    ) -> str:
        if duplicate_count > 0 or repeated_opening_count > 0:
            return "high"
        if repeated_token_count > 0:
            return "medium"
        return "low"

    def _reason_codes(
        self,
        *,
        cliche_risk_level: str,
        repetition_risk_level: str,
        generic_phrase_detected: bool,
        generic_cta_detected: bool,
        structural_repetition_detected: bool,
    ) -> list[str]:
        reason_codes = [
            f"CLICHE_RISK_{cliche_risk_level.upper()}",
            f"REPETITION_RISK_{repetition_risk_level.upper()}",
        ]
        reason_codes.append("GENERIC_PHRASE_DETECTED" if generic_phrase_detected else "GENERIC_PHRASE_NOT_DETECTED")
        reason_codes.append("GENERIC_CTA_DETECTED" if generic_cta_detected else "GENERIC_CTA_NOT_DETECTED")
        reason_codes.append(
            "STRUCTURAL_REPETITION_DETECTED"
            if structural_repetition_detected
            else "STRUCTURAL_REPETITION_NOT_DETECTED"
        )
        reason_codes.append("NO_EXTERNAL_MEMORY_USED")
        reason_codes.append("NO_RANDOMNESS_USED")
        return reason_codes

    def _rationale(
        self,
        *,
        cliche_risk_level: str,
        repetition_risk_level: str,
        generic_phrase_detected: bool,
        generic_cta_detected: bool,
        structural_repetition_detected: bool,
    ) -> list[str]:
        rationale = [
            "Diversity analysis is limited to the emitted script; no external memory is invented.",
            "Analysis is audit-only and does not rewrite script text.",
            f"Cliche risk classified as {cliche_risk_level}.",
            f"Repetition risk classified as {repetition_risk_level}.",
        ]
        if generic_phrase_detected:
            rationale.append("Generic narrative phrase detected.")
        if generic_cta_detected:
            rationale.append("Generic CTA phrase detected inside script text.")
        if structural_repetition_detected:
            rationale.append("Structural repetition detected within current hook/setup/payoff.")
        return rationale

    def _duplicate_blocks(self, blocks: dict[str, str]) -> list[str]:
        normalized = {name: self._normalized(value) for name, value in blocks.items()}
        duplicates: list[str] = []
        names = list(normalized)
        for index, name in enumerate(names):
            for other in names[index + 1:]:
                if normalized[name] and normalized[name] == normalized[other]:
                    duplicates.append(f"duplicate_{name}_{other}")
        return sorted(duplicates)

    def _repeated_openings(self, blocks: dict[str, str]) -> list[str]:
        openings: dict[str, int] = {}
        for value in blocks.values():
            tokens = self._content_tokens(value)
            if not tokens:
                continue
            opening = " ".join(tokens[:2])
            openings[opening] = openings.get(opening, 0) + 1
        return sorted(f"repeated_opening:{opening}" for opening, count in openings.items() if count >= 2)

    def _cliche_structures(self, content_tokens: list[str]) -> list[str]:
        token_set = set(content_tokens)
        patterns = []
        for pattern_name, required_tokens in _CLICHE_STRUCTURE_PATTERNS.items():
            if set(required_tokens).issubset(token_set):
                patterns.append(f"cliche_structure:{pattern_name}")
        return sorted(patterns)

    def _tokens(self, text: str) -> list[str]:
        return _WORD_RE.findall(str(text or "").lower())

    def _content_tokens(self, text: str) -> list[str]:
        return [token for token in self._tokens(text) if token not in _STOPWORDS]

    def _normalized(self, text: str) -> str:
        return " ".join(self._tokens(text))
