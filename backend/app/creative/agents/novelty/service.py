from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any

from app.creative.agents.novelty.models import NoveltyInput, NoveltyPressureProfile, NoveltyResult, PatternSignature


def _normalize_text(value: str) -> str:
    text = str(value or "").upper()
    text = re.sub(r"[^A-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return f" {text} "


@dataclass
class NoveltyEngineService:
    history_dir: Path = field(default_factory=lambda: Path("OUT/runtime/novelty_history"))
    recent_videos: int = 20
    focus_last_n: int = 5

    def generate(self, data: NoveltyInput) -> NoveltyResult:
        executions = list(data.recent_approved_executions) or self._load_recent_approved_executions(account_id=data.account_id)
        signatures = [self._signature_from_execution(item) for item in executions][-self.recent_videos :]
        profile = self._build_profile(signatures)
        return NoveltyResult(
            novelty_pressure_profile=profile,
            signatures_considered=signatures,
        )

    def register_approved_execution(self, *, account_id: str, execution_payload: dict[str, Any]) -> None:
        qc_status = str(execution_payload.get("video_qc", {}).get("status") or "").upper()
        if qc_status != "APPROVE":
            return
        record = {
            "creative_pack": execution_payload.get("creative_pack", {}),
            "video_qc": execution_payload.get("video_qc", {}),
        }
        path = self._history_path(account_id=account_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    def _load_recent_approved_executions(self, *, account_id: str) -> list[dict[str, Any]]:
        path = self._history_path(account_id=account_id)
        if not path.exists():
            return []
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        payloads: list[dict[str, Any]] = []
        for line in lines[-self.recent_videos :]:
            try:
                payloads.append(json.loads(line))
            except Exception:  # noqa: BLE001
                continue
        return payloads

    def _history_path(self, *, account_id: str) -> Path:
        return self.history_dir / f"{account_id}.jsonl"

    def _signature_from_execution(self, payload: dict[str, Any]) -> PatternSignature:
        creative_pack = dict(payload.get("creative_pack") or {})
        script_plan = dict(creative_pack.get("script_plan") or {})
        asset_plan = dict(creative_pack.get("asset_plan") or {})
        strategy_profile = dict(creative_pack.get("strategy_profile") or {})
        hook = str(script_plan.get("hook") or "")
        setup = str(script_plan.get("setup") or "")
        payoff = str(script_plan.get("payoff") or "")
        visual_payoff_family = str(asset_plan.get("segments", {}).get("payoff", {}).get("category") or "other")
        hook_family = self._hook_family(hook)
        payoff_structure = self._payoff_structure(payoff)
        semantic_closure_type = self._semantic_closure_type(payoff)
        motif_signature = f"{hook_family}>{payoff_structure}>{visual_payoff_family}"
        return PatternSignature(
            hook_family=hook_family,
            payoff_structure=payoff_structure,
            semantic_closure_type=semantic_closure_type,
            visual_payoff_family=visual_payoff_family,
            motif_signature=motif_signature,
            strategy_variation_policy=str(strategy_profile.get("variation_policy") or "low"),
            content_mode=str(strategy_profile.get("content_mode") or "standard"),
        )

    def _build_profile(self, signatures: list[PatternSignature]) -> NoveltyPressureProfile:
        recent = signatures[-self.focus_last_n :]
        long_window = signatures[-self.recent_videos :]
        semantic_counter = Counter(item.semantic_closure_type for item in recent if item.semantic_closure_type != "other")
        visual_counter = Counter(item.visual_payoff_family for item in recent if item.visual_payoff_family != "other")
        structural_counter = Counter(item.payoff_structure for item in recent if item.payoff_structure != "other")
        long_structural_counter = Counter(item.payoff_structure for item in long_window if item.payoff_structure != "other")
        variation_counter = Counter(item.strategy_variation_policy for item in recent if item.strategy_variation_policy)

        semantic_level, semantic_pattern = self._level_from_counter(semantic_counter, medium_at=3, high_at=4, critical_at=5)
        visual_level, visual_pattern = self._level_from_counter(visual_counter, medium_at=3, high_at=4, critical_at=5)
        structural_level, structural_pattern = self._structural_level(structural_counter, long_structural_counter)
        dominant: list[str] = []
        if semantic_pattern:
            dominant.append(f"semantic_closure_type:{semantic_pattern}")
        if visual_pattern:
            dominant.append(f"visual_payoff_family:{visual_pattern}")
        if structural_pattern:
            dominant.append(f"payoff_structure:{structural_pattern}")

        level_order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
        highest_level = max(semantic_level, visual_level, structural_level, key=lambda item: level_order[item])
        pressure_level = highest_level if highest_level != "none" else "low"
        novelty_budget = "low" if highest_level in {"none", "low"} else "medium" if highest_level == "medium" else "high"
        recommended_variation_policy = "medium" if highest_level in {"medium", "high", "critical"} else "low"
        if variation_counter and len(recent) >= 3 and variation_counter.get("low", 0) == len(recent):
            if recommended_variation_policy == "low":
                recommended_variation_policy = "medium"
                pressure_level = "medium"
                novelty_budget = "medium"

        blocked_payoff_structures: list[str] = []
        blocked_visual_categories: list[str] = []
        if structural_level in {"high", "critical"} and structural_pattern:
            blocked_payoff_structures.append(structural_pattern)
        if visual_level in {"high", "critical"} and visual_pattern:
            blocked_visual_categories.append(visual_pattern)
        preferred = self._preferred_alternatives(blocked_visual_categories)

        return NoveltyPressureProfile(
            semantic_saturation_level=semantic_level,
            visual_saturation_level=visual_level,
            structural_saturation_level=structural_level,
            dominant_repeated_patterns=dominant,
            novelty_budget=novelty_budget,
            pressure_level=pressure_level,
            recommended_variation_policy=recommended_variation_policy,
            blocked_payoff_structures=blocked_payoff_structures,
            blocked_visual_payoff_categories=blocked_visual_categories,
            preferred_alternative_payoff_families=preferred,
            trace={
                "memory_window": {
                    "recent_videos": self.recent_videos,
                    "focus_last_n": self.focus_last_n,
                    "weight_decay": "linear",
                },
                "recent_signature_count": len(recent),
                "semantic_counter": dict(semantic_counter),
                "visual_counter": dict(visual_counter),
                "structural_counter_recent": dict(structural_counter),
                "structural_counter_long": dict(long_structural_counter),
                "variation_counter": dict(variation_counter),
            },
        )

    def _level_from_counter(
        self,
        counter: Counter[str],
        *,
        medium_at: int,
        high_at: int,
        critical_at: int,
    ) -> tuple[str, str]:
        if not counter:
            return "none", ""
        pattern, count = counter.most_common(1)[0]
        if count >= critical_at:
            return "critical", pattern
        if count >= high_at:
            return "high", pattern
        if count >= medium_at:
            return "medium", pattern
        if count >= 2:
            return "low", pattern
        return "none", pattern

    def _structural_level(
        self,
        recent_counter: Counter[str],
        long_counter: Counter[str],
    ) -> tuple[str, str]:
        if not recent_counter:
            return "none", ""
        pattern, recent_count = recent_counter.most_common(1)[0]
        long_count = long_counter.get(pattern, 0)
        if recent_count >= 5:
            return "critical", pattern
        if recent_count >= 4 or (recent_count >= 2 and long_count >= 4):
            return "high", pattern
        if recent_count >= 3:
            return "medium", pattern
        if recent_count >= 2:
            return "low", pattern
        return "none", pattern

    def _preferred_alternatives(self, blocked_visual_categories: list[str]) -> list[str]:
        if not blocked_visual_categories:
            return []
        mapping = {
            "map_blueprint": ["warning_display", "sealed_access", "intercom_recorder"],
            "warning_display": ["sealed_access", "document", "intercom_recorder"],
            "sealed_access": ["map_blueprint", "warning_display", "document"],
            "document": ["warning_display", "sealed_access", "intercom_recorder"],
        }
        preferred: list[str] = []
        for blocked in blocked_visual_categories:
            preferred.extend(mapping.get(blocked, []))
        deduped: list[str] = []
        for item in preferred:
            if item in blocked_visual_categories or item in deduped:
                continue
            deduped.append(item)
        return deduped

    def _hook_family(self, hook: str) -> str:
        upper = _normalize_text(hook)
        if " A WITNESS " in upper:
            return "witness_report"
        if " RECOVERED TAPE " in upper or " ARCHIVE TAPE " in upper:
            return "recovered_recording"
        if " LOCALS STILL TALK " in upper or " LOCALS KEPT REPEATING " in upper:
            return "urban_legend_fragment"
        if " CASE NOTES " in upper or " OFFICIAL MEMO " in upper:
            return "official_warning"
        return "other"

    def _payoff_structure(self, payoff: str) -> str:
        upper = _normalize_text(payoff)
        if any(item in upper for item in (" REMOVED FROM THE FLOORPLAN ", " MISSING FROM THE MAP ", " ROOM 312 ", " DOOR 16 ")):
            return "named_location_removed"
        if any(item in upper for item in (" EXIT SIGN ", " WARNING ", " PANEL ", " POINTS TO ")):
            return "device_points_to_impossible_place"
        if any(item in upper for item in (" FILE ", " TRANSCRIPT ", " REPORT ", " ARCHIVE ", " RECORD ")):
            return "documentary_proof_reveal"
        if any(item in upper for item in (" INTERCOM ", " VOICE ", " RECORDER ", " CALLER ")):
            return "record_names_impossible_identity"
        if any(item in upper for item in (" SEALED ", " DOOR ", " LOCK ", " GATE ")):
            return "sealed_access_physical_reveal"
        return "other"

    def _semantic_closure_type(self, payoff: str) -> str:
        upper = _normalize_text(payoff)
        if any(item in upper for item in (" REMOVED FROM THE FLOORPLAN ", " MISSING FROM THE MAP ")):
            return "removed_from_system"
        if any(item in upper for item in (" EXIT SIGN ", " POINTS TO ", " POINTING INTO THE WALL ", " WARNING ")):
            return "warning_panel_contradiction"
        if any(item in upper for item in (" FILE ", " ARCHIVE ", " TRANSCRIPT ", " REPORT ", " RECORD ")):
            return "archival_discrepancy"
        if any(item in upper for item in (" INTERCOM ", " VOICE ", " RECORDER ", " CALLER ")):
            return "identity_reveal"
        if any(item in upper for item in (" SEALED ", " DOOR ", " LOCK ", " GATE ")):
            return "sealed_access_reveal"
        return "other"
