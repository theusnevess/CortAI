from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TrendSourcePolicy:
    allowed_source_classes: tuple[str, ...] = (
        "manual_curation",
        "validated_cache",
        "current_store",
        "history_snapshot",
        "safe_default",
        "internal_runtime_metrics",
        "approved_external_reference",
    )
    forbidden_source_classes: tuple[str, ...] = (
        "unknown",
        "unsupported_external",
        "unbounded_scrape",
        "fake_live_trend",
        "unverified_social_claim",
        "missing_source_type",
    )
    priority_order: tuple[str, ...] = (
        "approved_external_reference",
        "manual_curation",
        "current_store",
        "validated_cache",
        "history_snapshot",
        "internal_runtime_metrics",
        "safe_default",
    )
    allow_cache: bool = True
    allow_history: bool = True
    allow_manual_curation: bool = True
    allow_safe_default: bool = True
    require_source_type: bool = True
    require_source_timestamp: bool = False
    require_validity_semantics: bool = True
    region_policy: dict[str, Any] = field(
        default_factory=lambda: {
            "allow_region": True,
            "fallback_region": "US",
            "forbid_fake_region_claims": True,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_source_classes": list(self.allowed_source_classes),
            "forbidden_source_classes": list(self.forbidden_source_classes),
            "priority_order": list(self.priority_order),
            "allow_cache": self.allow_cache,
            "allow_history": self.allow_history,
            "allow_manual_curation": self.allow_manual_curation,
            "allow_safe_default": self.allow_safe_default,
            "require_source_type": self.require_source_type,
            "require_source_timestamp": self.require_source_timestamp,
            "require_validity_semantics": self.require_validity_semantics,
            "region_policy": dict(self.region_policy),
        }


@dataclass(frozen=True)
class TrendSourceDecision:
    source_id: str
    source_class: str
    accepted: bool
    priority_rank: int | None
    reason_code: str
    rationale: str
    governance_status: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_class": self.source_class,
            "accepted": self.accepted,
            "priority_rank": self.priority_rank,
            "reason_code": self.reason_code,
            "rationale": self.rationale,
            "governance_status": self.governance_status,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TrendSourceGovernanceResult:
    policy_version: str
    policy_respected: bool
    accepted_sources: tuple[TrendSourceDecision, ...] = ()
    rejected_sources: tuple[TrendSourceDecision, ...] = ()
    ignored_sources: tuple[TrendSourceDecision, ...] = ()
    selected_source_class: str | None = None
    source_mix: dict[str, int] = field(default_factory=dict)
    fallback_required: bool = False
    fallback_reason: str | None = None
    governance_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "policy_respected": self.policy_respected,
            "accepted_sources": [item.to_dict() for item in self.accepted_sources],
            "rejected_sources": [item.to_dict() for item in self.rejected_sources],
            "ignored_sources": [item.to_dict() for item in self.ignored_sources],
            "selected_source_class": self.selected_source_class,
            "source_mix": dict(self.source_mix),
            "fallback_required": self.fallback_required,
            "fallback_reason": self.fallback_reason,
            "governance_trace": dict(self.governance_trace),
        }


