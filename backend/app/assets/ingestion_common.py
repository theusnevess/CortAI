from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
import re

import httpx
from PIL import Image

from app.assets.catalog_registry import CatalogAssetEntry, ROOT, upsert_catalog_entries

TARGET_SIZE = (1080, 1920)
MIN_EDGE = 1080
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}


@dataclass(frozen=True)
class IngestedAsset:
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
    setup_specificity_score: float = 0.6
    genericity: float = 0.15
    strength: float = 0.85
    freshness_score: float = 1.0
    prompt: str = ''
    seed: str = ''

    def to_catalog_entry(self) -> dict[str, Any]:
        return CatalogAssetEntry(
            path=self.path,
            source_type=self.source_type,
            category=self.category,
            subtype=self.subtype,
            tags=self.tags,
            resolution=self.resolution,
            hook_strength_score=self.hook_strength_score,
            payoff_strength_score=self.payoff_strength_score,
            realism_score=self.realism_score,
            usage_count=self.usage_count,
            family=self.family or self.category,
            framing=self.framing,
            mood=self.mood,
            semantic_pattern_fit=self.semantic_pattern_fit or [],
            entity_fit=self.entity_fit or [],
            setup_specificity_score=self.setup_specificity_score,
            genericity=self.genericity,
            strength=self.strength,
            freshness_score=self.freshness_score,
            prompt=self.prompt,
            seed=self.seed,
        ).to_dict()


def _slug(value: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9]+', '_', value.strip().lower())
    return re.sub(r'_+', '_', text).strip('_') or 'asset'


def _resize_cover(image: Image.Image, target: tuple[int, int] = TARGET_SIZE) -> Image.Image:
    target_w, target_h = target
    source_w, source_h = image.size
    scale = max(target_w / source_w, target_h / source_h)
    resized = image.resize((int(source_w * scale), int(source_h * scale)))
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def normalize_and_store(*, image_bytes: bytes, source_type: str, category: str, subtype: str, asset_name: str, tags: list[str], dest_root: Path, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    metadata = metadata or {}
    with Image.open(BytesIO(image_bytes)) as image:
        rgb = image.convert('RGB')
        if min(rgb.size) < MIN_EDGE:
            raise ValueError(f'asset too small: {rgb.size}')
        normalized = _resize_cover(rgb)
    target_dir = dest_root / source_type / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{_slug(asset_name)}.jpg"
    normalized.save(target, format='JPEG', quality=92)
    try:
        rel = str(target.relative_to(ROOT)).replace('\\', '/')
    except ValueError:
        rel = str(target.resolve()).replace('\\', '/')
    entry = IngestedAsset(
        path=rel,
        source_type=source_type,
        category=category,
        subtype=subtype,
        tags=tags,
        resolution=[TARGET_SIZE[0], TARGET_SIZE[1]],
        hook_strength_score=float(metadata.get('hook_strength_score', 0.78)),
        payoff_strength_score=float(metadata.get('payoff_strength_score', 0.8)),
        realism_score=float(metadata.get('realism_score', 0.96)),
        family=str(metadata.get('family', category)),
        framing=str(metadata.get('framing', 'medium')),
        mood=str(metadata.get('mood', 'neutral')),
        semantic_pattern_fit=list(metadata.get('semantic_pattern_fit', [])),
        entity_fit=list(metadata.get('entity_fit', [])),
        setup_specificity_score=float(metadata.get('setup_specificity_score', 0.75)),
        genericity=float(metadata.get('genericity', 0.12)),
        strength=float(metadata.get('strength', 0.88)),
        freshness_score=float(metadata.get('freshness_score', 1.0)),
        prompt=str(metadata.get('prompt', '')),
        seed=str(metadata.get('seed', '')),
    ).to_catalog_entry()
    upsert_catalog_entries([entry])
    return entry


def download_bytes(url: str, *, headers: dict[str, str] | None = None, timeout: float = 120.0) -> bytes:
    merged_headers = dict(DEFAULT_HEADERS)
    if headers:
        merged_headers.update(headers)
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=merged_headers) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.content


def resolve_og_image(page_url: str, *, timeout: float = 60.0, headers: dict[str, str] | None = None) -> str:
    merged_headers = dict(DEFAULT_HEADERS)
    if headers:
        merged_headers.update(headers)
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=merged_headers) as client:
        response = client.get(page_url)
        response.raise_for_status()
        html = response.text
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    raise ValueError(f'could not resolve og:image for {page_url}')
