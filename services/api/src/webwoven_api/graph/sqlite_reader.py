"""Read-only adapter for the pipeline-owned SQLite v3 graph schema."""

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import Entity, GraphEdge, Round

GRAPH_SCHEMA_VERSION = "3"


class SQLiteGraphReader:
    """Query an immutable graph bundle without mutating or migrating it."""

    def __init__(self, path: Path) -> None:
        self._path = path.resolve()
        if not self._path.is_file():
            raise FileNotFoundError(f"Graph bundle not found: {self._path}")
        metadata = self._read_metadata()
        schema_version = metadata.get("schema_version")
        if schema_version != GRAPH_SCHEMA_VERSION:
            raise ValueError(
                "Unsupported graph schema version: "
                f"expected {GRAPH_SCHEMA_VERSION}, received {schema_version or 'missing'}"
            )
        self._graph_version = _graph_version(metadata)

    @property
    def graph_version(self) -> str:
        return self._graph_version

    def is_healthy(self) -> bool:
        try:
            with self._connect() as connection:
                row = connection.execute("PRAGMA quick_check").fetchone()
                schema_row = connection.execute(
                    "SELECT value FROM metadata WHERE key = 'schema_version'"
                ).fetchone()
                return (
                    row is not None
                    and row[0] == "ok"
                    and schema_row is not None
                    and str(schema_row[0]) == GRAPH_SCHEMA_VERSION
                )
        except sqlite3.Error:
            return False

    def get_entity(self, entity_id: str) -> Entity | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, label, description, entity_type, category,
                       image_path, image_attribution_json, wikipedia_url
                FROM entities WHERE id = ?
                """,
                (entity_id,),
            ).fetchone()
        return _entity_from_row(row) if row is not None else None

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        with self._connect() as connection:
            row = connection.execute(
                _EDGE_SELECT + " WHERE e.id = ? AND e.playable = 1", (edge_id,)
            ).fetchone()
        return _edge_from_row(row) if row is not None else None

    def get_edges(self, source_id: str) -> tuple[GraphEdge, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                _EDGE_SELECT
                + " WHERE e.source_id = ? AND e.playable = 1"
                + " ORDER BY e.relation_key, target.label COLLATE NOCASE, e.id",
                (source_id,),
            ).fetchall()
        return tuple(_edge_from_row(row) for row in rows)

    def get_round(self, round_id: str) -> Round | None:
        with self._connect() as connection:
            row = connection.execute(_ROUND_SELECT + " WHERE id = ?", (round_id,)).fetchone()
        return _round_from_row(row) if row is not None else None

    def list_published_rounds(
        self,
        *,
        category: str | None = None,
        difficulty: Difficulty | None = None,
    ) -> tuple[Round, ...]:
        clauses = ["published = 1"]
        parameters: list[str] = []
        if category is not None:
            clauses.append("category = ?")
            parameters.append(category)
        if difficulty is not None:
            clauses.append("difficulty = ?")
            parameters.append(difficulty.value)
        query = f"{_ROUND_SELECT} WHERE {' AND '.join(clauses)} ORDER BY id"
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return tuple(_round_from_row(row) for row in rows)

    def distance_to_target(self, round_id: str, entity_id: str) -> int | None:
        return self.distances_to_target(round_id, (entity_id,)).get(entity_id)

    def distances_to_target(self, round_id: str, entity_ids: tuple[str, ...]) -> dict[str, int]:
        unique_ids = tuple(dict.fromkeys(entity_ids))
        if not unique_ids:
            return {}
        placeholders = ", ".join("?" for _ in unique_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT entity_id, distance FROM distances "
                f"WHERE round_id = ? AND entity_id IN ({placeholders})",
                (round_id, *unique_ids),
            ).fetchall()
        return {str(row[0]): int(row[1]) for row in rows}

    def _read_metadata(self) -> dict[str, str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT key, value FROM metadata
                WHERE key IN ('graph_version', 'graph_build_id', 'build_id', 'schema_version')
                """
            ).fetchall()
        return {str(row[0]): str(row[1]) for row in rows}

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection]:
        uri = f"file:{self._path.as_posix()}?mode=ro&immutable=1"
        connection = sqlite3.connect(uri, uri=True, timeout=2)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()


_EDGE_SELECT = """
SELECT e.id, e.source_id, e.target_id, e.relation_key,
       CASE WHEN e.inverse = 1
            THEN COALESCE(rt.inverse_label, rt.forward_label)
            ELSE rt.forward_label
       END AS relation_label,
       e.inverse, e.statement_id, e.explanation,
       target.id AS target_entity_id, target.label AS target_label,
       target.description AS target_description, target.entity_type AS target_type,
       target.category AS target_category, target.image_path AS target_image_path,
       target.image_attribution_json AS target_attribution,
       target.wikipedia_url AS target_wikipedia_url
FROM edges AS e
JOIN relation_types AS rt ON rt.key = e.relation_key
JOIN entities AS target ON target.id = e.target_id
"""

_ROUND_SELECT = """
SELECT id, start_id, target_id, category, difficulty,
       optimal_distance, time_window, published
FROM rounds
"""


def _graph_version(metadata: dict[str, str]) -> str:
    return (
        metadata.get("graph_version")
        or metadata.get("graph_build_id")
        or metadata.get("build_id")
        or f"schema-v{GRAPH_SCHEMA_VERSION}"
    )


def _entity_from_row(row: sqlite3.Row) -> Entity:
    return Entity(
        id=str(row["id"]),
        label=str(row["label"]),
        description=str(row["description"]) if row["description"] is not None else None,
        entity_type=str(row["entity_type"]),
        category=str(row["category"]),
        image_path=str(row["image_path"]) if row["image_path"] is not None else None,
        image_attribution_json=(
            str(row["image_attribution_json"])
            if row["image_attribution_json"] is not None
            else None
        ),
        wikipedia_url=(str(row["wikipedia_url"]) if row["wikipedia_url"] is not None else None),
    )


def _edge_from_row(row: sqlite3.Row) -> GraphEdge:
    target = Entity(
        id=str(row["target_entity_id"]),
        label=str(row["target_label"]),
        description=(
            str(row["target_description"]) if row["target_description"] is not None else None
        ),
        entity_type=str(row["target_type"]),
        category=str(row["target_category"]),
        image_path=(
            str(row["target_image_path"]) if row["target_image_path"] is not None else None
        ),
        image_attribution_json=(
            str(row["target_attribution"]) if row["target_attribution"] is not None else None
        ),
        wikipedia_url=(
            str(row["target_wikipedia_url"]) if row["target_wikipedia_url"] is not None else None
        ),
    )
    return GraphEdge(
        id=str(row["id"]),
        source_id=str(row["source_id"]),
        target_id=str(row["target_id"]),
        relation_key=str(row["relation_key"]),
        relation_label=str(row["relation_label"]),
        statement_id=str(row["statement_id"]),
        explanation=str(row["explanation"]),
        target=target,
        direction="incoming" if bool(row["inverse"]) else "outgoing",
    )


def _round_from_row(row: sqlite3.Row) -> Round:
    return Round(
        id=str(row["id"]),
        start_id=str(row["start_id"]),
        target_id=str(row["target_id"]),
        category=str(row["category"]),
        difficulty=Difficulty(str(row["difficulty"])),
        optimal_distance=int(row["optimal_distance"]),
        time_window=int(row["time_window"]),
        published=bool(row["published"]),
    )
