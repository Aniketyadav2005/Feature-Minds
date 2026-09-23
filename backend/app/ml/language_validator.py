"""
Language validation for the Meme Hate Speech Detector.

Application-supported languages:
    en = English
    hi = Hindi
    mr = Marathi

The validator combines:
1. Script detection
2. Hindi/Marathi marker words
3. Marathi-specific letters
4. Hindi-specific nukta characters
5. IndicLID
6. Lingua

Important:
- We do NOT guess a language when evidence is weak.
- If Hindi vs Marathi cannot be distinguished reliably,
  the user receives a friendly "could not verify" message.
"""

import logging
import re
from dataclasses import dataclass
from functools import lru_cache

from app.ml.scripts import (
    LANG_SCRIPT,
    meaningful_text,
    normalize,
    script_counts,
)
from app.services.indiclid_service import get_indiclid_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Optional Lingua
# ---------------------------------------------------------------------------

try:
    import importlib.util

    if importlib.util.find_spec("lingua") is not None:
        import lingua  # type: ignore[import-not-found]

        Language = lingua.Language
        LanguageDetectorBuilder = lingua.LanguageDetectorBuilder
    else:
        raise ImportError("lingua is not installed")
except Exception:  # pragma: no cover
    Language = None
    LanguageDetectorBuilder = None


# ---------------------------------------------------------------------------
# Result models
# ---------------------------------------------------------------------------

@dataclass
class LanguageValidationResult:
    valid: bool
    selected_language: str
    detected_language: str | None
    reason: str


@dataclass
class LanguageDetectionResult:
    language: str | None
    confidence: float
    reason: str


# ---------------------------------------------------------------------------
# ONLY THREE APPLICATION LANGUAGES
# ---------------------------------------------------------------------------

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
}


SUPPORTED_LANGUAGES = {"en", "hi", "mr"}

SCRIPT_DISPLAY_NAMES = {
    "latin": "English/Latin",
    "devanagari": "Devanagari",
}


DEVANAGARI_LANGS = {"hi", "mr"}


# ---------------------------------------------------------------------------
# Marathi markers
# ---------------------------------------------------------------------------

MARATHI_WORDS = {
    "आहे",
    "आहेत",
    "आहात",
    "आहेस",
    "नाही",
    "नाहीत",
    "नको",
    "मला",
    "तुला",
    "त्याला",
    "तिला",
    "आम्हाला",
    "तुम्ही",
    "आम्ही",
    "आपण",
    "काय",
    "आणि",
    "पण",
    "होते",
    "होता",
    "होती",
    "आता",
    "खूप",
    "माझ्या",
    "माझा",
    "माझी",
    "माझे",
    "तुझ्या",
    "तुझा",
    "तुझी",
    "त्याच्या",
    "म्हणून",
    "म्हणजे",
    "कुठे",
    "कसा",
    "कशी",
    "कसे",
    "सांगा",
    "सांग",
    "झाले",
    "झाला",
    "झाली",
    "गेले",
    "गेला",
    "गेली",
    "आले",
    "आला",
    "आली",
    "मध्ये",
    "साठी",
    "काहीही",
    "नाहीतर",
    "फक्त",
    "बघ",
    "बघा",
}

MARATHI_SUFFIX = re.compile(
    r"(णार|णारा|णारी|णारे|तोय|तेय|तंय|लंय|यचं|यचे|यचा|यची)$"
)


# ---------------------------------------------------------------------------
# Hindi markers
# ---------------------------------------------------------------------------

HINDI_WORDS = {
    "है",
    "हैं",
    "हूँ",
    "हूं",
    "था",
    "थी",
    "थे",
    "मैं",
    "मुझे",
    "मेरा",
    "मेरी",
    "मेरे",
    "तुम",
    "तुम्हें",
    "तुम्हारा",
    "तुम्हारी",
    "हम",
    "हमें",
    "क्या",
    "नहीं",
    "और",
    "के",
    "को",
    "से",
    "में",
    "पर",
    "यह",
    "वह",
    "रहा",
    "रही",
    "रहे",
    "सकता",
    "सकती",
    "चाहिए",
    "बहुत",
    "अब",
    "भी",
    "लेकिन",
    "कि",
    "क्यों",
    "कैसे",
    "कहाँ",
    "कहां",
    "जब",
    "तब",
    "गया",
    "गई",
    "गये",
    "गए",
    "करना",
    "करके",
    "अपना",
    "अपनी",
    "उसे",
    "उन्हें",
}


# Hindi-specific nukta characters:
# ज़, फ़, ख़, ग़, क़, ड़, ढ़ etc.
NUKTA = "\u093c"

