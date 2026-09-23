"""
RoBERTa hate-speech text classifier, loaded once per process.
"""
import threading

from transformers import pipeline

from app.config import get_settings

settings = get_settings()

_lock = threading.Lock()
_classifier = None


def _load():
    global _classifier
    if _classifier is None:
        with _lock:
            if _classifier is None:
                _classifier = pipeline(
                    "text-classification",
                    model=settings.CLASSIFIER_MODEL_NAME,
                    return_all_scores=True,
                )
    return _classifier


def classify_text(text: str, threshold: float = 0.5) -> tuple[str, float, float]:
    """Returns (label, hate_score, safe_score) where scores are 0-1 floats."""
    classifier = _load()
    raw = classifier(text)
    results = raw[0] if isinstance(raw[0], list) else raw
    scores = {r["label"].lower(): r["score"] for r in results}

    hate_score = scores.get("hate", scores.get("label_1", 0.0))
    safe_score = scores.get("nothate", scores.get("label_0", 1.0 - hate_score))
    label = "hate" if hate_score >= threshold else "nothate"
    return label, hate_score, safe_score
