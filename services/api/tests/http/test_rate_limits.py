"""Sensitive write routes return actionable HTTP 429 responses."""

import pytest
from conftest import create_guest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from webwoven_api.main import create_app
from webwoven_api.settings import Settings


def test_anonymous_guest_creation_is_rate_limited(app_settings: Settings) -> None:
    settings = app_settings.model_copy(update={"rate_limit_guest_creates": 1})
    with TestClient(create_app(settings)) as client:
        assert client.post("/api/v1/guests", json={"display_name": "Atlas One"}).status_code == 201
        response = client.post("/api/v1/guests", json={"display_name": "Atlas Two"})

    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"
    assert int(response.headers["Retry-After"]) >= 1


def test_guest_name_updates_are_rate_limited(app_settings: Settings) -> None:
    settings = app_settings.model_copy(update={"rate_limit_guest_updates": 1})
    with TestClient(create_app(settings)) as client:
        headers = create_guest(client)
        assert (
            client.patch(
                "/api/v1/guests/me",
                headers=headers,
                json={"display_name": "Atlas One"},
            ).status_code
            == 200
        )
        response = client.patch(
            "/api/v1/guests/me",
            headers=headers,
            json={"display_name": "Atlas Two"},
        )

        other_headers = create_guest(client)
        other_guest = client.patch(
            "/api/v1/guests/me",
            headers=other_headers,
            json={"display_name": "Atlas Three"},
        )

    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"
    assert other_guest.status_code == 200


def test_authenticated_content_reports_are_rate_limited(app_settings: Settings) -> None:
    settings = app_settings.model_copy(update={"rate_limit_content_reports": 1})
    with TestClient(create_app(settings)) as client:
        guest = client.post("/api/v1/guests", json={"display_name": "Atlas Player"})
        headers = {
            "Origin": "http://testserver",
            "X-CSRF-Token": guest.json()["csrf_token"],
        }
        body = {
            "entity_qid": "Q42",
            "reason": "incorrect",
            "details": "This relationship needs editorial review.",
        }
        assert client.post("/api/v1/content-reports", json=body, headers=headers).status_code == 201
        response = client.post("/api/v1/content-reports", json=body, headers=headers)

    assert response.status_code == 429
    assert response.json()["code"] == "rate_limited"


def test_session_creation_is_rate_limited(app_settings: Settings) -> None:
    settings = app_settings.model_copy(update={"rate_limit_session_creates": 1})
    with TestClient(create_app(settings)) as client:
        headers = create_guest(client)
        assert client.post("/api/v1/sessions", headers=headers, json={}).status_code == 201
        response = client.post("/api/v1/sessions", headers=headers, json={})

    assert response.status_code == 429


def test_room_creation_and_ready_changes_are_rate_limited(app_settings: Settings) -> None:
    settings = app_settings.model_copy(
        update={"rate_limit_room_creates": 1, "rate_limit_room_ready": 1}
    )
    with TestClient(create_app(settings)) as client:
        headers = create_guest(client)
        first = client.post("/api/v1/rooms", headers=headers, json={"difficulty": "normal"})
        assert first.status_code == 201
        assert (
            client.post("/api/v1/rooms", headers=headers, json={"difficulty": "normal"}).status_code
            == 429
        )

        code = first.json()["code"]
        assert (
            client.post(
                f"/api/v1/rooms/{code}/ready", headers=headers, json={"ready": True}
            ).status_code
            == 200
        )
        response = client.post(
            f"/api/v1/rooms/{code}/ready", headers=headers, json={"ready": False}
        )

    assert response.status_code == 429


def test_room_invite_previews_are_rate_limited(app_settings: Settings) -> None:
    settings = app_settings.model_copy(update={"rate_limit_room_invites": 1})
    with TestClient(create_app(settings)) as client:
        headers = create_guest(client)
        room = client.post("/api/v1/rooms", headers=headers, json={"difficulty": "normal"}).json()
        path = f"/api/v1/rooms/{room['code']}/invite"
        first = client.get(path)
        response = client.get(path)

    assert first.status_code == 200
    assert response.status_code == 429


def test_websocket_resume_limit_closes_before_accept(app_settings: Settings) -> None:
    settings = app_settings.model_copy(update={"rate_limit_ws_resumes": 1})
    with TestClient(create_app(settings)) as client:
        headers = create_guest(client)
        room = client.post("/api/v1/rooms", headers=headers, json={"difficulty": "normal"}).json()
        ws_headers = {"Origin": "http://testserver"}
        with client.websocket_connect(
            f"/api/v1/ws/rooms/{room['code']}", headers=ws_headers
        ) as websocket:
            assert websocket.receive_json()["type"] == "room.snapshot"

        with (
            pytest.raises(WebSocketDisconnect) as disconnected,
            client.websocket_connect(f"/api/v1/ws/rooms/{room['code']}", headers=ws_headers),
        ):
            pass

    assert disconnected.value.code == 1013


def test_websocket_concurrent_limit_closes_before_accept(app_settings: Settings) -> None:
    settings = app_settings.model_copy(
        update={"rate_limit_ws_resumes": 10, "websocket_concurrent_per_guest": 1}
    )
    with TestClient(create_app(settings)) as client:
        headers = create_guest(client)
        room = client.post("/api/v1/rooms", headers=headers, json={"difficulty": "normal"}).json()
        ws_headers = {"Origin": "http://testserver"}
        with client.websocket_connect(
            f"/api/v1/ws/rooms/{room['code']}", headers=ws_headers
        ) as first:
            assert first.receive_json()["type"] == "room.snapshot"
            with (
                pytest.raises(WebSocketDisconnect) as disconnected,
                client.websocket_connect(f"/api/v1/ws/rooms/{room['code']}", headers=ws_headers),
            ):
                pass

    assert disconnected.value.code == 1013
