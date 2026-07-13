from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, cast

from .fact_grounding import FactGroundingError, validate_fact_grounding
from .language_validation import is_likely_english
from .models import ContentRequest, Fact
from .schema_validation import SchemaValidationError, validate_content_schema

EXPECTED_HINTS = {"compass", "lens", "map_fragment"}


class ContentValidationError(ValueError):
    """Raised when generated copy is unsafe or not grounded in its fact pack."""


def validate_content(payload: Mapping[str, Any], request: ContentRequest) -> None:
    try:
        validate_content_schema(payload)
    except SchemaValidationError as exc:
        raise ContentValidationError(str(exc)) from exc

    if set(payload) != {"hints", "explanations", "recap"}:
        raise ContentValidationError("content must have exactly hints, explanations, and recap")
    hints_value = payload.get("hints")
    explanations_value = payload.get("explanations")
    recap = payload.get("recap")
    if not isinstance(hints_value, list):
        raise ContentValidationError("content must contain exactly three hints")
    if not isinstance(explanations_value, list):
        raise ContentValidationError("explanations must be a list")
    hints = cast(list[Any], hints_value)
    explanations = cast(list[Any], explanations_value)
    if len(hints) != 3:
        raise ContentValidationError("content must contain exactly three hints")
    if not isinstance(recap, str) or not is_likely_english(recap):
        raise ContentValidationError("recap must be non-empty English text")
    _validate_grounded(
        recap,
        request.facts,
        context_values=(request.start_label, request.target_label, *request.target_aliases),
        derived_tokens=(str(len(request.facts)),),
        label="recap",
    )

    known_facts = {fact.id: fact for fact in request.facts}
    hint_kinds: set[str] = set()
    for hint in hints:
        if not isinstance(hint, dict):
            raise ContentValidationError("each hint has an invalid shape")
        hint_object = cast(dict[str, Any], hint)
        if set(hint_object) != {"kind", "text", "fact_ids"}:
            raise ContentValidationError("each hint has an invalid shape")
        kind = hint_object["kind"]
        text = hint_object["text"]
        fact_ids = hint_object["fact_ids"]
        if not isinstance(kind, str) or kind not in EXPECTED_HINTS:
            raise ContentValidationError("unknown hint kind")
        if kind in hint_kinds:
            raise ContentValidationError("hint kinds must be unique")
        hint_kinds.add(kind)
        if not isinstance(text, str) or not is_likely_english(text):
            raise ContentValidationError(f"{kind} hint must be concise English text")
        if _leaks_target(text, request):
            raise ContentValidationError(f"{kind} hint leaks the target")
        supporting_facts = _validate_fact_ids(fact_ids, known_facts)
        _validate_grounded(text, supporting_facts, label=f"{kind} hint")
    if hint_kinds != EXPECTED_HINTS:
        raise ContentValidationError("all three locked hint kinds are required")

    seen_explanations: set[str] = set()
    for explanation in explanations:
        if not isinstance(explanation, dict):
            raise ContentValidationError("each explanation has an invalid shape")
        explanation_object = cast(dict[str, Any], explanation)
        if set(explanation_object) != {"fact_id", "text"}:
            raise ContentValidationError("each explanation has an invalid shape")
        fact_id = explanation_object["fact_id"]
        text = explanation_object["text"]
        if not isinstance(fact_id, str) or fact_id not in known_facts:
            raise ContentValidationError("explanation references an unknown fact")
        if fact_id in seen_explanations:
            raise ContentValidationError("a fact may be explained only once")
        seen_explanations.add(fact_id)
        if not isinstance(text, str) or not is_likely_english(text):
            raise ContentValidationError("explanation must be concise English text")
        _validate_grounded(text, (known_facts[fact_id],), label="explanation")


def _validate_fact_ids(value: Any, known_facts: Mapping[str, Fact]) -> tuple[Fact, ...]:
    if not isinstance(value, list) or not value:
        raise ContentValidationError("hint fact_ids must be a non-empty string list")
    items = cast(list[Any], value)
    if any(not isinstance(item, str) for item in items):
        raise ContentValidationError("hint fact_ids must be a non-empty string list")
    fact_ids = cast(list[str], items)
    if not set(fact_ids).issubset(known_facts):
        raise ContentValidationError("hint references an unknown fact")
    return tuple(known_facts[fact_id] for fact_id in fact_ids)


def _validate_grounded(
    text: str,
    facts: tuple[Fact, ...],
    *,
    label: str,
    context_values: tuple[str, ...] = (),
    derived_tokens: tuple[str, ...] = (),
) -> None:
    try:
        validate_fact_grounding(
            text,
            facts,
            context_values=context_values,
            derived_tokens=derived_tokens,
        )
    except FactGroundingError as exc:
        raise ContentValidationError(f"{label} is not fact-grounded: {exc}") from exc


def _leaks_target(text: str, request: ContentRequest) -> bool:
    aliases = (request.target_label, *request.target_aliases)
    normalized = " ".join(text.casefold().split())
    for alias in aliases:
        candidate = " ".join(alias.casefold().split())
        if len(candidate) >= 3 and re.search(rf"(?<!\w){re.escape(candidate)}(?!\w)", normalized):
            return True
    return False
