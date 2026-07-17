from __future__ import annotations

import re
from dataclasses import dataclass

_LANGUAGE_CLASS_IDS = frozenset({"Q33742", "Q34770"})
_AWARD_CLASS_IDS = frozenset({"Q378427", "Q618779", "Q38033430"})
_RANKED_SELECTION_CLASS_IDS = frozenset(
    {
        "Q49958",  # opinion poll
        "Q12139612",  # list
        "Q13406463",  # Wikimedia list article
    }
)
_PLACE_CLASS_IDS = frozenset(
    {
        "Q515",  # city
        "Q6256",  # country
        "Q82794",  # geographic region
        "Q486972",  # human settlement
        "Q618123",  # geographical object
    }
)
_ORGANIZATION_CLASS_IDS = frozenset(
    {
        "Q3918",  # university
        "Q43229",  # organization
        "Q4830453",  # business
        "Q2385804",  # educational institution
    }
)

_RANKED_SELECTION_LABEL_WORDING = re.compile(
    r"(?:"
    r"\btop\s+(?:\d+|ten|twenty|fifty|hundred)\b|"
    r"\b\d+\s+(?:best|greatest|favorite|favourite)\b|"
    r"\b\d+\s+(?:(?:[a-z]+[ -]?){0,2})"
    r"(?:books?|films?|novels?|albums?|songs?|artists?|players?|people|women|men|works?)\b"
    r")",
    re.IGNORECASE,
)
_RANKED_SELECTION_DESCRIPTION_WORDING = re.compile(
    r"(?:"
    r"\b(?:wikimedia|selected|ranked|curated)\s+list(?:\s+article)?\b|"
    r"\bannual\s+listing\b|"
    r"\bopinion\s+poll\b|"
    r"\bbased\s+on\s+(?:public|reader|readers)\s+votes?\b"
    r")",
    re.IGNORECASE,
)
_AWARD_WORDING = re.compile(
    r"\b(?:award|awards|prize|prizes|medal|medals|honor|honors|honour|honours)\b",
    re.IGNORECASE,
)
SEMANTIC_TAG_AWARD = "award"
SEMANTIC_TAG_LANGUAGE = "language"
SEMANTIC_TAG_ORGANIZATION = "organization"
SEMANTIC_TAG_PLACE = "place"
SEMANTIC_TAG_RANKED_SELECTION = "ranked_selection"
SEMANTIC_TAG_RECOGNITION = "recognition"
KNOWN_SEMANTIC_TAGS = frozenset(
    {
        SEMANTIC_TAG_AWARD,
        SEMANTIC_TAG_LANGUAGE,
        SEMANTIC_TAG_ORGANIZATION,
        SEMANTIC_TAG_PLACE,
        SEMANTIC_TAG_RANKED_SELECTION,
        SEMANTIC_TAG_RECOGNITION,
    }
)


@dataclass(frozen=True, slots=True)
class RelationEntityProfile:
    """Small, source-neutral semantic view used to verbalize relationships."""

    label: str
    description: str = ""
    classification_ids: frozenset[str] = frozenset()
    semantic_tags: frozenset[str] = frozenset()


def is_ranked_selection(entity: RelationEntityProfile) -> bool:
    return bool(
        SEMANTIC_TAG_RANKED_SELECTION in entity.semantic_tags
        or entity.classification_ids & _RANKED_SELECTION_CLASS_IDS
        or _RANKED_SELECTION_LABEL_WORDING.search(entity.label)
        or _RANKED_SELECTION_DESCRIPTION_WORDING.search(entity.description)
    )


def is_award(entity: RelationEntityProfile) -> bool:
    return bool(
        SEMANTIC_TAG_AWARD in entity.semantic_tags
        or entity.classification_ids & _AWARD_CLASS_IDS
        or _AWARD_WORDING.search(_semantic_text(entity))
    )


def is_language(entity: RelationEntityProfile) -> bool:
    return bool(
        SEMANTIC_TAG_LANGUAGE in entity.semantic_tags
        or entity.classification_ids & _LANGUAGE_CLASS_IDS
    )


def is_place(entity: RelationEntityProfile) -> bool:
    return bool(
        SEMANTIC_TAG_PLACE in entity.semantic_tags or entity.classification_ids & _PLACE_CLASS_IDS
    )


def is_organization(entity: RelationEntityProfile) -> bool:
    return bool(
        SEMANTIC_TAG_ORGANIZATION in entity.semantic_tags
        or entity.classification_ids & _ORGANIZATION_CLASS_IDS
    )


def is_recognition(entity: RelationEntityProfile) -> bool:
    return bool(
        SEMANTIC_TAG_RECOGNITION in entity.semantic_tags
        or is_award(entity)
        or is_ranked_selection(entity)
    )


def _semantic_text(entity: RelationEntityProfile) -> str:
    return " ".join((entity.label, entity.description))


def semantic_tags_for_profile(entity: RelationEntityProfile) -> frozenset[str]:
    """Collapse provider-specific evidence into stable source-neutral semantic tags."""
    tags = set(entity.semantic_tags & KNOWN_SEMANTIC_TAGS)
    if is_ranked_selection(entity):
        tags.add(SEMANTIC_TAG_RANKED_SELECTION)
    if is_award(entity):
        tags.add(SEMANTIC_TAG_AWARD)
    if is_language(entity):
        tags.add(SEMANTIC_TAG_LANGUAGE)
    if is_place(entity):
        tags.add(SEMANTIC_TAG_PLACE)
    if is_organization(entity):
        tags.add(SEMANTIC_TAG_ORGANIZATION)
    return frozenset(tags)
