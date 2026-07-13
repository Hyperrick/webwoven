"""API fixtures with an isolated offline graph and in-memory persistence."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from webwoven_api.main import create_app
from webwoven_api.settings import Settings


@pytest.fixture
def app_settings(tmp_path: Path) -> Settings:
    return Settings(
        environment="testing",
        origin="http://testserver",
        api_origin="http://testserver",
        graph_path=tmp_path / "missing.sqlite3",
        allow_demo_graph=True,
        session_secret="test-session-secret-with-more-than-32-bytes",
        edge_secret="test-edge-secret-with-more-than-32-bytes",
    )


@pytest.fixture
def client(app_settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(app_settings)) as test_client:
        yield test_client


def create_guest(client: TestClient, name: str = "Atlas Player") -> dict[str, str]:
    response = client.post("/api/v1/guests", json={"display_name": name})
    assert response.status_code == 201
    token = response.json()["csrf_token"]
    return {"X-CSRF-Token": token, "Origin": "http://testserver"}
