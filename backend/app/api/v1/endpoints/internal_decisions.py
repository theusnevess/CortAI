from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.observability.decision_history import get_decision_history_item, list_decision_history
from app.observability.runtime_health import should_include_internal_status

router = APIRouter(prefix="/internal", tags=["internal"])


def _no_store_json(content: dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=content, status_code=status_code, headers={"Cache-Control": "no-store"})


@router.get("/decisions")
async def list_internal_decisions(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    since_ts: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not should_include_internal_status(request):
        raise HTTPException(status_code=404, detail="NotFound")

    items = await list_decision_history(
        db,
        limit=limit,
        since_ts=since_ts,
        state=state,
    )
    return _no_store_json({"version": "v1", "items": items, "next": None})


@router.get("/decisions/{decision_id}")
async def get_internal_decision(
    decision_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if not should_include_internal_status(request):
        raise HTTPException(status_code=404, detail="NotFound")

    item = await get_decision_history_item(db, decision_id=decision_id)
    if item is None:
        raise HTTPException(status_code=404, detail="NotFound")
    return _no_store_json(item)
