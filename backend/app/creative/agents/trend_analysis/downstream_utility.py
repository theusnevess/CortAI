from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import TrendProfile


@dataclass(frozen=True)
class TrendFieldUtility:
    field_name: str
    value_present: bool
    primary_consumers: tuple[str, ...] = ()
    strategy_relevance: str = "none"
    asset_relevance: str = "none"
    script_relevance: str = "none"
    editor_relevance: str = "none"
    interpretation_mode: str = "low_utility"
    authority_level: str = "none"
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "value_present": self.value_present,
            "primary_consumers": list(self.primary_consumers),
            "strategy_relevance": self.strategy_relevance,
            "asset_relevance": self.asset_relevance,
            "script_relevance": self.script_relevance,
            "editor_relevance": self.editor_relevance,
            "interpretation_mode": self.interpretation_mode,
            "authority_level": self.authority_level,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class TrendDownstreamUtilitySummary:
    utility_complete: bool
    material_fields: tuple[str, ...] = ()
    advisory_fields: tuple[str, ...] = ()
    audit_only_fields: tuple[str, ...] = ()
    low_utility_fields: tuple[str, ...] = ()
    consumer_summary: dict[str, dict[str, Any]] = field(default_factory=dict)
    boundary_statement: str = "Trend provides context only; Strategy remains the control layer."
    utility_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "utility_complete": self.utility_complete,
            "material_fields": list(self.material_fields),
            "advisory_fields": list(self.advisory_fields),
            "audit_only_fields": list(self.audit_only_fields),
            "low_utility_fields": list(self.low_utility_fields),
            "consumer_summary": {name: dict(payload) for name, payload in self.consumer_summary.items()},
            "boundary_statement": self.boundary_statement,
            "utility_trace": dict(self.utility_trace),
        }


