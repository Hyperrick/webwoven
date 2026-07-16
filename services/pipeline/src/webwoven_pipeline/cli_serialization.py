from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from .models import ContentRequest, Edge, Entity, Fact, Round


def parse_entities(value: Any) -> tuple[Entity, ...]:
    return tuple(
        Entity(
            id=required_string(item, "id"),
            label=required_string(item, "label"),
            description=required_string(item, "description"),
            entity_type=required_string(item, "entity_type"),
            category=required_string(item, "category"),
            image_path=optional_string(item, "image_path"),
            image_attribution=optional_object(item, "image_attribution"),
            wikipedia_url=optional_string(item, "wikipedia_url"),
        )
        for item in object_list(value, "entities")
    )


def parse_edges(value: Any) -> tuple[Edge, ...]:
    return tuple(
        Edge(
            id=required_string(item, "id"),
            source_id=required_string(item, "source_id"),
            target_id=required_string(item, "target_id"),
            relation_key=required_string(item, "relation_key"),
            statement_id=required_string(item, "statement_id"),
            explanation=required_string(item, "explanation"),
            inverse=required_boolean(item, "inverse"),
            playable=required_boolean(item, "playable"),
        )
        for item in object_list(value, "edges")
    )


def parse_rounds(value: Any) -> tuple[Round, ...]:
    return tuple(
        Round(
            id=required_string(item, "id"),
            start_id=required_string(item, "start_id"),
            target_id=required_string(item, "target_id"),
            category=required_string(item, "category"),
            difficulty=required_string(item, "difficulty"),
            optimal_distance=required_integer(item, "optimal_distance"),
            time_window=required_integer(item, "time_window"),
            published=required_boolean(item, "published"),
        )
        for item in object_list(value, "rounds")
    )


def parse_content_request(value: Any) -> ContentRequest:
    if not isinstance(value, dict):
        raise ValueError("fact pack must be an object with facts")
    content = cast(dict[str, Any], value)
    facts_value = content.get("facts")
    if not isinstance(facts_value, list):
        raise ValueError("fact pack must be an object with facts")
    aliases_value = content.get("target_aliases", [])
    if not isinstance(aliases_value, list):
        raise ValueError("target_aliases must be a string list")
    alias_items = cast(list[Any], aliases_value)
    if any(not isinstance(item, str) for item in alias_items):
        raise ValueError("target_aliases must be a string list")
    aliases = cast(list[str], alias_items)
    facts = tuple(
        Fact(
            id=required_string(item, "id"),
            subject=required_string(item, "subject"),
            relation=required_string(item, "relation"),
            object=required_string(item, "object"),
        )
        for item in object_list(facts_value, "facts")
    )
    return ContentRequest(
        round_id=required_string(content, "round_id"),
        start_label=required_string(content, "start_label"),
        target_label=required_string(content, "target_label"),
        target_aliases=tuple(aliases),
        facts=facts,
    )


def read_json(path: Path) -> object:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    return value


def read_object(path: Path) -> dict[str, Any]:
    value = read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return cast(dict[str, Any], value)


def object_list(value: Any, name: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    result: list[dict[str, Any]] = []
    for item in cast(list[Any], value):
        if not isinstance(item, dict):
            raise ValueError(f"every {name} item must be an object")
        result.append(cast(dict[str, Any], item))
    return tuple(result)


def string_mapping(value: Any, name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    result: dict[str, str] = {}
    for key, item in cast(dict[Any, Any], value).items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(f"every {name} entry must map strings to strings")
        result[key] = item
    return result


def nested_string_mapping(value: Any, name: str) -> dict[str, dict[str, str]]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    result: dict[str, dict[str, str]] = {}
    for key, item in cast(dict[Any, Any], value).items():
        if not isinstance(key, str) or not isinstance(item, dict):
            raise ValueError(f"every {name} entry must map a string to an object")
        result[key] = string_mapping(item, f"{name}.{key}")
    return result


def write_new_json(path: Path, value: object) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to replace output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(serialized, encoding="utf-8")


def required_string(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise ValueError(f"{key} must be a string")
    return item


def optional_string(value: dict[str, Any], key: str) -> str | None:
    item = value.get(key)
    if item is not None and not isinstance(item, str):
        raise ValueError(f"{key} must be a string or null")
    return item


def optional_object(value: dict[str, Any], key: str) -> dict[str, Any] | None:
    item = value.get(key)
    if item is not None and not isinstance(item, dict):
        raise ValueError(f"{key} must be an object or null")
    return cast(dict[str, Any], item) if item is not None else None


def required_integer(value: dict[str, Any], key: str) -> int:
    item = value.get(key)
    if not isinstance(item, int):
        raise ValueError(f"{key} must be an integer")
    return item


def required_boolean(value: dict[str, Any], key: str) -> bool:
    item = value.get(key)
    if not isinstance(item, bool):
        raise ValueError(f"{key} must be a boolean")
    return item
