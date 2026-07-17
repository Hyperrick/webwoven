"""Small immutable graph adapter used by tests and graph-missing development."""

from dataclasses import dataclass

from webwoven_api.domain.scoring import TIME_WINDOWS, Difficulty
from webwoven_api.graph.contracts import Entity, GraphEdge, RelationDirection, Round


@dataclass(frozen=True, slots=True)
class MemoryGraphReader:
    entities: dict[str, Entity]
    edges: tuple[GraphEdge, ...]
    rounds: tuple[Round, ...]
    distances: dict[tuple[str, str], int]
    version: str = "demo-v1"

    @property
    def graph_version(self) -> str:
        return self.version

    def is_healthy(self) -> bool:
        return bool(self.entities and self.rounds)

    def get_entity(self, entity_id: str) -> Entity | None:
        return self.entities.get(entity_id)

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        return next((edge for edge in self.edges if edge.id == edge_id), None)

    def get_edges(self, source_id: str) -> tuple[GraphEdge, ...]:
        return tuple(edge for edge in self.edges if edge.source_id == source_id)

    def get_round(self, round_id: str) -> Round | None:
        return next((round_ for round_ in self.rounds if round_.id == round_id), None)

    def list_published_rounds(
        self,
        *,
        category: str | None = None,
        difficulty: Difficulty | None = None,
    ) -> tuple[Round, ...]:
        return tuple(
            round_
            for round_ in self.rounds
            if round_.published
            and (category is None or round_.category == category)
            and (difficulty is None or round_.difficulty is difficulty)
        )

    def distance_to_target(self, round_id: str, entity_id: str) -> int | None:
        return self.distances.get((round_id, entity_id))

    def distances_to_target(self, round_id: str, entity_ids: tuple[str, ...]) -> dict[str, int]:
        return {
            entity_id: distance
            for entity_id in entity_ids
            if (distance := self.distances.get((round_id, entity_id))) is not None
        }

    @classmethod
    def demo(cls) -> "MemoryGraphReader":
        """Return a deterministic graph for the explicit testing environment."""
        entities = {
            "Q1": Entity("Q1", "Ada Lovelace", "English mathematician", "person", "people"),
            "Q2": Entity("Q2", "Charles Babbage", "English polymath", "person", "people"),
            "Q3": Entity(
                "Q3",
                "Analytical Engine",
                "Mechanical computer",
                "work",
                "science_technology",
            ),
            "Q4": Entity("Q4", "Computer", "Programmable machine", "concept", "science_technology"),
            "Q5": Entity(
                "Q5", "London", "Capital of the United Kingdom", "place", "places_architecture"
            ),
        }
        edge_data: tuple[
            tuple[str, str, str, str, str, str, RelationDirection],
            ...,
        ] = (
            (
                "edge-1",
                "Q1",
                "Q2",
                "P737",
                "influenced by",
                "Ada Lovelace was influenced by Charles Babbage.",
                "outgoing",
            ),
            (
                "edge-2",
                "Q2",
                "Q3",
                "P170",
                "creator of",
                "The Analytical Engine was created by Charles Babbage.",
                "incoming",
            ),
            (
                "edge-3",
                "Q3",
                "Q4",
                "P361",
                "part of",
                "The Analytical Engine is part of the history of the computer.",
                "outgoing",
            ),
            (
                "edge-4",
                "Q1",
                "Q5",
                "P19",
                "place of birth",
                "Ada Lovelace was born in London.",
                "outgoing",
            ),
            (
                "edge-5",
                "Q5",
                "Q4",
                "P361",
                "computing history",
                "London is part of the history of the computer.",
                "outgoing",
            ),
            (
                "edge-6",
                "Q2",
                "Q1",
                "P737",
                "influenced by",
                "Charles Babbage was influenced by Ada Lovelace.",
                "outgoing",
            ),
        )
        edges = tuple(
            GraphEdge(
                id=edge_id,
                source_id=source,
                target_id=target,
                relation_key=relation,
                relation_label=label,
                statement_id=f"demo-{edge_id}",
                explanation=explanation,
                target=entities[target],
                direction=direction,
            )
            for edge_id, source, target, relation, label, explanation, direction in edge_data
        )
        rounds = tuple(
            Round(
                id=f"demo-history-{difficulty.value}-{index}",
                start_id="Q1",
                target_id="Q4",
                category="people",
                difficulty=difficulty,
                optimal_distance=3,
                time_window=TIME_WINDOWS[difficulty],
                published=True,
            )
            for difficulty in Difficulty
            for index in (1, 2)
        )
        distances = {
            (round_.id, qid): distance
            for round_ in rounds
            for qid, distance in {"Q1": 3, "Q2": 2, "Q3": 1, "Q4": 0, "Q5": 1}.items()
        }
        return cls(entities=entities, edges=edges, rounds=rounds, distances=distances)
