"""Canonical root for the Content Performance Attribution subsystem.

Phase A boundary:
- `app.product.attribution` is the canonical product-grade attribution path.
- New product/runtime references should anchor here.
- `app.attribution` remains available only as a legacy analytical path.
"""

from app.product.attribution.builder import (
    AttributionDeps,
    EXPERIMENT_LINKAGE_STATUS,
    OPTIONAL_EVIDENCE_INPUTS,
    REQUIRED_EVIDENCE_INPUTS,
    build_attribution,
    build_evidence_summary,
    build_experiment_linkage,
)
from app.product.attribution.repo import get_by_publish_id, save_if_absent
from app.product.attribution.schema import (
    AttributionValidationError,
    OPTIONAL_ENRICHMENT_FIELDS,
    REQUIRED_BASE_FIELDS,
    validate_content_attribution,
)
from app.product.attribution.service import generate_and_save_attribution
from app.product.attribution.store_jsonl import DEFAULT_CONTENT_ATTRIBUTION_PATH, read_all_attributions

__all__ = [
    "AttributionDeps",
    "AttributionValidationError",
    "DEFAULT_CONTENT_ATTRIBUTION_PATH",
    "EXPERIMENT_LINKAGE_STATUS",
    "OPTIONAL_ENRICHMENT_FIELDS",
    "OPTIONAL_EVIDENCE_INPUTS",
    "REQUIRED_BASE_FIELDS",
    "REQUIRED_EVIDENCE_INPUTS",
    "build_attribution",
    "build_evidence_summary",
    "build_experiment_linkage",
    "generate_and_save_attribution",
    "get_by_publish_id",
    "read_all_attributions",
    "save_if_absent",
    "validate_content_attribution",
]
