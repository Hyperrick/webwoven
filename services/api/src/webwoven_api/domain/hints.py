"""Deterministic, graph-grounded hint selection."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from webwoven_api.domain.errors import DomainError


class HintType(StrEnum):
    COMPASS = "compass"
    LENS = "lens"
    MAP_FRAGMENT = "map_fragment"


HINT_PENALTIES: dict[HintType, int] = {
    HintType.COMPASS: 75,
    HintType.LENS: 150,
    HintType.MAP_FRAGMENT: 250,
}


@dataclass(frozen=True, slots=True)
class HintCandidate:
    relation_key: str
    entity_id: str
    entity_label: str
    distance: int | None


@dataclass(frozen=True, slots=True)
class HintResult:
    hint_type: HintType
    penalty: int
    relation_key: str | None
    entity_id: str | None
    message: str


def select_hint(
    hint_type: HintType,
    candidates: Iterable[HintCandidate],
    *,
    selected_relation_key: str | None = None,
) -> HintResult:
    """Choose a hint using only precomputed graph distances and stable sorting."""
    available = tuple(candidates)
    reachable = tuple(candidate for candidate in available if candidate.distance is not None)
    if not reachable:
        raise DomainError("hint_unavailable", "No grounded hint is available from this entity.")
    best = min(reachable, key=_candidate_sort_key)

    if hint_type is HintType.COMPASS:
        if selected_relation_key is None:
            raise DomainError("relation_required", "Choose a relationship group for the Compass.")
        in_group = tuple(
            candidate for candidate in reachable if candidate.relation_key == selected_relation_key
        )
        promising = (
            bool(in_group) and min(in_group, key=_candidate_sort_key).distance == best.distance
        )
        direction = "promising" if promising else "unlikely to shorten this route"
        return HintResult(
            hint_type=hint_type,
            penalty=HINT_PENALTIES[hint_type],
            relation_key=selected_relation_key,
            entity_id=None,
            message=f"Compass: that kind of connection looks {direction}.",
        )

    if hint_type is HintType.LENS:
        return HintResult(
            hint_type=hint_type,
            penalty=HINT_PENALTIES[hint_type],
            relation_key=best.relation_key,
            entity_id=None,
            message="Lens: a connection on a near-optimal route is now marked.",
        )

    return HintResult(
        hint_type=hint_type,
        penalty=HINT_PENALTIES[hint_type],
        relation_key=best.relation_key,
        entity_id=best.entity_id,
        message=f"Map Fragment: {best.entity_label} is a valid bridge ahead.",
    )


def _candidate_sort_key(candidate: HintCandidate) -> tuple[int, str, str]:
    assert candidate.distance is not None
    return (candidate.distance, candidate.relation_key, candidate.entity_id)
