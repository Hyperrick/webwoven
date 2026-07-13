from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter

import pytest
from webwoven_pipeline.fixture import build_smoke_graph, generate_smoke_fixture
from webwoven_pipeline.manifest import verify_manifest
from webwoven_pipeline.rounds import generate_rounds
from webwoven_pipeline.taxonomy import CATEGORIES


def test_round_generator_locks_candidate_and_publication_distribution() -> None:
    entities, edges = build_smoke_graph()

    rounds = generate_rounds(entities, edges)

    assert len(rounds) == 100
    assert sum(item.published for item in rounds) == 40
    for category in CATEGORIES:
        selected = [item for item in rounds if item.category == category]
        assert len(selected) == 25
        assert sum(item.published for item in selected) == 10
        assert _counts(selected, published=False) == {"easy": 10, "normal": 10, "hard": 5}
        assert _counts(selected, published=True) == {"easy": 4, "normal": 4, "hard": 2}


def test_round_endpoints_can_be_restricted_to_reviewed_ids() -> None:
    entities, edges = build_smoke_graph()
    allowed = {entity.id for entity in entities if not entity.id.endswith(("01", "07"))}

    rounds = generate_rounds(entities, edges, endpoint_ids=allowed)

    assert all(item.start_id in allowed and item.target_id in allowed for item in rounds)


def test_smoke_graph_is_a_readable_fictional_catalog(registry) -> None:
    entities, edges = build_smoke_graph()
    labels = {entity.id: entity.label for entity in entities}

    assert len(entities) == 48
    assert len(labels) == 48
    assert all("waypoint" not in label.casefold() for label in labels.values())
    assert all(entity.description.startswith("Fictional fixture ") for entity in entities)
    assert all(entity.entity_type.startswith("fictional_") for entity in entities)
    assert Counter(entity.category for entity in entities) == Counter(
        {category: 12 for category in CATEGORIES}
    )

    assert len(edges) == 96
    assert {edge.relation_key for edge in edges} == registry.playable_keys
    assert set(Counter(edge.source_id for edge in edges).values()) == {2}
    assert set(Counter(edge.target_id for edge in edges).values()) == {2}
    assert set(Counter(edge.statement_id for edge in edges).values()) == {2}
    assert all(edge.explanation.startswith("Fictional fixture fact: ") for edge in edges)
    assert len({edge.explanation for edge in edges}) == 48
    assert {
        edge.explanation
        for edge in edges
        if edge.relation_key == "P737" and labels[edge.source_id] == "Tobin Rill"
    } == {"Fictional fixture fact: Tobin Rill was influenced by Orra Venn's stage experiments."}
    assert Counter(edge.inverse for edge in edges) == Counter({False: 48, True: 48})
    assert all(
        {edge.inverse for edge in edges if edge.statement_id == statement_id} == {False, True}
        for statement_id in {edge.statement_id for edge in edges}
    )

    readable_edges = {
        (labels[edge.source_id], edge.relation_key, labels[edge.target_id]) for edge in edges
    }
    assert ("Elian Voss", "P19", "Gannet Hollow") in readable_edges
    assert ("Ochre Door", "P161", "Kei Moss") in readable_edges
    assert ("Republic of Avenmark", "P36", "Calder City") in readable_edges


def test_smoke_bundle_is_deterministic_and_graphreader_compatible(tmp_path, registry) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_build = generate_smoke_fixture(first, registry)
    second_build = generate_smoke_fixture(second, registry)

    assert first_build == second_build
    assert _sha256(first / "graph.sqlite3") == _sha256(second / "graph.sqlite3")
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    verify_manifest(first / "manifest.json")
    with sqlite3.connect(first / "graph.sqlite3") as connection:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        assert metadata["graph_build_id"] == first_build
        assert metadata["schema_version"] == "2"
        assert metadata["round_count"] == "100"
        assert metadata["published_round_count"] == "40"
        assert connection.execute("SELECT COUNT(*) FROM entities").fetchone() == (48,)
        assert connection.execute("SELECT COUNT(*) FROM edges").fetchone() == (96,)
        assert connection.execute("SELECT COUNT(*) FROM edges WHERE inverse = 1").fetchone() == (
            48,
        )
        assert connection.execute("SELECT COUNT(*) FROM relation_types").fetchone() == (20,)
        assert connection.execute("SELECT COUNT(*) FROM distances").fetchone()[0] > 100
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE edges SET inverse = 2 WHERE id = (SELECT id FROM edges LIMIT 1)"
            )
    reviews = json.loads((first / "fixture-review-decisions.json").read_text())
    assert sum(item["decision"] == "approved" for item in reviews["decisions"]) == 40


def _counts(rounds, *, published: bool) -> dict[str, int]:
    return {
        difficulty: sum(
            item.difficulty == difficulty and (item.published or not published) for item in rounds
        )
        for difficulty in ("easy", "normal", "hard")
    }


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
