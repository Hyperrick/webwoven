"""Versioning, idempotency, signed edges, hints, and Daily scoring."""

from conftest import create_guest
from fastapi.testclient import TestClient


def test_versioned_follow_is_idempotent_and_stale_returns_snapshot(client: TestClient) -> None:
    headers = create_guest(client)
    created = client.post("/api/v1/sessions", headers=headers, json={"mode": "solo"})
    assert created.status_code == 201
    session = created.json()
    edge_token = session["relation_groups"][0]["edges"][0]["edge_token"]
    command = {
        "type": "follow_edge",
        "client_command_id": "move-one",
        "expected_state_version": 0,
        "edge_token": edge_token,
    }
    first = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json=command,
    )
    assert first.status_code == 200
    assert first.json()["session"]["state_version"] == 1

    duplicate = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json=command,
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["session"]["state_version"] == 1

    stale = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json={
            "type": "back",
            "client_command_id": "stale-back",
            "expected_state_version": 0,
        },
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "stale_state"
    assert stale.json()["current"]["state_version"] == 1

    other_headers = create_guest(client, "Other Player")
    cross_guest_duplicate = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=other_headers,
        json=command,
    )
    assert cross_guest_duplicate.status_code == 403


def test_tampered_edge_token_is_rejected(client: TestClient) -> None:
    headers = create_guest(client)
    session = client.post("/api/v1/sessions", headers=headers, json={"mode": "solo"}).json()
    token = session["relation_groups"][0]["edges"][0]["edge_token"]
    tampered = f"{token[:-1]}{'A' if token[-1] != 'A' else 'B'}"
    response = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json={
            "type": "follow_edge",
            "client_command_id": "tampered",
            "expected_state_version": 0,
            "edge_token": tampered,
        },
    )
    assert response.status_code == 403


def test_hint_is_graph_grounded_and_penalized(client: TestClient) -> None:
    headers = create_guest(client)
    session = client.post("/api/v1/sessions", headers=headers, json={"mode": "solo"}).json()
    response = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json={
            "type": "use_hint",
            "client_command_id": "lens-one",
            "expected_state_version": 0,
            "hint_type": "lens",
        },
    )
    assert response.status_code == 200
    assert response.json()["hint"]["relation_property_id"] in {"P108", "P19"}
    assert response.json()["session"]["hint_penalty"] == 150


def test_daily_completion_enters_leaderboard(client: TestClient) -> None:
    headers = create_guest(client, "Daily Player")
    session = client.post("/api/v1/sessions", headers=headers, json={"mode": "daily"}).json()
    assert session["daily_day"] is not None
    for target_qid in ("Q2", "Q3", "Q4"):
        edge = next(
            edge
            for group in session["relation_groups"]
            for edge in group["edges"]
            if edge["target"]["qid"] == target_qid
        )
        response = client.post(
            f"/api/v1/sessions/{session['id']}/commands",
            headers=headers,
            json={
                "type": "follow_edge",
                "client_command_id": f"to-{target_qid}",
                "expected_state_version": session["state_version"],
                "edge_token": edge["edge_token"],
            },
        )
        assert response.status_code == 200
        session = response.json()["session"]
    assert session["status"] == "completed"
    leaderboard = client.get("/api/v1/leaderboards/daily").json()
    assert leaderboard["entries"][0]["display_name"] == "Daily Player"
    assert leaderboard["entries"][0]["rank"] == 1
