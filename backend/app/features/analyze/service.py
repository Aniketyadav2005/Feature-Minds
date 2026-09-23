import datetime as dt
import io
import logging

import numpy as np
import requests
from PIL import Image
from sqlalchemy.orm import Session

from app.models.user import User

from app.config import get_settings
from app.ml.caption_engine import generate_caption
from app.ml.classifier_engine import classify_text
from app.ml.image_utils import blur_image, save_image
from app.ml.keywords import categorize_hate
from app.ml.ocr_engine import extract_text
from app.ml.language_validator import (
    detect_language,
    validate_language,
)
from app.models.analysis import AnalysisResult


logger = logging.getLogger(__name__)

settings = get_settings()


# ---------------------------------------------------------------------------
# ONLY THREE LANGUAGES
# ---------------------------------------------------------------------------

SUPPORTED_OCR_LANGUAGES = (
    "en",
    "hi",
    "mr",
)


LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}


# ---------------------------------------------------------------------------
# URL helper kept for backward compatibility.
# URL analysis itself has been removed from the API.
# ---------------------------------------------------------------------------

def load_image_from_url(url: str) -> Image.Image:
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=15,
    )

    response.raise_for_status()

    return Image.open(
        io.BytesIO(response.content)
    ).convert("RGB")


# ---------------------------------------------------------------------------
# OCR candidate
# ---------------------------------------------------------------------------

def _find_best_language_ocr(
    image_np: np.ndarray,
    selected_language: str,
) -> tuple[str, float, str]:
    """
    Try OCR one language at a time.

    Priority:
        1. User-selected language
        2. Other supported languages

    Returns:
        extracted_text,
        OCR_confidence,
        detected_language
    """

    selected_language = selected_language.lower().strip()

    languages_to_try = [
        selected_language,
        *[
            lang
            for lang in SUPPORTED_OCR_LANGUAGES
            if lang != selected_language
        ],
    ]

    candidates = []

    for language in languages_to_try:

        try:
            text, ocr_confidence = extract_text(
                image_np,
                [language],
                min_confidence=0.20,
            )

        except Exception as exc:
            logger.warning(
                "OCR failed for language=%s: %s",
                language,
                exc,
            )
            continue

        if not text or not text.strip():
            logger.info(
                "OCR produced no usable text | language=%s",
                language,
            )
            continue

        text = text.strip()

        detection = detect_language(text)

        logger.info(
            "OCR candidate | requested=%s | detected=%s | "
            "ocr_confidence=%.3f | language_confidence=%.3f | text=%r",
            language,
            detection.language,
            ocr_confidence,
            detection.confidence,
            text,
        )

        if detection.language is None:
            continue

        # Combined score:
        # OCR quality + language detection quality.
        combined_score = (
            0.60 * float(ocr_confidence)
            + 0.40 * float(detection.confidence)
        )

        candidates.append(
            (
                combined_score,
                language,
                text,
                float(ocr_confidence),
                detection.language,
            )
        )

    # -----------------------------------------------------------------------
    # No readable candidate
    # -----------------------------------------------------------------------

    if not candidates:
        raise ValueError(
            "NO_TEXT|"
            "We could not detect readable English, Hindi, or Marathi text "
            "in this meme. Please upload a clearer image with visible text."
        )

    # Highest quality candidate
    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    (
        best_score,
        ocr_language,
        best_text,
        best_ocr_confidence,
        detected_language,
    ) = candidates[0]

    logger.info(
        "Best OCR candidate | OCR=%s | detected=%s | score=%.3f | text=%r",
        ocr_language,
        detected_language,
        best_score,
        best_text,
    )

    return (
        best_text,
        best_ocr_confidence,
        detected_language,
    )


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

