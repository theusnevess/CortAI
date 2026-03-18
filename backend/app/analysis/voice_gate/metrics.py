from __future__ import annotations

import statistics
from typing import Any


def duration_per_word(*, text: str, duration_s: float | None) -> float:
    words = max(1, len(str(text or "").split()))
    if duration_s is None:
        return 0.0
    return round(duration_s / words, 4)


def segment_duration_variation(segment_durations: list[float]) -> float:
    clean = [value for value in segment_durations if value > 0]
    if len(clean) < 2:
        return 0.0
    mean_value = statistics.mean(clean)
    if mean_value <= 0:
        return 0.0
    return round(statistics.pstdev(clean) / mean_value, 4)


def pause_distribution_from_voice_plan(voice_plan: Any) -> dict[str, int]:
    segments = getattr(voice_plan, "segments", {}) or {}
    hook = segments.get("hook")
    setup = segments.get("setup")
    payoff = segments.get("payoff")
    return {
        "pause_after_hook": int(getattr(hook, "pause_after_ms", 0) or 0),
        "pause_after_setup": int(getattr(setup, "pause_after_ms", 0) or 0),
        "pause_before_payoff": int(getattr(payoff, "pause_before_ms", 0) or 0),
    }


def segment_contrast_score(voice_plan: Any) -> float:
    segments = getattr(voice_plan, "segments", {}) or {}
    rates = [float(getattr(segment, "rate", 1.0) or 1.0) for segment in segments.values()]
    pauses = list(pause_distribution_from_voice_plan(voice_plan).values())
    emphasis_values = {str(getattr(segment, "emphasis", "medium")) for segment in segments.values()}
    rate_spread = max(rates) - min(rates) if rates else 0.0
    pause_score = min(1.0, sum(max(0, pause) for pause in pauses) / 900.0)
    emphasis_score = min(1.0, max(0, len(emphasis_values) - 1) / 2.0)
    return round(min(1.0, (rate_spread * 5.0) + (pause_score * 0.5) + (emphasis_score * 0.2)), 4)


def monotony_proxy_score(*, voice_plan: Any, segment_durations: list[float]) -> float:
    contrast = segment_contrast_score(voice_plan)
    duration_variation = min(1.0, segment_duration_variation(segment_durations) * 2.0)
    pauses = pause_distribution_from_voice_plan(voice_plan)
    pause_presence = min(1.0, sum(1 for value in pauses.values() if value > 0) / 3.0)
    score = 1.0 - min(1.0, (contrast * 0.5) + (duration_variation * 0.3) + (pause_presence * 0.2))
    return round(max(0.0, score), 4)


def delivery_variance_score(rows: list[dict[str, Any]]) -> float:
    if len(rows) < 2:
        return 0.0
    rhythm = [float(row.get("duration_per_word") or 0.0) for row in rows]
    monotony = [float(row.get("monotony_proxy_score") or 0.0) for row in rows]
    values = [value for value in rhythm + monotony if value > 0]
    if len(values) < 2:
        return 0.0
    return round(statistics.pstdev(values), 4)


def summarize_latency(latencies: list[float]) -> dict[str, float]:
    if not latencies:
        return {"avg_latency_s": 0.0, "p95_latency_s": 0.0}
    ordered = sorted(latencies)
    p95_index = max(0, int(len(ordered) * 0.95) - 1)
    return {
        "avg_latency_s": round(statistics.mean(ordered), 3),
        "p95_latency_s": round(ordered[p95_index], 3),
    }
