from __future__ import annotations

from pathlib import Path

import pytest
from webwoven_pipeline.registry import RelationRegistry, load_registry

PROJECT_ROOT = Path(__file__).parents[3]
REGISTRY_PATH = PROJECT_ROOT / "data/relation-registry/relations.v1.json"
SEEDS_PATH = PROJECT_ROOT / "data/seeds/anchors.v1.json"


@pytest.fixture
def registry() -> RelationRegistry:
    return load_registry(REGISTRY_PATH)
