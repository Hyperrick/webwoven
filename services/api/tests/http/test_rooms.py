"""Two-player lobby, server-created relay sessions, and WebSocket snapshot."""

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