@dataclass
class TrendSourceGovernanceEvaluator:
    policy: TrendSourcePolicy = field(default_factory=TrendSourcePolicy)
    policy_version: str = "trend_source_governance_v2_6"

    def classify_source(self, *, source_name: str, source_class_hint: str | None = None) -> str:
        hinted = (source_class_hint or "").strip()
        if hinted:
            return hinted
        source = (source_name or "").strip().lower()
        mapping = {
            "manual_curation": "manual_curation",
            "manual_file_legacy": "current_store",
            "creative_center": "approved_external_reference",
            "internal_metrics_validation": "internal_runtime_metrics",
            "safe_default": "safe_default",
            "validated_cache": "validated_cache",
            "history_snapshot": "history_snapshot",
            "current_store": "current_store",
        }
        return mapping.get(source, "unknown")

    def evaluate_candidates(
        self,
        *,
        candidates: list[dict[str, Any]],
        requested_region: str = "",
        selection_mode: str = "mixed_allowed",
    ) -> TrendSourceGovernanceResult:
        accepted_raw: list[TrendSourceDecision] = []
        rejected: list[TrendSourceDecision] = []
        requested = (requested_region or "").strip() or str(self.policy.region_policy.get("fallback_region") or "US")

        for candidate in sorted(
            [dict(item) for item in candidates],
            key=lambda item: (
                self._sort_priority_rank(str(item.get("source_class") or "")),
                str(item.get("source_id") or ""),
            ),
        ):
            decision = self._evaluate_candidate(candidate=candidate, requested_region=requested)
            if decision.governance_status == "rejected":
                rejected.append(decision)
            else:
                accepted_raw.append(decision)

        accepted: list[TrendSourceDecision] = []
        ignored: list[TrendSourceDecision] = []
        if selection_mode == "single_preferred" and accepted_raw:
            accepted.append(accepted_raw[0])
            for decision in accepted_raw[1:]:
                ignored.append(
                    TrendSourceDecision(
                        source_id=decision.source_id,
                        source_class=decision.source_class,
                        accepted=False,
                        priority_rank=decision.priority_rank,
                        reason_code="SOURCE_IGNORED_LOWER_PRIORITY",
                        rationale=(
                            f"Source {decision.source_class} was allowed but ignored because a higher-priority "
                            "source was selected."
                        ),
                        governance_status="ignored",
                        metadata=dict(decision.metadata),
                    )
                )
        else:
            accepted.extend(accepted_raw)

        selected_source_class = accepted[0].source_class if accepted else None
        source_mix: dict[str, int] = {}
        for decision in accepted:
            source_mix[decision.source_class] = source_mix.get(decision.source_class, 0) + 1

        fallback_required = not accepted or selected_source_class == "safe_default"
        fallback_reason = None
        if not accepted:
            fallback_reason = "NO_GOVERNED_SOURCE_ACCEPTED"
        elif selected_source_class == "safe_default":
            fallback_reason = "ONLY_SAFE_DEFAULT_SOURCE_ALLOWED"

        severe_rejections = {
            "SOURCE_REJECTED_FORBIDDEN_CLASS",
            "SOURCE_REJECTED_MISSING_TYPE",
            "SOURCE_REJECTED_UNSUPPORTED_EXTERNAL",
            "SOURCE_REJECTED_FAKE_REGION_CLAIM",
        }
        selected_rank = accepted[0].priority_rank if accepted else None
        policy_respected = not any(
            decision.reason_code in severe_rejections and (selected_rank is None or decision.priority_rank is None or decision.priority_rank <= selected_rank)
            for decision in rejected
        )

        return TrendSourceGovernanceResult(
            policy_version=self.policy_version,
            policy_respected=policy_respected,
            accepted_sources=tuple(accepted),
            rejected_sources=tuple(rejected),
            ignored_sources=tuple(ignored),
            selected_source_class=selected_source_class,
            source_mix=source_mix,
            fallback_required=fallback_required,
            fallback_reason=fallback_reason,
            governance_trace={
                "selection_mode": selection_mode,
                "requested_region": requested,
                "region_effective": requested,
                "policy": self.policy.to_dict(),
                "candidate_count": len(candidates),
                "accepted_count": len(accepted),
                "rejected_count": len(rejected),
                "ignored_count": len(ignored),
            },
        )

    def _evaluate_candidate(
        self,
        *,
        candidate: dict[str, Any],
        requested_region: str,
    ) -> TrendSourceDecision:
        source_id = str(candidate.get("source_id") or "")
        source_class = str(candidate.get("source_class") or "").strip()
        metadata = dict(candidate.get("metadata") or {})
        priority_rank = self._priority_rank(source_class) if source_class else None

        if self.policy.require_source_type and not source_class:
            return TrendSourceDecision(
                source_id=source_id,
                source_class="missing_source_type",
                accepted=False,
                priority_rank=None,
                reason_code="SOURCE_REJECTED_MISSING_TYPE",
                rationale="Source candidate was rejected because source_class was missing.",
                governance_status="rejected",
                metadata=metadata,
            )

        if source_class in self.policy.forbidden_source_classes:
            return TrendSourceDecision(
                source_id=source_id,
                source_class=source_class,
                accepted=False,
                priority_rank=priority_rank,
                reason_code="SOURCE_REJECTED_FORBIDDEN_CLASS",
                rationale=f"Source class {source_class} is forbidden by trend source governance policy.",
                governance_status="rejected",
                metadata=metadata,
            )

        if source_class not in self.policy.allowed_source_classes:
            reason_code = "SOURCE_REJECTED_UNSUPPORTED_EXTERNAL" if "external" in source_class else "SOURCE_REJECTED_FORBIDDEN_CLASS"
            return TrendSourceDecision(
                source_id=source_id,
                source_class=source_class or "unknown",
                accepted=False,
                priority_rank=priority_rank,
                reason_code=reason_code,
                rationale=f"Source class {source_class or 'unknown'} is not in the allowed source governance policy.",
                governance_status="rejected",
                metadata=metadata,
            )

        if self._is_fake_region_claim(candidate=candidate, requested_region=requested_region):
            return TrendSourceDecision(
                source_id=source_id,
                source_class=source_class,
                accepted=False,
                priority_rank=priority_rank,
                reason_code="SOURCE_REJECTED_FAKE_REGION_CLAIM",
                rationale="Source candidate was rejected because it claimed unsupported regional specificity.",
                governance_status="rejected",
                metadata=metadata,
            )

        if source_class == "validated_cache" and not self.policy.allow_cache:
            return self._rejected_policy_toggle(
                source_id=source_id,
                source_class=source_class,
                priority_rank=priority_rank,
                metadata=metadata,
            )
        if source_class == "history_snapshot" and not self.policy.allow_history:
            return self._rejected_policy_toggle(
                source_id=source_id,
                source_class=source_class,
                priority_rank=priority_rank,
                metadata=metadata,
            )
        if source_class == "manual_curation" and not self.policy.allow_manual_curation:
            return self._rejected_policy_toggle(
                source_id=source_id,
                source_class=source_class,
                priority_rank=priority_rank,
                metadata=metadata,
            )
        if source_class == "safe_default" and not self.policy.allow_safe_default:
            return self._rejected_policy_toggle(
                source_id=source_id,
                source_class=source_class,
                priority_rank=priority_rank,
                metadata=metadata,
            )

        if source_class == "safe_default":
            return TrendSourceDecision(
                source_id=source_id,
                source_class=source_class,
                accepted=True,
                priority_rank=priority_rank,
                reason_code="SOURCE_ACCEPTED_SAFE_DEFAULT_ALLOWED",
                rationale="safe_default is allowed only as explicit fallback-safe context and not as strong evidence.",
                governance_status="fallback_allowed",
                metadata=metadata,
            )

        reason_code = {
            "manual_curation": "SOURCE_ACCEPTED_MANUAL_CURATION_ALLOWED",
            "validated_cache": "SOURCE_ACCEPTED_CACHE_ALLOWED",
            "history_snapshot": "SOURCE_ACCEPTED_HISTORY_ALLOWED",
        }.get(source_class, "SOURCE_ACCEPTED_ALLOWED_CLASS")
        return TrendSourceDecision(
            source_id=source_id,
            source_class=source_class,
            accepted=True,
            priority_rank=priority_rank,
            reason_code=reason_code,
            rationale=f"Source class {source_class} is explicitly allowed by trend source governance policy.",
            governance_status="accepted",
            metadata=metadata,
        )

    def _rejected_policy_toggle(
        self,
        *,
        source_id: str,
        source_class: str,
        priority_rank: int | None,
        metadata: dict[str, Any],
    ) -> TrendSourceDecision:
        return TrendSourceDecision(
            source_id=source_id,
            source_class=source_class,
            accepted=False,
            priority_rank=priority_rank,
            reason_code="SOURCE_REJECTED_FORBIDDEN_CLASS",
            rationale=f"Source class {source_class} is supported in principle but disabled by current source policy.",
            governance_status="rejected",
            metadata=metadata,
        )

    def _priority_rank(self, source_class: str) -> int | None:
        try:
            return self.policy.priority_order.index(source_class) + 1
        except ValueError:
            return None

    def _sort_priority_rank(self, source_class: str) -> int:
        rank = self._priority_rank(source_class.strip()) if source_class.strip() else None
        return 999 if rank is None else rank

    def _is_fake_region_claim(self, *, candidate: dict[str, Any], requested_region: str) -> bool:
        if not bool(self.policy.region_policy.get("forbid_fake_region_claims", True)):
            return False
        metadata = dict(candidate.get("metadata") or {})
        if bool(metadata.get("fake_region_claim")):
            return True
        if metadata.get("region_specificity_supported") is False:
            candidate_region = str(candidate.get("region") or "").strip()
            fallback_region = str(self.policy.region_policy.get("fallback_region") or "US")
            if candidate_region and candidate_region not in {fallback_region, requested_region}:
                return True
        return False
