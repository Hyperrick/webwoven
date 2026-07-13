from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from .compiler import compile_graph
from .manifest import build_manifest, write_manifest
from .models import Edge, Entity, Round
from .registry import RelationRegistry
from .rounds import generate_rounds
from .taxonomy import CATEGORIES, CATEGORY_LABELS

FIXTURE_CREATED_AT = "2026-07-13T00:00:00Z"


def generate_smoke_fixture(
    destination: Path,
    registry: RelationRegistry,
    *,
    replace: bool = False,
) -> str:
    """Generate a complete, synthetic graph bundle for local and CI smoke tests."""
    if destination.exists():
        if not replace:
            raise FileExistsError(f"smoke fixture already exists: {destination}")
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    entities, edges = build_smoke_graph()
    rounds = generate_rounds(entities, edges)
    entities_path = destination / "entities.json"
    edges_path = destination / "edges.json"
    rounds_path = destination / "candidate-rounds.json"
    reviews_path = destination / "fixture-review-decisions.json"
    attribution_path = destination / "attribution.json"
    graph_path = destination / "graph.sqlite3"
    _write_json(entities_path, [item.to_dict() for item in entities])
    _write_json(edges_path, [item.to_dict() for item in edges])
    _write_json(rounds_path, [item.to_dict() for item in rounds])
    _write_json(reviews_path, _fixture_reviews(rounds))
    _write_json(
        attribution_path,
        {
            "version": 1,
            "fixture_only": True,
            "notice": "The synthetic smoke graph contains no external media.",
            "records": [],
        },
    )

    graph_build_id = compile_graph(graph_path, registry, entities, edges, rounds)
    manifest = build_manifest(
        graph_path,
        (
            (graph_path, "compiled_graph"),
            (entities_path, "normalized_fixture_entities"),
            (edges_path, "normalized_fixture_edges"),
            (rounds_path, "candidate_rounds"),
            (reviews_path, "fixture_review_decisions"),
            (attribution_path, "media_attribution"),
        ),
        graph_build_id=graph_build_id,
        created_at=FIXTURE_CREATED_AT,
    )
    write_manifest(destination / "manifest.json", manifest)
    return graph_build_id


def build_smoke_graph() -> tuple[tuple[Entity, ...], tuple[Edge, ...]]:
    """Build four isolated bidirectional rings with known shortest paths."""
    entities: list[Entity] = []
    edges: list[Edge] = []
    for category in CATEGORIES:
        category_entities = tuple(_fixture_entity(category, index) for index in range(1, 13))
        entities.extend(category_entities)
        for index, source in enumerate(category_entities):
            target = category_entities[(index + 1) % len(category_entities)]
            edges.append(_fixture_edge(source.id, target.id))
            edges.append(_fixture_edge(target.id, source.id))
    return tuple(entities), tuple(sorted(edges, key=lambda item: item.id))


def _fixture_entity(category: str, index: int) -> Entity:
    category_label = CATEGORY_LABELS[category]
    return Entity(
        id=f"fixture:{category}:{index:02d}",
        label=f"{category_label} waypoint {index:02d}",
        description="Synthetic smoke-test waypoint; not production knowledge data.",
        entity_type="fixture_item",
        category=category,
    )


def _fixture_edge(source_id: str, target_id: str) -> Edge:
    digest = hashlib.sha256(f"{source_id}\0P361\0{target_id}".encode()).hexdigest()[:24]
    return Edge(
        id=digest,
        source_id=source_id,
        target_id=target_id,
        relation_key="P361",
        statement_id=f"fixture-statement-{digest}",
        explanation="part of",
    )


def _fixture_reviews(rounds: tuple[Round, ...]) -> dict[str, Any]:
    return {
        "version": 1,
        "fixture_only": True,
        "notice": (
            "Approvals apply only to synthetic fixture behavior, not production knowledge data."
        ),
        "decisions": [
            {
                "round_id": item.id,
                "decision": "approved" if item.published else "held",
                "approval_scope": "synthetic_fixture",
            }
            for item in rounds
        ],
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
