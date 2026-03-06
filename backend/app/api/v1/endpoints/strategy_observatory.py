from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.v1.schemas.strategy_observatory import (
    StrategyImpactResponse,
    StrategyObservatoryErrorResponse,
    StrategyPatchDetailResponse,
    StrategyPatchesResponse,
    StrategyTimelineResponse,
)
from app.ops.strategy_observatory.service import StrategyObservatoryNotFoundError, StrategyObservatoryService

router = APIRouter()


def _service() -> StrategyObservatoryService:
    base_dir = Path(os.getenv("OPS_DASHBOARD_BASE_DIR") or os.getenv("CORTAI_OUT_DIR") or "OUT")
    return StrategyObservatoryService(base_dir=base_dir)


@router.get("/patches", response_model=StrategyPatchesResponse)
def get_strategy_patches(account_id: str | None = None, policy_stage: str | None = None, limit: int = 100):
    return {"items": _service().list_patches(account_id=account_id, policy_stage=policy_stage, limit=limit)}


@router.get(
    "/patch/{patch_id}",
    response_model=StrategyPatchDetailResponse,
    responses={404: {"model": StrategyObservatoryErrorResponse}},
)
def get_strategy_patch_detail(patch_id: str):
    try:
        return {"item": _service().get_patch(patch_id)}
    except StrategyObservatoryNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "STRATEGY_PATCH_NOT_FOUND", "message": "Strategy patch not found.", "details": {"patch_id": patch_id}}},
        )


@router.get("/impact", response_model=StrategyImpactResponse)
def get_strategy_impact(account_id: str | None = None, limit: int = 100):
    return {"items": _service().list_impact(account_id=account_id, limit=limit)}


@router.get("/timeline", response_model=StrategyTimelineResponse)
def get_strategy_timeline(account_id: str | None = None, limit: int = 100):
    return {"items": _service().list_timeline(account_id=account_id, limit=limit)}
