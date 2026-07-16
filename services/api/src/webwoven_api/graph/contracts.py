"""Stable graph types consumed by gameplay domains."""

from dataclasses import dataclass
from typing import Literal, Protocol

from webwoven_api.domain.scoring import Difficulty


@dataclass(frozen=True, slots=True)
class Entity:
    id: str
    label: str
    description: str | None
    entity_type: str
    category: str
    image_path: str | None = None
    image_attribution_json: str | None = None
    wikipedia_url: str | None = None


@dataclass(frozen=True, slots=True)
class Relation:
    key: str
    forward_label: str
    inverse_label: str
    category: str


RelationDirection = Literal["outgoing", "incoming"]


@dataclass(frozen=True, slots=True)
class GraphEdge:
    id: str
    source_id: str
    target_id: str
    relation_key: str
    relation_label: str
    statement_id: str
    explanation: str
    target: Entity
    direction: RelationDirection = "outgoing"


@dataclass(frozen=True, slots=True)
class Round:
    id: str
    start_id: str
    target_id: str
    category: str
    difficulty: Difficulty
    optimal_distance: int
    time_window: int
    published: bool


class GraphReader(Protocol):
    """Read-only boundary around a pinned graph bundle."""

    @property
    def graph_version(self) -> str: ...

    def is_healthy(self) -> bool: ...

    def get_entity(self, entity_id: str) -> Entity | None: ...

    def get_edge(self, edge_id: str) -> GraphEdge | None: ...

    def get_edges(self, source_id: str) -> tuple[GraphEdge, ...]: ...

    def get_round(self, round_id: str) -> Round | None: ...

    def list_published_rounds(
        self,
        *,
        category: str | None = None,
        difficulty: Difficulty | None = None,
    ) -> tuple[Round, ...]: ...

    def distance_to_target(self, round_id: str, entity_id: str) -> int | None: ...

    def distances_to_target(self, round_id: str, entity_ids: tuple[str, ...]) -> dict[str, int]: ...
