from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from .json_values import json_object

WIKIPEDIA_SITE_PRIORITY = (
    "enwiki",
    "dewiki",
    "frwiki",
    "eswiki",
    "itwiki",
    "ptwiki",
    "nlwiki",
    "plwiki",
    "ruwiki",
    "jawiki",
    "zhwiki",
    "svwiki",
)


def commons_category_name(raw: Mapping[str, Any]) -> str | None:
    """Return the preferred Commons category (P373) for an entity."""
    claims_value = raw.get("claims")
    if not isinstance(claims_value, dict):
        return None
    claims = cast(dict[str, Any], claims_value)
    statements_value = claims.get("P373")
    if not isinstance(statements_value, list):
        return None
    names: list[tuple[int, str]] = []
    for statement_value in cast(list[object], statements_value):
        if not isinstance(statement_value, Mapping):
            continue
        statement = cast(Mapping[str, Any], statement_value)
        rank_value: object = statement.get("rank", "normal")
        rank = rank_value if isinstance(rank_value, str) else "normal"
        if rank == "deprecated":
            continue
        mainsnak_value: object = statement.get("mainsnak")
        mainsnak = json_object(mainsnak_value)
        if mainsnak.get("snaktype") != "value":
            continue
        data_value: object = mainsnak.get("datavalue")
        data = json_object(data_value)
        value: object = data.get("value")
        if isinstance(value, str) and value.strip():
            names.append((0 if rank == "preferred" else 1, value.strip()))
    return min(names)[1] if names else None


def wikipedia_sitelinks(raw: Mapping[str, Any]) -> dict[str, str]:
    """Return a bounded, deterministic set of Wikipedia article titles."""
    sitelinks_value = raw.get("sitelinks")
    if not isinstance(sitelinks_value, dict):
        return {}
    sitelinks = cast(dict[str, Any], sitelinks_value)
    result: dict[str, str] = {}
    for site in WIKIPEDIA_SITE_PRIORITY:
        item_value: object = sitelinks.get(site)
        item = json_object(item_value)
        title: object = item.get("title")
        if isinstance(title, str) and title.strip():
            result[site] = title.strip()
    return result
