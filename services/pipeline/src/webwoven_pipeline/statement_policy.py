"""Shared policy for turning qualified Wikidata statements into present-tense game facts."""

from collections.abc import Iterable
from typing import Any, cast

END_TIME_PROPERTY = "P582"


def eligible_statements(values: Iterable[Any]) -> tuple[dict[str, Any], ...]:
    """Return current best-rank statements whose wording is safe without qualifiers."""
    current: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        statement = cast(dict[str, Any], value)
        if statement.get("rank") == "deprecated" or _has_end_time(statement):
            continue
        current.append(statement)
    preferred = tuple(item for item in current if item.get("rank") == "preferred")
    return preferred or tuple(current)


def _has_end_time(statement: dict[str, Any]) -> bool:
    qualifiers = statement.get("qualifiers")
    if not isinstance(qualifiers, dict):
        return False
    end_times = cast(dict[str, Any], qualifiers).get(END_TIME_PROPERTY)
    return isinstance(end_times, list) and len(cast(list[Any], end_times)) > 0
