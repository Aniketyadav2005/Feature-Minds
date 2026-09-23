"""
IndicLID (AI4Bharat) native-script language identifier, powered by fastText.

Notes
-----
* The file inside ``indiclid-ftn.zip`` is *named* ``model_baseline_roman.bin``
  but it is the IndicLID-FTN (native-script) model — that is the correct one
  for Devanagari / Bengali / Tamil ... text, so the model itself is fine.
* The model is loaded lazily and the service degrades gracefully: if fastText
  or the model file is missing, ``available`` is False and the validator simply
  uses its other signals instead of crashing the whole API at import time.
"""
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

try:  # fastText is an optional runtime dependency
    import fasttext  # type: ignore[import-not-found]

    try:  # silence the harmless "load_model does not return ..." warning
        fasttext.FastText.eprint = lambda *_a, **_k: None  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        pass
except ImportError:  # pragma: no cover
    fasttext = None


class IndicLIDService:
    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parents[2]  # backend/
        self.model_path = (
            base_dir / "models" / "indiclid" / "indiclid-ftn" / "model_baseline_roman.bin"
        )
        self.model = None

        if fasttext is None:
            logger.warning("fasttext is not installed - IndicLID disabled (pip install fasttext-wheel).")
            return
        if not self.model_path.exists():
            logger.warning("IndicLID model not found at %s - IndicLID disabled.", self.model_path)
            return

        logger.info("Loading IndicLID model: %s", self.model_path)
        self.model = fasttext.load_model(str(self.model_path))
        logger.info("IndicLID model loaded")

    @property
    def available(self) -> bool:
        return self.model is not None

    def detect_top_k(self, text: str, k: int = 3) -> list[tuple[str, float]]:
        """Returns [(label, probability), ...] e.g. [('mar_Deva', 0.99), ...]."""
        if not self.available or not text or not text.strip():
            return []

        text = " ".join(text.strip().split())  # fastText needs a single line
        labels, probs = self.model.predict(text, k=k)
        return [
            (label.replace("__label__", ""), float(prob))
            for label, prob in zip(labels, probs)
        ]

    def detect_language(self, text: str) -> dict:
        """Backwards-compatible helper: best label + confidence."""
        top = self.detect_top_k(text, k=1)
        if not top:
            return {"language": "unknown", "confidence": 0.0}
        return {"language": top[0][0], "confidence": top[0][1]}


@lru_cache(maxsize=1)
def get_indiclid_service() -> IndicLIDService:
    return IndicLIDService()