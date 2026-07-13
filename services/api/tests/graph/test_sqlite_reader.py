"""Contract test against the pipeline-owned smoke graph."""

import shutil
import sqlite3
from pathlib import Path

import pytest
from webwoven_api.graph.sqlite_reader import SQLiteGraphReader


def test_reads_pipeline_v2_smoke_graph() -> None:
    root = Path(__file__).resolve().parents[4]
    reader = SQLiteGraphReader(root / "data/fixtures/smoke/graph.sqlite3")
    rounds = reader.list_published_rounds()
    assert reader.is_healthy()
    assert len(reader.graph_version) == 64
    assert len(rounds) == 40
    round_ = rounds[0]
    assert reader.get_entity(round_.start_id) is not None
    assert reader.distance_to_target(round_.id, round_.target_id) == 0
    edges = reader.get_edges(round_.start_id)
    assert edges
    assert reader.get_edge(edges[0].id) == edges[0]


def test_uses_the_label_for_each_edge_direction_without_losing_explanation() -> None:
    root = Path(__file__).resolve().parents[4]
    reader = SQLiteGraphReader(root / "data/fixtures/smoke/graph.sqlite3")

    forward = next(
        edge
        for edge in reader.get_edges("fixture:places:03")
        if edge.target_id == "fixture:places:04"
    )
    inverse = next(
        edge
        for edge in reader.get_edges("fixture:places:04")
        if edge.target_id == "fixture:places:03"
    )

    assert forward.relation_label == "capital"
    assert inverse.relation_label == "capital of"
    assert forward.direction == "outgoing"
    assert inverse.direction == "incoming"
    assert forward.explanation == inverse.explanation
    assert forward.explanation == (
        "Fictional fixture fact: The capital of the Republic of Avenmark is Calder City."
    )


def test_rejects_an_older_graph_schema_before_serving_it(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    graph_path = tmp_path / "graph-v1.sqlite3"
    shutil.copyfile(root / "data/fixtures/smoke/graph.sqlite3", graph_path)
    with sqlite3.connect(graph_path) as connection:
        connection.execute("UPDATE metadata SET value = '1' WHERE key = 'schema_version'")

    with pytest.raises(ValueError, match="expected 2, received 1"):
        SQLiteGraphReader(graph_path)
