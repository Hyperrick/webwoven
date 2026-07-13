"""Focused session-presentation tests for relation group identity."""

from datetime import UTC, datetime
from unittest.mock import create_autospec

from webwoven_api.domain.navigation import start_navigation
from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import Entity, GraphEdge, Round
from webwoven_api.graph.memory_reader import MemoryGraphReader
from webwoven_api.http.presenters import SessionPresenter
from webwoven_api.sessions.models import GameSession, SessionMode, SessionStatus
from webwoven_api.sessions.service import SessionService


def test_relation_groups_distinguish_forward_and_inverse_uses_of_one_property() -> None:
    entities = {
        "Q1": Entity("Q1", "Crossroads", None, "place", "places"),
        "Q2": Entity("Q2", "Forward target", None, "place", "places"),
        "Q3": Entity("Q3", "Inverse target", None, "place", "places"),
    }
    edges = (
        GraphEdge(
            id="edge-forward",
            source_id="Q1",
            target_id="Q2",
            relation_key="P36",
            relation_label="capital",
            statement_id="statement-forward",
            explanation="Forward target is the capital of Crossroads.",
            target=entities["Q2"],
            direction="outgoing",
        ),
        GraphEdge(
            id="edge-inverse",
            source_id="Q1",
            target_id="Q3",
            relation_key="P36",
            relation_label="capital of",
            statement_id="statement-inverse",
            explanation="Crossroads is the capital of Inverse target.",
            target=entities["Q3"],
            direction="incoming",
        ),
    )
    round_ = Round(
        id="round",
        start_id="Q1",
        target_id="Q2",
        category="places",
        difficulty=Difficulty.EASY,
        optimal_distance=1,
        time_window=120,
        published=True,
    )
    graph = MemoryGraphReader(
        entities=entities,
        edges=edges,
        rounds=(round_,),
        distances={("round", "Q1"): 1, ("round", "Q2"): 0},
    )
    session = GameSession(
        id="session",
        guest_id="guest",
        mode=SessionMode.SOLO,
        graph_version=graph.graph_version,
        round=round_,
        navigation=start_navigation("Q1"),
        status=SessionStatus.ACTIVE,
        state_version=0,
        started_at=datetime(2026, 7, 13, tzinfo=UTC),
    )
    sessions = create_autospec(SessionService, instance=True)
    sessions.issue_edge_token.side_effect = lambda _session, edge_id: f"signed-{edge_id}"
    presenter = SessionPresenter(graph, sessions)

    first = presenter.snapshot(session).relation_groups
    second = presenter.snapshot(session).relation_groups

    assert [group.property_id for group in first] == ["P36", "P36"]
    assert {(group.label, group.direction) for group in first} == {
        ("capital", "outgoing"),
        ("capital of", "incoming"),
    }
    assert len({group.group_id for group in first}) == 2
    assert [group.group_id for group in first] == [group.group_id for group in second]
    assert all(group.group_id.startswith(f"P36-{group.direction}-") for group in first)
