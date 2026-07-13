"""Runtime configuration, health, and content-report contracts."""

from typing import Literal

from pydantic import Field

from webwoven_api.http.contracts.common import ApiModel


class ConfigResponse(ApiModel):
    api_version: Literal["v1"] = "v1"
    graph_version: str
    categories: list[str]
    difficulties: list[str]
    modes: list[str]
    daily_rollover_timezone: Literal["UTC"] = "UTC"
    room_min_players: Literal[2] = 2
    room_max_players: Literal[4] = 4


class HealthResponse(ApiModel):
    status: Literal["ok", "degraded"]
    component: str
    graph_version: str | None = None


class ContentReportRequest(ApiModel):
    entity_qid: str | None = Field(default=None, max_length=40)
    edge_id: str | None = Field(default=None, min_length=1, max_length=100)
    round_id: str | None = Field(default=None, max_length=100)
    reason: Literal["incorrect", "offensive", "license", "broken_media", "other"]
    details: str = Field(min_length=5, max_length=1000)


class ContentReportResponse(ApiModel):
    id: str
    status: Literal["received"] = "received"
