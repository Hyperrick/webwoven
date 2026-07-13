from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[2]
ILLUSTRATIONS = ROOT / "apps" / "web" / "public" / "illustrations"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc_timestamp(value: object) -> datetime:
    assert isinstance(value, str)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == UTC.utcoffset(parsed)
    return parsed


def test_generated_illustration_manifest_is_complete_and_truthful() -> None:
    manifest_value: Any = json.loads((ILLUSTRATIONS / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(manifest_value, dict)
    manifest = manifest_value
    assert manifest["generator"] == "codex"
    assert manifest["generation_tool"] == "imagegen"
    assert manifest["model_metadata"] == "unavailable"
    human_approval = manifest["human_approval"]
    assert human_approval["approved_by"] == "project_owner"
    approved_at = _utc_timestamp(human_approval["approved_at"])
    prompt_path = ROOT / manifest["prompt_document"]
    assert _digest(prompt_path) == manifest["prompt_document_sha256"]

    assets = manifest["assets"]
    assert {asset["id"] for asset in assets} == {
        "cartographer",
        "history_people",
        "nature_science",
        "arts_culture",
        "places",
    }
    cartographer = next(asset for asset in assets if asset["id"] == "cartographer")
    assert cartographer["prompt_section"] == "Cartographer replacement"
    assert cartographer["supersedes"] == {
        "source_artifact_id": "exec-705cb2f7-e641-4f4f-9230-7c36b8526d5f",
        "rejection_reason": (
            "The first composition made the outward-facing map surface spatially ambiguous."
        ),
    }
    for asset in assets:
        derivative = ILLUSTRATIONS / asset["derivative_path"]
        assert derivative.suffix == ".webp"
        assert _digest(derivative) == asset["derivative_sha256"]
        assert asset["approval_status"] == "approved"
        assert asset["approved_by"] == "project_owner"
        assert _utc_timestamp(asset["approved_at"]) == approved_at
        assert asset["validation_results"] == [
            "derivative_hash:passed",
            "format:webp:passed",
            "editorial_review:passed",
        ]
        assert asset["documentary_use_allowed"] is False
