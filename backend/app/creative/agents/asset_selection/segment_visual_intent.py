from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.creative.contracts.creative_pack import AssetPlan, AssetSegmentPlan


SEGMENT_VISUAL_INTENT_VERSION = "asset_segment_visual_intent_v2_6"


VISUAL_ROLES = {
    "hook": "attention_anchor",
    "setup": "context_bridge",
    "payoff": "reveal_evidence",
}


@dataclass(frozen=True)
class AssetSegmentVisualIntent:
    segment: str
    narrative_role: str
    visual_role: str
    requested_category: str
    requested_tags: list[str]
    intent_complete: bool
    rationale: list[str]
    selected_asset_path: str = ""
    requested_effects: list[str] = field(default_factory=list)
    visual_query: dict[str, Any] = field(default_factory=dict)
    decision_contract: dict[str, Any] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    degraded_fields: list[str] = field(default_factory=list)
    reason_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetSegmentVisualIntentMapping:
    mapping_version: str
    intent_complete: bool
    segments: dict[str, AssetSegmentVisualIntent]
    missing_segments: list[str]
    degraded_segments: list[str]
    boundary_statement: str
    rationale: list[str]
    intent_trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["segments"] = {
            name: intent.to_dict()
            for name, intent in self.segments.items()
        }
        return payload


@dataclass(frozen=True)
class AssetSegmentVisualIntentMapper:
    """Maps already-produced segment plans to explicit visual intent."""

    def map(self, *, asset_selection: AssetPlan) -> AssetSegmentVisualIntentMapping:
        segment_intents = {
            segment_name: self._segment_intent(
                segment_name=segment_name,
                segment=asset_selection.segments.get(segment_name, AssetSegmentPlan()),
                selected_path=self._selected_path(asset_selection=asset_selection, segment_name=segment_name),
            )
            for segment_name in ("hook", "setup", "payoff")
        }
        missing_segments = [
            name
            for name, intent in segment_intents.items()
            if "SEGMENT_PLAN_MISSING" in intent.reason_codes
        ]
        degraded_segments = [
            name
            for name, intent in segment_intents.items()
            if not intent.intent_complete and name not in missing_segments
        ]
        intent_complete = all(intent.intent_complete for intent in segment_intents.values())
        rationale = [
            "Segment visual intent is derived from the AssetPlan already produced by selection.",
            "The mapping is audit-only and does not alter selected assets, ranking, or fallback.",
        ]
        if degraded_segments:
            rationale.append("One or more segment intents are incomplete or degraded.")
        if missing_segments:
            rationale.append("One or more expected segment plans are missing.")

        return AssetSegmentVisualIntentMapping(
            mapping_version=SEGMENT_VISUAL_INTENT_VERSION,
            intent_complete=intent_complete,
            segments=segment_intents,
            missing_segments=missing_segments,
            degraded_segments=degraded_segments,
            boundary_statement="Asset Selection explains visual intent only; it does not create Strategy, QC, or Publisher authority.",
            rationale=rationale,
            intent_trace={
                "segment_count": len(segment_intents),
                "complete_segment_count": sum(1 for intent in segment_intents.values() if intent.intent_complete),
                "visual_roles": dict(VISUAL_ROLES),
                "read_only": True,
                "selection_ranking_unchanged": True,
                "fallback_behavior_unchanged": True,
            },
        )

    def _segment_intent(
        self,
        *,
        segment_name: str,
        segment: AssetSegmentPlan,
        selected_path: str,
    ) -> AssetSegmentVisualIntent:
        requested_category = str(segment.category or "").strip()
        requested_tags = [str(tag).strip() for tag in segment.tags if str(tag).strip()]
        requested_effects = [str(effect).strip() for effect in segment.effects if str(effect).strip()]
        visual_query = segment.visual_query.to_dict()
        decision_contract = segment.decision_contract.to_dict()
        missing_fields: list[str] = []
        degraded_fields: list[str] = []
        reason_codes: list[str] = []

        if segment == AssetSegmentPlan() and not selected_path:
            missing_fields.extend(["segment_plan", "selected_asset_path"])
            reason_codes.append("SEGMENT_PLAN_MISSING")
        if not requested_category:
            self._append_unique(missing_fields, "requested_category")
            reason_codes.append("REQUESTED_CATEGORY_MISSING")
        if not requested_tags:
            self._append_unique(missing_fields, "requested_tags")
            reason_codes.append("REQUESTED_TAGS_MISSING")
        if not selected_path:
            self._append_unique(missing_fields, "selected_asset_path")
            reason_codes.append("SELECTED_ASSET_PATH_MISSING")
        if not any(str(value or "").strip() for value in visual_query.values()):
            degraded_fields.append("visual_query")
            reason_codes.append("VISUAL_QUERY_EMPTY")
        if not any(str(value or "").strip() for value in decision_contract.values()):
            degraded_fields.append("decision_contract")
            reason_codes.append("DECISION_CONTRACT_EMPTY")

        intent_complete = not missing_fields and not degraded_fields
        if intent_complete:
            reason_codes.append("SEGMENT_VISUAL_INTENT_COMPLETE")
        rationale = self._rationale(
            segment_name=segment_name,
            requested_category=requested_category,
            requested_tags=requested_tags,
            selected_path=selected_path,
            intent_complete=intent_complete,
        )

        return AssetSegmentVisualIntent(
            segment=segment_name,
            narrative_role=segment_name,
            visual_role=VISUAL_ROLES.get(segment_name, "context"),
            requested_category=requested_category,
            requested_tags=requested_tags,
            intent_complete=intent_complete,
            rationale=rationale,
            selected_asset_path=selected_path,
            requested_effects=requested_effects,
            visual_query=visual_query,
            decision_contract=decision_contract,
            missing_fields=missing_fields,
            degraded_fields=degraded_fields,
            reason_codes=reason_codes,
        )

    def _rationale(
        self,
        *,
        segment_name: str,
        requested_category: str,
        requested_tags: list[str],
        selected_path: str,
        intent_complete: bool,
    ) -> list[str]:
        role = VISUAL_ROLES.get(segment_name, "context")
        if intent_complete:
            return [
                f"{segment_name} maps to visual role {role}.",
                f"Requested category {requested_category} and {len(requested_tags)} tags are present.",
                "Selected asset path is visible for audit linkage.",
            ]
        rationale = [f"{segment_name} maps to visual role {role}, but intent is incomplete."]
        if not requested_category:
            rationale.append("Requested category is missing.")
        if not requested_tags:
            rationale.append("Requested tags are missing.")
        if not selected_path:
            rationale.append("Selected asset path is missing.")
        return rationale

    def _selected_path(self, *, asset_selection: AssetPlan, segment_name: str) -> str:
        if segment_name == "hook":
            return asset_selection.hook_asset
        if segment_name == "setup":
            return asset_selection.setup_asset
        if segment_name == "payoff":
            return asset_selection.payoff_asset
        return ""

    def _append_unique(self, values: list[str], value: str) -> None:
        if value not in values:
            values.append(value)
