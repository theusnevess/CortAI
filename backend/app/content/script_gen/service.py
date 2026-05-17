from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable

import httpx

from app.content.script_gen.models import (
    ScriptGenerationContext,
    ScriptGenerationRequest,
    ScriptGenerationResponse,
    StructuredScriptPayload,
)
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import ExperimentPlan, ScriptPlan


class ScriptGenerationError(RuntimeError):
    """Raised when structured script generation fails."""


SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED = False
SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED = False
SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED = False
SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED = False
SAFE_PRE_CROSSING_RUNTIME_WIRING_AUTHORIZED = False
LOCAL_STRUCTURED_PROVIDER = "local_structured"
LOCAL_STRUCTURED_MODEL = "deterministic_narrative_rules_v1"


def _raise_safe_pre_crossing_block(reason: str) -> None:
    raise ScriptGenerationError(reason)


def _ensure_external_call_authorized() -> None:
    if not SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED:
        _raise_safe_pre_crossing_block("CORTAI_EXTERNAL_BOUNDARY_BLOCKED_SAFE_PRE_CROSSING")


def _ensure_credential_access_authorized() -> None:
    if not SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED:
        _raise_safe_pre_crossing_block("CORTAI_CREDENTIAL_ACCESS_BLOCKED_SAFE_PRE_CROSSING")


def _ensure_request_transformation_authorized() -> None:
    if not SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED:
        _raise_safe_pre_crossing_block("CORTAI_REQUEST_TRANSFORMATION_BLOCKED_SAFE_PRE_CROSSING")


def _ensure_transport_payload_authorized() -> None:
    if not SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED:
        _raise_safe_pre_crossing_block("CORTAI_TRANSPORT_PAYLOAD_BLOCKED_SAFE_PRE_CROSSING")


def _ensure_runtime_wiring_authorized() -> None:
    if not SAFE_PRE_CROSSING_RUNTIME_WIRING_AUTHORIZED:
        _raise_safe_pre_crossing_block("CORTAI_RUNTIME_WIRING_BLOCKED_SAFE_PRE_CROSSING")


GENERIC_RE = re.compile(r"^(Automated|Manual) pilot content for ", re.IGNORECASE)
ANTI_CLICHE_PHRASES = (
    "NOBODY COULD EXPLAIN IT",
    "THEN IT MOVED ON ITS OWN",
    "SOMETHING WAS WRONG",
    "NOBODY EVER FOUND OUT WHY",
    "NO ONE EVER KNEW WHY",
)
WEAK_PAYOFF_TERMS = (
    "EXPLAIN",
    "EXPLANATION",
    "UNEXPLAINED",
    "MYSTERIOUS",
    "UNKNOWN",
    "SOMEHOW",
)
WEAK_PAYOFF_PHRASES = (
    "EMPTY ROOM",
    "EMPTY HALLWAY",
    "SOMETHING ANSWERED",
    "SOMETHING WAS WAITING",
    "SOMEONE WAS THERE",
    "NOBODY UNDERSTOOD WHY",
    "NO ONE UNDERSTOOD WHY",
    "NOBODY EVER KNEW WHY",
    "NO ONE EVER KNEW WHY",
    "IT WAS NEVER EXPLAINED",
    "THE ROOM WAS WRONG",
    "BREATHING BEHIND THE DOOR",
    "POINTING INTO THE WALL",
)
CONCRETE_PAYOFF_HINTS = (
    "ROOM",
    "DOOR",
    "LOCK",
    "KEY",
    "TAPE",
    "FILE",
    "ARCHIVE",
    "PANEL",
    "WARNING",
    "INTERCOM",
    "ELEVATOR",
    "BADGE",
    "BODY",
    "VOICE",
    "NAME",
    "NUMBER",
    "TIMESTAMP",
    "FLOORPLAN",
    "REPORT",
    "TRANSCRIPT",
    "STATION",
    "WING",
    "CORRIDOR",
    "HATCH",
    "GATE",
)
GENERIC_ABSTRACT_PAYOFF_HINTS = (
    "PRESENCE",
    "SHADOW",
    "DARK",
    "VOID",
    "SILENCE",
    "WHISPER",
    "FIGURE",
    "THING",
    "SOMETHING",
    "SOMEONE",
    "FEELING",
)
SPECIFICITY_PAYOFF_HINTS = (
    "ROOM 312",
    "FLOORPLAN",
    "NON-EXISTENT",
    "NONEXISTENT",
    "REMOVED FROM THE MAP",
    "REMOVED FROM THE FLOORPLAN",
    "SEALED SINCE",
    "TIMESTAMP",
    "FILE",
    "TRANSCRIPT",
    "REPORT",
    "EXIT SIGN",
    "WARNING PANEL",
    "ROOM NUMBER",
    "LISTED AS",
)
PAYOFF_STOPWORDS = {
    "A", "AN", "THE", "AND", "OR", "BUT", "FROM", "INSIDE", "OUTSIDE", "AFTER", "BEFORE",
    "THROUGH", "UNDER", "OVER", "WITH", "WITHOUT", "THIS", "THAT", "THEN", "THEY", "THEIR",
    "CALLER", "VOICE", "FINAL", "LAST", "WHISPER", "WHISPERED", "EMPTY", "ROOM",
}
MEDIATOR_PREFIXES = (
    "A WITNESS",
    "POLICE",
    "A REPORT",
    "A RECOVERED TAPE",
    "FILES SHOW",
    "RECORDS INDICATE",
    "ARCHIVES",
    "AN OFFICIAL MEMO",
    "CASE NOTES",
)
NON_ANOMALY_LEADS = (
    "HISTORIANS MISSED",
    "LOCALS STILL TALK ABOUT",
)
INFERENTIAL_KEYWORDS = (
    "TAPE",
    "LOG",
    "RECORD",
    "FILE",
    "ARCHIVE",
    "TRANSCRIPT",
    "REPORT",
    "DATABASE",
    "STATEMENT",
    "MEMO",
)
EXPERIENTIAL_TOPIC_KEYWORDS = (
    "CAMERA",
    "BLACKOUT",
    "WARNING",
    "VOICE",
    "WHISPER",
    "ELEVATOR",
    "LOCKER RECORDER",
    "FIRE EXIT",
    "TUNNEL",
    "INTERCOM",
    "BUNKER MAP",
    "CORRIDOR BLUEPRINT",
    "PLATFORM TIMETABLE",
    "HOSPITAL WING",
    "ROOM",
)
NARRATIVE_MODES: tuple[str, ...] = (
    "witness_report",
    "recovered_recording",
    "official_warning",
    "contradiction_timeline",
    "urban_legend_fragment",
    "hidden_truth",
    "procedural_anomaly",
)


