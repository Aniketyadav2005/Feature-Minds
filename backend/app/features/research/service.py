"""
Research metrics feature — ground-truth labelling + Precision/Recall/F1/Accuracy.
Mirrors Tab 3 ("Research Metrics") of the original Streamlit app, but ground
truth is now persisted in MySQL instead of st.session_state.
"""
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisResult, GroundTruth
from app.schemas.analysis import MetricsOut


def upsert_ground_truth(
    db: Session,
    analysis_id: int,
    label: str,
    user_id: int,
) -> GroundTruth:
    record = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.id == analysis_id,
            AnalysisResult.user_id == user_id,
        )
        .first()
    )

    if not record:
        raise ValueError("Analysis result not found.")

    gt = (
        db.query(GroundTruth)
        .filter(
            GroundTruth.analysis_id == analysis_id
        )
        .first()
    )

    if gt:
        gt.label = label
    else:
        gt = GroundTruth(
            analysis_id=analysis_id,
            label=label,
        )
        db.add(gt)

    db.commit()
    db.refresh(gt)

    return gt


def compute_metrics(
    db: Session,
    user_id: int,
) -> MetricsOut | None:
    rows = (
        db.query(AnalysisResult, GroundTruth)
        .join(
            GroundTruth,
            GroundTruth.analysis_id == AnalysisResult.id,
        )
        .filter(
            AnalysisResult.user_id == user_id
        )
        .all()
    )

    if not rows:
        return None

    tp = sum(
        1
        for r, gt in rows
        if r.is_hate and gt.label == "hate"
    )

    fp = sum(
        1
        for r, gt in rows
        if r.is_hate and gt.label == "safe"
    )

    fn = sum(
        1
        for r, gt in rows
        if not r.is_hate and gt.label == "hate"
    )

    tn = sum(
        1
        for r, gt in rows
        if not r.is_hate and gt.label == "safe"
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    accuracy = (tp + tn) / len(rows)

    return MetricsOut(
        accuracy=round(accuracy, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1_score=round(f1, 4),
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        labelled_count=len(rows),
    )
