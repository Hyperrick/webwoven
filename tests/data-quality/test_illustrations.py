from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[2]
ILLUSTRATIONS = ROOT / "data" / "drafts" / "illustrations"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_generated_illustration_manifest_is_complete_and_truthful() -> None:
    manifest_value: Any = json.loads((ILLUSTRATIONS / "manifest.json").read_text(encoding="utf-8"))
    assert isinstance(manifest_value, dict)
    manifest = manifest_value
    assert manifest["generator"] == "codex"
    assert manifest["model_metadata"] == "unavailable"
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
    for asset in assets:
        derivative = ILLUSTRATIONS / asset["derivative_path"]
        assert derivative.suffix == ".webp"
        assert _digest(derivative) == asset["derivative_sha256"]
        assert asset["approval_status"] == "draft_pending_human_review"
        assert asset["validation_results"] == [
            "derivative_hash:passed",
            "format:webp:passed",
            "editorial_review:pending",
        ]
        assert asset["documentary_use_allowed"] is False
