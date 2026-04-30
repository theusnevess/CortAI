from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any

from app.creative.contracts.creative_pack import AssetPlan
from app.runtime.asset_selector import AssetSelector, CatalogEntry


VISUAL_ALIGNMENT_VERSION = "asset_visual_semantic_alignment_v2_6"


@dataclass(frozen=True)
class AssetSegmentVisualAlignment:
    segment: str
    requested_category: str
    selected_category: str
    selected_asset_path: str
    category_match: bool
    tag_overlap_count: int
    tag_overlap_ratio: float
    query_overlap_count: int
    query_overlap_ratio: float
    alignment_score: float
    alignment_level: str
    mismatch_detected: bool
    mismatch_level: str
    reason_codes: list[str]
    rationale: list[str]
    requested_tags: list[str] = field(default_factory=list)
    selected_tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetVisualSemanticAlignment:
    alignment_version: str
    alignment_complete: bool
    overall_alignment_score: float
    overall_alignment_level: str
    segment_alignments: dict[str, AssetSegmentVisualAlignment]
    mismatched_segments: list[str]
    missing_metadata_segments: list[str]
    boundary_statement: str
    alignment_trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["segment_alignments"] = {
            name: alignment.to_dict()
            for name, alignment in self.segment_alignments.items()
        }
        return payload


