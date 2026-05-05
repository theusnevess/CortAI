from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.creative.contracts.creative_pack import TrendProfile


@dataclass(frozen=True)
class TrendFreshnessState:
    source_id: str
    source_class: str
    captured_at: datetime | None
    age_seconds: int | None
    freshness_status: str
    within_valid_window: bool
    reason_code: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_class": self.source_class,
            "captured_at": None if self.captured_at is None else self._to_iso(self.captured_at),
            "age_seconds": self.age_seconds,
            "freshness_status": self.freshness_status,
            "within_valid_window": self.within_valid_window,
            "reason_code": self.reason_code,
            "rationale": self.rationale,
        }

    def _to_iso(self, value: datetime) -> str:
        return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class TrendValiditySummary:
    profile_valid: bool
    fresh_sources_count: int
    stale_sources_count: int
    expired_sources_count: int
    missing_timestamp_count: int
    uses_cache: bool
    cache_usage_mode: str
    fallback_due_to_freshness: bool
    validity_status: str
    rationale: str
    cache_allowed: bool = True
    aging_sources_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_valid": self.profile_valid,
            "fresh_sources_count": self.fresh_sources_count,
            "aging_sources_count": self.aging_sources_count,
            "stale_sources_count": self.stale_sources_count,
            "expired_sources_count": self.expired_sources_count,
            "missing_timestamp_count": self.missing_timestamp_count,
            "uses_cache": self.uses_cache,
            "cache_usage_mode": self.cache_usage_mode,
            "cache_allowed": self.cache_allowed,
            "fallback_due_to_freshness": self.fallback_due_to_freshness,
            "validity_status": self.validity_status,
            "rationale": self.rationale,
        }


