"""Runtime graph loading enforces bundle identity and immutable hashes."""

import shutil
from pathlib import Path

import pytest
from webwoven_api.graph.bundle import GraphBundleError, load_graph_bundle


def test_testing_loader_accepts_explicit_fixture_bundle(tmp_path: Path) -> None:
    graph, manifest = _copy_fixture(tmp_path)

    loaded = load_graph_bundle(graph, manifest, required_kind="test_fixture")

    assert loaded.is_healthy()


def test_normal_runtime_rejects_fixture_bundle(tmp_path: Path) -> None:
    graph, manifest = _copy_fixture(tmp_path)

    with pytest.raises(GraphBundleError, match="requires a wikidata"):
        load_graph_bundle(graph, manifest, required_kind="wikidata")


def test_loader_rejects_graph_changed_after_manifest(tmp_path: Path) -> None:
    graph, manifest = _copy_fixture(tmp_path)
    with graph.open("ab") as handle:
        handle.write(b"changed")

    with pytest.raises(GraphBundleError, match="size does not match"):
        load_graph_bundle(graph, manifest, required_kind="test_fixture")


def _copy_fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = Path(__file__).parents[4]
    fixture = root / "data/fixtures/smoke"
    graph = tmp_path / "graph.sqlite3"
    manifest = tmp_path / "manifest.json"
    shutil.copyfile(fixture / graph.name, graph)
    shutil.copyfile(fixture / manifest.name, manifest)
    return graph, manifest
