"""Versioning, idempotency, signed edges, hints, and Daily scoring."""

from conftest import create_guest
from fastapi.testclient import TestClient
from webwoven_api.main import create_app
from webwoven_api.settings import Settings


def test_solo_rounds_cycle_without_an_immediate_repeat(client: TestClient) -> None:
    headers = create_guest(client, "Varied Explorer")
    round_ids = [
        client.post(
            "/api/v1/sessions",
            headers=headers,
            json={"mode": "solo", "difficulty": "normal"},
        ).json()["round_id"]
        for _ in range(3)
    ]

    assert round_ids[0] != round_ids[1]
    assert round_ids[1] != round_ids[2]
    assert round_ids[0] == round_ids[2]


def test_solo_start_is_scheduled_and_early_commands_are_rejected(
    app_settings: Settings,
) -> None:
    app = create_app(app_settings.model_copy(update={"round_intro_seconds": 5}))
    with TestClient(app) as client:
        headers = create_guest(client, "Patient Explorer")
        created = client.post(
            "/api/v1/sessions",
            headers=headers,
            json={"mode": "solo", "difficulty": "hard"},
        )
        session = created.json()

        assert created.status_code == 201
        assert session["category"] == "history_people"
        assert session["difficulty"] == "hard"
        edge = session["relation_groups"][0]["edges"][0]
        early = client.post(
            f"/api/v1/sessions/{session['id']}/commands",
            headers=headers,
            json={
                "type": "follow_edge",
                "client_command_id": "before-intro-finishes",
                "expected_state_version": 0,
                "edge_token": edge["edge_token"],
            },
        )

        assert early.status_code == 422
        assert early.json()["code"] == "round_not_started"


def test_versioned_follow_is_idempotent_and_stale_returns_snapshot(client: TestClient) -> None:
    headers = create_guest(client)
    created = client.post("/api/v1/sessions", headers=headers, json={"mode": "solo"})
    assert created.status_code == 201
    session = created.json()
    assert session["optimal_distance"] == 3
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
    assert len(first.json()["session"]["decision_history"]) == 1

    duplicate = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json=command,
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert duplicate.json()["session"]["state_version"] == 1
    assert len(duplicate.json()["session"]["decision_history"]) == 1

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
    assert len(stale.json()["current"]["decision_history"]) == 1

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
    assert response.json()["session"]["decision_history"] == []


def test_compass_evaluates_the_exact_selected_entity(client: TestClient) -> None:
    headers = create_guest(client, "Precise Navigator")
    session = client.post("/api/v1/sessions", headers=headers, json={"mode": "solo"}).json()
    selected_group = next(
        group
        for group in session["relation_groups"]
        if any(edge["target"]["qid"] == "Q2" for edge in group["edges"])
    )
    response = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json={
            "type": "use_hint",
            "client_command_id": "compass-exact-entity",
            "expected_state_version": session["state_version"],
            "hint_type": "compass",
            "relation_property_id": selected_group["property_id"],
            "entity_qid": "Q2",
        },
    )

    assert response.status_code == 200
    assert response.json()["hint"]["entity_qid"] == "Q2"
    assert response.json()["hint"]["outcome"] == "longer"


def test_follow_and_back_publish_token_free_decision_history(client: TestClient) -> None:
    headers = create_guest(client)
    session = client.post("/api/v1/sessions", headers=headers, json={"mode": "solo"}).json()
    selected = next(
        edge
        for group in session["relation_groups"]
        for edge in group["edges"]
        if edge["target"]["qid"] == "Q2"
    )
    followed = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json={
            "type": "follow_edge",
            "client_command_id": "history-follow",
            "expected_state_version": session["state_version"],
            "edge_token": selected["edge_token"],
        },
    ).json()["session"]

    assert {
        edge["target"]["qid"] for group in followed["relation_groups"] for edge in group["edges"]
    } == {"Q3"}

    follow_stage = followed["decision_history"][0]
    assert follow_stage["index"] == 0
    assert follow_stage["action"] == "follow"
    assert follow_stage["source"]["qid"] == "Q1"
    assert follow_stage["destination"]["qid"] == "Q2"
    assert {choice["target"]["qid"] for choice in follow_stage["choices"]} == {"Q2", "Q5"}
    selected_choice = next(
        choice
        for choice in follow_stage["choices"]
        if choice["id"] == follow_stage["selected_choice_id"]
    )
    assert selected_choice["target"]["qid"] == "Q2"
    assert selected_choice["statement"] == "Ada Lovelace worked with Charles Babbage."
    assert selected_choice["connections"] == [
        {
            "id": "connection:0:Q1:edge-1",
            "relation": {
                "property_id": "P108",
                "label": "worked with",
                "direction": "outgoing",
            },
            "statement": "Ada Lovelace worked with Charles Babbage.",
        }
    ]
    assert "edge_token" not in str(follow_stage)

    backed = client.post(
        f"/api/v1/sessions/{session['id']}/commands",
        headers=headers,
        json={
            "type": "back",
            "client_command_id": "history-back",
            "expected_state_version": followed["state_version"],
        },
    ).json()["session"]
    assert len(backed["decision_history"]) == 2
    back_stage = backed["decision_history"][1]
    assert back_stage["index"] == 1
    assert back_stage["action"] == "back"
    assert back_stage["source"]["qid"] == "Q2"
    assert back_stage["destination"]["qid"] == "Q1"
    assert back_stage["selected_choice_id"] is None
    assert {choice["target"]["qid"] for choice in back_stage["choices"]} == {"Q3"}
    assert "edge_token" not in str(back_stage)
    assert {
        edge["target"]["qid"] for group in backed["relation_groups"] for edge in group["edges"]
    } == {"Q2", "Q5"}

    resumed = client.get(f"/api/v1/sessions/{session['id']}", headers=headers).json()
    assert resumed["decision_history"] == backed["decision_history"]


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
