"""Contract test against the pipeline-owned smoke graph."""

from pathlib import Path

from webwoven_api.graph.sqlite_reader import SQLiteGraphReader


def test_reads_pipeline_v1_smoke_graph() -> None:
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
