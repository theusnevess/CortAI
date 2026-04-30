from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.creative.contracts.agent_common import FallbackDecision
from app.creative.contracts.creative_pack import AssetPlan
from app.runtime.asset_selector import AssetSelector, CatalogEntry


ASSET_SOURCE_POLICY_VERSION = "local_catalog_only_v2_6"


@dataclass(frozen=True)
class AssetSelectedSource:
    segment: str
    path: str
    source_type: str
    source_class: str
    catalog_present: bool
    eligible_for_runtime: bool
    governance_status: str
    reason_code: str
    rationale: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetIneligibleSourceSummary:
    source_type: str
    reason_code: str
    count: int
    sample_paths: list[str]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AssetCatalogSourceGovernanceResult:
    policy_version: str
    policy_respected: bool
    catalog_available: bool
    catalog_path: str
    catalog_entry_count: int
    eligible_entry_count: int
    source_policy: dict[str, Any]
    selected_sources: list[AssetSelectedSource]
    ineligible_sources: list[AssetIneligibleSourceSummary]
    fallback_sources: list[dict[str, Any]]
    source_status_distribution: dict[str, int]
    source_mix: dict[str, int]
    coverage_limitations: list[str]
    governance_trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["selected_sources"] = [source.to_dict() for source in self.selected_sources]
        payload["ineligible_sources"] = [source.to_dict() for source in self.ineligible_sources]
        return payload


