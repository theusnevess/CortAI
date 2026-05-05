from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import os
from pathlib import Path
import re

from app.content.backgrounds.service import BackgroundGeneratorService
from app.creative.agents.asset_selection.catalog_source_governance import AssetCatalogSourceGovernanceEvaluator
from app.creative.agents.asset_selection.confidence_calibration import AssetConfidenceCalibrator
from app.creative.agents.asset_selection.context_governance import AssetContextGovernanceEvaluator
from app.creative.agents.asset_selection.diversity_guard import AssetDiversityGuard
from app.creative.agents.asset_selection.fallback_honesty import AssetFallbackHonestyEvaluator
from app.creative.agents.asset_selection.segment_visual_intent import AssetSegmentVisualIntentMapper
from app.creative.agents.asset_selection.trace_auditability import AssetTraceBuilder
from app.creative.agents.asset_selection.visual_semantic_alignment import AssetVisualSemanticAlignmentEvaluator
from app.creative.agents.asset_selection.visual_truthfulness import AssetVisualTruthfulnessEvaluator
from app.creative.agents.asset.interpreter import AssetInterpreterService
from app.creative.agents.asset_selection.models import AssetSelectionInput, AssetSelectionResult
from app.creative.contracts.agent_common import FallbackDecision, FallbackMode
from app.creative.contracts.creative_pack import (
    AssetBackgroundPlan,
    AssetPlan,
    AssetSegmentPlan,
    ScriptPlan,
    StrategyProfile,
)
from app.runtime.asset_selector import AssetSelector


