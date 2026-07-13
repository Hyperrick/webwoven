from __future__ import annotations

import unicodedata

from .copy_vocabulary import SAFE_COPY_TOKENS
from .text_tokens import text_tokens

# Function words are deliberately grouped by language. Counting a single English marker is not
# sufficient: English evidence must dominate every supported non-English marker set.
NON_ENGLISH_EVIDENCE = (
    frozenset(
        {
            "aber",
            "auch",
            "auf",
            "aus",
            "das",
            "dem",
            "den",
            "der",
            "des",
            "die",
            "durch",
            "eine",
            "einem",
            "einen",
            "einer",
            "endet",
            "für",
            "führt",
            "im",
            "in",
            "ist",
            "mit",
            "nicht",
            "oder",
            "sich",
            "stadt",
            "und",
            "von",
            "weg",
            "zu",
            "über",
        }
    ),
    frozenset(
        {
            "al",
            "con",
            "como",
            "del",
            "desde",
            "el",
            "en",
            "es",
            "esta",
            "hacia",
            "la",
            "las",
            "los",
            "para",
            "por",
            "que",
            "ruta",
            "sin",
            "una",
            "uno",
            "y",
        }
    ),
    frozenset(
        {
            "au",
            "aux",
            "avec",
            "ce",
            "cette",
            "dans",
            "de",
            "des",
            "du",
            "en",
            "est",
            "et",
            "la",
            "le",
            "les",
            "mais",
            "par",
            "pour",
            "route",
            "sans",
            "une",
            "vers",
        }
    ),
    frozenset(
        {
            "al",
            "che",
            "con",
            "da",
            "dal",
            "della",
            "di",
            "e",
            "gli",
            "il",
            "in",
            "la",
            "le",
            "ma",
            "nel",
            "per",
            "senza",
            "una",
            "verso",
        }
    ),
    frozenset(
        {
            "aan",
            "als",
            "bij",
            "de",
            "door",
            "een",
            "en",
            "het",
            "in",
            "is",
            "maar",
            "met",
            "naar",
            "niet",
            "op",
            "uit",
            "van",
            "voor",
            "zonder",
        }
    ),
)


def is_likely_english(text: str) -> bool:
    """Apply a deterministic English-dominance check suitable for short game copy."""

    tokens = text_tokens(text)
    if not tokens or _has_non_latin_letters(text):
        return False
    english_score = sum(token in SAFE_COPY_TOKENS for token in tokens)
    required_score = 1 if len(tokens) <= 4 else 2
    if english_score < required_score:
        return False
    foreign_score = max(
        (
            sum(token in language and token not in SAFE_COPY_TOKENS for token in tokens)
            for language in NON_ENGLISH_EVIDENCE
        ),
        default=0,
    )
    return english_score > foreign_score


def _has_non_latin_letters(text: str) -> bool:
    for character in text:
        if not character.isalpha():
            continue
        name = unicodedata.name(character, "")
        if "LATIN" not in name:
            return True
    return False
