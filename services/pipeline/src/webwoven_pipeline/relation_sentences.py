from __future__ import annotations

import re
from typing import Final

from .relation_semantics import (
    RelationEntityProfile,
    is_award,
    is_language,
    is_organization,
    is_place,
    is_ranked_selection,
    is_recognition,
)

# Templates receive labels in navigation order: source is the current entity and
# target is the reachable entity. Inverse templates restore the underlying fact's
# natural subject/object order instead of exposing database relation vocabulary.
_RELATION_SENTENCES: Final[dict[str, tuple[str, str]]] = {
    "P19": (
        "{source} was born in {target}.",
        "{target} was born in {source}.",
    ),
    "P36": (
        "{target} is the capital of {source}.",
        "{source} is the capital of {target}.",
    ),
    "P50": (
        "{source} was written by {target}.",
        "{target} was written by {source}.",
    ),
    "P57": (
        "{source} was directed by {target}.",
        "{target} was directed by {source}.",
    ),
    "P61": (
        "{source} was discovered or invented by {target}.",
        "{target} was discovered or invented by {source}.",
    ),
    "P69": (
        "{source} studied at {target}.",
        "{target} studied at {source}.",
    ),
    "P108": (
        "{source} worked for {target}.",
        "{target} worked for {source}.",
    ),
    "P131": (
        "{source} is located in {target}.",
        "{target} is located in {source}.",
    ),
    "P138": (
        "{source} was named after {target}.",
        "{target} was named after {source}.",
    ),
    "P161": (
        "{target} appeared in the cast of {source}.",
        "{source} appeared in the cast of {target}.",
    ),
    "P170": (
        "{source} was created by {target}.",
        "{target} was created by {source}.",
    ),
    "P171": (
        "{source} is classified directly under {target}.",
        "{target} is classified directly under {source}.",
    ),
    "P175": (
        "{source} was performed by {target}.",
        "{target} was performed by {source}.",
    ),
    "P276": (
        "{source} is located at {target}.",
        "{target} is located at {source}.",
    ),
    "P361": (
        "{source} is part of {target}.",
        "{target} is part of {source}.",
    ),
    "P463": (
        "{source} is a member of {target}.",
        "{target} is a member of {source}.",
    ),
    "P737": (
        "{source} was influenced by {target}.",
        "{target} was influenced by {source}.",
    ),
    "P800": (
        "{target} is a notable work by {source}.",
        "{source} is a notable work by {target}.",
    ),
}

_PLAIN_RANK = re.compile(r"\d+")
_COUNTRIES_WITH_ARTICLE: Final[frozenset[str]] = frozenset(
    {
        "Bahamas",
        "Czech Republic",
        "Dominican Republic",
        "Gambia",
        "Maldives",
        "Marshall Islands",
        "Netherlands",
        "Philippines",
        "Seychelles",
        "Solomon Islands",
        "United Arab Emirates",
        "United Kingdom",
        "United States",
    }
)
_COUNTRY_ARTICLE_PREFIXES: Final[tuple[str, ...]] = (
    "Commonwealth of ",
    "Democratic Republic of ",
    "Federated States of ",
    "Kingdom of ",
    "People's Republic of ",
    "Principality of ",
    "Republic of ",
    "Sultanate of ",
    "United ",
)
_COUNTRY_ARTICLE_SUFFIXES: Final[tuple[str, ...]] = (
    " Democratic Republic",
    " Empire",
    " Kingdom",
    " Republic",
    " States",
    " Union",
)


def format_relation_sentence(
    relation_key: str,
    source: str | RelationEntityProfile,
    target: str | RelationEntityProfile,
    *,
    inverse: bool,
    series_ordinal: str | None = None,
) -> str:
    """Describe one navigable edge as a complete fact-grounded English sentence."""
    source_entity = _as_profile(source)
    target_entity = _as_profile(target)
    subject, object_value = (
        (target_entity, source_entity) if inverse else (source_entity, target_entity)
    )
    if relation_key == "P17":
        sentence = _format_country_relationship(subject, object_value)
    elif relation_key == "P166":
        sentence = _format_recognition_relationship(subject, object_value, series_ordinal)
    else:
        templates = _RELATION_SENTENCES.get(relation_key)
        if templates is None:
            sentence = (
                f"{source_entity.label} has a documented connection to {target_entity.label}."
            )
        else:
            template = templates[1 if inverse else 0]
            sentence = template.format(
                source=source_entity.label,
                target=target_entity.label,
            )
    return _remove_appended_punctuation(sentence)


def _format_country_relationship(
    subject: RelationEntityProfile,
    country: RelationEntityProfile,
) -> str:
    country_label = _country_label(country.label)
    if is_language(subject):
        return f"{subject.label} is used in {country_label}."
    if is_recognition(subject):
        return f"{subject.label} is associated with {country_label}."
    if is_organization(subject):
        return f"{subject.label} is based in {country_label}."
    if is_place(subject):
        return f"{subject.label} is in {country_label}."
    return f"{subject.label} is associated with {country_label}."


def _format_recognition_relationship(
    subject: RelationEntityProfile,
    recognition: RelationEntityProfile,
    series_ordinal: str | None,
) -> str:
    if is_ranked_selection(recognition):
        selection = _selection_label(recognition.label)
        rank = _rank_label(series_ordinal)
        if rank is not None:
            return f"{subject.label} ranked {rank} on {selection}."
        return f"{subject.label} was included in {selection}."
    if is_award(recognition):
        return f"{subject.label} received {_definite_label(recognition.label)}."
    return (
        f"{subject.label} has a recorded recognition connection to "
        f"{_definite_label(recognition.label)}."
    )


def _as_profile(value: str | RelationEntityProfile) -> RelationEntityProfile:
    return value if isinstance(value, RelationEntityProfile) else RelationEntityProfile(value)


def _rank_label(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > 32:
        return None
    return f"#{normalized}" if _PLAIN_RANK.fullmatch(normalized) else normalized


def _definite_label(label: str) -> str:
    return label if label.casefold().startswith("the ") else f"the {label}"


def _selection_label(label: str) -> str:
    first_words = " ".join(label.split()[:3])
    if re.search(r"(?:['’]s\b|s['’](?:\s|$))", first_words, re.IGNORECASE):
        return label
    return _definite_label(label)


def _country_label(label: str) -> str:
    if (
        label.casefold().startswith("the ")
        or label in _COUNTRIES_WITH_ARTICLE
        or label.startswith(_COUNTRY_ARTICLE_PREFIXES)
        or label.endswith(_COUNTRY_ARTICLE_SUFFIXES)
    ):
        return _definite_label(label)
    return label


def _remove_appended_punctuation(sentence: str) -> str:
    if len(sentence) > 1 and sentence.endswith(".") and sentence[-2] in ".!?":
        return sentence[:-1]
    return sentence
