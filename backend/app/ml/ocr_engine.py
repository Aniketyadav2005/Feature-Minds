
"""
Production OCR wrapper for meme analysis - V2.

Features:
- Cached EasyOCR readers
- Image upscaling
- Original-image OCR
- CLAHE contrast enhancement
- Adaptive threshold OCR fallback
- Language-specific OCR
- Confidence filtering
- Bounding-box ordering
- Duplicate-text removal
- Multi-pass OCR result scoring
- Better handling of difficult meme text
"""

import threading
from functools import lru_cache

import cv2
import easyocr
import numpy as np
from app.ml.scripts import LANG_SCRIPT, normalize, script_ratio
from app.ml.text_postprocess import fix_word_spacing

# Languages exposed by this application.
# We intentionally support only the three languages required
# for the competition demo.
EASYOCR_SUPPORTED_LANGS = {"en", "hi", "mr"}

_lock = threading.Lock()


@lru_cache(maxsize=8)
def _get_reader(langs: tuple[str, ...]) -> easyocr.Reader:
    """
    Create and cache one EasyOCR reader per language set.
    """

    with _lock:
        print(
            f"Loading EasyOCR reader for language: {langs}"
        )

        return easyocr.Reader(
            list(langs),
            gpu=False,
        )


def _upscale_image(
    image: np.ndarray,
) -> np.ndarray:
    """
    Upscale smaller images for better OCR.

    Larger text gives EasyOCR more pixels to work with,
    especially for Marathi/Indic scripts.
    """

    if image is None or image.size == 0:
        return image

    height, width = image.shape[:2]

    longest_side = max(
        height,
        width,
    )

    if longest_side < 1200:
        scale = 2.5

    elif longest_side < 1800:
        scale = 2.0

    elif longest_side < 2400:
        scale = 1.5

    else:
        scale = 1.0

    if scale == 1.0:
        return image

    return cv2.resize(
        image,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_CUBIC,
    )


def _prepare_image(
    image_np: np.ndarray,
) -> np.ndarray:
    """
    Normalize the input image and upscale it.
    """

    if image_np is None or image_np.size == 0:
        return image_np

    image = image_np.copy()

    if image.dtype != np.uint8:
        image = np.clip(
            image,
            0,
            255,
        ).astype(np.uint8)

    return _upscale_image(image)


def _preprocess_image(
    image_np: np.ndarray,
) -> np.ndarray:
    """
    CLAHE-based enhanced OCR image.

    This is intentionally separate from the original image
    so that OCR can compare both versions.
    """

    if image_np is None or image_np.size == 0:
        return image_np

    image = image_np.copy()

    lab = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2LAB,
    )

    l_channel, a_channel, b_channel = cv2.split(
        lab
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.5,
        tileGridSize=(8, 8),
    )

    l_channel = clahe.apply(
        l_channel
    )

    enhanced = cv2.merge(
        (
            l_channel,
            a_channel,
            b_channel,
        )
    )

    enhanced = cv2.cvtColor(
        enhanced,
        cv2.COLOR_LAB2RGB,
    )

    return enhanced


def _create_threshold_image(
    image: np.ndarray,
) -> np.ndarray:
    """
    Create a high-contrast grayscale image.

    IMPORTANT:
    Thresholding is performed directly from the
    upscaled original image rather than the CLAHE image.
    """

    if image is None or image.size == 0:
        return image

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY,
    )

    # Reduce small noise while preserving text edges.
    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    thresholded = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    return cv2.cvtColor(
        thresholded,
        cv2.COLOR_GRAY2RGB,
    )


def _normalise_text(
    text: str,
) -> str:
    """
    Basic whitespace cleanup.

    Does NOT attempt to insert Marathi word boundaries,
    because doing that heuristically can corrupt OCR text.
    """

    if not text:
        return ""

    return " ".join(
        normalize(str(text)).strip().split()
    )


def _box_position(
    box,
) -> tuple[float, float]:
    """
    Return top-left x/y position of an OCR bounding box.
    """

    try:

        xs = [
            float(point[0])
            for point in box
        ]

        ys = [
            float(point[1])
            for point in box
        ]

        return (
            min(xs),
            min(ys),
        )

    except Exception:

        return (
            0.0,
            0.0,
        )


