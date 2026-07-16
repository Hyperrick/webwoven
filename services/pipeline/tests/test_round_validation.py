from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import Any

import pytest
from webwoven_pipeline.commons_assets import (
    CommonsAsset,
    CommonsMediaBundle,
    enrich_entities_with_commons,
)
from webwoven_pipeline.fixture import build_smoke_graph
from webwoven_pipeline.models import Edge, Entity, MediaRecord, Round
from webwoven_pipeline.registry import RelationRegistry
from webwoven_pipeline.round_validation import RoundValidationError, validate_round_selection
from webwoven_pipeline.rounds import DEFAULT_SELECTION_SEED, TIME_WINDOWS, generate_rounds
from webwoven_pipeline.wikidata_bundle import build_wikidata_bundle


def test_round_selection_passes_deterministic_publication_policy(registry) -> None:
    entities, edges = build_smoke_graph()
    rounds = generate_rounds(entities, edges)

    report = _validate(registry, rounds, entities, edges)

    assert report["status"] == "passed"
    assert report["policy"] == "deterministic-round-publication-v1"
    assert report["inputs"]["selection_seed"] == DEFAULT_SELECTION_SEED
    assert report["inputs"]["registry_version"] == registry.version
    assert len(report["inputs"]["endpoint_catalog_sha256"]) == 64
    assert report["summary"] == {
        "candidate_rounds": 100,
        "published_rounds": 40,
        "curated_endpoints": 120,
    }
    assert all(report["checks"].values())
    assert sum(item["publication_status"] == "published" for item in report["rounds"]) == 40


def test_round_selection_fails_closed_for_an_uncurated_endpoint(registry) -> None:
    entities, edges = build_smoke_graph()
    rounds = generate_rounds(entities, edges)
    invalid = (replace(rounds[0], start_id="Q999999999"), *rounds[1:])

    with pytest.raises(RoundValidationError, match="all_round_checks"):
        _validate(registry, invalid, entities, edges)


def test_round_selection_rejects_invalid_time_window(registry) -> None:
    entities, edges = build_smoke_graph()
    rounds = generate_rounds(entities, edges)
    invalid = (replace(rounds[0], time_window=999), *rounds[1:])

    with pytest.raises(RoundValidationError, match="all_round_checks"):
        _validate(registry, invalid, entities, edges)


def test_round_selection_rejects_difficulty_that_disagrees_with_distance(registry) -> None:
    entities, edges = build_smoke_graph()
    rounds = generate_rounds(entities, edges)
    wrong_difficulty = "hard" if rounds[0].difficulty != "hard" else "easy"
    invalid = (
        replace(
            rounds[0],
            difficulty=wrong_difficulty,
            time_window=TIME_WINDOWS[wrong_difficulty],
        ),
        *rounds[1:],
    )

    with pytest.raises(RoundValidationError, match="all_round_checks"):
        _validate(registry, invalid, entities, edges)


def test_round_selection_rejects_category_swaps_that_preserve_distribution(registry) -> None:
    entities, edges = build_smoke_graph()
    rounds = list(generate_rounds(entities, edges))
    first = next(
        index
        for index, item in enumerate(rounds)
        if item.category == "people" and item.difficulty == "easy" and item.published
    )
    second = next(
        index
        for index, item in enumerate(rounds)
        if item.category == "places_architecture" and item.difficulty == "easy" and item.published
    )
    first_category = rounds[first].category
    rounds[first] = replace(rounds[first], category=rounds[second].category)
    rounds[second] = replace(rounds[second], category=first_category)

    with pytest.raises(RoundValidationError, match="all_round_checks"):
        _validate(registry, tuple(rounds), entities, edges)


def test_round_selection_rejects_duplicate_round_ids(registry) -> None:
    entities, edges = build_smoke_graph()
    rounds = generate_rounds(entities, edges)
    invalid = (rounds[0], replace(rounds[1], id=rounds[0].id), *rounds[2:])

    with pytest.raises(RoundValidationError, match="unique_round_ids"):
        _validate(registry, invalid, entities, edges)


