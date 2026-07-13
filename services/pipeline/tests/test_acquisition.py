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
        seeds=(Seed("Q1", "One", "history_people", "Fixture seed"),),
    )

    result = acquire_graph(seeds, registry, client, hops=2, max_entities=10)

    assert tuple(result.entities) == ("Q1", "Q2", "Q3")
    assert result.category_by_qid == {
        "Q1": "history_people",
        "Q2": "history_people",
        "Q3": "history_people",
    }
    assert client.calls == [("Q1",), ("Q2",), ("Q3",)]


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
