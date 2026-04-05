from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.creative.contracts.creative_pack import TrendProfile


@dataclass(frozen=True)
class TrendValidationResult:
    decision: str
    valid: bool
    warnings: list[str]
    errors: list[str]
    overall_confidence: float
    freshness_state: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.decision,
            "valid": self.valid,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "overall_confidence": self.overall_confidence,
            "freshness_state": self.freshness_state,
        }


@dataclass
class TrendConfidenceScoringService:
    hold_floor: float = 0.45
    approve_floor: float = 0.65

    def overall_confidence(self, trend_profile: TrendProfile) -> float:
        if trend_profile.confidence_scores:
            raw_value = trend_profile.confidence_scores.get("overall")
            if raw_value is not None:
                return float(raw_value)
            return float(sum(trend_profile.confidence_scores.values()) / max(len(trend_profile.confidence_scores), 1))
        return 0.0


@dataclass
class TrendValidationService:
    confidence_service: TrendConfidenceScoringService = field(default_factory=TrendConfidenceScoringService)
    near_expiry_days: int = 2
    minimum_sample_size: int = 3

    def validate(self, *, trend_profile: TrendProfile, current_time: datetime) -> TrendValidationResult:
        warnings: list[str] = []
        errors: list[str] = []
        updated_at = self._parse_iso(trend_profile.updated_at, fallback=current_time)
        valid_until = self._parse_iso(trend_profile.valid_until, fallback=updated_at)

        if current_time > valid_until:
            errors.append("TREND_STALE")
            freshness_state = "stale"
        elif current_time + timedelta(days=self.near_expiry_days) > valid_until:
            warnings.append("TREND_NEAR_EXPIRY")
            freshness_state = "near_expiry"
        else:
            freshness_state = "fresh"

        if not trend_profile.trend_source.strip():
            errors.append("MISSING_TREND_SOURCE")
        if valid_until < updated_at:
            errors.append("INVALID_TEMPORAL_WINDOW")
        if not trend_profile.dominant_hooks:
            errors.append("MISSING_DOMINANT_HOOKS")

        legacy_profile = trend_profile.trend_source == "manual_file_legacy"
        if not trend_profile.evidence:
            if legacy_profile:
                warnings.append("NO_EVIDENCE_REFERENCES")
            else:
                errors.append("NO_EVIDENCE_REFERENCES")

        if trend_profile.sample_size < self.minimum_sample_size:
            if legacy_profile and trend_profile.sample_size <= 0:
                warnings.append("SAMPLE_SIZE_UNSPECIFIED")
            else:
                warnings.append("LOW_SAMPLE_SIZE")

        overall_confidence = round(self.confidence_service.overall_confidence(trend_profile), 4)
        if overall_confidence < self.confidence_service.hold_floor:
            errors.append("LOW_CONFIDENCE")
        elif overall_confidence < self.confidence_service.approve_floor:
            warnings.append("CONFIDENCE_BELOW_APPROVE_THRESHOLD")

        if errors:
            decision = "REJECT"
            valid = False
        elif warnings:
            decision = "HOLD"
            valid = True
        else:
            decision = "APPROVE"
            valid = True
        return TrendValidationResult(
            decision=decision,
            valid=valid,
            warnings=warnings,
            errors=errors,
            overall_confidence=overall_confidence,
            freshness_state=freshness_state,
        )

    def _parse_iso(self, value: str, *, fallback: datetime) -> datetime:
        normalized = (value or "").strip()
        if not normalized:
            return fallback
        return datetime.fromisoformat(normalized.replace("Z", "+00:00")).astimezone(fallback.tzinfo)