# Marathi-specific retroflex L:
# ळ
MARATHI_LLA = "\u0933"


# ---------------------------------------------------------------------------
# Lingua detector
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _hi_mr_lingua_detector():
    """
    Build a Lingua detector restricted to Hindi and Marathi.
    """
    if LanguageDetectorBuilder is None or Language is None:
        return None

    try:
        return (
            LanguageDetectorBuilder
            .from_languages(
                Language.HINDI,
                Language.MARATHI,
            )
            .build()
        )
    except Exception:
        return None


def _lingua_vote(text: str) -> tuple[str | None, float]:
    """
    Returns:
        (language, confidence)

    Example:
        ("mr", 0.91)
        ("hi", 0.86)
        (None, 0.0)
    """

    detector = _hi_mr_lingua_detector()

    if detector is None:
        return None, 0.0

    try:
        values = detector.compute_language_confidence_values(text)
    except Exception:
        return None, 0.0

    confidence = {
        "mr": 0.0,
        "hi": 0.0,
    }

    for item in values:
        if item.language == Language.MARATHI:
            confidence["mr"] = item.value

        elif item.language == Language.HINDI:
            confidence["hi"] = item.value

    best_language = max(
        confidence,
        key=confidence.get,
    )

    best_confidence = confidence[best_language]

    if best_confidence >= 0.70:
        return best_language, best_confidence

    return None, best_confidence


# ---------------------------------------------------------------------------
# IndicLID
# ---------------------------------------------------------------------------

def _indiclid_vote(text: str) -> tuple[str | None, float]:
    """
    Detect Hindi/Marathi using IndicLID.
    """

    try:
        top = get_indiclid_service().detect_top_k(
            text,
            k=3,
        )
    except Exception:
        return None, 0.0

    if not top:
        return None, 0.0

    label, probability = top[0]

    if label == "mar_Deva":
        if probability >= 0.60:
            return "mr", probability

    if label == "hin_Deva":
        if probability >= 0.60:
            return "hi", probability

    return None, probability


# ---------------------------------------------------------------------------
# Marker scoring
# ---------------------------------------------------------------------------

def _marker_scores(text: str) -> tuple[int, int]:
    """
    Returns:
        (marathi_score, hindi_score)
    """

    tokens = text.split()

    mr_score = 0
    hi_score = 0

    for token in tokens:

        if token in MARATHI_WORDS:
            mr_score += 2

        if MARATHI_SUFFIX.search(token):
            mr_score += 2

        if token in HINDI_WORDS:
            hi_score += 2

    # Marathi-specific letter
    mr_score += 3 * text.count(MARATHI_LLA)

    # Hindi nukta
    hi_score += 3 * text.count(NUKTA)

    return mr_score, hi_score


# ---------------------------------------------------------------------------
# Hindi / Marathi detector
# ---------------------------------------------------------------------------

def _detect_devanagari_language(
    text: str,
) -> LanguageDetectionResult:
    """
    Detect Hindi vs Marathi.

    We require meaningful evidence.
    We never blindly assume Marathi/Hindi merely because
    the text is Devanagari.
    """

    mr_score, hi_score = _marker_scores(text)

    evidence = []

    # Marker evidence
    if mr_score > hi_score and mr_score >= 2:
        evidence.append(("mr", min(mr_score / 6.0, 1.0), "Marathi markers"))

    elif hi_score > mr_score and hi_score >= 2:
        evidence.append(("hi", min(hi_score / 6.0, 1.0), "Hindi markers"))

    # IndicLID
    indic_language, indic_confidence = _indiclid_vote(text)

    if indic_language:
        evidence.append(
            (
                indic_language,
                indic_confidence,
                "IndicLID",
            )
        )

    # Lingua
    lingua_language, lingua_confidence = _lingua_vote(text)

    if lingua_language:
        evidence.append(
            (
                lingua_language,
                lingua_confidence,
                "Lingua",
            )
        )

    logger.info(
        "Hindi/Marathi detection | text=%r | "
        "markers(mr=%d, hi=%d) | "
        "IndicLID=%s %.3f | "
        "Lingua=%s %.3f",
        text,
        mr_score,
        hi_score,
        indic_language,
        indic_confidence,
        lingua_language,
        lingua_confidence,
    )

    if not evidence:
        return LanguageDetectionResult(
            language=None,
            confidence=0.0,
            reason=(
                "The text is Devanagari, but there is not enough reliable "
                "evidence to distinguish Hindi from Marathi."
            ),
        )

    # Weighted voting
    scores = {
        "mr": 0.0,
        "hi": 0.0,
    }

    for language, confidence, source in evidence:

        if source == "Marathi markers":
            weight = 0.40

        elif source == "Hindi markers":
            weight = 0.40

        elif source == "IndicLID":
            weight = 0.35

        else:
            weight = 0.25

        scores[language] += confidence * weight

    detected = max(
        scores,
        key=scores.get,
    )

    detected_score = scores[detected]
    other = "hi" if detected == "mr" else "mr"

    # Need meaningful separation.
    difference = detected_score - scores[other]

    if detected_score < 0.35 or difference < 0.12:
        return LanguageDetectionResult(
            language=None,
            confidence=detected_score,
            reason=(
                "We could read Devanagari text, but we could not reliably "
                "distinguish Hindi from Marathi."
            ),
        )

    return LanguageDetectionResult(
        language=detected,
        confidence=min(detected_score, 1.0),
        reason=f"Detected {LANGUAGE_NAMES[detected]} text.",
    )