def _run_ocr(
    reader: easyocr.Reader,
    image: np.ndarray,
) -> list[dict]:
    """
    Run one EasyOCR pass.
    """

    if image is None or image.size == 0:
        return []

    try:

        results = reader.readtext(
            image,

            # -------------------------------------------------
            # Text detection
            # -------------------------------------------------

            text_threshold=0.55,
            low_text=0.25,
            link_threshold=0.35,

            # -------------------------------------------------
            # Image scaling
            # -------------------------------------------------

            canvas_size=3000,
            mag_ratio=1.5,

            # -------------------------------------------------
            # Text geometry
            # -------------------------------------------------

            paragraph=False,

            slope_ths=0.3,
            ycenter_ths=0.5,
            height_ths=0.5,
            width_ths=0.8,
        )

    except Exception as exc:

        print(
            f"⚠️ EasyOCR pass failed: {exc}"
        )

        return []

    accepted = []

    for item in results:

        if len(item) < 3:
            continue

        box = item[0]

        text = _normalise_text(
            item[1]
        )

        try:
            confidence = float(
                item[2]
            )

        except Exception:
            continue

        if not text:
            continue

        accepted.append(
            {
                "box": box,
                "text": text,
                "confidence": confidence,
            }
        )

    return accepted


def _deduplicate_results(
    results: list[dict],
    min_confidence: float,
) -> list[dict]:
    """
    Remove low-confidence and duplicate detections.
    """

    filtered = [
        item
        for item in results
        if item["confidence"]
        >= min_confidence
    ]

    if not filtered:
        return []

    # ---------------------------------------------------------
    # Sort top-to-bottom and left-to-right.
    # ---------------------------------------------------------

    filtered.sort(
        key=lambda item: (
            round(
                _box_position(
                    item["box"]
                )[1] / 25
            ) * 25,

            _box_position(
                item["box"]
            )[0],
        )
    )

    unique = []

    seen = set()

    for item in filtered:

        # Normalize duplicate comparison.
        #
        # Spaces are ignored only for duplicate detection.
        # Original OCR text is preserved.
        key = (
            item["text"]
            .casefold()
            .replace(" ", "")
        )

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)

        unique.append(item)

    return unique


def _build_text(
    results: list[dict],
) -> tuple[str, float]:
    """
    Convert OCR results into final text.
    """

    if not results:
        return "", 0.0

    texts = [
        item["text"]
        for item in results
    ]

    confidences = [
        item["confidence"]
        for item in results
    ]

    final_text = " ".join(
        texts
    )

    average_confidence = (
        sum(confidences)
        / len(confidences)
    )

    return (
        final_text.strip(),
        round(
            average_confidence,
            4,
        ),
    )


def _text_quality(
    text: str,
) -> float:
    """
    Estimate whether the OCR result contains a useful
    amount of actual text.

    This is intentionally language-agnostic.
    """

    if not text:
        return 0.0

    compact = text.replace(
        " ",
        "",
    )

    if not compact:
        return 0.0

    length = len(compact)

    # Very short OCR output is less useful.
    if length < 3:
        return 0.15

    if length < 8:
        return 0.40

    if length < 20:
        return 0.70

    if length < 50:
        return 0.90

    # Prevent very long noisy OCR from automatically winning.
    return 1.0


def _score_candidate(
    text: str,
    confidence: float,
    lang: str,
) -> float:
    """
    Score one OCR candidate. Scaled by how much of the text is in the
    script of the selected language, so high-confidence junk never beats
    the pass that actually read the Devanagari text.
    """

    if not text:
        return 0.0

    quality = _text_quality(
        text
    )

    base = (
        confidence * 0.80
        + quality * 0.20
    )

    expected_script = LANG_SCRIPT.get(lang)

    if not expected_script:
        return base

    ratio = script_ratio(
        text,
        expected_script,
    )

    # Floor of 0.5 so mixed-script memes are never wiped out.
    return base * (0.5 + 0.5 * ratio)


