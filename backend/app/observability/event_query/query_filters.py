from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any

from app.observability.event_query.models import EventQueryFilters


def canonicalize_filters(filters: EventQueryFilters | dict[str, Any]) -> dict[str, Any]:
    """Normaliza filtros para payload canonico e estavel."""
    if isinstance(filters, EventQueryFilters):
        source = asdict(filters)
    elif is_dataclass(filters):
        source = asdict(filters)
    elif isinstance(filters, dict):
        source = dict(filters)
    else:
        raise TypeError("filters must be EventQueryFilters or dict")

    source.pop("limit", None)
    source.pop("cursor", None)

    start = source.pop("start_ts", None)
    end = source.pop("end_ts", None)
    canonical: dict[str, Any] = {}

    if start is not None or end is not None:
        canonical["time_range"] = {
            "start": _canonicalize_value(start),
            "end": _canonicalize_value(end),
        }

    for key in sorted(source.keys()):
        value = _canonicalize_value(source[key])
        if value is None:
            continue
        canonical[key] = value

    return canonical


def compute_filters_hash(canonical: dict[str, Any]) -> str:
    """Calcula hash SHA-256 do payload canonico de filtros."""
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def build_filters_hash(filters: EventQueryFilters | dict[str, Any]) -> str:
    """Helper para gerar hash estavel diretamente dos filtros de entrada."""
    return compute_filters_hash(canonicalize_filters(filters))


def _canonicalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
        return normalized if normalized else None
    if isinstance(value, list):
        canonical_items = [_canonicalize_value(item) for item in value]
        canonical_items = [item for item in canonical_items if item is not None]
        canonical_items.sort(key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")))
        return canonical_items
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key in sorted(value.keys()):
            item = _canonicalize_value(value[key])
            if item is None:
                continue
            result[str(key)] = item
        return result
    return value
