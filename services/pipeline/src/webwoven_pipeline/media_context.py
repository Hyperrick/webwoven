from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from .models import Edge

_RELATION_PRIORITY = {
    "P170": 0,
    "P50": 1,
    "P138": 2,
    "P361": 3,
    "P166": 4,
    "P161": 5,
    "P800": 6,
    "P276": 7,
    "P69": 8,
    "P19": 9,
    "P108": 10,
    "P463": 11,
    "P131": 12,
    "P17": 13,
}


@dataclass(frozen=True, slots=True)
class MediaContextHint:
    entity_id: str
    label: str
    relation_key: str


@dataclass(frozen=True, slots=True)
class MediaContextCandidate:
    file_name: str
    provenance: str


def selected_neighbor_media_candidates(
    entity_ids: Iterable[str],
    context_by_qid: Mapping[str, tuple[MediaContextHint, ...]],
    selected_files_by_qid: Mapping[str, str],
) -> dict[str, tuple[MediaContextCandidate, ...]]:
    """Use an exact image from a documented graph neighbor as a safe fallback."""
    results: dict[str, tuple[MediaContextCandidate, ...]] = {}
    for qid in sorted(set(entity_ids), key=_qid_number):
        candidates = tuple(
            MediaContextCandidate(
                file_name,
                f"graph_context:{hint.relation_key}:{hint.entity_id}:{hint.label}",
            )
            for hint in context_by_qid.get(qid, ())
            if (file_name := selected_files_by_qid.get(hint.entity_id)) is not None
        )
        if candidates:
            results[qid] = candidates
    return results


def build_media_context_hints(
    entity_ids: Iterable[str],
    labels_by_qid: Mapping[str, str],
    edges: Iterable[Edge],
    *,
    max_hints: int = 3,
) -> dict[str, tuple[MediaContextHint, ...]]:
    """Rank exact graph neighbors that can provide contextual documentary media."""
    requested = set(entity_ids)
    hints: dict[str, dict[str, MediaContextHint]] = {qid: {} for qid in requested}
    for edge in edges:
        for qid, neighbor_id in (
            (edge.source_id, edge.target_id),
            (edge.target_id, edge.source_id),
        ):
            label = labels_by_qid.get(neighbor_id)
            if qid not in requested or not label or neighbor_id == qid:
                continue
            hints[qid][neighbor_id] = MediaContextHint(
                neighbor_id,
                label,
                edge.relation_key,
            )
    return {
        qid: tuple(
            sorted(
                values.values(),
                key=lambda hint: (
                    _RELATION_PRIORITY.get(hint.relation_key, 99),
                    hint.label.casefold(),
                    hint.entity_id,
                ),
            )[:max_hints]
        )
        for qid, values in sorted(hints.items())
        if values
    }


def _qid_number(value: str) -> int:
    if len(value) < 2 or value[0] != "Q" or not value[1:].isdigit():
        raise ValueError(f"invalid QID: {value}")
    return int(value[1:])
