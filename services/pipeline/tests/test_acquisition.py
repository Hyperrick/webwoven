from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from webwoven_pipeline.acquisition import acquire_graph
from webwoven_pipeline.seeds import Seed, SeedCatalog
from webwoven_pipeline.wikidata import WikidataBatch


class FixtureBatchClient:
    def __init__(self, raw_entities: dict[str, dict[str, Any]], cache_path: Path) -> None:
        self.raw_entities = raw_entities
        self.cache_path = cache_path
        self.calls: list[tuple[str, ...]] = []

    def fetch_entities(self, qids: Iterable[str]) -> tuple[WikidataBatch, ...]:
        requested = tuple(qids)
        self.calls.append(requested)
        entities = {qid: self.raw_entities[qid] for qid in requested}
        return (
            WikidataBatch(
                qids=requested,
                cache_path=self.cache_path,
                sha256="a" * 64,
                payload={"entities": entities},
            ),
        )


def test_acquisition_expands_exactly_two_outgoing_hops(tmp_path, registry) -> None:
    raw_entities = {
        "Q1": _entity_with_part("Q2", "Q1$to-2"),
        "Q2": _entity_with_part("Q3", "Q2$to-3"),
        "Q3": {"id": "Q3", "claims": {}},
    }
    client = FixtureBatchClient(raw_entities, tmp_path / "batch.json")
    seeds = SeedCatalog(
        version=1,
        seeds=(Seed("Q1", "One", "people", "Fixture seed"),),
    )

    result = acquire_graph(seeds, registry, client, hops=2, max_entities=10)

    assert tuple(result.entities) == ("Q1", "Q2", "Q3")
    assert result.category_by_qid == {
        "Q1": "people",
        "Q2": "people",
        "Q3": "people",
    }
    assert client.calls == [("Q1",), ("Q2",), ("Q3",)]


def test_acquisition_cap_counts_only_previously_unseen_entities(tmp_path, registry) -> None:
    raw_entities = {
        "Q1": _entity_with_parts("Q1", "Q2", "Q3"),
        "Q2": {"id": "Q2", "claims": {}},
        "Q3": {"id": "Q3", "claims": {}},
    }
    client = FixtureBatchClient(raw_entities, tmp_path / "batch.json")
    seeds = SeedCatalog(
        version=1,
        seeds=(
            Seed("Q1", "One", "people", "Fixture seed"),
            Seed("Q2", "Two", "people", "Fixture seed"),
        ),
    )

    result = acquire_graph(seeds, registry, client, hops=1, max_entities=3)

    assert tuple(result.entities) == ("Q1", "Q2", "Q3")
    assert client.calls == [("Q1", "Q2"), ("Q3",)]


def test_acquisition_balances_a_capped_frontier_across_categories(tmp_path, registry) -> None:
    raw_entities = {
        "Q1": _entity_with_parts("Q10", "Q11", "Q12"),
        "Q2": _entity_with_parts("Q20", "Q21", "Q22"),
        "Q3": _entity_with_parts("Q30", "Q31", "Q32"),
        "Q4": _entity_with_parts("Q40", "Q41", "Q42"),
        **{f"Q{value}": {"id": f"Q{value}", "claims": {}} for value in range(10, 43)},
    }
    client = FixtureBatchClient(raw_entities, tmp_path / "batch.json")
    seeds = SeedCatalog(
        version=1,
        seeds=(
            Seed("Q1", "History", "people", "Fixture seed"),
            Seed("Q2", "Nature", "nature_life", "Fixture seed"),
            Seed("Q3", "Arts", "art_design", "Fixture seed"),
            Seed("Q4", "Places", "places_architecture", "Fixture seed"),
        ),
    )

    result = acquire_graph(seeds, registry, client, hops=1, max_entities=8)

    assert client.calls[1] == ("Q10", "Q20", "Q30", "Q40")
    assert {result.category_by_qid[qid] for qid in client.calls[1]} == {
        "people",
        "nature_life",
        "art_design",
        "places_architecture",
    }


def _entity_with_part(target: str, statement_id: str) -> dict[str, Any]:
    return {
        "claims": {
            "P361": [
                {
                    "id": statement_id,
                    "rank": "normal",
                    "mainsnak": {
                        "snaktype": "value",
                        "datavalue": {"value": {"id": target}},
                    },
                }
            ]
        }
    }


def _entity_with_parts(*targets: str) -> dict[str, Any]:
    return {
        "claims": {
            "P361": [
                {
                    "id": f"fixture${target}",
                    "rank": "normal",
                    "mainsnak": {
                        "snaktype": "value",
                        "datavalue": {"value": {"id": target}},
                    },
                }
                for target in targets
            ]
        }
    }
