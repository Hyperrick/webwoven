from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .models import Relation


class RegistryError(ValueError):
    """Raised when a relation registry violates the pipeline contract."""


@dataclass(frozen=True, slots=True)
class RelationRegistry:
    version: int
    relations: tuple[Relation, ...]
    classification_properties: tuple[str, ...]
    media_property: str

    @property
    def by_key(self) -> dict[str, Relation]:
        return {relation.key: relation for relation in self.relations}

    @property
    def playable_keys(self) -> frozenset[str]:
        return frozenset(relation.key for relation in self.relations if relation.playable)


def load_registry(path: Path) -> RelationRegistry:
    payload = _read_object(path)
    relations_value = payload.get("relations")
    if not isinstance(relations_value, list):
        raise RegistryError("relations must be a list")
    relations_payload = cast(list[Any], relations_value)

    relations = tuple(_parse_relation(item) for item in relations_payload)
    keys = [relation.key for relation in relations]
    if len(relations) != 20:
        raise RegistryError(f"registry must define exactly 20 relations, found {len(relations)}")
    if len(keys) != len(set(keys)):
        raise RegistryError("relation keys must be unique")
    if keys != sorted(keys, key=lambda value: int(value[1:])):
        raise RegistryError("relations must be ordered by numeric property ID")

    classifications = _string_tuple(
        payload.get("classification_properties"),
        "classification_properties",
    )
    if set(classifications) != {"P31", "P279"}:
        raise RegistryError("classification_properties must be P31 and P279")
    media_property = payload.get("media_property")
    if media_property != "P18":
        raise RegistryError("media_property must be P18")

    version = payload.get("version")
    if not isinstance(version, int) or version < 1:
        raise RegistryError("version must be a positive integer")
    return RelationRegistry(version, relations, classifications, media_property)


def _parse_relation(value: Any) -> Relation:
    if not isinstance(value, dict):
        raise RegistryError("every relation must be an object")
    item = cast(dict[str, Any], value)
    required = ("key", "forward_label", "inverse_label", "category")
    if any(not isinstance(item.get(key), str) for key in required):
        raise RegistryError(f"relation is missing a required string: {item!r}")
    key_value = item["key"]
    forward_value = item["forward_label"]
    inverse_value = item["inverse_label"]
    category_value = item["category"]
    assert isinstance(key_value, str)
    assert isinstance(forward_value, str)
    assert isinstance(inverse_value, str)
    assert isinstance(category_value, str)
    if not all(
        value.strip() for value in (key_value, forward_value, inverse_value, category_value)
    ):
        raise RegistryError(f"relation contains an empty required string: {item!r}")
    key = key_value
    if not key.startswith("P") or not key[1:].isdigit():
        raise RegistryError(f"invalid Wikidata property ID: {key}")
    max_targets = item.get("max_targets", 8)
    if not isinstance(max_targets, int) or not 1 <= max_targets <= 8:
        raise RegistryError(f"max_targets for {key} must be between 1 and 8")
    playable = item.get("playable", True)
    if not isinstance(playable, bool):
        raise RegistryError(f"playable for {key} must be boolean")
    return Relation(
        key=key,
        forward_label=forward_value.strip(),
        inverse_label=inverse_value.strip(),
        category=category_value.strip(),
        max_targets=max_targets,
        playable=playable,
    )


def _read_object(path: Path) -> dict[str, Any]:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RegistryError(f"{path} must contain a JSON object")
    return cast(dict[str, Any], value)


def _string_tuple(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise RegistryError(f"{name} must be a list of strings")
    items = cast(list[Any], value)
    if any(not isinstance(item, str) for item in items):
        raise RegistryError(f"{name} must be a list of strings")
    return tuple(cast(list[str], items))
