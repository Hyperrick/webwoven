from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Mapping

from .models import Edge, Entity
from .relation_semantics import (
    RelationEntityProfile,
    is_award,
    is_language,
    is_organization,
    is_place,
    is_ranked_selection,
    is_recognition,
)
from .relation_sentences import format_relation_sentence

_AWARD_WORDING = re.compile(
    r"\b(?:"
    r"receiv(?:e|es|ed|ing)|win|wins|won|"
    r"award(?:s|ed|ing)|grant(?:s|ed|ing)|honou?r(?:s|ed|ing)"
    r")\b",
    re.IGNORECASE,
)
_PHYSICAL_PLACE_WORDING = re.compile(
    r"\b(?:is|are|was|were|lies?|located|situated)\s+(?:directly\s+)?(?:in|at|within)\b",
    re.IGNORECASE,
)
_LANGUAGE_COUNTRY_WORDING = re.compile(r"\b(?:is|are|was|were)\s+used\s+in\b", re.IGNORECASE)
_ORGANIZATION_COUNTRY_WORDING = re.compile(r"\b(?:is|are|was|were)\s+based\s+in\b", re.IGNORECASE)
_SENTENCE_END = re.compile(r"[.!?][\"'’”)]?$", re.UNICODE)
_DUPLICATE_SENTENCE_END = re.compile(r"[.!?]{2,}[\"'’”)]?$", re.UNICODE)
_FIXTURE_EXPLANATION_PREFIX = "Fictional fixture fact: "


def relationship_explanation_issue(
    edge: Edge,
    entities_by_id: Mapping[str, Entity],
) -> str | None:
    """Return a semantic wording issue for a compiled relationship, if one exists."""
    explanation = edge.explanation
    if explanation != explanation.strip():
        return "has leading or trailing whitespace"
    if "\n" in explanation or "\r" in explanation:
        return "must be a single line"
    if any(unicodedata.category(character) == "Cf" for character in explanation):
        return "contains invisible formatting characters"
    if not _SENTENCE_END.search(explanation):
        return "must be a complete sentence ending in punctuation"
    if _DUPLICATE_SENTENCE_END.search(explanation):
        return "has duplicated terminal punctuation"

    subject, object_value = _statement_entities(edge, entities_by_id)
    relation_prose, missing_entity_issue = _without_entity_labels(
        explanation,
        ("subject", subject),
        ("object", object_value),
    )
    if missing_entity_issue is not None:
        return missing_entity_issue
    if edge.relation_key == "P166" and not is_recognition(_profile(object_value)):
        return (
            f"lacks semantic recognition evidence for {object_value.label!r}; "
            "provide award, ranked_selection, or recognition"
        )
    if (
        edge.relation_key == "P166"
        and is_ranked_selection(_profile(object_value))
        and _AWARD_WORDING.search(relation_prose)
    ):
        return (
            f"uses award wording for ranked selection {object_value.label!r}; "
            "use ranking or inclusion wording"
        )
    if (
        edge.relation_key == "P166"
        and not is_award(_profile(object_value))
        and _AWARD_WORDING.search(relation_prose)
    ):
        return (
            f"uses award wording without award evidence for {object_value.label!r}; "
            "use neutral recognition wording"
        )
    if (
        edge.relation_key == "P17"
        and not is_language(_profile(subject))
        and _LANGUAGE_COUNTRY_WORDING.search(relation_prose)
    ):
        return f"uses language wording for non-language subject {subject.label!r}"
    if (
        edge.relation_key == "P17"
        and not is_organization(_profile(subject))
        and _ORGANIZATION_COUNTRY_WORDING.search(relation_prose)
    ):
        return f"uses organization wording for non-organization subject {subject.label!r}"
    if (
        edge.relation_key == "P17"
        and not is_place(_profile(subject))
        and _PHYSICAL_PLACE_WORDING.search(relation_prose)
    ):
        return (
            f"uses physical-place wording for non-place subject {subject.label!r}; "
            "describe the country relationship semantically"
        )
    if edge.relation_key in {"P17", "P166"}:
        expected = format_relation_sentence(
            edge.relation_key,
            _profile(entities_by_id[edge.source_id]),
            _profile(entities_by_id[edge.target_id]),
            inverse=edge.inverse,
            series_ordinal=edge.series_ordinal,
        )
        actual = explanation.removeprefix(_FIXTURE_EXPLANATION_PREFIX)
        if actual != expected:
            return f"does not use canonical {edge.relation_key} wording; expected {expected!r}"
    return None


def relationship_pairing_issue(edges: tuple[Edge, ...]) -> str | None:
    """Require inverse navigation copies of one source fact to preserve identical prose."""
    groups: dict[tuple[str, str], list[Edge]] = defaultdict(list)
    for edge in edges:
        groups[(edge.statement_id, edge.relation_key)].append(edge)
    for (statement_id, relation_key), group in sorted(groups.items()):
        if len(group) == 1:
            continue
        if len(group) != 2:
            return f"{statement_id}/{relation_key} has {len(group)} navigation edges"
        first, second = group
        if (
            first.source_id != second.target_id
            or first.target_id != second.source_id
            or first.inverse == second.inverse
        ):
            return f"{statement_id}/{relation_key} does not form one forward/inverse pair"
        if first.explanation != second.explanation:
            return f"{statement_id}/{relation_key} changes explanation by direction"
        if first.series_ordinal != second.series_ordinal:
            return f"{statement_id}/{relation_key} changes qualifiers by direction"
        if first.playable != second.playable:
            return f"{statement_id}/{relation_key} changes playability by direction"
    return None


def _statement_entities(
    edge: Edge,
    entities_by_id: Mapping[str, Entity],
) -> tuple[Entity, Entity]:
    if edge.inverse:
        return entities_by_id[edge.target_id], entities_by_id[edge.source_id]
    return entities_by_id[edge.source_id], entities_by_id[edge.target_id]


def _without_entity_labels(
    explanation: str,
    *entities: tuple[str, Entity],
) -> tuple[str, str | None]:
    """Remove one endpoint mention each and report missing statement endpoints."""
    prose = explanation
    ordered = sorted(entities, key=lambda item: len(item[1].label), reverse=True)
    for role, entity in ordered:
        prose, replacements = re.subn(
            rf"(?<!\w){re.escape(entity.label)}(?!\w)",
            " ",
            prose,
            count=1,
            flags=re.IGNORECASE,
        )
        if replacements == 0:
            return prose, f"does not mention statement {role} {entity.label!r}"
    return prose, None


def _profile(entity: Entity) -> RelationEntityProfile:
    return RelationEntityProfile(
        label=entity.label,
        description=entity.description,
        semantic_tags=frozenset(entity.semantic_tags),
    )
