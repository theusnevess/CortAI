from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.assets.catalog_registry import increment_usage_counts
from app.assets.comfyui_image_service import ComfyUIImageError, ComfyUIImageService
from app.creative.contracts.creative_pack import AssetBackgroundPlan, AssetPlan, AssetSegmentPlan
from app.runtime.asset_selector import AssetSelector, CatalogEntry


@dataclass
class AssetRouter:
    selector: AssetSelector = field(default_factory=AssetSelector)
    comfyui_service: ComfyUIImageService = field(default_factory=ComfyUIImageService)

    def resolve_plan(self, *, asset_plan: AssetPlan, render_job_id: str) -> tuple[AssetPlan, dict[str, object]]:
        used_paths: set[str] = set()
        trace_rows: list[dict[str, object]] = []
        resolved_segments: dict[str, AssetSegmentPlan] = {}

        for segment_name in ("hook", "setup", "payoff"):
            segment = asset_plan.segments.get(segment_name, AssetSegmentPlan())
            resolved_bg, trace = self._resolve_segment(
                segment_name=segment_name,
                segment=segment,
                asset_plan=asset_plan,
                render_job_id=render_job_id,
                used_paths=used_paths,
            )
            used_paths.add(resolved_bg.path)
            resolved_segments[segment_name] = AssetSegmentPlan(
                background=resolved_bg,
                category=segment.category,
                tags=list(segment.tags),
                effects=list(segment.effects),
                decision_contract=segment.decision_contract,
                visual_query=segment.visual_query,
            )
            trace_rows.append(trace)

        resolved_segments, trace_rows, kill_switch_meta = self._enforce_video_level_solution_kill_switch(
            asset_plan=asset_plan,
            render_job_id=render_job_id,
            resolved_segments=resolved_segments,
            trace_rows=trace_rows,
        )

        resolved = AssetPlan(
            hook_asset=resolved_segments["hook"].background.path,
            setup_asset=resolved_segments["setup"].background.path,
            payoff_asset=resolved_segments["payoff"].background.path,
            visual_style=asset_plan.visual_style,
            motion_profile=asset_plan.motion_profile,
            visual_anchor=asset_plan.visual_anchor,
            semantic_pattern=asset_plan.semantic_pattern,
            entity=asset_plan.entity,
            case_visual_pack=dict(asset_plan.case_visual_pack),
            segments=resolved_segments,
            runtime_constraints=asset_plan.runtime_constraints,
        )
        trace = {
            "render_job_id": render_job_id,
            "visual_anchor": asset_plan.visual_anchor,
            "semantic_pattern": asset_plan.semantic_pattern,
            "entity": asset_plan.entity,
            "case_visual_pack": dict(asset_plan.case_visual_pack),
            "video_solution_validation": kill_switch_meta,
            "rows": trace_rows,
        }
        increment_usage_counts([
            segment.background.path
            for segment in resolved_segments.values()
            if segment.background.path
        ])
        return resolved, trace

    def _enforce_video_level_solution_kill_switch(
        self,
        *,
        asset_plan: AssetPlan,
        render_job_id: str,
        resolved_segments: dict[str, AssetSegmentPlan],
        trace_rows: list[dict[str, object]],
    ) -> tuple[dict[str, AssetSegmentPlan], list[dict[str, object]], dict[str, object]]:
        requested_case_pack = self.selector.requested_case_pack(
            tags=[tag for segment in resolved_segments.values() for tag in segment.tags],
            query_text=" ".join(
                part
                for part in (
                    asset_plan.visual_anchor,
                    asset_plan.semantic_pattern,
                    asset_plan.entity,
                    " ".join(tag for segment in resolved_segments.values() for tag in segment.tags),
                )
                if part
            ),
        )
        if not any(requested_case_pack.values()):
            return resolved_segments, trace_rows, {
                "valid": True,
                "rebuild_used": False,
                "failure_code": "",
                "kill_switch_active": False,
            }
        hook_entry = self._signature_entry_for_segment(
            segment_name="hook",
            segment=resolved_segments["hook"],
            render_job_id=render_job_id,
        )
        setup_entry = self._signature_entry_for_segment(
            segment_name="setup",
            segment=resolved_segments["setup"],
            render_job_id=render_job_id,
        )
        payoff_entry = self._signature_entry_for_segment(
            segment_name="payoff",
            segment=resolved_segments["payoff"],
            render_job_id=render_job_id,
        )
        valid, error_code = self.selector.validate_and_register_video_signature(
            hook_candidate=hook_entry,
            setup_candidate=setup_entry,
            payoff_candidate=payoff_entry,
            requested_case_pack=requested_case_pack,
        )
        if valid:
            return resolved_segments, trace_rows, {
                "valid": True,
                "rebuild_used": False,
                "failure_code": "",
                "kill_switch_active": True,
            }
        raise RuntimeError(error_code or "ASSET_RUNTIME_REPEATED_SIGNATURE")

    def _signature_entry_for_segment(
        self,
        *,
        segment_name: str,
        segment: AssetSegmentPlan,
        render_job_id: str,
    ) -> CatalogEntry | None:
        path = (segment.background.path or "").strip()
        if not path:
            return None
        entry = self.selector.lookup_catalog_entry(path=path)
        if entry is not None:
            return entry
        if segment.background.source == "comfyui":
            return CatalogEntry(
                path=path,
                category=segment.category or "generated",
                subtype="comfyui_generated",
                family=segment.category or "generated",
                framing=segment.visual_query.framing or "medium",
                tags=list(segment.tags),
                mood=segment.visual_query.mood or "",
                semantic_pattern_fit=[],
                entity_fit=[segment.decision_contract.entity] if segment.decision_contract.entity else [],
                hook_strength_score=0.8,
                payoff_strength_score=0.8,
                setup_specificity_score=0.8,
                realism_score=0.7,
                source_type="comfyui",
                usage_count=0,
                freshness_score=1.0,
                resolution=[832, 1472],
                strength=0.85,
                genericity=0.05,
                phase1_legacy=False,
                eligible_for_runtime=True,
            )
        return None

    def _resolve_segment(
        self,
        *,
        segment_name: str,
        segment: AssetSegmentPlan,
        asset_plan: AssetPlan,
        render_job_id: str,
        used_paths: set[str],
    ) -> tuple[AssetBackgroundPlan, dict[str, object]]:
        seed = asset_plan.runtime_constraints.deterministic_seed or render_job_id
        requested = segment.background.to_dict()
        path = ""
        source = ""
        query_text = " ".join(
            part
            for part in (
                segment.visual_query.search_query_real,
                asset_plan.visual_anchor,
                asset_plan.semantic_pattern,
                asset_plan.entity,
                " ".join(segment.tags),
            )
            if part
        )

        if segment.background.path:
            candidate = Path(segment.background.path)
            if candidate.exists() and (
                self.selector.is_runtime_eligible_path(path=str(candidate))
                or segment.background.source == "comfyui"
            ):
                path = str(candidate)
                entry = self.selector.lookup_catalog_entry(path=path)
                source = (entry.source_type if entry is not None else segment.background.source or "local")

        if not path:
            selected = self.selector.select(
                category=segment.category or asset_plan.visual_anchor or "room",
                tags=list(segment.tags),
                seed=f"{seed}:{segment_name}",
                exclude_paths=used_paths,
                query_text=query_text,
                minimum_score=6.0 if segment_name == "setup" else 7.0,
                segment_role=segment_name,
            )
            if selected:
                path = selected
                entry = self.selector.lookup_catalog_entry(path=selected)
                source = entry.source_type if entry is not None else "local"

        if not path and asset_plan.runtime_constraints.allow_safe_fallback:
            selected = self.selector.safe_fallback(seed=f"{seed}:{segment_name}:safe")
            if selected:
                path = selected
                entry = self.selector.lookup_catalog_entry(path=selected)
                source = entry.source_type if entry is not None else "fallback"

        if path and asset_plan.runtime_constraints.allow_comfyui_edit and self._segment_requests_comfyui_edit(segment=segment):
            try:
                edited = self.comfyui_service.edit_image(
                    prompt=self._comfyui_edit_prompt(
                        asset_plan=asset_plan,
                        segment=segment,
                        segment_name=segment_name,
                    ),
                    input_image_path=path,
                    render_job_id=render_job_id,
                    segment_name=segment_name,
                )
                path = edited.image_path
                source = edited.source_type
            except ComfyUIImageError as exc:
                raise RuntimeError(f"ASSET_RUNTIME_COMFYUI_EDIT_FAILED:{exc}") from exc

        if not path and asset_plan.runtime_constraints.allow_comfyui_generation_fallback:
            try:
                generated = self.comfyui_service.generate_image(
                    prompt=self._comfyui_generation_prompt(
                        asset_plan=asset_plan,
                        segment=segment,
                        segment_name=segment_name,
                    ),
                    render_job_id=render_job_id,
                    segment_name=segment_name,
                    seed=f"{seed}:{segment_name}:comfyui",
                )
                path = generated.image_path
                source = generated.source_type
            except ComfyUIImageError as exc:
                raise RuntimeError(f"ASSET_RUNTIME_COMFYUI_GENERATION_FAILED:{exc}") from exc

        if not path:
            raise RuntimeError("ASSET_RUNTIME_NO_EXTERNAL_ASSET")

        resolved = AssetBackgroundPlan(
            source=source or "local",
            path=path,
        )
        trace = {
            "segment": segment_name,
            "requested_asset": requested,
            "resolved_asset": resolved.to_dict(),
            "category": segment.category,
            "search_query_real": segment.visual_query.search_query_real,
            "query_text_sent_to_selector": query_text,
            "visual_query": segment.visual_query.to_dict(),
            "tags": list(segment.tags),
            "effects": list(segment.effects),
            "source": resolved.source,
            "entity": segment.decision_contract.entity,
            "event": segment.decision_contract.event,
            "anomaly_type": segment.decision_contract.anomaly_type,
            "visibility_requirement": segment.decision_contract.visibility_requirement,
            "photographability": segment.decision_contract.photographability,
            "justification": segment.decision_contract.justification,
        }
        return resolved, trace

    def _segment_requests_comfyui_edit(self, *, segment: AssetSegmentPlan) -> bool:
        effects = {str(item).strip().lower() for item in segment.effects}
        return bool({"comfyui_edit", "ai_edit", "enhance_with_comfyui"} & effects)

    def _comfyui_generation_prompt(
        self,
        *,
        asset_plan: AssetPlan,
        segment: AssetSegmentPlan,
        segment_name: str,
    ) -> str:
        query = segment.visual_query
        return ", ".join(
            part
            for part in (
                query.framing,
                query.subject,
                query.state_or_event,
                f"in {query.environment}" if query.environment else "",
                query.lighting,
                query.mood,
                "photorealistic vertical frame",
                f"case world {asset_plan.visual_anchor}" if asset_plan.visual_anchor else "",
                f"segment {segment_name}",
            )
            if part
        )

    def _comfyui_edit_prompt(
        self,
        *,
        asset_plan: AssetPlan,
        segment: AssetSegmentPlan,
        segment_name: str,
    ) -> str:
        query = segment.visual_query
        return "Preserve the scene but increase case-specific evidence: " + ", ".join(
            part
            for part in (
                query.subject,
                query.state_or_event,
                query.environment,
                query.lighting,
                query.mood,
                asset_plan.semantic_pattern,
                segment.decision_contract.justification,
                f"segment {segment_name}",
            )
            if part
        )
