from __future__ import annotations

import re
from dataclasses import dataclass


_WHITESPACE = re.compile(r"\s+")
_DUPLICATE_PUNCTUATION = re.compile(r"([,.;:!?]){2,}")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_COMMA_TRIGGERS = ("but", "because", "while", "when", "although", "though")


@dataclass(frozen=True)
class TtsReadabilityTuner:
    minimum_words_for_comma: int = 7

    def tune(self, text: str) -> str:
        blocks = [self._normalize_block(block) for block in str(text or "").split("\n\n")]
        tuned_blocks = [self._tune_block(block) for block in blocks if block]
        return "\n\n".join(tuned_blocks)

    def _tune_block(self, block: str) -> str:
        sentences = [item.strip() for item in _SENTENCE_SPLIT.split(block) if item.strip()]
        tuned = [self._tune_sentence(sentence) for sentence in sentences]
        return " ".join(tuned)

    def _tune_sentence(self, sentence: str) -> str:
        normalized = self._normalize_block(sentence)
        if not normalized:
            return ""

        base = self._ensure_terminal(normalized)
        if "," in base:
            return base

        words = base[:-1].split()
        if len(words) < self.minimum_words_for_comma:
            return base

        lowered = [word.strip(",.;:!?").lower() for word in words]
        for index, token in enumerate(lowered):
            if token not in _COMMA_TRIGGERS:
                continue
            if index < 4 or index > len(words) - 3:
                continue
            if words[index].endswith(","):
                continue
            words[index] = f"{words[index]},"
            return self._ensure_terminal(" ".join(words))
        return base

    def _normalize_block(self, text: str) -> str:
        normalized = _WHITESPACE.sub(" ", str(text or "").strip())
        normalized = _DUPLICATE_PUNCTUATION.sub(lambda match: match.group(1), normalized)
        normalized = normalized.replace(" ,", ",").replace(" .", ".").replace(" !", "!").replace(" ?", "?")
        return normalized.strip()

    def _ensure_terminal(self, text: str) -> str:
        if not text:
            return ""
        return text if text.endswith((".", "!", "?")) else f"{text}."