@dataclass(frozen=True)
class AssetCatalogSourceGovernanceEvaluator:
    """Read-only source governance for already-selected assets."""

    def evaluate(
        self,
        *,
        selector: AssetSelector,
        asset_selection: AssetPlan,
        fallback: FallbackDecision,
        local_assets_available: bool,
    ) -> AssetCatalogSourceGovernanceResult:
        catalog_entries, catalog_error = self._load_catalog(selector)
        entry_by_path = {
            self._normalize_path(entry.path): entry
            for entry in catalog_entries
        }
        selected_sources = [
            self._selected_source(
                segment=segment,
                path=path,
                selector=selector,
                entry_by_path=entry_by_path,
                fallback=fallback,
            )
            for segment, path in (
                ("hook", asset_selection.hook_asset),
                ("setup", asset_selection.setup_asset),
                ("payoff", asset_selection.payoff_asset),
            )
        ]
        ineligible_sources = self._ineligible_sources(selector=selector, catalog_entries=catalog_entries)
        eligible_entry_count = sum(
            1
            for entry in catalog_entries
            if selector._is_runtime_eligible_entry(entry=entry)  # noqa: SLF001 - read-only audit mirror.
        )
        selected_violations = [
            source.reason_code
            for source in selected_sources
            if source.path and source.governance_status != "accepted"
        ]
        policy_respected = catalog_error == "" and not selected_violations
        source_status_distribution = Counter(source.governance_status for source in selected_sources)
        source_mix = Counter(source.source_type for source in selected_sources if source.source_type)
        coverage_limitations = self._coverage_limitations(
            catalog_available=not catalog_error,
            catalog_entries=catalog_entries,
            eligible_entry_count=eligible_entry_count,
            local_assets_available=local_assets_available,
            fallback=fallback,
            selected_sources=selected_sources,
        )

        fallback_sources: list[dict[str, Any]] = []
        if fallback.used:
            fallback_sources.append(
                {
                    "mode": fallback.mode,
                    "reason": fallback.reason,
                    "source_class": "safe_default" if not any(source.path for source in selected_sources) else "local_fallback",
                    "rationale": "Asset Selection fallback was reported by the existing fallback decision.",
                }
            )

        return AssetCatalogSourceGovernanceResult(
            policy_version=ASSET_SOURCE_POLICY_VERSION,
            policy_respected=policy_respected,
            catalog_available=not catalog_error,
            catalog_path=str(selector.catalog_path),
            catalog_entry_count=len(catalog_entries),
            eligible_entry_count=eligible_entry_count,
            source_policy={
                "policy": ASSET_SOURCE_POLICY_VERSION,
                "allowed_source_types": sorted(selector.ALLOWED_RUNTIME_SOURCES),
                "requires_catalog_entry": True,
                "requires_runtime_eligible_entry": True,
                "forbidden_source_types": ["local_curated", "unknown", "unregistered_external"],
                "external_collection_allowed": False,
                "ranking_change_allowed": False,
                "fallback_change_allowed": False,
            },
            selected_sources=selected_sources,
            ineligible_sources=ineligible_sources,
            fallback_sources=fallback_sources,
            source_status_distribution=dict(sorted(source_status_distribution.items())),
            source_mix=dict(sorted(source_mix.items())),
            coverage_limitations=coverage_limitations,
            governance_trace={
                "catalog_error": catalog_error,
                "local_assets_available": local_assets_available,
                "selected_violation_reason_codes": selected_violations,
                "read_only": True,
                "selection_ranking_unchanged": True,
                "fallback_behavior_unchanged": True,
            },
        )

    def _load_catalog(self, selector: AssetSelector) -> tuple[list[CatalogEntry], str]:
        try:
            if not Path(selector.catalog_path).exists():
                return [], "CATALOG_FILE_MISSING"
            return selector._load_catalog(), ""  # noqa: SLF001 - read-only audit mirror.
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return [], f"CATALOG_LOAD_FAILED:{exc.__class__.__name__}"

    def _selected_source(
        self,
        *,
        segment: str,
        path: str,
        selector: AssetSelector,
        entry_by_path: dict[str, CatalogEntry],
        fallback: FallbackDecision,
    ) -> AssetSelectedSource:
        normalized = self._normalize_path(path)
        if not normalized:
            return AssetSelectedSource(
                segment=segment,
                path="",
                source_type="",
                source_class="safe_default" if fallback.used else "missing_asset",
                catalog_present=False,
                eligible_for_runtime=False,
                governance_status="fallback" if fallback.used else "missing",
                reason_code="SELECTED_SOURCE_EMPTY_FALLBACK" if fallback.used else "SELECTED_SOURCE_EMPTY",
                rationale=(
                    "No concrete asset path was emitted because Asset Selection returned fallback."
                    if fallback.used
                    else "No concrete asset path was emitted for this segment."
                ),
            )

        entry = entry_by_path.get(normalized)
        if entry is None:
            return AssetSelectedSource(
                segment=segment,
                path=path,
                source_type="unknown",
                source_class="unregistered_local_path",
                catalog_present=False,
                eligible_for_runtime=False,
                governance_status="rejected",
                reason_code="SELECTED_SOURCE_NOT_IN_CATALOG",
                rationale="Selected asset path is not present in the governed local catalog.",
            )

        eligible = selector._is_runtime_eligible_entry(entry=entry)  # noqa: SLF001 - read-only audit mirror.
        if eligible:
            return AssetSelectedSource(
                segment=segment,
                path=entry.path,
                source_type=entry.source_type,
                source_class="local_catalog_asset",
                catalog_present=True,
                eligible_for_runtime=True,
                governance_status="accepted",
                reason_code="SELECTED_SOURCE_ACCEPTED_LOCAL_CATALOG",
                rationale="Selected asset is present in the local catalog and runtime eligible.",
                metadata=self._entry_metadata(entry),
            )
        return AssetSelectedSource(
            segment=segment,
            path=entry.path,
            source_type=entry.source_type,
            source_class="local_catalog_asset",
            catalog_present=True,
            eligible_for_runtime=False,
            governance_status="rejected",
            reason_code=self._ineligible_reason(selector=selector, entry=entry),
            rationale="Selected asset is cataloged but not runtime eligible under local_catalog_only_v2_6.",
            metadata=self._entry_metadata(entry),
        )

    def _entry_metadata(self, entry: CatalogEntry) -> dict[str, Any]:
        return {
            "category": entry.category,
            "family": entry.family,
            "framing": entry.framing,
            "phase1_legacy": entry.phase1_legacy,
            "eligible_for_runtime": entry.eligible_for_runtime,
            "resolution": list(entry.resolution),
        }

    def _ineligible_sources(
        self,
        *,
        selector: AssetSelector,
        catalog_entries: list[CatalogEntry],
    ) -> list[AssetIneligibleSourceSummary]:
        grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
        for entry in catalog_entries:
            if selector._is_runtime_eligible_entry(entry=entry):  # noqa: SLF001 - read-only audit mirror.
                continue
            reason_code = self._ineligible_reason(selector=selector, entry=entry)
            grouped[(entry.source_type, reason_code)].append(entry.path)

        summaries = []
        for (source_type, reason_code), paths in sorted(grouped.items()):
            sample_paths = sorted(paths)[:5]
            summaries.append(
                AssetIneligibleSourceSummary(
                    source_type=source_type,
                    reason_code=reason_code,
                    count=len(paths),
                    sample_paths=sample_paths,
                    rationale=self._ineligible_rationale(reason_code),
                )
            )
        return summaries

    def _ineligible_reason(self, *, selector: AssetSelector, entry: CatalogEntry) -> str:
        if entry.source_type.strip().lower() == "local_curated":
            return "SOURCE_REJECTED_LOCAL_CURATED_RUNTIME_DISABLED"
        if entry.source_type.strip().lower() not in selector.ALLOWED_RUNTIME_SOURCES:
            return "SOURCE_REJECTED_UNSUPPORTED_SOURCE_TYPE"
        if entry.phase1_legacy or self._normalize_path(entry.path) in {
            self._normalize_path(path)
            for path in selector.RETIRED_PHASE1_PATHS
        }:
            return "SOURCE_REJECTED_PHASE1_LEGACY"
        if not entry.eligible_for_runtime:
            return "SOURCE_REJECTED_NOT_RUNTIME_ELIGIBLE"
        return "SOURCE_REJECTED_SELECTOR_POLICY"

    def _ineligible_rationale(self, reason_code: str) -> str:
        return {
            "SOURCE_REJECTED_LOCAL_CURATED_RUNTIME_DISABLED": "Legacy local curated assets remain visible in the catalog but are not runtime-eligible.",
            "SOURCE_REJECTED_UNSUPPORTED_SOURCE_TYPE": "Source type is outside the explicit local catalog runtime policy.",
            "SOURCE_REJECTED_PHASE1_LEGACY": "Phase 1 legacy or retired path is excluded from runtime selection.",
            "SOURCE_REJECTED_NOT_RUNTIME_ELIGIBLE": "Catalog entry is marked not eligible for runtime.",
            "SOURCE_REJECTED_SELECTOR_POLICY": "Catalog entry failed the existing selector runtime eligibility policy.",
        }.get(reason_code, "Catalog entry is not eligible under local_catalog_only_v2_6.")

    def _coverage_limitations(
        self,
        *,
        catalog_available: bool,
        catalog_entries: list[CatalogEntry],
        eligible_entry_count: int,
        local_assets_available: bool,
        fallback: FallbackDecision,
        selected_sources: list[AssetSelectedSource],
    ) -> list[str]:
        limitations: list[str] = []
        if not catalog_available:
            limitations.append("ASSET_CATALOG_NOT_AVAILABLE")
        if catalog_entries and eligible_entry_count < len(catalog_entries):
            limitations.append("CATALOG_CONTAINS_INELIGIBLE_LEGACY_OR_UNSUPPORTED_SOURCES")
        if not local_assets_available:
            limitations.append("LOCAL_ASSET_FILES_NOT_AVAILABLE")
        if fallback.used:
            limitations.append("ASSET_SELECTION_FALLBACK_REPORTED")
        if any(source.governance_status in {"missing", "fallback"} for source in selected_sources):
            limitations.append("SEGMENT_SOURCE_PATH_NOT_FULLY_OBSERVABLE")
        if not limitations:
            limitations.append("NO_CATALOG_SOURCE_LIMITATIONS_DETECTED")
        return limitations

    def _normalize_path(self, path: str) -> str:
        return str(path or "").replace("\\", "/").strip().lower()
