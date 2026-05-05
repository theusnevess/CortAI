from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Pattern:
    type: str
    finding: str
    evidence_count: int
    confidence: float
    source: str = "qc_evidence"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class QCAnalysis:
    approve_rate: float
    hold_rate: float
    reject_rate: float
    avg_scores: dict[str, float]
    patterns: list[Pattern]
    sample_size: int
    clean_sample_size: int
    contamination_rate: float
    generated_at: str
    cluster_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)
    contaminated_evidence: list[dict[str, Any]] = field(default_factory=list)
    confidence_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["patterns"] = [pattern.to_dict() for pattern in self.patterns]
        return payload


class QCEvidenceAnalyzer:
    """Converts QC outputs into bounded learning evidence.

    The analyzer reports correlations and signal quality. It never emits winner
    selection, direct strategy instructions, or causal claims beyond the evidence.
    """

    def analyze(self, qc_results: list[dict[str, Any]]) -> QCAnalysis:
        normalized = [self._normalize_result(result) for result in qc_results if isinstance(result, dict)]
        sample_size = len(normalized)
        clean_rows = [row for row in normalized if not row["contaminated"]]
        clean_sample_size = len(clean_rows)
        source_rows = clean_rows or normalized
        contamination_rate = round((sample_size - clean_sample_size) / sample_size, 4) if sample_size else 0.0
        status_counts = self._status_counts(normalized)

        patterns = [
            *self.analyze_hook_patterns(clean_rows),
            *self.analyze_payoff_patterns(clean_rows),
            *self.analyze_quality_drivers(clean_rows),
        ]
        patterns.sort(key=lambda item: (-item.confidence, -item.evidence_count, item.type, item.finding))

        base_confidence = self.calculate_confidence(
            sample_size=clean_sample_size,
            consistency=self._status_consistency(clean_rows),
            signal_strength=self._score_separation(clean_rows),
        )
        adjusted_confidence = round(max(0.0, base_confidence * (1.0 - min(contamination_rate, 0.75))), 4)

        return QCAnalysis(
            approve_rate=self._rate(status_counts.get("APPROVE", 0), sample_size),
            hold_rate=self._rate(status_counts.get("HOLD", 0), sample_size),
            reject_rate=self._rate(status_counts.get("REJECT", 0), sample_size),
            avg_scores={
                "overall": self._average(source_rows, "overall_score"),
                "hook": self._average(source_rows, "hook_score"),
                "payoff": self._average(source_rows, "payoff_score"),
                "product": self._average(source_rows, "product_score"),
            },
            patterns=patterns[:12],
            sample_size=sample_size,
            clean_sample_size=clean_sample_size,
            contamination_rate=contamination_rate,
            generated_at=self._generated_at(normalized),
            cluster_breakdown={
                "approved": self._cluster_summary([row for row in normalized if row["status"] == "APPROVE"]),
                "held": self._cluster_summary([row for row in normalized if row["status"] == "HOLD"]),
                "rejected": self._cluster_summary([row for row in normalized if row["status"] == "REJECT"]),
            },
            contaminated_evidence=[
                {"index": index, "reason": row["contamination_reason"]}
                for index, row in enumerate(normalized)
                if row["contaminated"]
            ],
            confidence_summary={
                "base_confidence": base_confidence,
                "adjusted_confidence": adjusted_confidence,
                "sample_size": clean_sample_size,
                "consistency": self._status_consistency(clean_rows),
                "signal_strength": self._score_separation(clean_rows),
                "contamination_rate": contamination_rate,
            },
        )

    def analyze_hook_patterns(self, rows: list[dict[str, Any]]) -> list[Pattern]:
        return self._categorical_patterns(
            rows=rows,
            key="hook_type",
            pattern_type="hook_type",
            label="hook type",
            score_key="hook_score",
        )

    def analyze_payoff_patterns(self, rows: list[dict[str, Any]]) -> list[Pattern]:
        return self._categorical_patterns(
            rows=rows,
            key="payoff_specificity",
            pattern_type="payoff_specificity",
            label="payoff specificity",
            score_key="payoff_score",
        )

    def analyze_quality_drivers(self, rows: list[dict[str, Any]]) -> list[Pattern]:
        if len(rows) < 5:
            return []
        low_product_rows = [row for row in rows if row["product_score"] > 0 and row["product_score"] < 0.65]
        if len(low_product_rows) < 2:
            return []
        hold_reject_rate = self._hold_reject_rate(low_product_rows)
        if hold_reject_rate < 0.6:
            return []
        confidence = self.calculate_confidence(
            sample_size=len(low_product_rows),
            consistency=hold_reject_rate,
            signal_strength=min(1.0, 1.0 - self._average(low_product_rows, "product_score")),
        )
        if confidence <= 0.0:
            return []
        return [
            Pattern(
                type="quality_driver",
                finding="low product_score is associated with HOLD/REJECT in the clean QC sample",
                evidence_count=len(low_product_rows),
                confidence=confidence,
            )
        ]

    def calculate_confidence(self, sample_size: int, consistency: float, signal_strength: float) -> float:
        if sample_size <= 0:
            return 0.0
        base = min(sample_size / 20.0, 1.0)
        consistency = self._clamp(consistency)
        signal_strength = self._clamp(signal_strength)
        mixed_penalty = 0.65 if consistency < 0.65 else 1.0
        small_sample_penalty = 0.55 if sample_size < 5 else 1.0
        confidence = base * consistency * signal_strength * mixed_penalty * small_sample_penalty
        return round(self._clamp(confidence), 4)

    def _categorical_patterns(
        self,
        *,
        rows: list[dict[str, Any]],
        key: str,
        pattern_type: str,
        label: str,
        score_key: str,
    ) -> list[Pattern]:
        if len(rows) < 5:
            return []
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            value = str(row.get(key) or "").strip()
            if not value or value == "unknown":
                continue
            grouped.setdefault(value, []).append(row)

        patterns: list[Pattern] = []
        for value, value_rows in grouped.items():
            if len(value_rows) < 2:
                continue
            approve_rate = self._approve_rate(value_rows)
            avg_score = self._average(value_rows, score_key)
            global_approve_rate = self._approve_rate(rows)
            global_avg_score = self._average(rows, score_key)
            separation = max(0.0, ((approve_rate - global_approve_rate) + (avg_score - global_avg_score)) / 2.0)
            if separation < 0.08:
                continue
            consistency = max(approve_rate, 1.0 - self._hold_reject_rate(value_rows))
            confidence = self.calculate_confidence(
                sample_size=len(value_rows),
                consistency=consistency,
                signal_strength=min(1.0, separation + 0.35),
            )
            if confidence <= 0.0:
                continue
            patterns.append(
                Pattern(
                    type=pattern_type,
                    finding=f"{label} '{value}' is associated with stronger QC outcomes in the clean sample",
                    evidence_count=len(value_rows),
                    confidence=confidence,
                )
            )
        return patterns

    def _normalize_result(self, result: dict[str, Any]) -> dict[str, Any]:
        script_metadata = self._dict(result.get("script_metadata"))
        asset_metadata = self._dict(result.get("asset_metadata"))
        voice_metadata = self._dict(result.get("voice_metadata"))
        fallback_used = bool(result.get("fallback_used")) or any(
            bool(metadata.get("fallback_used") or metadata.get("fallback"))
            for metadata in (script_metadata, asset_metadata, voice_metadata)
        )
        status = str(result.get("status") or "UNKNOWN").upper()
        overall_score = self._float(result.get("overall_score"))
        hook_score = self._float(result.get("hook_score"))
        payoff_score = self._float(result.get("payoff_score"))
        product_score = self._float(result.get("product_score"))
        missing_metadata = not script_metadata and not asset_metadata and not voice_metadata
        low_signal = status not in {"APPROVE", "HOLD", "REJECT"} or overall_score <= 0.0

        contaminated = fallback_used or low_signal or missing_metadata or bool(result.get("contaminated"))
        reason = ""
        if fallback_used or bool(result.get("contaminated")):
            reason = "fallback_usage"
        elif low_signal:
            reason = "low_signal"
        elif missing_metadata:
            reason = "missing_data"

        payoff_specificity = (
            str(script_metadata.get("payoff_specificity") or result.get("payoff_specificity") or "").strip()
            or self._payoff_specificity_from_text(str(script_metadata.get("payoff") or result.get("payoff") or ""))
        )
        return {
            "status": status,
            "publishable": bool(result.get("publishable")),
            "overall_score": overall_score,
            "hook_score": hook_score,
            "payoff_score": payoff_score,
            "product_score": product_score,
            "technical_valid": bool(result.get("technical_valid", True)),
            "hook_type": str(script_metadata.get("hook_type") or script_metadata.get("hook_style") or result.get("hook_type") or "unknown"),
            "payoff_specificity": payoff_specificity or "unknown",
            "timestamp": str(result.get("timestamp") or ""),
            "contaminated": contaminated,
            "contamination_reason": reason,
        }

    def _cluster_summary(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "count": len(rows),
            "avg_overall": self._average(rows, "overall_score"),
            "avg_hook": self._average(rows, "hook_score"),
            "avg_payoff": self._average(rows, "payoff_score"),
            "avg_product": self._average(rows, "product_score"),
            "clean_count": sum(1 for row in rows if not row["contaminated"]),
        }

    def _status_counts(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        counts = {"APPROVE": 0, "HOLD": 0, "REJECT": 0}
        for row in rows:
            status = row["status"]
            if status in counts:
                counts[status] += 1
        return counts

    def _status_consistency(self, rows: list[dict[str, Any]]) -> float:
        if not rows:
            return 0.0
        counts = self._status_counts(rows)
        return round(max(counts.values()) / len(rows), 4)

    def _score_separation(self, rows: list[dict[str, Any]]) -> float:
        approved = [row for row in rows if row["status"] == "APPROVE"]
        negative = [row for row in rows if row["status"] in {"HOLD", "REJECT"}]
        if not approved or not negative:
            return self._status_consistency(rows)
        return self._clamp(abs(self._average(approved, "overall_score") - self._average(negative, "overall_score")))

    def _approve_rate(self, rows: list[dict[str, Any]]) -> float:
        if not rows:
            return 0.0
        return self._rate(sum(1 for row in rows if row["status"] == "APPROVE"), len(rows))

    def _hold_reject_rate(self, rows: list[dict[str, Any]]) -> float:
        if not rows:
            return 0.0
        return self._rate(sum(1 for row in rows if row["status"] in {"HOLD", "REJECT"}), len(rows))

    def _average(self, rows: list[dict[str, Any]], key: str) -> float:
        values = [self._float(row.get(key)) for row in rows if self._float(row.get(key)) > 0]
        if not values:
            return 0.0
        return round(sum(values) / len(values), 4)

    def _rate(self, count: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round(count / total, 4)

    def _dict(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _float(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return round(float(value), 4)
        return 0.0

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, round(float(value), 4)))

    def _payoff_specificity_from_text(self, payoff: str) -> str:
        text = str(payoff or "").upper()
        if any(token in text for token in ("DOOR ", "ROOM ", "FLOORPLAN", "MAP", "CAMERA", "TAPE")):
            return "specific"
        if len(text.split()) >= 8:
            return "medium"
        return "low"

    def _generated_at(self, rows: list[dict[str, Any]]) -> str:
        timestamps = sorted(str(row.get("timestamp") or "").strip() for row in rows if str(row.get("timestamp") or "").strip())
        return timestamps[-1] if timestamps else "INPUT_DETERMINISTIC"