@dataclass
class LocalScriptGeneratorService:
    base_url: str = os.getenv("CORTAI_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model: str = os.getenv("CORTAI_OLLAMA_MODEL", "qwen2.5:7b")
    groq_model: str = os.getenv("CORTAI_GROQ_MODEL", "llama-3.3-70b-versatile")
    timeout_s: float = 60.0
    http_client_factory: Callable[..., httpx.Client] = httpx.Client

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
        del hook_hint
        request = ScriptGenerationRequest(
            context=ScriptGenerationContext(
                account_id=(account_id or "").strip() or "general",
                niche=theme.strip() or "dark mystery",
                topic=(angle or "").strip() or "unexplained event",
            )
        )
        response = self.generate_structured(request)
        return response.script_plan.narration_text()

    def generate_structured(self, request: ScriptGenerationRequest) -> ScriptGenerationResponse:
        prompt = self._build_prompt(request)
        errors: list[str] = []
        preferred = (request.preferred_provider or "").strip().lower()
        providers = self._provider_order(preferred)
        if not providers:
            errors.append("provider_execution_blocked_safe_pre_crossing")
            try:
                return self._generate_with_local_structured(
                    request=request,
                    prompt=prompt,
                    provider_attempt_trace=errors,
                )
            except ScriptGenerationError as exc:
                errors.append(f"{LOCAL_STRUCTURED_PROVIDER}:{exc}")

        for provider in providers:
            attempts = 2 if provider == "groq" else 1
            for attempt in range(1, attempts + 1):
                try:
                    if provider == "groq":
                        return self._generate_with_groq(
                            prompt=prompt,
                            request=request,
                            provider_attempt_trace=errors,
                        )
                    if provider == "ollama":
                        return self._generate_with_ollama(
                            prompt=prompt,
                            request=request,
                            provider_attempt_trace=errors,
                        )
                except ScriptGenerationError as exc:
                    errors.append(f"{provider}[{attempt}/{attempts}]:{exc}")
                    if provider == "groq" and attempt < attempts:
                        time.sleep(0.8 * attempt)
                    if attempt >= attempts:
                        break

        return self._deterministic_fallback(request=request, prompt=prompt, errors=errors)

    def _generate_with_local_structured(
        self,
        *,
        request: ScriptGenerationRequest,
        prompt: str,
        provider_attempt_trace: list[str] | tuple[str, ...] = (),
    ) -> ScriptGenerationResponse:
        context = request.context
        mode = self._select_narrative_mode(context)
        payload = self._local_structured_payload(context=context, mode=mode)
        payload = self._finalize_payload(payload, context=context)
        self._validate_payload(payload)
        script_plan = ScriptPlan(
            hook=payload.hook,
            setup=payload.setup,
            payoff=payload.payoff,
            generation_mode=LOCAL_STRUCTURED_PROVIDER,
        )
        return ScriptGenerationResponse(
            script_plan=script_plan,
            payload=payload,
            provider_used=LOCAL_STRUCTURED_PROVIDER,
            model_used=LOCAL_STRUCTURED_MODEL,
            prompt_used=prompt,
            raw_output=json.dumps(payload.to_dict(), ensure_ascii=True, sort_keys=True),
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            provider_attempt_trace=tuple(provider_attempt_trace),
        )

    def _provider_order(self, preferred: str) -> list[str]:
        groq_key = ""
        order: list[str] = []
        groq_allowed = SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED and SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED
        ollama_allowed = SAFE_PRE_CROSSING_RUNTIME_WIRING_AUTHORIZED and SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED
        if groq_allowed:
            groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if preferred == "groq" and groq_allowed and groq_key:
            order.append("groq")
        if preferred == "ollama" and ollama_allowed:
            order.append("ollama")
        if groq_allowed and groq_key and "groq" not in order:
            order.append("groq")
        if ollama_allowed and "ollama" not in order:
            order.append("ollama")
        return order

    def _generate_with_groq(
        self,
        *,
        prompt: str,
        request: ScriptGenerationRequest,
        provider_attempt_trace: list[str] | tuple[str, ...] = (),
    ) -> ScriptGenerationResponse:
        _ensure_external_call_authorized()
        _ensure_credential_access_authorized()
        _ensure_request_transformation_authorized()
        _ensure_transport_payload_authorized()
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ScriptGenerationError("GROQ_API_KEY_MISSING")

        payload = {
            "model": self.groq_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.45,
            "top_p": 0.85,
            "response_format": {
                "type": "json_object",
            },
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        url = "https://api.groq.com/openai/v1/chat/completions"
        try:
            with self.http_client_factory(timeout=self.timeout_s) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ScriptGenerationError(f"GROQ_GENERATION_FAILED: {exc}") from exc

        raw = self._extract_groq_text(data)
        return self._build_response(
            request=request,
            prompt=prompt,
            raw_output=raw,
            provider="groq",
            model=self.groq_model,
            provider_attempt_trace=provider_attempt_trace,
        )

    def _generate_with_ollama(
        self,
        *,
        prompt: str,
        request: ScriptGenerationRequest,
        provider_attempt_trace: list[str] | tuple[str, ...] = (),
    ) -> ScriptGenerationResponse:
        _ensure_runtime_wiring_authorized()
        _ensure_request_transformation_authorized()
        _ensure_transport_payload_authorized()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.15,
                "seed": self._ollama_seed(request=request),
            },
        }
        try:
            with self.http_client_factory(timeout=self.timeout_s) as client:
                response = client.post(f"{self.base_url.rstrip('/')}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ScriptGenerationError(f"OLLAMA_GENERATION_FAILED: {exc}") from exc

        raw = str(data.get("response") or "").strip()
        return self._build_response(
            request=request,
            prompt=prompt,
            raw_output=raw,
            provider="ollama",
            model=self.model,
            provider_attempt_trace=provider_attempt_trace,
        )

    def _ollama_seed(self, *, request: ScriptGenerationRequest) -> int:
        context = request.context
        material = "|".join(
            [
                str(context.account_id or "").strip(),
                str(context.niche or "").strip(),
                str(context.topic or "").strip(),
                str(context.account_health_status or "").strip(),
                str(context.experiment_plan.variant_id if context.experiment_plan else "").strip(),
                str((context.experiment_plan.variant_params if context.experiment_plan else {}).get("narrative_mode") or "").strip(),
            ]
        ).encode("utf-8")
        return int(sha256(material).hexdigest()[:8], 16)

    def _build_response(
        self,
        *,
        request: ScriptGenerationRequest,
        prompt: str,
        raw_output: str,
        provider: str,
        model: str,
        provider_attempt_trace: list[str] | tuple[str, ...] = (),
    ) -> ScriptGenerationResponse:
        payload = self._parse_structured_response(raw_output, request=request)
        payload = self._finalize_payload(payload, context=request.context)
        self._validate_payload(payload)
        script_plan = ScriptPlan(
            hook=payload.hook,
            setup=payload.setup,
            payoff=payload.payoff,
            generation_mode=f"{provider}_structured",
        )
        return ScriptGenerationResponse(
            script_plan=script_plan,
            payload=payload,
            provider_used=provider,
            model_used=model,
            prompt_used=prompt,
            raw_output=raw_output,
            fallback=FallbackDecision(used=False, mode=FallbackMode.NONE.value, reason=""),
            provider_attempt_trace=tuple(provider_attempt_trace),
        )

    def _build_prompt(self, request: ScriptGenerationRequest) -> str:
        context = request.context
        narrative_mode = self._select_narrative_mode(context)
        strategy = context.strategy_profile
        trend = context.trend_profile
        learning = context.learning_insights
        experiment = context.experiment_plan or ExperimentPlan()

        anti_cliche = "\n".join(f"- {item.lower()}" for item in ANTI_CLICHE_PHRASES)
        dominant_hooks = ", ".join(trend.dominant_hooks) if trend and trend.dominant_hooks else "question"
        recommendations = ", ".join(learning.recommendations[:4]) if learning and learning.recommendations else "none"
        experiment_variant = experiment.variant_id if experiment else "A"
        experiment_payload = json.dumps(experiment.variant_params if experiment else {}, ensure_ascii=True, sort_keys=True)
        blocked_structures = ", ".join(self._blocked_payoff_structures(context)) or "none"
        blocked_visual = ", ".join(self._blocked_visual_categories(context)) or "none"

        experiment_hook_guidance = ""
        if self._hook_experiment_enabled():
            experiment_hook_guidance = (
                "Hook experiment active:\n"
                "- The hook must be anomaly-first.\n"
                "- Do not start the hook with mediators such as witness, police, report, tape, files or records.\n"
                "- The first clause must contain a concrete entity plus an anomalous behavior, contradiction or impossible state.\n"
                "- Provenance may exist only after the anomaly.\n"
                "- Avoid bureaucratic case-title phrasing.\n"
                "- Prefer hook families such as state anomaly, temporal contradiction, system malfunction, spatial inconsistency, human behavior anomaly, recurring event or hidden rule violation.\n\n"
            )

        return (
            "You are CortAI's senior narrative copywriter for short-form vertical video.\n"
            "Write only a structured JSON object.\n"
            "Goal: produce a high-retention three-block script for on-screen narration and captions.\n"
            "The output must feel specific, vivid and unnerving, not generic.\n"
            "Use the assigned narrative mode and the system context below.\n\n"
            "Required JSON schema:\n"
            "{\n"
            '  "narrative_mode": "<one of the requested modes>",\n'
            '  "hook": "<6 to 11 words, strong opening>",\n'
            '  "setup": "<7 to 13 words, escalates tension>",\n'
            '  "payoff": "<7 to 13 words, concrete unsettling closure>"\n'
            "}\n\n"
            "Hard constraints:\n"
            "- English only.\n"
            "- Output valid JSON only. No markdown. No commentary.\n"
            "- Each block must be semantically complete on its own.\n"
            "- Avoid filler, vagueness and abstract endings.\n"
            "- The payoff must resolve the narrative promise with a concrete reveal.\n"
            "- Do not repeat key nouns across all three blocks unless necessary.\n"
            "- Do not use these cliches:\n"
            f"{anti_cliche}\n"
            "- Do not mention hashtags, camera directions or labels.\n"
            "- Prefer concrete nouns, verbs and anomalies over vague suspense language.\n\n"
            "Narrative modes available:\n"
            "- witness_report\n"
            "- recovered_recording\n"
            "- official_warning\n"
            "- contradiction_timeline\n"
            "- urban_legend_fragment\n"
            "- hidden_truth\n"
            "- procedural_anomaly\n\n"
            f"Assigned narrative mode: {narrative_mode}\n"
            f"Account ID: {context.account_id}\n"
            f"Niche: {context.niche}\n"
            f"Topic: {context.topic}\n"
            f"Account health status: {context.account_health_status}\n"
            f"Strategy goal: {strategy.goal if strategy else 'retention'}\n"
            f"Strategy content mode: {strategy.content_mode if strategy else 'standard'}\n"
            f"Hook aggressiveness: {strategy.hook_aggressiveness if strategy else 'medium'}\n"
            f"Target duration range: {strategy.target_duration_range if strategy else '8-12s'}\n"
            f"Trend dominant hooks: {dominant_hooks}\n"
            f"Trend pacing: {trend.pacing if trend else 'baseline'}\n"
            f"Trend visual style: {trend.visual_style if trend else 'phase1_baseline'}\n"
            f"Learning recommendations: {recommendations}\n"
            f"Recommended hook type: {learning.recommended_hook_type if learning else 'question'}\n"
            f"Preferred voice style: {learning.preferred_voice_style if learning else 'phase1_baseline'}\n"
            f"Experiment variant: {experiment_variant}\n"
            f"Experiment payload: {experiment_payload}\n\n"
            f"{experiment_hook_guidance}"
            "Creative guidance:\n"
            "- If the hook style points to question, build an implied question without ending weakly.\n"
            "- If the hook style points to story_opening, open with a concrete event already in motion.\n"
            "- If the hook style points to shock_statement, use a bold factual anomaly.\n"
            "- Make the setup intensify the anomaly, not restate the hook.\n"
            "- Make the payoff specific enough to visualize instantly.\n"
            "- The payoff must end on an observable reveal, not an abstract mystery statement.\n"
            "- Prefer concrete reveals such as a voice, name, room number, tape, station, key, body, timestamp or warning.\n"
            "- The payoff must reveal one concrete observable fact, not only a creepy implication.\n"
            "- Avoid endings built only on broad eerie concepts such as empty room, unknown presence or unexplained feeling.\n"
            "- Favor distinctive nouns linked to the topic.\n"
            f"- Avoid these blocked payoff structures: {blocked_structures}.\n"
            f"- Avoid these blocked visual payoff families when implying evidence: {blocked_visual}.\n"
        )

    def generate_experimental_hook(
        self,
        *,
        context: ScriptGenerationContext,
        hook: str,
        setup: str,
        payoff: str,
        narrative_mode: str,
    ) -> str:
        del narrative_mode
        if not self._hook_experiment_enabled():
            return hook

        normalized_hook = self._normalize_block(hook)
        hook_upper = normalized_hook.upper()
        inferential_enabled = self._inferential_hook_experiment_enabled()
        if inferential_enabled and self._is_inferential_hook_candidate(
            topic=context.topic,
            hook=normalized_hook,
            setup=setup,
            payoff=payoff,
        ):
            candidate = self._inferential_hook_from_topic(context.topic, default=normalized_hook)
            if candidate and candidate != normalized_hook:
                return candidate
        if hook_upper.startswith(MEDIATOR_PREFIXES) or hook_upper.startswith(NON_ANOMALY_LEADS):
            candidate = self._anomaly_first_hook_from_topic(context.topic, default=normalized_hook)
        else:
            candidate = self._normalize_hook_candidate(normalized_hook)
        return candidate or normalized_hook

    def _select_narrative_mode(self, context: ScriptGenerationContext) -> str:
        experiment_variant = (context.experiment_plan.variant_id if context.experiment_plan else "A").strip() or "A"
        forced = ""
        if context.experiment_plan:
            forced = str(context.experiment_plan.variant_params.get("narrative_mode") or "").strip().lower()
        if forced in NARRATIVE_MODES:
            return forced

        niche = context.niche.strip().lower()
        if niche in {"true_crime", "crime"}:
            modes = ("procedural_anomaly", "official_warning", "witness_report", "hidden_truth")
        elif niche in {"history", "ancient_history", "facts"}:
            modes = ("contradiction_timeline", "hidden_truth", "official_warning")
        elif niche in {"horror", "mystery"}:
            modes = ("recovered_recording", "witness_report", "urban_legend_fragment", "official_warning")
        else:
            modes = NARRATIVE_MODES

        material = f"{context.account_id}|{context.topic}|{experiment_variant}".encode("utf-8")
        index = int(sha256(material).hexdigest()[:8], 16) % len(modes)
        return modes[index]

    def _extract_groq_text(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ScriptGenerationError("GROQ_EMPTY_RESPONSE")
        choice = choices[0]
        message = choice.get("message") if isinstance(choice, dict) else None
        text = str(message.get("content") or "").strip() if isinstance(message, dict) else ""
        if not text:
            raise ScriptGenerationError("GROQ_TEXT_EMPTY")
        return text

    def _parse_structured_response(
        self,
        raw_output: str,
        *,
        request: ScriptGenerationRequest,
    ) -> StructuredScriptPayload:
        text = (raw_output or "").strip()
        if not text:
            raise ScriptGenerationError("SCRIPT_OUTPUT_EMPTY")

        for candidate in self._candidate_json_strings(text):
            try:
                payload = json.loads(candidate)
            except Exception:
                continue
            structured = self._payload_from_object(payload)
            if structured is not None:
                return structured

        normalized = self._normalize_script(text)
        sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", normalized) if item.strip()]
        while len(sentences) < 3:
            sentences.append("")
        if not any(sentences):
            raise ScriptGenerationError("SCRIPT_OUTPUT_PARSE_FAILED")
        return StructuredScriptPayload(
            hook=sentences[0],
            setup=sentences[1],
            payoff=sentences[2],
            narrative_mode=self._select_narrative_mode(request.context),
        )

    def _candidate_json_strings(self, text: str) -> list[str]:
        candidates = [text]
        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        candidates.extend(fenced)
        balanced = self._extract_balanced_json(text)
        if balanced:
            candidates.append(balanced)
        return candidates

    def _extract_balanced_json(self, text: str) -> str | None:
        start = text.find("{")
        if start < 0:
            return None
        depth = 0
        in_string = False
        escape = False
        for index, char in enumerate(text[start:], start=start):
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:index + 1]
        return None

    def _payload_from_object(self, payload: Any) -> StructuredScriptPayload | None:
        if not isinstance(payload, dict):
            return None
        hook = str(payload.get("hook") or "").strip()
        setup = str(payload.get("setup") or "").strip()
        payoff = str(payload.get("payoff") or "").strip()
        mode = str(payload.get("narrative_mode") or payload.get("mode") or "").strip().lower()
        if not hook or not setup or not payoff:
            return None
        return StructuredScriptPayload(
            hook=hook,
            setup=setup,
            payoff=payoff,
            narrative_mode=mode or "witness_report",
        )

    def _normalize_payload(self, payload: StructuredScriptPayload) -> StructuredScriptPayload:
        hook = self._normalize_block(payload.hook)
        setup = self._normalize_block(payload.setup)
        payoff = self._normalize_block(payload.payoff)
        mode = payload.narrative_mode.strip().lower()
        if mode not in NARRATIVE_MODES:
            mode = "witness_report"
        return StructuredScriptPayload(
            hook=hook,
            setup=setup,
            payoff=payoff,
            narrative_mode=mode,
        )

    def _finalize_payload(
        self,
        payload: StructuredScriptPayload,
        *,
        context: ScriptGenerationContext,
    ) -> StructuredScriptPayload:
        normalized = self._normalize_payload(payload)
        if self._payoff_needs_repair(
            hook=normalized.hook,
            setup=normalized.setup,
            payoff=normalized.payoff,
            context=context,
        ):
            normalized = StructuredScriptPayload(
                hook=normalized.hook,
                setup=normalized.setup,
                payoff=self._repair_payoff(
                    topic=context.topic,
                    hook=normalized.hook,
                    setup=normalized.setup,
                    payoff=normalized.payoff,
                    narrative_mode=normalized.narrative_mode,
                    niche=context.niche,
                    context=context,
                ),
                narrative_mode=normalized.narrative_mode,
            )
        return normalized

    def _normalize_block(self, value: str) -> str:
        text = value.strip().replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
        text = re.sub(r"\b(hook|setup|payoff)\s*:\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip().strip('"').strip("'").strip()
        text = text.strip(" -")
        if text.endswith(":"):
            text = text[:-1].strip()
        if text and text[-1] not in ".!?":
            text = f"{text}."
        return text

    def _validate_payload(self, payload: StructuredScriptPayload) -> None:
        blocks = [payload.hook, payload.setup, payload.payoff]
        normalized_upper = [self._normalize_script(item).upper() for item in blocks]
        if len({item for item in normalized_upper if item}) != 3:
            raise ScriptGenerationError("SCRIPT_BLOCKS_DUPLICATED")

        for item in blocks:
            words = [token for token in re.findall(r"[A-Za-z0-9']+", item)]
            if len(words) < 3:
                raise ScriptGenerationError("SCRIPT_BLOCK_TOO_SHORT")
            if len(words) > 16:
                raise ScriptGenerationError("SCRIPT_BLOCK_TOO_LONG")

        joined = " ".join(normalized_upper)
        for phrase in ANTI_CLICHE_PHRASES:
            if phrase in joined:
                raise ScriptGenerationError(f"SCRIPT_CLICHE_DETECTED:{phrase}")
        payoff_upper = normalized_upper[2]
        if any(term in payoff_upper for term in WEAK_PAYOFF_TERMS):
            raise ScriptGenerationError("SCRIPT_PAYOFF_TOO_ABSTRACT")
        if any(phrase in payoff_upper for phrase in WEAK_PAYOFF_PHRASES):
            raise ScriptGenerationError("SCRIPT_PAYOFF_TOO_WEAK")
        if self._payoff_needs_repair(
            hook=payload.hook,
            setup=payload.setup,
            payoff=payload.payoff,
            context=None,
        ):
            raise ScriptGenerationError("SCRIPT_PAYOFF_LACKS_CONCRETE_REVEAL")

    def _payoff_needs_repair(self, *, hook: str, setup: str, payoff: str, context: ScriptGenerationContext | None) -> bool:
        payoff_upper = self._normalize_script(payoff).upper()
        if not payoff_upper:
            return True
        if self._payoff_structure_label(payoff_upper) in set(self._blocked_payoff_structures(context)):
            return True
        if any(term in payoff_upper for term in WEAK_PAYOFF_TERMS):
            return True
        if any(phrase in payoff_upper for phrase in WEAK_PAYOFF_PHRASES):
            return True
        if any(phrase in payoff_upper for phrase in WEAK_PAYOFF_PHRASES):
            return True
        if any(hint in payoff_upper for hint in SPECIFICITY_PAYOFF_HINTS):
            return False
        has_numeric_anchor = bool(re.search(r"\b\d{1,4}\b", payoff_upper))
        has_concrete_hint = any(term in payoff_upper for term in CONCRETE_PAYOFF_HINTS)
        if has_numeric_anchor or has_concrete_hint:
            if any(term in payoff_upper for term in ("SOMEONE", "SOMETHING", "PRESENCE")):
                return True
            if any(phrase in payoff_upper for phrase in ("BEHIND THE DOOR", "INSIDE THE WALL", "INTO THE WALL")):
                return True
            return False
        payoff_tokens = [token for token in re.findall(r"[A-Z0-9']+", payoff_upper) if token not in PAYOFF_STOPWORDS]
        if len(payoff_tokens) < 2:
            return True
        if any(term in payoff_upper for term in GENERIC_ABSTRACT_PAYOFF_HINTS):
            return True
        # Prevent pure atmospheric restatements by requiring the payoff to materially differ from the setup.
        setup_upper = self._normalize_script(setup).upper()
        hook_upper = self._normalize_script(hook).upper()
        if payoff_upper in {hook_upper, setup_upper}:
            return True
        return False

    def _repair_payoff(
        self,
        *,
        topic: str,
        hook: str,
        setup: str,
        payoff: str,
        narrative_mode: str,
        niche: str,
        context: ScriptGenerationContext | None,
    ) -> str:
        upper_material = " ".join(
            self._normalize_script(value).upper()
            for value in (topic, hook, setup, payoff, narrative_mode, niche)
            if value
        )
        blocked_structures = set(self._blocked_payoff_structures(context))
        if "named_location_removed" in blocked_structures:
            if any(token in upper_material for token in ("WARNING", "SCREEN", "MONITOR", "PANEL", "EXIT SIGN", "SIGNAL")):
                return "THE FINAL WARNING POINTED TO A DOOR THAT WAS NEVER ON THE MAP."
            if any(token in upper_material for token in ("TAPE", "ARCHIVE", "FILE", "LOG", "TRANSCRIPT", "REPORT")):
                return "THE FINAL RECORD NAMED A VOICE ERASED FROM THE STAFF LOG."
            if any(token in upper_material for token in ("PHONE", "CALL", "CALLER", "VOICE", "INTERCOM")):
                return "THE LAST INTERCOM WORD MATCHED A NAME ERASED FROM THE NIGHT LOG."
            return "THE FINAL WARNING NAMED A STAIRWELL ERASED FROM THE STATION MAP."
        if any(token in upper_material for token in ("ROOM", "WING", "CORRIDOR", "FLOOR", "HALLWAY")):
            return "THE LAST WHISPER NAMED ROOM 312 ON THE SEALED FLOOR."
        if any(token in upper_material for token in ("TAPE", "ARCHIVE", "FILE", "LOG", "TRANSCRIPT", "REPORT")):
            return "THE FINAL RECORD NAMED A FILE SEALED SINCE 1997."
        if any(token in upper_material for token in ("DOOR", "LOCK", "KEY", "HATCH", "GATE")):
            return "THE LAST CLICK CAME FROM DOOR 16, REMOVED FROM THE FLOORPLAN."
        if any(token in upper_material for token in ("PHONE", "CALL", "CALLER", "VOICE", "INTERCOM")):
            return "THE LAST WHISPER NAMED ROOM 312, LISTED AS NON-EXISTENT."
        if any(token in upper_material for token in ("CAMERA", "SCREEN", "MONITOR", "WARNING", "PANEL")):
            return "THE FINAL WARNING SHOWED A ROOM NUMBER REMOVED FROM THE MAP."
        return "THE FINAL WARNING NAMED A ROOM REMOVED FROM THE FLOORPLAN."

    def _deterministic_fallback(
        self,
        *,
        request: ScriptGenerationRequest,
        prompt: str,
        errors: list[str],
    ) -> ScriptGenerationResponse:
        context = request.context
        mode = self._select_narrative_mode(context)
        payload = self._fallback_payload(context=context, mode=mode)
        script_plan = ScriptPlan(
            hook=payload.hook,
            setup=payload.setup,
            payoff=payload.payoff,
            generation_mode="fallback_contextual",
        )
        return ScriptGenerationResponse(
            script_plan=script_plan,
            payload=payload,
            provider_used="fallback",
            model_used="deterministic",
            prompt_used=prompt,
            raw_output="; ".join(errors),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="script_generation_contextual_fallback",
            ),
            provider_attempt_trace=tuple(errors),
        )

    def _local_structured_payload(self, *, context: ScriptGenerationContext, mode: str) -> StructuredScriptPayload:
        return self._fallback_payload(context=context, mode=mode)

    def _fallback_payload(self, *, context: ScriptGenerationContext, mode: str) -> StructuredScriptPayload:
        topic_phrase = self._topic_phrase(context.topic, default=context.niche or "this place")
        theme = context.niche.strip().lower()
        blocked_structures = set(self._blocked_payoff_structures(context))
        if theme in {"true_crime", "crime"}:
            templates = {
                "procedural_anomaly": (
                    f"POLICE REOPENED {topic_phrase.upper()}",
                    "THE LOGS SHOWED A TIMESTAMP NOBODY FILED",
                    "THE RECORDER CAPTURED A VOICE FROM SEALED EVIDENCE",
                ),
                "official_warning": (
                    f"CASE NOTES FLAGGED {topic_phrase.upper()}",
                    "OFFICERS WERE TOLD NEVER TO WORK THAT ROOM ALONE",
                    "THE LAST TAPE NAMED AN OFFICER WHO DIED YEARS AGO",
                ),
            }
        elif theme in {"history", "ancient_history", "facts"}:
            templates = {
                "contradiction_timeline": (
                    f"ARCHIVES KEPT CHANGING {topic_phrase.upper()}",
                    "EACH VERSION ERASED THE WITNESS FROM THE TIMELINE",
                    "THE FINAL ENTRY PLACED THEM IN A CITY THAT NEVER STOOD",
                ),
                "hidden_truth": (
                    f"HISTORIANS MISSED {topic_phrase.upper()}",
                    "THE RECORD LOOKED ROUTINE UNTIL THE LAST LINE VANISHED",
                    "A REDACTED NAME REAPPEARED IN TOMORROW'S REPORT",
                ),
                "procedural_anomaly": (
                    f"RESEARCH LOGS FLAGGED {topic_phrase.upper()}",
                    "THE INSTRUMENTS SPIKED BEFORE ANY TECHNICIAN ENTERED",
                    "THE FINAL TIMESTAMP POINTED TO A LAB THAT WAS SEALED",
                ),
                "witness_report": (
                    f"A SURVIVOR DESCRIBED {topic_phrase.upper()}",
                    "THE NOTEBOOK CHANGED AFTER THE SECOND READING",
                    "THE LAST PAGE NAMED A ROOM REMOVED FROM THE FLOORPLAN",
                ),
                "recovered_recording": (
                    f"AN ARCHIVE TAPE MENTIONED {topic_phrase.upper()}",
                    "THE SPEAKER STOPPED WHEN THE CLOCK HIT 3 14",
                    "THE FINAL WORD MATCHED A FILE MARKED DESTROYED",
                ),
                "official_warning": (
                    f"AN OFFICIAL MEMO FLAGGED {topic_phrase.upper()}",
                    "STAFF WERE TOLD TO LOCK THE CABINET BEFORE DAWN",
                    "THE LAST REVISION WAS SIGNED HOURS BEFORE IT EXISTED",
                ),
                "urban_legend_fragment": (
                    f"LOCALS KEPT REPEATING {topic_phrase.upper()}",
                    "THE STORY ALWAYS CHANGES AFTER THE MISSING TIMESTAMP",
                    "BY MORNING THE MAP SHOWS A CORRIDOR THAT SHOULD NOT FIT",
                ),
            }
        else:
            templates = {
                "recovered_recording": (
                    f"A RECOVERED TAPE MENTIONED {topic_phrase.upper()}",
                    "THE SPEAKER KEPT DESCRIBING FOOTSTEPS BEHIND THE WALL",
                    "THE LAST SECOND MATCHED DOOR 16, REMOVED FROM THE FLOORPLAN",
                ),
                "witness_report": (
                    f"A WITNESS SAW {topic_phrase.upper()}",
                    "THEIR STORY TURNED STRANGER EVERY TIME THE LIGHTS FAILED",
                    "THE FINAL DETAIL NAMED DOOR 16, REMOVED FROM THE FLOORPLAN",
                ),
                "urban_legend_fragment": (
                    f"LOCALS STILL TALK ABOUT {topic_phrase.upper()}",
                    "THE WARNING ONLY MAKES SENSE AFTER THE SECOND SOUND",
                    "BY THEN THE EXIT SIGN POINTS TO DOOR 16, MISSING FROM THE MAP",
                ),
            }

        if "named_location_removed" in blocked_structures:
            templates = dict(templates)
            if theme in {"true_crime", "crime"}:
                templates["procedural_anomaly"] = (
                    f"POLICE REOPENED {topic_phrase.upper()}",
                    "THE LOGS SHOWED A TIMESTAMP NOBODY FILED",
                    "THE LAST RECORD NAMED A VOICE ERASED FROM THE NIGHT LOG",
                )
            elif theme in {"history", "ancient_history", "facts"}:
                templates["witness_report"] = (
                    f"A SURVIVOR DESCRIBED {topic_phrase.upper()}",
                    "THE NOTEBOOK CHANGED AFTER THE SECOND READING",
                    "THE LAST WARNING NAMED A STAIRWELL MISSING FROM THE INDEX",
                )
            else:
                templates["witness_report"] = (
                    f"A WITNESS SAW {topic_phrase.upper()}",
                    "THEIR STORY TURNED STRANGER EVERY TIME THE LIGHTS FAILED",
                    "THE FINAL WARNING POINTED TO A DOOR THAT WAS NEVER ON THE MAP",
                )
                templates["urban_legend_fragment"] = (
                    f"LOCALS STILL TALK ABOUT {topic_phrase.upper()}",
                    "THE WARNING ONLY MAKES SENSE AFTER THE SECOND SOUND",
                    "BY THEN THE PANEL IS NAMING A STAIRWELL THAT DOES NOT EXIST",
                )

        hook, setup, payoff = templates.get(mode) or next(iter(templates.values()))
        return StructuredScriptPayload(
            hook=hook,
            setup=setup,
            payoff=payoff,
            narrative_mode=mode,
        )

    def _blocked_payoff_structures(self, context: ScriptGenerationContext | None) -> list[str]:
        if context is None or context.strategy_profile is None:
            return []
        hints = getattr(context.strategy_profile, "novelty_hints", {}) or {}
        return [str(item).strip() for item in hints.get("blocked_payoff_structures", []) if str(item).strip()]

    def _blocked_visual_categories(self, context: ScriptGenerationContext | None) -> list[str]:
        if context is None or context.strategy_profile is None:
            return []
        hints = getattr(context.strategy_profile, "novelty_hints", {}) or {}
        return [str(item).strip() for item in hints.get("blocked_visual_payoff_categories", []) if str(item).strip()]

    def _payoff_structure_label(self, payoff_upper: str) -> str:
        if any(item in payoff_upper for item in (" REMOVED FROM THE FLOORPLAN ", " MISSING FROM THE MAP ", " ROOM 312 ", " DOOR 16 ")):
            return "named_location_removed"
        if any(item in payoff_upper for item in (" EXIT SIGN ", " WARNING ", " PANEL ", " POINTS TO ", " POINTED TO ")):
            return "device_points_to_impossible_place"
        if any(item in payoff_upper for item in (" FILE ", " ARCHIVE ", " TRANSCRIPT ", " REPORT ", " RECORD ")):
            return "documentary_proof_reveal"
        if any(item in payoff_upper for item in (" INTERCOM ", " VOICE ", " CALLER ", " RECORDER ")):
            return "record_names_impossible_identity"
        if any(item in payoff_upper for item in (" DOOR ", " LOCK ", " GATE ", " SEALED ")):
            return "sealed_access_physical_reveal"
        return "other"

    def _hook_experiment_enabled(self) -> bool:
        return os.getenv("CORTAI_EXPERIMENT_SCRIPT_HOOK_ANOMALY_FIRST", "0") == "1"

    def _inferential_hook_experiment_enabled(self) -> bool:
        return os.getenv("CORTAI_EXPERIMENT_SCRIPT_HOOK_INFERENTIAL", "0") == "1"

    def _is_inferential_hook_candidate(
        self,
        *,
        topic: str,
        hook: str,
        setup: str,
        payoff: str,
    ) -> bool:
        topic_upper = self._normalize_ascii(topic).upper()
        _ = hook, setup, payoff
        keyword_hits = sum(1 for item in INFERENTIAL_KEYWORDS if item in topic_upper)
        if keyword_hits == 0:
            return False
        if any(item in topic_upper for item in EXPERIENTIAL_TOPIC_KEYWORDS):
            return False
        if any(item in topic_upper for item in ("TRANSCRIPT", "ARCHIVE", "LOG", "RECORD", "TAPE", "STATEMENT", "OVERRIDE", "DATE", "CONTRADICTION", "DISCREPANCY")):
            return True
        return False

    def _inferential_hook_from_topic(self, topic: str, *, default: str) -> str:
        text = self._normalize_ascii(topic)
        lower = text.lower()
        if not lower:
            return ""

        if "dispatcher tape reopened" in lower:
            return "THE DISPATCHER TAPE APPEARED IN EVIDENCE TWICE."
        if "archive override on server 9" in lower:
            return "THE ARCHIVE LOG SHOWED AN UNAUTHORIZED OVERRIDE ON SERVER 9."
        if "contradictory evidence tape" in lower:
            return "THE EVIDENCE TAPE CONTAINED TWO CONFLICTING STATEMENTS."
        if "security log erased a minute" in lower:
            return "THE SECURITY LOG WAS MISSING A FULL MINUTE."
        if "sealed call transcript discrepancy" in lower:
            return "THE SEALED CALL TRANSCRIPT DID NOT MATCH THE AUDIO."
        if "missing witness transcript" in lower:
            return "THE WITNESS TRANSCRIPT WAS MISSING A PAGE."
        if "janitor witness statement" in lower:
            return "THE JANITOR STATEMENT DID NOT MATCH THE RECORD."
        if "archive page changed date" in lower:
            return "THE ARCHIVE PAGE CONTAINED A DATE FROM THE FUTURE."
        if "research log contradiction" in lower:
            return "THE RESEARCH LOG CONTAINED TWO CONFLICTING ENTRIES."
        if "night watch log with future date" in lower:
            return "THE NIGHT WATCH LOG CONTAINED A DATE FROM THE FUTURE."
        if "urban legend tied to census record" in lower:
            return "THE CENSUS RECORD MATCHED A STORY IT SHOULD NOT HAVE KNOWN."
        if "future date" in lower:
            subject = self._topic_subject(lower, remove={"with", "future", "date"})
            return f"THE {subject} CONTAINED A DATE FROM THE FUTURE.".upper()
        if "changed date" in lower:
            subject = self._topic_subject(lower, remove={"changed", "date"})
            return f"THE {subject} CONTAINED A DATE FROM THE FUTURE.".upper()
        if "contradiction" in lower:
            subject = self._topic_subject(lower, remove={"contradiction"})
            return f"THE {subject} CONTAINED TWO CONFLICTING ENTRIES.".upper()
        if "discrepancy" in lower:
            subject = self._topic_subject(lower, remove={"discrepancy"})
            return f"THE {subject} DID NOT MATCH THE RECORD.".upper()
        return ""

    def _anomaly_first_hook_from_topic(self, topic: str, *, default: str) -> str:
        text = self._normalize_ascii(topic)
        lower = text.lower()
        if not lower:
            return self._normalize_hook_candidate(default)

        if "camera desync" in lower:
            return "THE AUTOPSY ROOM CAMERA FELL OUT OF SYNC."
        if "warning" in lower and "tunnel" in lower:
            return "THE RAIL TUNNEL DISPLAYED A WARNING."
        if "warning" in lower and "intercom" in lower:
            return "THE STATION INTERCOM DISPLAYED A WARNING."
        if "blackout" in lower and "sector" in lower:
            sector = self._extract_sector(lower)
            return f"THE CAMERA WENT DARK IN {sector}.".upper()
        if "future date" in lower:
            subject = self._topic_subject(lower, remove={"with", "future", "date"})
            return f"THE {subject} CARRIED A FUTURE DATE.".upper()
        if "changed date" in lower:
            subject = self._topic_subject(lower, remove={"changed", "date"})
            return f"THE {subject} CHANGED DATE.".upper()
        if "missing corridor" in lower:
            subject = self._topic_subject(lower, remove={"missing", "corridor"})
            return f"THE {subject} WAS MISSING A CORRIDOR.".upper()
        if "contradiction" in lower:
            subject = self._topic_subject(lower, remove={"contradiction"})
            return f"THE {subject} CONTAINED A CONTRADICTION.".upper()
        if "discrepancy" in lower:
            subject = self._topic_subject(lower, remove={"discrepancy"})
            return f"THE {subject} SHOWED A DISCREPANCY.".upper()
        if "erased a minute" in lower:
            subject = self._topic_subject(lower, remove={"erased", "a", "minute"})
            return f"THE {subject} ERASED A MINUTE.".upper()
        if "sealed after" in lower:
            parts = re.split(r"sealed after", lower, maxsplit=1)
            subject = self._topic_subject(parts[0], remove={"sealed"})
            suffix = self._normalize_ascii(parts[1]).strip()
            return f"AFTER {suffix} THE {subject} WAS SEALED.".upper()
        if "reopened itself" in lower:
            subject = self._topic_subject(lower, remove={"reopened", "itself", "that"})
            return f"THE {subject} REOPENED ITSELF.".upper()
        if "timetable" in lower and "abandoned platform" in lower:
            return "THE ABANDONED PLATFORM TIMETABLE KEPT CHANGING."
        if "blueprint" in lower and "1975" in lower:
            return "THE 1975 BLUEPRINT SHOWED AN EXTRA CORRIDOR."
        if "museum audio anomaly" in lower:
            return "THE MUSEUM AUDIO CHANGED AFTER MIDNIGHT."
        if "urban legend" in lower and "census record" in lower:
            return "THE CENSUS RECORD MATCHED THE URBAN LEGEND."
        if "hospital wing" in lower and "3 am" in lower:
            return "AFTER 3 AM THE HOSPITAL WING WAS SEALED."
        if "voice behind the fire exit" in lower:
            return "A VOICE SPOKE BEHIND THE FIRE EXIT."
        if "sealed evidence room whisper" in lower:
            return "THE SEALED EVIDENCE ROOM STARTED WHISPERING."
        if "sealed locker recorder" in lower:
            return "THE SEALED LOCKER RECORDER STARTED PLAYING."
        if "dispatcher tape reopened" in lower:
            return "THE DISPATCHER TAPE RETURNED TO EVIDENCE."
        if "missing witness transcript" in lower:
            return "THE WITNESS TRANSCRIPT LOST A PAGE."
        if "archive override on server 9" in lower:
            return "SERVER 9 SHOWED AN ARCHIVE OVERRIDE."
        if "research log contradiction" in lower:
            return "THE RESEARCH LOG CONTAINED A CONTRADICTION."
        return self._normalize_hook_candidate(default)

    def _normalize_hook_candidate(self, text: str) -> str:
        normalized = self._normalize_block(text)
        words = re.findall(r"[A-Za-z0-9']+", normalized)
        if not words:
            return normalized
        if len(words) > 11:
            normalized = " ".join(words[:11]) + "."
        if normalized.upper().startswith(MEDIATOR_PREFIXES):
            return normalized
        if normalized.endswith(".") and normalized.upper() == normalized:
            return normalized
        return normalized.upper()

    def _topic_subject(self, text: str, *, remove: set[str]) -> str:
        words = [w for w in re.findall(r"[a-z0-9']+", text.lower()) if w not in remove]
        if not words:
            return "EVENT"
        return " ".join(words[:4])

    def _extract_sector(self, text: str) -> str:
        match = re.search(r"sector\s+([a-z0-9']+)", text)
        if not match:
            return "SECTOR"
        return f"SECTOR {match.group(1)}".upper()

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
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def _topic_phrase(self, topic: str, *, default: str) -> str:
        words = [token for token in re.findall(r"[A-Za-z0-9']+", topic or "")]
        if not words:
            words = [token for token in re.findall(r"[A-Za-z0-9']+", default)]
        trimmed = words[:6]
        return " ".join(trimmed) if trimmed else "THIS PLACE"

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
