from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = Path(__file__).resolve().parent / 'catalog.json'
ALLOWED_RUNTIME_SOURCES = {"pexels", "unsplash", "pixabay", "comfyui"}


@dataclass(frozen=True)
class CatalogAssetEntry:
    path: str
    source_type: str
    category: str
    subtype: str
    tags: list[str]
    resolution: list[int]
    hook_strength_score: float
    payoff_strength_score: float
    realism_score: float
    usage_count: int = 0
    family: str = ''
    framing: str = 'medium'
    mood: str = 'neutral'
    semantic_pattern_fit: list[str] | None = None
    entity_fit: list[str] | None = None
    setup_specificity_score: float = 0.5
    genericity: float = 0.2
    strength: float = 0.8
    freshness_score: float = 0.5
    prompt: str = ''
    seed: str = ''
    ingested_at: str = ''
    phase1_legacy: bool = False
    eligible_for_runtime: bool = False

    def _runtime_eligibility(self) -> bool:
        source = self.source_type.strip().lower()
        return source in ALLOWED_RUNTIME_SOURCES and not self.phase1_legacy and source != "local_curated"

    def to_dict(self) -> dict[str, Any]:
        return {
            'path': self.path,
            'source_type': self.source_type,
            'category': self.category,
            'subtype': self.subtype,
            'tags': self.tags,
            'resolution': self.resolution,
            'hook_strength_score': self.hook_strength_score,
            'payoff_strength_score': self.payoff_strength_score,
            'realism_score': self.realism_score,
            'usage_count': self.usage_count,
            'family': self.family or self.category,
            'framing': self.framing,
            'mood': self.mood,
            'semantic_pattern_fit': self.semantic_pattern_fit or [],
            'entity_fit': self.entity_fit or [],
            'setup_specificity_score': self.setup_specificity_score,
            'genericity': self.genericity,
            'strength': self.strength,
            'freshness_score': self.freshness_score,
            'prompt': self.prompt,
            'seed': self.seed,
            'ingested_at': self.ingested_at or datetime.now(timezone.utc).isoformat(),
            'phase1_legacy': self.phase1_legacy,
            'eligible_for_runtime': self.eligible_for_runtime or self._runtime_eligibility(),
        }


def _normalize_runtime_eligibility(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(entry)
    source = str(normalized.get('source_type', 'local_curated')).strip().lower()
    normalized['source_type'] = source
    phase1_legacy = bool(normalized.get('phase1_legacy', False))
    normalized['phase1_legacy'] = phase1_legacy
    normalized['eligible_for_runtime'] = bool(
        normalized.get('eligible_for_runtime', source in ALLOWED_RUNTIME_SOURCES and not phase1_legacy and source != "local_curated")
    )
    return normalized


def load_catalog(path: Path = CATALOG_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = json.loads(path.read_text(encoding='utf-8'))
    return [_normalize_runtime_eligibility(item) for item in rows]


def save_catalog(entries: list[dict[str, Any]], path: Path = CATALOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = sorted((_normalize_runtime_eligibility(item) for item in entries), key=lambda item: str(item.get('path', '')))
    path.write_text(json.dumps(normalized, indent=2), encoding='utf-8')


def upsert_catalog_entries(entries: list[dict[str, Any]], path: Path = CATALOG_PATH) -> list[dict[str, Any]]:
    current = {str(item.get('path', '')): item for item in load_catalog(path)}
    for entry in entries:
        existing = current.get(entry['path'])
        if existing:
            usage_count = int(existing.get('usage_count', 0))
            merged = dict(existing)
            merged.update(entry)
            merged['usage_count'] = int(entry.get('usage_count', usage_count))
            current[entry['path']] = merged
        else:
            current[entry['path']] = dict(entry)
    result = list(current.values())
    save_catalog(result, path)
    return result


def increment_usage_counts(paths: list[str], path: Path = CATALOG_PATH) -> list[dict[str, Any]]:
    if not paths:
        return load_catalog(path)
    current = {str(item.get('path', '')): item for item in load_catalog(path)}
    for asset_path in paths:
        key = str(asset_path or '')
        if not key or key not in current:
            continue
        entry = dict(current[key])
        entry['usage_count'] = int(entry.get('usage_count', 0)) + 1
        current[key] = entry
    result = list(current.values())
    save_catalog(result, path)
    return result
