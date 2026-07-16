from webwoven_pipeline.media_context import (
    MediaContextHint,
    build_media_context_hints,
    selected_neighbor_media_candidates,
)
from webwoven_pipeline.models import Edge


def test_context_hints_prefer_creator_over_generic_country() -> None:
    edges = (
        Edge("country", "Q1", "Q30", "P17", "S1", "in country", False, True),
        Edge("creator", "Q1", "Q42", "P170", "S2", "created by", False, True),
    )

    result = build_media_context_hints(
        ["Q1"],
        {"Q1": "Work", "Q30": "United States", "Q42": "Creator"},
        edges,
    )

    assert [hint.entity_id for hint in result["Q1"]] == ["Q42", "Q30"]


def test_context_candidates_reuse_an_exact_documented_neighbor_image() -> None:
    result = selected_neighbor_media_candidates(
        ["Q1"],
        {"Q1": (MediaContextHint("Q42", "Creator", "P170"),)},
        {"Q42": "Creator portrait.jpg"},
    )

    assert result["Q1"][0].file_name == "Creator portrait.jpg"
    assert result["Q1"][0].provenance == "graph_context:P170:Q42:Creator"