def analyze_image(
    db: Session,
    image_pil: Image.Image,
    filename: str,
    source: str,
    threshold_pct: int,
    ocr_langs: list[str],
    user: User,
) -> AnalysisResult:

    """
    Full pipeline:

        OCR
        ↓
        Language validation
        ↓
        BLIP caption
        ↓
        Hate classifier
        ↓
        Category
        ↓
        Optional blur
        ↓
        Database
    """

    # -----------------------------------------------------------------------
    # Validate selected language
    # -----------------------------------------------------------------------

    if len(ocr_langs) != 1:
        raise ValueError(
            "Please select exactly one OCR language."
        )

    selected_language = (
        ocr_langs[0] or ""
    ).strip().lower()

    if selected_language not in SUPPORTED_OCR_LANGUAGES:
        raise ValueError(
            "Please select English, Hindi, or Marathi Ocr Language."
        )

    # -----------------------------------------------------------------------
    # Threshold
    # -----------------------------------------------------------------------

    threshold = threshold_pct / 100.0

    # -----------------------------------------------------------------------
    # Convert image
    # -----------------------------------------------------------------------

    image_np = np.array(
        image_pil.convert("RGB")
    )

    # -----------------------------------------------------------------------
    # OCR
    # -----------------------------------------------------------------------

    extracted_text, ocr_confidence, detected_language = (
        _find_best_language_ocr(
            image_np,
            selected_language,
        )
    )

    # -----------------------------------------------------------------------
    # LANGUAGE VALIDATION
    # -----------------------------------------------------------------------

    language_result = validate_language(
        extracted_text,
        selected_language,
    )

    logger.info(
        "Language validation | selected=%s | detected=%s | "
        "valid=%s | reason=%s",
        selected_language,
        language_result.detected_language,
        language_result.valid,
        language_result.reason,
    )

    if not language_result.valid:

        detected_name = (
            language_result.detected_language
            or LANGUAGE_NAMES.get(
                detected_language,
                "unknown",
            )
        )

        raise ValueError(
            "LANGUAGE_MISMATCH|"
            f"selected={LANGUAGE_NAMES[selected_language]}|"
            f"detected={detected_name}|"
            f"{language_result.reason}"
        )

    # -----------------------------------------------------------------------
    # Caption
    # -----------------------------------------------------------------------

    caption = generate_caption(
        image_pil
    )

    # -----------------------------------------------------------------------
    # Classification
    # -----------------------------------------------------------------------

    combined = (
        f"{caption} {extracted_text}"
    )

    label, hate_score, safe_score = classify_text(
        combined,
        threshold=threshold,
    )

    is_hate = label == "hate"

    # -----------------------------------------------------------------------
    # Hate category
    # -----------------------------------------------------------------------

    category = (
        categorize_hate(combined)
        if is_hate
        else "none"
    )

    # -----------------------------------------------------------------------
    # Save original image
    # -----------------------------------------------------------------------

    image_path = save_image(
        image_np,
        settings.UPLOAD_DIR,
    )

    # -----------------------------------------------------------------------
    # Blur hate image
    # -----------------------------------------------------------------------

    blurred_path = None

    if is_hate:

        blurred_np = blur_image(
            image_np
        )

        blurred_path = save_image(
            blurred_np,
            settings.BLURRED_DIR,
            prefix="blur_",
        )

    # -----------------------------------------------------------------------
    # Database
    # -----------------------------------------------------------------------

    record = AnalysisResult(
        user_id=user.id,
        filename=filename,
        source=source,
        timestamp=dt.datetime.utcnow(),

        extracted_text=extracted_text,
        caption=caption,

        label=label,
        is_hate=is_hate,

        hate_score=round(
            hate_score * 100,
            1,
        ),

        safe_score=round(
            safe_score * 100,
            1,
        ),

        category=category,

        threshold_used=threshold_pct,

        image_path=image_path,
        blurred_image_path=blurred_path,

        has_image=True,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


# ---------------------------------------------------------------------------
# Kept only so old imports do not break.
# URL analysis endpoint itself has been removed.
# ---------------------------------------------------------------------------

def derive_filename_from_url(url: str) -> str:

    raw_name = (
        url
        .split("/")[-1]
        .split("?")[0]
    )

    return (
        raw_name
        if raw_name
        else "url_image.jpg"
    )