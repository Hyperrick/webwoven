"""Shared API value objects with stable wire meaning."""

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorResponse(ApiModel):
    code: str
    message: str


class EntityResponse(ApiModel):
    qid: str
    label: str
    description: str | None
    category: str
    entity_type: str
    image_path: str | None
