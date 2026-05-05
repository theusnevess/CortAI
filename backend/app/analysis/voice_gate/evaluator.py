from __future__ import annotations

from collections import Counter
from typing import Any

from app.analysis.voice_gate.metrics import summarize_latency


def evaluate_gate(*, battery: dict[str, Any], video_batch: dict[str, Any]) -> dict[str, Any]:
    rows = list(battery.get("rows", []))
    fallback_cases = list(battery.get("fallback_cases", []))
    video_rows = list(video_batch.get("rows", []))
    failures: list[str] = []
    warnings: list[str] = []

    provider_pairs = [(row.get("provider_requested", ""), row.get("provider_executed", "")) for row in rows]
    provider_traceability = all(row.get("provider_executed") for row in rows)
    voice_plan_obeyed = all(requested == executed for requested, executed in provider_pairs)
    fallback_visibility = all(
        (not row.get("fallback_used")) or bool(row.get("fallback_reason"))
        for row in rows + fallback_cases
    )

    success_rate = _ratio(sum(1 for row in rows if row.get("audio_duration_seconds")), max(1, len(rows)))
    fallback_rate = _ratio(sum(1 for row in rows if row.get("fallback_used")), max(1, len(rows)))
    latency_summary = summarize_latency([float(row.get("tts_latency_seconds") or 0.0) for row in rows if row.get("tts_latency_seconds")])
    avg_segment_contrast = _avg([float(row.get("segment_contrast_score") or 0.0) for row in rows])
    avg_monotony = _avg([float(row.get("monotony_proxy_score") or 0.0) for row in rows])
    avg_pause_after_hook = _avg([float(row.get("pause_after_hook") or 0.0) for row in rows])
    avg_pause_before_payoff = _avg([float(row.get("pause_before_payoff") or 0.0) for row in rows])
    video_success_rate = _ratio(
        sum(1 for row in video_rows if row.get("pipeline_status") == "READY" and row.get("video_qc_status") == "APPROVE"),
        max(1, len(video_rows)),
    )

    if not provider_traceability:
        failures.append("provider traceability missing in one or more battery runs")
    if not fallback_visibility:
        failures.append("fallback occurred without explicit fallback_reason")
    if success_rate < 0.95:
        failures.append(f"text battery success_rate too low: {success_rate:.2f}")
    if video_success_rate < 0.8:
        failures.append(f"video batch success_rate too low: {video_success_rate:.2f}")
    if avg_segment_contrast < 0.45:
        failures.append(f"segment contrast below threshold: {avg_segment_contrast:.3f}")
    if avg_monotony > 0.65:
        failures.append(f"monotony proxy too high: {avg_monotony:.3f}")
    if avg_pause_after_hook < 200:
        failures.append(f"pause_after_hook too low: {avg_pause_after_hook:.1f}ms")
    if avg_pause_before_payoff < 300:
        failures.append(f"pause_before_payoff too low: {avg_pause_before_payoff:.1f}ms")
    if latency_summary["avg_latency_s"] > 15:
        failures.append(f"avg TTS latency impractical: {latency_summary['avg_latency_s']:.3f}s")
    if not any(item.get("fallback_used") and item.get("provider_executed") == "piper" for item in fallback_cases):
        failures.append("forced fallback battery did not prove Piper fallback")

    if not voice_plan_obeyed:
        warnings.append("some requested providers were not executed directly; fallback path was used")
    if fallback_rate > 0.2:
        warnings.append(f"fallback rate elevated: {fallback_rate:.2f}")

    architecture_checks = {
        "VoicePlan obeyed": "PASS" if voice_plan_obeyed else "FAIL",
        "TTS Router canonical": "PASS" if provider_traceability else "FAIL",
        "Provider traceability": "PASS" if provider_traceability and fallback_visibility else "FAIL",
    }
    perceptual_checks = {
        "segment contrast": "PASS" if avg_segment_contrast >= 0.45 else "FAIL",
        "pause distribution": "PASS" if avg_pause_after_hook >= 200 and avg_pause_before_payoff >= 300 else "FAIL",
        "monotony reduction": "PASS" if avg_monotony <= 0.65 else "FAIL",
    }
    operational_checks = {
        "success_rate": round(success_rate, 3),
        "fallback_rate": round(fallback_rate, 3),
        "avg_latency_s": latency_summary["avg_latency_s"],
        "p95_latency_s": latency_summary["p95_latency_s"],
        "video_success_rate": round(video_success_rate, 3),
    }
    return {
        "status": "GO" if not failures else "NO-GO",
        "failures": failures,
        "warnings": warnings,
        "architecture_checks": architecture_checks,
        "perceptual_checks": perceptual_checks,
        "operational_checks": operational_checks,
        "summary": {
            "provider_counts": dict(Counter(row.get("provider_executed", "") for row in rows)),
            "requested_counts": dict(Counter(row.get("provider_requested", "") for row in rows)),
            "avg_segment_contrast": round(avg_segment_contrast, 3),
            "avg_monotony_proxy": round(avg_monotony, 3),
            "avg_pause_after_hook": round(avg_pause_after_hook, 1),
            "avg_pause_before_payoff": round(avg_pause_before_payoff, 1),
            "delivery_variance_score": battery.get("delivery_variance_score", 0.0),
        },
    }


def _avg(values: list[float]) -> float:
    clean = [value for value in values if value is not None]
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator
