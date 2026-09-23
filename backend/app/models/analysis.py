"""
ORM models — mirrors the data that used to live in st.session_state.history
and the ground_truth dict, now persisted in MySQL.
"""
import datetime as dt

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    filename = Column(String(255), nullable=False, index=True)
    source = Column(SAEnum("upload", "url", name="source_type"), default="upload")
    timestamp = Column(DateTime, default=dt.datetime.utcnow, index=True)
    
    user = relationship(
        "User",
        back_populates="analyses",
    )

    extracted_text = Column(Text, default="")
    caption = Column(Text, default="")

    label = Column(SAEnum("hate", "nothate", name="label_type"), nullable=False)
    is_hate = Column(Boolean, default=False, index=True)
    hate_score = Column(Float, default=0.0)
    safe_score = Column(Float, default=0.0)
    category = Column(String(50), default="none")
    threshold_used = Column(Integer, default=50)

    # Stored relative to the static dir; None if not persisted (e.g. failed save)
    image_path = Column(String(500), nullable=True)
    blurred_image_path = Column(String(500), nullable=True)
    has_image = Column(Boolean, default=True)

    ground_truth = relationship(
        "GroundTruth", back_populates="analysis", uselist=False,
        cascade="all, delete-orphan",
    )


class GroundTruth(Base):
    """
    Human-labelled ground truth for one analysis result, used to compute
    Precision / Recall / F1 / Accuracy on the Research Metrics feature.
    """
    __tablename__ = "ground_truth"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(
        Integer, ForeignKey("analysis_results.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    label = Column(SAEnum("hate", "safe", name="gt_label_type"), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    analysis = relationship("AnalysisResult", back_populates="ground_truth")
