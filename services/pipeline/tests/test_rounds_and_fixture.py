from __future__ import annotations

import hashlib
import json
import sqlite3

from webwoven_pipeline.fixture import build_smoke_graph, generate_smoke_fixture
from webwoven_pipeline.manifest import verify_manifest
from webwoven_pipeline.rounds import generate_rounds
from webwoven_pipeline.taxonomy import CATEGORIES


def test_round_generator_locks_candidate_and_publication_distribution() -> None:
    entities, edges = build_smoke_graph()

    rounds = generate_rounds(entities, edges)

    assert len(rounds) == 100
    assert sum(item.published for item in rounds) == 40
    for category in CATEGORIES:
        selected = [item for item in rounds if item.category == category]
        assert len(selected) == 25
        assert sum(item.published for item in selected) == 10
        assert _counts(selected, published=False) == {"easy": 10, "normal": 10, "hard": 5}
        assert _counts(selected, published=True) == {"easy": 4, "normal": 4, "hard": 2}


def test_smoke_bundle_is_deterministic_and_graphreader_compatible(tmp_path, registry) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    first_build = generate_smoke_fixture(first, registry)
    second_build = generate_smoke_fixture(second, registry)

    assert first_build == second_build
    assert _sha256(first / "graph.sqlite3") == _sha256(second / "graph.sqlite3")
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    verify_manifest(first / "manifest.json")
    with sqlite3.connect(first / "graph.sqlite3") as connection:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        assert metadata["graph_build_id"] == first_build
        assert metadata["schema_version"] == "1"
        assert metadata["round_count"] == "100"
        assert metadata["published_round_count"] == "40"
        assert connection.execute("SELECT COUNT(*) FROM entities").fetchone() == (48,)
        assert connection.execute("SELECT COUNT(*) FROM relation_types").fetchone() == (20,)
        assert connection.execute("SELECT COUNT(*) FROM distances").fetchone()[0] > 100
    reviews = json.loads((first / "fixture-review-decisions.json").read_text())
    assert sum(item["decision"] == "approved" for item in reviews["decisions"]) == 40


def _counts(rounds, *, published: bool) -> dict[str, int]:
    return {
        difficulty: sum(
            item.difficulty == difficulty and (item.published or not published) for item in rounds
        )
        for difficulty in ("easy", "normal", "hard")
    }


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