@dataclass
class TrendDownstreamUtilityMapper:
    field_rules: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "dominant_hooks": {
                "strategy_relevance": "high",
                "asset_relevance": "medium",
                "script_relevance": "high",
                "editor_relevance": "low",
                "interpretation_mode": "material_context",
                "primary_consumers": ("strategy", "script", "asset"),
            },
            "pacing": {
                "strategy_relevance": "high",
                "asset_relevance": "low",
                "script_relevance": "medium",
                "editor_relevance": "medium",
                "interpretation_mode": "material_context",
                "primary_consumers": ("strategy", "script", "editor"),
            },
            "visual_style": {
                "strategy_relevance": "medium",
                "asset_relevance": "high",
                "script_relevance": "low",
                "editor_relevance": "medium",
                "interpretation_mode": "material_context",
                "primary_consumers": ("asset", "editor", "strategy"),
            },
            "text_style": {
                "strategy_relevance": "low",
                "asset_relevance": "none",
                "script_relevance": "medium",
                "editor_relevance": "medium",
                "interpretation_mode": "advisory_context",
                "primary_consumers": ("script", "editor"),
            },
            "avg_duration": {
                "strategy_relevance": "medium",
                "asset_relevance": "none",
                "script_relevance": "medium",
                "editor_relevance": "medium",
                "interpretation_mode": "advisory_context",
                "primary_consumers": ("strategy", "script", "editor"),
            },
            "region": {
                "strategy_relevance": "low",
                "asset_relevance": "none",
                "script_relevance": "none",
                "editor_relevance": "none",
                "interpretation_mode": "advisory_context",
                "primary_consumers": ("strategy",),
            },
            "sample_size": {
                "strategy_relevance": "none",
                "asset_relevance": "none",
                "script_relevance": "none",
                "editor_relevance": "none",
                "interpretation_mode": "audit_only",
                "primary_consumers": (),
            },
            "updated_at": {
                "strategy_relevance": "none",
                "asset_relevance": "none",
                "script_relevance": "none",
                "editor_relevance": "none",
                "interpretation_mode": "audit_only",
                "primary_consumers": (),
            },
            "valid_until": {
                "strategy_relevance": "none",
                "asset_relevance": "none",
                "script_relevance": "none",
                "editor_relevance": "none",
                "interpretation_mode": "audit_only",
                "primary_consumers": (),
            },
            "evidence": {
                "strategy_relevance": "none",
                "asset_relevance": "none",
                "script_relevance": "none",
                "editor_relevance": "none",
                "interpretation_mode": "audit_only",
                "primary_consumers": (),
            },
            "trend_source": {
                "strategy_relevance": "none",
                "asset_relevance": "none",
                "script_relevance": "none",
                "editor_relevance": "none",
                "interpretation_mode": "audit_only",
                "primary_consumers": (),
            },
        }
    )

    def map(
        self,
        *,
        trend_profile: TrendProfile,
        provenance: dict[str, Any] | None,
        confidence_calibration: dict[str, Any] | None,
        validity: dict[str, Any] | None,
        fallback_used: bool,
    ) -> TrendDownstreamUtilitySummary:
        profile_payload = trend_profile.to_dict()
        provenance_payload = dict(provenance or {})
        field_provenance = dict(provenance_payload.get("field_provenance") or {})
        confidence_payload = dict(confidence_calibration or {})
        validity_payload = dict(validity or {})
        field_utilities = tuple(
            self._field_utility(
                field_name=field_name,
                value=profile_payload.get(field_name),
                field_provenance=dict(field_provenance.get(field_name) or {}),
                confidence_payload=confidence_payload,
                validity_payload=validity_payload,
                fallback_used=fallback_used,
            )
            for field_name in self.field_rules
            if field_name in profile_payload
        )
        material_fields = tuple(item.field_name for item in field_utilities if item.interpretation_mode == "material_context")
        advisory_fields = tuple(item.field_name for item in field_utilities if item.interpretation_mode == "advisory_context")
        audit_only_fields = tuple(item.field_name for item in field_utilities if item.interpretation_mode == "audit_only")
        low_utility_fields = tuple(item.field_name for item in field_utilities if item.interpretation_mode == "low_utility")
        return TrendDownstreamUtilitySummary(
            utility_complete=self._utility_complete(field_utilities=field_utilities),
            material_fields=material_fields,
            advisory_fields=advisory_fields,
            audit_only_fields=audit_only_fields,
            low_utility_fields=low_utility_fields,
            consumer_summary=self._consumer_summary(field_utilities=field_utilities),
            utility_trace={
                "field_utilities": [item.to_dict() for item in field_utilities],
                "fallback_used": fallback_used,
                "provenance_complete": bool(provenance_payload.get("provenance_complete", False)),
                "confidence_level": confidence_payload.get("confidence_level"),
                "confidence_meaning": confidence_payload.get("confidence_meaning"),
                "validity_status": validity_payload.get("validity_status"),
                "authority_cap": "advisory",
            },
        )

    def _field_utility(
        self,
        *,
        field_name: str,
        value: Any,
        field_provenance: dict[str, Any],
        confidence_payload: dict[str, Any],
        validity_payload: dict[str, Any],
        fallback_used: bool,
    ) -> TrendFieldUtility:
        rule = dict(self.field_rules.get(field_name) or {})
        value_present = self._value_present(value)
        interpretation_mode = str(rule.get("interpretation_mode") or "low_utility")
        authority_level = "advisory" if interpretation_mode in {"material_context", "advisory_context"} and value_present else "none"
        if not value_present:
            interpretation_mode = "low_utility"
            authority_level = "none"
        elif self._should_degrade_utility(
            field_provenance=field_provenance,
            confidence_payload=confidence_payload,
            validity_payload=validity_payload,
            fallback_used=fallback_used,
        ) and interpretation_mode == "material_context":
            interpretation_mode = "advisory_context"
        return TrendFieldUtility(
            field_name=field_name,
            value_present=value_present,
            primary_consumers=tuple(rule.get("primary_consumers") or ()),
            strategy_relevance=str(rule.get("strategy_relevance") or "none"),
            asset_relevance=str(rule.get("asset_relevance") or "none"),
            script_relevance=str(rule.get("script_relevance") or "none"),
            editor_relevance=str(rule.get("editor_relevance") or "none"),
            interpretation_mode=interpretation_mode,
            authority_level=authority_level,
            rationale=self._rationale(
                field_name=field_name,
                interpretation_mode=interpretation_mode,
                authority_level=authority_level,
                field_provenance=field_provenance,
                fallback_used=fallback_used,
            ),
        )

    def _should_degrade_utility(
        self,
        *,
        field_provenance: dict[str, Any],
        confidence_payload: dict[str, Any],
        validity_payload: dict[str, Any],
        fallback_used: bool,
    ) -> bool:
        if fallback_used:
            return True
        if str(field_provenance.get("support_level") or "") in {"fallback", "unknown", "weak"}:
            return True
        if str(confidence_payload.get("confidence_level") or "") == "low":
            return True
        if str(validity_payload.get("validity_status") or "") in {"degraded", "invalid"}:
            return True
        return False

    def _consumer_summary(self, *, field_utilities: tuple[TrendFieldUtility, ...]) -> dict[str, dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        for consumer in ("strategy", "asset", "script", "editor"):
            relevant_fields = []
            material_fields = []
            for item in field_utilities:
                relevance = getattr(item, f"{consumer}_relevance")
                if relevance != "none" and item.value_present:
                    relevant_fields.append(item.field_name)
                if item.interpretation_mode == "material_context" and relevance in {"medium", "high"}:
                    material_fields.append(item.field_name)
            summary[consumer] = {
                "relevant_fields": relevant_fields,
                "material_fields": material_fields,
                "interpretation": (
                    "Context annotation only. This does not create downstream authority or behavioral change."
                ),
            }
        return summary

    def _utility_complete(self, *, field_utilities: tuple[TrendFieldUtility, ...]) -> bool:
        utility_fields = {item.field_name for item in field_utilities}
        return set(self.field_rules).issubset(utility_fields)

    def _rationale(
        self,
        *,
        field_name: str,
        interpretation_mode: str,
        authority_level: str,
        field_provenance: dict[str, Any],
        fallback_used: bool,
    ) -> str:
        support_level = str(field_provenance.get("support_level") or "unknown")
        fallback_note = " Fallback context reduces utility interpretation." if fallback_used else ""
        return (
            f"Field {field_name} is classified as {interpretation_mode} with {authority_level} authority. "
            f"Provenance support is {support_level}.{fallback_note}"
        )

    def _value_present(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, set, dict)):
            return bool(value)
        return True
