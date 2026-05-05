from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import TrendProfile


@dataclass(frozen=True)
class TrendFieldProvenance:
    field_name: str
    value_present: bool
    source_classes: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    support_level: str = "unknown"
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "value_present": self.value_present,
            "source_classes": list(self.source_classes),
            "source_ids": list(self.source_ids),
            "evidence_ids": list(self.evidence_ids),
            "support_level": self.support_level,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class TrendProvenanceEvidenceReference:
    evidence_id: str
    source_id: str | None
    source_class: str
    evidence_type: str
    field_names: tuple[str, ...] = ()
    usable: bool = True
    reason_code: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "source_class": self.source_class,
            "evidence_type": self.evidence_type,
            "field_names": list(self.field_names),
            "usable": self.usable,
            "reason_code": self.reason_code,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TrendProvenanceSummary:
    provenance_complete: bool
    source_mix: dict[str, int] = field(default_factory=dict)
    field_provenance: dict[str, TrendFieldProvenance] = field(default_factory=dict)
    evidence_references: tuple[TrendProvenanceEvidenceReference, ...] = ()
    accepted_sources: tuple[dict[str, Any], ...] = ()
    rejected_sources: tuple[dict[str, Any], ...] = ()
    ignored_sources: tuple[dict[str, Any], ...] = ()
    fallback_fields: tuple[str, ...] = ()
    weakly_supported_fields: tuple[str, ...] = ()
    unknown_source_fields: tuple[str, ...] = ()
    provenance_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance_complete": self.provenance_complete,
            "source_mix": dict(self.source_mix),
            "field_provenance": {
                name: payload.to_dict() for name, payload in self.field_provenance.items()
            },
            "evidence_references": [item.to_dict() for item in self.evidence_references],
            "accepted_sources": [dict(item) for item in self.accepted_sources],
            "rejected_sources": [dict(item) for item in self.rejected_sources],
            "ignored_sources": [dict(item) for item in self.ignored_sources],
            "fallback_fields": list(self.fallback_fields),
            "weakly_supported_fields": list(self.weakly_supported_fields),
            "unknown_source_fields": list(self.unknown_source_fields),
            "provenance_trace": dict(self.provenance_trace),
        }


