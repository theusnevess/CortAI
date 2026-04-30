from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan, AssetSegmentPlan
from app.runtime.asset_selector import AssetSelector, CatalogEntry


VISUAL_TRUTHFULNESS_VERSION = "asset_visual_truthfulness_v2_6"


@dataclass(frozen=True)
class AssetSegmentVisualTruthfulness:
    segment: str
    truthfulness_status: str
    risk_level: str
    selected_asset_path: str
    requested_category: str
    selected_category: str
    category_truthful: bool
    visually_supported: bool
    metadata_support_score: float
    generic_asset_risk: bool
    fallback_or_default_risk: bool
    wrong_category_risk: bool
    unsupported_visual_claims: list[str]
    reason_codes: list[str]
    rationale: list[str]
    evidence_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetVisualTruthfulness:
    truthfulness_version: str
    truthfulness_complete: bool
    overall_risk_level: str
    segment_truthfulness: dict[str, AssetSegmentVisualTruthfulness]
    high_risk_segments: list[str]
    unsupported_claim_segments: list[str]
    generic_or_fallback_segments: list[str]
    boundary_statement: str
    truthfulness_trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["segment_truthfulness"] = {
            name: truthfulness.to_dict()
            for name, truthfulness in self.segment_truthfulness.items()
        }
        return payload


