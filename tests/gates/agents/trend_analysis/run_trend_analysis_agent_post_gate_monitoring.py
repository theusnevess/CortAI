from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "backend").exists())
EVENT_LOG = ROOT / "OUT" / "events" / "events.jsonl"
OUTPUT_DIR = ROOT / "OUT" / "audit" / "trend_analysis_post_gate_monitoring"


TREND_EVENT_TYPES = {
    "CREATIVE/trend_profile_loaded",
    "CREATIVE/trend_profile_fallback",
    "CREATIVE/trend_collection_completed",
    "CREATIVE/trend_collection_failed",
    "CREATIVE/trend_validation_approved",
    "CREATIVE/trend_validation_hold",
    "CREATIVE/trend_validation_rejected",
}


def _read_rows(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _details(row: dict[str, object]) -> dict[str, object]:
    details = row.get("details")
    return dict(details) if isinstance(details, dict) else {}


def _write_json(name: str, payload: object) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _group_trend_windows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = defaultdict(dict)
    for row in rows:
        event_type = str(row.get("event_type") or "")
        if event_type not in TREND_EVENT_TYPES | {"CREATIVE/strategy_profile_generated", "CREATIVE/asset_selection_generated", "CREATIVE/video_qc_approved", "CREATIVE/video_qc_hold", "CREATIVE/video_qc_rejected"}:
            continue
        details = _details(row)
        account_id = str(row.get("account_id") or details.get("account_id") or "")
        if not account_id:
            continue
        grouped[account_id][event_type] = {"row": row, "details": details}
    return [{"account_id": account_id, **payload} for account_id, payload in grouped.items()]


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def main() -> None:
    rows = _read_rows(EVENT_LOG)
    trend_rows = [row for row in rows if str(row.get("event_type") or "") in TREND_EVENT_TYPES]
    windows = _group_trend_windows(rows)

    collection_counter: Counter[str] = Counter()
    validation_counter: Counter[str] = Counter()
    fallback_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    freshness_counter: Counter[str] = Counter()

    creative_center_cases = 0
    collection_failed_cases = 0
    validation_reject_cases = 0
    safe_default_cases = 0
    frozen_input_ready_cases = 0
    strategy_fast_alignment_hits = 0
    strategy_fast_alignment_total = 0
    asset_visual_alignment_hits = 0
    asset_visual_alignment_total = 0
    qc_approve_count = 0
    qc_non_null_count = 0

    execution_examples: list[dict[str, object]] = []

    for window in windows:
        loaded = window.get("CREATIVE/trend_profile_loaded")
        fallback = window.get("CREATIVE/trend_profile_fallback")
        collection_ok = window.get("CREATIVE/trend_collection_completed")
        collection_fail = window.get("CREATIVE/trend_collection_failed")
        validation = (
            window.get("CREATIVE/trend_validation_approved")
            or window.get("CREATIVE/trend_validation_hold")
            or window.get("CREATIVE/trend_validation_rejected")
        )
        strategy = window.get("CREATIVE/strategy_profile_generated")
        asset = window.get("CREATIVE/asset_selection_generated")
        qc = (
            window.get("CREATIVE/video_qc_approved")
            or window.get("CREATIVE/video_qc_hold")
            or window.get("CREATIVE/video_qc_rejected")
        )

        if collection_ok:
            collection_counter["completed"] += 1
        if collection_fail:
            collection_counter["failed"] += 1
            collection_failed_cases += 1

        trend_event = loaded or fallback
        trend_details = dict((trend_event or {}).get("details") or {})
        if trend_details.get("trend_source") or trend_details.get("validation_status"):
            frozen_input_ready_cases += 1
        trend_source = str(trend_details.get("trend_source") or "")
        if trend_source:
            source_counter[trend_source] += 1
        freshness_state = str(trend_details.get("freshness_state") or "")
        if freshness_state:
            freshness_counter[freshness_state] += 1

        if fallback:
            path = str(trend_details.get("fallback_path") or "unknown")
            fallback_counter[path] += 1
            if path == "safe_default":
                safe_default_cases += 1

        if validation:
            validation_status = str(dict(validation.get("details") or {}).get("status") or "")
            if validation_status:
                validation_counter[validation_status] += 1
            if validation_status == "REJECT":
                validation_reject_cases += 1

        if trend_source == "creative_center":
            creative_center_cases += 1

        if strategy and trend_event:
            strategy_details = dict(strategy.get("details") or {})
            if str(trend_details.get("pacing") or "") == "fast_first_3s":
                strategy_fast_alignment_total += 1
                if str(strategy_details.get("hook_aggressiveness") or "") == "high":
                    strategy_fast_alignment_hits += 1

        if asset and trend_event:
            asset_details = dict(asset.get("details") or {})
            trend_visual_style = str(trend_details.get("visual_style") or "")
            if trend_visual_style:
                asset_visual_alignment_total += 1
                if str(asset_details.get("visual_style") or "") == trend_visual_style:
                    asset_visual_alignment_hits += 1

        if qc:
            qc_non_null_count += 1
            qc_status = str(qc.get("event_type") or "")
            if qc_status == "CREATIVE/video_qc_approved":
                qc_approve_count += 1

        if len(execution_examples) < 10:
            execution_examples.append(
                {
                    "account_id": window["account_id"],
                    "trend_source": trend_source,
                    "validation_status": str(dict((validation or {}).get("details") or {}).get("status") or ""),
                    "fallback_path": str(trend_details.get("fallback_path") or ""),
                    "pacing": str(trend_details.get("pacing") or ""),
                    "trend_visual_style": str(trend_details.get("visual_style") or ""),
                    "strategy_hook_aggressiveness": str(dict((strategy or {}).get("details") or {}).get("hook_aggressiveness") or ""),
                    "asset_visual_style": str(dict((asset or {}).get("details") or {}).get("visual_style") or ""),
                }
            )

    total_windows = len(windows)
    metrics = {
        "trend_window_count": total_windows,
        "trend_event_count": len(trend_rows),
        "frozen_input_ready_rate": _safe_rate(frozen_input_ready_cases, total_windows),
        "creative_center_rate": _safe_rate(creative_center_cases, total_windows),
        "collection_completed_rate": _safe_rate(collection_counter["completed"], total_windows),
        "collection_failed_rate": _safe_rate(collection_failed_cases, total_windows),
        "validation_status_distribution": dict(validation_counter),
        "safe_default_fallback_rate": _safe_rate(safe_default_cases, total_windows),
        "strategy_fast_pacing_alignment_rate": _safe_rate(strategy_fast_alignment_hits, strategy_fast_alignment_total),
        "asset_visual_alignment_rate": _safe_rate(asset_visual_alignment_hits, asset_visual_alignment_total),
        "qc_approve_rate": _safe_rate(qc_approve_count, qc_non_null_count),
        "fallback_path_distribution": dict(fallback_counter),
        "trend_source_distribution": dict(source_counter),
        "freshness_state_distribution": dict(freshness_counter),
    }

    alerts: list[str] = []
    input_ready = metrics["frozen_input_ready_rate"] >= 0.5
    if not input_ready:
        alerts.append("MONITORING_INPUT_NOT_READY")
    else:
        if metrics["collection_failed_rate"] > 0.35:
            alerts.append("CREATIVE_CENTER_COLLECTION_FAILURE_RATE_HIGH")
        if metrics["safe_default_fallback_rate"] > 0.1:
            alerts.append("SAFE_DEFAULT_FALLBACK_RATE_HIGH")
        if validation_reject_cases > 0:
            alerts.append("TREND_VALIDATION_REJECT_OBSERVED")
        if metrics["strategy_fast_pacing_alignment_rate"] < 0.8 and strategy_fast_alignment_total > 0:
            alerts.append("STRATEGY_FAST_PACING_ALIGNMENT_WEAK")
        if metrics["asset_visual_alignment_rate"] < 0.8 and asset_visual_alignment_total > 0:
            alerts.append("ASSET_VISUAL_ALIGNMENT_WEAK")
        if metrics["creative_center_rate"] < 0.5 and total_windows > 0:
            alerts.append("CREATIVE_CENTER_NOT_DOMINANT_DURING_MONITORING")

    monitoring_summary = {
        "status": "INSUFFICIENT_INPUT" if not input_ready else ("STABLE" if not alerts else "MONITORING_ALERTS"),
        "window_rule": {
            "recommended_days": 7,
            "recommended_executions_min": 20,
            "recommended_executions_preferred": 30,
        },
        "metrics": metrics,
        "alerts": alerts,
    }

    human_review = {
        "summary": "This monitoring window is intended to confirm post-gate runtime stability, not to reopen Trend design. It tracks collector stability, validation behavior, fallback pressure, and whether Strategy and Asset continue reflecting Trend context in live executions.",
        "limitations": [
            "This runner depends on frozen event payloads emitted by the orchestrator and does not reconstruct hidden state outside that event surface.",
            "Strategy monitoring here is a causal proxy based on fast pacing to high hook aggressiveness alignment, not a full semantic evaluation of strategic quality.",
            "Creative Center regional filtering remains limited by the public surface and should be interpreted with that constraint in mind.",
        ],
    }

    _write_json("monitoring_summary.json", monitoring_summary)
    _write_json("rolling_metrics.json", metrics)
    _write_json("regression_alerts.json", {"alerts": alerts})
    _write_json("human_review.json", human_review)
    _write_json("execution_examples.json", {"examples": execution_examples})


if __name__ == "__main__":
    main()
