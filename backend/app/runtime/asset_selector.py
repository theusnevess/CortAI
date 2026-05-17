from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import ClassVar


@dataclass(frozen=True)
class CatalogEntry:
    path: str
    category: str
    subtype: str
    family: str
    framing: str
    tags: list[str]
    mood: str
    semantic_pattern_fit: list[str]
    entity_fit: list[str]
    hook_strength_score: float
    payoff_strength_score: float
    setup_specificity_score: float
    realism_score: float
    source_type: str
    usage_count: int
    freshness_score: float
    resolution: list[int]
    strength: float = 1.0
    genericity: float = 0.0
    phase1_legacy: bool = False
    eligible_for_runtime: bool = False


@dataclass
class AssetSelector:
    catalog_path: Path = Path("backend/app/assets/catalog.json")
    _selection_contexts: dict[str, dict[str, CatalogEntry]] = field(default_factory=dict, init=False, repr=False)
    _batch_family_usage: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _batch_family_usage_by_role: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    _global_video_signatures: ClassVar[dict[str, list[dict[str, str]]]] = {}
    _global_failed_sequences_prevented: ClassVar[dict[str, int]] = {}
    ALLOWED_RUNTIME_SOURCES = {"pexels", "unsplash", "pixabay", "comfyui"}
    RETIRED_PHASE1_PATHS = {
        "assets/curated/archive/archive_shelves_01.jpg",
        "assets/curated/archive/archive_shelves_02.jpg",
        "assets/curated/archive/archive_storage_real_01.jpg",
        "assets/curated/archive/archive_storage_real_02.jpg",
        "assets/curated/door/door_sealed_entry_01.jpg",
        "assets/curated/horror_interior/horror_interior_hospital_wing_04.jpg",
        "assets/curated/horror_interior/horror_interior_threshold_03.jpg",
        "assets/curated/institutional_space/institutional_space_station_notice_04.jpg",
        "assets/curated/intercom_recorder/intercom_recorder_real_01.jpg",
        "assets/curated/intercom_recorder/intercom_recorder_real_02.jpg",
        "assets/curated/investigative_interior/investigative_interior_01.jpg",
        "assets/curated/investigative_interior/investigative_interior_03.jpg",
        "assets/curated/room/room_archive_interior_01.jpg",
        "assets/curated/room/room_investigative_interior_02.jpg",
        "assets/curated/warning_display/warning_display_real_01.jpg",
    }

    def _load_catalog(self) -> list[CatalogEntry]:
        payload = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        return [
            self._catalog_entry_from_dict(item=item)
            for item in payload
        ]

    def _catalog_entry_from_dict(self, *, item: dict[str, object]) -> CatalogEntry:
        source_type = str(item.get("source_type", "local_curated")).strip().lower()
        path = str(item["path"])
        phase1_legacy = bool(item.get("phase1_legacy", False))
        eligible_for_runtime = bool(
            item.get(
                "eligible_for_runtime",
                source_type in self.ALLOWED_RUNTIME_SOURCES and not phase1_legacy and source_type != "local_curated",
            )
        )
        return CatalogEntry(
            path=path,
            category=str(item["category"]),
            subtype=str(item.get("subtype", "")),
            family=str(item.get("family", item.get("category", ""))),
            framing=str(item.get("framing", "medium")),
            tags=list(item.get("tags", [])),
            mood=str(item.get("mood", "")),
            semantic_pattern_fit=list(item.get("semantic_pattern_fit", [])),
            entity_fit=list(item.get("entity_fit", [])),
            hook_strength_score=float(item.get("hook_strength_score", 0.5)),
            payoff_strength_score=float(item.get("payoff_strength_score", 0.5)),
            setup_specificity_score=float(item.get("setup_specificity_score", 0.5)),
            realism_score=float(item.get("realism_score", 0.5)),
            source_type=source_type,
            usage_count=int(item.get("usage_count", 0)),
            freshness_score=float(item.get("freshness_score", 0.5)),
            resolution=list(item.get("resolution", [1080, 1920])),
            strength=float(item.get("strength", 1.0)),
            genericity=float(item.get("genericity", 0.0)),
            phase1_legacy=phase1_legacy,
            eligible_for_runtime=eligible_for_runtime,
        )

    def _sequence_context_key(self, *, seed: str, segment_role: str) -> str:
        suffix = f":{segment_role}"
        if seed.endswith(suffix):
            return seed[: -len(suffix)]
        return seed

    def _sequence_context(self, *, seed: str, segment_role: str) -> dict[str, CatalogEntry]:
        key = self._sequence_context_key(seed=seed, segment_role=segment_role)
        return self._selection_contexts.setdefault(key, {})

    def _signature_batch_key(self, *, requested_case_pack: dict[str, set[str]]) -> str:
        return self._case_pack_batch_key(requested_case_pack=requested_case_pack, prefix="solution")

    def requested_case_pack(self, *, tags: list[str], query_text: str) -> dict[str, set[str]]:
        tag_set = {tag.strip().lower() for tag in tags if tag}
        query_tokens = self._query_tokens(query_text)
        return self._requested_case_pack(requested_tags=tag_set, query_tokens=query_tokens)

    def _remember_sequence_choice(
        self,
        *,
        seed: str,
        segment_role: str,
        entry: CatalogEntry,
    ) -> None:
        context = self._sequence_context(seed=seed, segment_role=segment_role)
        context[segment_role] = entry

    def _clear_sequence_context(self, *, seed: str, segment_role: str) -> None:
        key = self._sequence_context_key(seed=seed, segment_role=segment_role)
        self._selection_contexts.pop(key, None)

    def _solution_signature(
        self,
        *,
        hook_candidate: CatalogEntry,
        setup_candidate: CatalogEntry,
        payoff_candidate: CatalogEntry,
    ) -> dict[str, str]:
        hook_family = self._family_key(entry=hook_candidate)
        setup_family = self._family_key(entry=setup_candidate)
        payoff_family = self._family_key(entry=payoff_candidate)
        progression_type = (
            f"{self._sequence_bucket(entry=hook_candidate)}>"
            f"{self._sequence_bucket(entry=setup_candidate)}>"
            f"{self._sequence_bucket(entry=payoff_candidate)}"
        )
        hook_state = sorted(self._sequence_escalation_state(entry=hook_candidate))
        setup_state = sorted(self._sequence_escalation_state(entry=setup_candidate))
        payoff_state = sorted(self._sequence_escalation_state(entry=payoff_candidate))
        evidence_pattern = (
            f"h:{','.join(hook_state) or 'none'}|"
            f"s:{','.join(setup_state) or 'none'}|"
            f"p:{','.join(payoff_state) or 'none'}"
        )
        dominant_counter = Counter([hook_family, setup_family, payoff_family]).most_common(1)[0]
        dominant_family = dominant_counter[0] if dominant_counter[1] >= 2 else "mixed"
        return {
            "hook_family": hook_family,
            "setup_family": setup_family,
            "payoff_family": payoff_family,
            "progression_type": progression_type,
            "evidence_pattern": evidence_pattern,
            "dominant_family": dominant_family,
        }

    def _signature_similarity(self, *, first: dict[str, str], second: dict[str, str]) -> float:
        checks = [
            first.get("hook_family", "") == second.get("hook_family", ""),
            first.get("setup_family", "") == second.get("setup_family", ""),
            first.get("payoff_family", "") == second.get("payoff_family", ""),
            first.get("progression_type", "") == second.get("progression_type", ""),
            first.get("evidence_pattern", "") == second.get("evidence_pattern", ""),
        ]
        return sum(1.0 for matched in checks if matched) / float(len(checks))

    def _would_repeat_solution_signature(
        self,
        *,
        signature: dict[str, str],
        batch_key: str,
    ) -> bool:
        prior = self._global_video_signatures.get(batch_key, [])
        if not prior:
            return False
        for item in prior:
            if self._signature_similarity(first=signature, second=item) > 0.8:
                return True
        return False

    def _signature_policy_violation(
        self,
        *,
        signature: dict[str, str],
        batch_key: str,
    ) -> str | None:
        prior = self._global_video_signatures.get(batch_key, [])
        if not prior:
            return None
        if self._would_repeat_solution_signature(signature=signature, batch_key=batch_key):
            return "ASSET_RUNTIME_REPEATED_SIGNATURE"
        progression = signature.get("progression_type", "")
        progression_count = sum(1 for item in prior if item.get("progression_type", "") == progression)
        if progression_count >= 1:
            if self._allow_progression_repeat_under_evidence_difference(signature=signature, batch_key=batch_key):
                return None
            return "ASSET_RUNTIME_REPEATED_PROGRESSION_PATTERN"
        dominant_family = signature.get("dominant_family", "")
        if dominant_family == "mixed":
            return None
        dominant_count = sum(1 for item in prior if item.get("dominant_family", "") == dominant_family)
        if dominant_count >= 1:
            if self._allow_family_repeat_under_diversity(signature=signature, batch_key=batch_key):
                return None
            return "ASSET_RUNTIME_FAMILY_MONOCULTURE_FAILURE"
        return None

    def _allow_family_repeat_under_diversity(
        self,
        *,
        signature: dict[str, str],
        batch_key: str,
    ) -> bool:
        prior = self._global_video_signatures.get(batch_key, [])
        if not prior:
            return False
        if not self._batch_diversity_already_proven(batch_key=batch_key):
            return False
        if self._is_phase1_like_signature(signature=signature):
            return False
        if not self._has_strong_signature_evidence_progression(signature=signature):
            return False
        return self._family_repeat_offers_novelty(signature=signature, batch_key=batch_key)

    def _allow_progression_repeat_under_evidence_difference(
        self,
        *,
        signature: dict[str, str],
        batch_key: str,
    ) -> bool:
        prior = self._global_video_signatures.get(batch_key, [])
        progression = signature.get("progression_type", "")
        if not prior or not progression:
            return False
        if self._is_phase1_like_signature(signature=signature):
            return False
        if not self._has_strong_signature_evidence_progression(signature=signature):
            return False
        matching_progression = [
            item
            for item in prior
            if item.get("progression_type", "") == progression
        ]
        if not matching_progression:
            return False
        evidence_pattern = signature.get("evidence_pattern", "")
        if any(item.get("evidence_pattern", "") == evidence_pattern for item in matching_progression):
            return False
        return True

    def _batch_diversity_already_proven(self, *, batch_key: str) -> bool:
        prior = self._global_video_signatures.get(batch_key, [])
        total = len(prior)
        if total < 8:
            return False
        repeated = 0
        for index, signature in enumerate(prior):
            if any(
                self._signature_similarity(first=signature, second=item) > 0.8
                for item in prior[:index]
            ):
                repeated += 1
        repeated_rate = (repeated / total) if total else 0.0
        uniqueness_rate = 1.0 - repeated_rate if total else 0.0
        return uniqueness_rate >= 0.6 and repeated_rate <= 0.35

    def _parse_evidence_pattern(self, *, evidence_pattern: str) -> dict[str, set[str]]:
        sections: dict[str, set[str]] = {}
        for item in evidence_pattern.split("|"):
            if ":" not in item:
                continue
            role, payload = item.split(":", 1)
            states = {part.strip() for part in payload.split(",") if part.strip() and part.strip() != "none"}
            sections[role.strip()] = states
        return sections

    def _has_strong_signature_evidence_progression(self, *, signature: dict[str, str]) -> bool:
        sections = self._parse_evidence_pattern(evidence_pattern=signature.get("evidence_pattern", ""))
        hook_states = sections.get("h", set())
        setup_states = sections.get("s", set())
        payoff_states = sections.get("p", set())
        if not payoff_states:
            return False
        if not setup_states:
            return False
        setup_adds = setup_states - hook_states
        payoff_adds = payoff_states - (hook_states | setup_states)
        return bool(setup_adds) and bool(payoff_adds)

    def _is_phase1_like_signature(self, *, signature: dict[str, str]) -> bool:
        hook_family = signature.get("hook_family", "")
        setup_family = signature.get("setup_family", "")
        payoff_family = signature.get("payoff_family", "")
        progression = signature.get("progression_type", "")
        if progression in {
            "document_evidence>passage_context>document_evidence",
            "document_evidence>archive_context>document_evidence",
            "device_signal>passage_context>device_signal",
            "device_signal>barrier_signal>device_signal",
            "room_context>passage_context>room_context",
        }:
            return True
        if hook_family == payoff_family and setup_family in {
            "archive_context",
            "archive_family",
            "investigative_ambient",
            "institutional_passage",
            "corridor",
            "barrier_signal",
        }:
            return True
        return False

    def _family_repeat_offers_novelty(
        self,
        *,
        signature: dict[str, str],
        batch_key: str,
    ) -> bool:
        dominant_family = signature.get("dominant_family", "")
        if not dominant_family or dominant_family == "mixed":
            return False
        prior_same_family = [
            item
            for item in self._global_video_signatures.get(batch_key, [])
            if item.get("dominant_family", "") == dominant_family
        ]
        if not prior_same_family:
            return True
        progression = signature.get("progression_type", "")
        evidence_pattern = signature.get("evidence_pattern", "")
        if all(item.get("progression_type", "") != progression for item in prior_same_family):
            return True
        if all(item.get("evidence_pattern", "") != evidence_pattern for item in prior_same_family):
            return True
        return False

    def validate_and_register_video_signature(
        self,
        *,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry | None,
        payoff_candidate: CatalogEntry | None,
        requested_case_pack: dict[str, set[str]],
    ) -> tuple[bool, str]:
        if hook_candidate is None or setup_candidate is None or payoff_candidate is None:
            return False, "ASSET_RUNTIME_NO_VALID_NON_PROXY_SEQUENCE"
        signature = self._solution_signature(
            hook_candidate=hook_candidate,
            setup_candidate=setup_candidate,
            payoff_candidate=payoff_candidate,
        )
        batch_key = self._signature_batch_key(requested_case_pack=requested_case_pack)
        violation = self._signature_policy_violation(signature=signature, batch_key=batch_key)
        if violation is not None:
            self._global_failed_sequences_prevented[batch_key] = self._global_failed_sequences_prevented.get(batch_key, 0) + 1
            return False, violation
        self._global_video_signatures.setdefault(batch_key, []).append(signature)
        return True, ""

    def failed_sequences_prevented(self, *, requested_case_pack: dict[str, set[str]]) -> int:
        batch_key = self._signature_batch_key(requested_case_pack=requested_case_pack)
        return self._global_failed_sequences_prevented.get(batch_key, 0)

    def signature_metrics(self, *, requested_case_pack: dict[str, set[str]]) -> dict[str, float | int | bool]:
        batch_key = self._signature_batch_key(requested_case_pack=requested_case_pack)
        signatures = self._global_video_signatures.get(batch_key, [])
        total = len(signatures)
        repeated = 0
        for index, signature in enumerate(signatures):
            if any(
                self._signature_similarity(first=signature, second=prior) > 0.8
                for prior in signatures[:index]
            ):
                repeated += 1
        repeated_rate = (repeated / total) if total else 0.0
        uniqueness_rate = 1.0 - repeated_rate if total else 1.0
        dominant_share = 0.0
        if total:
            family_counts = Counter(
                item.get("dominant_family", "")
                for item in signatures
                if item.get("dominant_family", "") and item.get("dominant_family", "") != "mixed"
            )
            if family_counts:
                dominant_share = max(family_counts.values()) / total
        return {
            "batch_diversity_valid": repeated_rate <= 0.2,
            "signature_count": total,
            "solution_uniqueness_rate": round(uniqueness_rate, 4),
            "repeated_signature_rate": round(repeated_rate, 4),
            "dominant_family_share": round(dominant_share, 4),
            "failed_sequences_prevented": self._global_failed_sequences_prevented.get(batch_key, 0),
        }

    def _source_is_allowed_for_runtime(self, *, source_type: str) -> bool:
        return source_type.strip().lower() in self.ALLOWED_RUNTIME_SOURCES

    def _is_runtime_eligible_entry(self, *, entry: CatalogEntry) -> bool:
        if not entry.eligible_for_runtime:
            return False
        if not self._source_is_allowed_for_runtime(source_type=entry.source_type):
            return False
        if entry.source_type == "local_curated":
            return False
        if entry.phase1_legacy:
            return False
        if self._is_retired_phase1_entry(entry=entry):
            return False
        if self._legacy_visual_family(entry=entry) is not None:
            return False
        return True

    def lookup_catalog_entry(self, *, path: str) -> CatalogEntry | None:
        normalized = path.replace("\\", "/").strip().lower()
        for entry in self._load_catalog():
            if entry.path.replace("\\", "/").strip().lower() == normalized:
                return entry
        return None

    def is_runtime_eligible_path(self, *, path: str) -> bool:
        entry = self.lookup_catalog_entry(path=path)
        if entry is None:
            return False
        return self._is_runtime_eligible_entry(entry=entry)

    def select(
        self,
        *,
        category: str,
        tags: list[str],
        seed: str,
        exclude_paths: set[str] | None = None,
        query_text: str = "",
        minimum_score: float = 0.0,
        segment_role: str = "setup",
    ) -> str | None:
        exclude = exclude_paths or set()
        catalog = self._load_catalog()
        family_usage = self._family_usage_totals(catalog=catalog)
        scored: list[tuple[float, str]] = []
        tag_set = {tag.strip().lower() for tag in tags if tag}
        query_tokens = self._query_tokens(query_text)
        requested_case_pack = self._requested_case_pack(
            requested_tags=tag_set,
            query_tokens=query_tokens,
        )
        batch_key = self._batch_key_from_case_pack(requested_case_pack=requested_case_pack)
        sequence_context = self._sequence_context(seed=seed, segment_role=segment_role)
        hook_candidate = sequence_context.get("hook")
        setup_context_candidate = sequence_context.get("setup")
        has_strong_new_real_candidate = self._has_strong_new_real_candidate(
            catalog=catalog,
            requested_category=category,
            tag_set=tag_set,
            query_tokens=query_tokens,
            segment_role=segment_role,
        )
        for entry in catalog:
            if entry.path in exclude:
                continue
            if not self._is_runtime_eligible_entry(entry=entry):
                continue
            if self._should_hard_reject_case_proxy(
                entry=entry,
                requested_case_pack=requested_case_pack,
                segment_role=segment_role,
            ):
                continue
            if self._should_hard_reject_family_cap(
                entry=entry,
                catalog=catalog,
                batch_key=batch_key,
                segment_role=segment_role,
                requested_case_pack=requested_case_pack,
                requested_category=category,
                requested_tags=tag_set,
                query_tokens=query_tokens,
            ):
                continue
            case_specificity_score = self._case_specificity_score(
                entry=entry,
                requested_case_pack=requested_case_pack,
            )
            new_evidence_value = self._new_evidence_value(
                entry=entry,
                hook_candidate=hook_candidate,
                setup_candidate=setup_context_candidate,
                segment_role=segment_role,
            )
            anti_proxy_score = self._anti_proxy_score(
                entry=entry,
                requested_case_pack=requested_case_pack,
            )
            batch_family_novelty = self._batch_family_novelty_score(
                entry=entry,
                batch_key=batch_key,
            )
            if self._should_hard_reject_case_evidence_strict(
                entry=entry,
                catalog=catalog,
                requested_case_pack=requested_case_pack,
                requested_category=category,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
                case_specificity_score=case_specificity_score,
                new_evidence_value=new_evidence_value,
                batch_family_novelty=batch_family_novelty,
            ):
                continue
            retired_phase1 = self._is_retired_phase1_entry(entry=entry)
            category_score = self._category_score(category=category, entry_category=entry.category)
            score = category_score
            entry_tags = {tag.strip().lower() for tag in entry.tags}
            tag_overlap = len(tag_set & entry_tags)
            query_tag_overlap = len(query_tokens & entry_tags)
            subtype_overlap = self._subtype_overlap(entry=entry, query_tokens=query_tokens | tag_set)
            semantic_overlap = self._semantic_overlap(entry=entry, query_tokens=query_tokens)
            event_evidence_score = self._event_evidence_score(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            visual_world_score = self._visual_world_score(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            atmosphere_score = self._atmosphere_emotion_score(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            setup_event_alignment_score = self._setup_event_alignment_score(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            documentary_case_linkage_score = self._documentary_case_linkage_score(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            style_coherence_score = self._style_coherence_score(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            legacy_family = self._legacy_visual_family(entry=entry)
            if self._should_hard_reject_context_only(
                entry=entry,
                requested_category=category,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
                event_evidence_score=event_evidence_score,
                setup_event_alignment_score=setup_event_alignment_score,
                documentary_case_linkage_score=documentary_case_linkage_score,
            ):
                continue
            if self._should_hard_reject_world_drift(
                entry=entry,
                requested_tags=tag_set,
                segment_role=segment_role,
                event_evidence_score=event_evidence_score,
            ):
                continue
            if (
                segment_role == "setup"
                and self._should_hard_reject_setup_progression(
                    hook_candidate=hook_candidate,
                    setup_candidate=entry,
                    requested_tags=tag_set,
                    query_tokens=query_tokens,
                    event_evidence_score=event_evidence_score,
                    documentary_case_linkage_score=documentary_case_linkage_score,
                )
            ):
                continue
            if self.motif_loop_rejection(
                hook_candidate=hook_candidate,
                setup_candidate=entry if segment_role == "setup" else setup_context_candidate,
                payoff_candidate=entry if segment_role == "payoff" else None,
                segment_role=segment_role,
            ):
                continue
            if (
                segment_role == "payoff"
                and self._should_hard_reject_sequence_candidate(
                    hook_candidate=hook_candidate,
                    setup_candidate=setup_context_candidate,
                    payoff_candidate=entry,
                )
            ):
                continue
            score += tag_overlap * 1.25
            score += query_tag_overlap * 1.6
            score += self._segment_strength(entry=entry, segment_role=segment_role)
            score += entry.realism_score * 1.5
            score += entry.freshness_score * 1.25
            score += entry.strength * 0.8
            score += self._fit_bonus(entry=entry, query_tokens=query_tokens)
            score += self._framing_bonus(entry=entry, segment_role=segment_role)
            score += self._subtype_bonus(entry=entry, subtype_overlap=subtype_overlap, segment_role=segment_role)
            score += event_evidence_score
            score += visual_world_score
            score += atmosphere_score
            score += setup_event_alignment_score
            score += documentary_case_linkage_score
            score += style_coherence_score
            score += case_specificity_score * 2.6
            score += new_evidence_value * 2.2
            score += batch_family_novelty * 1.5
            score += anti_proxy_score * 1.3
            score += self._new_real_source_bonus(
                entry=entry,
                category_score=category_score,
                tag_overlap=tag_overlap,
                query_tag_overlap=query_tag_overlap,
                semantic_overlap=semantic_overlap,
                subtype_overlap=subtype_overlap,
                segment_role=segment_role,
            )
            score += self._segment_role_bonus(
                requested_category=category,
                entry=entry,
                segment_role=segment_role,
                requested_tags=tag_set,
                query_tokens=query_tokens,
            )
            score += self.evidence_progression_score(
                hook_candidate=hook_candidate,
                setup_candidate=entry if segment_role == "setup" else setup_context_candidate,
                payoff_candidate=entry if segment_role == "payoff" else None,
                segment_role=segment_role,
            )
            score -= self._motif_reuse_penalty(
                hook_candidate=hook_candidate,
                setup_candidate=entry if segment_role == "setup" else setup_context_candidate,
                payoff_candidate=entry if segment_role == "payoff" else None,
                segment_role=segment_role,
            )
            if self._batch_family_count(entry=entry, batch_key=batch_key) >= 2:
                score -= 1.6
            score *= self._event_dominance_multiplier(
                entry=entry,
                requested_category=category,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
                event_evidence_score=event_evidence_score,
                documentary_case_linkage_score=documentary_case_linkage_score,
            )
            score -= entry.genericity * 1.4
            score -= self._usage_penalty(entry=entry)
            score -= self._family_usage_penalty(
                entry=entry,
                catalog=catalog,
                family_usage=family_usage,
                requested_category=category,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            score -= self._setup_generic_penalty(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            score -= self._visual_world_break_penalty(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            score -= self._style_break_penalty(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            score -= self._payoff_under_delivery_penalty(
                entry=entry,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
                event_evidence_score=event_evidence_score,
            )
            score -= self._legacy_dominance_penalty(
                entry=entry,
                category_score=category_score,
                tag_overlap=tag_overlap,
                query_tag_overlap=query_tag_overlap,
                subtype_overlap=subtype_overlap,
                has_strong_new_real_candidate=has_strong_new_real_candidate,
            )
            score -= self._legacy_pool_lock_in_penalty(
                entry=entry,
                catalog=catalog,
                requested_category=category,
                segment_role=segment_role,
                has_strong_new_real_candidate=has_strong_new_real_candidate,
            )
            score -= self._legacy_family_penalty(
                entry=entry,
                catalog=catalog,
                requested_category=category,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
                event_evidence_score=event_evidence_score,
                setup_event_alignment_score=setup_event_alignment_score,
            )
            score -= self._documentary_transition_penalty(
                entry=entry,
                catalog=catalog,
                requested_category=category,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                segment_role=segment_role,
                documentary_case_linkage_score=documentary_case_linkage_score,
            )
            if retired_phase1:
                if segment_role == "setup":
                    continue
                if self._has_non_retired_alternative(
                    catalog=catalog,
                    entry=entry,
                    requested_category=category,
                    requested_tags=tag_set,
                    query_tokens=query_tokens,
                    segment_role=segment_role,
                ):
                    continue
            if (
                segment_role == "setup"
                and legacy_family is not None
                and not self._setup_has_quality_floor(
                    entry=entry,
                    requested_tags=tag_set,
                    query_tokens=query_tokens,
                    event_evidence_score=event_evidence_score,
                    setup_event_alignment_score=setup_event_alignment_score,
                )
            ):
                continue
            if (
                segment_role == "setup"
                and self._is_documentary_transition_request(
                    requested_category=category,
                    requested_tags=tag_set,
                    query_tokens=query_tokens,
                )
                and not self._documentary_setup_quality_floor(
                    entry=entry,
                    requested_tags=tag_set,
                    query_tokens=query_tokens,
                    documentary_case_linkage_score=documentary_case_linkage_score,
                    event_evidence_score=event_evidence_score,
                )
            ):
                continue
            if (
                segment_role == "setup"
                and self._is_generic_setup_entry(entry=entry)
                and setup_event_alignment_score <= 0.0
                and visual_world_score <= 0.4
            ):
                continue
            if (
                segment_role == "setup"
                and self._should_hard_reject_legacy_setup(
                    entry=entry,
                    catalog=catalog,
                    requested_category=category,
                )
            ):
                continue
            if score <= 0:
                continue
            jitter = self._deterministic_jitter(seed=seed, entry_path=entry.path)
            scored.append((score + jitter, entry.path))
        if not scored:
            replacement = self._preferred_new_real_replacement(
                catalog=catalog,
                requested_category=category,
                requested_tags=tag_set,
                query_tokens=query_tokens,
                exclude=exclude,
                seed=seed,
                segment_role=segment_role,
            )
            if replacement:
                return replacement
            return None
        scored.sort(key=lambda item: item[0], reverse=True)
        if scored[0][0] < minimum_score:
            return None
        selected_path = scored[0][1]
        selected_entry = next((entry for entry in catalog if entry.path == selected_path), None)
        if selected_entry is not None and segment_role in {"hook", "setup", "payoff"}:
            self._remember_sequence_choice(seed=seed, segment_role=segment_role, entry=selected_entry)
            self._remember_batch_family(entry=selected_entry, batch_key=batch_key)
            self._remember_batch_family_role(entry=selected_entry, batch_key=batch_key, segment_role=segment_role)
            if segment_role == "payoff":
                self._clear_sequence_context(seed=seed, segment_role=segment_role)
        return selected_path

    def safe_fallback(self, *, seed: str, exclude_paths: set[str] | None = None) -> str | None:
        catalog = self._load_catalog()
        if not catalog:
            return None
        exclude = exclude_paths or set()
        eligible = [
            entry
            for entry in catalog
            if self._is_runtime_eligible_entry(entry=entry) and entry.path not in exclude
        ]
        if not eligible:
            return None
        ranked = sorted(
            eligible,
            key=lambda entry: self._deterministic_jitter(seed=seed, entry_path=entry.path),
            reverse=True,
        )
        return ranked[0].path

    def audit_case_pack_rejections(
        self,
        *,
        tags: list[str],
        query_text: str,
        segment_role: str,
    ) -> dict[str, object]:
        tag_set = {tag.strip().lower() for tag in tags if tag}
        query_tokens = self._query_tokens(query_text)
        requested_case_pack = self._requested_case_pack(
            requested_tags=tag_set,
            query_tokens=query_tokens,
        )
        rejected: list[str] = []
        accepted: list[str] = []
        for entry in self._load_catalog():
            if not self._is_runtime_eligible_entry(entry=entry):
                continue
            if self._should_hard_reject_case_proxy(
                entry=entry,
                requested_case_pack=requested_case_pack,
                segment_role=segment_role,
            ):
                rejected.append(entry.path)
            else:
                accepted.append(entry.path)
        return {
            "segment_role": segment_role,
            "case_pack_active": bool(any(requested_case_pack.values())),
            "rejected_count": len(rejected),
            "accepted_count": len(accepted),
            "rejected_samples": rejected[:10],
            "accepted_samples": accepted[:10],
        }

    def _preferred_new_real_replacement(
        self,
        *,
        catalog: list[CatalogEntry],
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        exclude: set[str],
        seed: str,
        segment_role: str,
    ) -> str | None:
        requested_case_pack = self._requested_case_pack(
            requested_tags=requested_tags,
            query_tokens=query_tokens,
        )
        candidates: list[tuple[float, str]] = []
        for entry in catalog:
            if entry.path in exclude:
                continue
            if not self._is_runtime_eligible_entry(entry=entry):
                continue
            if not self._source_is_new_real(entry):
                continue
            if self._should_hard_reject_case_proxy(
                entry=entry,
                requested_case_pack=requested_case_pack,
                segment_role=segment_role,
            ):
                continue
            if self._category_score(category=requested_category, entry_category=entry.category) < 6.0:
                continue
            event_evidence_score = self._event_evidence_score(
                entry=entry,
                requested_tags=requested_tags,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            setup_event_alignment_score = self._setup_event_alignment_score(
                entry=entry,
                requested_tags=requested_tags,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            documentary_case_linkage_score = self._documentary_case_linkage_score(
                entry=entry,
                requested_tags=requested_tags,
                query_tokens=query_tokens,
                segment_role=segment_role,
            )
            if self._should_hard_reject_context_only(
                entry=entry,
                requested_category=requested_category,
                requested_tags=requested_tags,
                query_tokens=query_tokens,
                segment_role=segment_role,
                event_evidence_score=event_evidence_score,
                setup_event_alignment_score=setup_event_alignment_score,
                documentary_case_linkage_score=documentary_case_linkage_score,
            ):
                continue
            if self._should_hard_reject_world_drift(
                entry=entry,
                requested_tags=requested_tags,
                segment_role=segment_role,
                event_evidence_score=event_evidence_score,
            ):
                continue
            score = (
                entry.setup_specificity_score * 2.0
                + entry.realism_score * 1.5
                + entry.freshness_score * 1.2
                + entry.strength * 0.8
                - entry.genericity
                + event_evidence_score
                + self._deterministic_jitter(seed=seed, entry_path=entry.path)
            )
            candidates.append((score, entry.path))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _has_non_retired_alternative(
        self,
        *,
        catalog: list[CatalogEntry],
        entry: CatalogEntry,
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> bool:
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        for candidate in catalog:
            if candidate.path == entry.path:
                continue
            if self._is_retired_phase1_entry(entry=candidate):
                continue
            if self._category_score(category=requested_category, entry_category=candidate.category) < 4.4:
                continue
            candidate_tokens = self._entry_token_set(entry=candidate)
            match = len(requested_signals & candidate_tokens) + self._semantic_overlap(entry=candidate, query_tokens=query_tokens)
            if match <= 0 and candidate.category != requested_category:
                continue
            if self._segment_strength(entry=candidate, segment_role=segment_role) >= 1.0:
                return True
        return False

    def _deterministic_jitter(self, *, seed: str, entry_path: str) -> float:
        material = f"{seed}::{entry_path}".encode("utf-8")
        digest = sha256(material).hexdigest()
        return (int(digest[:8], 16) % 1000) / 1000.0

    def _category_score(self, *, category: str, entry_category: str) -> float:
        normalized = category.strip().lower()
        entry = entry_category.strip().lower()
        if normalized == entry:
            return 6.0
        aliases = {
            "device": {"screen", "intercom", "recorder", "camera", "warning_panel"},
            "document": {"archive", "transcript", "record", "file", "ledger", "map", "blueprint"},
            "archive": {"document", "evidence_surface", "transcript", "record", "file"},
            "corridor": {"hallway", "tunnel", "stairwell", "passage"},
            "institutional_space": {"warning_display", "intercom_recorder", "monitor_screen", "sealed_access", "door"},
            "horror_interior": {"sealed_access", "door", "corridor"},
            "room": {"lab", "office", "archive_room", "evidence_room"},
            "door": {"locked_door", "sealed_door", "entryway"},
        }
        if entry in aliases.get(normalized, set()):
            return 4.4
        return 0.0

    def _query_tokens(self, value: str) -> set[str]:
        return {
            token.strip().lower()
            for token in re.sub(r"[^a-z0-9]+", " ", value.lower()).split()
            if len(token.strip()) >= 4
        }

    def _source_is_new_real(self, entry: CatalogEntry) -> bool:
        return entry.source_type in {"pexels", "unsplash", "pixabay"}

    def _subtype_tokens(self, entry: CatalogEntry) -> set[str]:
        return {
            token.strip().lower()
            for token in entry.subtype.replace("-", "_").split("_")
            if len(token.strip()) >= 4
        }

    def _subtype_overlap(self, *, entry: CatalogEntry, query_tokens: set[str]) -> int:
        return len(self._subtype_tokens(entry) & query_tokens)

    def _semantic_overlap(self, *, entry: CatalogEntry, query_tokens: set[str]) -> int:
        semantic = {token.strip().lower() for token in entry.semantic_pattern_fit}
        entities = {token.strip().lower() for token in entry.entity_fit}
        return len(query_tokens & semantic) + len(query_tokens & entities)

    def _entry_token_set(self, *, entry: CatalogEntry) -> set[str]:
        tokens: set[str] = set()
        for value in [entry.category, entry.subtype, entry.family, entry.mood, entry.path]:
            tokens |= self._query_tokens(value)
        for collection in [entry.tags, entry.semantic_pattern_fit, entry.entity_fit]:
            for value in collection:
                tokens |= self._query_tokens(value)
                lowered = value.strip().lower()
                if lowered:
                    tokens.add(lowered)
        return tokens

    def _visual_entry_token_set(self, *, entry: CatalogEntry) -> set[str]:
        tokens: set[str] = set()
        for value in [entry.category, entry.subtype, entry.family, entry.path]:
            tokens |= self._query_tokens(value)
        for value in entry.tags:
            tokens |= self._query_tokens(value)
            lowered = value.strip().lower()
            if lowered:
                tokens.add(lowered)
        return tokens

    def _sequence_bucket(self, *, entry: CatalogEntry | None) -> str:
        if entry is None:
            return "none"
        entry_tokens = self._visual_entry_token_set(entry=entry)
        category = entry.category.strip().lower()
        family = (entry.family or entry.category).strip().lower()
        subtype = entry.subtype.strip().lower()
        if category in {"document", "evidence_surface"} or family in {"documentary_evidence", "document"}:
            return "document_evidence"
        if category in {"warning_display", "intercom_recorder", "monitor_screen"}:
            return "device_signal"
        if category in {"sealed_access", "door"}:
            return "barrier_signal"
        if category == "archive":
            return "archive_context"
        if category in {"corridor", "institutional_space"} and {"walkway", "hallway", "platform", "passage", "stair", "stairs", "corridor"} & entry_tokens:
            return "passage_context"
        if category in {"horror_interior", "room", "investigative_interior", "institutional_space"} and {"room", "interior", "wing", "office", "hall"} & entry_tokens:
            return "room_context"
        if family in {"investigative_ambient", "documentary_context"} or subtype in {"station_walkway", "public_walkway"}:
            return "generic_context"
        return "event_focus"

    def _same_visual_world(self, *, first: CatalogEntry | None, second: CatalogEntry | None) -> bool:
        if first is None or second is None:
            return False
        first_family = (first.family or first.category).strip().lower()
        second_family = (second.family or second.category).strip().lower()
        if first_family == second_family:
            return True
        allied_groups = (
            {"documentary_evidence", "document", "archive"},
            {"device_signal", "warning_display", "intercom_recorder", "monitor_screen", "institutional_space"},
            {"institutional_horror", "sealed_access", "door", "horror_interior", "corridor"},
        )
        first_bucket = {first_family, first.category.strip().lower()}
        second_bucket = {second_family, second.category.strip().lower()}
        return any(first_bucket & group and second_bucket & group for group in allied_groups)

    def _sequence_escalation_state(
        self,
        *,
        entry: CatalogEntry | None,
    ) -> set[str]:
        if entry is None:
            return set()
        tokens = self._visual_entry_token_set(entry=entry)
        return {
            token
            for token in {
                "anomaly", "changed", "timestamp", "date", "redacted", "marked", "evidence",
                "signal", "warning", "active", "sealed", "breach", "glow", "whisper",
                "presence", "distorted", "missing", "route", "security", "lock",
            }
            if token in tokens
        }

    def _setup_adds_new_state(
        self,
        *,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry,
    ) -> bool:
        setup_state = self._sequence_escalation_state(entry=setup_candidate)
        if not setup_state:
            return False
        hook_state = self._sequence_escalation_state(entry=hook_candidate)
        return bool(setup_state - hook_state) or len(setup_state) >= max(len(hook_state), 1)

    def detect_legacy_sequence_pattern(
        self,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry | None,
        payoff_candidate: CatalogEntry | None,
    ) -> bool:
        hook_bucket = self._sequence_bucket(entry=hook_candidate)
        setup_bucket = self._sequence_bucket(entry=setup_candidate)
        payoff_bucket = self._sequence_bucket(entry=payoff_candidate)

        if setup_bucket in {"generic_context", "archive_context", "passage_context", "room_context"}:
            if hook_bucket == "document_evidence" and payoff_bucket == "document_evidence":
                return True
            if hook_bucket in {"device_signal", "event_focus"} and payoff_bucket in {"barrier_signal", "device_signal"}:
                return True
            if hook_bucket != "none" and payoff_bucket != "none" and hook_bucket == payoff_bucket:
                return True
        if setup_bucket in {"passage_context", "generic_context"} and hook_bucket == "device_signal" and payoff_bucket == "barrier_signal":
            return True
        if setup_bucket in {"archive_context", "generic_context", "room_context"} and hook_bucket == "document_evidence" and payoff_bucket == "document_evidence":
            return True
        return False

    def _partial_legacy_setup_pattern(
        self,
        *,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry,
    ) -> bool:
        hook_bucket = self._sequence_bucket(entry=hook_candidate)
        setup_bucket = self._sequence_bucket(entry=setup_candidate)
        if hook_bucket == "document_evidence" and setup_bucket in {"archive_context", "generic_context", "room_context"}:
            return True
        if hook_bucket == "device_signal" and setup_bucket in {"passage_context", "generic_context"}:
            return True
        if hook_bucket in {"barrier_signal", "event_focus"} and setup_bucket in {"passage_context", "generic_context"}:
            return True
        return False

    def _requested_case_pack(
        self,
        *,
        requested_tags: set[str],
        query_tokens: set[str],
    ) -> dict[str, set[str]]:
        case_pack: dict[str, set[str]] = {
            "family": set(),
            "objects": set(),
            "evidence_forms": set(),
            "environments": set(),
            "forbidden_proxy_families": set(),
            "required_event_states": set(),
            "forbidden_symbolic_motifs": set(),
            "required_progression_steps": set(),
        }
        prefix_map = (
            ("case_family_", "family"),
            ("case_object_", "objects"),
            ("case_evidence_", "evidence_forms"),
            ("case_environment_", "environments"),
            ("case_forbid_", "forbidden_proxy_families"),
            ("case_state_", "required_event_states"),
            ("case_core_", "objects"),
            ("case_form_", "evidence_forms"),
            ("case_context_", "environments"),
            ("case_motif_forbid_", "forbidden_symbolic_motifs"),
            ("case_step_", "required_progression_steps"),
        )
        for tag in requested_tags:
            lowered = tag.strip().lower()
            for prefix, key in prefix_map:
                if not lowered.startswith(prefix):
                    continue
                value = lowered[len(prefix):].strip()
                if not value:
                    continue
                case_pack[key].add(value)
                case_pack[key] |= self._query_tokens(value.replace("_", " "))
        if not any(case_pack.values()):
            return case_pack
        # Keep request tokens to avoid over-pruning when family/object markers are sparse.
        case_pack["objects"] |= query_tokens
        return case_pack

    def _entry_family_tokens(self, *, entry: CatalogEntry) -> set[str]:
        values = [entry.family, entry.category, entry.subtype, entry.path]
        tokens: set[str] = set()
        for value in values:
            tokens |= self._query_tokens(str(value))
            slug = str(value).strip().lower().replace("-", "_").replace(" ", "_")
            if slug:
                tokens.add(slug)
        return tokens

    def _batch_key_from_case_pack(self, *, requested_case_pack: dict[str, set[str]]) -> str:
        return self._case_pack_batch_key(requested_case_pack=requested_case_pack, prefix="batch")

    def _case_pack_batch_key(self, *, requested_case_pack: dict[str, set[str]], prefix: str) -> str:
        family = sorted(token for token in requested_case_pack.get("family", set()) if token)
        objects = sorted(token for token in requested_case_pack.get("objects", set()) if token)
        environments = sorted(token for token in requested_case_pack.get("environments", set()) if token)
        if family:
            return f"{prefix}:family:{family[0]}"
        if objects:
            return f"{prefix}:object:{objects[0]}"
        if environments:
            return f"{prefix}:environment:{environments[0]}"
        return f"{prefix}:global"

    def _family_key(self, *, entry: CatalogEntry) -> str:
        family = (entry.family or entry.category).strip().lower()
        return family or entry.category.strip().lower()

    def _batch_usage_map_key(self, *, batch_key: str, family_key: str) -> str:
        return f"{batch_key}::{family_key}"

    def _remember_batch_family(self, *, entry: CatalogEntry, batch_key: str) -> None:
        family_key = self._family_key(entry=entry)
        map_key = self._batch_usage_map_key(batch_key=batch_key, family_key=family_key)
        self._batch_family_usage[map_key] = self._batch_family_usage.get(map_key, 0) + 1

    def _remember_batch_family_role(self, *, entry: CatalogEntry, batch_key: str, segment_role: str) -> None:
        family_key = self._family_key(entry=entry)
        map_key = f"{batch_key}::{segment_role}::{family_key}"
        self._batch_family_usage_by_role[map_key] = self._batch_family_usage_by_role.get(map_key, 0) + 1

    def _batch_family_count(self, *, entry: CatalogEntry, batch_key: str) -> int:
        family_key = self._family_key(entry=entry)
        map_key = self._batch_usage_map_key(batch_key=batch_key, family_key=family_key)
        return self._batch_family_usage.get(map_key, 0)

    def _batch_family_role_count(self, *, entry: CatalogEntry, batch_key: str, segment_role: str) -> int:
        family_key = self._family_key(entry=entry)
        map_key = f"{batch_key}::{segment_role}::{family_key}"
        return self._batch_family_usage_by_role.get(map_key, 0)

    def _family_saturation_threshold(self, *, segment_role: str) -> int:
        if segment_role == "hook":
            return 5
        if segment_role == "setup":
            return 3
        if segment_role == "payoff":
            return 3
        return 4

    def _role_family_saturation_threshold(self, *, segment_role: str) -> int:
        if segment_role == "hook":
            return 4
        if segment_role == "setup":
            return 2
        if segment_role == "payoff":
            return 2
        return 3

    def _batch_family_novelty_score(self, *, entry: CatalogEntry, batch_key: str) -> float:
        count = self._batch_family_count(entry=entry, batch_key=batch_key)
        if count == 0:
            return 1.2
        if count == 1:
            return 0.45
        if count == 2:
            return -0.75
        return -1.5

    def _batch_family_distribution(self, *, batch_key: str) -> dict[str, int]:
        prefix = f"{batch_key}::"
        distribution: dict[str, int] = {}
        for key, value in self._batch_family_usage.items():
            if not key.startswith(prefix):
                continue
            family = key[len(prefix):]
            distribution[family] = distribution.get(family, 0) + value
        return distribution

    def _dominant_family_share(self, *, batch_key: str) -> float:
        distribution = self._batch_family_distribution(batch_key=batch_key)
        if not distribution:
            return 0.0
        total = sum(distribution.values())
        if total <= 0:
            return 0.0
        dominant = max(distribution.values())
        return dominant / total

    def _dominant_family(self, *, batch_key: str) -> str:
        distribution = self._batch_family_distribution(batch_key=batch_key)
        if not distribution:
            return ""
        return max(distribution.items(), key=lambda item: item[1])[0]

    def _should_hard_reject_family_cap(
        self,
        *,
        entry: CatalogEntry,
        catalog: list[CatalogEntry],
        batch_key: str,
        segment_role: str,
        requested_case_pack: dict[str, set[str]],
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
    ) -> bool:
        family_count = self._batch_family_count(entry=entry, batch_key=batch_key)
        role_count = self._batch_family_role_count(entry=entry, batch_key=batch_key, segment_role=segment_role)
        if (
            family_count < self._family_saturation_threshold(segment_role=segment_role)
            and role_count < self._role_family_saturation_threshold(segment_role=segment_role)
        ):
            return False
        if not self._has_case_specific_alternative(
            catalog=catalog,
            entry=entry,
            requested_case_pack=requested_case_pack,
            requested_category=requested_category,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
            segment_role=segment_role,
        ):
            return False
        return True

    def _case_specificity_score(
        self,
        *,
        entry: CatalogEntry,
        requested_case_pack: dict[str, set[str]],
    ) -> float:
        if not any(requested_case_pack.values()):
            return 0.0
        entry_tokens = self._entry_token_set(entry=entry)
        family_tokens = self._entry_family_tokens(entry=entry)
        score = 0.0
        core_overlap = len((entry_tokens | family_tokens) & requested_case_pack["objects"])
        evidence_overlap = len(entry_tokens & requested_case_pack["evidence_forms"])
        state_overlap = len(entry_tokens & requested_case_pack["required_event_states"])
        context_overlap = len((entry_tokens | family_tokens) & requested_case_pack["environments"])
        step_overlap = len(entry_tokens & requested_case_pack["required_progression_steps"])
        score += min(core_overlap, 3) * 0.55
        score += min(evidence_overlap, 3) * 0.85
        score += min(state_overlap, 3) * 0.9
        score += min(context_overlap, 2) * 0.35
        score += min(step_overlap, 2) * 0.65
        return score

    def _new_evidence_value(
        self,
        *,
        entry: CatalogEntry,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry | None,
        segment_role: str,
    ) -> float:
        if segment_role == "hook":
            return 0.5
        current_state = self._sequence_escalation_state(entry=entry)
        if not current_state:
            return 0.0
        if segment_role == "setup":
            prior_state = self._sequence_escalation_state(entry=hook_candidate)
            delta = current_state - prior_state
            return min(len(delta), 3) * 0.9
        prior_state = self._sequence_escalation_state(entry=hook_candidate) | self._sequence_escalation_state(entry=setup_candidate)
        delta = current_state - prior_state
        return min(len(delta), 3) * 0.8

    def _anti_proxy_score(
        self,
        *,
        entry: CatalogEntry,
        requested_case_pack: dict[str, set[str]],
    ) -> float:
        if not any(requested_case_pack.values()):
            return 0.0
        entry_tokens = self._entry_token_set(entry=entry)
        if entry_tokens & requested_case_pack["forbidden_proxy_families"]:
            return -2.0
        if entry_tokens & requested_case_pack["forbidden_symbolic_motifs"]:
            return -2.0
        direct_case_overlap = len(
            entry_tokens
            & (
                requested_case_pack["objects"]
                | requested_case_pack["evidence_forms"]
                | requested_case_pack["required_event_states"]
            )
        )
        if direct_case_overlap <= 0:
            return -0.9
        return min(direct_case_overlap, 3) * 0.4

    def _has_case_specific_alternative(
        self,
        *,
        catalog: list[CatalogEntry],
        entry: CatalogEntry,
        requested_case_pack: dict[str, set[str]],
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> bool:
        target_family = self._family_key(entry=entry)
        for candidate in catalog:
            if candidate.path == entry.path:
                continue
            if not self._is_runtime_eligible_entry(entry=candidate):
                continue
            if self._family_key(entry=candidate) == target_family:
                continue
            if self._category_score(category=requested_category, entry_category=candidate.category) < 4.4:
                continue
            if self._should_hard_reject_case_proxy(
                entry=candidate,
                requested_case_pack=requested_case_pack,
                segment_role=segment_role,
            ):
                continue
            if self._case_specificity_score(entry=candidate, requested_case_pack=requested_case_pack) < 1.3:
                continue
            if self._event_evidence_score(
                entry=candidate,
                requested_tags=requested_tags,
                query_tokens=query_tokens,
                segment_role=segment_role,
            ) < 0.8:
                continue
            return True
        return False

    def _should_hard_reject_case_evidence_strict(
        self,
        *,
        entry: CatalogEntry,
        catalog: list[CatalogEntry],
        requested_case_pack: dict[str, set[str]],
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
        case_specificity_score: float,
        new_evidence_value: float,
        batch_family_novelty: float,
    ) -> bool:
        if not any(requested_case_pack.values()):
            return False
        entry_tokens = self._entry_token_set(entry=entry)
        if entry_tokens & requested_case_pack["forbidden_symbolic_motifs"]:
            return True
        min_specificity = 1.0 if segment_role == "hook" else 1.4 if segment_role == "setup" else 1.6
        if case_specificity_score < min_specificity:
            return True
        if segment_role == "setup" and new_evidence_value <= 0.0:
            return True
        if segment_role == "payoff" and new_evidence_value <= 0.0:
            return True
        family_count = self._batch_family_count(entry=entry, batch_key=self._batch_key_from_case_pack(requested_case_pack=requested_case_pack))
        if family_count >= 2 and batch_family_novelty <= -0.75:
            if not self._has_case_specific_alternative(
                catalog=catalog,
                entry=entry,
                requested_case_pack=requested_case_pack,
                requested_category=requested_category,
                requested_tags=requested_tags,
                query_tokens=query_tokens,
                segment_role=segment_role,
            ):
                return False
            if case_specificity_score < (2.0 if segment_role != "hook" else 1.6):
                return True
        return False

    def _should_hard_reject_case_proxy(
        self,
        *,
        entry: CatalogEntry,
        requested_case_pack: dict[str, set[str]],
        segment_role: str,
    ) -> bool:
        if not any(requested_case_pack.values()):
            return False
        entry_tokens = self._entry_token_set(entry=entry)
        family_tokens = self._entry_family_tokens(entry=entry)
        forbidden = requested_case_pack["forbidden_proxy_families"]
        motif_forbidden = requested_case_pack["forbidden_symbolic_motifs"]
        forbidden_union = forbidden | motif_forbidden
        if forbidden_union and ((entry_tokens | family_tokens) & forbidden_union):
            return True
        world_tokens = (
            requested_case_pack["family"]
            | requested_case_pack["objects"]
            | requested_case_pack["evidence_forms"]
            | requested_case_pack["environments"]
        )
        state_tokens = requested_case_pack["required_event_states"]
        in_case_world = bool((entry_tokens | family_tokens) & world_tokens)
        has_case_state = bool(entry_tokens & state_tokens)
        required_steps = requested_case_pack["required_progression_steps"]
        has_case_evidence = bool(entry_tokens & requested_case_pack["evidence_forms"])
        has_progression_marker = bool(entry_tokens & required_steps)

        if segment_role == "hook":
            return not (in_case_world or has_case_state or has_case_evidence or has_progression_marker)
        if segment_role == "setup":
            return not (in_case_world and (has_case_state or has_case_evidence or has_progression_marker))
        if segment_role == "payoff":
            return not (in_case_world and (has_case_state or has_case_evidence or has_progression_marker))
        return not in_case_world

    def _motif_signature(self, *, entry: CatalogEntry | None) -> str:
        if entry is None:
            return "none"
        bucket = self._sequence_bucket(entry=entry)
        family = (entry.family or entry.category).strip().lower()
        subtype = entry.subtype.strip().lower()
        return f"{bucket}|{family}|{subtype}"

    def _motif_reuse_penalty(
        self,
        *,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry | None,
        payoff_candidate: CatalogEntry | None,
        segment_role: str,
    ) -> float:
        if segment_role == "setup" and setup_candidate is not None and hook_candidate is not None:
            if self._motif_signature(entry=setup_candidate) == self._motif_signature(entry=hook_candidate):
                if not self._setup_adds_new_state(hook_candidate=hook_candidate, setup_candidate=setup_candidate):
                    return 4.2
            return 0.0
        if segment_role == "payoff" and payoff_candidate is not None:
            prior = setup_candidate or hook_candidate
            if prior is None:
                return 0.0
            if self._motif_signature(entry=payoff_candidate) == self._motif_signature(entry=prior):
                prior_state = self._sequence_escalation_state(entry=prior)
                payoff_state = self._sequence_escalation_state(entry=payoff_candidate)
                if not (payoff_state - prior_state):
                    return 3.8
        return 0.0

    def motif_loop_rejection(
        self,
        *,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry | None,
        payoff_candidate: CatalogEntry | None,
        segment_role: str,
    ) -> bool:
        if segment_role == "setup" and setup_candidate is not None and hook_candidate is not None:
            if self._motif_signature(entry=setup_candidate) == self._motif_signature(entry=hook_candidate):
                return not self._setup_adds_new_state(hook_candidate=hook_candidate, setup_candidate=setup_candidate)
        if segment_role == "payoff" and payoff_candidate is not None:
            prior = setup_candidate or hook_candidate
            if prior is not None and self._motif_signature(entry=payoff_candidate) == self._motif_signature(entry=prior):
                prior_state = self._sequence_escalation_state(entry=prior)
                payoff_state = self._sequence_escalation_state(entry=payoff_candidate)
                return not bool(payoff_state - prior_state)
        return False

    def evidence_progression_score(
        self,
        *,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry | None,
        payoff_candidate: CatalogEntry | None,
        segment_role: str,
    ) -> float:
        return self._sequence_progression_score(
            hook_candidate=hook_candidate,
            setup_candidate=setup_candidate,
            payoff_candidate=payoff_candidate,
            segment_role=segment_role,
        )

    def _requested_event_signals(self, *, requested_tags: set[str], query_tokens: set[str]) -> set[str]:
        signals: set[str] = set()
        for tag in requested_tags:
            lowered = tag.strip().lower()
            if lowered.startswith(("event_", "anomaly_", "evidence_", "visibility_", "context_")):
                signals |= self._query_tokens(lowered.replace("_", " "))
                signals.add(lowered)
        for token in query_tokens:
            if token in {
                "warning", "intercom", "signal", "audio", "device", "changed", "date", "timestamp",
                "redacted", "anomaly", "sealed", "security", "breach", "presence", "whisper",
                "glow", "blueprint", "map", "missing", "route", "distorted", "glitch",
            }:
                signals.add(token)
        return signals

    def _event_signal_expansion(self, *, signal: str) -> set[str]:
        expansions = {
            "warning": {"warning", "alert", "signal", "display", "panel", "screen", "intercom", "device", "activation"},
            "activation": {"warning", "alert", "signal", "display", "panel", "screen", "light", "active"},
            "intercom": {"intercom", "speaker", "recorder", "device", "panel", "warning"},
            "audio": {"audio", "voice", "intercom", "recorder", "speaker", "warning", "signal"},
            "changed": {"changed", "altered", "revised", "anomaly", "document", "date", "timestamp", "margin"},
            "date": {"date", "timestamp", "calendar", "future", "record", "log", "document", "casefile"},
            "timestamp": {"timestamp", "date", "clock", "record", "document", "casefile", "changed"},
            "contradiction": {"contradiction", "changed", "date", "timestamp", "future", "anomaly", "record"},
            "redacted": {"redacted", "marked", "anomaly", "document", "casefile", "evidence"},
            "anomaly": {"anomaly", "changed", "distorted", "redacted", "glow", "warning", "evidence"},
            "sealed": {"sealed", "lock", "security", "tape", "door", "restricted", "blocked"},
            "security": {"security", "lock", "sealed", "door", "warning", "panel", "restricted"},
            "breach": {"breach", "sealed", "door", "lock", "tape", "entry", "violation", "window"},
            "presence": {"presence", "whisper", "glow", "inside", "threshold", "wing", "room"},
            "whisper": {"whisper", "voice", "presence", "inside", "glow", "threshold"},
            "glow": {"glow", "window", "warning", "presence", "light"},
            "blueprint": {"blueprint", "map", "route", "exit", "corridor", "timetable"},
            "map": {"map", "blueprint", "route", "exit", "corridor", "timetable"},
            "missing": {"missing", "route", "exit", "blueprint", "map", "erased"},
            "route": {"route", "exit", "blueprint", "map", "corridor", "missing"},
            "glitch": {"glitch", "distorted", "signal", "screen", "camera", "warning", "impossible"},
            "distorted": {"distorted", "glitch", "impossible", "anomaly", "screen", "signal"},
            "archive": {"archive", "records", "storage", "files", "document"},
            "institutional": {"institutional", "hospital", "hallway", "corridor", "station", "wing"},
            "corridor": {"corridor", "hallway", "passage", "tunnel", "station", "wing"},
            "document": {"document", "record", "casefile", "file", "transcript", "evidence", "archive"},
        }
        return expansions.get(signal, {signal})

    def _style_signal_expansion(self, *, signal: str) -> set[str]:
        expansions = {
            "style_documentary_dark": {"document", "archive", "record", "casefile", "evidence", "files", "clinical", "tense", "dark"},
            "style_horror_institutional": {"sealed", "door", "wing", "window", "hospital", "ominous", "glow", "threshold", "institutional"},
            "style_institutional_cold": {"institutional", "corridor", "hallway", "hospital", "station", "platform", "clinical", "security"},
            "style_device_tense": {"warning", "signal", "display", "panel", "intercom", "device", "screen", "alert"},
            "style_archive_case": {"archive", "records", "files", "document", "casefile", "evidence", "storage"},
            "style_bridge_frame": {"medium", "wide", "corridor", "archive", "institutional", "room"},
            "style_reveal_frame": {"detail", "closeup", "anomaly", "warning", "document", "intercom", "glow", "evidence"},
        }
        return expansions.get(signal, set())

    def _visual_world_fields(self, *, requested_tags: set[str]) -> dict[str, set[str]]:
        mapping: dict[str, set[str]] = {
            "visual_family": set(),
            "environment_type": set(),
            "lighting_style": set(),
            "color_palette": set(),
            "texture_profile": set(),
            "realism_level": set(),
            "dominant_emotion": set(),
            "secondary_emotion": set(),
            "tension_level": set(),
            "mood": set(),
            "allowed_categories": set(),
            "preferred_families": set(),
            "preferred_moods": set(),
            "forbidden_patterns": set(),
        }
        prefixes = {
            "visual_family_": "visual_family",
            "environment_type_": "environment_type",
            "lighting_style_": "lighting_style",
            "color_palette_": "color_palette",
            "texture_profile_": "texture_profile",
            "realism_level_": "realism_level",
            "dominant_emotion_": "dominant_emotion",
            "secondary_emotion_": "secondary_emotion",
            "tension_level_": "tension_level",
            "mood_": "mood",
            "world_allow_": "allowed_categories",
            "world_family_": "preferred_families",
            "world_mood_": "preferred_moods",
            "world_forbid_": "forbidden_patterns",
        }
        for tag in requested_tags:
            lowered = tag.strip().lower()
            for prefix, bucket in prefixes.items():
                if lowered.startswith(prefix):
                    mapping[bucket].add(lowered[len(prefix):])
                    break
        return mapping

    def _visual_world_signal_expansion(self, *, signal: str) -> set[str]:
        expansions = {
            "documentary_caseworld": {"archive", "records", "document", "casefile", "evidence", "files", "storage"},
            "institutional_device_alert": {"warning", "intercom", "signal", "display", "panel", "device", "screen", "station"},
            "sealed_institutional_horror": {"sealed", "door", "threshold", "window", "wing", "hospital", "decay", "glow"},
            "institutional_passage_tension": {"corridor", "hallway", "institutional", "station", "platform", "tunnel", "passage"},
            "institutional_investigation": {"institutional", "document", "evidence", "corridor", "archive", "records"},
            "archive_evidence_interior": {"archive", "records", "files", "document", "storage", "evidence"},
            "device_institutional_interior": {"device", "warning", "intercom", "signal", "panel", "display", "corridor"},
            "contained_decay_interior": {"sealed", "door", "decay", "wing", "hospital", "corridor", "threshold"},
            "narrow_passage_interior": {"corridor", "hallway", "passage", "tunnel", "station", "institutional"},
            "interior_institutional": {"institutional", "interior", "corridor", "room", "archive", "hospital"},
            "low_key_cold": {"dark", "cold", "institutional", "ominous", "tense"},
            "low_key_documentary": {"document", "archive", "evidence", "clinical", "dark", "tense"},
            "contrast_device_glow": {"warning", "signal", "display", "intercom", "glow", "light", "screen"},
            "low_key_ominous": {"dark", "ominous", "sealed", "glow", "threshold", "hospital"},
            "cold_falloff": {"dark", "corridor", "hallway", "institutional", "night"},
            "desaturated_paper_steel": {"archive", "document", "paper", "clinical", "records"},
            "cold_gray_signal_red": {"warning", "signal", "panel", "screen", "device", "intercom"},
            "dirty_green_steel": {"sealed", "door", "hospital", "wing", "decay", "dark"},
            "gray_blue_shadow": {"corridor", "hallway", "institutional", "dark", "night"},
            "paper_grain_evidence": {"document", "paper", "record", "evidence", "casefile"},
            "metal_panel_noise": {"device", "panel", "intercom", "display", "screen", "warning"},
            "decay_threshold": {"sealed", "threshold", "door", "window", "decay", "horror"},
            "hard_surface_depth": {"corridor", "hallway", "platform", "station", "institutional"},
            "photorealistic": {"pexels", "unsplash", "pixabay", "clinical", "institutional"},
            "stylized_realistic": {"generated", "glow", "distorted", "impossible"},
            "mystery": {"archive", "document", "whisper", "record", "sealed", "dark"},
            "curiosity": {"document", "record", "archive", "detail", "casefile"},
            "threat": {"warning", "signal", "sealed", "door", "intercom", "glow"},
            "fear": {"sealed", "door", "horror", "hospital", "wing", "threshold"},
            "urgency": {"warning", "signal", "display", "alert", "panel"},
            "dread": {"whisper", "presence", "glow", "sealed", "inside"},
            "claustrophobia": {"corridor", "hallway", "door", "wing", "hospital", "sealed"},
            "tension": {"warning", "corridor", "archive", "dark", "sealed", "institutional"},
            "unease": {"changed", "date", "timestamp", "document", "corridor", "record"},
            "high": {"warning", "signal", "sealed", "breach", "glow", "alert"},
            "medium": {"corridor", "archive", "document", "institutional"},
            "investigative": {"archive", "document", "records", "evidence", "clinical"},
            "threatening": {"warning", "signal", "intercom", "sealed", "glow"},
            "oppressive": {"sealed", "horror", "wing", "door", "threshold", "hospital"},
            "mysterious": {"archive", "document", "corridor", "dark", "record", "whisper"},
        }
        return expansions.get(signal, {signal})

    def _visual_world_score(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        fields = self._visual_world_fields(requested_tags=requested_tags)
        entry_tokens = self._visual_entry_token_set(entry=entry)
        score = 0.0
        for field in ("visual_family", "environment_type", "lighting_style", "color_palette", "texture_profile", "realism_level", "mood"):
            for signal in fields[field]:
                overlap = len(self._visual_world_signal_expansion(signal=signal) & entry_tokens)
                if overlap > 0:
                    score += min(overlap, 3) * 0.32
        if entry.category in fields["allowed_categories"]:
            score += 0.85
        if (entry.family or entry.category).strip().lower() in fields["preferred_families"]:
            score += 1.1
        if entry.mood.strip().lower() in fields["preferred_moods"]:
            score += 0.55
        if segment_role == "setup" and fields["environment_type"]:
            score += 0.15 if entry.framing in {"medium", "wide"} else -0.15
        if segment_role == "payoff" and entry.framing in {"closeup", "detail"}:
            score += 0.2
        return score

    def _atmosphere_emotion_score(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        fields = self._visual_world_fields(requested_tags=requested_tags)
        entry_tokens = self._entry_token_set(entry=entry)
        score = 0.0
        for field in ("dominant_emotion", "secondary_emotion", "tension_level"):
            for signal in fields[field]:
                overlap = len(self._visual_world_signal_expansion(signal=signal) & entry_tokens)
                if overlap > 0:
                    score += min(overlap, 3) * 0.26
        constraint_tokens = {
            token.replace("constraint_", "")
            for token in requested_tags
            if token.startswith("constraint_")
        }
        if constraint_tokens:
            constraint_overlap = len(constraint_tokens & entry_tokens)
            score += min(constraint_overlap, 3) * 0.34
        if segment_role == "hook" and {"threat", "urgency", "fear"} & fields["dominant_emotion"] and entry.framing in {"closeup", "detail", "medium"}:
            score += 0.2
        return score

    def _visual_world_break_penalty(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        fields = self._visual_world_fields(requested_tags=requested_tags)
        entry_tokens = self._entry_token_set(entry=entry)
        penalty = 0.0
        corporate_tokens = {"people", "person", "group", "team", "business", "office", "meeting", "workspace", "corporate", "lifestyle"}
        forbidden_token_map = {
            "corporate_people": corporate_tokens,
            "bright_lifestyle": {"bright", "sunny", "lifestyle", "people", "workspace"},
            "sunny_exterior": {"sunny", "outdoor", "exterior", "landscape", "daylight"},
            "playful_stock": {"playful", "happy", "lifestyle", "team", "office"},
            "meeting_room": {"meeting", "conference", "office", "team", "workspace"},
            "lifestyle_office": {"lifestyle", "office", "workspace", "people", "desk"},
            "sunny_walkway": {"sunny", "walkway", "public_space", "outdoor"},
            "outdoor_daylight": {"outdoor", "daylight", "sunny", "landscape"},
            "bright_lobby": {"bright", "lobby", "open", "clean"},
            "clean_office": {"office", "workspace", "clean", "business"},
        }
        for pattern in fields["forbidden_patterns"]:
            overlap = forbidden_token_map.get(pattern, {pattern}) & entry_tokens
            if overlap:
                penalty += 1.25
        if fields["allowed_categories"] and entry.category not in fields["allowed_categories"]:
            penalty += 0.7
        if fields["preferred_families"] and (entry.family or entry.category).strip().lower() not in fields["preferred_families"]:
            penalty += 0.55
        if fields["preferred_moods"] and entry.mood.strip().lower() and entry.mood.strip().lower() not in fields["preferred_moods"]:
            penalty += 0.25
        if "stylized_realistic" in fields["realism_level"] and entry.source_type in {"pexels", "unsplash", "pixabay"} and {"impossible", "distorted", "glow"} & entry_tokens:
            penalty -= 0.2
        if segment_role == "setup" and corporate_tokens & entry_tokens:
            penalty += 0.7
        if segment_role in {"hook", "payoff"} and entry.category in {"institutional_space", "investigative_interior"} and not ({"warning", "signal", "archive", "document", "sealed", "glow", "evidence", "intercom"} & entry_tokens):
            penalty += 0.45
        return max(penalty, 0.0)

    def _event_evidence_score(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        if not requested_signals:
            return 0.0
        entry_tokens = self._entry_token_set(entry=entry)
        overlap = 0.0
        for signal in requested_signals:
            expansion = self._event_signal_expansion(signal=signal)
            signal_overlap = len(expansion & entry_tokens)
            if signal_overlap <= 0:
                continue
            overlap += min(signal_overlap, 3) * 0.42
        if overlap <= 0:
            return 0.0
        weight = 1.25
        if segment_role == "hook":
            weight = 1.7
        elif segment_role == "payoff":
            weight = 2.05
        return overlap * weight

    def _setup_event_alignment_score(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        if segment_role != "setup":
            return 0.0
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        if not requested_signals:
            return 0.0
        entry_tokens = self._entry_token_set(entry=entry)
        context_hits = 0
        for signal in requested_signals:
            expansion = self._event_signal_expansion(signal=signal)
            if expansion & entry_tokens:
                context_hits += 1
        score = min(context_hits, 3) * 0.55
        if {"archive", "document", "records"} & requested_signals and {"archive", "document", "records", "files", "storage"} & entry_tokens:
            score += 0.7
        if {"warning", "intercom", "signal"} & requested_signals and {"warning", "intercom", "signal", "panel", "display", "device"} & entry_tokens:
            score += 0.8
        if {"sealed", "breach", "presence", "whisper"} & requested_signals and {"sealed", "door", "security", "window", "glow", "threshold"} & entry_tokens:
            score += 0.8
        if {"map", "blueprint", "route", "missing"} & requested_signals and {"map", "blueprint", "route", "exit", "corridor"} & entry_tokens:
            score += 0.75
        return score

    def _style_coherence_score(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        style_tags = {tag for tag in requested_tags if tag.startswith("style_")}
        if not style_tags:
            return 0.0
        entry_tokens = self._entry_token_set(entry=entry)
        score = 0.0
        for tag in style_tags:
            expansion = self._style_signal_expansion(signal=tag)
            if not expansion:
                continue
            overlap = len(expansion & entry_tokens)
            if overlap <= 0:
                continue
            score += min(overlap, 3) * 0.3
        if segment_role == "setup" and "style_bridge_frame" in style_tags and entry.framing in {"medium", "wide"}:
            score += 0.35
        if segment_role == "payoff" and "style_reveal_frame" in style_tags and entry.framing in {"detail", "closeup"}:
            score += 0.45
        return score

    def _subtype_bonus(self, *, entry: CatalogEntry, subtype_overlap: int, segment_role: str) -> float:
        if subtype_overlap <= 0:
            return 0.0
        weight = 0.95 if segment_role == "setup" else 0.75
        return min(subtype_overlap, 2) * weight

    def _new_real_source_bonus(
        self,
        *,
        entry: CatalogEntry,
        category_score: float,
        tag_overlap: int,
        query_tag_overlap: int,
        semantic_overlap: int,
        subtype_overlap: int,
        segment_role: str,
    ) -> float:
        if not self._source_is_new_real(entry):
            return 0.0
        if category_score < 4.4:
            return 0.0
        match_strength = tag_overlap + query_tag_overlap + semantic_overlap + subtype_overlap
        if match_strength <= 0:
            return 0.0
        bonus = 0.8
        if category_score >= 6.0:
            bonus += 0.8
        bonus += min(match_strength, 4) * 0.35
        if subtype_overlap > 0:
            bonus += 0.45
        if segment_role == "setup" and entry.framing in {"medium", "wide"}:
            bonus += 0.25
        return bonus

    def _usage_penalty(self, *, entry: CatalogEntry) -> float:
        if self._source_is_new_real(entry):
            return min(entry.usage_count, 10) * 0.04
        return min(entry.usage_count, 12) * 0.16

    def _legacy_dominance_penalty(
        self,
        *,
        entry: CatalogEntry,
        category_score: float,
        tag_overlap: int,
        query_tag_overlap: int,
        subtype_overlap: int,
        has_strong_new_real_candidate: bool,
    ) -> float:
        if entry.source_type != "local_curated":
            return 0.0
        if not has_strong_new_real_candidate:
            return 0.0
        if category_score < 6.0:
            return 0.0
        penalty = 0.9
        if subtype_overlap == 0:
            penalty += 0.45
        if tag_overlap + query_tag_overlap <= 1:
            penalty += 0.45
        return penalty

    def _has_strong_new_real_candidate(
        self,
        *,
        catalog: list[CatalogEntry],
        requested_category: str,
        tag_set: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> bool:
        combined_query = tag_set | query_tokens
        for entry in catalog:
            if not self._source_is_new_real(entry):
                continue
            category_score = self._category_score(category=requested_category, entry_category=entry.category)
            if category_score < 6.0:
                continue
            entry_tags = {tag.strip().lower() for tag in entry.tags}
            subtype_overlap = self._subtype_overlap(entry=entry, query_tokens=combined_query)
            semantic_overlap = self._semantic_overlap(entry=entry, query_tokens=query_tokens)
            match_strength = len(tag_set & entry_tags) + len(query_tokens & entry_tags) + semantic_overlap + subtype_overlap
            if match_strength <= 0:
                continue
            role_strength = self._segment_strength(entry=entry, segment_role=segment_role)
            if role_strength >= 1.6 and entry.realism_score >= 0.9:
                return True
        return False

    def _segment_strength(self, *, entry: CatalogEntry, segment_role: str) -> float:
        role = segment_role.strip().lower()
        if role == "hook":
            return entry.hook_strength_score * 2.4
        if role == "payoff":
            return entry.payoff_strength_score * 2.2
        return ((entry.hook_strength_score + entry.payoff_strength_score) / 2.0) * 1.3

    def _fit_bonus(self, *, entry: CatalogEntry, query_tokens: set[str]) -> float:
        semantic = {token.strip().lower() for token in entry.semantic_pattern_fit}
        entities = {token.strip().lower() for token in entry.entity_fit}
        score = 0.0
        score += len(query_tokens & semantic) * 1.4
        score += len(query_tokens & entities) * 1.25
        if entry.mood and entry.mood.lower() in query_tokens:
            score += 0.7
        if entry.subtype and entry.subtype.lower() in query_tokens:
            score += 1.0
        return score

    def _segment_role_bonus(
        self,
        *,
        requested_category: str,
        entry: CatalogEntry,
        segment_role: str,
        requested_tags: set[str],
        query_tokens: set[str],
    ) -> float:
        role = segment_role.strip().lower()
        requested = requested_category.strip().lower()
        entry_category = entry.category.strip().lower()
        entry_tokens = self._entry_token_set(entry=entry)
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)

        if role == "setup":
            score = entry.setup_specificity_score * 2.2
            if requested == entry_category:
                score += 1.8
            if requested in {"institutional_space", "investigative_interior", "archive", "room", "corridor", "horror_interior"} and entry_category in {
                "warning_display",
                "intercom_recorder",
                "monitor_screen",
                "document",
                "evidence_surface",
                "sealed_access",
                "door",
            }:
                if self._has_visible_event_state(
                    entry=entry,
                    requested_tags=requested_tags,
                    query_tokens=query_tokens,
                    event_evidence_score=self._event_evidence_score(
                        entry=entry,
                        requested_tags=requested_tags,
                        query_tokens=query_tokens,
                        segment_role="setup",
                    ),
                    documentary_case_linkage_score=self._documentary_case_linkage_score(
                        entry=entry,
                        requested_tags=requested_tags,
                        query_tokens=query_tokens,
                        segment_role="setup",
                    ),
                ):
                    score += 1.4
                else:
                    score -= 0.9
            if {"archive", "document"} & requested_signals and not ({"archive", "records", "files", "document"} & entry_tokens):
                score -= 1.0
            if {"institutional", "corridor", "hospital", "station", "wing"} & requested_signals and not ({"institutional", "corridor", "hallway", "hospital", "station", "wing"} & entry_tokens):
                score -= 1.0
            if "public_space" in entry.tags or "walkway" in entry.tags:
                score -= 0.8
            if entry.framing == "closeup":
                score -= 0.9
            if self._is_generic_setup_entry(entry=entry):
                score -= 0.7
            return score
        if role == "hook":
            score = 0.0
            if requested in {"warning_display", "intercom_recorder", "document", "sealed_access"} and requested == entry_category:
                score += 1.2
            if entry.framing in {"closeup", "detail"}:
                score += 0.9
            return score
        if role == "payoff":
            score = 0.0
            if requested == entry_category:
                score += 1.0
            if entry.framing in {"closeup", "detail"}:
                score += 1.25
            if entry.framing == "wide":
                score -= 0.8
            if {"changed", "date", "timestamp", "redacted", "anomaly", "warning", "sealed", "breach", "whisper", "glow"} & requested_signals:
                if entry.framing not in {"closeup", "detail"}:
                    score -= 0.7
            return score
        return 0.0

    def _is_generic_setup_entry(self, *, entry: CatalogEntry) -> bool:
        entry_tokens = self._entry_token_set(entry=entry)
        generic_categories = {"corridor", "room", "institutional_space", "investigative_interior"}
        if entry.category not in generic_categories:
            return False
        return not bool(
            {"archive", "records", "document", "files", "warning", "intercom", "signal", "sealed", "security", "window", "map", "blueprint", "glow", "casefile"} & entry_tokens
        )

    def _family_usage_totals(self, *, catalog: list[CatalogEntry]) -> dict[str, int]:
        totals: dict[str, int] = {}
        for entry in catalog:
            family = entry.family or entry.category
            totals[family] = totals.get(family, 0) + max(entry.usage_count, 0)
        return totals

    def _has_valid_alternative_family(
        self,
        *,
        catalog: list[CatalogEntry],
        entry: CatalogEntry,
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> bool:
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        for candidate in catalog:
            if candidate.path == entry.path:
                continue
            if (candidate.family or candidate.category) == (entry.family or entry.category):
                continue
            if self._category_score(category=requested_category, entry_category=candidate.category) < 4.4:
                continue
            candidate_tokens = self._entry_token_set(entry=candidate)
            match = len(requested_signals & candidate_tokens) + self._semantic_overlap(entry=candidate, query_tokens=query_tokens)
            if match <= 0:
                continue
            if self._segment_strength(entry=candidate, segment_role=segment_role) >= 1.0:
                return True
        return False

    def _family_usage_penalty(
        self,
        *,
        entry: CatalogEntry,
        catalog: list[CatalogEntry],
        family_usage: dict[str, int],
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        family = entry.family or entry.category
        usage = family_usage.get(family, 0)
        if usage <= 0:
            return 0.0
        if not self._has_valid_alternative_family(
            catalog=catalog,
            entry=entry,
            requested_category=requested_category,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
            segment_role=segment_role,
        ):
            return 0.0
        penalty = min(usage, 8) * 0.12
        if segment_role == "setup":
            penalty += 0.18
        return penalty

    def _style_break_penalty(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        style_tags = {tag for tag in requested_tags if tag.startswith("style_")}
        if not style_tags:
            return 0.0
        entry_tokens = self._entry_token_set(entry=entry)
        penalty = 0.0
        corporate_tokens = {"people", "person", "group", "team", "business", "office", "meeting", "workspace", "corporate"}
        if (
            {"style_documentary_dark", "style_horror_institutional", "style_archive_case", "style_institutional_cold"} & style_tags
            and corporate_tokens & entry_tokens
        ):
            penalty += 1.4
        if "style_horror_institutional" in style_tags and {"bright", "sunny", "outdoor"} & entry_tokens:
            penalty += 1.2
        if "style_documentary_dark" in style_tags and {"playful", "lifestyle"} & entry_tokens:
            penalty += 1.0
        if segment_role == "setup" and "style_bridge_frame" in style_tags and entry.framing == "detail":
            penalty += 0.7
        return penalty

    def _payoff_under_delivery_penalty(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
        event_evidence_score: float,
    ) -> float:
        if segment_role != "payoff":
            return 0.0
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        if not requested_signals:
            return 0.0
        penalty = 0.0
        if event_evidence_score < 1.0:
            penalty += 1.1
        if entry.framing not in {"detail", "closeup"}:
            penalty += 0.6
        return penalty

    def _setup_generic_penalty(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        if segment_role != "setup":
            return 0.0
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        entry_tokens = self._entry_token_set(entry=entry)
        penalty = 0.0
        if {"archive", "document", "records"} & requested_signals and {"corridor", "hallway", "institutional"} & entry_tokens and not {"archive", "document", "records", "files"} & entry_tokens:
            penalty += 1.0
        if {"warning", "intercom", "signal"} & requested_signals and entry.category in {"corridor", "room", "institutional_space"} and not {"intercom", "warning", "signal", "device"} & entry_tokens:
            penalty += 0.9
        if {"sealed", "breach", "presence", "whisper"} & requested_signals and entry.category in {"corridor", "institutional_space"} and not {"sealed", "security", "door", "window", "glow", "threshold"} & entry_tokens:
            penalty += 0.95
        return penalty

    def _framing_bonus(self, *, entry: CatalogEntry, segment_role: str) -> float:
        role = segment_role.strip().lower()
        framing = entry.framing.strip().lower()
        if role == "hook":
            if framing == "closeup":
                return 0.9
            if framing == "medium":
                return 0.45
        if role == "setup":
            if framing == "wide":
                return 0.55
            if framing == "medium":
                return 0.35
        if role == "payoff":
            if framing == "detail":
                return 1.1
            if framing == "closeup":
                return 0.85
        return 0.0

    def _legacy_visual_family(self, *, entry: CatalogEntry) -> str | None:
        if self._is_retired_phase1_entry(entry=entry):
            lowered = entry.path.replace("\\", "/").lower()
            if "archive/" in lowered:
                return "generic_archive_shelf"
            if "institutional_space/" in lowered:
                return "neutral_hallway"
            if "intercom_recorder/" in lowered or "warning_display/" in lowered:
                return "phase1_device_closeup"
            if "door/" in lowered or "horror_interior/" in lowered:
                return "phase1_institutional_horror"
            if "investigative_interior/" in lowered or "room/" in lowered:
                return "empty_room_context"
        entry_tokens = self._entry_token_set(entry=entry)
        family = (entry.family or entry.category).strip().lower()
        subtype = entry.subtype.strip().lower()

        if family in {"documentary_context"} or (
            entry.category == "archive"
            and {"shelves", "storage", "records"} & entry_tokens
            and not {"anomaly", "changed", "date", "timestamp", "evidence", "redacted"} & entry_tokens
        ):
            return "generic_archive_shelf"
        if (
            entry.category in {"corridor", "institutional_space"}
            and {"walkway", "public_space"} & entry_tokens
        ) or subtype in {"public_walkway", "station_walkway"}:
            return "open_walkway"
        if (
            entry.category in {"corridor", "institutional_space"}
            and {"corridor", "hallway", "institutional"} & entry_tokens
            and not {"warning", "intercom", "signal", "sealed", "glow", "archive", "map", "blueprint", "records"} & entry_tokens
        ):
            return "neutral_hallway" if entry.category == "institutional_space" else "generic_corridor"
        if (
            entry.category in {"room", "investigative_interior", "institutional_space"}
            and {"room", "interior", "lab", "office"} & entry_tokens
            and not {"warning", "intercom", "signal", "archive", "records", "document", "sealed", "threshold", "glow", "map"} & entry_tokens
        ):
            return "empty_room_context"
        return None

    def _is_retired_phase1_entry(self, *, entry: CatalogEntry) -> bool:
        return entry.phase1_legacy or entry.path.replace("\\", "/").lower() in self.RETIRED_PHASE1_PATHS

    def _has_visible_event_state(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        event_evidence_score: float,
        documentary_case_linkage_score: float,
    ) -> bool:
        entry_tokens = self._visual_entry_token_set(entry=entry)
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        visible_state_tokens = {
            "anomaly", "changed", "altered", "timestamp", "date", "redacted", "marked",
            "evidence", "casefile", "case_file", "surface", "transcript", "warning",
            "alert", "signal", "active", "sealed", "lock", "security", "breach",
            "glow", "whisper", "presence", "distorted", "glitch", "missing", "route",
            "erased", "panel", "screen", "device", "door", "window",
        }
        non_visible_context_signals = {"archive", "institutional", "corridor", "document"}
        if bool(visible_state_tokens & entry_tokens):
            return True
        if documentary_case_linkage_score >= 1.0:
            return True
        for signal in requested_signals:
            if signal in non_visible_context_signals:
                continue
            visible_overlap = self._event_signal_expansion(signal=signal) & visible_state_tokens & entry_tokens
            if visible_overlap:
                return True
        return False

    def _is_context_only_entry(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        event_evidence_score: float,
        documentary_case_linkage_score: float,
    ) -> bool:
        contextual_categories = {
            "archive",
            "corridor",
            "room",
            "institutional_space",
            "investigative_interior",
            "horror_interior",
            "document",
        }
        if entry.category not in contextual_categories:
            return False
        return not self._has_visible_event_state(
            entry=entry,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
            event_evidence_score=event_evidence_score,
            documentary_case_linkage_score=documentary_case_linkage_score,
        )

    def _should_hard_reject_context_only(
        self,
        *,
        entry: CatalogEntry,
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
        event_evidence_score: float,
        setup_event_alignment_score: float,
        documentary_case_linkage_score: float,
    ) -> bool:
        if segment_role == "hook":
            return False
        visible_state = self._has_visible_event_state(
            entry=entry,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
            event_evidence_score=event_evidence_score,
            documentary_case_linkage_score=documentary_case_linkage_score,
        )
        if self._is_context_only_entry(
            entry=entry,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
            event_evidence_score=event_evidence_score,
            documentary_case_linkage_score=documentary_case_linkage_score,
        ):
            return True
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        documentary_request = self._is_documentary_transition_request(
            requested_category=requested_category,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
        )
        if documentary_request:
            if segment_role == "payoff":
                return not (
                    visible_state
                    and (documentary_case_linkage_score >= 1.0 or event_evidence_score >= 1.8)
                )
            return not (
                visible_state
                and (
                    documentary_case_linkage_score >= 1.0
                    or (event_evidence_score >= 1.8 and setup_event_alignment_score >= 1.2)
                )
            )
        if segment_role == "payoff":
            return not (visible_state and event_evidence_score >= 1.0)
        if requested_signals:
            return not (
                visible_state
                and (event_evidence_score >= 0.8 or setup_event_alignment_score >= 1.0)
            )
        return not visible_state

    def _should_hard_reject_setup_progression(
        self,
        *,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        event_evidence_score: float,
        documentary_case_linkage_score: float,
    ) -> bool:
        if self.motif_loop_rejection(
            hook_candidate=hook_candidate,
            setup_candidate=setup_candidate,
            payoff_candidate=None,
            segment_role="setup",
        ):
            return True
        if self._partial_legacy_setup_pattern(
            hook_candidate=hook_candidate,
            setup_candidate=setup_candidate,
        ):
            return True
        if not self._has_visible_event_state(
            entry=setup_candidate,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
            event_evidence_score=event_evidence_score,
            documentary_case_linkage_score=documentary_case_linkage_score,
        ):
            return True
        if not self._setup_adds_new_state(
            hook_candidate=hook_candidate,
            setup_candidate=setup_candidate,
        ):
            return True
        return False

    def _should_hard_reject_sequence_candidate(
        self,
        *,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry | None,
        payoff_candidate: CatalogEntry,
    ) -> bool:
        if self.motif_loop_rejection(
            hook_candidate=hook_candidate,
            setup_candidate=setup_candidate,
            payoff_candidate=payoff_candidate,
            segment_role="payoff",
        ):
            return True
        return self.detect_legacy_sequence_pattern(
            hook_candidate=hook_candidate,
            setup_candidate=setup_candidate,
            payoff_candidate=payoff_candidate,
        )

    def _sequence_progression_score(
        self,
        *,
        hook_candidate: CatalogEntry | None,
        setup_candidate: CatalogEntry | None,
        payoff_candidate: CatalogEntry | None,
        segment_role: str,
    ) -> float:
        score = 0.0
        if segment_role == "setup" and setup_candidate is not None:
            if self._same_visual_world(first=hook_candidate, second=setup_candidate):
                score += 0.8
            if self._setup_adds_new_state(hook_candidate=hook_candidate, setup_candidate=setup_candidate):
                score += 2.2
            if self._sequence_bucket(entry=setup_candidate) in {"document_evidence", "device_signal", "barrier_signal", "event_focus"}:
                score += 1.1
            if self._partial_legacy_setup_pattern(hook_candidate=hook_candidate, setup_candidate=setup_candidate):
                score -= 5.0
            return score
        if segment_role == "payoff" and payoff_candidate is not None:
            if self._same_visual_world(first=setup_candidate or hook_candidate, second=payoff_candidate):
                score += 0.7
            payoff_state = self._sequence_escalation_state(entry=payoff_candidate)
            prior_state = self._sequence_escalation_state(entry=setup_candidate) | self._sequence_escalation_state(entry=hook_candidate)
            if payoff_state - prior_state:
                score += 1.8
            if payoff_candidate.framing in {"detail", "closeup"}:
                score += 0.6
            if self.detect_legacy_sequence_pattern(
                hook_candidate=hook_candidate,
                setup_candidate=setup_candidate,
                payoff_candidate=payoff_candidate,
            ):
                score -= 6.0
            return score
        return score

    def _should_hard_reject_world_drift(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        segment_role: str,
        event_evidence_score: float,
    ) -> bool:
        if segment_role == "hook":
            return False
        fields = self._visual_world_fields(requested_tags=requested_tags)
        if not fields["preferred_families"]:
            return False
        family = (entry.family or entry.category).strip().lower()
        if family in fields["preferred_families"]:
            return False
        if entry.category in fields["allowed_categories"]:
            return False
        return event_evidence_score < 1.4

    def _event_dominance_multiplier(
        self,
        *,
        entry: CatalogEntry,
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
        event_evidence_score: float,
        documentary_case_linkage_score: float,
    ) -> float:
        if segment_role == "hook":
            return 1.0
        entry_tokens = self._entry_token_set(entry=entry)
        multiplier = 1.0
        if event_evidence_score >= 2.0:
            multiplier += 1.15
        elif event_evidence_score >= 1.2:
            multiplier += 0.55
        if {
            "anomaly", "changed", "timestamp", "date", "redacted", "marked", "evidence",
            "warning", "signal", "breach", "glow", "whisper", "presence", "distorted",
        } & entry_tokens:
            multiplier += 0.45
        if documentary_case_linkage_score >= 1.0:
            multiplier += 0.4
        if segment_role == "payoff" and entry.framing in {"closeup", "detail"}:
            multiplier += 0.25
        if (
            segment_role == "setup"
            and self._is_documentary_transition_request(
                requested_category=requested_category,
                requested_tags=requested_tags,
                query_tokens=query_tokens,
            )
            and entry.category in {"document", "evidence_surface"}
        ):
            multiplier += 0.35
        return multiplier

    def _setup_has_quality_floor(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        event_evidence_score: float,
        setup_event_alignment_score: float,
    ) -> bool:
        entry_tokens = self._entry_token_set(entry=entry)
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        contextual_evidence_tokens = {
            "archive", "records", "files", "document", "warning", "intercom", "signal",
            "sealed", "security", "window", "threshold", "map", "blueprint", "route",
            "hospital", "wing", "station", "platform", "notice",
        }
        has_event_hint = event_evidence_score >= 1.0
        has_contextual_evidence = bool((requested_signals | contextual_evidence_tokens) & entry_tokens) and setup_event_alignment_score >= 0.75
        increases_tension = entry.mood.strip().lower() in {"tense", "ominous"} or {"dark", "glow", "warning", "sealed"} & entry_tokens
        return has_event_hint or has_contextual_evidence or increases_tension

    def _is_documentary_transition_request(
        self,
        *,
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
    ) -> bool:
        requested = requested_category.strip().lower()
        requested_signals = self._requested_event_signals(requested_tags=requested_tags, query_tokens=query_tokens)
        documentary_tokens = {"archive", "document", "records", "casefile", "record", "transcript", "timestamp", "date", "page", "file", "form", "redacted", "changed"}
        documentary_tag_markers = {
            "style_archive_case",
            "visual_family_documentary_caseworld",
            "context_archive",
            "context_document",
            "evidence_document_anomaly",
            "evidence_date",
            "evidence_timestamp",
            "evidence_redacted",
        }
        return (
            requested in {"archive", "document", "evidence_surface", "investigative_interior"}
            or bool((requested_signals | query_tokens) & documentary_tokens)
            or bool(requested_tags & documentary_tag_markers)
        )

    def _documentary_transition_family(self, *, entry: CatalogEntry) -> str | None:
        entry_tokens = self._entry_token_set(entry=entry)
        family = (entry.family or entry.category).strip().lower()
        if entry.category == "archive" and family in {"archive", "documentary_context"}:
            if {"archive", "records", "storage", "shelves", "files"} & entry_tokens and not {"anomaly", "redacted", "timestamp", "date", "changed", "casefile", "evidence", "surface", "marked", "page", "form", "transcript"} & entry_tokens:
                return "generic_document_storage_ambience"
        if entry.category in {"archive", "investigative_interior", "institutional_space"} and {"archive", "records", "room", "hall", "storage"} & entry_tokens:
            if not {"anomaly", "redacted", "timestamp", "date", "casefile", "evidence", "surface", "marked", "page", "form", "transcript"} & entry_tokens:
                return "generic_records_room"
        return None

    def _documentary_case_linkage_score(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
    ) -> float:
        if segment_role != "setup":
            return 0.0
        if not self._is_documentary_transition_request(
            requested_category=entry.category,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
        ):
            return 0.0
        entry_tokens = self._entry_token_set(entry=entry)
        score = 0.0
        linkage_tokens = {
            "redacted", "timestamp", "date", "changed", "anomaly", "casefile", "evidence",
            "surface", "marked", "page", "form", "transcript", "recording",
        }
        overlap = len(linkage_tokens & entry_tokens)
        score += min(overlap, 4) * 0.55
        if entry.category in {"document", "evidence_surface"}:
            score += 1.2
        if entry.framing in {"closeup", "detail"}:
            score += 0.8
        if {"case_file", "casefile"} & entry_tokens:
            score += 0.8
        return score

    def _documentary_setup_quality_floor(
        self,
        *,
        entry: CatalogEntry,
        requested_tags: set[str],
        query_tokens: set[str],
        documentary_case_linkage_score: float,
        event_evidence_score: float,
    ) -> bool:
        if not self._is_documentary_transition_request(
            requested_category=entry.category,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
        ):
            return True
        entry_tokens = self._entry_token_set(entry=entry)
        has_anomaly_marker = bool({"anomaly", "redacted", "timestamp", "date", "changed", "marked"} & entry_tokens)
        has_case_surface = bool({"casefile", "case_file", "evidence", "surface", "transcript", "form", "page"} & entry_tokens)
        has_institutional_signal = bool({"warning", "label", "notice", "sealed", "security"} & entry_tokens)
        closer_evidence_framing = entry.framing in {"closeup", "detail"}
        explicit_investigative_context = bool({"investigation", "records", "archive", "document"} & entry_tokens and {"desk", "surface", "evidence", "casefile"} & entry_tokens)
        return (
            documentary_case_linkage_score >= 1.8
            or event_evidence_score >= 1.4
            or has_anomaly_marker
            or has_case_surface
            or (has_institutional_signal and closer_evidence_framing)
            or explicit_investigative_context
        )

    def _legacy_family_penalty(
        self,
        *,
        entry: CatalogEntry,
        catalog: list[CatalogEntry],
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
        event_evidence_score: float,
        setup_event_alignment_score: float,
    ) -> float:
        legacy_family = self._legacy_visual_family(entry=entry)
        if legacy_family is None:
            return 0.0
        penalty = 0.85
        if segment_role == "setup":
            penalty += 0.95
            if event_evidence_score >= 1.0 or setup_event_alignment_score >= 1.0:
                penalty -= 0.9
        if self._has_valid_alternative_family(
            catalog=catalog,
            entry=entry,
            requested_category=requested_category,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
            segment_role=segment_role,
        ):
            penalty += 0.75
        return penalty

    def _legacy_pool_lock_in_penalty(
        self,
        *,
        entry: CatalogEntry,
        catalog: list[CatalogEntry],
        requested_category: str,
        segment_role: str,
        has_strong_new_real_candidate: bool,
    ) -> float:
        has_new_real_alternative = has_strong_new_real_candidate or any(
            self._source_is_new_real(candidate)
            and self._category_score(category=requested_category, entry_category=candidate.category) >= 6.0
            and candidate.realism_score >= 0.9
            and candidate.freshness_score >= 0.75
            for candidate in catalog
        )
        if not has_new_real_alternative:
            return 0.0
        if entry.source_type != "local_curated":
            return 0.0
        if segment_role != "setup":
            return 0.0
        if entry.freshness_score >= 0.8:
            return 0.0
        if entry.setup_specificity_score >= 0.7 and entry.genericity <= 0.12:
            return 0.0
        return 1.8

    def _should_hard_reject_legacy_setup(
        self,
        *,
        entry: CatalogEntry,
        catalog: list[CatalogEntry],
        requested_category: str,
    ) -> bool:
        if entry.source_type != "local_curated":
            return False
        if entry.setup_specificity_score >= 0.7:
            return False
        return any(
            self._source_is_new_real(candidate)
            and self._category_score(category=requested_category, entry_category=candidate.category) >= 6.0
            and candidate.realism_score >= 0.9
            and candidate.setup_specificity_score >= 0.7
            for candidate in catalog
        )

    def _documentary_transition_penalty(
        self,
        *,
        entry: CatalogEntry,
        catalog: list[CatalogEntry],
        requested_category: str,
        requested_tags: set[str],
        query_tokens: set[str],
        segment_role: str,
        documentary_case_linkage_score: float,
    ) -> float:
        if segment_role != "setup":
            return 0.0
        if not self._is_documentary_transition_request(
            requested_category=requested_category,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
        ):
            return 0.0
        transition_family = self._documentary_transition_family(entry=entry)
        if transition_family is None:
            return 0.0
        penalty = 1.55
        if documentary_case_linkage_score < 1.0:
            penalty += 1.25
        if self._has_valid_alternative_family(
            catalog=catalog,
            entry=entry,
            requested_category=requested_category,
            requested_tags=requested_tags,
            query_tokens=query_tokens,
            segment_role=segment_role,
        ):
            penalty += 1.0
        return penalty
