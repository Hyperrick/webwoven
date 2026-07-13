"""Strict helpers for decoding adapter-owned JSON documents."""

from datetime import date, datetime
from typing import cast


class PersistenceDataError(ValueError):
    """Stored data does not match the versioned adapter contract."""


def require_object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PersistenceDataError(f"{field} must be an object")
    raw = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in raw):
        raise PersistenceDataError(f"{field} must use string keys")
    return cast(dict[str, object], raw)


def require_list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise PersistenceDataError(f"{field} must be an array")
    return cast(list[object], value)


def require_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise PersistenceDataError(f"{field} must be a string")
    return value


def optional_string(value: object, field: str) -> str | None:
    if value is None:
        return None
    return require_string(value, field)


def require_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PersistenceDataError(f"{field} must be an integer")
    return value


def optional_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    return require_int(value, field)


def require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise PersistenceDataError(f"{field} must be a boolean")
    return value


def require_datetime(value: object, field: str) -> datetime:
    raw = require_string(value, field)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as error:
        raise PersistenceDataError(f"{field} must be an ISO datetime") from error
    if parsed.tzinfo is None:
        raise PersistenceDataError(f"{field} must include a timezone")
    return parsed


def optional_datetime(value: object, field: str) -> datetime | None:
    if value is None:
        return None
    return require_datetime(value, field)


def optional_date(value: object, field: str) -> date | None:
    if value is None:
        return None
    raw = require_string(value, field)
    try:
        return date.fromisoformat(raw)
    except ValueError as error:
        raise PersistenceDataError(f"{field} must be an ISO date") from error


def require_json_object(value: object, field: str) -> dict[str, object]:
    document = require_object(value, field)
    _validate_json(document, field)
    return document


def _validate_json(value: object, field: str) -> None:
    if value is None or isinstance(value, str | bool | int | float):
        return
    if isinstance(value, list):
        items = cast(list[object], value)
        for index, item in enumerate(items):
            _validate_json(item, f"{field}[{index}]")
        return
    if isinstance(value, dict):
        items = cast(dict[object, object], value)
        if not all(isinstance(key, str) for key in items):
            raise PersistenceDataError(f"{field} contains a non-string key")
        for key, item in items.items():
            _validate_json(item, f"{field}.{key}")
        return
    raise PersistenceDataError(f"{field} contains a non-JSON value")
