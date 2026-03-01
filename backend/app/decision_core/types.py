from __future__ import annotations

from typing import Any, TypedDict


class CollectorEvents(TypedDict, total=False):
    success: int
    failed: int


class CollectorSummary(TypedDict, total=False):
    window_minutes: int
    events: CollectorEvents
    by_error_type: dict[str, int]
    last_events: list[dict[str, Any]]


class PolicyDecision(TypedDict, total=False):
    version: str
    score: int
    state: str
    decision: str
    signals: list[str] | dict[str, Any]
    trust_score: int
    system_state: str
    recommendation: str
    as_of: str


class TrustBlock(TypedDict, total=False):
    state: str
    decision: str
    message: str
    derived_from: list[str]


class RecommendationBlock(TypedDict, total=False):
    action: str
    priority: str
    message: str
    derived_from: list[str]
