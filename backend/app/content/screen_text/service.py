from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenTextCue:
    text: str
    start: float
    end: float
    style_role: str


@dataclass(frozen=True)
class ScreenTextBlocks:
    hook_text: str
    setup_text: str
    payoff_text: str

    def as_list(self) -> list[str]:
        return [self.hook_text, self.setup_text, self.payoff_text]

    def narration_blocks(self) -> list[str]:
        pieces: list[str] = []
        for item in self.as_list():
            text = item.strip()
            if not text:
                continue
            if text.endswith(("?", "!", ".")):
                pieces.append(text)
            else:
                pieces.append(f"{text}.")
        return pieces

    def narration_text(self) -> str:
        return "\n\n".join(self.narration_blocks())

    def timed_cues(self, timings: list[tuple[float, float]]) -> list[ScreenTextCue]:
        cues: list[ScreenTextCue] = []
        for index, (text, timing) in enumerate(zip(self.as_list(), timings, strict=False)):
            role = "hook" if index == 0 else "payoff" if index == 2 else "setup"
            cues.append(
                ScreenTextCue(
                    text=text,
                    start=timing[0],
                    end=timing[1],
                    style_role=role,
                )
            )
        return cues


class ScreenTextAdapterService:
    def adapt(self, script_text: str) -> ScreenTextBlocks:
        sentences = self._split_sentences(script_text)
        while len(sentences) < 3:
            sentences.append("")

        hook = self._adapt_hook(sentences[0])
        setup = self._adapt_setup(sentences[1])
        payoff = self._adapt_payoff(sentences[2])
        return ScreenTextBlocks(hook_text=hook, setup_text=setup, payoff_text=payoff)

    def _split_sentences(self, script_text: str) -> list[str]:
        normalized = self._normalize_ascii(script_text)
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", normalized) if item.strip()]
        if len(sentences) >= 3:
            middle = " ".join(sentences[1:-1]).strip()
            return [sentences[0], middle or sentences[1], sentences[-1]]
        if len(sentences) == 2:
            return self._expand_two_sentences(sentences[0], sentences[1])
        if len(sentences) == 1:
            return self._expand_single_sentence(sentences[0])
        return sentences[:3]

    def _expand_two_sentences(self, first: str, second: str) -> list[str]:
        lead_parts = self._split_clauses(first)
        tail_parts = self._split_clauses(second)

        if len(lead_parts) >= 2:
            hook = lead_parts[0]
            setup = " ".join(lead_parts[1:]).strip()
            payoff = " ".join(tail_parts).strip() or second
            return [hook, setup, payoff]

        if len(tail_parts) >= 2:
            hook = first
            setup = tail_parts[0]
            payoff = " ".join(tail_parts[1:]).strip()
            return [hook, setup, payoff]

        return [first, second, self._compress_tail(second)]

    def _expand_single_sentence(self, sentence: str) -> list[str]:
        parts = self._split_clauses(sentence)
        if len(parts) >= 3:
            return [parts[0], parts[1], " ".join(parts[2:]).strip()]
        if len(parts) == 2:
            return [parts[0], parts[1], self._compress_tail(parts[1])]
        return [sentence, self._compress_tail(sentence), self._compress_tail(sentence, stronger=True)]

    def _split_clauses(self, sentence: str) -> list[str]:
        raw = re.split(r"\s*(?:\.\.\.|,|;|:\s+|\s+but\s+|\s+then\s+|\s+until\s+)\s*", sentence.strip(), flags=re.IGNORECASE)
        parts = [self._normalize_clause(item) for item in raw if self._normalize_clause(item)]
        return parts

    def _normalize_clause(self, value: str) -> str:
        text = value.strip().strip(",;:. ")
        text = re.sub(r"^(AND|BUT|THEN|UNTIL)\s+", "", text, flags=re.IGNORECASE)
        return text.strip()

    def _compress_tail(self, sentence: str, *, stronger: bool = False) -> str:
        text = self._normalize_clause(sentence)
        words = text.split()
        if len(words) <= 8:
            return text
        keep = 5 if stronger else 8
        return " ".join(words[-keep:])

    def _adapt_hook(self, sentence: str) -> str:
        text = self._upper(sentence)
        text = re.sub(r"^(IN THE DEAD OF NIGHT|AT MIDNIGHT|LATE THAT NIGHT|AFTER MIDNIGHT)[, ]+", "", text)
        if re.search(r"\bLIGHTS?\b", text) and re.search(r"\b(BY THEMSELVES|ON THEIR OWN)\b", text):
            place = self._compress_place(text)
            return f"{place} LIGHTS TURNED ON BY THEMSELVES"
        if re.search(r"\bWROTE\b", text) and re.search(r"\bMIRROR\b", text):
            return "SOMEONE WROTE ON THE MIRROR"
        if re.search(r"\bRED PHONE\b", text) and re.search(r"\b(RINGING|RANG)\b", text):
            return "THE RED PHONE STARTED RINGING AGAIN"
        if re.search(r"\bTIMETABLE\b", text) and re.search(r"\b(KEPT|CHANGING|CHANGED)\b", text):
            return "ONE TIMETABLE KEPT CHANGING AFTER MIDNIGHT"
        return self._compress_for_screen(text, max_words=8)

    def _adapt_setup(self, sentence: str) -> str:
        text = self._upper(sentence)
        if re.search(r"\bWHO\b", text) and re.search(r"\bFLIP\b", text) and re.search(r"\bSWITCH", text):
            return "WHO WAS FLIPPING THE SWITCHES?"
        if re.search(r"\bWHO\b", text) and re.search(r"\bWARNING\b", text):
            return "WHO LEFT THE WARNING?"
        if re.search(r"\bROOM WITH NO EXIT\b", text):
            return "A ROOM WITH NO EXIT"
        return self._compress_for_screen(text, max_words=8, keep_question=text.endswith("?"))

    def _adapt_payoff(self, sentence: str) -> str:
        text = self._upper(sentence)
        if re.search(r"\bFACE\b", text) and re.search(r"\b(STARING|STARED)\b", text) and re.search(r"\bMIRROR\b", text):
            return "A FACE STARED BACK FROM THE MIRROR"
        if re.search(r"\bDOOR\b", text) and re.search(r"\bWOULDN'T OPEN\b", text):
            return "THE DOOR WOULDN'T OPEN"
        if re.search(r"\bVOICE\b", text) and re.search(r"\bEMPTY ROOM\b", text):
            return "A VOICE WHISPERED AN EMPTY ROOM NUMBER"
        if re.search(r"\bDEPARTURE\b", text) and re.search(r"\bSTATION\b", text) and re.search(r"\bEXISTED\b", text):
            return "FINAL DEPARTURE TO A STATION THAT NEVER EXISTED"
        return self._compress_for_screen(text, max_words=8)

    def _compress_place(self, text: str) -> str:
        patterns = [
            (r"\bOLD [A-Z]+ MOTELS?\b", "THE OLD MOTEL"),
            (r"\bOLD [A-Z]+ HOTELS?\b", "THE OLD HOTEL"),
            (r"\bOLD [A-Z]+ HOSPITAL\b", "THE OLD HOSPITAL"),
            (r"\bOLD [A-Z]+ HOUSE\b", "THE OLD HOUSE"),
        ]
        for pattern, replacement in patterns:
            if re.search(pattern, text):
                return replacement
        if "MOTEL" in text or "MOTELS" in text:
            return "THE OLD MOTEL"
        if "HOTEL" in text or "HOTELS" in text:
            return "THE OLD HOTEL"
        if "HOUSE" in text:
            return "THE OLD HOUSE"
        return "THE BUILDING"

    def _normalize_ascii(self, value: str) -> str:
        normalized = (
            value.replace("\u2014", " ")
            .replace("\u2013", " ")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2026", "...")
        )
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"\s*-\s*", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _strip_punctuation(self, text: str, *, keep_question: bool = False) -> str:
        text = text.strip()
        if keep_question and text.endswith("?"):
            return text[:-1].strip(" .,!;:") + "?"
        return text.strip(" .,!;:?")

    def _compress_for_screen(self, text: str, *, max_words: int, keep_question: bool = False) -> str:
        cleaned = self._strip_punctuation(text, keep_question=keep_question)
        words = cleaned.split()
        if len(words) <= max_words:
            return cleaned

        trimmed = list(words)
        while len(trimmed) > max_words:
            removable_index = self._find_removable_index(trimmed)
            if removable_index is None:
                trimmed = self._preserve_tail(trimmed, keep=max_words)
                break
            trimmed.pop(removable_index)

        candidate = " ".join(trimmed)
        if keep_question:
            return candidate.rstrip("?") + "?"
        return candidate

    def _find_removable_index(self, words: list[str]) -> int | None:
        removable = {
            "A", "AN", "THE", "THAT", "THIS", "THESE", "THOSE", "IN", "ON", "AT", "OF",
            "TO", "FOR", "WITH", "BY", "FROM", "AND", "THEN", "JUST", "SOMEONE", "EVERY",
        }
        tail_keep = 2 if len(words) >= 6 else 1
        cutoff = max(1, len(words) - tail_keep)
        for index, word in enumerate(words[:cutoff]):
            if index == 0:
                continue
            if word in removable:
                return index
        return None

    def _preserve_tail(self, words: list[str], *, keep: int) -> list[str]:
        if len(words) <= keep:
            return words
        tail_keep = 2 if keep >= 6 else 1
        tail = words[-tail_keep:]
        head_budget = max(1, keep - tail_keep)
        head = words[:head_budget]
        return head + tail

    def _upper(self, text: str) -> str:
        return self._normalize_ascii(text).upper()
