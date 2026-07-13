from __future__ import annotations

from webwoven_pipeline.cli import _edges


def test_graph_source_parser_preserves_edge_direction() -> None:
    edges = _edges(
        [
            {
                "id": "edge-1",
                "source_id": "Q2",
                "target_id": "Q1",
                "relation_key": "P19",
                "statement_id": "Q1$birthplace",
                "explanation": "Ada was born in Exampleton.",
                "inverse": True,
                "playable": True,
            }
        ]
    )

    assert len(edges) == 1
    assert edges[0].inverse is True
    assert edges[0].explanation == "Ada was born in Exampleton."
