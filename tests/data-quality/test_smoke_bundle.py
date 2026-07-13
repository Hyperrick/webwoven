from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "data" / "fixtures" / "smoke"
CATEGORIES = {"history_people", "nature_science", "arts_culture", "places"}
PLAYABLE_PROPERTIES = {
    "P19",
    "P69",
    "P108",
    "P463",
    "P166",
    "P800",
    "P737",
    "P170",
    "P50",
    "P57",
    "P161",
    "P175",
    "P131",
    "P17",
    "P36",
    "P276",
    "P361",
    "P171",
    "P61",
    "P138",
}


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _json_list(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, list)
    assert all(isinstance(item, dict) for item in value)
    return value


def test_manifest_checksums_cover_every_fixture_artifact() -> None:
    manifest = _json(FIXTURE / "manifest.json")
    assert manifest["graph_schema_version"] == 2
    entries = manifest["artifacts"]
    assert isinstance(entries, list)
    assert {entry["path"] for entry in entries} == {
        path.name for path in FIXTURE.iterdir() if path.name != "manifest.json"
    }
    for entry in entries:
        path = FIXTURE / entry["path"]
        assert path.stat().st_size == entry["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]


def test_smoke_graph_has_locked_round_distribution_and_integrity() -> None:
    with sqlite3.connect(FIXTURE / "graph.sqlite3") as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        rounds = connection.execute("SELECT category, difficulty, published FROM rounds").fetchall()
        assert connection.execute("SELECT COUNT(*) FROM entities").fetchone() == (48,)
        assert connection.execute("SELECT COUNT(*) FROM edges").fetchone() == (96,)
    assert len(rounds) == 100
    assert sum(published for _, _, published in rounds) == 40
    assert Counter(category for category, _, _ in rounds) == Counter(
        {category: 25 for category in CATEGORIES}
    )
    assert Counter((category, difficulty) for category, difficulty, _ in rounds) == Counter(
        {
            (category, difficulty): count
            for category in CATEGORIES
            for difficulty, count in {"easy": 10, "normal": 10, "hard": 5}.items()
        }
    )
    assert Counter(
        (category, difficulty) for category, difficulty, published in rounds if published
    ) == Counter(
        {
            (category, difficulty): count
            for category in CATEGORIES
            for difficulty, count in {"easy": 4, "normal": 4, "hard": 2}.items()
        }
    )


def test_fixture_entities_and_edges_are_readable_but_unmistakably_fictional() -> None:
    entities = _json_list(FIXTURE / "entities.json")
    edges = _json_list(FIXTURE / "edges.json")
    labels = {entity["id"]: entity["label"] for entity in entities}

    assert len(entities) == 48
    assert len(labels) == 48
    assert len(set(labels.values())) == 48
    assert all("waypoint" not in label.casefold() for label in labels.values())
    assert all(entity["description"].startswith("Fictional fixture ") for entity in entities)
    assert all(entity["entity_type"].startswith("fictional_") for entity in entities)
    assert Counter(entity["category"] for entity in entities) == Counter(
        {category: 12 for category in CATEGORIES}
    )

    assert len(edges) == 96
    assert {edge["relation_key"] for edge in edges} == PLAYABLE_PROPERTIES
    assert set(Counter(edge["source_id"] for edge in edges).values()) == {2}
    assert set(Counter(edge["target_id"] for edge in edges).values()) == {2}
    assert set(Counter(edge["statement_id"] for edge in edges).values()) == {2}
    assert all(edge["explanation"].startswith("Fictional fixture fact: ") for edge in edges)
    assert len({edge["explanation"] for edge in edges}) == 48
    assert Counter(edge["inverse"] for edge in edges) == Counter({False: 48, True: 48})


def test_relation_registry_is_locked_and_has_explicit_inverses() -> None:
    registry = _json(ROOT / "data" / "relation-registry" / "relations.v1.json")
    relations = registry["relations"]
    assert {relation["key"] for relation in relations} == PLAYABLE_PROPERTIES
    assert all(relation["inverse_label"] for relation in relations)
    assert registry["classification_properties"] == ["P31", "P279"]
    assert registry["media_property"] == "P18"


def test_anchor_catalog_has_forty_unique_qids_per_category() -> None:
    seeds = _json(ROOT / "data" / "seeds" / "anchors.v1.json")
    groups = seeds["categories"]
    assert {group["id"] for group in groups} == CATEGORIES
    all_qids: list[str] = []
    for group in groups:
        qids = [anchor["qid"] for anchor in group["anchors"]]
        assert len(qids) == 40
        assert len(qids) == len(set(qids))
        assert all(qid.startswith("Q") and qid[1:].isdigit() for qid in qids)
        all_qids.extend(qids)
    assert len(all_qids) == len(set(all_qids))


def test_fixture_carries_no_external_media_without_attribution() -> None:
    attribution = _json(FIXTURE / "attribution.json")
    assert attribution["fixture_only"] is True
    assert "invented for local testing" in attribution["notice"]
    assert attribution["records"] == []
