"""
OCR text post-processing: put back spaces that EasyOCR dropped between words.

WHY
---
Memes use tight, bold fonts, so the gap between two Devanagari words can be
almost zero and EasyOCR returns them glued together:

    "तू आतामला शिकवणार"   (OCR)   ->   "तू आता मला शिकवणार"   (correct)

HOW (deliberately conservative)
-------------------------------
A token is split ONLY when

  * it is not itself a known word,
  * it is written completely in Devanagari,
  * the WHOLE token can be built from known, standalone Marathi words
    (pronouns, question words, conjunctions, common adverbs ...), and
  * at least one piece has 3+ characters (this stops real words such as
    'काका' = का+का or 'हाती' = हा+ती from being split).

Unknown / content words (e.g. 'शिकवणार') are never touched, so this cannot
corrupt text it does not understand. To support more words, add them to
MARATHI_STANDALONE_WORDS.
"""
from functools import lru_cache

from app.ml.scripts import is_letter_or_mark, normalize, script_ratio

# Standalone Marathi words that are normally written with spaces around them.
# NOTE: clitics that are written JOINED to the previous word (-ही, -च, -ला,
# -चा ...) and postpositions (पर्यंत, पासून ...) are intentionally NOT here.
MARATHI_STANDALONE_WORDS = frozenset("""
मी तू तो ती ते तुम्ही आम्ही आपण
मला तुला त्याला तिला त्यांना आम्हाला तुम्हाला आपल्याला
माझा माझी माझे माझ्या तुझा तुझी तुझे तुझ्या
त्याचा त्याची त्याचे त्याच्या तिचा तिची तिचे तिच्या
आमचा आमची आमचे आमच्या तुमचा तुमची तुमचे तुमच्या
हा ही हे या ह्या त्या
कोण काय कुठे कधी कसा कशी कसे किती कोणता कोणती कोणते का
म्हणजे म्हणून कारण आणि पण किंवा तर जर मग की परंतु म्हणे
आहे आहेत आहेस आहात आहोत नाही नाहीत नाहीस नको
होता होती होते होतो होतास हो
असा असे अशी असं
आता इथे तिथे येथे तेथे आज उद्या काल परवा नेहमी पुन्हा
फार खूप थोडा थोडी थोडे सगळे सगळा सगळी सर्व सारे काही प्रत्येक
एक दोन तीन फक्त सुद्धा अगदी जरा बरं बरे
अरे अहो अगं चला बघा सांगा ऐका
""".split())

_MIN_LONG_PIECE = 3  # at least one piece must have this many characters


def _split_core(core: str) -> list[str] | None:
    """
    Split ``core`` into >=2 known words (fewest pieces, then longest pieces).
    Returns None when the token cannot be fully explained by known words.
    """
    n = len(core)
    # best[i] = (piece_count, -sum_of_squared_lengths, previous_index)
    best: list[tuple[int, int, int] | None] = [None] * (n + 1)
    best[0] = (0, 0, -1)

    for end in range(1, n + 1):
        for start in range(0, end):
            if best[start] is None:
                continue
            piece = core[start:end]
            if piece not in MARATHI_STANDALONE_WORDS:
                continue
            count = best[start][0] + 1
            score = best[start][1] - len(piece) ** 2
            candidate = (count, score, start)
            if best[end] is None or candidate[:2] < best[end][:2]:
                best[end] = candidate

    if best[n] is None or best[n][0] < 2:
        return None

    pieces: list[str] = []
    idx = n
    while idx > 0:
        prev = best[idx][2]
        pieces.append(core[prev:idx])
        idx = prev
    pieces.reverse()

    if not any(len(p) >= _MIN_LONG_PIECE for p in pieces):
        return None
    return pieces


def _fix_token(token: str) -> str:
    # Separate punctuation at both ends (e.g. 'आतामला,' or '"आतामला"').
    start = 0
    end = len(token)
    while start < end and not is_letter_or_mark(token[start]):
        start += 1
    while end > start and not is_letter_or_mark(token[end - 1]):
        end -= 1

    lead, core, tail = token[:start], token[start:end], token[end:]

    if len(core) < 4 or core in MARATHI_STANDALONE_WORDS:
        return token
    if script_ratio(core, "devanagari") < 1.0:
        return token  # mixed with Latin/digits -> do not touch

    pieces = _split_core(core)
    if not pieces:
        return token
    return lead + " ".join(pieces) + tail


@lru_cache(maxsize=4096)
def _fix_cached(text: str) -> str:
    return " ".join(_fix_token(tok) for tok in text.split())


def fix_word_spacing(text: str, lang: str) -> str:
    """Restore missing spaces between merged words. Only Marathi for now."""
    if not text or lang != "mr":
        return text
    return _fix_cached(normalize(text))