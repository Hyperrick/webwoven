"""Environment-backed API configuration."""

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEVELOPMENT_SECRET = "development-only-change-me-32-bytes"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WEBWOVEN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    environment: Literal["development", "testing", "production"] = Field(
        default="development",
        validation_alias=AliasChoices("WEBWOVEN_ENV", "WEBWOVEN_ENVIRONMENT"),
    )
    origin: str = "http://localhost:5173"
    api_origin: str = "http://localhost:8000"
    database_url: str = "postgresql+asyncpg://webwoven:webwoven@localhost:5432/webwoven"
    valkey_url: str = "redis://localhost:6379/0"
    graph_path: Path = Path("data/builds/current/graph.sqlite3")
    graph_manifest_path: Path = Path("data/builds/current/manifest.json")
    session_secret: str = Field(default=_DEVELOPMENT_SECRET, min_length=32)
    edge_secret: str = Field(default="development-edge-change-me-32-bytes", min_length=32)
    cookie_secure: bool = False
    cookie_name: str = "ww_guest"
    csrf_cookie_name: str = "ww_csrf"
    edge_token_ttl_seconds: int = Field(default=300, ge=30, le=3600)
    round_intro_seconds: float = Field(default=5, ge=0, le=15)
    use_memory_persistence: bool = True
    auto_create_schema: bool = True
    room_active_ttl_seconds: int = Field(default=3600, ge=300, le=86400)
    room_completed_ttl_seconds: int = Field(default=600, ge=300, le=86400)
    room_lock_lease_seconds: int = Field(default=30, ge=5, le=120)
    room_lock_wait_seconds: float = Field(default=5, ge=0.1, le=30)
    room_event_stream_max_length: int = Field(default=200, ge=50, le=2000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    rate_limit_guest_creates: int = Field(default=20, ge=1, le=1000)
    rate_limit_guest_updates: int = Field(default=10, ge=1, le=1000)
    rate_limit_session_creates: int = Field(default=30, ge=1, le=1000)
    rate_limit_session_commands: int = Field(default=180, ge=1, le=5000)
    rate_limit_room_creates: int = Field(default=10, ge=1, le=1000)
    rate_limit_room_actions: int = Field(default=60, ge=1, le=1000)
    rate_limit_room_ready: int = Field(default=60, ge=1, le=1000)
    rate_limit_room_invites: int = Field(default=120, ge=1, le=5000)
    rate_limit_content_reports: int = Field(default=10, ge=1, le=100)
    rate_limit_ws_resumes: int = Field(default=30, ge=1, le=1000)
    websocket_concurrent_per_guest: int = Field(default=3, ge=1, le=20)
    websocket_idle_timeout_seconds: int = Field(default=120, ge=10, le=3600)
    websocket_max_lifetime_seconds: int = Field(default=900, ge=1, le=86400)

    @model_validator(mode="after")
    def reject_development_secrets_in_production(self) -> "Settings":
        weak = _looks_like_placeholder(self.session_secret) or _looks_like_placeholder(
            self.edge_secret
        )
        if self.environment == "production" and weak:
            raise ValueError("Production requires unique session and edge secrets")
        if self.environment == "production" and not self.cookie_secure:
            raise ValueError("Production requires secure cookies")
        if self.environment == "production" and not self.origin.startswith("https://"):
            raise ValueError("Production requires an HTTPS browser origin")
        if self.environment == "production" and not self.api_origin.startswith("https://"):
            raise ValueError("Production requires an HTTPS API origin")
        if self.session_secret == self.edge_secret:
            raise ValueError("Session and edge secrets must be different")
        return self


def _looks_like_placeholder(value: str) -> bool:
    folded = value.casefold()
    return folded.startswith(("development-", "replace-with-")) or len(set(value)) < 8
