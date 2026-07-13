from __future__ import annotations

import json
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CODEX_ARTIFACT_SCHEMA_PATH = PROJECT_ROOT / "data/manifests/codex-content-artifact.schema.json"


class SchemaValidationError(ValueError):
    """Raised when content does not satisfy the committed JSON Schema."""


class ErrorIteratorValidator(Protocol):
    """Typed surface used from jsonschema's dynamically generated validator class."""

    def iter_errors(self, instance: object) -> Iterable[ValidationError]: ...


def validate_codex_artifact_schema(payload: object) -> None:
    """Validate an artifact against the committed Draft 2020-12 schema."""

    _validate(payload, _artifact_validator(), "artifact")


def validate_content_schema(payload: object) -> None:
    """Validate fallback or assisted copy against the schema's content contract."""

    _validate(payload, _content_validator(), "content")


@lru_cache(maxsize=1)
def _artifact_validator() -> Draft202012Validator:
    schema = _load_committed_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@lru_cache(maxsize=1)
def _content_validator() -> Draft202012Validator:
    schema = _load_committed_schema()
    properties_value: object = schema.get("properties")
    if not isinstance(properties_value, dict):
        raise SchemaValidationError("committed artifact schema has no properties object")
    properties = cast(dict[str, Any], properties_value)
    content_schema_value: object = properties.get("content")
    if not isinstance(content_schema_value, dict):
        raise SchemaValidationError("committed artifact schema has no content contract")
    content_schema = cast(dict[str, Any], content_schema_value)
    Draft202012Validator.check_schema(content_schema)
    return Draft202012Validator(content_schema, format_checker=FormatChecker())


@lru_cache(maxsize=1)
def _load_committed_schema() -> dict[str, Any]:
    try:
        value: object = json.loads(CODEX_ARTIFACT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaValidationError(
            f"cannot load committed schema at {CODEX_ARTIFACT_SCHEMA_PATH}"
        ) from exc
    if not isinstance(value, dict):
        raise SchemaValidationError("committed artifact schema must be a JSON object")
    return cast(dict[str, Any], value)


def _validate(
    payload: object,
    validator: Draft202012Validator,
    label: str,
) -> None:
    error_iterator = cast(ErrorIteratorValidator, validator)
    errors = sorted(
        error_iterator.iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if not errors:
        return
    error = errors[0]
    path = ".".join(str(part) for part in error.absolute_path)
    location = f" at {path}" if path else ""
    raise SchemaValidationError(f"{label} schema validation failed{location}: {error.message}")
