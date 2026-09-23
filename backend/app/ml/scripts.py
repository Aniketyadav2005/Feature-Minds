"""
Unicode script helpers shared by the OCR engine and the language validator.

WHY THIS FILE EXISTS
--------------------
The old code used ``str.isalpha()`` to "keep only letters". In Indic scripts
(Devanagari, Bengali, Tamil, Telugu, Kannada, Gujarati ...) vowel signs such as
'ा', 'ि', 'ी', 'ू' and the virama '्' are *combining marks* (Unicode category
Mc / Mn), and ``isalpha()`` returns False for them. So

    "तू आता मला शिकवणार"  ->  "त आत मल शकवणर"

which is not Marathi any more, and Lingua then guessed "Hindi".
Here we keep letters (category L*) AND combining marks (category M*).
"""
import unicodedata

# (start, end) inclusive code-point ranges per script.
SCRIPT_RANGES: dict[str, list[tuple[int, int]]] = {
    "latin": [(0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F)],
    "devanagari": [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
    "bengali": [(0x0980, 0x09FF)],
    "gurmukhi": [(0x0A00, 0x0A7F)],
    "gujarati": [(0x0A80, 0x0AFF)],
    "tamil": [(0x0B80, 0x0BFF)],
    "telugu": [(0x0C00, 0x0C7F)],
    "kannada": [(0x0C80, 0x0CFF)],
    "arabic": [(0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
}

# Script expected for each UI language code.
LANG_SCRIPT: dict[str, str] = {
    "en": "latin",
    "hi": "devanagari",
    "mr": "devanagari",
    "bn": "bengali",
    "te": "telugu",
    "ta": "tamil",
    "kn": "kannada",
    "gu": "gujarati",
    "ur": "arabic",
}


def normalize(text: str) -> str:
    """NFC-normalise and drop invisible characters that OCR sometimes emits."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    for bad in ("\u200b", "\ufeff", "\u200e", "\u200f"):
        text = text.replace(bad, "")
    return text


def is_letter_or_mark(ch: str) -> bool:
    """True for letters (L*) and combining marks (M*) — i.e. real Indic text."""
    return unicodedata.category(ch)[0] in ("L", "M")


def meaningful_text(text: str) -> str:
    """
    Keep letters + combining marks + spaces. Drops digits, punctuation, emoji.
    (Unlike ``str.isalpha()`` this does NOT destroy Indic vowel signs.)
    """
    text = normalize(text).replace("'", "").replace("\u2019", "")
    kept = "".join(ch if (is_letter_or_mark(ch) or ch.isspace()) else " " for ch in text)
    return " ".join(kept.split())


def script_of(ch: str) -> str | None:
    cp = ord(ch)
    for name, ranges in SCRIPT_RANGES.items():
        for lo, hi in ranges:
            if lo <= cp <= hi:
                return name
    return None


def script_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ch in text:
        if not is_letter_or_mark(ch):
            continue
        name = script_of(ch)
        if name:
            counts[name] = counts.get(name, 0) + 1
    return counts


def script_ratio(text: str, script: str) -> float:
    """Share (0-1) of the letters in ``text`` that belong to ``script``."""
    counts = script_counts(text)
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return counts.get(script, 0) / total