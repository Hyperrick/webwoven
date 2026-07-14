"""Typed persistence documents round-trip immutable domain state."""

from datetime import UTC, date, datetime

import pytest
from webwoven_api.domain.hints import HintResult, HintType
from webwoven_api.domain.navigation import NavigationState
from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import Round
from webwoven_api.persistence.serialization import (
    command_execution_from_dict,
    command_execution_to_dict,
    room_from_dict,
    room_to_dict,
    session_from_dict,
    session_to_dict,
)
from webwoven_api.persistence.serialization.values import PersistenceDataError
from webwoven_api.rooms.models import Participant, Room, RoomEvent, RoomState
from webwoven_api.sessions.exploration import followed_frame
from webwoven_api.sessions.models import (
    CommandExecution,
    GameSession,
    HintUse,
    SessionMode,
    SessionStatus,
)

NOW = datetime(2026, 7, 13, 12, 30, tzinfo=UTC)


def test_session_and_command_round_trip() -> None:
    session = _session()
    assert session_from_dict(session_to_dict(session)) == session

    hint = HintResult(HintType.LENS, 150, "P19", None, "Inspect birthplace.")
    result = CommandExecution(session=session, applied=True, hint=hint)
    assert command_execution_from_dict(command_execution_to_dict(result)) == result


def test_session_deserialization_accepts_pre_history_documents() -> None:
    document = session_to_dict(_session())
    document.pop("decision_history")

    assert session_from_dict(document).decision_history == ()


def test_session_deserialization_rejects_legacy_cyclic_active_stack() -> None:
    document = session_to_dict(_session())
    navigation = document["navigation"]
    assert isinstance(navigation, dict)
    navigation["stack"] = ["Q1", "Q3", "Q1"]
    navigation["trail"] = ["Q1", "Q3", "Q1"]
    navigation["moves"] = 2

    with pytest.raises(ValueError, match="stack must contain unique entities"):
        session_from_dict(document)


def test_session_deserialization_allows_repeated_visible_trail_entries() -> None:
    restored = session_from_dict(session_to_dict(_session()))

    assert restored.navigation.stack == ("Q1", "Q3")
    assert restored.navigation.trail == ("Q1", "Q3", "Q1", "Q3")


def test_room_round_trip_preserves_reconnect_state_and_events() -> None:
    event = RoomEvent(1, "race.started", NOW, {"state": "racing"})
    room = Room(
        code="ABC123",
        host_guest_id="guest-1",
        graph_version="graph-v1",
        round_id="round-1",
        state=RoomState.RACING,
        participants=(
            Participant(
                "guest-1",
                "Atlas",
                ready=True,
                connected=False,
                session_id="session-1",
                moves=2,
            ),
        ),
        created_at=NOW,
        updated_at=NOW,
        sequence=1,
        events=(event,),
    )
    assert room_from_dict(room_to_dict(room)) == room


def test_serialization_rejects_unversioned_or_non_json_data() -> None:
    with pytest.raises(PersistenceDataError, match="schema_version"):
        session_from_dict({"schema_version": "one"})
    event = RoomEvent(1, "bad", NOW, {"invalid": object()})
    with pytest.raises(PersistenceDataError, match="non-JSON"):
        room_from_dict(
            {
                **room_to_dict(
                    Room(
                        "ABC123",
                        "guest-1",
                        "v1",
                        "r1",
                        RoomState.LOBBY,
                        (),
                        NOW,
                        NOW,
                    )
                ),
                "events": [
                    {
                        "sequence": event.sequence,
                        "type": event.type,
                        "occurred_at": event.occurred_at.isoformat(),
                        "payload": event.payload,
                    }
                ],
            }
        )


def _session() -> GameSession:
    round_ = Round("round-1", "Q1", "Q2", "science", Difficulty.NORMAL, 3, 180, True)
    hint = HintUse(HintType.COMPASS, 75, "P19", None, "Promising.", NOW)
    return GameSession(
        id="session-1",
        guest_id="guest-1",
        mode=SessionMode.DAILY,
        graph_version="graph-v1",
        round=round_,
        navigation=NavigationState(("Q1", "Q3"), ("Q1", "Q3", "Q1", "Q3"), 3),
        status=SessionStatus.ACTIVE,
        state_version=3,
        started_at=NOW,
        decision_history=(
            followed_frame(
                source_id="Q1",
                destination_id="Q3",
                visible_edge_ids=("edge-1", "edge-4"),
                selected_edge_id="edge-1",
            ),
        ),
        hints=(hint,),
        room_code=None,
        daily_day=date(2026, 7, 13),
    )
