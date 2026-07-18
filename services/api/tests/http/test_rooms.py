"""Relay lobby, authoritative deadlines, reconnects, and rematches."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from conftest import create_guest
from fastapi.testclient import TestClient
from webwoven_api.main import create_app
from webwoven_api.settings import Settings

ROOT = Path(__file__).parents[4]


def test_host_category_filter_pins_matching_relay_round(app_settings: Settings) -> None:
    fixture = ROOT / "data/fixtures/smoke"
    app = create_app(
        app_settings.model_copy(
            update={
                "graph_path": fixture / "graph.sqlite3",
                "graph_manifest_path": fixture / "manifest.json",
            }
        )
    )
    with TestClient(app) as client:
        headers = create_guest(client, "Focused Host")
        created = client.post(
            "/api/v1/rooms",
            headers=headers,
            json={"difficulty": "normal", "category": "science_technology"},
        )

        assert created.status_code == 201
        room = created.json()
        assert room["category"] == "science_technology"
        assert room["difficulty"] == "normal"
        assert room["start"]["category"] == "science_technology"
        assert room["target"]["category"] == "science_technology"


def test_invite_preview_names_host_and_reports_joinability(app_settings: Settings) -> None:
    app = create_app(app_settings)
    with TestClient(app) as host, TestClient(app) as visitor:
        host_headers = create_guest(host, "Paper Fox")
        create_guest(visitor, "Map Guest")
        room = host.post(
            "/api/v1/rooms", headers=host_headers, json={"difficulty": "normal"}
        ).json()

        preview = visitor.get(f"/api/v1/rooms/{room['code']}/invite")
        member_preview = host.get(f"/api/v1/rooms/{room['code']}/invite")

        assert preview.status_code == 200
        assert preview.json() == {
            "code": room["code"],
            "host_display_name": "Paper Fox",
            "state": "lobby",
            "player_count": 1,
            "max_players": 4,
            "is_member": False,
            "joinable": True,
        }
        assert member_preview.json()["is_member"] is True
        assert member_preview.json()["joinable"] is True


def test_two_player_room_and_reconnect_snapshot(app_settings: Settings) -> None:
    app = create_app(app_settings.model_copy(update={"round_intro_seconds": 5}))
    with TestClient(app) as host, TestClient(app) as guest:
        host_headers = create_guest(host, "Host Atlas")
        guest_headers = create_guest(guest, "Guest Atlas")
        created = host.post("/api/v1/rooms", headers=host_headers, json={"difficulty": "easy"})
        assert created.status_code == 201
        assert created.json()["category"] == "people"
        assert created.json()["difficulty"] == "easy"
        assert created.json()["start"]["qid"] == "Q1"
        assert created.json()["target"]["qid"] == "Q4"
        code = created.json()["code"]
        joined = guest.post(f"/api/v1/rooms/{code}/join", headers=guest_headers)
        assert joined.status_code == 200
        assert len(joined.json()["participants"]) == 2

        host.post(f"/api/v1/rooms/{code}/ready", headers=host_headers, json={"ready": True})
        guest.post(f"/api/v1/rooms/{code}/ready", headers=guest_headers, json={"ready": True})
        started = host.post(f"/api/v1/rooms/{code}/start", headers=host_headers)
        assert started.status_code == 200
        assert started.json()["state"] == "countdown"
        own = next(item for item in started.json()["participants"] if item["is_self"])
        other = next(item for item in started.json()["participants"] if not item["is_self"])
        assert own["session_id"] is not None
        assert other["session_id"] is None

        relay_session = host.get(f"/api/v1/sessions/{own['session_id']}").json()
        assert relay_session["started_at"] == started.json()["countdown_ends_at"]
        guest_room = guest.get(f"/api/v1/rooms/{code}", headers=guest_headers).json()
        guest_participant = next(item for item in guest_room["participants"] if item["is_self"])
        guest_session = guest.get(f"/api/v1/sessions/{guest_participant['session_id']}").json()
        assert guest_session["started_at"] == relay_session["started_at"]
        early_edge = relay_session["relation_groups"][0]["edges"][0]
        early_move = host.post(
            f"/api/v1/sessions/{own['session_id']}/commands",
            headers=host_headers,
            json={
                "type": "follow_edge",
                "client_command_id": "too-early",
                "expected_state_version": 0,
                "edge_token": early_edge["edge_token"],
            },
        )
        assert early_move.status_code == 422
        assert early_move.json()["code"] == "round_not_started"

        with host.websocket_connect(
            f"/api/v1/ws/rooms/{code}", headers={"Origin": "http://testserver"}
        ) as websocket:
            snapshot = websocket.receive_json()
            assert snapshot["type"] == "room.snapshot"
            assert snapshot["payload"]["code"] == code
            websocket.send_text("ping")
            assert websocket.receive_text() == "pong"


def test_first_move_at_countdown_deadline_does_not_need_a_room_refresh(
    app_settings: Settings,
) -> None:
    app = create_app(app_settings.model_copy(update={"round_intro_seconds": 0}))
    with TestClient(app) as host, TestClient(app) as guest:
        host_headers, guest_headers, started = _start_room(host, guest)
        own_session = _own_session(started)
        session = host.get(f"/api/v1/sessions/{own_session}").json()
        edge = _edge_to(session, "Q2")

        moved = _follow(host, host_headers, session, edge, "at-deadline")

        assert moved.status_code == 200
        assert moved.json()["session"]["state_version"] == 1
        room = host.get(f"/api/v1/rooms/{started['code']}", headers=host_headers)
        assert room.json()["state"] == "racing"


def test_grace_deadline_expires_unfinished_session_before_rejecting_move(
    app_settings: Settings,
) -> None:
    app = create_app(app_settings.model_copy(update={"round_intro_seconds": 0}))
    with TestClient(app) as host, TestClient(app) as guest:
        host_headers, guest_headers, started = _start_room(host, guest)
        code = started["code"]
        host.get(f"/api/v1/rooms/{code}", headers=host_headers)
        host_session = _complete_easy_route(host, host_headers, _own_session(started))
        grace = guest.get(f"/api/v1/rooms/{code}", headers=guest_headers).json()
        guest_session_id = _own_session(grace)
        assert host_session["status"] == "completed"
        assert grace["state"] == "grace_period"
        assert grace["grace_ends_at"] is not None

        _replace_room(
            app,
            code,
            grace_ends_at=datetime.now(UTC) - timedelta(milliseconds=1),
        )
        guest_session = guest.get(f"/api/v1/sessions/{guest_session_id}").json()
        rejected = _follow(
            guest,
            guest_headers,
            guest_session,
            _edge_to(guest_session, "Q2"),
            "after-grace",
        )

        assert rejected.status_code == 422
        assert rejected.json()["code"] == "race_not_active"
        finished = guest.get(f"/api/v1/rooms/{code}", headers=guest_headers).json()
        expired = guest.get(f"/api/v1/sessions/{guest_session_id}").json()
        assert finished["state"] == "finished"
        assert finished["rematch_ends_at"] is not None
        assert expired["status"] == "expired"
        assert expired["completed_at"] is not None


def test_two_yes_votes_keep_the_room_code_and_timeout_removes_nonvoter(
    app_settings: Settings,
) -> None:
    app = create_app(app_settings.model_copy(update={"round_intro_seconds": 0}))
    with TestClient(app) as host, TestClient(app) as guest, TestClient(app) as third:
        host_headers = create_guest(host, "Host Atlas")
        guest_headers = create_guest(guest, "Guest Atlas")
        third_headers = create_guest(third, "Third Atlas")
        created = host.post(
            "/api/v1/rooms", headers=host_headers, json={"difficulty": "easy"}
        ).json()
        code = created["code"]
        guest.post(f"/api/v1/rooms/{code}/join", headers=guest_headers)
        third.post(f"/api/v1/rooms/{code}/join", headers=third_headers)
        for client, headers in (
            (host, host_headers),
            (guest, guest_headers),
            (third, third_headers),
        ):
            client.post(f"/api/v1/rooms/{code}/ready", headers=headers, json={"ready": True})
        started = host.post(f"/api/v1/rooms/{code}/start", headers=host_headers).json()
        host.get(f"/api/v1/rooms/{code}", headers=host_headers)
        old_host_session_id = _own_session(started)
        old_guest_session_id = _own_session(
            guest.get(f"/api/v1/rooms/{code}", headers=guest_headers).json()
        )
        old_third_session_id = _own_session(
            third.get(f"/api/v1/rooms/{code}", headers=third_headers).json()
        )
        _complete_easy_route(host, host_headers, _own_session(started))
        _replace_room(
            app,
            code,
            grace_ends_at=datetime.now(UTC) - timedelta(milliseconds=1),
        )
        finished = host.get(f"/api/v1/rooms/{code}", headers=host_headers).json()
        assert finished["state"] == "finished"

        assert (
            host.post(
                f"/api/v1/rooms/{code}/rematch",
                headers=host_headers,
                json={"accept": True},
            ).json()["state"]
            == "finished"
        )
        assert (
            guest.post(
                f"/api/v1/rooms/{code}/rematch",
                headers=guest_headers,
                json={"accept": True},
            ).json()["state"]
            == "finished"
        )
        _replace_room(
            app,
            code,
            rematch_ends_at=datetime.now(UTC) - timedelta(milliseconds=1),
        )

        rematch = host.get(f"/api/v1/rooms/{code}", headers=host_headers).json()
        active = [item for item in rematch["participants"] if item["active"]]
        removed = next(
            item for item in rematch["participants"] if item["display_name"] == "Third Atlas"
        )
        assert rematch["code"] == code
        assert rematch["state"] == "countdown"
        assert len(active) == 2
        assert _own_session(rematch) != old_host_session_id
        guest_rematch = guest.get(f"/api/v1/rooms/{code}", headers=guest_headers).json()
        assert _own_session(guest_rematch) != old_guest_session_id
        assert removed["active"] is False
        third_result = third.get(f"/api/v1/rooms/{code}", headers=third_headers).json()
        third_self = next(item for item in third_result["participants"] if item["is_self"])
        assert third_self["session_id"] == old_third_session_id
        invite = third.get(f"/api/v1/rooms/{code}/invite").json()
        assert invite["is_member"] is False
        assert invite["joinable"] is False


def test_fewer_than_two_rematch_votes_close_the_room(
    app_settings: Settings,
) -> None:
    app = create_app(app_settings.model_copy(update={"round_intro_seconds": 0}))
    with TestClient(app) as host, TestClient(app) as guest:
        host_headers, guest_headers, started = _start_room(host, guest)
        code = started["code"]
        host.get(f"/api/v1/rooms/{code}", headers=host_headers)
        _complete_easy_route(host, host_headers, _own_session(started))
        _replace_room(
            app,
            code,
            grace_ends_at=datetime.now(UTC) - timedelta(milliseconds=1),
        )
        host.get(f"/api/v1/rooms/{code}", headers=host_headers)

        host.post(
            f"/api/v1/rooms/{code}/rematch",
            headers=host_headers,
            json={"accept": True},
        )
        closed = guest.post(
            f"/api/v1/rooms/{code}/rematch",
            headers=guest_headers,
            json={"accept": False},
        )

        assert closed.status_code == 200
        assert closed.json()["state"] == "closed"
        assert closed.json()["close_reason"] == "not_enough_players"
        declined = next(item for item in closed.json()["participants"] if item["is_self"])
        assert declined["active"] is False
        assert declined["session_id"] is not None


def test_websocket_wakes_at_the_countdown_deadline(app_settings: Settings) -> None:
    app = create_app(app_settings.model_copy(update={"round_intro_seconds": 0.05}))
    with TestClient(app) as host, TestClient(app) as guest:
        host_headers, _, started = _start_room(host, guest)
        code = started["code"]
        with host.websocket_connect(
            f"/api/v1/ws/rooms/{code}", headers={"Origin": "http://testserver"}
        ) as websocket:
            assert websocket.receive_json()["type"] == "room.snapshot"
            event_types = [websocket.receive_json()["type"] for _ in range(2)]

        assert "race.started" in event_types
        assert host.get(f"/api/v1/rooms/{code}", headers=host_headers).json()["state"] == "racing"


def _start_room(
    host: TestClient, guest: TestClient
) -> tuple[dict[str, str], dict[str, str], dict[str, object]]:
    host_headers = create_guest(host, "Host Atlas")
    guest_headers = create_guest(guest, "Guest Atlas")
    created = host.post("/api/v1/rooms", headers=host_headers, json={"difficulty": "easy"}).json()
    code = created["code"]
    guest.post(f"/api/v1/rooms/{code}/join", headers=guest_headers)
    for client, headers in ((host, host_headers), (guest, guest_headers)):
        client.post(f"/api/v1/rooms/{code}/ready", headers=headers, json={"ready": True})
    started = host.post(f"/api/v1/rooms/{code}/start", headers=host_headers)
    assert started.status_code == 200
    return host_headers, guest_headers, started.json()


def _own_session(room: dict[str, object]) -> str:
    participants = room["participants"]
    assert isinstance(participants, list)
    participant = next(item for item in participants if item["is_self"])
    session_id = participant["session_id"]
    assert isinstance(session_id, str)
    return session_id


def _edge_to(session: dict[str, object], qid: str) -> dict[str, object]:
    groups = session["relation_groups"]
    assert isinstance(groups, list)
    return next(edge for group in groups for edge in group["edges"] if edge["target"]["qid"] == qid)


def _follow(
    client: TestClient,
    headers: dict[str, str],
    session: dict[str, object],
    edge: dict[str, object],
    command_id: str,
):
    return client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json={
            "type": "follow_edge",
            "client_command_id": command_id,
            "expected_state_version": session["state_version"],
            "edge_token": edge["edge_token"],
        },
    )


def _complete_easy_route(
    client: TestClient, headers: dict[str, str], session_id: str
) -> dict[str, object]:
    session = client.get(f"/api/v1/sessions/{session_id}").json()
    for qid in ("Q2", "Q3", "Q4"):
        response = _follow(client, headers, session, _edge_to(session, qid), f"to-{qid}")
        assert response.status_code == 200, response.json()
        session = response.json()["session"]
    return session


def _replace_room(app, code: str, **changes: object) -> None:
    repository = app.state.container.rooms._repository
    room = asyncio.run(repository.get(code))
    assert room is not None
    asyncio.run(repository.save(replace(room, **changes)))
