from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import TrendProfile


@dataclass(frozen=True)
class TrendFieldChange:
    field_name: str
    previous_value: Any
    current_value: Any
    changed: bool
    change_type: str
    severity: str
    operationally_significant: bool
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "changed": self.changed,
            "change_type": self.change_type,
            "severity": self.severity,
            "operationally_significant": self.operationally_significant,
            "rationale": self.rationale,
        }

    def to_legacy_change(self) -> dict[str, Any]:
        return {
            "field": self.field_name,
            "old": self.previous_value,
            "new": self.current_value,
            "significance": self._legacy_significance(),
        }

    def _legacy_significance(self) -> str:
        if self.severity == "strong":
            return "high"
        if self.severity == "moderate":
            return "medium"
        if self.severity == "weak":
            return "low"
        return "none"


@dataclass(frozen=True)
class TrendShiftAnalysis:
    baseline_available: bool
    shift_detected: bool
    shift_severity: str
    operational_significance: str
    change_count: int
    meaningful_change_count: int
    field_changes: tuple[TrendFieldChange, ...] = ()
    weak_variations: tuple[TrendFieldChange, ...] = ()
    meaningful_shifts: tuple[TrendFieldChange, ...] = ()
    rationale: tuple[str, ...] = ()
    baseline_summary: dict[str, Any] = field(default_factory=dict)
    current_summary: dict[str, Any] = field(default_factory=dict)
    comparison_source: str = ""

    def to_dict(self) -> dict[str, Any]:
        legacy_changes = [change.to_legacy_change() for change in self.meaningful_shifts]
        return {
            "baseline_available": self.baseline_available,
            "shift_detected": self.shift_detected,
            "shift_severity": self.shift_severity,
            "operational_significance": self.operational_significance,
            "change_count": self.change_count,
            "meaningful_change_count": self.meaningful_change_count,
            "field_changes": [change.to_dict() for change in self.field_changes],
            "weak_variations": [change.to_dict() for change in self.weak_variations],
            "meaningful_shifts": [change.to_dict() for change in self.meaningful_shifts],
            "rationale": list(self.rationale),
            "baseline_summary": dict(self.baseline_summary),
            "current_summary": dict(self.current_summary),
            "comparison_source": self.comparison_source,
            "changes": legacy_changes,
        }


