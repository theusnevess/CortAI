from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import TrendProfile


@dataclass(frozen=True)
class TrendTraceAuditSummary:
    reconstructible: bool
    required_sections_present: bool
    source_governance_present: bool
    provenance_present: bool
    freshness_present: bool
    validity_present: bool
    confidence_calibration_present: bool
    shift_analysis_present: bool
    downstream_utility_present: bool
    fallback_visible: bool
    silent_failure_indicators: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "reconstructible": self.reconstructible,
            "required_sections_present": self.required_sections_present,
            "source_governance_present": self.source_governance_present,
            "provenance_present": self.provenance_present,
            "freshness_present": self.freshness_present,
            "validity_present": self.validity_present,
            "confidence_calibration_present": self.confidence_calibration_present,
            "shift_analysis_present": self.shift_analysis_present,
            "downstream_utility_present": self.downstream_utility_present,
            "fallback_visible": self.fallback_visible,
            "silent_failure_indicators": list(self.silent_failure_indicators),
        }


@dataclass
class TrendTraceBuilder:
    required_trace_sections: tuple[str, ...] = (
        "source_governance",
        "provenance",
        "freshness",
        "validity",
        "confidence_calibration",
        "shift_analysis",
        "downstream_utility",
    )
    source_governance_fields: tuple[str, ...] = (
        "policy_version",
        "policy_respected",
        "accepted_sources",
        "rejected_sources",
        "ignored_sources",
        "selected_source_class",
        "source_mix",
        "fallback_required",
        "fallback_reason",
    )
    provenance_fields: tuple[str, ...] = (
        "provenance_complete",
        "field_provenance",
        "evidence_references",
        "fallback_fields",
        "weakly_supported_fields",
        "unknown_source_fields",
    )
    freshness_fields: tuple[str, ...] = (
        "sources",
        "fresh_sources_count",
        "stale_sources_count",
        "expired_sources_count",
        "missing_timestamp_count",
    )
    validity_fields: tuple[str, ...] = (
        "profile_valid",
        "validity_status",
        "cache_usage_mode",
        "fallback_due_to_freshness",
        "rationale",
    )
    confidence_fields: tuple[str, ...] = (
        "confidence",
        "confidence_level",
        "components",
        "penalties",
        "rationale",
        "confidence_meaning",
    )
    shift_fields: tuple[str, ...] = (
        "baseline_available",
        "shift_detected",
        "shift_severity",
        "operational_significance",
        "field_changes",
        "weak_variations",
        "meaningful_shifts",
        "rationale",
    )
    downstream_fields: tuple[str, ...] = (
        "material_fields",
        "advisory_fields",
        "audit_only_fields",
        "low_utility_fields",
        "consumer_summary",
        "boundary_statement",
    )

    def build(
        self,
        *,
        trend_profile: TrendProfile,
        fallback: FallbackDecision | dict[str, Any] | None,
        validation_summary: dict[str, Any] | None,
        collector_trace: dict[str, Any] | None,
    ) -> dict[str, Any]:
        trace_payload = self._copy_payload(dict(collector_trace or {}))
        trace_payload.pop("trend_trace", None)
        validation_payload = self._copy_payload(dict(validation_summary or {}))
        fallback_payload = self._fallback_payload(fallback)

        source_governance = self._section_payload(
            trace_payload.get("source_governance"),
            fields=self.source_governance_fields,
        )
        provenance = self._section_payload(trace_payload.get("provenance"), fields=self.provenance_fields)
        freshness = self._section_payload(trace_payload.get("freshness"), fields=self.freshness_fields)
        validity = self._section_payload(trace_payload.get("validity"), fields=self.validity_fields)
        confidence_calibration = self._section_payload(
            trace_payload.get("confidence_calibration"),
            fields=self.confidence_fields,
        )
        shift_analysis = self._section_payload(trace_payload.get("shift_analysis"), fields=self.shift_fields)
        downstream_utility = self._section_payload(
            trace_payload.get("downstream_utility"),
            fields=self.downstream_fields,
        )
        fallback_summary = self._fallback_summary(
            fallback_payload=fallback_payload,
            trace_payload=trace_payload,
            trend_profile=trend_profile,
        )
        final_rationale = self._final_trend_profile_rationale(
            trend_profile=trend_profile,
            source_governance=source_governance,
            provenance=provenance,
            validity=validity,
            confidence_calibration=confidence_calibration,
            shift_analysis=shift_analysis,
            downstream_utility=downstream_utility,
            fallback_summary=fallback_summary,
        )
        missing_or_degraded_inputs = self._missing_or_degraded_inputs(
            source_governance=source_governance,
            provenance=provenance,
            freshness=freshness,
        )
        audit_summary = self._audit_summary(
            trace_payload=trace_payload,
            fallback_summary=fallback_summary,
            final_rationale=final_rationale,
        )
        return {
            "source_governance": source_governance,
            "provenance": provenance,
            "freshness": freshness,
            "validity": validity,
            "confidence_calibration": confidence_calibration,
            "shift_analysis": shift_analysis,
            "downstream_utility": downstream_utility,
            "fallback": fallback_summary,
            "final_trend_profile_rationale": final_rationale,
            "missing_or_degraded_inputs": missing_or_degraded_inputs,
            "audit_summary": audit_summary.to_dict(),
            "trace_context": {
                "validation_status": validation_payload.get("status"),
                "assembly_mode": trace_payload.get("assembly_mode"),
                "collector_version": trace_payload.get("collector_version"),
            },
        }

    def validation_summary(self, *, trend_trace: dict[str, Any] | None) -> dict[str, Any]:
        audit_summary = dict(dict(trend_trace or {}).get("audit_summary") or {})
        return {
            "trend_trace_present": bool(trend_trace),
            "reconstructible": bool(audit_summary.get("reconstructible", False)),
            "required_sections_present": bool(audit_summary.get("required_sections_present", False)),
            "silent_failure_indicators": list(audit_summary.get("silent_failure_indicators") or []),
        }

    def _section_payload(self, value: Any, *, fields: tuple[str, ...]) -> dict[str, Any]:
        source = dict(value or {}) if isinstance(value, dict) else {}
        if not source:
            return {}
        payload = {field_name: self._copy_payload(source.get(field_name)) for field_name in fields if field_name in source}
        for field_name, field_value in source.items():
            if field_name not in payload:
                payload[field_name] = self._copy_payload(field_value)
        return payload

    def _fallback_payload(self, fallback: FallbackDecision | dict[str, Any] | None) -> dict[str, Any]:
        if fallback is None:
            return {}
        if isinstance(fallback, dict):
            return self._copy_payload(fallback)
        return fallback.to_dict()

    def _fallback_summary(
        self,
        *,
        fallback_payload: dict[str, Any],
        trace_payload: dict[str, Any],
        trend_profile: TrendProfile,
    ) -> dict[str, Any]:
        fallback_used = bool(fallback_payload.get("used", False))
        fallback_reason = str(fallback_payload.get("reason") or "")
        fallback_path = str(trace_payload.get("fallback_path") or "")
        safe_default_used = trend_profile.trend_source == "safe_default"
        return {
            "used": fallback_used,
            "mode": fallback_payload.get("mode"),
            "reason": fallback_reason,
            "fallback_path": fallback_path,
            "safe_default_used": safe_default_used,
            "fallback_path_visible": (not fallback_used) or bool(fallback_path or fallback_reason or safe_default_used),
        }

    def _final_trend_profile_rationale(
        self,
        *,
        trend_profile: TrendProfile,
        source_governance: dict[str, Any],
        provenance: dict[str, Any],
        validity: dict[str, Any],
        confidence_calibration: dict[str, Any],
        shift_analysis: dict[str, Any],
        downstream_utility: dict[str, Any],
        fallback_summary: dict[str, Any],
    ) -> dict[str, Any]:
        selected_source_class = source_governance.get("selected_source_class")
        provenance_complete = provenance.get("provenance_complete")
        validity_status = validity.get("validity_status")
        confidence_level = confidence_calibration.get("confidence_level")
        shift_severity = shift_analysis.get("shift_severity")
        material_fields = list(downstream_utility.get("material_fields") or [])
        advisory_fields = list(downstream_utility.get("advisory_fields") or [])
        evidence_references = list(provenance.get("evidence_references") or [])
        rationale = [
            f"TrendProfile emitted for niche={trend_profile.niche} using source={trend_profile.trend_source}.",
            f"Selected governed source class: {selected_source_class}.",
            f"Source policy respected: {source_governance.get('policy_respected')}.",
            f"Provenance complete: {provenance_complete}.",
            f"Validity status: {validity_status}.",
            f"Calibrated confidence level: {confidence_level}.",
            f"Shift severity: {shift_severity}.",
            f"Fallback used: {fallback_summary.get('used')}.",
        ]
        return {
            "profile_emitted": True,
            "selected_source_class": selected_source_class,
            "source_policy_respected": source_governance.get("policy_respected"),
            "provenance_complete": provenance_complete,
            "validity_status": validity_status,
            "confidence_level": confidence_level,
            "shift_severity": shift_severity,
            "fallback_used": fallback_summary.get("used"),
            "key_evidence_support": {
                "evidence_reference_count": len(evidence_references),
                "field_provenance_count": len(dict(provenance.get("field_provenance") or {})),
                "source_mix": dict(source_governance.get("source_mix") or {}),
            },
            "primary_downstream_utility": {
                "material_fields": material_fields,
                "advisory_fields": advisory_fields,
            },
            "rationale": rationale,
        }

    def _missing_or_degraded_inputs(
        self,
        *,
        source_governance: dict[str, Any],
        provenance: dict[str, Any],
        freshness: dict[str, Any],
    ) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        for source in sorted(
            [dict(item) for item in list(source_governance.get("rejected_sources") or [])],
            key=lambda item: (str(item.get("source_class") or ""), str(item.get("source_id") or "")),
        ):
            identifier = str(source.get("source_id") or source.get("source_class") or "unknown")
            items.append(
                {
                    "kind": "rejected_source",
                    "identifier": identifier,
                    "impact": "source_governance",
                    "rationale": str(source.get("rationale") or source.get("reason_code") or "Source rejected."),
                }
            )
        for source in sorted(
            [dict(item) for item in list(freshness.get("sources") or [])],
            key=lambda item: (str(item.get("freshness_status") or ""), str(item.get("source_id") or "")),
        ):
            status = str(source.get("freshness_status") or "")
            kind = {
                "missing_timestamp": "missing_timestamp",
                "expired": "expired_source",
                "stale": "stale_source",
            }.get(status)
            if kind is None:
                continue
            identifier = str(source.get("source_id") or source.get("source_class") or "unknown")
            items.append(
                {
                    "kind": kind,
                    "identifier": identifier,
                    "impact": "freshness",
                    "rationale": str(source.get("rationale") or f"Source freshness status is {status}."),
                }
            )
        for field_name in sorted(str(item) for item in list(provenance.get("weakly_supported_fields") or [])):
            items.append(
                {
                    "kind": "weak_field",
                    "identifier": field_name,
                    "impact": "provenance",
                    "rationale": f"Field {field_name} has weak provenance support.",
                }
            )
        for field_name in sorted(str(item) for item in list(provenance.get("unknown_source_fields") or [])):
            items.append(
                {
                    "kind": "unknown_field",
                    "identifier": field_name,
                    "impact": "provenance",
                    "rationale": f"Field {field_name} has unknown source linkage.",
                }
            )
        for field_name in sorted(str(item) for item in list(provenance.get("fallback_fields") or [])):
            items.append(
                {
                    "kind": "fallback_field",
                    "identifier": field_name,
                    "impact": "fallback",
                    "rationale": f"Field {field_name} was emitted from fallback context.",
                }
            )
        return items

    def _audit_summary(
        self,
        *,
        trace_payload: dict[str, Any],
        fallback_summary: dict[str, Any],
        final_rationale: dict[str, Any],
    ) -> TrendTraceAuditSummary:
        section_presence = {
            section_name: self._section_present(trace_payload.get(section_name))
            for section_name in self.required_trace_sections
        }
        fallback_visible = "used" in fallback_summary and bool(fallback_summary.get("fallback_path_visible", False))
        final_rationale_present = bool(final_rationale.get("profile_emitted")) and bool(final_rationale.get("rationale"))
        indicators = []
        for section_name, present in section_presence.items():
            if not present:
                indicators.append(f"MISSING_{section_name.upper()}")
        if not fallback_visible:
            indicators.append("FALLBACK_STATUS_NOT_VISIBLE")
        if not final_rationale_present:
            indicators.append("MISSING_FINAL_TREND_PROFILE_RATIONALE")
        required_sections_present = all(section_presence.values())
        reconstructible = required_sections_present and fallback_visible and final_rationale_present
        return TrendTraceAuditSummary(
            reconstructible=reconstructible,
            required_sections_present=required_sections_present,
            source_governance_present=section_presence["source_governance"],
            provenance_present=section_presence["provenance"],
            freshness_present=section_presence["freshness"],
            validity_present=section_presence["validity"],
            confidence_calibration_present=section_presence["confidence_calibration"],
            shift_analysis_present=section_presence["shift_analysis"],
            downstream_utility_present=section_presence["downstream_utility"],
            fallback_visible=fallback_visible,
            silent_failure_indicators=tuple(indicators),
        )

    def _section_present(self, value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        return bool(value)

    def _copy_payload(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._copy_payload(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._copy_payload(item) for item in value]
        if isinstance(value, set):
            return sorted(self._copy_payload(item) for item in value)
        return value