@dataclass
class AssetSelectionAgentService:
    background_service: BackgroundGeneratorService = field(default_factory=BackgroundGeneratorService)
    interpreter: AssetInterpreterService = field(default_factory=AssetInterpreterService)
    selector: AssetSelector = field(default_factory=AssetSelector)
    context_governance: AssetContextGovernanceEvaluator = field(default_factory=AssetContextGovernanceEvaluator)
    source_governance: AssetCatalogSourceGovernanceEvaluator = field(default_factory=AssetCatalogSourceGovernanceEvaluator)
    segment_intent_mapper: AssetSegmentVisualIntentMapper = field(default_factory=AssetSegmentVisualIntentMapper)
    visual_alignment_evaluator: AssetVisualSemanticAlignmentEvaluator = field(default_factory=AssetVisualSemanticAlignmentEvaluator)
    visual_truthfulness_evaluator: AssetVisualTruthfulnessEvaluator = field(default_factory=AssetVisualTruthfulnessEvaluator)
    fallback_honesty_evaluator: AssetFallbackHonestyEvaluator = field(default_factory=AssetFallbackHonestyEvaluator)
    diversity_guard: AssetDiversityGuard = field(default_factory=AssetDiversityGuard)
    confidence_calibrator: AssetConfidenceCalibrator = field(default_factory=AssetConfidenceCalibrator)
    trace_builder: AssetTraceBuilder = field(default_factory=AssetTraceBuilder)

    def select(self, data: AssetSelectionInput) -> AssetSelectionResult:
        local_assets_available = self._has_local_assets()
        if not local_assets_available:
            fallback_result = self._fallback_result()
            return self._with_context_governance(
                data=data,
                result=fallback_result,
                local_assets_available=False,
                script_plan_used=None,
                script_fallback_used=False,
                selection_requests={},
                segment_fallback_trace={},
            )
        script_fallback_used = data.script_plan is None
        script_plan = data.script_plan or self._fallback_script_plan(data.topic)
        seed = self._selection_key(data.niche, data.topic, script_plan, data.strategy_profile)
        plan = self.interpreter.build_plan(
            niche=data.niche,
            topic=data.topic,
            script_plan=script_plan,
            trend_profile=data.trend_profile,
            deterministic_seed=seed,
        )
        plan = self._apply_strategy_plan_variation(
            plan=plan,
            strategy_profile=data.strategy_profile,
            script_plan=script_plan,
        )
        resolved_segments: dict[str, AssetSegmentPlan] = {}
        selection_requests: dict[str, dict[str, object]] = {}
        segment_fallback_trace: dict[str, dict[str, object]] = {}
        used_paths: set[str] = set()
        for segment_name in ("hook", "setup", "payoff"):
            segment = plan.segments.get(segment_name, AssetSegmentPlan())
            payoff_evidence = self._payoff_evidence_profile(
                segment_name=segment_name,
                script_plan=script_plan,
            )
            effective_category = self._selection_category(
                segment=segment,
                plan=plan,
                segment_name=segment_name,
                strategy_profile=data.strategy_profile,
                payoff_evidence=payoff_evidence,
            )
            effective_tags = self._selection_tags(
                segment=segment,
                segment_name=segment_name,
                strategy_profile=data.strategy_profile,
                payoff_evidence=payoff_evidence,
            )
            query_text = self._segment_query_text(
                segment_name=segment_name,
                topic=data.topic,
                script_plan=script_plan,
                asset_plan=plan,
                strategy_profile=data.strategy_profile,
                payoff_evidence=payoff_evidence,
            )
            minimum_score = self._minimum_local_score(
                segment_name=segment_name,
                strategy_profile=data.strategy_profile,
                payoff_evidence=payoff_evidence,
            )
            selection_requests[segment_name] = {
                "requested_category": effective_category,
                "requested_tags": list(effective_tags),
                "query_text": query_text,
                "minimum_score": minimum_score,
            }
            local_path = self.selector.select(
                category=effective_category,
                tags=effective_tags,
                seed=f"{seed}:{segment_name}",
                exclude_paths=used_paths,
                query_text=query_text,
                minimum_score=minimum_score,
                segment_role=segment_name,
            ) or ""
            primary_local_path = local_path
            primary_selector_returned_asset = bool(local_path)
            local_path = self._enforce_payoff_evidence_category(
                local_path=local_path,
                effective_category=effective_category,
                effective_tags=effective_tags,
                query_text=query_text,
                seed=seed,
                segment_name=segment_name,
                exclude_paths=used_paths,
                payoff_evidence=payoff_evidence,
            )
            exact_enforcement_changed_asset = bool(local_path) and local_path != primary_local_path
            safe_fallback_used = False
            if not local_path:
                fallback_path = self.selector.safe_fallback(seed=f"{seed}:{segment_name}:safe") or ""
                safe_fallback_used = bool(fallback_path)
                local_path = fallback_path
            segment_fallback_trace[segment_name] = {
                "primary_selector_returned_asset": primary_selector_returned_asset,
                "safe_fallback_used": safe_fallback_used,
                "exact_enforcement_changed_asset": exact_enforcement_changed_asset,
            }
            selected_entry = self.selector.lookup_catalog_entry(path=local_path) if local_path else None
            background = AssetBackgroundPlan(
                source=(selected_entry.source_type if selected_entry is not None else "local"),
                path=local_path,
            )
            if local_path:
                used_paths.add(local_path)
            realized_category = selected_entry.category if selected_entry is not None else effective_category
            resolved_segments[segment_name] = AssetSegmentPlan(
                background=background,
                category=realized_category,
                tags=list(effective_tags),
                effects=list(segment.effects),
                decision_contract=segment.decision_contract,
                visual_query=segment.visual_query,
            )

        finalized = AssetPlan(
            hook_asset=resolved_segments["hook"].background.path,
            setup_asset=resolved_segments["setup"].background.path,
            payoff_asset=resolved_segments["payoff"].background.path,
            visual_style=plan.visual_style,
            motion_profile=plan.motion_profile,
            visual_anchor=plan.visual_anchor,
            semantic_pattern=plan.semantic_pattern,
            entity=plan.entity,
            case_visual_pack=dict(plan.case_visual_pack),
            segments=resolved_segments,
            runtime_constraints=plan.runtime_constraints,
        )
        missing_segments = [
            name
            for name, segment in resolved_segments.items()
            if not segment.background.path
        ]
        fallback = FallbackDecision(
            used=bool(missing_segments),
            mode=FallbackMode.NONE.value if not missing_segments else FallbackMode.LOCAL_DEFAULT.value,
            reason="" if not missing_segments else "ASSET_SELECTION_MISSING_SEGMENT",
        )
        return self._with_context_governance(
            data=data,
            result=AssetSelectionResult(asset_selection=finalized, fallback=fallback),
            local_assets_available=local_assets_available,
            script_plan_used=script_plan,
            script_fallback_used=script_fallback_used,
            selection_requests=selection_requests,
            segment_fallback_trace=segment_fallback_trace,
        )

    def _with_context_governance(
        self,
        *,
        data: AssetSelectionInput,
        result: AssetSelectionResult,
        local_assets_available: bool,
        script_plan_used: ScriptPlan | None,
        script_fallback_used: bool,
        selection_requests: dict[str, dict[str, object]] | None = None,
        segment_fallback_trace: dict[str, dict[str, object]] | None = None,
    ) -> AssetSelectionResult:
        governance = self.context_governance.evaluate(
            data=data,
            asset_selection=result.asset_selection,
            local_assets_available=local_assets_available,
            script_plan_used=script_plan_used,
            script_fallback_used=script_fallback_used,
            asset_fallback_used=result.fallback.used,
            asset_fallback_reason=result.fallback.reason,
        )
        source_governance = self.source_governance.evaluate(
            selector=self.selector,
            asset_selection=result.asset_selection,
            fallback=result.fallback,
            local_assets_available=local_assets_available,
        )
        segment_intent = self.segment_intent_mapper.map(asset_selection=result.asset_selection)
        visual_alignment = self.visual_alignment_evaluator.evaluate(
            selector=self.selector,
            asset_selection=result.asset_selection,
            selection_requests=selection_requests,
        )
        visual_truthfulness = self.visual_truthfulness_evaluator.evaluate(
            selector=self.selector,
            asset_selection=result.asset_selection,
            fallback=result.fallback,
            visual_alignment=visual_alignment.to_dict(),
        )
        fallback_honesty = self.fallback_honesty_evaluator.evaluate(
            asset_selection=result.asset_selection,
            fallback=result.fallback,
            segment_fallback_trace=segment_fallback_trace,
            visual_alignment=visual_alignment.to_dict(),
            visual_truthfulness=visual_truthfulness.to_dict(),
        )
        asset_diversity = self.diversity_guard.evaluate(
            selector=self.selector,
            asset_selection=result.asset_selection,
            fallback=result.fallback,
        )
        confidence = self.confidence_calibrator.calibrate(
            asset_context_governance=governance.to_dict(),
            asset_source_governance=source_governance.to_dict(),
            segment_visual_intent=segment_intent.to_dict(),
            visual_alignment=visual_alignment.to_dict(),
            visual_truthfulness=visual_truthfulness.to_dict(),
            asset_fallback_honesty=fallback_honesty.to_dict(),
            asset_diversity=asset_diversity.to_dict(),
        )
        asset_trace = self.trace_builder.build(
            asset_selection=result.asset_selection,
            fallback=result.fallback,
            asset_context_governance=governance.to_dict(),
            asset_source_governance=source_governance.to_dict(),
            segment_visual_intent=segment_intent.to_dict(),
            visual_alignment=visual_alignment.to_dict(),
            visual_truthfulness=visual_truthfulness.to_dict(),
            asset_fallback_honesty=fallback_honesty.to_dict(),
            asset_diversity=asset_diversity.to_dict(),
            confidence=confidence.confidence,
            confidence_level=confidence.confidence_level,
            confidence_components=confidence.confidence_components,
            confidence_rationale=confidence.confidence_rationale,
        )
        return AssetSelectionResult(
            asset_selection=result.asset_selection,
            fallback=result.fallback,
            asset_context_governance=governance.to_dict(),
            asset_source_governance=source_governance.to_dict(),
            segment_visual_intent=segment_intent.to_dict(),
            visual_alignment=visual_alignment.to_dict(),
            visual_truthfulness=visual_truthfulness.to_dict(),
            asset_fallback_honesty=fallback_honesty.to_dict(),
            asset_diversity=asset_diversity.to_dict(),
            confidence=confidence.confidence,
            confidence_level=confidence.confidence_level,
            confidence_components=confidence.confidence_components,
            confidence_rationale=confidence.confidence_rationale,
            asset_trace=asset_trace,
        )

    def _enforce_payoff_evidence_category(
        self,
        *,
        local_path: str,
        effective_category: str,
        effective_tags: list[str],
        query_text: str,
        seed: str,
        segment_name: str,
        exclude_paths: set[str],
        payoff_evidence: dict[str, object] | None,
    ) -> str:
        if segment_name != "payoff":
            return local_path
        if not payoff_evidence or not payoff_evidence.get("category"):
            return local_path
        selected_entry = self.selector.lookup_catalog_entry(path=local_path) if local_path else None
        if selected_entry is not None and selected_entry.category == effective_category:
            return local_path
        exact_match = self._select_exact_category_asset(
            category=effective_category,
            tags=effective_tags,
            query_text=query_text,
            seed=f"{seed}:{segment_name}:exact",
            exclude_paths=exclude_paths | ({local_path} if local_path else set()),
        )
        return exact_match or local_path

    def _select_exact_category_asset(
        self,
        *,
        category: str,
        tags: list[str],
        query_text: str,
        seed: str,
        exclude_paths: set[str],
    ) -> str:
        requested = category.strip().lower()
        tag_set = {tag.strip().lower() for tag in tags if tag}
        query_tokens = {token.strip().lower() for token in query_text.split() if token.strip()}
        candidates: list[tuple[float, str]] = []
        for entry in self.selector._load_catalog():
            if entry.path in exclude_paths:
                continue
            if not self.selector._is_runtime_eligible_entry(entry=entry):
                continue
            if entry.category.strip().lower() != requested:
                continue
            entry_tags = {tag.strip().lower() for tag in entry.tags}
            score = 0.0
            score += len(tag_set & entry_tags) * 1.4
            score += len(query_tokens & entry_tags) * 1.1
            score += entry.realism_score * 1.5
            score += entry.freshness_score * 1.2
            score += entry.strength * 0.8
            score += self.selector._segment_strength(entry=entry, segment_role="payoff")
            score += self.selector._deterministic_jitter(seed=seed, entry_path=entry.path)
            candidates.append((score, entry.path))
        if not candidates:
            return ""
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def align_first_frame(
        self,
        *,
        niche: str,
        topic: str,
        hook_text: str,
        asset_plan: AssetPlan,
    ) -> AssetPlan:
        if not self._hook_visual_alignment_enabled():
            return asset_plan
        hook_segment = asset_plan.segments.get("hook", AssetSegmentPlan())
        if asset_plan.segments:
            category = hook_segment.category or asset_plan.visual_anchor or self._legacy_anchor(hook_text=hook_text)
            path = self.selector.select(
                category=category,
                tags=list(hook_segment.tags or [niche, category, "high_impact"]),
                seed=f"{asset_plan.runtime_constraints.deterministic_seed or self._selection_key(niche, topic, ScriptPlan(hook=hook_text, setup='', payoff=''))}:hook-align",
                query_text=f"{topic} {hook_text}",
                minimum_score=8.0,
                segment_role="hook",
            )
            if not path:
                return asset_plan
            aligned_segments = dict(asset_plan.segments)
            aligned_segments["hook"] = AssetSegmentPlan(
                background=AssetBackgroundPlan(source="local", path=path),
                category=category,
                tags=list(hook_segment.tags),
                effects=list(hook_segment.effects),
                decision_contract=hook_segment.decision_contract,
                visual_query=hook_segment.visual_query,
            )
            return AssetPlan(
                hook_asset=path,
                setup_asset=asset_plan.setup_asset,
                payoff_asset=asset_plan.payoff_asset,
                visual_style=asset_plan.visual_style,
                motion_profile=asset_plan.motion_profile,
                visual_anchor=asset_plan.visual_anchor or category,
                semantic_pattern=asset_plan.semantic_pattern,
                entity=asset_plan.entity,
                case_visual_pack=dict(asset_plan.case_visual_pack),
                segments=aligned_segments,
                runtime_constraints=asset_plan.runtime_constraints,
            )
        hook_type = self._detect_hook_type(topic=topic, hook_text=hook_text)
        anchor_signal = self._detect_anchor_signal(hook_type=hook_type, hook_text=hook_text)
        path_obj = self._resolve_anchor_asset(hook_type=hook_type, anchor_signal=anchor_signal, niche=niche)
        path = str(path_obj) if path_obj is not None else ""
        if not path:
            return asset_plan
        aligned_segments = dict(asset_plan.segments)
        aligned_segments["hook"] = AssetSegmentPlan(
            background=AssetBackgroundPlan(source="local", path=path),
            category=hook_segment.category or asset_plan.visual_anchor or self._legacy_anchor(hook_text=hook_text),
            tags=list(hook_segment.tags),
            effects=list(hook_segment.effects),
            decision_contract=hook_segment.decision_contract,
            visual_query=hook_segment.visual_query,
        )
        return AssetPlan(
            hook_asset=path,
            setup_asset=asset_plan.setup_asset,
            payoff_asset=asset_plan.payoff_asset,
            visual_style=asset_plan.visual_style,
            motion_profile=asset_plan.motion_profile,
            visual_anchor=asset_plan.visual_anchor or hook_segment.category or self._legacy_anchor(hook_text=hook_text),
            semantic_pattern=asset_plan.semantic_pattern,
            entity=asset_plan.entity,
            case_visual_pack=dict(asset_plan.case_visual_pack),
            segments=aligned_segments,
            runtime_constraints=asset_plan.runtime_constraints,
        )

    def _selection_key(self, niche: str, topic: str, script_plan: ScriptPlan, strategy_profile: StrategyProfile) -> str:
        base_material = (
            f"{niche.strip().lower()}::{topic.strip().lower()}::"
            f"{script_plan.hook.strip().lower()}::{script_plan.setup.strip().lower()}::{script_plan.payoff.strip().lower()}"
        )
        strategy_suffix = ""
        if strategy_profile.content_mode != "standard" or strategy_profile.variation_policy != "low":
            strategy_suffix = (
                f"::{strategy_profile.content_mode.strip().lower()}::"
                f"{strategy_profile.target_duration_range.strip().lower()}::{strategy_profile.variation_policy.strip().lower()}"
            )
        material = f"{base_material}{strategy_suffix}".encode("utf-8")
        return sha256(material).hexdigest()[:16]

    def _fallback_script_plan(self, topic: str) -> ScriptPlan:
        title = topic.strip() or "anomalous scene"
        return ScriptPlan(
            hook=title,
            setup=title,
            payoff=title,
            generation_mode="asset_selection_fallback",
        )

    def _legacy_anchor(self, *, hook_text: str) -> str:
        text = hook_text.upper()
        if any(token in text for token in (" RECORD ", " TRANSCRIPT ", " ARCHIVE ", " LOG ", " FILE ")):
            return "document"
        if any(token in text for token in (" CAMERA ", " DISPLAY ", " INTERCOM ", " SIGNAL ", " RECORDER ")):
            return "device"
        if any(token in text for token in (" DOOR ", " LOCKER ", " SEALED ")):
            return "door"
        return "room"

    def _hook_visual_alignment_enabled(self) -> bool:
        return os.getenv("CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT", "1") != "0"

    def _hook_visual_alignment_mode(self) -> str:
        return os.getenv("CORTAI_EXPERIMENT_HOOK_VISUAL_ALIGNMENT_MODE", "refined_experiential").strip().lower() or "refined_experiential"

    def _detect_hook_type(self, *, topic: str, hook_text: str) -> str:
        text = self._normalize_text(f"{topic} {hook_text}")
        experiential_signals = (
            " CAMERA ", " BLACKOUT ", " GLITCH ", " ELEVATOR ", " DOOR ", " WARNING ", " SIGNAL ",
            " VOICE ", " INTERCOM ", " TUNNEL ", " MAP ", " BLUEPRINT ", " PLATFORM ", " TIMETABLE ",
            " CORRIDOR ", " ROOM ", " WING ", " LOCKER ",
        )
        inferential_signals = (
            " LOG ", " RECORD ", " FILE ", " ARCHIVE ", " TRANSCRIPT ", " STATEMENT ", " TAPE ",
            " EVIDENCE ", " DATE ", " TIMESTAMP ", " OVERRIDE ", " AUDIO ",
        )
        if any(token in text for token in experiential_signals):
            return "experiential"
        if any(token in text for token in inferential_signals):
            return "inferential"
        return "experiential"

    def _detect_anchor_signal(self, *, hook_type: str, hook_text: str) -> str:
        text = self._normalize_text(hook_text)
        if hook_type == "inferential":
            if any(token in text for token in (" TRANSCRIPT ", " AUDIO ")):
                return "text_audio_mismatch"
            if any(token in text for token in (" DATE ", " TIMESTAMP ", " FUTURE ")):
                return "timestamp_focus"
            if any(token in text for token in (" ARCHIVE ", " OVERRIDE ")):
                return "archive_override"
            if any(token in text for token in (" TAPE ", " EVIDENCE ")):
                return "evidence_media"
            if any(token in text for token in (" LOG ", " RECORD ", " FILE ", " STATEMENT ")):
                return "document_log"
            return ""
        if any(token in text for token in (" CAMERA ", " BLACKOUT ", " GLITCH ")):
            return "camera_glitch"
        if any(token in text for token in (" MAP ", " BLUEPRINT ", " TIMETABLE ", " CORRIDOR ")):
            return "map_corridor"
        if any(token in text for token in (" SEALED ", " LOCKED ", " LOCKER ", " ROOM ", " WING ")):
            return "sealed_access"
        if any(token in text for token in (" ELEVATOR ", " DOOR ")):
            return "object_anomaly"
        if any(token in text for token in (" WARNING ", " SIGNAL ")):
            return "warning_display"
        if any(token in text for token in (" VOICE ", " INTERCOM ", " RECORDER ", " SPEAKER ")):
            return "active_device"
        return ""

    def _resolve_anchor_asset(self, *, hook_type: str, anchor_signal: str, niche: str) -> Path | None:
        if hook_type == "inferential":
            return self._asset_path("conspiracy", "conspiracy_02.jpg")
        baseline = {
            "camera_glitch": self._asset_path("horror", "horror_03.jpg"),
            "object_anomaly": self._asset_path("horror", "horror_04.jpg"),
            "warning_display": self._asset_path("horror", "horror_04.jpg"),
            "active_device": self._asset_path("horror", "horror_03.jpg"),
        }
        refined = dict(baseline)
        if self._hook_visual_alignment_mode() == "refined_experiential":
            refined.update(
                {
                    "camera_glitch": self._asset_path("facts", "facts_02.jpg"),
                    "active_device": self._asset_path("facts", "facts_02.jpg"),
                    "map_corridor": self._asset_path("conspiracy", "conspiracy_02.jpg"),
                    "sealed_access": self._asset_path("horror", "horror_04.jpg"),
                }
            )
            if niche.strip().lower() in {"true_crime", "crime"}:
                refined["active_device"] = self._asset_path("conspiracy", "conspiracy_02.jpg")
        return refined.get(anchor_signal)

    def _asset_path(self, theme: str, filename: str) -> Path | None:
        path = self.background_service.local_assets_dir / theme / filename
        return path if path.exists() else None

    def _normalize_text(self, value: str) -> str:
        text = value.upper()
        text = re.sub(r"[^A-Z0-9\\s]", " ", text)
        text = re.sub(r"\\s+", " ", text).strip()
        return f" {text} "

    def _segment_query_text(
        self,
        *,
        segment_name: str,
        topic: str,
        script_plan: ScriptPlan,
        asset_plan: AssetPlan,
        strategy_profile: StrategyProfile,
        payoff_evidence: dict[str, object] | None = None,
    ) -> str:
        segment_text = {
            "hook": script_plan.hook,
            "setup": script_plan.setup,
            "payoff": script_plan.payoff,
        }.get(segment_name, "")
        strategy_tokens = ""
        if strategy_profile.content_mode != "standard" or strategy_profile.variation_policy != "low":
            strategy_tokens = f"{strategy_profile.variation_policy} {strategy_profile.content_mode}"
        evidence_tokens = ""
        if payoff_evidence and payoff_evidence.get("query_suffix"):
            evidence_tokens = str(payoff_evidence["query_suffix"])
        return " ".join(
            part
            for part in (
                asset_plan.segments.get(segment_name, AssetSegmentPlan()).visual_query.search_query_real,
                topic,
                segment_text,
                asset_plan.visual_anchor,
                asset_plan.semantic_pattern,
                asset_plan.entity,
                strategy_tokens,
                evidence_tokens,
            )
            if part
        )

    def _minimum_local_score(
        self,
        *,
        segment_name: str,
        strategy_profile: StrategyProfile,
        payoff_evidence: dict[str, object] | None = None,
    ) -> float:
        if segment_name == "hook":
            base = 8.0
        elif segment_name == "payoff":
            base = 7.0
        else:
            base = 5.5
        if strategy_profile.variation_policy == "medium":
            if segment_name == "setup":
                return base + 0.9
            if segment_name == "payoff":
                return base + 0.6
            return base + 0.3
        if strategy_profile.variation_policy == "none" or strategy_profile.content_mode == "conservative":
            if segment_name == "hook":
                return base + 0.2
            return base + 0.4
        if segment_name == "payoff" and payoff_evidence and payoff_evidence.get("category"):
            return base + 0.6
        return base

    def _selection_category(
        self,
        *,
        segment: AssetSegmentPlan,
        plan: AssetPlan,
        segment_name: str,
        strategy_profile: StrategyProfile,
        payoff_evidence: dict[str, object] | None = None,
    ) -> str:
        category = segment.category or plan.visual_anchor or "room"
        payoff_has_explicit_evidence = bool(segment_name == "payoff" and payoff_evidence and payoff_evidence.get("category"))
        if segment_name == "payoff" and payoff_evidence and payoff_evidence.get("category"):
            category = str(payoff_evidence["category"])
        if strategy_profile.variation_policy == "medium" and not payoff_has_explicit_evidence:
            category = self._variation_forward_category(
                segment_name=segment_name,
                category=category,
                plan=plan,
            )
        elif strategy_profile.variation_policy == "none" or strategy_profile.content_mode == "conservative":
            category = self._variation_safe_category(
                segment_name=segment_name,
                category=category,
                plan=plan,
            )
        if segment_name == "payoff":
            category = self._novelty_safe_payoff_category(
                category=category,
                strategy_profile=strategy_profile,
            )
        return category

    def _novelty_safe_payoff_category(
        self,
        *,
        category: str,
        strategy_profile: StrategyProfile,
    ) -> str:
        hints = getattr(strategy_profile, "novelty_hints", {}) or {}
        blocked = {str(item).strip() for item in hints.get("blocked_visual_payoff_categories", []) if str(item).strip()}
        if category not in blocked:
            return category
        preferred = [str(item).strip() for item in hints.get("preferred_alternative_payoff_families", []) if str(item).strip()]
        for candidate in preferred:
            if candidate and candidate not in blocked:
                return candidate
        fallback_map = {
            "map_blueprint": "warning_display",
            "warning_display": "sealed_access",
            "sealed_access": "document",
            "document": "warning_display",
        }
        reroute = fallback_map.get(category, category)
        if reroute not in blocked:
            return reroute
        return category

    def _selection_tags(
        self,
        *,
        segment: AssetSegmentPlan,
        segment_name: str,
        strategy_profile: StrategyProfile,
        payoff_evidence: dict[str, object] | None = None,
    ) -> list[str]:
        tags = list(segment.tags)
        if segment_name == "payoff" and payoff_evidence:
            tags.extend(str(tag) for tag in payoff_evidence.get("tags", []) if str(tag).strip())
        tags.append(f"strategy_variation_{strategy_profile.variation_policy}")
        tags.append(f"strategy_mode_{strategy_profile.content_mode}")
        if strategy_profile.variation_policy == "medium":
            tags.extend([f"strategy_role_{segment_name}", "anti_repetition_bias"])
            if segment_name == "hook":
                tags.append("high_impact")
            elif segment_name == "payoff":
                tags.append("reveal")
        elif strategy_profile.variation_policy == "none":
            tags.extend(["literal_evidence_bias", "safe_selection_bias"])
        return tags

    def _payoff_evidence_profile(
        self,
        *,
        segment_name: str,
        script_plan: ScriptPlan,
        ) -> dict[str, object]:
        if segment_name != "payoff":
            return {}
        text = self._normalize_text(script_plan.payoff)
        if any(
            token in text
            for token in (
                " EXIT SIGN ",
                " POINTING ",
                " POINTED ",
                " INTO THE WALL ",
                " MISSING ROUTE ",
                " ERASED ROUTE ",
                " ROUTE ",
                " WALL ",
            )
        ):
            return {
                "category": "warning_display",
                "tags": ["payoff_evidence_bias", "route_erasure_reveal", "directional_sign_proof"],
                "query_suffix": "exit sign warning panel directional sign route erased wall evidence",
            }
        if any(token in text for token in (" ROOM ", " FLOORPLAN ", " MAP ", " BLUEPRINT ", " NON EXISTENT ", " NONEXISTENT ")):
            return {
                "category": "map_blueprint",
                "tags": ["payoff_evidence_bias", "room_number_evidence", "floorplan_reveal"],
                "query_suffix": "room number floorplan removed map blueprint evidence",
            }
        if any(token in text for token in (" FILE ", " RECORD ", " REPORT ", " TRANSCRIPT ", " ARCHIVE ", " TAPE ", " PAGE ")):
            return {
                "category": "document",
                "tags": ["payoff_evidence_bias", "documentary_reveal", "archival_proof"],
                "query_suffix": "document file record archive transcript proof evidence",
            }
        if any(token in text for token in (" INTERCOM ", " VOICE ", " CALL ", " CALLER ", " RECORDER ", " WHISPER ")):
            return {
                "category": "intercom_recorder",
                "tags": ["payoff_evidence_bias", "audio_source_reveal", "recorded_voice_proof"],
                "query_suffix": "intercom recorder voice caller whisper audio evidence",
            }
        if any(token in text for token in (" DOOR ", " LOCK ", " HANDLE ", " BREATHING ", " INSIDE ")):
            return {
                "category": "sealed_access",
                "tags": ["payoff_evidence_bias", "sealed_access_reveal", "containment_proof"],
                "query_suffix": "sealed door lock handle access point evidence",
            }
        if any(token in text for token in (" WARNING ", " SCREEN ", " PANEL ", " DISPLAY ", " MONITOR ")):
            return {
                "category": "warning_display",
                "tags": ["payoff_evidence_bias", "display_reveal", "warning_panel_proof"],
                "query_suffix": "warning display monitor panel screen proof evidence",
            }
        return {}

    def _apply_strategy_plan_variation(
        self,
        *,
        plan: AssetPlan,
        strategy_profile: StrategyProfile,
        script_plan: ScriptPlan,
    ) -> AssetPlan:
        if not plan.segments:
            return plan
        updated_segments = dict(plan.segments)
        if strategy_profile.variation_policy == "medium":
            hook_segment = updated_segments.get("hook", AssetSegmentPlan())
            setup_segment = updated_segments.get("setup", AssetSegmentPlan())
            payoff_segment = updated_segments.get("payoff", AssetSegmentPlan())
            updated_segments["setup"] = AssetSegmentPlan(
                background=setup_segment.background,
                category=self._variation_forward_category(segment_name="setup", category=setup_segment.category or plan.visual_anchor or "room", plan=plan),
                tags=list(setup_segment.tags) + ["strategy_variation_medium", "editorial_progression", "segment_setup"],
                effects=list(setup_segment.effects),
                decision_contract=setup_segment.decision_contract,
                visual_query=setup_segment.visual_query,
            )
            updated_segments["payoff"] = AssetSegmentPlan(
                background=payoff_segment.background,
                category=self._variation_forward_category(segment_name="payoff", category=payoff_segment.category or plan.visual_anchor or "room", plan=plan),
                tags=list(payoff_segment.tags) + ["strategy_variation_medium", "editorial_reveal", "segment_payoff"],
                effects=list(payoff_segment.effects),
                decision_contract=payoff_segment.decision_contract,
                visual_query=payoff_segment.visual_query,
            )
            updated_segments["hook"] = AssetSegmentPlan(
                background=hook_segment.background,
                category=hook_segment.category,
                tags=list(hook_segment.tags) + ["strategy_variation_medium", "segment_hook"],
                effects=list(hook_segment.effects),
                decision_contract=hook_segment.decision_contract,
                visual_query=hook_segment.visual_query,
            )
        elif strategy_profile.variation_policy == "none" or strategy_profile.content_mode == "conservative":
            for segment_name in ("hook", "setup", "payoff"):
                segment = updated_segments.get(segment_name, AssetSegmentPlan())
                updated_segments[segment_name] = AssetSegmentPlan(
                    background=segment.background,
                    category=self._variation_safe_category(
                        segment_name=segment_name,
                        category=segment.category or plan.visual_anchor or "room",
                        plan=plan,
                    ),
                    tags=list(segment.tags) + ["strategy_safe_mode", f"strategy_variation_{strategy_profile.variation_policy}"],
                    effects=list(segment.effects),
                    decision_contract=segment.decision_contract,
                    visual_query=segment.visual_query,
                )
        return AssetPlan(
            hook_asset=plan.hook_asset,
            setup_asset=plan.setup_asset,
            payoff_asset=plan.payoff_asset,
            visual_style=plan.visual_style,
            motion_profile=plan.motion_profile,
            visual_anchor=plan.visual_anchor,
            semantic_pattern=plan.semantic_pattern,
            entity=plan.entity,
            case_visual_pack=dict(plan.case_visual_pack),
            segments=updated_segments,
            runtime_constraints=plan.runtime_constraints,
        )

    def _variation_forward_category(self, *, segment_name: str, category: str, plan: AssetPlan) -> str:
        if segment_name == "hook":
            return category
        if plan.visual_anchor == "device":
            if segment_name == "setup":
                return "institutional_space"
            return "intercom_recorder" if category != "intercom_recorder" else "warning_display"
        if plan.visual_anchor == "document":
            if segment_name == "setup":
                return "archive" if category != "archive" else "investigative_interior"
            return "document" if category != "document" else "evidence_surface"
        if plan.visual_anchor == "door":
            if segment_name == "setup":
                return "corridor" if category != "corridor" else "institutional_space"
            return "sealed_access"
        if plan.visual_anchor == "corridor":
            if segment_name == "setup":
                return "institutional_space"
            return "map_blueprint" if category != "map_blueprint" else "corridor"
        if segment_name == "setup":
            return "investigative_interior" if category != "investigative_interior" else category
        return "document" if category != "document" else category

    def _variation_safe_category(self, *, segment_name: str, category: str, plan: AssetPlan) -> str:
        if segment_name == "hook":
            return category or plan.visual_anchor or "room"
        if plan.visual_anchor == "device" and segment_name == "payoff":
            return "warning_display" if "warning" in (plan.semantic_pattern or "") else category
        if plan.visual_anchor == "document":
            return "document" if segment_name == "payoff" else "archive"
        if plan.visual_anchor == "door":
            return "sealed_access" if segment_name == "payoff" else "institutional_space"
        return category or plan.visual_anchor or "room"

    def _has_local_assets(self) -> bool:
        root = self.background_service.local_assets_dir
        return root.exists() and any(root.rglob("*.jpg"))

    def _fallback_result(self) -> AssetSelectionResult:
        return AssetSelectionResult(
            asset_selection=AssetPlan(
                hook_asset="",
                setup_asset="",
                payoff_asset="",
                visual_style="phase1_baseline",
                motion_profile="subtle_push_in",
            ),
            fallback=FallbackDecision(
                used=True,
                mode=FallbackMode.SAFE_DEFAULT.value,
                reason="ASSET_SELECTION_FALLBACK",
            ),
        )