# ---------------------------------------------------------------------------
# Public language detector
# ---------------------------------------------------------------------------

def detect_language(text: str) -> LanguageDetectionResult:
    """
    Detect one of the three application languages:

        en
        hi
        mr

    Returns language=None when evidence is insufficient.
    """

    text = normalize(text or "")
    cleaned = meaningful_text(text)

    if len(cleaned.replace(" ", "")) < 3:
        return LanguageDetectionResult(
            language=None,
            confidence=0.0,
            reason=(
                "Not enough readable text was found to identify "
                "the language."
            ),
        )

    counts = script_counts(cleaned)

    total = sum(counts.values())

    if total <= 0:
        return LanguageDetectionResult(
            language=None,
            confidence=0.0,
            reason="No supported writing script was detected.",
        )

    dominant_script = max(
        counts,
        key=counts.get,
    )

    dominant_share = counts[dominant_script] / total

    # ---------------------------------------------------------------
    # English
    # ---------------------------------------------------------------

    if dominant_script == "latin":

        if dominant_share >= 0.55:
            return LanguageDetectionResult(
                language="en",
                confidence=min(dominant_share, 1.0),
                reason="Detected English/Latin-script text.",
            )

        return LanguageDetectionResult(
            language=None,
            confidence=dominant_share,
            reason=(
                "The image contains mixed Latin and non-Latin text, "
                "so English could not be verified reliably."
            ),
        )

    # ---------------------------------------------------------------
    # Hindi / Marathi
    # ---------------------------------------------------------------

    if dominant_script == "devanagari":

        return _detect_devanagari_language(cleaned)

    # ---------------------------------------------------------------
    # Unsupported script
    # ---------------------------------------------------------------

    return LanguageDetectionResult(
        language=None,
        confidence=dominant_share,
        reason=(
            "The image does not contain readable English, Hindi, "
            "or Marathi text."
        ),
    )


# ---------------------------------------------------------------------------
# Public validator
# ---------------------------------------------------------------------------

def validate_language(
    text: str,
    selected_language: str,
) -> LanguageValidationResult:

    selected_language = (
        selected_language or ""
    ).lower().strip()

    if selected_language not in SUPPORTED_LANGUAGES:
        return LanguageValidationResult(
            valid=False,
            selected_language=selected_language,
            detected_language=None,
            reason=(
                "Please select English, Hindi, or Marathi."
            ),
        )

    detected = detect_language(text)

    # ---------------------------------------------------------------
    # Cannot determine
    # ---------------------------------------------------------------

    if detected.language is None:

        return LanguageValidationResult(
            valid=False,
            selected_language=selected_language,
            detected_language=None,
            reason=(
                "We could not reliably identify the language of this meme. "
                "Please upload a clearer image with larger, readable text."
            ),
        )

    # ---------------------------------------------------------------
    # Correct language
    # ---------------------------------------------------------------

    if detected.language == selected_language:

        return LanguageValidationResult(
            valid=True,
            selected_language=selected_language,
            detected_language=LANGUAGE_NAMES[selected_language],
            reason=(
                f"{LANGUAGE_NAMES[selected_language]} language verified."
            ),
        )

    # ---------------------------------------------------------------
    # Wrong language
    # ---------------------------------------------------------------

    detected_name = LANGUAGE_NAMES[detected.language]
    selected_name = LANGUAGE_NAMES[selected_language]

    return LanguageValidationResult(
        valid=False,
        selected_language=selected_language,
        detected_language=detected_name,
        reason=(
            f"This meme appears to contain {detected_name} text, "
            f"but you selected {selected_name}. "
            f"Please select {detected_name} Ocr Language and try again."
        ),
    )