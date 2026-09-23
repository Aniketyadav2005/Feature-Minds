"""
Keyword-based hate category classifier (unchanged logic from the original
Streamlit app — kept simple/interpretable rather than another ML model).
"""

HATE_KEYWORDS: dict[str, list[str]] = {
    "racism": [
        "race", "racial", "racist", "negro", "ethnic", "colored",
        "mongrel", "xenophob", "supremacist", "apartheid",
    ],
    "sexism": [
        "women", "female", "feminist", "misogyn", "sexist",
        "kitchen", "sandwich", "gender", "bitch", "slut", "whore",
    ],
    "religion": [
        "muslim", "islam", "jew", "jewish", "christian", "hindu",
        "infidel", "kafir", "crusade", "jihad", "atheist",
    ],
    "homophobia": [
        "gay", "lesbian", "lgbt", "queer", "homo", "faggot",
        "tranny", "trans", "bisexual",
    ],
    "violence": [
        "kill", "murder", "die", "death", "shoot", "bomb",
        "attack", "threat", "destroy", "exterminate", "genocide",
    ],
}

CATEGORY_COLORS: dict[str, str] = {
    "racism": "#e57373",
    "sexism": "#f06292",
    "religion": "#ffb74d",
    "homophobia": "#ce93d8",
    "violence": "#ef5350",
    "general": "#90a4ae",
    "none": "#4caf7d",
}


def categorize_hate(text: str) -> str:
    """Returns the first matching category, or 'general' as a fallback."""
    text_lower = text.lower()
    for category, keywords in HATE_KEYWORDS.items():
        if any(k in text_lower for k in keywords):
            return category
    return "general"