@dataclass(frozen=True)
class AssetVisualSemanticAlignmentEvaluator:
    """Metadata-only visual alignment evaluator for already-selected assets."""

    def evaluate(
        self,
        *,
        selector: AssetSelector,
        asset_selection: AssetPlan,
        selection_requests: dict[str, dict[str, Any]] | None = None,
    ) -> AssetVisualSemanticAlignment:
        requests = selection_requests or {}
        alignments = {
            segment_name: self._segment_alignment(
                selector=selector,
                asset_selection=asset_selection,
                segment_name=segment_name,
                request=dict(requests.get(segment_name) or {}),
            )
            for segment_name in ("hook", "setup", "payoff")
        }
        scores = [
            alignment.alignment_score
            for alignment in alignments.values()
            if alignment.alignment_level != "unknown"
        ]
        overall_score = round(sum(scores) / len(scores), 4) if scores else 0.0
        mismatched_segments = [
            name
            for name, alignment in alignments.items()
            if alignment.mismatch_detected
        ]
        missing_metadata_segments = [
            name
            for name, alignment in alignments.items()
            if alignment.alignment_level == "unknown"
        ]
        alignment_complete = not mismatched_segments and not missing_metadata_segments

        return AssetVisualSemanticAlignment(
            alignment_version=VISUAL_ALIGNMENT_VERSION,
            alignment_complete=alignment_complete,
            overall_alignment_score=overall_score,
            overall_alignment_level=self._level(overall_score) if scores else "unknown",
            segment_alignments=alignments,
            mismatched_segments=mismatched_segments,
            missing_metadata_segments=missing_metadata_segments,
            boundary_statement="Visual semantic alignment is metadata-only; it does not inspect images, change ranking, or make QC decisions.",
            alignment_trace={
                "segments_evaluated": list(alignments.keys()),
                "image_analysis_used": False,
                "ml_used": False,
                "read_only": True,
                "selection_ranking_unchanged": True,
                "fallback_behavior_unchanged": True,
            },
        )

    def _segment_alignment(
        self,
        *,
        selector: AssetSelector,
        asset_selection: AssetPlan,
        segment_name: str,
        request: dict[str, Any],
    ) -> AssetSegmentVisualAlignment:
        segment = asset_selection.segments.get(segment_name)
        selected_path = self._selected_path(asset_selection=asset_selection, segment_name=segment_name)
        requested_category = str(request.get("requested_category") or (segment.category if segment else "") or "").strip()
        requested_tags = [str(tag).strip().lower() for tag in request.get("requested_tags", []) if str(tag).strip()]
        query_text = str(request.get("query_text") or "").strip()

        if not selected_path:
            return self._unknown_alignment(
                segment_name=segment_name,
                requested_category=requested_category,
                requested_tags=requested_tags,
                selected_path=selected_path,
                reason_code="SELECTED_ASSET_PATH_MISSING",
                rationale="Selected asset path is missing, so metadata alignment cannot be evaluated.",
            )

        entry = selector.lookup_catalog_entry(path=selected_path)
        if entry is None:
            return self._unknown_alignment(
                segment_name=segment_name,
                requested_category=requested_category,
                requested_tags=requested_tags,
                selected_path=selected_path,
                reason_code="SELECTED_ASSET_METADATA_MISSING",
                rationale="Selected asset is not present in the local catalog metadata.",
            )

        selected_category = str(entry.category or "").strip()
        category_match = self._normalize_value(requested_category) == self._normalize_value(selected_category)
        selected_tags = [str(tag).strip().lower() for tag in entry.tags if str(tag).strip()]
        tag_overlap_count, tag_overlap_ratio = self._overlap(
            set(requested_tags),
            set(selected_tags),
        )
        query_tokens = self._tokens(query_text)
        entry_tokens = self._entry_tokens(entry)
        query_overlap_count, query_overlap_ratio = self._overlap(query_tokens, entry_tokens)

        category_score = 0.55 if category_match else 0.0
        if not category_match and self._normalize_value(requested_category) in {self._normalize_value(tag) for tag in selected_tags}:
            category_score = 0.25
        tag_score = min(tag_overlap_ratio * 0.25, 0.25)
        query_score = min(query_overlap_ratio * 0.20, 0.20)
        alignment_score = round(category_score + tag_score + query_score, 4)
        mismatch_level = self._mismatch_level(
            category_match=category_match,
            tag_overlap_ratio=tag_overlap_ratio,
            query_overlap_ratio=query_overlap_ratio,
        )
        mismatch_detected = mismatch_level in {"medium", "high"}
        level = self._level(alignment_score)
        reason_codes = self._reason_codes(
            category_match=category_match,
            tag_overlap_count=tag_overlap_count,
            query_overlap_count=query_overlap_count,
            mismatch_level=mismatch_level,
        )

        return AssetSegmentVisualAlignment(
            segment=segment_name,
            requested_category=requested_category,
            selected_category=selected_category,
            selected_asset_path=selected_path,
            category_match=category_match,
            tag_overlap_count=tag_overlap_count,
            tag_overlap_ratio=tag_overlap_ratio,
            query_overlap_count=query_overlap_count,
            query_overlap_ratio=query_overlap_ratio,
            alignment_score=alignment_score,
            alignment_level=level,
            mismatch_detected=mismatch_detected,
            mismatch_level=mismatch_level,
            reason_codes=reason_codes,
            rationale=self._rationale(
                requested_category=requested_category,
                selected_category=selected_category,
                category_match=category_match,
                tag_overlap_count=tag_overlap_count,
                query_overlap_count=query_overlap_count,
                mismatch_level=mismatch_level,
            ),
            requested_tags=requested_tags,
            selected_tags=selected_tags,
            metadata={
                "source_type": entry.source_type,
                "family": entry.family,
                "subtype": entry.subtype,
                "mood": entry.mood,
                "eligible_for_runtime": entry.eligible_for_runtime,
            },
        )

    def _unknown_alignment(
        self,
        *,
        segment_name: str,
        requested_category: str,
        requested_tags: list[str],
        selected_path: str,
        reason_code: str,
        rationale: str,
    ) -> AssetSegmentVisualAlignment:
        return AssetSegmentVisualAlignment(
            segment=segment_name,
            requested_category=requested_category,
            selected_category="",
            selected_asset_path=selected_path,
            category_match=False,
            tag_overlap_count=0,
            tag_overlap_ratio=0.0,
            query_overlap_count=0,
            query_overlap_ratio=0.0,
            alignment_score=0.0,
            alignment_level="unknown",
            mismatch_detected=False,
            mismatch_level="unknown",
            reason_codes=[reason_code],
            rationale=[rationale],
            requested_tags=requested_tags,
            selected_tags=[],
        )

    def _reason_codes(
        self,
        *,
        category_match: bool,
        tag_overlap_count: int,
        query_overlap_count: int,
        mismatch_level: str,
    ) -> list[str]:
        codes = []
        codes.append("CATEGORY_MATCH" if category_match else "CATEGORY_MISMATCH")
        codes.append("TAG_OVERLAP_PRESENT" if tag_overlap_count else "TAG_OVERLAP_MISSING")
        codes.append("QUERY_OVERLAP_PRESENT" if query_overlap_count else "QUERY_OVERLAP_MISSING")
        if mismatch_level in {"medium", "high"}:
            codes.append(f"VISUAL_SEMANTIC_MISMATCH_{mismatch_level.upper()}")
        else:
            codes.append("VISUAL_SEMANTIC_ALIGNMENT_ACCEPTABLE")
        return codes

    def _rationale(
        self,
        *,
        requested_category: str,
        selected_category: str,
        category_match: bool,
        tag_overlap_count: int,
        query_overlap_count: int,
        mismatch_level: str,
    ) -> list[str]:
        rationale = [
            f"Requested category '{requested_category}' was compared with selected category '{selected_category}'.",
            f"Metadata overlap used {tag_overlap_count} tag matches and {query_overlap_count} query-token matches.",
        ]
        if category_match:
            rationale.append("Selected category matches the requested visual category.")
        elif mismatch_level in {"medium", "high"}:
            rationale.append("Selected category differs from the request and supporting metadata overlap is limited.")
        else:
            rationale.append("Selected category differs, but metadata overlap provides partial support.")
        return rationale

    def _mismatch_level(
        self,
        *,
        category_match: bool,
        tag_overlap_ratio: float,
        query_overlap_ratio: float,
    ) -> str:
        if category_match:
            return "none"
        if tag_overlap_ratio < 0.15 and query_overlap_ratio < 0.10:
            return "high"
        return "medium"

    def _level(self, score: float) -> str:
        if score >= 0.70:
            return "high"
        if score >= 0.45:
            return "medium"
        return "low"

    def _overlap(self, left: set[str], right: set[str]) -> tuple[int, float]:
        if not left:
            return 0, 0.0
        overlap_count = len(left & right)
        return overlap_count, round(overlap_count / len(left), 4)

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

    def _normalize_value(self, value: str) -> str:
        return re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower()).strip("_")

    def _selected_path(self, *, asset_selection: AssetPlan, segment_name: str) -> str:
        if segment_name == "hook":
            return asset_selection.hook_asset
        if segment_name == "setup":
            return asset_selection.setup_asset
        if segment_name == "payoff":
            return asset_selection.payoff_asset
        return ""
