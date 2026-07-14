"""Small immutable graph adapter used by tests and graph-missing development."""

from dataclasses import dataclass

from webwoven_api.domain.scoring import TIME_WINDOWS, Difficulty
from webwoven_api.graph.contracts import Entity, GraphEdge, Round


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
            "Q1": Entity("Q1", "Ada Lovelace", "English mathematician", "person", "history"),
            "Q2": Entity("Q2", "Charles Babbage", "English polymath", "person", "history"),
            "Q3": Entity("Q3", "Analytical Engine", "Mechanical computer", "work", "science"),
            "Q4": Entity("Q4", "Computer", "Programmable machine", "concept", "science"),
            "Q5": Entity("Q5", "London", "Capital of the United Kingdom", "place", "places"),
        }
        edge_data = (
            ("edge-1", "Q1", "Q2", "P108", "worked with"),
            ("edge-2", "Q2", "Q3", "P61", "designed"),
            ("edge-3", "Q3", "Q4", "P361", "part of"),
            ("edge-4", "Q1", "Q5", "P19", "place of birth"),
            ("edge-5", "Q5", "Q4", "P138", "associated with"),
            ("edge-6", "Q2", "Q1", "P108", "worked with"),
        )
        edges = tuple(
            GraphEdge(
                id=edge_id,
                source_id=source,
                target_id=target,
                relation_key=relation,
                relation_label=label,
                statement_id=f"demo-{edge_id}",
                explanation=f"{entities[source].label} {label} {entities[target].label}.",
                target=entities[target],
            )
            for edge_id, source, target, relation, label in edge_data
        )
        rounds = tuple(
            Round(
                id=f"demo-history-{difficulty.value}-{index}",
                start_id="Q1",
                target_id="Q4",
                category="history_people",
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
