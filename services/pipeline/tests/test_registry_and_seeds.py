from __future__ import annotations

import hashlib
import json

from webwoven_pipeline.registry import load_registry
from webwoven_pipeline.seeds import load_seeds
from webwoven_pipeline.taxonomy import CATEGORIES

from .conftest import REGISTRY_PATH, SEEDS_PATH


def test_locked_relation_registry_is_structurally_complete() -> None:
    registry = load_registry(REGISTRY_PATH)

    assert len(registry.relations) == 20
    assert registry.classification_properties == ("P31", "P279")
    assert registry.media_property == "P18"
    assert all(item.inverse_label for item in registry.relations)
    assert all(item.max_targets == 8 for item in registry.relations)


def test_starter_seeds_cover_every_category_with_real_qids() -> None:
    catalog = load_seeds(SEEDS_PATH)
    grouped = {category: [] for category in CATEGORIES}
    for seed in catalog.seeds:
        grouped[seed.category].append(seed)

    assert len(catalog.seeds) == 160
    assert all(len(grouped[category]) == 40 for category in CATEGORIES)
    assert all(seed.qid.startswith("Q") and seed.qid[1:].isdigit() for seed in catalog.seeds)


def test_seed_provenance_manifest_matches_reviewed_catalog() -> None:
    manifest_path = SEEDS_PATH.parents[1] / "manifests/seed-catalog.v1.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["qid_count"] == 160
    assert manifest["sha256"] == hashlib.sha256(SEEDS_PATH.read_bytes()).hexdigest()
