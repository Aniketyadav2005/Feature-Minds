"""
Pydantic request/response models for the API layer.
"""
import datetime as dt
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from pydantic import BaseModel, ConfigDict, Field


class AnalysisResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    source: str
    timestamp: dt.datetime
    extracted_text: str
    caption: str
    label: str
    is_hate: bool
    hate_score: float
    safe_score: float
    category: str
    threshold_used: int
    image_url: Optional[str] = None
    blurred_image_url: Optional[str] = None
    has_image: bool
    ground_truth_label: Optional[str] = None


class AnalyzeUrlRequest(BaseModel):
    url: str
    threshold_pct: int = Field(50, ge=10, le=90)
    ocr_lang: str = Field(..., min_length=2, max_length=10)


class GroundTruthIn(BaseModel):
    analysis_id: int
    label: Literal["hate", "safe"]


class MetricsOut(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    tp: int
    fp: int
    fn: int
    tn: int
    labelled_count: int


class HistoryStatsOut(BaseModel):
    total: int
    hate_count: int
    safe_count: int
    avg_hate_score: float
    category_breakdown: dict[str, int]
    timeline: List[dict]  # [{timestamp, hate_score}]


class ClearHistoryResponse(BaseModel):
    deleted: int
