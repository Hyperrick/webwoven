from __future__ import annotations

import json
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .commons_assets import (
    CommonsAssetError,
    CommonsMediaBundle,
    commons_attribution_records,
    copy_commons_assets,
)
from .compiler import compile_graph
from .manifest import build_manifest, write_manifest
from .models import Edge, Entity
from .registry import RelationRegistry
from .round_validation import validate_round_selection
from .rounds import DEFAULT_SELECTION_SEED, generate_rounds


def build_wikidata_bundle(
    destination: Path,
    registry: RelationRegistry,
    entities: Iterable[Entity],
    edges: Iterable[Edge],
    source_batches: Iterable[Mapping[str, Any]],
    *,
    endpoint_ids: Iterable[str],
    created_at: str,
    selection_seed: str = DEFAULT_SELECTION_SEED,
    commons_media: CommonsMediaBundle | None = None,
    commons_media_candidates: Mapping[str, str] | None = None,
) -> str:
    """Assemble an immutable, validated real-data bundle."""
    if destination.exists():
        raise FileExistsError(f"refusing to replace Wikidata bundle: {destination}")

    entity_values = tuple(entities)
    edge_values = tuple(edges)
    batch_values = tuple(dict(batch) for batch in source_batches)
    endpoint_values = tuple(endpoint_ids)
    if not batch_values:
        raise ValueError("Wikidata bundles require immutable source batch records")
    _validate_commons_bindings(
        entity_values,
        endpoint_values,
        commons_media,
        commons_media_candidates,
    )

    destination.mkdir(parents=True)
    try:
        rounds = generate_rounds(
            entity_values,
            edge_values,
            selection_seed=selection_seed,
            endpoint_ids=endpoint_values,
        )
        validation_report = validate_round_selection(
            rounds,
            entity_values,
            edge_values,
            endpoint_ids=endpoint_values,
            playable_relation_keys=registry.playable_keys,
            source_kind="wikidata",
            selection_seed=selection_seed,
            registry_version=registry.version,
        )
        entities_path = destination / "entities.json"
        edges_path = destination / "edges.json"
        rounds_path = destination / "candidate-rounds.json"
        validation_path = destination / "round-validation-report.json"
        attribution_path = destination / "attribution.json"
        graph_path = destination / "graph.sqlite3"

        media_paths = (
            copy_commons_assets(commons_media, destination) if commons_media is not None else ()
        )

        _write_json(entities_path, [item.to_dict() for item in entity_values])
        _write_json(edges_path, [item.to_dict() for item in edge_values])
        _write_json(rounds_path, [item.to_dict() for item in rounds])
        _write_json(validation_path, validation_report)
        _write_json(attribution_path, _attribution(created_at, commons_media))

        graph_build_id = compile_graph(
            graph_path,
            registry,
            entity_values,
            edge_values,
            rounds,
        )
        artifacts = [
            (graph_path, "compiled_graph"),
            (entities_path, "normalized_wikidata_entities"),
            (edges_path, "normalized_wikidata_edges"),
            (rounds_path, "candidate_rounds"),
            (validation_path, "round_validation_report"),
            (attribution_path, "knowledge_attribution"),
            *((path, "commons_media") for path in media_paths),
        ]
        manifest = build_manifest(
            graph_path,
            artifacts,
            graph_build_id=graph_build_id,
            created_at=created_at,
            bundle_kind="wikidata",
            source_batches=batch_values,
        )
        write_manifest(destination / "manifest.json", manifest)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return graph_build_id


def _attribution(
    created_at: str,
    commons_media: CommonsMediaBundle | None,
) -> dict[str, Any]:
    media_records = commons_attribution_records(commons_media) if commons_media is not None else []
    return {
        "version": 2,
        "knowledge_source": "Wikidata",
        "knowledge_source_url": "https://www.wikidata.org/",
        "knowledge_license": "CC0 1.0",
        "snapshot_created_at": created_at,
        "media_records": media_records,
        "notice": (
            "Documentary media is stored locally after an automatic Public Domain, CC0, or "
            "complete CC BY 4.0 provenance gate. Project-authored category illustrations remain "
            "the non-documentary fallback when an endpoint has no accepted asset."
            if media_records
            else "This pack contains no accepted Commons media; project-authored category "
            "illustrations are used as non-documentary fallbacks."
        ),
    }


def _validate_commons_bindings(
    entities: tuple[Entity, ...],
    endpoint_ids: tuple[str, ...],
    commons_media: CommonsMediaBundle | None,
    candidates: Mapping[str, str] | None,
) -> None:
    attributed = tuple(
        entity
        for entity in entities
        if entity.image_path is not None or entity.image_attribution is not None
    )
    if commons_media is None:
        if attributed:
            raise CommonsAssetError("entity media requires a Commons bundle")
        return
    if candidates is None:
        raise CommonsAssetError("Commons media requires graph-source candidate bindings")

    assets = commons_media.assets_by_file
    entity_files = commons_media.file_by_entity
    entity_ids = {entity.id for entity in entities}
    endpoint_set = set(endpoint_ids)
    if set(entity_files) - entity_ids:
        raise CommonsAssetError("Commons media maps an entity outside the graph")
    if set(entity_files) - endpoint_set:
        raise CommonsAssetError("Commons media maps an entity outside the curated endpoints")
    if any(candidates.get(entity_id) != file_name for entity_id, file_name in entity_files.items()):
        raise CommonsAssetError("Commons media mapping does not match the graph source")
    if set(assets) - set(entity_files.values()):
        raise CommonsAssetError("Commons media bundle contains an unreferenced asset")

    for entity in entities:
        file_name = entity_files.get(entity.id)
        asset = assets.get(file_name) if file_name is not None else None
        if asset is None:
            if entity.image_path is not None or entity.image_attribution is not None:
                raise CommonsAssetError(f"entity {entity.id} media is absent from the manifest")
            continue
        if (
            entity.image_path != asset.public_path
            or entity.image_attribution != asset.record.to_dict()
        ):
            raise CommonsAssetError(f"entity {entity.id} media does not match the manifest")


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