@dataclass
class TrendProvenanceBuilder:
    important_fields: tuple[str, ...] = (
        "niche",
        "region",
        "dominant_hooks",
        "avg_duration",
        "pacing",
        "visual_style",
        "text_style",
        "trend_source",
        "confidence_scores",
        "updated_at",
        "valid_until",
        "sample_size",
        "evidence",
    )

    def build(
        self,
        *,
        trend_profile: TrendProfile,
        source_governance: dict[str, Any] | None,
        fallback_used: bool,
        fallback_reason: str,
    ) -> TrendProvenanceSummary:
        governance = dict(source_governance or {})
        accepted_sources = [dict(item) for item in list(governance.get("accepted_sources") or [])]
        rejected_sources = [dict(item) for item in list(governance.get("rejected_sources") or [])]
        ignored_sources = [dict(item) for item in list(governance.get("ignored_sources") or [])]

        evidence_references = self._normalize_evidence_references(
            trend_profile=trend_profile,
            accepted_sources=accepted_sources,
            rejected_sources=rejected_sources,
            ignored_sources=ignored_sources,
            fallback_used=fallback_used,
        )
        field_provenance = self._build_field_provenance(
            trend_profile=trend_profile,
            accepted_sources=accepted_sources,
            evidence_references=evidence_references,
            fallback_used=fallback_used,
        )

        fallback_fields = tuple(
            name
            for name, payload in field_provenance.items()
            if payload.support_level == "fallback"
        )
        weakly_supported_fields = tuple(
            name
            for name, payload in field_provenance.items()
            if payload.support_level == "weak"
        )
        unknown_source_fields = tuple(
            name
            for name, payload in field_provenance.items()
            if payload.support_level == "unknown"
        )
        provenance_complete = not unknown_source_fields

        return TrendProvenanceSummary(
            provenance_complete=provenance_complete,
            source_mix=dict(governance.get("source_mix") or {}),
            field_provenance=field_provenance,
            evidence_references=tuple(evidence_references),
            accepted_sources=tuple(accepted_sources),
            rejected_sources=tuple(rejected_sources),
            ignored_sources=tuple(ignored_sources),
            fallback_fields=fallback_fields,
            weakly_supported_fields=weakly_supported_fields,
            unknown_source_fields=unknown_source_fields,
            provenance_trace={
                "fallback_used": fallback_used,
                "fallback_reason": fallback_reason,
                "source_governance_present": bool(source_governance),
                "policy_respected": governance.get("policy_respected"),
                "selected_source_class": governance.get("selected_source_class"),
                "important_fields": list(self.important_fields),
            },
        )

    def _normalize_evidence_references(
        self,
        *,
        trend_profile: TrendProfile,
        accepted_sources: list[dict[str, Any]],
        rejected_sources: list[dict[str, Any]],
        ignored_sources: list[dict[str, Any]],
        fallback_used: bool,
    ) -> list[TrendProvenanceEvidenceReference]:
        evidence_ids_by_source: dict[str, str] = {}
        for source in [*accepted_sources, *rejected_sources, *ignored_sources]:
            metadata = dict(source.get("metadata") or {})
            for evidence_id in list(metadata.get("evidence_ids") or []):
                evidence_ids_by_source[str(evidence_id)] = str(source.get("source_id") or "")

        normalized: list[TrendProvenanceEvidenceReference] = []
        for index, evidence in enumerate(trend_profile.evidence):
            evidence_id = self._evidence_id(evidence.to_dict(), index=index)
            source_id = evidence_ids_by_source.get(evidence_id)
            source_class = self._source_class_for_evidence(
                source_id=source_id,
                accepted_sources=accepted_sources,
                rejected_sources=rejected_sources,
                ignored_sources=ignored_sources,
            )
            usable = source_class not in {"safe_default", "unknown"}
            if fallback_used or source_class == "safe_default":
                usable = False
            normalized.append(
                TrendProvenanceEvidenceReference(
                    evidence_id=evidence_id,
                    source_id=source_id,
                    source_class=source_class,
                    evidence_type=str(evidence.evidence_type or ""),
                    field_names=(),
                    usable=usable,
                    reason_code="EVIDENCE_FALLBACK_DEFAULT" if source_class == "safe_default" else "EVIDENCE_LINKED",
                    metadata=evidence.to_dict(),
                )
            )
        if fallback_used and not normalized:
            normalized.append(
                TrendProvenanceEvidenceReference(
                    evidence_id="fallback:safe_default",
                    source_id="safe_default",
                    source_class="safe_default",
                    evidence_type="safe_default",
                    field_names=(),
                    usable=False,
                    reason_code="EVIDENCE_FALLBACK_DEFAULT",
                    metadata={"fallback_default": True},
                )
            )
        return normalized

    def _build_field_provenance(
        self,
        *,
        trend_profile: TrendProfile,
        accepted_sources: list[dict[str, Any]],
        evidence_references: list[TrendProvenanceEvidenceReference],
        fallback_used: bool,
    ) -> dict[str, TrendFieldProvenance]:
        field_provenance: dict[str, TrendFieldProvenance] = {}
        profile_payload = trend_profile.to_dict()
        for field_name in self.important_fields:
            if field_name not in profile_payload:
                continue
            value = profile_payload.get(field_name)
            value_present = self._value_present(value)
            supporting_sources = []
            evidence_ids: list[str] = []
            for source in accepted_sources:
                metadata = dict(source.get("metadata") or {})
                supported_fields = list(metadata.get("supported_fields") or [])
                if field_name in supported_fields:
                    supporting_sources.append(source)
                    evidence_ids.extend(str(item) for item in list(metadata.get("evidence_ids") or []))
            evidence_ids = sorted(set(evidence_ids))
            support_level, rationale = self._support_level(
                field_name=field_name,
                value_present=value_present,
                supporting_sources=supporting_sources,
                evidence_ids=evidence_ids,
                fallback_used=fallback_used,
            )
            field_provenance[field_name] = TrendFieldProvenance(
                field_name=field_name,
                value_present=value_present,
                source_classes=tuple(sorted({str(item.get("source_class") or "") for item in supporting_sources})),
                source_ids=tuple(str(item.get("source_id") or "") for item in supporting_sources),
                evidence_ids=tuple(evidence_ids),
                support_level=support_level,
                rationale=rationale,
            )

        field_names_by_evidence: dict[str, list[str]] = {}
        for name, payload in field_provenance.items():
            for evidence_id in payload.evidence_ids:
                field_names_by_evidence.setdefault(evidence_id, []).append(name)
        for index, evidence in enumerate(evidence_references):
            evidence_references[index] = TrendProvenanceEvidenceReference(
                evidence_id=evidence.evidence_id,
                source_id=evidence.source_id,
                source_class=evidence.source_class,
                evidence_type=evidence.evidence_type,
                field_names=tuple(sorted(field_names_by_evidence.get(evidence.evidence_id, []))),
                usable=evidence.usable,
                reason_code=evidence.reason_code,
                metadata=evidence.metadata,
            )
        return field_provenance

    def _support_level(
        self,
        *,
        field_name: str,
        value_present: bool,
        supporting_sources: list[dict[str, Any]],
        evidence_ids: list[str],
        fallback_used: bool,
    ) -> tuple[str, str]:
        if not value_present:
            return "unknown", f"Field {field_name} is absent or empty in the emitted trend profile."
        source_classes = {str(item.get("source_class") or "") for item in supporting_sources}
        if fallback_used or source_classes == {"safe_default"}:
            return "fallback", f"Field {field_name} came from safe_default fallback context."
        if not supporting_sources:
            return "unknown", f"Field {field_name} is present but no governed source linkage was available."
        if evidence_ids:
            return "strong", f"Field {field_name} is linked to accepted governed source evidence."
        if len(supporting_sources) >= 1:
            if field_name in {"confidence_scores", "updated_at", "valid_until", "trend_source"}:
                return "partial", f"Field {field_name} is linked to accepted governed sources without direct evidence IDs."
            return "weak", f"Field {field_name} is linked to accepted governed sources but lacks direct evidence IDs."
        return "unknown", f"Field {field_name} could not be classified conservatively."

    def _evidence_id(self, payload: dict[str, Any], *, index: int) -> str:
        reference_id = str(payload.get("reference_id") or "").strip()
        if reference_id:
            return reference_id
        source = str(payload.get("source") or "unknown")
        evidence_type = str(payload.get("evidence_type") or "unknown")
        captured_at = str(payload.get("captured_at") or "undated")
        return f"{source}:{evidence_type}:{captured_at}:{index}"

    def _source_class_for_evidence(
        self,
        *,
        source_id: str | None,
        accepted_sources: list[dict[str, Any]],
        rejected_sources: list[dict[str, Any]],
        ignored_sources: list[dict[str, Any]],
    ) -> str:
        for source in [*accepted_sources, *rejected_sources, *ignored_sources]:
            if str(source.get("source_id") or "") == str(source_id or ""):
                return str(source.get("source_class") or "unknown")
        return "unknown"

    def _value_present(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, dict, set)):
            return bool(value)
        return True
