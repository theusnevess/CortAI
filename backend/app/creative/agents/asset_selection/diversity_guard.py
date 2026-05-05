from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan
from app.runtime.asset_selector import AssetSelector


ASSET_DIVERSITY_VERSION = "asset_diversity_guard_v2_6"


@dataclass(frozen=True)
class AssetSegmentDiversity:
    segment: str
    asset_path: str
    category: str
    source_type: str
    family: str
    repeated_asset: bool
    repeated_category: bool
    progression_role: str
    progression_contribution: str
    reason_codes: list[str]
    rationale: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetDiversityResult:
    diversity_version: str
    diversity_complete: bool
    repeated_asset_detected: bool
    repeated_category_detected: bool
    repeated_asset_paths: list[str]
    repeated_categories: list[str]
    category_sequence: list[str]
    visual_progression_level: str
    visual_progression_valid: bool
    segment_diversity: dict[str, AssetSegmentDiversity]
    reason_codes: list[str]
    rationale: list[str]
    boundary_statement: str
    diversity_trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["segment_diversity"] = {
            name: segment.to_dict()
            for name, segment in self.segment_diversity.items()
        }
        return payload


@dataclass(frozen=True)
class AssetDiversityGuard:
    """Read-only repetition and visual progression guard for selected assets."""

    def evaluate(
        self,
        *,
        selector: AssetSelector,
        asset_selection: AssetPlan,
        fallback: FallbackDecision | None = None,
    ) -> AssetDiversityResult:
        segment_order = ("hook", "setup", "payoff")
        segment_paths = {
            name: self._selected_path(asset_selection=asset_selection, segment_name=name)
            for name in segment_order
        }
        segment_categories = {
            name: self._category(selector=selector, asset_selection=asset_selection, segment_name=name, path=path)
            for name, path in segment_paths.items()
        }
        path_counts = Counter(path for path in segment_paths.values() if path)
        category_counts = Counter(category for category in segment_categories.values() if category)
        repeated_asset_paths = sorted(path for path, count in path_counts.items() if count > 1)
        repeated_categories = sorted(category for category, count in category_counts.items() if count > 1)
        repeated_asset_detected = bool(repeated_asset_paths)
        repeated_category_detected = bool(repeated_categories)
        category_sequence = [segment_categories[name] for name in segment_order]
        selected_count = sum(1 for path in segment_paths.values() if path)
        unique_category_count = len({category for category in category_sequence if category})
        visual_progression_level = self._progression_level(
            selected_count=selected_count,
            unique_category_count=unique_category_count,
            repeated_asset_detected=repeated_asset_detected,
        )
        visual_progression_valid = (
            selected_count == 3
            and not repeated_asset_detected
            and visual_progression_level in {"moderate", "strong"}
        )
        segment_diversity = {
            name: self._segment_diversity(
                selector=selector,
                segment_name=name,
                path=segment_paths[name],
                category=segment_categories[name],
                path_counts=path_counts,
                category_counts=category_counts,
            )
            for name in segment_order
        }
        reason_codes = self._reason_codes(
            repeated_asset_detected=repeated_asset_detected,
            repeated_category_detected=repeated_category_detected,
            visual_progression_level=visual_progression_level,
            fallback_used=bool(fallback and fallback.used),
        )
        diversity_complete = selected_count == 3 and not repeated_asset_detected

        return AssetDiversityResult(
            diversity_version=ASSET_DIVERSITY_VERSION,
            diversity_complete=diversity_complete,
            repeated_asset_detected=repeated_asset_detected,
            repeated_category_detected=repeated_category_detected,
            repeated_asset_paths=repeated_asset_paths,
            repeated_categories=repeated_categories,
            category_sequence=category_sequence,
            visual_progression_level=visual_progression_level,
            visual_progression_valid=visual_progression_valid,
            segment_diversity=segment_diversity,
            reason_codes=reason_codes,
            rationale=self._rationale(
                repeated_asset_detected=repeated_asset_detected,
                repeated_category_detected=repeated_category_detected,
                visual_progression_level=visual_progression_level,
                selected_count=selected_count,
            ),
            boundary_statement="Asset diversity is an audit signal only; it does not add randomness or change selected assets.",
            diversity_trace={
                "segments_evaluated": list(segment_order),
                "selected_segment_count": selected_count,
                "unique_category_count": unique_category_count,
                "randomness_added": False,
                "selection_ranking_unchanged": True,
                "fallback_behavior_unchanged": True,
            },
        )

    def _segment_diversity(
        self,
        *,
        selector: AssetSelector,
        segment_name: str,
        path: str,
        category: str,
        path_counts: Counter[str],
        category_counts: Counter[str],
    ) -> AssetSegmentDiversity:
        entry = selector.lookup_catalog_entry(path=path) if path else None
        repeated_asset = bool(path and path_counts[path] > 1)
        repeated_category = bool(category and category_counts[category] > 1)
        progression_contribution = self._progression_contribution(
            path=path,
            category=category,
            repeated_asset=repeated_asset,
            repeated_category=repeated_category,
        )
        reason_codes = []
        if not path:
            reason_codes.append("SEGMENT_ASSET_MISSING")
        if repeated_asset:
            reason_codes.append("SEGMENT_REPEATED_ASSET")
        if repeated_category:
            reason_codes.append("SEGMENT_REPEATED_CATEGORY")
        if progression_contribution == "unique_category":
            reason_codes.append("SEGMENT_ADDS_VISUAL_CATEGORY_VARIETY")
        if not reason_codes:
            reason_codes.append("SEGMENT_DIVERSITY_OBSERVED")

        return AssetSegmentDiversity(
            segment=segment_name,
            asset_path=path,
            category=category,
            source_type=entry.source_type if entry is not None else "",
            family=entry.family if entry is not None else "",
            repeated_asset=repeated_asset,
            repeated_category=repeated_category,
            progression_role=self._progression_role(segment_name),
            progression_contribution=progression_contribution,
            reason_codes=reason_codes,
            rationale=self._segment_rationale(
                segment_name=segment_name,
                category=category,
                repeated_asset=repeated_asset,
                repeated_category=repeated_category,
                progression_contribution=progression_contribution,
            ),
            metadata={
                "catalog_metadata_available": entry is not None,
                "category_count_in_sequence": category_counts.get(category, 0) if category else 0,
                "path_count_in_sequence": path_counts.get(path, 0) if path else 0,
            },
        )

    def _progression_level(
        self,
        *,
        selected_count: int,
        unique_category_count: int,
        repeated_asset_detected: bool,
    ) -> str:
        if selected_count == 0:
            return "none"
        if repeated_asset_detected:
            return "weak"
        if selected_count < 3:
            return "weak"
        if unique_category_count >= 3:
            return "strong"
        if unique_category_count == 2:
            return "moderate"
        return "weak"

    def _progression_contribution(
        self,
        *,
        path: str,
        category: str,
        repeated_asset: bool,
        repeated_category: bool,
    ) -> str:
        if not path:
            return "missing_asset"
        if repeated_asset:
            return "repeated_asset"
        if repeated_category:
            return "repeated_category"
        if category:
            return "unique_category"
        return "unknown_category"

    def _reason_codes(
        self,
        *,
        repeated_asset_detected: bool,
        repeated_category_detected: bool,
        visual_progression_level: str,
        fallback_used: bool,
    ) -> list[str]:
        codes: list[str] = []
        if repeated_asset_detected:
            codes.append("REPEATED_ASSET_PATH_DETECTED")
        if repeated_category_detected:
            codes.append("REPEATED_VISUAL_CATEGORY_DETECTED")
        if fallback_used:
            codes.append("FALLBACK_LIMITS_DIVERSITY_CONFIDENCE")
        codes.append(f"VISUAL_PROGRESSION_{visual_progression_level.upper()}")
        return codes

    def _rationale(
        self,
        *,
        repeated_asset_detected: bool,
        repeated_category_detected: bool,
        visual_progression_level: str,
        selected_count: int,
    ) -> list[str]:
        rationale = [
            f"{selected_count} selected segment assets were evaluated for repetition.",
            f"Visual progression level is {visual_progression_level}.",
        ]
        if repeated_asset_detected:
            rationale.append("At least one exact asset path is reused across segments.")
        if repeated_category_detected:
            rationale.append("At least one visual category repeats across segments.")
        if not repeated_asset_detected and visual_progression_level in {"moderate", "strong"}:
            rationale.append("No exact asset reuse was detected and category progression is observable.")
        return rationale

    def _segment_rationale(
        self,
        *,
        segment_name: str,
        category: str,
        repeated_asset: bool,
        repeated_category: bool,
        progression_contribution: str,
    ) -> list[str]:
        rationale = [
            f"{segment_name} uses category '{category or 'unknown'}'.",
            f"Progression contribution is {progression_contribution}.",
        ]
        if repeated_asset:
            rationale.append("The same asset path appears in another segment.")
        if repeated_category:
            rationale.append("The same category appears in another segment.")
        return rationale

    def _category(self, *, selector: AssetSelector, asset_selection: AssetPlan, segment_name: str, path: str) -> str:
        segment = asset_selection.segments.get(segment_name)
        if segment is not None and segment.category:
            return segment.category
        entry = selector.lookup_catalog_entry(path=path) if path else None
        return entry.category if entry is not None else ""

    def _progression_role(self, segment_name: str) -> str:
        return {
            "hook": "attention_anchor",
            "setup": "context_bridge",
            "payoff": "reveal_evidence",
        }.get(segment_name, "context")

    def _selected_path(self, *, asset_selection: AssetPlan, segment_name: str) -> str:
        if segment_name == "hook":
            return asset_selection.hook_asset
        if segment_name == "setup":
            return asset_selection.setup_asset
        if segment_name == "payoff":
            return asset_selection.payoff_asset
        return ""