def _select_best_result(
    candidates: list[tuple[str, float, str]],
    lang: str,
) -> tuple[str, float]:
    """
    Select the best OCR result from multiple passes.

    Candidate format:
        (text, confidence, pass_name)
    """

    valid_candidates = [
        candidate
        for candidate in candidates
        if candidate[0]
    ]

    if not valid_candidates:
        return "", 0.0

    best = max(
        valid_candidates,
        key=lambda candidate: _score_candidate(
            candidate[0],
            candidate[1],
            lang,
        ),
    )

    best_text = best[0]
    best_confidence = best[1]
    best_pass = best[2]

    print(
        "OCR selected "
        f"pass={best_pass}, "
        f"confidence={best_confidence:.4f}, "
        f"text={best_text!r}"
    )

    return (
        best_text,
        best_confidence,
    )


def extract_text(
    image_np: np.ndarray,
    langs: list[str],
    min_confidence: float = 0.30,
) -> tuple[str, float]:
    """
    Run production multi-pass OCR.

    Passes:
        1. Original/upscaled image
        2. CLAHE enhanced image
        3. Adaptive threshold image

    Returns:
        (recognized_text, average_confidence)
    """

    if (
        image_np is None
        or image_np.size == 0
    ):
        return "", 0.0

    # ---------------------------------------------------------
    # Validate OCR languages
    # ---------------------------------------------------------

    clean_langs = [
        str(lang)
        .strip()
        .lower()
        for lang in langs
        if str(lang).strip()
    ]

    # Your application intentionally supports
    # exactly one selected OCR language.
    if len(clean_langs) != 1:
        return "", 0.0
    if clean_langs[0] not in EASYOCR_SUPPORTED_LANGS:
        raise ValueError(
            f"OCR for '{clean_langs[0]}' is not supported by the EasyOCR "
            "engine. Please choose another language."
        )

    # ---------------------------------------------------------
    # Get cached EasyOCR reader
    # ---------------------------------------------------------

    reader = _get_reader(
        tuple(clean_langs)
    )

    # ---------------------------------------------------------
    # Prepare original image
    # ---------------------------------------------------------

    original = _prepare_image(
        image_np
    )

    if (
        original is None
        or original.size == 0
    ):
        return "", 0.0

    candidates = []

    # =========================================================
    # PASS 1: Original / Upscaled
    # =========================================================

    try:

        original_results = _run_ocr(
            reader,
            original,
        )

        original_results = _deduplicate_results(
            original_results,
            min_confidence,
        )

        original_text, original_confidence = (
            _build_text(
                original_results
            )
        )

        if original_text:

            candidates.append(
                (
                    original_text,
                    original_confidence,
                    "original",
                )
            )

    except Exception as exc:

        print(
            f"⚠️ Original OCR pass failed: {exc}"
        )

    # =========================================================
    # PASS 2: CLAHE Enhanced
    # =========================================================

    try:

        enhanced = _preprocess_image(
            original
        )

        enhanced_results = _run_ocr(
            reader,
            enhanced,
        )

        enhanced_results = _deduplicate_results(
            enhanced_results,
            min_confidence,
        )

        enhanced_text, enhanced_confidence = (
            _build_text(
                enhanced_results
            )
        )

        if enhanced_text:

            candidates.append(
                (
                    enhanced_text,
                    enhanced_confidence,
                    "enhanced",
                )
            )

    except Exception as exc:

        print(
            f"⚠️ Enhanced OCR pass failed: {exc}"
        )

    # =========================================================
    # PASS 3: Adaptive Threshold
    # =========================================================

    try:

        # IMPORTANT:
        # Threshold is created from ORIGINAL/UPSCALED image,
        # not the CLAHE-enhanced image.
        threshold_image = _create_threshold_image(
            original
        )

        threshold_results = _run_ocr(
            reader,
            threshold_image,
        )

        threshold_results = _deduplicate_results(
            threshold_results,
            min_confidence,
        )

        threshold_text, threshold_confidence = (
            _build_text(
                threshold_results
            )
        )

        if threshold_text:

            candidates.append(
                (
                    threshold_text,
                    threshold_confidence,
                    "threshold",
                )
            )

    except Exception as exc:

        print(
            f"⚠️ Threshold OCR pass failed: {exc}"
        )

    # =========================================================
    # Select best candidate
    # =========================================================

    best_text, best_confidence = _select_best_result(
        candidates,
        clean_langs[0],
    )

    # Put back spaces that EasyOCR dropped between glued words.
    best_text = fix_word_spacing(
        best_text,
        clean_langs[0],
    )

    return best_text, best_confidence
