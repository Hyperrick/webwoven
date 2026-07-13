"""Immutable records of the choices visible when a navigation move was made."""

from dataclasses import dataclass
from enum import StrEnum


class DecisionAction(StrEnum):
    FOLLOW = "follow"
    BACK = "back"


@dataclass(frozen=True, slots=True)
class DecisionFrame:
    """One resolved frontier; edge IDs are pinned to the session graph build."""

    source_id: str
    destination_id: str
    action: DecisionAction
    visible_edge_ids: tuple[str, ...]
    selected_edge_id: str | None = None


def followed_frame(
    *,
    source_id: str,
    destination_id: str,
    visible_edge_ids: tuple[str, ...],
    selected_edge_id: str,
) -> DecisionFrame:
    if selected_edge_id not in visible_edge_ids:
        raise ValueError("selected_edge_id must belong to the visible frontier")
    return DecisionFrame(
        source_id=source_id,
        destination_id=destination_id,
        action=DecisionAction.FOLLOW,
        visible_edge_ids=visible_edge_ids,
        selected_edge_id=selected_edge_id,
    )


def backed_frame(
    *,
    source_id: str,
    destination_id: str,
    visible_edge_ids: tuple[str, ...],
) -> DecisionFrame:
    return DecisionFrame(
        source_id=source_id,
        destination_id=destination_id,
        action=DecisionAction.BACK,
        visible_edge_ids=visible_edge_ids,
    )