@dataclass
class TrendShiftAnalyzer:
    fields_to_compare: tuple[str, ...] = (
        "dominant_hooks",
        "avg_duration",
        "pacing",
        "visual_style",
        "text_style",
        "trend_source",
        "region",
        "sample_size",
    )

    def analyze(
        self,
        *,
        current_profile: TrendProfile,
        baseline_profile: TrendProfile | None,
    ) -> TrendShiftAnalysis:
        current_summary = self._summary(current_profile)
        if baseline_profile is None:
            return TrendShiftAnalysis(
                baseline_available=False,
                shift_detected=False,
                shift_severity="none",
                operational_significance="none",
                change_count=0,
                meaningful_change_count=0,
                field_changes=(),
                weak_variations=(),
                meaningful_shifts=(),
                rationale=("NO_BASELINE_AVAILABLE",),
                baseline_summary={},
                current_summary=current_summary,
                comparison_source="",
            )

        baseline_summary = self._summary(baseline_profile)
        field_changes = tuple(
            self._compare_field(
                field_name=field_name,
                previous_value=baseline_summary.get(field_name),
                current_value=current_summary.get(field_name),
            )
            for field_name in self.fields_to_compare
            if field_name in current_summary
        )
        changed = tuple(change for change in field_changes if change.changed)
        weak_variations = tuple(change for change in changed if change.severity == "weak")
        meaningful_shifts = tuple(change for change in changed if change.severity in {"moderate", "strong"})
        shift_severity = self._overall_severity(meaningful_shifts=meaningful_shifts, weak_variations=weak_variations)
        operational_significance = self._operational_significance(
            shift_severity=shift_severity,
            meaningful_count=len(meaningful_shifts),
            weak_count=len(weak_variations),
        )
        return TrendShiftAnalysis(
            baseline_available=True,
            shift_detected=bool(meaningful_shifts),
            shift_severity=shift_severity,
            operational_significance=operational_significance,
            change_count=len(changed),
            meaningful_change_count=len(meaningful_shifts),
            field_changes=field_changes,
            weak_variations=weak_variations,
            meaningful_shifts=meaningful_shifts,
            rationale=tuple(
                self._rationale(
                    shift_severity=shift_severity,
                    operational_significance=operational_significance,
                    meaningful_count=len(meaningful_shifts),
                    weak_count=len(weak_variations),
                )
            ),
            baseline_summary=baseline_summary,
            current_summary=current_summary,
            comparison_source=baseline_profile.trend_source,
        )

    def _compare_field(self, *, field_name: str, previous_value: Any, current_value: Any) -> TrendFieldChange:
        if previous_value is None and current_value is None:
            return self._change(
                field_name=field_name,
                previous_value=previous_value,
                current_value=current_value,
                changed=False,
                change_type="none",
                severity="none",
                rationale=f"Field {field_name} is missing in both baseline and current profile.",
            )
        if previous_value is None:
            return self._change(
                field_name=field_name,
                previous_value=previous_value,
                current_value=current_value,
                changed=True,
                change_type="missing_previous",
                severity="moderate",
                rationale=f"Field {field_name} has no baseline value.",
            )
        if current_value is None:
            return self._change(
                field_name=field_name,
                previous_value=previous_value,
                current_value=current_value,
                changed=True,
                change_type="missing_current",
                severity="moderate",
                rationale=f"Field {field_name} is missing from current profile.",
            )
        if previous_value == current_value:
            return self._change(
                field_name=field_name,
                previous_value=previous_value,
                current_value=current_value,
                changed=False,
                change_type="none",
                severity="none",
                rationale=f"Field {field_name} did not change.",
            )
        if isinstance(previous_value, list) and isinstance(current_value, list):
            return self._compare_list_field(
                field_name=field_name,
                previous_value=previous_value,
                current_value=current_value,
            )
        return self._compare_scalar_field(
            field_name=field_name,
            previous_value=previous_value,
            current_value=current_value,
        )

    def _compare_list_field(
        self,
        *,
        field_name: str,
        previous_value: list[Any],
        current_value: list[Any],
    ) -> TrendFieldChange:
        previous_set = set(previous_value)
        current_set = set(current_value)
        if previous_set == current_set:
            return self._change(
                field_name=field_name,
                previous_value=previous_value,
                current_value=current_value,
                changed=True,
                change_type="list_reordered",
                severity="weak",
                rationale=f"Field {field_name} changed ordering but kept the same values.",
            )
        added = current_set - previous_set
        removed = previous_set - current_set
        change_type = "list_added" if added and not removed else "list_removed" if removed and not added else "value_change"
        overlap = len(previous_set.intersection(current_set))
        largest_size = max(len(previous_set), len(current_set), 1)
        changed_ratio = 1.0 - (overlap / largest_size)
        if field_name == "dominant_hooks" and changed_ratio >= 0.5:
            severity = "strong"
        elif field_name == "dominant_hooks":
            severity = "moderate"
        else:
            severity = "moderate" if changed_ratio >= 0.34 else "weak"
        return self._change(
            field_name=field_name,
            previous_value=previous_value,
            current_value=current_value,
            changed=True,
            change_type=change_type,
            severity=severity,
            rationale=f"Field {field_name} list values changed with changed_ratio={round(changed_ratio, 4)}.",
        )

    def _compare_scalar_field(self, *, field_name: str, previous_value: Any, current_value: Any) -> TrendFieldChange:
        severity = {
            "pacing": "moderate",
            "avg_duration": "moderate",
            "visual_style": "moderate",
            "text_style": "weak",
            "trend_source": self._trend_source_severity(str(previous_value), str(current_value)),
            "region": "strong",
            "sample_size": self._sample_size_severity(previous_value=previous_value, current_value=current_value),
        }.get(field_name, "weak")
        return self._change(
            field_name=field_name,
            previous_value=previous_value,
            current_value=current_value,
            changed=True,
            change_type="value_change",
            severity=severity,
            rationale=f"Field {field_name} changed from baseline to current profile.",
        )

    def _trend_source_severity(self, previous_value: str, current_value: str) -> str:
        if "safe_default" in {previous_value, current_value}:
            return "strong"
        if previous_value != current_value:
            return "moderate"
        return "none"

    def _sample_size_severity(self, *, previous_value: Any, current_value: Any) -> str:
        try:
            previous = int(previous_value)
            current = int(current_value)
        except (TypeError, ValueError):
            return "weak"
        delta = abs(current - previous)
        if delta >= 20:
            return "moderate"
        if delta >= 5:
            return "weak"
        return "weak"

    def _overall_severity(
        self,
        *,
        meaningful_shifts: tuple[TrendFieldChange, ...],
        weak_variations: tuple[TrendFieldChange, ...],
    ) -> str:
        if not meaningful_shifts:
            return "weak" if weak_variations else "none"
        if any(change.severity == "strong" for change in meaningful_shifts):
            return "strong"
        if len(meaningful_shifts) >= 3:
            return "strong"
        return "moderate"

    def _operational_significance(self, *, shift_severity: str, meaningful_count: int, weak_count: int) -> str:
        if shift_severity == "none":
            return "none"
        if shift_severity == "weak":
            return "low" if weak_count else "none"
        if shift_severity == "moderate":
            return "high" if meaningful_count >= 3 else "medium"
        if shift_severity == "strong":
            return "high"
        return "none"

    def _rationale(
        self,
        *,
        shift_severity: str,
        operational_significance: str,
        meaningful_count: int,
        weak_count: int,
    ) -> list[str]:
        if shift_severity == "none":
            return ["NO_MEANINGFUL_SHIFT_DETECTED"]
        return [
            (
                f"Shift classified as {shift_severity} from {meaningful_count} meaningful changes "
                f"and {weak_count} weak variations."
            ),
            f"Operational significance is advisory-only and classified as {operational_significance}.",
            "Shift analysis is retrospective and does not forecast performance or future trend movement.",
        ]

    def _change(
        self,
        *,
        field_name: str,
        previous_value: Any,
        current_value: Any,
        changed: bool,
        change_type: str,
        severity: str,
        rationale: str,
    ) -> TrendFieldChange:
        return TrendFieldChange(
            field_name=field_name,
            previous_value=previous_value,
            current_value=current_value,
            changed=changed,
            change_type=change_type,
            severity=severity,
            operationally_significant=severity in {"moderate", "strong"},
            rationale=rationale,
        )

    def _summary(self, profile: TrendProfile) -> dict[str, Any]:
        payload = profile.to_dict()
        return {
            field_name: payload.get(field_name)
            for field_name in self.fields_to_compare
            if field_name in payload
        }
