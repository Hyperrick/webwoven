from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast


@dataclass(frozen=True, slots=True)
class WikidataMediaCandidate:
    file_name: str
    property_id: str


# Prefer a direct depiction, then other entity-specific views, maps and marks.
# Audio, video, generic category artwork and non-media identifiers are excluded.
MEDIA_PROPERTY_PRIORITY = (
    "P18",  # image
    "P2716",  # montage image
    "P4291",  # panoramic view
    "P8592",  # aerial view
    "P3451",  # nighttime view
    "P5252",  # winter view
    "P948",  # page banner
    "P242",  # locator map image
    "P1943",  # location map
    "P1621",  # detail map
    "P5555",  # schematic
    "P94",  # coat of arms image
    "P41",  # flag image
    "P154",  # logo image
    "P8972",  # small logo or icon
    "P2910",  # icon
    "P158",  # seal image
    "P1801",  # plaque image
    "P109",  # signature
    "P1442",  # image of grave
    "P2425",  # service ribbon image
)


def wikidata_media_candidate(
    raw: Mapping[str, Any],
) -> WikidataMediaCandidate | None:
    """Return the highest-priority deterministic Commons media claim."""
    claims_value = raw.get("claims")
    if not isinstance(claims_value, dict):
        return None
    claims = cast(dict[str, Any], claims_value)
    for property_id in MEDIA_PROPERTY_PRIORITY:
        file_name = _preferred_file_name(claims.get(property_id))
        if file_name is not None:
            return WikidataMediaCandidate(file_name, property_id)
    return None


def _preferred_file_name(statements_value: object) -> str | None:
    if not isinstance(statements_value, list):
        return None
    statements = cast(list[Any], statements_value)
    names: list[tuple[int, str]] = []
    for statement in statements:
        if not isinstance(statement, dict):
            continue
        statement_object = cast(dict[str, Any], statement)
        rank = statement_object.get("rank", "normal")
        if rank == "deprecated":
            continue
        mainsnak_value = statement_object.get("mainsnak")
        mainsnak = cast(dict[str, Any], mainsnak_value) if isinstance(mainsnak_value, dict) else {}
        if mainsnak.get("snaktype") != "value":
            continue
        data_value_value = mainsnak.get("datavalue")
        data_value = (
            cast(dict[str, Any], data_value_value) if isinstance(data_value_value, dict) else {}
        )
        name = data_value.get("value")
        if isinstance(name, str) and name.strip():
            names.append((0 if rank == "preferred" else 1, name.strip().replace("_", " ")))
    return min(names)[1] if names else None