@dataclass
class TrendFreshnessEvaluator:
    fresh_max_seconds: int = 24 * 60 * 60
    aging_max_seconds: int = 72 * 60 * 60
    stale_max_seconds: int = 7 * 24 * 60 * 60

    def evaluate_sources(
        self,
        *,
        source_governance: dict[str, Any] | None,
        current_time: datetime,
    ) -> tuple[TrendFreshnessState, ...]:
        governance = dict(source_governance or {})
        source_decisions = [
            *list(governance.get("accepted_sources") or []),
            *list(governance.get("ignored_sources") or []),
            *list(governance.get("rejected_sources") or []),
        ]
        return tuple(
            self.evaluate_source(source=dict(source), current_time=current_time)
            for source in source_decisions
        )

    def evaluate_source(self, *, source: dict[str, Any], current_time: datetime) -> TrendFreshnessState:
        metadata = dict(source.get("metadata") or {})
        captured_at = self._parse_first_timestamp(
            metadata.get("captured_at"),
            metadata.get("collected_at"),
            metadata.get("updated_at"),
            metadata.get("timestamp"),
        )
        source_id = str(source.get("source_id") or "")
        source_class = str(source.get("source_class") or "unknown")
        if captured_at is None:
            return TrendFreshnessState(
                source_id=source_id,
                source_class=source_class,
                captured_at=None,
                age_seconds=None,
                freshness_status="missing_timestamp",
                within_valid_window=False,
                reason_code="SOURCE_MISSING_TIMESTAMP",
                rationale=f"Source {source_id or source_class} did not provide a timestamp.",
            )

        age_seconds = int((current_time.astimezone(timezone.utc) - captured_at).total_seconds())
        status = self._classify_age(age_seconds=age_seconds)
        valid_until = self._parse_first_timestamp(metadata.get("valid_until"))
        within_valid_window = current_time.astimezone(timezone.utc) <= valid_until if valid_until is not None else status not in {"expired"}
        reason_code = {
            "fresh": "SOURCE_FRESH",
            "aging": "SOURCE_AGING",
            "stale": "SOURCE_STALE",
            "expired": "SOURCE_EXPIRED",
        }[status]
        return TrendFreshnessState(
            source_id=source_id,
            source_class=source_class,
            captured_at=captured_at,
            age_seconds=age_seconds,
            freshness_status=status,
            within_valid_window=within_valid_window,
            reason_code=reason_code,
            rationale=f"Source {source_id or source_class} is {status} based on captured_at age.",
        )

    def build_validity_summary(
        self,
        *,
        trend_profile: TrendProfile,
        source_governance: dict[str, Any] | None,
        freshness_states: tuple[TrendFreshnessState, ...],
        fallback_used: bool,
        fallback_reason: str,
        cache_usage_mode: str,
        decision_trace: list[dict[str, Any]] | None = None,
    ) -> TrendValiditySummary:
        governance = dict(source_governance or {})
        accepted_ids = {
            str(source.get("source_id") or "")
            for source in list(governance.get("accepted_sources") or [])
        }
        selected_source_class = str(governance.get("selected_source_class") or "")
        policy = dict(dict(governance.get("governance_trace") or {}).get("policy") or {})
        cache_allowed = bool(policy.get("allow_cache", True))
        accepted_states = tuple(
            state for state in freshness_states if state.source_id in accepted_ids
        )
        if not accepted_states:
            accepted_states = freshness_states

        counts = self._status_counts(accepted_states)
        uses_cache = cache_usage_mode in {"primary", "fallback"} or selected_source_class == "validated_cache"
        fallback_due_to_freshness = self._fallback_due_to_freshness(
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            decision_trace=decision_trace or [],
        )
        validity_status = self._validity_status(
            trend_profile=trend_profile,
            selected_source_class=selected_source_class,
            accepted_states=accepted_states,
            counts=counts,
            fallback_used=fallback_used,
        )
        return TrendValiditySummary(
            profile_valid=validity_status in {"valid", "weak"},
            fresh_sources_count=counts["fresh"],
            aging_sources_count=counts["aging"],
            stale_sources_count=counts["stale"],
            expired_sources_count=counts["expired"],
            missing_timestamp_count=counts["missing_timestamp"],
            uses_cache=uses_cache,
            cache_usage_mode=cache_usage_mode,
            cache_allowed=cache_allowed,
            fallback_due_to_freshness=fallback_due_to_freshness,
            validity_status=validity_status,
            rationale=self._validity_rationale(
                validity_status=validity_status,
                selected_source_class=selected_source_class,
                counts=counts,
                fallback_used=fallback_used,
                fallback_reason=fallback_reason,
            ),
        )

    def evaluate(
        self,
        *,
        trend_profile: TrendProfile,
        source_governance: dict[str, Any] | None,
        current_time: datetime,
        fallback_used: bool,
        fallback_reason: str,
        cache_usage_mode: str,
        decision_trace: list[dict[str, Any]] | None = None,
    ) -> tuple[tuple[TrendFreshnessState, ...], TrendValiditySummary]:
        states = self.evaluate_sources(source_governance=source_governance, current_time=current_time)
        validity = self.build_validity_summary(
            trend_profile=trend_profile,
            source_governance=source_governance,
            freshness_states=states,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
            cache_usage_mode=cache_usage_mode,
            decision_trace=decision_trace,
        )
        return states, validity

    def _classify_age(self, *, age_seconds: int) -> str:
        if age_seconds <= self.fresh_max_seconds:
            return "fresh"
        if age_seconds <= self.aging_max_seconds:
            return "aging"
        if age_seconds <= self.stale_max_seconds:
            return "stale"
        return "expired"

    def _validity_status(
        self,
        *,
        trend_profile: TrendProfile,
        selected_source_class: str,
        accepted_states: tuple[TrendFreshnessState, ...],
        counts: dict[str, int],
        fallback_used: bool,
    ) -> str:
        if selected_source_class == "safe_default" or trend_profile.trend_source == "safe_default":
            return "invalid"
        if not accepted_states:
            return "invalid"
        if counts["expired"] == len(accepted_states) or counts["missing_timestamp"] == len(accepted_states):
            return "invalid"
        if counts["expired"] or counts["stale"] > counts["fresh"] + counts["aging"]:
            return "degraded"
        if counts["missing_timestamp"] or counts["stale"] or counts["aging"] or fallback_used:
            return "weak"
        if counts["fresh"] > 0:
            return "valid"
        return "invalid"

    def _validity_rationale(
        self,
        *,
        validity_status: str,
        selected_source_class: str,
        counts: dict[str, int],
        fallback_used: bool,
        fallback_reason: str,
    ) -> str:
        if validity_status == "valid":
            return "Trend profile is supported by fresh governed sources."
        if validity_status == "weak":
            return "Trend profile has usable temporal evidence but includes aging, stale, missing, or fallback indicators."
        if validity_status == "degraded":
            return "Trend profile is temporally degraded because stale or expired signals are material."
        if selected_source_class == "safe_default":
            return "Trend profile uses safe_default fallback and has no real temporal evidence."
        if fallback_used:
            return f"Trend profile fallback path is active: {fallback_reason}."
        return f"Trend profile has insufficient usable temporal evidence: {counts}."

    def _fallback_due_to_freshness(
        self,
        *,
        fallback_used: bool,
        fallback_reason: str,
        decision_trace: list[dict[str, Any]],
    ) -> bool:
        if not fallback_used:
            return False
        if "FRESH" in fallback_reason or "STALE" in fallback_reason or "EXPIR" in fallback_reason:
            return True
        temporal_markers = {"TREND_STALE", "TREND_NEAR_EXPIRY"}
        for item in decision_trace:
            errors = set(str(value) for value in list(item.get("errors") or []))
            warnings = set(str(value) for value in list(item.get("warnings") or []))
            if errors.intersection(temporal_markers) or warnings.intersection(temporal_markers):
                return True
        return False

    def _status_counts(self, states: tuple[TrendFreshnessState, ...]) -> dict[str, int]:
        counts = {
            "fresh": 0,
            "aging": 0,
            "stale": 0,
            "expired": 0,
            "missing_timestamp": 0,
        }
        for state in states:
            counts[state.freshness_status] = counts.get(state.freshness_status, 0) + 1
        return counts

    def _parse_first_timestamp(self, *values: Any) -> datetime | None:
        for value in values:
            parsed = self._parse_timestamp(value)
            if parsed is not None:
                return parsed
        return None

    def _parse_timestamp(self, value: Any) -> datetime | None:
        raw_value = str(value or "").strip()
        if not raw_value:
            return None
        try:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None
