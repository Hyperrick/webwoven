import re

from webwoven_api.graph.memory_reader import MemoryGraphReader


def test_demo_graph_uses_complete_direction_aligned_statements() -> None:
    graph = MemoryGraphReader.demo()

    assert all(re.search(r"[.!?]$", edge.explanation) for edge in graph.edges)
    assert all(
        "\n" not in edge.explanation and "\r" not in edge.explanation for edge in graph.edges
    )
    first_edge = graph.get_edge("edge-1")
    assert first_edge is not None
    assert first_edge.relation_key == "P737"
    assert first_edge.relation_label == "influenced by"
    assert first_edge.explanation == "Ada Lovelace was influenced by Charles Babbage."

    edge = graph.get_edge("edge-2")
    assert edge is not None
    assert edge.relation_key == "P170"
    assert edge.relation_label == "creator of"
    assert edge.direction == "incoming"
    assert edge.explanation == "The Analytical Engine was created by Charles Babbage."
