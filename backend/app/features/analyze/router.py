"""
POST endpoints for running meme analysis.

Supports image-file uploads only.
URL analysis has been removed.
"""

from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from PIL import Image
from sqlalchemy.orm import Session
from app.database import get_db
from app.features.analyze.service import analyze_image
from app.features.serializers import to_out
from app.schemas.analysis import AnalysisResultOut
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/api/analyze",
    tags=["analyze"],
)

MAX_BATCH = 20


@router.post("/upload", response_model=List[AnalysisResultOut])
async def analyze_uploaded_files(
    files: List[UploadFile] = File(...),
    threshold_pct: int = Form(50),
    ocr_lang: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files provided.",
        )

    files = files[:MAX_BATCH]

    if not ocr_lang.strip():
        raise HTTPException(
            status_code=400,
            detail="Please select an OCR language.",
        )

    langs = [ocr_lang.strip().lower()]

    results = []

    for f in files:
        try:
            image_pil = Image.open(f.file).convert("RGB")

            record = analyze_image(
                db,
                image_pil,
                f.filename,
                "upload",
                threshold_pct,
                langs,
                current_user,
            )

            results.append(to_out(record))

        except ValueError as e:
            message = str(e)

            if message.startswith("LANGUAGE_MISMATCH|"):
                parts = message.split("|", 3)

                detail = parts[-1]

                raise HTTPException(
                    status_code=422,
                    detail=detail,
                )

            raise HTTPException(
                status_code=400,
                detail=message,
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Could not analyse {f.filename}: {e}",
            )

    return results