def test_round_selection_rejects_missing_playable_edge_metadata(registry) -> None:
    entities, edges = build_smoke_graph()
    rounds = generate_rounds(entities, edges)
    invalid_edges = (replace(edges[0], explanation=""), *edges[1:])

    with pytest.raises(RoundValidationError, match="playable_edge_metadata_present"):
        _validate(registry, rounds, entities, invalid_edges)


def test_round_selection_rejects_non_allowlisted_playable_relation(registry) -> None:
    entities, edges = build_smoke_graph()
    rounds = generate_rounds(entities, edges)
    invalid_edges = (replace(edges[0], relation_key="P999999"), *edges[1:])

    with pytest.raises(RoundValidationError, match="allowlisted_playable_relations"):
        _validate(registry, rounds, entities, invalid_edges)


def test_wikidata_bundle_writes_validation_report_for_endpoint_iterator(tmp_path, registry) -> None:
    entities, edges = build_smoke_graph()
    destination = tmp_path / "bundle"

    build_wikidata_bundle(
        destination,
        registry,
        entities,
        edges,
        ({"path": "batch.json", "qids": [item.id for item in entities], "sha256": "0" * 64},),
        endpoint_ids=(item.id for item in entities),
        created_at="2026-07-15T00:00:00Z",
    )

    report = json.loads((destination / "round-validation-report.json").read_text())
    manifest = json.loads((destination / "manifest.json").read_text())
    assert report["status"] == "passed"
    assert report["summary"]["curated_endpoints"] == 120
    assert any(
        item["path"] == "round-validation-report.json" and item["role"] == "round_validation_report"
        for item in manifest["artifacts"]
    )


def test_wikidata_bundle_removes_partial_destination_after_validation_failure(
    tmp_path, registry, monkeypatch
) -> None:
    entities, edges = build_smoke_graph()
    destination = tmp_path / "bundle"

    def reject_selection(*args: object, **kwargs: object) -> dict[str, Any]:
        raise RoundValidationError("rejected for test")

    monkeypatch.setattr(
        "webwoven_pipeline.wikidata_bundle.validate_round_selection", reject_selection
    )
    with pytest.raises(RoundValidationError, match="rejected for test"):
        build_wikidata_bundle(
            destination,
            registry,
            entities,
            edges,
            ({"path": "batch.json", "qids": [], "sha256": "0" * 64},),
            endpoint_ids=(item.id for item in entities),
            created_at="2026-07-15T00:00:00Z",
        )

    assert not destination.exists()


