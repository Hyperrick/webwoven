from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .models import Edge, Entity, GeneratedContent, Round
from .registry import RelationRegistry
from .rounds import shortest_distances_to_target

GRAPH_SCHEMA_VERSION = 2

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    description TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    category TEXT NOT NULL,
    image_path TEXT,
    image_attribution_json TEXT
) WITHOUT ROWID;
CREATE TABLE relation_types (
    key TEXT PRIMARY KEY,
    forward_label TEXT NOT NULL,
    inverse_label TEXT,
    category TEXT NOT NULL
) WITHOUT ROWID;
CREATE TABLE edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES entities(id),
    target_id TEXT NOT NULL REFERENCES entities(id),
    relation_key TEXT NOT NULL REFERENCES relation_types(key),
    statement_id TEXT NOT NULL,
    explanation TEXT NOT NULL,
    inverse INTEGER NOT NULL CHECK (inverse IN (0, 1)),
    playable INTEGER NOT NULL CHECK (playable IN (0, 1))
) WITHOUT ROWID;
CREATE TABLE rounds (
    id TEXT PRIMARY KEY,
    start_id TEXT NOT NULL REFERENCES entities(id),
    target_id TEXT NOT NULL REFERENCES entities(id),
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK (difficulty IN ('easy', 'normal', 'hard')),
    optimal_distance INTEGER NOT NULL CHECK (optimal_distance > 0),
    time_window INTEGER NOT NULL CHECK (time_window > 0),
    published INTEGER NOT NULL CHECK (published IN (0, 1))
) WITHOUT ROWID;
CREATE TABLE distances (
    round_id TEXT NOT NULL REFERENCES rounds(id),
    entity_id TEXT NOT NULL REFERENCES entities(id),
    distance INTEGER NOT NULL CHECK (distance >= 0),
    PRIMARY KEY (round_id, entity_id)
) WITHOUT ROWID;
CREATE TABLE round_content (
    round_id TEXT PRIMARY KEY REFERENCES rounds(id),
    hints_json TEXT NOT NULL,
    recap TEXT NOT NULL,
    provenance_json TEXT NOT NULL
) WITHOUT ROWID;
CREATE INDEX idx_edges_source_id ON edges(source_id);
CREATE INDEX idx_rounds_publication ON rounds(published, category, difficulty);
CREATE INDEX idx_distances_round_entity ON distances(round_id, entity_id);
"""


class GraphCompileError(ValueError):
    """Raised when graph inputs cannot satisfy schema invariants."""


def compile_graph(
    destination: Path,
    registry: RelationRegistry,
    entities: Iterable[Entity],
    edges: Iterable[Edge],
    rounds: Iterable[Round],
    *,
    content: Mapping[str, GeneratedContent] | None = None,
) -> str:
    """Compile a logically deterministic immutable SQLite graph bundle."""
    if destination.exists():
        raise FileExistsError(f"refusing to replace immutable graph: {destination}")
    entity_values = tuple(sorted(entities, key=lambda item: item.id))
    edge_values = tuple(sorted(edges, key=lambda item: item.id))
    round_values = tuple(sorted(rounds, key=lambda item: item.id))
    content_values = content or {}
    _validate_references(registry, entity_values, edge_values, round_values, content_values)
    graph_build_id = _graph_build_id(
        registry,
        entity_values,
        edge_values,
        round_values,
        content_values,
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(destination)
    try:
        connection.executescript(SCHEMA)
        with connection:
            _insert_metadata(connection, graph_build_id, entity_values, edge_values, round_values)
            _insert_relations(connection, registry)
            _insert_entities(connection, entity_values)
            _insert_edges(connection, edge_values)
            _insert_rounds(connection, round_values)
            _insert_distances(connection, round_values, edge_values)
            _insert_content(connection, round_values, content_values)
        result = connection.execute("PRAGMA integrity_check").fetchone()
        if result != ("ok",):
            raise GraphCompileError(f"SQLite integrity check failed: {result}")
        connection.execute("VACUUM")
    except Exception:
        connection.close()
        destination.unlink(missing_ok=True)
        raise
    finally:
        connection.close()
    return graph_build_id


def _validate_references(
    registry: RelationRegistry,
    entities: tuple[Entity, ...],
    edges: tuple[Edge, ...],
    rounds: tuple[Round, ...],
    content: Mapping[str, GeneratedContent],
) -> None:
    entity_ids = {item.id for item in entities}
    relation_keys = set(registry.by_key)
    round_ids = {item.id for item in rounds}
    if len(entity_ids) != len(entities):
        raise GraphCompileError("entity IDs must be unique")
    if len({item.id for item in edges}) != len(edges):
        raise GraphCompileError("edge IDs must be unique")
    if len(round_ids) != len(rounds):
        raise GraphCompileError("round IDs must be unique")
    for edge in edges:
        if edge.source_id not in entity_ids or edge.target_id not in entity_ids:
            raise GraphCompileError(f"edge {edge.id} references an unknown entity")
        if edge.relation_key not in relation_keys:
            raise GraphCompileError(f"edge {edge.id} references an unknown relation")
    for round_value in rounds:
        if round_value.start_id not in entity_ids or round_value.target_id not in entity_ids:
            raise GraphCompileError(f"round {round_value.id} references an unknown entity")
    if not set(content).issubset(round_ids):
        raise GraphCompileError("content references an unknown round")
    for round_id, generated in content.items():
        generator = generated.provenance.get("generator")
        approval = generated.provenance.get("approval_status")
        if generator == "codex" and approval != "approved":
            raise GraphCompileError(f"Codex content for {round_id} is not approved")
        if generator not in {"codex", "deterministic_fallback"}:
            raise GraphCompileError(f"content for {round_id} has an unsupported generator")


def _insert_metadata(
    connection: sqlite3.Connection,
    build_id: str,
    entities: tuple[Entity, ...],
    edges: tuple[Edge, ...],
    rounds: tuple[Round, ...],
) -> None:
    values = {
        "graph_build_id": build_id,
        "schema_version": str(GRAPH_SCHEMA_VERSION),
        "entity_count": str(len(entities)),
        "edge_count": str(len(edges)),
        "round_count": str(len(rounds)),
        "published_round_count": str(sum(item.published for item in rounds)),
    }
    connection.executemany("INSERT INTO metadata VALUES (?, ?)", sorted(values.items()))


def _insert_relations(connection: sqlite3.Connection, registry: RelationRegistry) -> None:
    connection.executemany(
        "INSERT INTO relation_types VALUES (?, ?, ?, ?)",
        [
            (item.key, item.forward_label, item.inverse_label, item.category)
            for item in sorted(registry.relations, key=lambda value: value.key)
        ],
    )


def _insert_entities(connection: sqlite3.Connection, entities: tuple[Entity, ...]) -> None:
    connection.executemany(
        "INSERT INTO entities VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                item.id,
                item.label,
                item.description,
                item.entity_type,
                item.category,
                item.image_path,
                _json(item.image_attribution) if item.image_attribution else None,
            )
            for item in entities
        ],
    )


def _insert_edges(connection: sqlite3.Connection, edges: tuple[Edge, ...]) -> None:
    connection.executemany(
        "INSERT INTO edges VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                item.id,
                item.source_id,
                item.target_id,
                item.relation_key,
                item.statement_id,
                item.explanation,
                int(item.inverse),
                int(item.playable),
            )
            for item in edges
        ],
    )


def _insert_rounds(connection: sqlite3.Connection, rounds: tuple[Round, ...]) -> None:
    connection.executemany(
        "INSERT INTO rounds VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                item.id,
                item.start_id,
                item.target_id,
                item.category,
                item.difficulty,
                item.optimal_distance,
                item.time_window,
                int(item.published),
            )
            for item in rounds
        ],
    )


def _insert_distances(
    connection: sqlite3.Connection,
    rounds: tuple[Round, ...],
    edges: tuple[Edge, ...],
) -> None:
    rows: list[tuple[str, str, int]] = []
    for item in rounds:
        distances = shortest_distances_to_target(item.target_id, edges)
        if distances.get(item.start_id) != item.optimal_distance:
            raise GraphCompileError(f"round {item.id} optimal distance does not match the graph")
        rows.extend((item.id, entity_id, distance) for entity_id, distance in distances.items())
    connection.executemany("INSERT INTO distances VALUES (?, ?, ?)", sorted(rows))


def _insert_content(
    connection: sqlite3.Connection,
    rounds: tuple[Round, ...],
    content: Mapping[str, GeneratedContent],
) -> None:
    rows: list[tuple[str, str, str, str]] = []
    for item in rounds:
        generated = content.get(item.id)
        if generated is None:
            rows.append((item.id, "[]", "", "{}"))
        else:
            rows.append(
                (
                    item.id,
                    _json(
                        {
                            "hints": list(generated.hints),
                            "explanations": list(generated.explanations),
                        }
                    ),
                    generated.recap,
                    _json(generated.provenance),
                )
            )
    connection.executemany("INSERT INTO round_content VALUES (?, ?, ?, ?)", rows)


def _graph_build_id(
    registry: RelationRegistry,
    entities: tuple[Entity, ...],
    edges: tuple[Edge, ...],
    rounds: tuple[Round, ...],
    content: Mapping[str, GeneratedContent],
) -> str:
    payload: dict[str, Any] = {
        "schema_version": GRAPH_SCHEMA_VERSION,
        "relations": [item.to_dict() for item in registry.relations],
        "entities": [item.to_dict() for item in entities],
        "edges": [item.to_dict() for item in edges],
        "rounds": [item.to_dict() for item in rounds],
        "content": {key: content[key].to_dict() for key in sorted(content)},
    }
    return hashlib.sha256(_json(payload).encode()).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
