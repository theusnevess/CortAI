"""Legacy analytical attribution path.

Phase A boundary:
- `app.attribution` is not the canonical product attribution root.
- It may remain for descriptive analytics and support studies.
- New product/runtime attribution ownership should live under `app.product.attribution`.
"""

from app.attribution.models import DurationAnalysis, HookPerformance, PatternPerformance, StructurePerformance
from app.attribution.service import AdvancedAttributionService

__all__ = [
    "AdvancedAttributionService",
    "DurationAnalysis",
    "HookPerformance",
    "PatternPerformance",
    "StructurePerformance",
]
