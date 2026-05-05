from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

import httpx

from app.assets.ingestion_common import download_bytes, normalize_and_store, resolve_og_image
from app.assets.catalog_registry import ROOT

API_URL = 'https://api.pexels.com/v1/search'


SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED = False
SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED = False
SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED = False
SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED = False


def _ensure_pexels_external_boundary_authorized() -> None:
    if not SAFE_PRE_CROSSING_EXTERNAL_CALL_AUTHORIZED:
        raise RuntimeError('CORTAI_EXTERNAL_BOUNDARY_BLOCKED_SAFE_PRE_CROSSING')
    if not SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED:
        raise RuntimeError('CORTAI_CREDENTIAL_ACCESS_BLOCKED_SAFE_PRE_CROSSING')
    if not SAFE_PRE_CROSSING_REQUEST_TRANSFORMATION_AUTHORIZED:
        raise RuntimeError('CORTAI_REQUEST_TRANSFORMATION_BLOCKED_SAFE_PRE_CROSSING')
    if not SAFE_PRE_CROSSING_TRANSPORT_PAYLOAD_AUTHORIZED:
        raise RuntimeError('CORTAI_TRANSPORT_PAYLOAD_BLOCKED_SAFE_PRE_CROSSING')


@dataclass
class PexelsIngestor:
    api_key: str = ''
    imports_root: Path = ROOT / 'assets' / 'imports'

    def __post_init__(self) -> None:
        if not self.api_key:
            if not SAFE_PRE_CROSSING_CREDENTIAL_ACCESS_AUTHORIZED:
                return
            self.api_key = os.getenv('PEXELS_API_KEY', '').strip()

    def search(self, *, query: str, per_page: int = 20) -> list[dict]:
        _ensure_pexels_external_boundary_authorized()
        if not self.api_key:
            raise RuntimeError('PEXELS_API_KEY missing')
        headers = {'Authorization': self.api_key}
        with httpx.Client(timeout=60.0, headers=headers) as client:
            response = client.get(API_URL, params={'query': query, 'per_page': per_page})
            response.raise_for_status()
            data = response.json()
        return list(data.get('photos', []))

    def ingest_query(self, *, query: str, category: str, subtype: str, tags: list[str], limit: int = 3, metadata: dict | None = None) -> list[dict]:
        _ensure_pexels_external_boundary_authorized()
        rows = self.search(query=query, per_page=max(limit, 10))
        ingested = []
        for index, row in enumerate(rows[:limit], start=1):
            image_url = str(row.get('src', {}).get('original') or row.get('src', {}).get('large2x') or row.get('src', {}).get('large'))
            if not image_url:
                continue
            content = download_bytes(image_url, headers={'Authorization': self.api_key})
            ingested.append(normalize_and_store(
                image_bytes=content,
                source_type='pexels',
                category=category,
                subtype=subtype,
                asset_name=f"pexels_{query}_{index}",
                tags=tags,
                dest_root=self.imports_root,
                metadata=metadata or {},
            ))
        return ingested

    def ingest_page(self, *, page_url: str, category: str, subtype: str, tags: list[str], asset_name: str, metadata: dict | None = None) -> dict:
        _ensure_pexels_external_boundary_authorized()
        image_url = resolve_og_image(page_url)
        content = download_bytes(image_url)
        return normalize_and_store(
            image_bytes=content,
            source_type='pexels',
            category=category,
            subtype=subtype,
            asset_name=asset_name,
            tags=tags,
            dest_root=self.imports_root,
            metadata=metadata or {},
        )
