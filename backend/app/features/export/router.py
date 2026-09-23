"""
PDF export endpoints.

1. GET /api/export/pdf/history
   Export all history belonging to the logged-in user.

2. POST /api/export/pdf/batch
   Export only the analysis records supplied by the current
   Home-page analysis batch.

3. GET /api/export/pdf/{analysis_id}
   Export one analysis belonging to the logged-in user.
"""

import datetime as dt
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.features.export.service import (
    export_pdf,
    export_single_pdf,
)
from app.features.history.service import list_history
from app.models.analysis import AnalysisResult
from app.models.user import User


router = APIRouter(
    prefix="/api/export",
    tags=["export"],
)


# =========================================================
# REQUEST MODEL — CURRENT HOME BATCH
# =========================================================

class BatchExportRequest(BaseModel):
    analysis_ids: list[int] = Field(
        ...,
        min_length=1,
        max_length=20,
    )


# =========================================================
# HISTORY PDF
# IMPORTANT:
# Keep this BEFORE /pdf/{analysis_id}
# =========================================================

@router.get("/pdf/history")
def export_history_pdf_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    records = list_history(
        db,
        "all",
        limit=10_000,
        user_id=current_user.id,
    )

    if not records:
        raise HTTPException(
            status_code=404,
            detail="No analysis history found.",
        )

    data = export_pdf(records)

    timestamp = dt.datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="meme_history_{timestamp}.pdf"'
            )
        },
    )


# =========================================================
# CURRENT HOME-PAGE BATCH PDF
# =========================================================

@router.post("/pdf/batch")
def export_batch_pdf_endpoint(
    payload: BatchExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Remove duplicate IDs while preserving order.
    requested_ids = list(
        dict.fromkeys(payload.analysis_ids)
    )

    if not requested_ids:
        raise HTTPException(
            status_code=400,
            detail="No analysis IDs were provided.",
        )

    # IMPORTANT:
    # Only fetch records belonging to the logged-in user.
    records = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.id.in_(requested_ids),
            AnalysisResult.user_id == current_user.id,
        )
        .all()
    )

    # Security check:
    # If even one requested ID does not belong to the user,
    # do not generate a partial report.
    found_ids = {record.id for record in records}

    missing_ids = [
        analysis_id
        for analysis_id in requested_ids
        if analysis_id not in found_ids
    ]

    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=(
                "One or more analysis records were not found "
                "for the current user."
            ),
        )

    # Preserve the exact order from the Home page.
    records_by_id = {
        record.id: record
        for record in records
    }

    ordered_records = [
        records_by_id[analysis_id]
        for analysis_id in requested_ids
    ]

    data = export_pdf(ordered_records)

    timestamp = dt.datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="current_analysis_{timestamp}.pdf"'
            )
        },
    )


# =========================================================
# SINGLE ANALYSIS PDF
# =========================================================

@router.get("/pdf/{analysis_id}")
def export_single_pdf_endpoint(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.id == analysis_id,
            AnalysisResult.user_id == current_user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Analysis result not found.",
        )

    data = export_single_pdf(record)

    timestamp = dt.datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'meme_analysis_{analysis_id}_{timestamp}.pdf'
            )
        },
    )