@dataclass(frozen=True)
class AssetVisualTruthfulnessEvaluator:
    """Metadata-only truthfulness risk evaluator for selected assets."""

    def evaluate(
        self,
        *,
        selector: AssetSelector,
        asset_selection: AssetPlan,
        fallback: FallbackDecision,
        visual_alignment: dict[str, Any] | None = None,
    ) -> AssetVisualTruthfulness:
        alignment_by_segment = dict((visual_alignment or {}).get("segment_alignments") or {})
        segment_truthfulness = {
            segment_name: self._segment_truthfulness(
                selector=selector,
                asset_selection=asset_selection,
                fallback=fallback,
                segment_name=segment_name,
                alignment=dict(alignment_by_segment.get(segment_name) or {}),
            )
            for segment_name in ("hook", "setup", "payoff")
        }
        high_risk_segments = [
            name
            for name, truthfulness in segment_truthfulness.items()
            if truthfulness.risk_level == "high"
        ]
        unsupported_claim_segments = [
            name
            for name, truthfulness in segment_truthfulness.items()
            if truthfulness.unsupported_visual_claims
        ]
        generic_or_fallback_segments = [
            name
            for name, truthfulness in segment_truthfulness.items()
            if truthfulness.generic_asset_risk or truthfulness.fallback_or_default_risk
        ]
        risk_level = self._overall_risk(segment_truthfulness=segment_truthfulness)

        return AssetVisualTruthfulness(
            truthfulness_version=VISUAL_TRUTHFULNESS_VERSION,
            truthfulness_complete=not high_risk_segments,
            overall_risk_level=risk_level,
            segment_truthfulness=segment_truthfulness,
            high_risk_segments=high_risk_segments,
            unsupported_claim_segments=unsupported_claim_segments,
            generic_or_fallback_segments=generic_or_fallback_segments,
            boundary_statement="Visual truthfulness is an audit signal only; QC remains responsible for final product quality and publishability.",
            truthfulness_trace={
                "metadata_only": True,
                "image_pixels_inspected": False,
                "ml_used": False,
                "selection_ranking_unchanged": True,
                "fallback_behavior_unchanged": True,
                "publishability_decision_made": False,
            },
        )

    def _segment_truthfulness(
        self,
        *,
        selector: AssetSelector,
        asset_selection: AssetPlan,
        fallback: FallbackDecision,
        segment_name: str,
        alignment: dict[str, Any],
    ) -> AssetSegmentVisualTruthfulness:
        segment = asset_selection.segments.get(segment_name, AssetSegmentPlan())
        selected_path = self._selected_path(asset_selection=asset_selection, segment_name=segment_name)
        requested_category = str(alignment.get("requested_category") or segment.category or "").strip()
        selected_category = str(alignment.get("selected_category") or "").strip()
        fallback_or_default_risk = bool(fallback.used or not selected_path)
        if not selected_path:
            return self._missing_asset_truthfulness(
                segment_name=segment_name,
                requested_category=requested_category,
                fallback_or_default_risk=fallback_or_default_risk,
            )

        entry = selector.lookup_catalog_entry(path=selected_path)
        if entry is None:
            return self._missing_metadata_truthfulness(
                segment_name=segment_name,
                selected_path=selected_path,
                requested_category=requested_category,
                fallback_or_default_risk=fallback_or_default_risk,
            )

        selected_category = selected_category or entry.category
        category_truthful = bool(alignment.get("category_match", False))
        alignment_score = self._float(alignment.get("alignment_score"), 0.0)
        mismatch_level = str(alignment.get("mismatch_level") or "unknown")
        wrong_category_risk = self._wrong_category_risk(
            segment_name=segment_name,
            category_truthful=category_truthful,
            mismatch_level=mismatch_level,
        )
        support_score, unsupported_claims = self._metadata_support(
            segment=segment,
            entry=entry,
        )
        generic_asset_risk = self._generic_asset_risk(
            entry=entry,
            alignment_score=alignment_score,
            support_score=support_score,
        )
        pretty_but_weak = self._pretty_but_weak(
            entry=entry,
            alignment_score=alignment_score,
            support_score=support_score,
        )
        risk_level = self._risk_level(
            fallback_or_default_risk=fallback_or_default_risk,
            wrong_category_risk=wrong_category_risk,
            generic_asset_risk=generic_asset_risk,
            pretty_but_weak=pretty_but_weak,
            unsupported_claims=unsupported_claims,
            support_score=support_score,
        )
        visually_supported = support_score >= 0.45 and not unsupported_claims
        reason_codes = self._reason_codes(
            fallback_or_default_risk=fallback_or_default_risk,
            wrong_category_risk=wrong_category_risk,
            generic_asset_risk=generic_asset_risk,
            pretty_but_weak=pretty_but_weak,
            unsupported_claims=unsupported_claims,
            visually_supported=visually_supported,
        )

        return AssetSegmentVisualTruthfulness(
            segment=segment_name,
            truthfulness_status=self._status(risk_level=risk_level, visually_supported=visually_supported),
            risk_level=risk_level,
            selected_asset_path=selected_path,
            requested_category=requested_category,
            selected_category=selected_category,
            category_truthful=category_truthful,
            visually_supported=visually_supported,
            metadata_support_score=support_score,
            generic_asset_risk=generic_asset_risk,
            fallback_or_default_risk=fallback_or_default_risk,
            wrong_category_risk=wrong_category_risk,
            unsupported_visual_claims=unsupported_claims,
            reason_codes=reason_codes,
            rationale=self._rationale(
                segment_name=segment_name,
                requested_category=requested_category,
                selected_category=selected_category,
                category_truthful=category_truthful,
                support_score=support_score,
                risk_level=risk_level,
                reason_codes=reason_codes,
            ),
            evidence_summary={
                "alignment_score": alignment_score,
                "alignment_level": alignment.get("alignment_level", ""),
                "mismatch_level": mismatch_level,
                "source_type": entry.source_type,
                "genericity": entry.genericity,
                "realism_score": entry.realism_score,
                "strength": entry.strength,
                "category": entry.category,
                "family": entry.family,
            },
        )

    def _metadata_support(self, *, segment: AssetSegmentPlan, entry: CatalogEntry) -> tuple[float, list[str]]:
        entry_tokens = self._entry_tokens(entry)
        claims = self._claim_tokens(segment=segment)
        if not claims:
            return 0.65, []
        supported = sorted(claim for claim in claims if claim in entry_tokens)
        unsupported = sorted(claim for claim in claims if claim not in entry_tokens)
        support_score = round(len(supported) / len(claims), 4)
        return support_score, unsupported[:8]

    def _claim_tokens(self, *, segment: AssetSegmentPlan) -> set[str]:
        values: list[str] = []
        contract = segment.decision_contract
        query = segment.visual_query
        values.extend(
            [
                contract.entity,
                contract.event,
                contract.anomaly_type,
                contract.visibility_requirement,
                contract.photographability,
                query.subject,
                query.state_or_event,
                query.environment,
                query.search_query_real,
            ]
        )
        claims = {
            token
            for token in self._tokens(" ".join(str(value) for value in values if value))
            if token not in self._stop_tokens()
        }
        return claims

    def _generic_asset_risk(self, *, entry: CatalogEntry, alignment_score: float, support_score: float) -> bool:
        if entry.genericity >= 0.35:
            return True
        if entry.category in {"room", "corridor", "institutional_space", "investigative_interior", "horror_interior"}:
            return alignment_score < 0.55 and support_score < 0.45
        return False

    def _pretty_but_weak(self, *, entry: CatalogEntry, alignment_score: float, support_score: float) -> bool:
        visually_strong = entry.realism_score >= 0.9 or entry.strength >= 0.85
        return visually_strong and (alignment_score < 0.45 or support_score < 0.35)

    def _wrong_category_risk(self, *, segment_name: str, category_truthful: bool, mismatch_level: str) -> bool:
        if category_truthful:
            return False
        if segment_name in {"hook", "payoff"}:
            return mismatch_level in {"medium", "high", "unknown"}
        return mismatch_level == "high"

    def _risk_level(
        self,
        *,
        fallback_or_default_risk: bool,
        wrong_category_risk: bool,
        generic_asset_risk: bool,
        pretty_but_weak: bool,
        unsupported_claims: list[str],
        support_score: float,
    ) -> str:
        if fallback_or_default_risk or wrong_category_risk or (pretty_but_weak and unsupported_claims):
            return "high"
        if generic_asset_risk or pretty_but_weak or unsupported_claims or support_score < 0.45:
            return "medium"
        return "low"

    def _status(self, *, risk_level: str, visually_supported: bool) -> str:
        if risk_level == "high":
            return "mismatch_risk"
        if visually_supported:
            return "supported"
        if risk_level == "medium":
            return "weakly_supported"
        return "partial"

    def _reason_codes(
        self,
        *,
        fallback_or_default_risk: bool,
        wrong_category_risk: bool,
        generic_asset_risk: bool,
        pretty_but_weak: bool,
        unsupported_claims: list[str],
        visually_supported: bool,
    ) -> list[str]:
        codes: list[str] = []
        if fallback_or_default_risk:
            codes.append("FALLBACK_OR_DEFAULT_VISUAL_RISK")
        if wrong_category_risk:
            codes.append("WRONG_CATEGORY_FOR_SEGMENT_ROLE")
        if generic_asset_risk:
            codes.append("GENERIC_ASSET_SEMANTIC_RISK")
        if pretty_but_weak:
            codes.append("PRETTY_BUT_SEMANTICALLY_WEAK_ASSET")
        if unsupported_claims:
            codes.append("UNSUPPORTED_VISUAL_CLAIMS")
        if visually_supported and not codes:
            codes.append("VISUAL_TRUTHFULNESS_METADATA_SUPPORTED")
        if not codes:
            codes.append("VISUAL_TRUTHFULNESS_PARTIAL_SUPPORT")
        return codes

    def _rationale(
        self,
        *,
        segment_name: str,
        requested_category: str,
        selected_category: str,
        category_truthful: bool,
        support_score: float,
        risk_level: str,
        reason_codes: list[str],
    ) -> list[str]:
        rationale = [
            f"{segment_name} requested '{requested_category}' and selected '{selected_category}'.",
            f"Metadata support score is {support_score}.",
            f"Risk level is {risk_level}.",
        ]
        if category_truthful:
            rationale.append("Selected category matches the requested category.")
        else:
            rationale.append("Selected category does not fully match the requested category.")
        if "UNSUPPORTED_VISUAL_CLAIMS" in reason_codes:
            rationale.append("One or more visual claims were not supported by catalog metadata.")
        if "PRETTY_BUT_SEMANTICALLY_WEAK_ASSET" in reason_codes:
            rationale.append("Asset appears strong by catalog quality metadata but weak by semantic support.")
        return rationale

    def _missing_asset_truthfulness(
        self,
        *,
        segment_name: str,
        requested_category: str,
        fallback_or_default_risk: bool,
    ) -> AssetSegmentVisualTruthfulness:
        return AssetSegmentVisualTruthfulness(
            segment=segment_name,
            truthfulness_status="fallback_or_missing",
            risk_level="high" if fallback_or_default_risk else "medium",
            selected_asset_path="",
            requested_category=requested_category,
            selected_category="",
            category_truthful=False,
            visually_supported=False,
            metadata_support_score=0.0,
            generic_asset_risk=False,
            fallback_or_default_risk=fallback_or_default_risk,
            wrong_category_risk=False,
            unsupported_visual_claims=[],
            reason_codes=["SELECTED_ASSET_PATH_MISSING", "FALLBACK_OR_DEFAULT_VISUAL_RISK"],
            rationale=["Selected asset path is missing; visual truthfulness cannot be verified from metadata."],
        )

    def _missing_metadata_truthfulness(
        self,
        *,
        segment_name: str,
        selected_path: str,
        requested_category: str,
        fallback_or_default_risk: bool,
    ) -> AssetSegmentVisualTruthfulness:
        return AssetSegmentVisualTruthfulness(
            segment=segment_name,
            truthfulness_status="unknown_metadata",
            risk_level="high",
            selected_asset_path=selected_path,
            requested_category=requested_category,
            selected_category="",
            category_truthful=False,
            visually_supported=False,
            metadata_support_score=0.0,
            generic_asset_risk=False,
            fallback_or_default_risk=fallback_or_default_risk,
            wrong_category_risk=False,
            unsupported_visual_claims=[],
            reason_codes=["SELECTED_ASSET_METADATA_MISSING"],
            rationale=["Selected asset is not present in catalog metadata; truthfulness support is unknown."],
        )

    def _overall_risk(self, *, segment_truthfulness: dict[str, AssetSegmentVisualTruthfulness]) -> str:
        levels = [truthfulness.risk_level for truthfulness in segment_truthfulness.values()]
        if "high" in levels:
            return "high"
        if "medium" in levels:
            return "medium"
        return "low"

    def _entry_tokens(self, entry: CatalogEntry) -> set[str]:
        values: list[str] = [
            entry.category,
            entry.subtype,
            entry.family,
            entry.framing,
            entry.mood,
            entry.source_type,
        ]
        values.extend(entry.tags)
        values.extend(entry.semantic_pattern_fit)
        values.extend(entry.entity_fit)
        return self._tokens(" ".join(str(value) for value in values if value))

    def _tokens(self, value: str) -> set[str]:
        normalized = re.sub(r"[^a-zA-Z0-9_]+", " ", str(value or "").lower())
        return {token for token in normalized.split() if len(token) >= 3}

    def _stop_tokens(self) -> set[str]:
        return {
            "the",
            "and",
            "with",
            "from",
            "into",
            "that",
            "this",
            "needs",
            "show",
            "shows",
            "showing",
            "segment",
            "visual",
            "evidence",
            "state",
            "event",
        }

    def _float(self, value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _selected_path(self, *, asset_selection: AssetPlan, segment_name: str) -> str:
        if segment_name == "hook":
            return asset_selection.hook_asset
        if segment_name == "setup":
            return asset_selection.setup_asset
        if segment_name == "payoff":
            return asset_selection.payoff_asset
        return ""
