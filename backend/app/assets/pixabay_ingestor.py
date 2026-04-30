from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

import httpx

from app.assets.ingestion_common import download_bytes, normalize_and_store, resolve_og_image
from app.assets.catalog_registry import ROOT

API_URL = 'https://pixabay.com/api/'


@dataclass
class PixabayIngestor:
    api_key: str = ''
    imports_root: Path = ROOT / 'assets' / 'imports'

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.getenv('PIXABAY_API_KEY', '').strip()

    def search(self, *, query: str, per_page: int = 20) -> list[dict]:
        if not self.api_key:
            raise RuntimeError('PIXABAY_API_KEY missing')
        with httpx.Client(timeout=60.0) as client:
            response = client.get(API_URL, params={'key': self.api_key, 'q': query, 'per_page': per_page, 'image_type': 'photo', 'orientation': 'vertical'})
            response.raise_for_status()
            data = response.json()
        return list(data.get('hits', []))

    def ingest_query(self, *, query: str, category: str, subtype: str, tags: list[str], limit: int = 3, metadata: dict | None = None) -> list[dict]:
        rows = self.search(query=query, per_page=max(limit, 10))
        ingested = []
        for index, row in enumerate(rows[:limit], start=1):
            image_url = str(row.get('largeImageURL') or row.get('webformatURL'))
            if not image_url:
                continue
            content = download_bytes(image_url)
            ingested.append(normalize_and_store(
                image_bytes=content,
                source_type='pixabay',
                category=category,
                subtype=subtype,
                asset_name=f"pixabay_{query}_{index}",
                tags=tags,
                dest_root=self.imports_root,
                metadata=metadata or {},
            ))
        return ingested

    def ingest_page(self, *, page_url: str, category: str, subtype: str, tags: list[str], asset_name: str, metadata: dict | None = None) -> dict:
        image_url = resolve_og_image(page_url)
        content = download_bytes(image_url)
        return normalize_and_store(
            image_bytes=content,
            source_type='pixabay',
            category=category,
            subtype=subtype,
            asset_name=asset_name,
            tags=tags,
            dest_root=self.imports_root,
            metadata=metadata or {},
        )