def test_wikidata_bundle_copies_and_manifests_attributed_commons_media(tmp_path, registry) -> None:
    entities, edges = build_smoke_graph()
    body = b"\xff\xd8\xfffixture-media"
    digest = hashlib.sha256(body).hexdigest()
    media_root = tmp_path / "commons"
    asset_source = media_root / "assets" / f"{digest}.jpg"
    asset_source.parent.mkdir(parents=True)
    asset_source.write_bytes(body)
    manifest_path = media_root / "media-manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    record = MediaRecord(
        file_name="Fixture.jpg",
        original_url="https://upload.wikimedia.org/original.jpg",
        derivative_url="https://upload.wikimedia.org/derivative.jpg",
        source_url="https://commons.wikimedia.org/wiki/File:Fixture.jpg",
        license_id="PUBLIC_DOMAIN",
        creator="Fixture creator",
        license_url="https://creativecommons.org/publicdomain/mark/1.0/",
        attribution_text="Fixture creator — Public Domain — Wikimedia Commons",
    )
    commons = CommonsMediaBundle(
        manifest_path=manifest_path,
        created_at="2026-07-15T00:00:00Z",
        assets=(
            CommonsAsset(
                record=record,
                asset_path=f"assets/{digest}.jpg",
                public_path=f"/api/v1/media/{digest}.jpg",
                content_type="image/jpeg",
                byte_count=len(body),
                remote_sha256=digest,
                local_sha256=digest,
                retrieved_at="2026-07-15T00:00:00Z",
                review_status="automatic_allowlist_passed",
            ),
        ),
        entity_files=((entities[0].id, record.file_name),),
    )
    enriched = enrich_entities_with_commons(entities, commons)
    destination = tmp_path / "bundle"

    build_wikidata_bundle(
        destination,
        registry,
        enriched,
        edges,
        ({"path": "batch.json", "qids": [], "sha256": "0" * 64},),
        endpoint_ids=(item.id for item in enriched),
        created_at="2026-07-15T00:00:00Z",
        commons_media=commons,
        commons_media_candidates={entities[0].id: record.file_name},
    )

    manifest = json.loads((destination / "manifest.json").read_text())
    attribution = json.loads((destination / "attribution.json").read_text())
    assert (destination / "media" / f"{digest}.jpg").read_bytes() == body
    assert any(item["role"] == "commons_media" for item in manifest["artifacts"])
    assert attribution["media_records"][0]["entity_ids"] == [entities[0].id]

    context_source = {entities[0].id: "graph_context:P170:Q42:Fixture creator"}
    contextual = enrich_entities_with_commons(entities, commons, context_source)
    contextual_destination = tmp_path / "contextual-bundle"
    build_wikidata_bundle(
        contextual_destination,
        registry,
        contextual,
        edges,
        ({"path": "batch.json", "qids": [], "sha256": "0" * 64},),
        endpoint_ids=(item.id for item in contextual),
        created_at="2026-07-15T00:00:00Z",
        commons_media=commons,
        commons_media_candidates={entities[0].id: record.file_name},
        commons_media_sources=context_source,
    )
    contextual_entities = json.loads(
        (contextual_destination / "entities.json").read_text(encoding="utf-8")
    )
    assert contextual_entities[0]["image_attribution"]["context_label"] == "Fixture creator"

    tampered = (
        replace(enriched[0], image_path=f"/api/v1/media/{'f' * 64}.jpg"),
        *enriched[1:],
    )
    with pytest.raises(ValueError, match="does not match the manifest"):
        build_wikidata_bundle(
            tmp_path / "tampered-bundle",
            registry,
            tampered,
            edges,
            ({"path": "batch.json", "qids": [], "sha256": "0" * 64},),
            endpoint_ids=(item.id for item in tampered),
            created_at="2026-07-15T00:00:00Z",
            commons_media=commons,
            commons_media_candidates={entities[0].id: record.file_name},
        )

    remapped = replace(
        commons,
        entity_files=((entities[1].id, record.file_name),),
    )
    remapped_entities = enrich_entities_with_commons(entities, remapped)
    with pytest.raises(ValueError, match="does not match the graph source"):
        build_wikidata_bundle(
            tmp_path / "remapped-bundle",
            registry,
            remapped_entities,
            edges,
            ({"path": "batch.json", "qids": [], "sha256": "0" * 64},),
            endpoint_ids=(item.id for item in remapped_entities),
            created_at="2026-07-15T00:00:00Z",
            commons_media=remapped,
            commons_media_candidates={entities[0].id: record.file_name},
        )


def _validate(
    registry: RelationRegistry,
    rounds: tuple[Round, ...],
    entities: tuple[Entity, ...],
    edges: tuple[Edge, ...],
) -> dict[str, Any]:
    return validate_round_selection(
        rounds,
        entities,
        edges,
        endpoint_ids=(item.id for item in entities),
        playable_relation_keys=registry.playable_keys,
        source_kind="synthetic_fixture",
        selection_seed=DEFAULT_SELECTION_SEED,
        registry_version=registry.version,
    )
