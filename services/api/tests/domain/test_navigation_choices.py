"""Dense real graphs stay playable without hiding every route to the goal."""

from webwoven_api.graph.contracts import Entity, GraphEdge
from webwoven_api.sessions.choices import MAX_VISIBLE_TARGETS, select_visible_edges


def test_choice_projection_is_bounded_and_keeps_progress_route() -> None:
    edges = tuple(_edge(index, relation="P19" if index < 10 else "P800") for index in range(1, 13))
    distances = {f"Q{index}": 4 for index in range(1, 13)}
    distances["Q12"] = 2

    visible = select_visible_edges(edges, distances, current_distance=3)

    assert len({edge.target_id for edge in visible}) == MAX_VISIBLE_TARGETS
    assert "Q12" in {edge.target_id for edge in visible}
    assert {edge.relation_key for edge in visible} == {"P19", "P800"}
    assert visible == select_visible_edges(edges, distances, current_distance=3)


def test_choice_projection_preserves_multiple_facts_for_selected_target() -> None:
    shared_target = Entity("Q2", "Shared target", "Description", "item", "places_architecture")
    edges = (
        _edge(1),
        GraphEdge(
            id="edge-shared",
            source_id="Q0",
            target_id="Q2",
            relation_key="P800",
            relation_label="notable work",
            statement_id="statement-shared",
            explanation="Source also connects to Shared target.",
            target=shared_target,
        ),
        _edge(2),
    )

    visible = select_visible_edges(edges, {"Q2": 0}, current_distance=1, limit=1)

    assert len(visible) == 2
    assert {edge.id for edge in visible} == {"edge-2", "edge-shared"}


def _edge(index: int, *, relation: str = "P19") -> GraphEdge:
    target = Entity(
        id=f"Q{index}",
        label=f"Target {index:02d}",
        description="Description",
        entity_type="item",
        category="places_architecture",
    )
    return GraphEdge(
        id=f"edge-{index}",
        source_id="Q0",
        target_id=target.id,
        relation_key=relation,
        relation_label="connection",
        statement_id=f"statement-{index}",
        explanation=f"Source connects to {target.label}.",
        target=target,
    )
