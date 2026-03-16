from __future__ import annotations

import os
import re
from dataclasses import dataclass

import httpx


class ScriptGenerationError(RuntimeError):
    """Raised when local script generation fails."""


GENERIC_RE = re.compile(r"^(Automated|Manual) pilot content for ", re.IGNORECASE)


@dataclass
class LocalScriptGeneratorService:
    base_url: str = os.getenv("CORTAI_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model: str = os.getenv("CORTAI_OLLAMA_MODEL", "qwen2.5:7b")
    timeout_s: float = 60.0

    def should_generate(self, script_text: str) -> bool:
        text = str(script_text or "").strip()
        return not text or bool(GENERIC_RE.match(text))

    def generate(
        self,
        *,
        theme: str,
        angle: str | None = None,
        hook_hint: str | None = None,
        account_id: str | None = None,
    ) -> str:
        prompt = self._build_prompt(
            theme=theme.strip() or "dark mystery",
            angle=(angle or "").strip(),
            hook_hint=(hook_hint or "").strip(),
            account_id=(account_id or "").strip(),
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(f"{self.base_url.rstrip('/')}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ScriptGenerationError(f"OLLAMA_GENERATION_FAILED: {exc}") from exc

        text = str(data.get("response") or "").strip()
        normalized = self._normalize_script(text)
        if not normalized:
            raise ScriptGenerationError("OLLAMA_EMPTY_SCRIPT")
        return normalized

    def _build_prompt(self, *, theme: str, angle: str, hook_hint: str, account_id: str) -> str:
        return (
            "Write a short TikTok dark-story script in English.\n"
            "Constraints:\n"
            "- Exactly 3 sentences.\n"
            "- 28 to 42 words total.\n"
            "- Strong curiosity-gap hook in sentence 1.\n"
            "- Clear escalation in sentence 2.\n"
            "- Unsettling payoff in sentence 3.\n"
            "- No hashtags.\n"
            "- No emojis.\n"
            "- No labels like Hook/Setup/Payoff.\n"
            "- Make it sound spoken, not written.\n"
            "- Avoid generic filler.\n"
            f"Theme: {theme}\n"
            f"Angle: {angle or 'unexplained event'}\n"
            f"Hook hint: {hook_hint or 'a detail that should not exist'}\n"
            f"Audience account: {account_id or 'general'}\n"
            "Return only the final script."
        )

    def _normalize_script(self, text: str) -> str:
        value = text.strip().replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
        value = re.sub(r"\s+", " ", value)
        lines = [line.strip(" -\t") for line in value.splitlines() if line.strip()]
        value = " ".join(lines)
        value = re.sub(r"\b(hook|setup|payoff|script)\s*:\s*", "", value, flags=re.IGNORECASE)
        value = self._strip_stage_directions(value)
        value = self._normalize_quotes(value)
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", value) if item.strip()]
        sentences = [self._ensure_terminal_punctuation(item) for item in sentences if item.strip()]
        if len(sentences) > 3:
            sentences = sentences[:3]
        sentences = [self._sanitize_sentence(item) for item in sentences]
        sentences = [item for item in sentences if item]
        return " ".join(sentences)

    def _strip_stage_directions(self, value: str) -> str:
        cleaned = re.sub(r"\[[^\]]*\]", "", value)
        cleaned = re.sub(r"\([^\)]*\)", "", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    def _normalize_quotes(self, value: str) -> str:
        if value.count('"') % 2 != 0:
            value = value.replace('"', "")
        if value.count("'") % 2 != 0:
            contractions = {"don't", "can't", "won't", "who's", "it's", "that's", "there's", "what's", "i'm"}
            lowered = value.lower()
            if not any(token in lowered for token in contractions):
                value = value.replace("'", "")
        return value.strip()

    def _ensure_terminal_punctuation(self, sentence: str) -> str:
        trimmed = sentence.strip().strip('"').strip("'").strip()
        if not trimmed:
            return ""
        if trimmed[-1] not in ".!?":
            trimmed = f"{trimmed}."
        return trimmed

    def _sanitize_sentence(self, sentence: str) -> str:
        cleaned = re.sub(r"\s+", " ", sentence).strip()
        cleaned = cleaned.strip('"').strip("'").strip()
        if not cleaned:
            return ""
        if cleaned.endswith(":"):
            cleaned = cleaned[:-1].strip()
        if cleaned and cleaned[-1] not in ".!?":
            cleaned = f"{cleaned}."
        return cleaned
