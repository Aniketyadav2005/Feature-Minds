"""
GET/DELETE endpoints for browsing and managing analysis history.
"""
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.database import get_db
from app.features.history import service
from app.features.serializers import to_out
from app.schemas.analysis import (
    AnalysisResultOut, HistoryStatsOut, ClearHistoryResponse,
)

router = APIRouter(prefix="/api/history", tags=["history"])

# @router.get("", response_model=List[AnalysisResultOut])
# def get_history(
#     filter_opt: Literal["all", "hate", "safe"] = Query("all", alias="filter"),
#     limit: int = Query(200, le=500),
#     offset: int = 0,
#     db: Session = Depends(get_db),
# ):
#     records = service.list_history(db, filter_opt, limit, offset)
#     return [to_out(r) for r in records]

@router.get("", response_model=List[AnalysisResultOut])
def get_history(
    filter_opt: Literal["all", "hate", "safe"] = Query(
        "all",
        alias="filter",
    ),
    limit: int = Query(200, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = service.list_history(
        db,
        filter_opt,
        limit,
        offset,
        current_user.id,
    )

    return [to_out(r) for r in records]


@router.get("/stats", response_model=HistoryStatsOut)
def get_history_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_stats(db, current_user.id)


@router.delete("/{analysis_id}")
def delete_history_item(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = service.delete_one(
        db,
        analysis_id,
        current_user.id,
    )

    if not ok:
        raise HTTPException(404, "Analysis result not found.")

    return {"deleted": analysis_id}


@router.delete("", response_model=ClearHistoryResponse)
def clear_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = service.clear_all(
        db,
        current_user.id,
    )

    return ClearHistoryResponse(deleted=count)