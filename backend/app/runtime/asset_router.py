from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.assets.catalog_registry import increment_usage_counts
from app.assets.comfyui_image_service import ComfyUIImageError, ComfyUIImageService
from app.creative.contracts.creative_pack import AssetBackgroundPlan, AssetPlan, AssetSegmentPlan, VisualQuery
from app.runtime.asset_selector import AssetSelector, CatalogEntry


@dataclass
class AssetRouter:
    selector: AssetSelector = field(default_factory=AssetSelector)
    comfyui_service: ComfyUIImageService = field(default_factory=ComfyUIImageService)
    signature_rebuild_attempts: int = 4

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
                "signature_metrics": self.selector.signature_metrics(requested_case_pack=requested_case_pack),
            }
        rebuilt = self._attempt_signature_rebuild(
            asset_plan=asset_plan,
            render_job_id=render_job_id,
            resolved_segments=resolved_segments,
            trace_rows=trace_rows,
            requested_case_pack=requested_case_pack,
            initial_failure_code=error_code or "ASSET_RUNTIME_REPEATED_SIGNATURE",
        )
        if rebuilt is not None:
            return rebuilt
        failed_codes = getattr(self, "_last_signature_rebuild_failed_codes", [])
        if failed_codes:
            raise RuntimeError(
                f"{error_code or 'ASSET_RUNTIME_REPEATED_SIGNATURE'}:REBUILD_EXHAUSTED:"
                + "|".join(str(item) for item in failed_codes)
            )
        raise RuntimeError(error_code or "ASSET_RUNTIME_REPEATED_SIGNATURE")

    def _attempt_signature_rebuild(
        self,
        *,
        asset_plan: AssetPlan,
        render_job_id: str,
        resolved_segments: dict[str, AssetSegmentPlan],
        trace_rows: list[dict[str, object]],
        requested_case_pack: dict[str, set[str]],
        initial_failure_code: str,
    ) -> tuple[dict[str, AssetSegmentPlan], list[dict[str, object]], dict[str, object]] | None:
        failed_codes = [initial_failure_code]
        rebuild_strategies: tuple[tuple[tuple[str, ...], bool], ...] = (
            (("payoff",), False),
            (("setup", "payoff"), False),
            (("hook", "setup", "payoff"), False),
            (("payoff",), True),
        )
        max_attempts = max(0, min(self.signature_rebuild_attempts, len(rebuild_strategies)))
        for attempt, (roles_to_rebuild, use_signature_escape) in enumerate(rebuild_strategies[:max_attempts], start=1):
            snapshot = self._selection_state_snapshot()
            try:
                candidate_segments, candidate_rows = self._rebuild_signature_retry_segments(
                    asset_plan=asset_plan,
                    render_job_id=render_job_id,
                    resolved_segments=resolved_segments,
                    retry_attempt=attempt,
                    roles_to_rebuild=set(roles_to_rebuild),
                    use_signature_escape=use_signature_escape,
                )
                hook_entry = self._signature_entry_for_segment(
                    segment_name="hook",
                    segment=candidate_segments["hook"],
                    render_job_id=render_job_id,
                )
                setup_entry = self._signature_entry_for_segment(
                    segment_name="setup",
                    segment=candidate_segments["setup"],
                    render_job_id=render_job_id,
                )
                payoff_entry = self._signature_entry_for_segment(
                    segment_name="payoff",
                    segment=candidate_segments["payoff"],
                    render_job_id=render_job_id,
                )
                valid, error_code = self.selector.validate_and_register_video_signature(
                    hook_candidate=hook_entry,
                    setup_candidate=setup_entry,
                    payoff_candidate=payoff_entry,
                    requested_case_pack=requested_case_pack,
                )
            except RuntimeError as exc:
                self._restore_selection_state(snapshot)
                failed_codes.append(str(exc) or "ASSET_RUNTIME_REBUILD_FAILED")
                continue

            if valid:
                return candidate_segments, trace_rows + candidate_rows, {
                    "valid": True,
                    "rebuild_used": True,
                    "rebuild_attempts": attempt,
                    "rebuild_roles": list(roles_to_rebuild),
                    "rebuild_signature_escape_used": use_signature_escape,
                    "failure_code": "",
                    "initial_failure_code": initial_failure_code,
                    "failed_attempt_codes": failed_codes,
                    "kill_switch_active": True,
                    "signature_metrics": self.selector.signature_metrics(requested_case_pack=requested_case_pack),
                }
            self._restore_selection_state(snapshot)
            failed_codes.append(error_code or "ASSET_RUNTIME_REPEATED_SIGNATURE")
        self._last_signature_rebuild_failed_codes = failed_codes
        return None

    def _rebuild_signature_retry_segments(
        self,
        *,
        asset_plan: AssetPlan,
        render_job_id: str,
        resolved_segments: dict[str, AssetSegmentPlan],
        retry_attempt: int,
        roles_to_rebuild: set[str],
        use_signature_escape: bool,
    ) -> tuple[dict[str, AssetSegmentPlan], list[dict[str, object]]]:
        retry_segments: dict[str, AssetSegmentPlan] = {}
        retry_rows: list[dict[str, object]] = []
        used_paths = {
            segment.background.path
            for segment in resolved_segments.values()
            if segment.background.path
        }
        mode = "signature-escape" if use_signature_escape else "standard"
        seed_suffix = f":signature-retry:{retry_attempt}:{mode}:{'-'.join(sorted(roles_to_rebuild))}"
        for segment_name in ("hook", "setup", "payoff"):
            original = resolved_segments[segment_name]
            if segment_name not in roles_to_rebuild:
                retry_segments[segment_name] = original
                self._prime_retry_sequence_context(
                    asset_plan=asset_plan,
                    render_job_id=render_job_id,
                    retry_segments=retry_segments,
                    seed_suffix=seed_suffix,
                )
                continue

            retry_segment = AssetSegmentPlan(
                background=AssetBackgroundPlan(source=original.background.source, path=""),
                category=self._signature_retry_category(
                    segment_name=segment_name,
                    original_category=original.category,
                    use_signature_escape=use_signature_escape,
                ),
                tags=self._signature_retry_tags(
                    segment_name=segment_name,
                    original_tags=list(original.tags),
                    use_signature_escape=use_signature_escape,
                ),
                effects=list(original.effects),
                decision_contract=original.decision_contract,
                visual_query=self._signature_retry_visual_query(
                    segment_name=segment_name,
                    original_query=original.visual_query,
                    use_signature_escape=use_signature_escape,
                ),
            )
            resolved_bg, trace = self._resolve_segment(
                segment_name=segment_name,
                segment=retry_segment,
                asset_plan=asset_plan,
                render_job_id=render_job_id,
                used_paths=used_paths,
                seed_suffix=seed_suffix,
            )
            used_paths.add(resolved_bg.path)
            retry_segments[segment_name] = AssetSegmentPlan(
                background=resolved_bg,
                category=original.category,
                tags=list(original.tags),
                effects=list(original.effects),
                decision_contract=original.decision_contract,
                visual_query=original.visual_query,
            )
            trace = dict(trace)
            trace["signature_rebuild_attempt"] = retry_attempt
            trace["signature_rebuild"] = True
            trace["signature_rebuild_roles"] = list(sorted(roles_to_rebuild))
            trace["signature_rebuild_escape"] = use_signature_escape
            retry_rows.append(trace)
        return retry_segments, retry_rows

    def _signature_retry_category(
        self,
        *,
        segment_name: str,
        original_category: str,
        use_signature_escape: bool,
    ) -> str:
        if not use_signature_escape:
            return original_category
        if segment_name == "payoff":
            return "document"
        if segment_name == "setup":
            return "investigative_interior"
        return original_category

    def _signature_retry_tags(
        self,
        *,
        segment_name: str,
        original_tags: list[str],
        use_signature_escape: bool,
    ) -> list[str]:
        if not use_signature_escape:
            return original_tags
        if segment_name == "payoff":
            return [
                "case_object_document",
                "case_evidence_document",
                "case_evidence_contradiction_proof",
                "case_state_timestamp_anomaly",
            ]
        if segment_name == "setup":
            return [
                "case_environment_evidence_desk",
                "case_state_contradiction",
                "case_progression_context",
            ]
        return original_tags

    def _signature_retry_visual_query(
        self,
        *,
        segment_name: str,
        original_query: VisualQuery,
        use_signature_escape: bool,
    ) -> VisualQuery:
        if not use_signature_escape:
            return original_query
        if segment_name == "payoff":
            return VisualQuery(
                subject="document evidence close up",
                state_or_event="timestamp contradiction proof",
                environment="evidence desk",
                lighting=original_query.lighting or "low key",
                framing="detail",
                mood=original_query.mood or "tense",
                search_query_real="case document timestamp evidence close up",
            )
        if segment_name == "setup":
            return VisualQuery(
                subject="investigative evidence desk",
                state_or_event="case context review",
                environment="investigation room",
                lighting=original_query.lighting or "low key",
                framing=original_query.framing or "medium",
                mood=original_query.mood or "tense",
                search_query_real="investigation room evidence desk",
            )
        return original_query

    def _prime_retry_sequence_context(
        self,
        *,
        asset_plan: AssetPlan,
        render_job_id: str,
        retry_segments: dict[str, AssetSegmentPlan],
        seed_suffix: str,
    ) -> None:
        if not retry_segments:
            return
        base_seed = f"{asset_plan.runtime_constraints.deterministic_seed or render_job_id}{seed_suffix}"
        context = self.selector._sequence_context(seed=f"{base_seed}:payoff", segment_role="payoff")
        for segment_name in ("hook", "setup"):
            segment = retry_segments.get(segment_name)
            if segment is None:
                continue
            entry = self._signature_entry_for_segment(
                segment_name=segment_name,
                segment=segment,
                render_job_id=render_job_id,
            )
            if entry is not None:
                context[segment_name] = entry

    def _selection_state_snapshot(self) -> dict[str, object]:
        return {
            "selection_contexts": {
                key: dict(value)
                for key, value in self.selector._selection_contexts.items()
            },
            "batch_family_usage": dict(self.selector._batch_family_usage),
            "batch_family_usage_by_role": dict(self.selector._batch_family_usage_by_role),
        }

    def _restore_selection_state(self, snapshot: dict[str, object]) -> None:
        self.selector._selection_contexts = {
            str(key): dict(value)
            for key, value in dict(snapshot.get("selection_contexts", {})).items()
        }
        self.selector._batch_family_usage = dict(snapshot.get("batch_family_usage", {}))
        self.selector._batch_family_usage_by_role = dict(snapshot.get("batch_family_usage_by_role", {}))

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
        seed_suffix: str = "",
    ) -> tuple[AssetBackgroundPlan, dict[str, object]]:
        seed = f"{asset_plan.runtime_constraints.deterministic_seed or render_job_id}{seed_suffix}"
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
            selected = self.selector.safe_fallback(seed=f"{seed}:{segment_name}:safe", exclude_paths=used_paths)
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
