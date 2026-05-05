from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


_CANONICAL_OPTIONAL_SOURCES = {
    "metric_window": "metric_window_summary",
    "qc_history": "qc_history_summary",
    "failure_history": "failure_history_summary",
    "format_repetition": "format_repetition_summary",
}


@dataclass(frozen=True)
class AccountHealthTelemetrySourceSummary:
    source_name: str
    source_type: str
    source_status: str
    record_count: int
    freshness_status: str
    latest_timestamp: str | None = None
    evidence_ref: str | None = None
    reason_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AccountHealthTelemetrySummary:
    telemetry_enrichment_version: str
    lineage_summary: dict[str, Any]
    freshness_summary: dict[str, Any]
    source_status_distribution: dict[str, int]
    source_summaries: list[dict[str, Any]]
    available_signals: list[str]
    missing_signals: list[str]
    degraded_input_mode: bool
    degradation_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AccountHealthTelemetryEnricher:
    """Builds auditable telemetry summaries without changing Health decisions."""

    version = "account-health-telemetry-enrichment-v2.6"

    def enrich(self, data: Any | None) -> AccountHealthTelemetrySummary:
        if data is None:
            return self._empty_summary(reason="ACCOUNT_HEALTH_INPUT_MISSING")

        freshness = self._mapping(getattr(data, "telemetry_freshness", {}))
        explicit_sources = [
            self._source_from_mapping(source, freshness=freshness)
            for source in list(getattr(data, "telemetry_sources", []) or [])
            if isinstance(source, dict)
        ]
        sources_by_name = {source.source_name: source for source in explicit_sources}

        for source_name, attr_name in _CANONICAL_OPTIONAL_SOURCES.items():
            if source_name in sources_by_name:
                continue
            payload = self._mapping(getattr(data, attr_name, {}))
            sources_by_name[source_name] = self._source_from_summary(
                source_name=source_name,
                payload=payload,
                freshness=freshness,
            )

        sources_by_name["legacy_scalar_inputs"] = self._legacy_scalar_source(data)
        sources = [sources_by_name[name] for name in sorted(sources_by_name)]

        distribution = self._status_distribution(sources)
        available_signals = self._available_signals(data=data, sources=sources)
        missing_signals = self._missing_signals(sources)
        degradation_reasons = self._degradation_reasons(
            distribution=distribution,
            explicit_source_count=len(explicit_sources),
            sources=sources,
        )

        return AccountHealthTelemetrySummary(
            telemetry_enrichment_version=self.version,
            lineage_summary={
                "total_source_count": len(sources),
                "real_source_count": distribution["REAL"],
                "absent_source_count": distribution["ABSENT"],
                "stale_source_count": distribution["STALE"],
                "degraded_source_count": distribution["DEGRADED"],
                "dominant_source_status": self._dominant_status(distribution),
                "lineage_available": distribution["REAL"] > 0 or distribution["STALE"] > 0,
            },
            freshness_summary={
                "fresh_source_count": sum(1 for source in sources if source.freshness_status == "fresh"),
                "stale_source_count": sum(1 for source in sources if source.freshness_status == "stale"),
                "unknown_freshness_source_count": sum(
                    1 for source in sources if source.freshness_status == "unknown"
                ),
                "absent_freshness_source_count": sum(1 for source in sources if source.freshness_status == "absent"),
            },
            source_status_distribution=distribution,
            source_summaries=[source.to_dict() for source in sources],
            available_signals=available_signals,
            missing_signals=missing_signals,
            degraded_input_mode=bool(degradation_reasons),
            degradation_reasons=degradation_reasons,
        )

    def _empty_summary(self, *, reason: str) -> AccountHealthTelemetrySummary:
        return AccountHealthTelemetrySummary(
            telemetry_enrichment_version=self.version,
            lineage_summary={
                "total_source_count": 0,
                "real_source_count": 0,
                "absent_source_count": 0,
                "stale_source_count": 0,
                "degraded_source_count": 0,
                "dominant_source_status": "ABSENT",
                "lineage_available": False,
            },
            freshness_summary={
                "fresh_source_count": 0,
                "stale_source_count": 0,
                "unknown_freshness_source_count": 0,
                "absent_freshness_source_count": 0,
            },
            source_status_distribution={"REAL": 0, "ABSENT": 0, "STALE": 0, "DEGRADED": 0},
            source_summaries=[],
            available_signals=[],
            missing_signals=[],
            degraded_input_mode=True,
            degradation_reasons=[reason],
        )

    def _source_from_mapping(
        self,
        payload: dict[str, Any],
        *,
        freshness: dict[str, Any],
    ) -> AccountHealthTelemetrySourceSummary:
        source_name = str(payload.get("source_name") or payload.get("name") or payload.get("source") or "unknown")
        return self._build_source(
            source_name=source_name,
            source_type=str(payload.get("source_type") or payload.get("type") or "runtime_history"),
            payload=payload,
            freshness=freshness,
            absent_reason="SOURCE_DECLARED_ABSENT",
        )

    def _source_from_summary(
        self,
        *,
        source_name: str,
        payload: dict[str, Any],
        freshness: dict[str, Any],
    ) -> AccountHealthTelemetrySourceSummary:
        if not payload:
            return AccountHealthTelemetrySourceSummary(
                source_name=source_name,
                source_type="account_health_optional_summary",
                source_status="ABSENT",
                record_count=0,
                freshness_status="absent",
                latest_timestamp=None,
                evidence_ref=None,
                reason_codes=["OPTIONAL_TELEMETRY_NOT_PROVIDED"],
            )
        return self._build_source(
            source_name=source_name,
            source_type=str(payload.get("source_type") or "account_health_optional_summary"),
            payload=payload,
            freshness=freshness,
            absent_reason="SUMMARY_EMPTY_OR_UNAVAILABLE",
        )

    def _build_source(
        self,
        *,
        source_name: str,
        source_type: str,
        payload: dict[str, Any],
        freshness: dict[str, Any],
        absent_reason: str,
    ) -> AccountHealthTelemetrySourceSummary:
        record_count = self._record_count(payload)
        explicitly_available = bool(payload.get("available")) if "available" in payload else None
        source_status = self._normalize_source_status(payload.get("source_status") or payload.get("status"))
        freshness_status = self._freshness_for(source_name=source_name, payload=payload, freshness=freshness)
        reason_codes = [str(item) for item in list(payload.get("reason_codes") or [])]

        if source_status is None:
            if explicitly_available is False:
                source_status = "ABSENT"
                reason_codes.append(absent_reason)
            elif freshness_status == "stale":
                source_status = "STALE"
            elif record_count > 0 or explicitly_available is True:
                source_status = "REAL"
                if record_count == 0:
                    reason_codes.append("ZERO_RECORDS_REPORTED")
            else:
                source_status = "DEGRADED"
                reason_codes.append("SOURCE_PRESENT_WITHOUT_RECORD_EVIDENCE")

        if source_status == "REAL" and freshness_status == "stale":
            source_status = "STALE"
        if source_status == "ABSENT":
            freshness_status = "absent"
        elif freshness_status == "absent":
            freshness_status = "unknown"

        return AccountHealthTelemetrySourceSummary(
            source_name=source_name,
            source_type=source_type,
            source_status=source_status,
            record_count=record_count,
            freshness_status=freshness_status,
            latest_timestamp=self._optional_str(payload.get("latest_timestamp") or payload.get("updated_at")),
            evidence_ref=self._optional_str(payload.get("evidence_ref") or payload.get("path") or payload.get("source_ref")),
            reason_codes=sorted(set(reason_codes)),
        )

    def _legacy_scalar_source(self, data: Any) -> AccountHealthTelemetrySourceSummary:
        reason_codes = ["LEGACY_SCALAR_INPUTS_AVAILABLE"]
        if not getattr(data, "telemetry_sources", None) and not any(
            self._mapping(getattr(data, attr_name, {})) for attr_name in _CANONICAL_OPTIONAL_SOURCES.values()
        ):
            reason_codes.append("SOURCE_LINEAGE_NOT_PROVIDED")
        return AccountHealthTelemetrySourceSummary(
            source_name="legacy_scalar_inputs",
            source_type="account_health_input",
            source_status="REAL",
            record_count=4,
            freshness_status="unknown",
            latest_timestamp=None,
            evidence_ref=None,
            reason_codes=sorted(reason_codes),
        )

    def _available_signals(self, *, data: Any, sources: list[AccountHealthTelemetrySourceSummary]) -> list[str]:
        signals = {
            "recent_publish_count",
            "recent_format_repetition_ratio",
            "recent_views_drop_ratio",
            "recent_low_performance_streak",
        }
        for source in sources:
            if source.source_status in {"REAL", "STALE"}:
                signals.add(source.source_name)
        return sorted(signals)

    def _missing_signals(self, sources: list[AccountHealthTelemetrySourceSummary]) -> list[str]:
        return sorted(
            source.source_name
            for source in sources
            if source.source_status == "ABSENT"
        )

    def _degradation_reasons(
        self,
        *,
        distribution: dict[str, int],
        explicit_source_count: int,
        sources: list[AccountHealthTelemetrySourceSummary],
    ) -> list[str]:
        reasons: list[str] = []
        if distribution["ABSENT"] > 0:
            reasons.append("MISSING_OPTIONAL_TELEMETRY")
        if distribution["STALE"] > 0:
            reasons.append("STALE_TELEMETRY_PRESENT")
        if distribution["DEGRADED"] > 0:
            reasons.append("DEGRADED_TELEMETRY_PRESENT")
        if explicit_source_count == 0:
            reasons.append("NO_EXPLICIT_TELEMETRY_SOURCES")
        if any("SOURCE_LINEAGE_NOT_PROVIDED" in source.reason_codes for source in sources):
            reasons.append("LEGACY_SCALAR_INPUT_ONLY")
        return sorted(set(reasons))

    def _status_distribution(self, sources: list[AccountHealthTelemetrySourceSummary]) -> dict[str, int]:
        distribution = {"REAL": 0, "ABSENT": 0, "STALE": 0, "DEGRADED": 0}
        for source in sources:
            distribution[source.source_status] = distribution.get(source.source_status, 0) + 1
        return distribution

    def _dominant_status(self, distribution: dict[str, int]) -> str:
        return sorted(distribution.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def _freshness_for(
        self,
        *,
        source_name: str,
        payload: dict[str, Any],
        freshness: dict[str, Any],
    ) -> str:
        value = payload.get("freshness_status") or payload.get("freshness")
        if value is None and source_name in freshness:
            value = freshness[source_name]
        if isinstance(value, dict):
            value = value.get("freshness_status") or value.get("status")
        return self._normalize_freshness(value)

    def _normalize_freshness(self, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"fresh", "current", "valid"}:
            return "fresh"
        if normalized in {"stale", "expired", "old"}:
            return "stale"
        if normalized in {"absent", "missing", "not_available"}:
            return "absent"
        if normalized in {"degraded", "low_signal"}:
            return "unknown"
        return "unknown"

    def _normalize_source_status(self, value: Any) -> str | None:
        normalized = str(value or "").strip().upper()
        if normalized in {"REAL", "AVAILABLE", "PRESENT", "OK"}:
            return "REAL"
        if normalized in {"ABSENT", "MISSING", "NOT_AVAILABLE"}:
            return "ABSENT"
        if normalized in {"STALE", "EXPIRED", "OLD"}:
            return "STALE"
        if normalized in {"DEGRADED", "LOW_SIGNAL", "PARTIAL"}:
            return "DEGRADED"
        return None

    def _record_count(self, payload: dict[str, Any]) -> int:
        for key in ("record_count", "sample_size", "count"):
            if key in payload:
                return max(0, self._safe_int(payload.get(key)))
        records = payload.get("records")
        if isinstance(records, list):
            return len(records)
        return 0

    def _mapping(self, value: Any) -> dict[str, Any]:
        return dict(value) if isinstance(value, dict) else {}

    def _safe_int(self, value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _optional_str(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
