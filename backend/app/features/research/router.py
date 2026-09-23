"""
Endpoints for ground-truth labelling and computed research metrics.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.database import get_db
from app.features.research import service
from app.schemas.analysis import GroundTruthIn, MetricsOut

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/ground-truth")
def set_ground_truth(
    payload: GroundTruthIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        gt = service.upsert_ground_truth(
            db,
            payload.analysis_id,
            payload.label,
            current_user.id,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

    return {
        "analysis_id": gt.analysis_id,
        "label": gt.label,
    }


@router.get("/metrics", response_model=MetricsOut | None)
def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.compute_metrics(
        db,
        current_user.id,
    )
