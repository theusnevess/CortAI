from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StrategyPatchItem(BaseModel):
    patch_id: str
    account_id: str
    window_id: str
    policy_stage: str
    reason_code: str | None = None
    created_at: str
    status: str


class StrategyPatchDetail(StrategyPatchItem):
    reason_codes: list[str] = Field(default_factory=list)
    layers_applied: list[str] = Field(default_factory=list)
    overrides: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    application: dict[str, Any] | None = None


class StrategyPatchesResponse(BaseModel):
    items: list[StrategyPatchItem] = Field(default_factory=list)


class StrategyPatchDetailResponse(BaseModel):
    item: StrategyPatchDetail


class StrategyImpactItem(BaseModel):
    patch_id: str
    account_id: str
    policy_stage: str
    status: str
    window_id_before: str
    window_id_after: str | None = None
    scorecard_delta: dict[str, float | None] = Field(default_factory=dict)


class StrategyImpactResponse(BaseModel):
    items: list[StrategyImpactItem] = Field(default_factory=list)


class StrategyTimelineItem(BaseModel):
    patch_id: str
    account_id: str
    window_id: str
    policy_stage: str
    status: str
    reason_code: str | None = None
    created_at: str


class StrategyTimelineResponse(BaseModel):
    items: list[StrategyTimelineItem] = Field(default_factory=list)


class StrategyObservatoryErrorResponse(BaseModel):
    error: dict[str, Any]
