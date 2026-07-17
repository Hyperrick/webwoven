from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
VERIFY_GRAPH = REPOSITORY_ROOT / "infra" / "scripts" / "verify-graph.sh"


def _write_bundle(bundle_dir: Path, schema_version: int) -> None:
    bundle_dir.mkdir()
    graph_path = bundle_dir / "graph.sqlite3"
    with sqlite3.connect(graph_path) as connection:
        connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.executemany(
            "INSERT INTO metadata (key, value) VALUES (?, ?)",
            (
                ("graph_build_id", "deployment-test"),
                ("schema_version", str(schema_version)),
            ),
        )

    graph_bytes = graph_path.read_bytes()
    manifest = {
        "bundle_kind": "wikidata",
        "graph_build_id": "deployment-test",
        "graph_schema_version": schema_version,
        "source_batches": [{"id": "test"}],
        "artifacts": [
            {
                "path": "graph.sqlite3",
                "role": "compiled_graph",
                "bytes": len(graph_bytes),
                "sha256": hashlib.sha256(graph_bytes).hexdigest(),
            }
        ],
    }
    (bundle_dir / "manifest.json").write_text(json.dumps(manifest))


def test_verify_graph_accepts_current_schema(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "schema-v3"
    _write_bundle(bundle_dir, schema_version=3)

    result = subprocess.run(
        ["sh", str(VERIFY_GRAPH), str(bundle_dir)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "verified graph deployment-test" in result.stdout


@pytest.mark.parametrize("schema_version", [1, 2, 4])
def test_verify_graph_rejects_other_schemas(tmp_path: Path, schema_version: int) -> None:
    bundle_dir = tmp_path / f"schema-v{schema_version}"
    _write_bundle(bundle_dir, schema_version=schema_version)

    result = subprocess.run(
        ["sh", str(VERIFY_GRAPH), str(bundle_dir)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "deployment requires graph schema v3" in result.stderr
