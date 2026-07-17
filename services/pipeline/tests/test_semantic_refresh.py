from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from webwoven_pipeline.semantic_refresh import (
    SemanticRefreshError,
    refresh_wikidata_relationships,
)


def test_refresh_rebuilds_edges_and_preserves_enriched_source_metadata(
    tmp_path: Path,
    registry,
) -> None:
    batch_path = tmp_path / "batch.json"
    batch_path.write_bytes(
        _batch_bytes(
            {
                "Q1": {
                    "labels": {"en": {"value": "Animal Farm"}},
                    "descriptions": {"en": {"value": "1945 novella"}},
                    "claims": {"P166": [_statement("Q2", "Q1$list", series_ordinal="13")]},
                },
                "Q2": {
                    "labels": {"en": {"value": "NPR Top 100 Books"}},
                    "descriptions": {"en": {"value": "selection based on public votes"}},
                    "claims": {"P31": [_statement("Q49958", "Q2$poll")]},
                },
            }
        )
    )
    source = {
        "schema_version": 2,
        "source": "wikidata",
        "entities": [{"id": "Q1"}, {"id": "Q2"}],
        "edges": [{"explanation": "stale"}],
        "commons_media_candidates": {"Q1": "Animal Farm.jpg"},
        "media_discovery": {"strategy": "preserve-me"},
        "source_batches": [
            {
                "path": batch_path.name,
                "qids": ["Q1", "Q2"],
                "sha256": hashlib.sha256(batch_path.read_bytes()).hexdigest(),
            }
        ],
    }

    refreshed = refresh_wikidata_relationships(source, tmp_path, registry, ("Q1", "Q2"))

    assert refreshed["commons_media_candidates"] == {"Q1": "Animal Farm.jpg"}
    assert refreshed["media_discovery"] == {"strategy": "preserve-me"}
    assert {edge["explanation"] for edge in refreshed["edges"]} == {
        "Animal Farm ranked #13 on the NPR Top 100 Books."
    }
    assert {edge["series_ordinal"] for edge in refreshed["edges"]} == {"13"}
    assert refreshed["entities"] == [
        {"id": "Q1", "label": "Animal Farm", "description": "1945 novella"},
        {
            "id": "Q2",
            "label": "NPR Top 100 Books",
            "description": "selection based on public votes",
            "semantic_tags": ["ranked_selection", "recognition"],
        },
    ]
    assert source["edges"] == [{"explanation": "stale"}]


def test_refresh_rejects_a_changed_recorded_batch(tmp_path: Path, registry) -> None:
    batch_path = tmp_path / "batch.json"
    batch_path.write_bytes(_batch_bytes({}))
    source = {
        "schema_version": 2,
        "source": "wikidata",
        "source_batches": [{"path": batch_path.name, "qids": [], "sha256": "0" * 64}],
    }

    with pytest.raises(SemanticRefreshError, match="SHA-256 verification"):
        refresh_wikidata_relationships(source, tmp_path, registry, ())


def _statement(target: str, statement_id: str, *, series_ordinal: str | None = None) -> dict:
    result = {
        "id": statement_id,
        "rank": "normal",
        "mainsnak": {
            "snaktype": "value",
            "datavalue": {"value": {"id": target}},
        },
    }
    if series_ordinal is not None:
        result["qualifiers"] = {"P1545": [{"datavalue": {"value": series_ordinal}}]}
    return result


def _batch_bytes(entities: dict) -> bytes:
    return (
        json.dumps(
            {"entities": entities}, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        + "\n"
    ).encode()
