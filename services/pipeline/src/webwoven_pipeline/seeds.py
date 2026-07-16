from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .taxonomy import CATEGORIES

ANCHORS_PER_CATEGORY = 20


class SeedError(ValueError):
    """Raised when the reviewed anchor file is invalid."""


@dataclass(frozen=True, slots=True)
class Seed:
    qid: str
    label: str
    category: str
    reason: str


@dataclass(frozen=True, slots=True)
class SeedCatalog:
    version: int
    seeds: tuple[Seed, ...]

    @property
    def qids(self) -> tuple[str, ...]:
        return tuple(seed.qid for seed in self.seeds)

    @property
    def category_by_qid(self) -> dict[str, str]:
        return {seed.qid: seed.category for seed in self.seeds}


def load_seeds(path: Path) -> SeedCatalog:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SeedError("seed file must have a categories list")
    payload = cast(dict[str, Any], value)
    categories_value = payload.get("categories")
    if not isinstance(categories_value, list):
        raise SeedError("seed file must have a categories list")
    categories = cast(list[Any], categories_value)
    version = payload.get("version")
    if not isinstance(version, int) or version < 1:
        raise SeedError("seed version must be a positive integer")

    seeds: list[Seed] = []
    found_categories: list[str] = []
    for category_value in categories:
        category, category_seeds = _parse_category(category_value)
        found_categories.append(category)
        seeds.extend(category_seeds)
    if tuple(found_categories) != CATEGORIES:
        raise SeedError(f"categories must appear in canonical order: {CATEGORIES}")
    qids = [seed.qid for seed in seeds]
    if len(qids) != len(set(qids)):
        raise SeedError("an anchor QID can belong to only one starter category")
    return SeedCatalog(version=version, seeds=tuple(seeds))


def _parse_category(value: Any) -> tuple[str, tuple[Seed, ...]]:
    if not isinstance(value, dict):
        raise SeedError("each category must be an object")
    item = cast(dict[str, Any], value)
    category = item.get("id")
    anchors_value = item.get("anchors")
    if not isinstance(category, str) or category not in CATEGORIES:
        raise SeedError("unknown seed category")
    if not isinstance(anchors_value, list) or not anchors_value:
        raise SeedError("each known category must contain anchors")
    anchors = cast(list[Any], anchors_value)
    parsed = tuple(_parse_seed(item, category) for item in anchors)
    if len(parsed) != ANCHORS_PER_CATEGORY:
        raise SeedError(f"{category} must contain exactly {ANCHORS_PER_CATEGORY} curated anchors")
    return category, parsed


def _parse_seed(value: Any, category: str) -> Seed:
    if not isinstance(value, dict):
        raise SeedError("each anchor must be an object")
    item = cast(dict[str, Any], value)
    qid = item.get("qid")
    label = item.get("label")
    reason = item.get("reason")
    if not isinstance(qid, str) or not qid.startswith("Q") or not qid[1:].isdigit():
        raise SeedError(f"invalid anchor QID: {qid}")
    if not isinstance(label, str) or not label.strip():
        raise SeedError(f"anchor {qid} needs a review label")
    if not isinstance(reason, str) or not reason.strip():
        raise SeedError(f"anchor {qid} needs a review reason")
    return Seed(qid=qid, label=label.strip(), category=category, reason=reason.strip())
