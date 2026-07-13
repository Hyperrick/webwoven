"""Production configuration safety checks."""

import pytest
from pydantic import ValidationError
from webwoven_api.settings import Settings


def test_webwoven_env_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEBWOVEN_ENV", "testing")
    assert Settings(_env_file=None).environment == "testing"


def test_production_rejects_default_secrets() -> None:
    with pytest.raises(ValidationError, match="Production requires unique"):
        Settings(environment="production", _env_file=None)


def test_production_rejects_documented_placeholder_secrets() -> None:
    with pytest.raises(ValidationError, match="Production requires unique"):
        Settings(
            environment="production",
            session_secret="replace-with-at-least-32-random-bytes",
            edge_secret="replace-with-a-different-32-byte-secret",
            _env_file=None,
        )


def test_production_rejects_low_entropy_secrets() -> None:
    with pytest.raises(ValidationError, match="Production requires unique"):
        Settings(
            environment="production",
            session_secret="a" * 32,
            edge_secret="b" * 32,
            _env_file=None,
        )


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValidationError, match="secure cookies"):
        Settings(
            environment="production",
            session_secret="a-unique-session-secret-with-32-bytes",
            edge_secret="a-different-edge-secret-with-32-bytes",
            cookie_secure=False,
            _env_file=None,
        )


def test_environment_rejects_unknown_values() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="Production", _env_file=None)  # type: ignore[arg-type]


def test_production_requires_https_origins() -> None:
    with pytest.raises(ValidationError, match="HTTPS browser origin"):
        Settings(
            environment="production",
            origin="http://webwoven.example.com",
            api_origin="https://webwoven.example.com",
            session_secret="a-unique-session-secret-with-32-bytes",
            edge_secret="a-different-edge-secret-with-32-bytes",
            cookie_secure=True,
            _env_file=None,
        )


def test_valid_production_settings_are_accepted() -> None:
    settings = Settings(
        environment="production",
        origin="https://webwoven.example.com",
        api_origin="https://webwoven.example.com",
        session_secret="a-unique-session-secret-with-32-bytes",
        edge_secret="a-different-edge-secret-with-32-bytes",
        cookie_secure=True,
        _env_file=None,
    )

    assert settings.environment == "production"
