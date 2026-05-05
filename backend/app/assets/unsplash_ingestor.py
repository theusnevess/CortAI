from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

import httpx

from app.assets.ingestion_common import download_bytes, normalize_and_store, resolve_og_image
from app.assets.catalog_registry import ROOT

API_URL = 'https://api.unsplash.com/search/photos'


SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED = False
SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED = False
SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED = False
SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED = False


def _ensure_unsplash_external_boundary_authorized() -> None:
    if not SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED:
        raise RuntimeError('CORTAI_EXTERNAL_BOUNDARY_BLOCKED_SAFE_PRE_CROSSING')
    if not SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED:
        raise RuntimeError('CORTAI_CREDENTIAL_ACCESS_BLOCKED_SAFE_PRE_CROSSING')
    if not SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED:
        raise RuntimeError('CORTAI_REQUEST_TRANSFORMATION_BLOCKED_SAFE_PRE_CROSSING')
    if not SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED:
        raise RuntimeError('CORTAI_TRANSPORT_PAYLOAD_BLOCKED_SAFE_PRE_CROSSING')


@dataclass
class UnsplashIngestor:
    access_key: str = ''
    imports_root: Path = ROOT / 'assets' / 'imports'

    def __post_init__(self) -> None:
        if not self.access_key:
            if not SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED:
                return
            self.access_key = os.getenv('UNSPLASH_ACCESS_KEY', '').strip()

    def search(self, *, query: str, per_page: int = 20) -> list[dict]:
        _ensure_unsplash_external_boundary_authorized()
        if not self.access_key:
            raise RuntimeError('UNSPLASH_ACCESS_KEY missing')
        headers = {'Authorization': f'Client-ID {self.access_key}'}
        with httpx.Client(timeout=60.0, headers=headers) as client:
            response = client.get(API_URL, params={'query': query, 'per_page': per_page, 'orientation': 'portrait'})
            response.raise_for_status()
            data = response.json()
        return list(data.get('results', []))

    def ingest_query(self, *, query: str, category: str, subtype: str, tags: list[str], limit: int = 3, metadata: dict | None = None) -> list[dict]:
        _ensure_unsplash_external_boundary_authorized()
        rows = self.search(query=query, per_page=max(limit, 10))
        ingested = []
        for index, row in enumerate(rows[:limit], start=1):
            image_url = str(row.get('urls', {}).get('raw') or row.get('urls', {}).get('full') or row.get('urls', {}).get('regular'))
            if not image_url:
                continue
            content = download_bytes(image_url)
            ingested.append(normalize_and_store(
                image_bytes=content,
                source_type='unsplash',
                category=category,
                subtype=subtype,
                asset_name=f"unsplash_{query}_{index}",
                tags=tags,
                dest_root=self.imports_root,
                metadata=metadata or {},
            ))
        return ingested

    def ingest_page(self, *, page_url: str, category: str, subtype: str, tags: list[str], asset_name: str, metadata: dict | None = None) -> dict:
        _ensure_unsplash_external_boundary_authorized()
        image_url = resolve_og_image(page_url)
        content = download_bytes(image_url)
        return normalize_and_store(
            image_bytes=content,
            source_type='unsplash',
            category=category,
            subtype=subtype,
            asset_name=asset_name,
            tags=tags,
            dest_root=self.imports_root,
            metadata=metadata or {},
        )
