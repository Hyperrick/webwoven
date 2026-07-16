"""Guest cookies, CSRF/Origin protection, health, and reports."""

from conftest import create_guest
from fastapi.testclient import TestClient
from webwoven_api.main import create_app
from webwoven_api.settings import Settings


def test_health_config_and_guest_cookie(client: TestClient) -> None:
    assert client.get("/health/live").json() == {
        "status": "ok",
        "component": "api",
        "graph_version": None,
    }
    assert client.get("/health/ready").status_code == 200
    assert client.get("/health/graph").json()["status"] == "ok"
    config = client.get("/api/v1/config").json()
    assert config["api_version"] == "v1"
    assert config["daily_rollover_timezone"] == "UTC"

    headers = create_guest(client)
    current = client.get("/api/v1/guests/me")
    assert current.status_code == 200
    assert current.json()["csrf_token"] == headers["X-CSRF-Token"]
    assert client.cookies.get("ww_guest")
    assert client.cookies.get("ww_csrf")
    update = client.patch(
        "/api/v1/guests/me",
        json={"display_name": "Map Reader"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["display_name"] == "Map Reader"


def test_guest_names_are_normalized_and_reserved_roles_are_rejected(
    client: TestClient,
) -> None:
    guest = client.post("/api/v1/guests", json={})
    headers = {
        "Origin": "http://testserver",
        "X-CSRF-Token": guest.json()["csrf_token"],
    }

    normalized = client.patch(
        "/api/v1/guests/me",
        json={"display_name": "  Léa   O’Neil  "},
        headers=headers,
    )
    assert normalized.status_code == 200
    assert normalized.json()["display_name"] == "Léa O’Neil"

    normalized_before_length_check = client.patch(
        "/api/v1/guests/me",
        json={"display_name": "  Atlas                  Reader  "},
        headers=headers,
    )
    assert normalized_before_length_check.status_code == 200
    assert normalized_before_length_check.json()["display_name"] == "Atlas Reader"

    unsupported = client.patch(
        "/api/v1/guests/me",
        json={"display_name": "Atlas<script>"},
        headers=headers,
    )
    assert unsupported.status_code == 422
    assert unsupported.json()["code"] == "invalid_display_name"

    reserved = client.patch(
        "/api/v1/guests/me",
        json={"display_name": "Webwoven Guide"},
        headers=headers,
    )
    assert reserved.status_code == 422
    assert reserved.json()["code"] == "reserved_display_name"


def test_guest_names_do_not_need_to_be_unique(app_settings: Settings) -> None:
    app = create_app(app_settings)
    with TestClient(app) as first, TestClient(app) as second:
        for client in (first, second):
            guest = client.post("/api/v1/guests", json={}).json()
            response = client.patch(
                "/api/v1/guests/me",
                headers={
                    "Origin": "http://testserver",
                    "X-CSRF-Token": guest["csrf_token"],
                },
                json={"display_name": "Paper Fox"},
            )
            assert response.status_code == 200
            assert response.json()["display_name"] == "Paper Fox"


def test_unsafe_requests_require_csrf_and_validate_origin(client: TestClient) -> None:
    headers = create_guest(client)
    missing = client.post(
        "/api/v1/sessions",
        json={"mode": "solo"},
        headers={"Origin": "http://testserver"},
    )
    assert missing.status_code == 403
    assert missing.json()["code"] == "csrf_rejected"

    missing_origin = client.post(
        "/api/v1/sessions",
        json={"mode": "solo"},
        headers={"X-CSRF-Token": headers["X-CSRF-Token"]},
    )
    assert missing_origin.status_code == 403
    assert missing_origin.json()["code"] == "origin_rejected"

    wrong_origin = client.post(
        "/api/v1/sessions",
        json={"mode": "solo"},
        headers={**headers, "Origin": "https://attacker.example"},
    )
    assert wrong_origin.status_code == 403
    assert wrong_origin.json()["code"] == "origin_rejected"


def test_csrf_token_is_bound_to_authenticated_guest(app_settings: Settings) -> None:
    app = create_app(app_settings)
    with TestClient(app) as victim_client, TestClient(app) as attacker_client:
        victim = victim_client.post("/api/v1/guests", json={}).json()
        victim_cookie = victim_client.cookies.get("ww_guest")
        assert victim_cookie is not None
        attacker = attacker_client.post("/api/v1/guests", json={}).json()
        attacker_client.cookies.clear()
        attacker_client.cookies.set("ww_guest", victim_cookie)
        attacker_client.cookies.set("ww_csrf", attacker["csrf_token"])

        response = attacker_client.patch(
            "/api/v1/guests/me",
            headers={
                "Origin": "http://testserver",
                "X-CSRF-Token": attacker["csrf_token"],
            },
            json={"display_name": "Taken Over"},
        )

    assert response.status_code == 403
    assert response.json()["code"] == "csrf_rejected"
    assert victim["id"] != attacker["id"]


def test_content_report_requires_subject(client: TestClient) -> None:
    headers = create_guest(client)
    rejected = client.post(
        "/api/v1/content-reports",
        headers=headers,
        json={"reason": "other", "details": "Something needs review."},
    )
    assert rejected.status_code == 422
    accepted = client.post(
        "/api/v1/content-reports",
        headers=headers,
        json={
            "entity_qid": "Q1",
            "reason": "incorrect",
            "details": "The description needs a source check.",
        },
    )
    assert accepted.status_code == 201
    assert accepted.json()["status"] == "received"
