"""
Shared helper to turn an ORM AnalysisResult into the API response schema,
building public URLs for the stored (and optionally blurred) images.
"""
from app.models.analysis import AnalysisResult
from app.schemas.analysis import AnalysisResultOut


def _to_static_url(path: str | None) -> str | None:
    if not path:
        return None
    # Files are saved under app/static/... and served at /static/...
    normalized = path.replace("\\", "/")
    idx = normalized.find("static/")
    rel = normalized[idx:] if idx != -1 else normalized
    return f"/{rel}"


def to_out(record: AnalysisResult) -> AnalysisResultOut:
    return AnalysisResultOut(
        id=record.id,
        filename=record.filename,
        source=record.source,
        timestamp=record.timestamp,
        extracted_text=record.extracted_text,
        caption=record.caption,
        label=record.label,
        is_hate=record.is_hate,
        hate_score=record.hate_score,
        safe_score=record.safe_score,
        category=record.category,
        threshold_used=record.threshold_used,
        image_url=_to_static_url(record.image_path),
        blurred_image_url=_to_static_url(record.blurred_image_path),
        has_image=record.has_image,
        ground_truth_label=record.ground_truth.label if record.ground_truth else None,
    )
