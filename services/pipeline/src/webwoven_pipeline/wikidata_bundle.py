from __future__ import annotations

import json
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from .compiler import compile_graph
from .manifest import build_manifest, write_manifest
from .models import Edge, Entity, Round
from .registry import RelationRegistry
from .rounds import generate_rounds


def build_wikidata_bundle(
    destination: Path,
    registry: RelationRegistry,
    entities: Iterable[Entity],
    edges: Iterable[Edge],
    source_batches: Iterable[Mapping[str, Any]],
    *,
    endpoint_ids: Iterable[str],
    created_at: str,
    selection_seed: str = "webwoven-build-week-v1",
) -> str:
    """Assemble an immutable, real-data local playtest bundle."""
    if destination.exists():
        raise FileExistsError(f"refusing to replace Wikidata bundle: {destination}")

    entity_values = tuple(entities)
    edge_values = tuple(edges)
    batch_values = tuple(dict(batch) for batch in source_batches)
    if not batch_values:
        raise ValueError("Wikidata bundles require immutable source batch records")

    destination.mkdir(parents=True)
    try:
        rounds = generate_rounds(
            entity_values,
            edge_values,
            selection_seed=selection_seed,
            endpoint_ids=endpoint_ids,
        )
        entities_path = destination / "entities.json"
        edges_path = destination / "edges.json"
        rounds_path = destination / "candidate-rounds.json"
        review_path = destination / "round-review-status.json"
        attribution_path = destination / "attribution.json"
        graph_path = destination / "graph.sqlite3"

        _write_json(entities_path, [item.to_dict() for item in entity_values])
        _write_json(edges_path, [item.to_dict() for item in edge_values])
        _write_json(rounds_path, [item.to_dict() for item in rounds])
        _write_json(review_path, _playtest_review_status(rounds))
        _write_json(attribution_path, _attribution(created_at))

        graph_build_id = compile_graph(
            graph_path,
            registry,
            entity_values,
            edge_values,
            rounds,
        )
        manifest = build_manifest(
            graph_path,
            (
                (graph_path, "compiled_graph"),
                (entities_path, "normalized_wikidata_entities"),
                (edges_path, "normalized_wikidata_edges"),
                (rounds_path, "candidate_rounds"),
                (review_path, "round_review_status"),
                (attribution_path, "knowledge_attribution"),
            ),
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


def _playtest_review_status(rounds: tuple[Round, ...]) -> dict[str, Any]:
    return {
        "version": 1,
        "scope": "local_playtest",
        "human_approval_complete": False,
        "notice": (
            "Forty deterministic routes are enabled for local playtesting. "
            "They remain pending human editorial approval and are not production rounds."
        ),
        "decisions": [
            {
                "round_id": item.id,
                "decision": "pending",
                "local_playtest_enabled": item.published,
            }
            for item in rounds
        ],
    }


def _attribution(created_at: str) -> dict[str, Any]:
    return {
        "version": 1,
        "knowledge_source": "Wikidata",
        "knowledge_source_url": "https://www.wikidata.org/",
        "knowledge_license": "CC0 1.0",
        "snapshot_created_at": created_at,
        "media_records": [],
        "notice": (
            "This local playtest pack contains real Wikidata knowledge but no Wikimedia "
            "Commons documentary media. Project-authored category illustrations are used as "
            "non-documentary fallbacks."
        ),
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
