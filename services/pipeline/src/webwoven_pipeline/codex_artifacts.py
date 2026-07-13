from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from .content_contract import fact_pack_sha256, output_sha256, prompt_sha256
from .content_validation import validate_content
from .models import ContentRequest, GeneratedContent
from .schema_validation import SchemaValidationError, validate_codex_artifact_schema


class CodexArtifactError(ValueError):
    """Raised when a static Codex artifact is malformed or not approved."""


def ingest_codex_artifact(path: Path, request: ContentRequest) -> GeneratedContent:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CodexArtifactError("Codex artifact must be a JSON object")
    payload = cast(dict[str, Any], value)
    try:
        validate_codex_artifact_schema(payload)
    except SchemaValidationError as exc:
        raise CodexArtifactError(str(exc)) from exc
    _validate_bound_values(payload, request)
    content_value = payload["content"]
    if not isinstance(content_value, dict):
        raise CodexArtifactError("content must be an object")
    content = cast(dict[str, Any], content_value)
    validate_content(content, request)
    if payload["output_sha256"] != output_sha256(content):
        raise CodexArtifactError("output hash does not match content")

    approval_value = payload["approval"]
    assert isinstance(approval_value, dict)
    approval = cast(dict[str, Any], approval_value)
    provenance: dict[str, Any] = {
        "generator": "codex",
        "generated_at": payload["generated_at"],
        "prompt_id": payload["prompt_id"],
        "prompt_text": payload["prompt_text"],
        "prompt_sha256": payload["prompt_sha256"],
        "fact_pack_sha256": payload["fact_pack_sha256"],
        "output_sha256": payload["output_sha256"],
        "validation_results": [
            "schema:passed",
            "grounding:passed",
            "answer_leak:passed",
            "language:passed",
            "approval:passed",
        ],
        "approval_status": approval["status"],
        "reviewer": approval["reviewer"],
        "approved_at": approval["approved_at"],
    }
    hints_value = content["hints"]
    explanations_value = content["explanations"]
    recap = content["recap"]
    assert isinstance(hints_value, list)
    assert isinstance(explanations_value, list)
    assert isinstance(recap, str)
    hints = tuple(cast(dict[str, Any], hint) for hint in cast(list[Any], hints_value))
    explanations = tuple(
        cast(dict[str, str], explanation) for explanation in cast(list[Any], explanations_value)
    )
    return GeneratedContent(
        round_id=request.round_id,
        hints=hints,
        explanations=explanations,
        recap=recap,
        provenance=provenance,
    )


def _validate_bound_values(payload: Mapping[str, Any], request: ContentRequest) -> None:
    if payload["round_id"] != request.round_id:
        raise CodexArtifactError("artifact round does not match its fact pack")
    prompt_text = payload["prompt_text"]
    assert isinstance(prompt_text, str)
    if payload["prompt_sha256"] != prompt_sha256(prompt_text):
        raise CodexArtifactError("prompt hash does not match the preserved prompt text")
    if payload["fact_pack_sha256"] != fact_pack_sha256(request):
        raise CodexArtifactError("fact pack hash does not match verified inputs")
