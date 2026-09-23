"""
History feature — listing, filtering, stats and deletion.
Mirrors Tab 2 ("Upload History") of the original Streamlit app.
"""
import os
from collections import Counter
from typing import Literal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisResult


def list_history(
    db: Session,
    filter_opt: Literal["all", "hate", "safe"] = "all",
    limit: int = 200,
    offset: int = 0,
    user_id: int | None = None,
) -> list[AnalysisResult]:

    q = db.query(AnalysisResult)

    # Show history only for the logged-in user
    if user_id is not None:
        q = q.filter(
            AnalysisResult.user_id == user_id
        )

    # Filter hate results
    if filter_opt == "hate":
        q = q.filter(
            AnalysisResult.is_hate.is_(True)
        )

    # Filter safe results
    elif filter_opt == "safe":
        q = q.filter(
            AnalysisResult.is_hate.is_(False)
        )

    return (
        q.order_by(
            AnalysisResult.timestamp.desc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_stats(
    db: Session,
    user_id: int,
) -> dict:
    total = (
        db.query(func.count(AnalysisResult.id))
        .filter(AnalysisResult.user_id == user_id)
        .scalar()
        or 0
    )

    hate_count = (
        db.query(func.count(AnalysisResult.id))
        .filter(
            AnalysisResult.user_id == user_id,
            AnalysisResult.is_hate.is_(True),
        )
        .scalar()
        or 0
    )

    safe_count = total - hate_count

    avg_hate = (
        db.query(func.avg(AnalysisResult.hate_score))
        .filter(AnalysisResult.user_id == user_id)
        .scalar()
        or 0.0
    )

    hate_rows = (
        db.query(AnalysisResult.category)
        .filter(
            AnalysisResult.user_id == user_id,
            AnalysisResult.is_hate.is_(True),
        )
        .all()
    )

    category_breakdown = dict(
        Counter(r[0] for r in hate_rows)
    )

    timeline_rows = (
        db.query(
            AnalysisResult.timestamp,
            AnalysisResult.hate_score,
        )
        .filter(AnalysisResult.user_id == user_id)
        .order_by(AnalysisResult.timestamp.asc())
        .all()
    )

    timeline = [
        {
            "timestamp": ts.isoformat(),
            "hate_score": score,
        }
        for ts, score in timeline_rows
        if ts is not None
    ]

    return {
        "total": total,
        "hate_count": hate_count,
        "safe_count": safe_count,
        "avg_hate_score": round(float(avg_hate), 1),
        "category_breakdown": category_breakdown,
        "timeline": timeline,
    }


def delete_one(
    db: Session,
    analysis_id: int,
    user_id: int,
) -> bool:
    record = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.id == analysis_id,
            AnalysisResult.user_id == user_id,
        )
        .first()
    )

    if not record:
        return False

    _remove_files(record)
    db.delete(record)
    db.commit()

    return True

    if not record:
        return False
    _remove_files(record)
    db.delete(record)
    db.commit()
    return True


def clear_all(
    db: Session,
    user_id: int,
) -> int:
    records = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.user_id == user_id)
        .all()
    )

    count = len(records)

    for r in records:
        _remove_files(r)
        db.delete(r)

    db.commit()

    return count
    count = len(records)
    for r in records:
        _remove_files(r)
        db.delete(r)
    db.commit()
    return count


def _remove_files(record: AnalysisResult) -> None:
    for path in (record.image_path, record.blurred_image_path):
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
