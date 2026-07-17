from pathlib import Path

import pytest
from webwoven_pipeline.cli_serialization import parse_edges, parse_entities
from webwoven_pipeline.compiler import GraphCompileError, compile_graph


def test_generic_graph_source_preserves_and_compiles_semantic_evidence(
    tmp_path: Path,
    registry,
) -> None:
    entities = parse_entities(
        [
            {
                "id": "external:work",
                "label": "Example",
                "description": "provider work",
                "entity_type": "work",
                "category": "literature_language",
            },
            {
                "id": "external:selection",
                "label": "Readers Choice",
                "description": "provider-authored collection",
                "entity_type": "collection",
                "category": "literature_language",
                "semantic_tags": ["ranked_selection"],
            },
        ]
    )
    edges = parse_edges(
        [
            {
                "id": "external:edge",
                "source_id": "external:work",
                "target_id": "external:selection",
                "relation_key": "P166",
                "statement_id": "external:statement",
                "explanation": "Example ranked #7 on the Readers Choice.",
                "inverse": False,
                "playable": True,
                "series_ordinal": "7",
            }
        ]
    )

    assert entities[1].semantic_tags == ("ranked_selection",)
    assert edges[0].series_ordinal == "7"
    assert edges[0].explanation == "Example ranked #7 on the Readers Choice."
    compile_graph(tmp_path / "graph.sqlite3", registry, entities, edges, ())


def test_generic_graph_source_must_supply_semantics_for_ambiguous_recognition(
    tmp_path: Path,
    registry,
) -> None:
    entities = parse_entities(
        [
            {
                "id": "external:work",
                "label": "Example",
                "description": "provider work",
                "entity_type": "work",
                "category": "literature_language",
            },
            {
                "id": "external:selection",
                "label": "Readers Choice",
                "description": "provider-authored collection",
                "entity_type": "collection",
                "category": "literature_language",
            },
        ]
    )
    edges = parse_edges(
        [
            {
                "id": "external:edge",
                "source_id": "external:work",
                "target_id": "external:selection",
                "relation_key": "P166",
                "statement_id": "external:statement",
                "explanation": (
                    "Example has a recorded recognition connection to the Readers Choice."
                ),
                "inverse": False,
                "playable": True,
            }
        ]
    )

    with pytest.raises(GraphCompileError, match="lacks semantic recognition evidence"):
        compile_graph(tmp_path / "graph.sqlite3", registry, entities, edges, ())
