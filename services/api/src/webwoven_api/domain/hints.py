"""Deterministic, graph-grounded hint selection."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from webwoven_api.domain.errors import DomainError


class HintType(StrEnum):
    COMPASS = "compass"
    LENS = "lens"
    MAP_FRAGMENT = "map_fragment"


class HintOutcome(StrEnum):
    PROMISING = "promising"
    LONGER = "longer"
    DEAD_END = "dead_end"


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
    outcome: HintOutcome | None = None


def select_hint(
    hint_type: HintType,
    candidates: Iterable[HintCandidate],
    *,
    selected_relation_key: str | None = None,
    selected_entity_id: str | None = None,
) -> HintResult:
    """Choose a hint using only precomputed graph distances and stable sorting."""
    available = tuple(candidates)
    if hint_type is HintType.COMPASS:
        if selected_relation_key is None or selected_entity_id is None:
            raise DomainError("route_required", "Choose a specific route for the Compass.")
        selected = next(
            (
                candidate
                for candidate in available
                if candidate.relation_key == selected_relation_key
                and candidate.entity_id == selected_entity_id
            ),
            None,
        )
        if selected is None:
            raise DomainError("hint_unavailable", "That route is no longer available.")
        reachable = tuple(candidate for candidate in available if candidate.distance is not None)
        best = min(reachable, key=_candidate_sort_key) if reachable else None
        if selected.distance is None:
            outcome = HintOutcome.DEAD_END
            message = f"Compass: {selected.entity_label} is a dead end from here."
        elif best is not None and selected.distance == best.distance:
            outcome = HintOutcome.PROMISING
            message = f"Compass: {selected.entity_label} is a promising route."
        else:
            outcome = HintOutcome.LONGER
            message = f"Compass: {selected.entity_label} takes a longer route."
        return HintResult(
            hint_type=hint_type,
            penalty=HINT_PENALTIES[hint_type],
            relation_key=selected.relation_key,
            entity_id=selected.entity_id,
            message=message,
            outcome=outcome,
        )

    reachable = tuple(candidate for candidate in available if candidate.distance is not None)
    if not reachable:
        raise DomainError("hint_unavailable", "No grounded hint is available from this entity.")
    best = min(reachable, key=_candidate_sort_key)

    if hint_type is HintType.LENS:
        return HintResult(
            hint_type=hint_type,
            penalty=HINT_PENALTIES[hint_type],
            relation_key=best.relation_key,
            entity_id=best.entity_id,
            message=f"Lens: {best.entity_label} is on a near-optimal route.",
            outcome=HintOutcome.PROMISING,
        )

    return HintResult(
        hint_type=hint_type,
        penalty=HINT_PENALTIES[hint_type],
        relation_key=best.relation_key,
        entity_id=best.entity_id,
        message=f"Map Fragment: {best.entity_label} is a valid bridge ahead.",
        outcome=HintOutcome.PROMISING,
    )


def _candidate_sort_key(candidate: HintCandidate) -> tuple[int, str, str]:
    assert candidate.distance is not None
    return (candidate.distance, candidate.relation_key, candidate.entity_id)
