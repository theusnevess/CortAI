from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class EvidenceItem:
    raw_value: float
    timestamp: str = ""
    age_days: int | None = None
    contaminated: bool = False
    source: str = "runtime_history"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WeightedEvidence:
    weighted_sample_size: float
    weighted_signal_strength: float
    weighted_consistency: float
    weighted_recency_score: float
    recent_weight: float
    mid_term_weight: float
    long_term_weight: float
    dominant_window: str
    pattern_type: str
    staleness_detected: bool
    volatility_detected: bool
    window_breakdown: dict[str, dict[str, Any]]
    items_considered: int
    clean_items_considered: int
    contaminated_items_excluded: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TemporalWeightingEngine:
    """Applies deterministic temporal weighting to bounded Learning evidence."""

    def apply_weighting(self, evidence_items: list[EvidenceItem]) -> WeightedEvidence:
        normalized = self._normalize_items(evidence_items)
        clean_items = [item for item in normalized if not item["contaminated"]]
        source_items = clean_items or normalized
        window_breakdown = {
            "recent": self._window_summary(source_items, "recent"),
            "mid_term": self._window_summary(source_items, "mid_term"),
            "long_term": self._window_summary(source_items, "long_term"),
        }
        total_weight = round(sum(item["recency_weight"] for item in source_items), 4)
        weighted_signal_strength = self._weighted_signal_strength(source_items, total_weight)
        weighted_consistency = self._weighted_consistency(source_items, total_weight)
        weighted_recency_score = self._weighted_average(source_items, "recency_weight", total_weight)
        dominant_window = self._dominant_window(window_breakdown)
        pattern_type = self._classify_temporal_pattern(window_breakdown, dominant_window)

        return WeightedEvidence(
            weighted_sample_size=total_weight,
            weighted_signal_strength=weighted_signal_strength,
            weighted_consistency=weighted_consistency,
            weighted_recency_score=weighted_recency_score,
            recent_weight=self._window_weight_share(window_breakdown, "recent", total_weight),
            mid_term_weight=self._window_weight_share(window_breakdown, "mid_term", total_weight),
            long_term_weight=self._window_weight_share(window_breakdown, "long_term", total_weight),
            dominant_window=dominant_window,
            pattern_type=pattern_type,
            staleness_detected=pattern_type == "stale_signal",
            volatility_detected=pattern_type == "volatile",
            window_breakdown=window_breakdown,
            items_considered=len(normalized),
            clean_items_considered=len(clean_items),
            contaminated_items_excluded=len(normalized) - len(clean_items),
        )

    def compute_recency_weight(self, age_days: int) -> float:
        age_days = max(0, int(age_days))
        return round(max(0.3, 1.0 - (age_days / 60.0)), 4)

    def classify_evidence_window(self, age_days: int) -> str:
        age_days = max(0, int(age_days))
        if age_days <= 7:
            return "recent"
        if age_days <= 30:
            return "mid_term"
        return "long_term"

    def _normalize_items(self, evidence_items: list[EvidenceItem]) -> list[dict[str, Any]]:
        parsed_timestamps = [self._parse_timestamp(item.timestamp) for item in evidence_items]
        valid_timestamps = [item for item in parsed_timestamps if item is not None]
        reference = max(valid_timestamps) if valid_timestamps else None
        normalized: list[dict[str, Any]] = []
        for item, parsed in zip(evidence_items, parsed_timestamps):
            age_days = item.age_days
            if age_days is None and reference is not None and parsed is not None:
                age_days = max(0, (reference.date() - parsed.date()).days)
            if age_days is None:
                age_days = 0
            age_days = max(0, int(age_days))
            raw_value = self._clamp(item.raw_value)
            recency_weight = self.compute_recency_weight(age_days)
            normalized.append(
                {
                    "raw_value": raw_value,
                    "age_days": age_days,
                    "window": self.classify_evidence_window(age_days),
                    "recency_weight": recency_weight,
                    "weighted_value": round(raw_value * recency_weight, 4),
                    "direction": self._direction(raw_value),
                    "contaminated": bool(item.contaminated),
                    "source": item.source,
                    "metadata": dict(item.metadata),
                }
            )
        return normalized

    def _window_summary(self, items: list[dict[str, Any]], window: str) -> dict[str, Any]:
        rows = [item for item in items if item["window"] == window]
        total_weight = round(sum(item["recency_weight"] for item in rows), 4)
        avg_value = self._weighted_average(rows, "raw_value", total_weight)
        return {
            "count": len(rows),
            "weighted_count": total_weight,
            "avg_signal": avg_value,
            "direction": self._direction(avg_value) if rows else "absent",
            "avg_age_days": self._average_age(rows),
        }

    def _classify_temporal_pattern(self, window_breakdown: dict[str, dict[str, Any]], dominant_window: str) -> str:
        recent = window_breakdown["recent"]
        mid = window_breakdown["mid_term"]
        long = window_breakdown["long_term"]
        present = [item for item in (recent, mid, long) if item["count"] > 0]
        if not present:
            return "stale_signal"
        if long["count"] > 0 and recent["count"] == 0 and long["weighted_count"] >= max(recent["weighted_count"], mid["weighted_count"]):
            return "stale_signal"

        recent_direction = recent["direction"]
        older_directions = [item["direction"] for item in (mid, long) if item["direction"] in {"positive", "negative"}]
        if recent_direction in {"positive", "negative"} and any(direction != recent_direction for direction in older_directions):
            return "volatile"

        durable_windows = [
            item for item in (recent, mid, long)
            if item["direction"] in {"positive", "negative"} and item["direction"] == recent_direction
        ]
        if recent_direction in {"positive", "negative"} and len(durable_windows) >= 2:
            return "durable_pattern"

        if recent["direction"] == "positive" and dominant_window == "recent" and (mid["count"] + long["count"]) < 3:
            return "recent_spike"
        if dominant_window == "long_term" and recent["count"] == 0:
            return "stale_signal"
        return "volatile"

    def _weighted_signal_strength(self, items: list[dict[str, Any]], total_weight: float) -> float:
        if total_weight <= 0:
            return 0.0
        weighted_average = self._weighted_average(items, "raw_value", total_weight)
        return round(min(1.0, abs(weighted_average - 0.5) * 2.0), 4)

    def _weighted_consistency(self, items: list[dict[str, Any]], total_weight: float) -> float:
        if total_weight <= 0:
            return 0.0
        direction_weights = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
        for item in items:
            direction_weights[item["direction"]] += item["recency_weight"]
        return round(max(direction_weights.values()) / total_weight, 4)

    def _weighted_average(self, items: list[dict[str, Any]], key: str, total_weight: float) -> float:
        if total_weight <= 0:
            return 0.0
        total = sum(float(item.get(key, 0.0)) * item["recency_weight"] for item in items)
        return round(total / total_weight, 4)

    def _window_weight_share(self, window_breakdown: dict[str, dict[str, Any]], window: str, total_weight: float) -> float:
        if total_weight <= 0:
            return 0.0
        return round(float(window_breakdown[window]["weighted_count"]) / total_weight, 4)

    def _dominant_window(self, window_breakdown: dict[str, dict[str, Any]]) -> str:
        return max(
            ("recent", "mid_term", "long_term"),
            key=lambda window: (window_breakdown[window]["weighted_count"], window),
        )

    def _average_age(self, items: list[dict[str, Any]]) -> float:
        if not items:
            return 0.0
        return round(sum(item["age_days"] for item in items) / len(items), 4)

    def _direction(self, raw_value: float) -> str:
        raw_value = self._clamp(raw_value)
        if raw_value >= 0.7:
            return "positive"
        if raw_value <= 0.55:
            return "negative"
        return "neutral"

    def _parse_timestamp(self, value: str) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _clamp(self, value: float) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        return max(0.0, min(1.0, round(numeric, 4)))
