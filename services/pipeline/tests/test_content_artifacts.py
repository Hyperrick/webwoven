from __future__ import annotations

import ast
import json
import tomllib
from pathlib import Path

import pytest
from webwoven_pipeline.codex_artifacts import CodexArtifactError, ingest_codex_artifact
from webwoven_pipeline.content_contract import fact_pack_sha256, output_sha256, prompt_sha256
from webwoven_pipeline.models import ContentRequest, Fact
from webwoven_pipeline.template_content import DeterministicFallback


@pytest.fixture
def content_request() -> ContentRequest:
    return ContentRequest(
        round_id="round-1",
        start_label="Ada Lovelace",
        target_label="Paris",
        target_aliases=("City of Paris",),
        facts=(
            Fact("fact-1", "Ada Lovelace", "educated at", "Bridge College"),
            Fact("fact-2", "Bridge College", "located in", "France"),
        ),
    )


def test_deterministic_fallback_is_grounded_and_has_provenance(content_request) -> None:
    generated = DeterministicFallback().generate(content_request)

    assert generated.provenance["generator"] == "deterministic_fallback"
    assert generated.provenance["validation_results"] == [
        "schema:passed",
        "grounding:passed",
        "answer_leak:passed",
        "language:passed",
    ]
    assert {hint["kind"] for hint in generated.hints} == {
        "compass",
        "lens",
        "map_fragment",
    }


def test_only_hash_bound_approved_codex_artifact_is_ingested(tmp_path, content_request) -> None:
    content = DeterministicFallback().generate(content_request).content_dict()
    artifact = _artifact(content_request, content)
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    generated = ingest_codex_artifact(path, content_request)

    assert generated.provenance["generator"] == "codex"
    assert generated.provenance["approval_status"] == "approved"
    assert generated.provenance["prompt_text"] == artifact["prompt_text"]
    assert generated.provenance["validation_results"][-1] == "approval:passed"


def test_artifact_rejects_prompt_text_that_does_not_match_its_hash(
    tmp_path, content_request
) -> None:
    content = DeterministicFallback().generate(content_request).content_dict()
    artifact = _artifact(content_request, content)
    artifact["prompt_text"] = "A changed prompt."
    path = tmp_path / "prompt-mismatch.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(CodexArtifactError, match="prompt hash"):
        ingest_codex_artifact(path, content_request)


def test_artifact_rejects_answer_leak_and_unapproved_copy(tmp_path, content_request) -> None:
    content = DeterministicFallback().generate(content_request).content_dict()
    content["hints"][0]["text"] = "The answer is Paris."
    artifact = _artifact(content_request, content)
    path = tmp_path / "leak.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(ValueError, match="leaks the target"):
        ingest_codex_artifact(path, content_request)

    artifact["approval"]["status"] = "needs_review"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(CodexArtifactError, match="approved"):
        ingest_codex_artifact(path, content_request)


def test_artifact_schema_rejects_overlength_recap(tmp_path, content_request) -> None:
    content = DeterministicFallback().generate(content_request).content_dict()
    content["recap"] = "x" * 421
    artifact = _artifact(content_request, content)
    path = tmp_path / "overlength-recap.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(CodexArtifactError, match=r"schema validation failed at content\.recap"):
        ingest_codex_artifact(path, content_request)


def test_artifact_schema_checks_date_time_formats(tmp_path, content_request) -> None:
    content = DeterministicFallback().generate(content_request).content_dict()
    artifact = _artifact(content_request, content)
    artifact["generated_at"] = "yesterday"
    path = tmp_path / "invalid-generation-date.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(CodexArtifactError, match=r"schema validation failed at generated_at"):
        ingest_codex_artifact(path, content_request)


def test_artifact_rejects_unsupported_prose_with_valid_fact_id(tmp_path, content_request) -> None:
    content = DeterministicFallback().generate(content_request).content_dict()
    content["hints"][0]["text"] = "This route uses a verified connection to a secret moon colony."
    artifact = _artifact(content_request, content)
    path = tmp_path / "unsupported-prose.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(ValueError, match="not fact-grounded"):
        ingest_codex_artifact(path, content_request)


def test_artifact_rejects_non_english_copy_with_english_marker(tmp_path, content_request) -> None:
    content = DeterministicFallback().generate(content_request).content_dict()
    content["hints"][0]["text"] = "The Weg führt durch eine Stadt und endet dort."
    artifact = _artifact(content_request, content)
    path = tmp_path / "non-english-copy.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    with pytest.raises(ValueError, match="English text"):
        ingest_codex_artifact(path, content_request)


def test_content_creation_boundary_is_offline_and_sdk_free() -> None:
    service_root = Path(__file__).parents[1]
    project = tomllib.loads((service_root / "pyproject.toml").read_text(encoding="utf-8"))
    assert set(project["project"]["dependencies"]) == {
        "httpx>=0.28.1,<0.29",
        "jsonschema[format-nongpl]>=4.25,<5",
    }

    source_root = service_root / "src/webwoven_pipeline"
    creation_modules = (
        "codex_artifacts.py",
        "content_contract.py",
        "content_validation.py",
        "copy_vocabulary.py",
        "fact_grounding.py",
        "language_validation.py",
        "schema_validation.py",
        "template_content.py",
        "text_tokens.py",
    )
    integration_roots = {"http", "os", "socket", "subprocess", "urllib"}
    imported_roots: set[str] = set()
    for module in creation_modules:
        tree = ast.parse((source_root / module).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.partition(".")[0])
    assert imported_roots.isdisjoint(integration_roots)


def _artifact(request: ContentRequest, content: dict) -> dict:
    prompt_text = "Use only the supplied verified facts and do not reveal the target in hints."
    return {
        "artifact_version": 1,
        "round_id": request.round_id,
        "generator": "codex",
        "generated_at": "2026-07-13T10:00:00Z",
        "prompt_id": "round-learning-copy-v1",
        "prompt_text": prompt_text,
        "prompt_sha256": prompt_sha256(prompt_text),
        "fact_pack_sha256": fact_pack_sha256(request),
        "output_sha256": output_sha256(content),
        "approval": {
            "status": "approved",
            "reviewer": "fixture-reviewer",
            "approved_at": "2026-07-13T11:00:00Z",
        },
        "content": content,
    }
