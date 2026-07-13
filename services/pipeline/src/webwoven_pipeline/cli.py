from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from .acquisition import acquire_graph
from .codex_artifacts import ingest_codex_artifact
from .commons import CommonsClient
from .compiler import compile_graph
from .fixture import generate_smoke_fixture
from .manifest import verify_manifest
from .models import ContentRequest, Edge, Entity, Fact, Round
from .normalization import normalize_edges, normalize_entities
from .registry import load_registry
from .rounds import generate_rounds
from .seeds import load_seeds
from .wikidata import WikidataClient

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_REGISTRY = PROJECT_ROOT / "data/relation-registry/relations.v1.json"
DEFAULT_SMOKE_OUTPUT = PROJECT_ROOT / "data/fixtures/smoke"


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    command = args.command
    if command == "validate-inputs":
        registry = load_registry(args.registry)
        seeds = load_seeds(args.seeds)
        print(f"valid: {len(registry.relations)} relations, {len(seeds.seeds)} anchors")
    elif command == "acquire":
        _acquire(args)
    elif command == "commons-metadata":
        _commons_metadata(args)
    elif command == "generate-rounds":
        _generate_rounds(args)
    elif command == "compile":
        _compile(args)
    elif command in {"generate-smoke", "build-smoke"}:
        if command == "build-smoke":
            args.registry = DEFAULT_REGISTRY
            args.output = DEFAULT_SMOKE_OUTPUT
            args.replace = True
        registry = load_registry(args.registry)
        build_id = generate_smoke_fixture(args.output, registry, replace=args.replace)
        print(build_id)
    elif command == "verify-manifest":
        verify_manifest(args.manifest)
        print("valid")
    elif command == "validate-codex-artifact":
        request = _content_request(_read_json(args.fact_pack))
        artifact = ingest_codex_artifact(args.artifact, request)
        print(json.dumps(artifact.provenance, sort_keys=True))
    else:
        parser.error(f"unknown command: {command}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="webwoven-pipeline")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-inputs", help="validate relation and anchor inputs")
    _registry_argument(validate)
    validate.add_argument("--seeds", type=Path, required=True)

    acquire = commands.add_parser("acquire", help="fetch and normalize a cached Wikidata snapshot")
    _registry_argument(acquire)
    acquire.add_argument("--seeds", type=Path, required=True)
    acquire.add_argument("--cache", type=Path, required=True)
    acquire.add_argument("--output", type=Path, required=True)
    acquire.add_argument("--user-agent", required=True)
    acquire.add_argument("--hops", type=int, default=2)
    acquire.add_argument("--max-entities", type=int, default=10_000)

    commons = commands.add_parser("commons-metadata", help="fetch and filter Commons metadata")
    commons.add_argument("--files", type=Path, required=True)
    commons.add_argument("--output", type=Path, required=True)
    commons.add_argument("--user-agent", required=True)

    round_command = commands.add_parser(
        "generate-rounds",
        help="generate locked round distribution",
    )
    round_command.add_argument("--graph-source", type=Path, required=True)
    round_command.add_argument("--output", type=Path, required=True)
    round_command.add_argument("--selection-seed", default="webwoven-build-week-v1")

    compile_command = commands.add_parser("compile", help="compile normalized JSON to SQLite")
    _registry_argument(compile_command)
    compile_command.add_argument("--graph-source", type=Path, required=True)
    compile_command.add_argument("--rounds", type=Path, required=True)
    compile_command.add_argument("--output", type=Path, required=True)

    smoke = commands.add_parser("generate-smoke", help="create the complete synthetic smoke bundle")
    _registry_argument(smoke)
    smoke.add_argument("--output", type=Path, required=True)
    smoke.add_argument("--replace", action="store_true")

    commands.add_parser(
        "build-smoke",
        help="rebuild the canonical committed smoke bundle with project defaults",
    )

    verify = commands.add_parser("verify-manifest", help="verify artifact hashes and sizes")
    verify.add_argument("manifest", type=Path)

    codex = commands.add_parser(
        "validate-codex-artifact",
        help="validate an approved static Codex content artifact against its fact pack",
    )
    codex.add_argument("--fact-pack", type=Path, required=True)
    codex.add_argument("--artifact", type=Path, required=True)
    return parser


def _registry_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--registry", type=Path, required=True)


def _acquire(args: argparse.Namespace) -> None:
    registry = load_registry(args.registry)
    seeds = load_seeds(args.seeds)
    client = WikidataClient(args.cache, args.user_agent)
    acquired = acquire_graph(
        seeds,
        registry,
        client,
        hops=args.hops,
        max_entities=args.max_entities,
    )
    entities = normalize_entities(acquired.entities, acquired.category_by_qid)
    edges = normalize_edges(acquired.entities, registry)
    batches = [
        {
            "path": batch.cache_path.name,
            "qids": list(batch.qids),
            "sha256": batch.sha256,
        }
        for batch in acquired.batches
    ]
    _write_new_json(
        args.output,
        {
            "schema_version": 2,
            "source": "wikidata",
            "entities": [item.to_dict() for item in entities],
            "edges": [item.to_dict() for item in edges],
            "source_batches": batches,
        },
    )


def _commons_metadata(args: argparse.Namespace) -> None:
    file_names_value = _read_json(args.files)
    if not isinstance(file_names_value, list):
        raise ValueError("--files must contain a JSON string array")
    file_names_items = cast(list[Any], file_names_value)
    if any(not isinstance(item, str) for item in file_names_items):
        raise ValueError("--files must contain a JSON string array")
    file_names = cast(list[str], file_names_items)
    records = CommonsClient(args.user_agent).fetch_metadata(file_names)
    _write_new_json(args.output, {name: record.to_dict() for name, record in records.items()})


def _generate_rounds(args: argparse.Namespace) -> None:
    source = _read_object(args.graph_source)
    entities = _entities(source.get("entities"))
    edges = _edges(source.get("edges"))
    rounds = generate_rounds(entities, edges, selection_seed=args.selection_seed)
    _write_new_json(args.output, [item.to_dict() for item in rounds])


def _compile(args: argparse.Namespace) -> None:
    source = _read_object(args.graph_source)
    registry = load_registry(args.registry)
    rounds_value = _read_json(args.rounds)
    build_id = compile_graph(
        args.output,
        registry,
        _entities(source.get("entities")),
        _edges(source.get("edges")),
        _rounds(rounds_value),
    )
    print(build_id)


def _entities(value: Any) -> tuple[Entity, ...]:
    return tuple(
        Entity(
            id=_string(item, "id"),
            label=_string(item, "label"),
            description=_string(item, "description"),
            entity_type=_string(item, "entity_type"),
            category=_string(item, "category"),
            image_path=_optional_string(item, "image_path"),
            image_attribution=_optional_object(item, "image_attribution"),
        )
        for item in _object_list(value, "entities")
    )


def _edges(value: Any) -> tuple[Edge, ...]:
    return tuple(
        Edge(
            id=_string(item, "id"),
            source_id=_string(item, "source_id"),
            target_id=_string(item, "target_id"),
            relation_key=_string(item, "relation_key"),
            statement_id=_string(item, "statement_id"),
            explanation=_string(item, "explanation"),
            inverse=_boolean(item, "inverse"),
            playable=_boolean(item, "playable"),
        )
        for item in _object_list(value, "edges")
    )


def _rounds(value: Any) -> tuple[Round, ...]:
    return tuple(
        Round(
            id=_string(item, "id"),
            start_id=_string(item, "start_id"),
            target_id=_string(item, "target_id"),
            category=_string(item, "category"),
            difficulty=_string(item, "difficulty"),
            optimal_distance=_integer(item, "optimal_distance"),
            time_window=_integer(item, "time_window"),
            published=_boolean(item, "published"),
        )
        for item in _object_list(value, "rounds")
    )


def _content_request(value: Any) -> ContentRequest:
    if not isinstance(value, dict):
        raise ValueError("fact pack must be an object with facts")
    content = cast(dict[str, Any], value)
    facts_value = content.get("facts")
    if not isinstance(facts_value, list):
        raise ValueError("fact pack must be an object with facts")
    aliases_value = content.get("target_aliases", [])
    if not isinstance(aliases_value, list):
        raise ValueError("target_aliases must be a string list")
    alias_items = cast(list[Any], aliases_value)
    if any(not isinstance(item, str) for item in alias_items):
        raise ValueError("target_aliases must be a string list")
    aliases = cast(list[str], alias_items)
    facts = tuple(
        Fact(
            id=_string(item, "id"),
            subject=_string(item, "subject"),
            relation=_string(item, "relation"),
            object=_string(item, "object"),
        )
        for item in _object_list(facts_value, "facts")
    )
    return ContentRequest(
        round_id=_string(content, "round_id"),
        start_label=_string(content, "start_label"),
        target_label=_string(content, "target_label"),
        target_aliases=tuple(aliases),
        facts=facts,
    )


def _read_json(path: Path) -> object:
    value: object = json.loads(path.read_text(encoding="utf-8"))
    return value


def _read_object(path: Path) -> dict[str, Any]:
    value = _read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return cast(dict[str, Any], value)


def _object_list(value: Any, name: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    result: list[dict[str, Any]] = []
    for item in cast(list[Any], value):
        if not isinstance(item, dict):
            raise ValueError(f"every {name} item must be an object")
        result.append(cast(dict[str, Any], item))
    return tuple(result)


def _write_new_json(path: Path, value: object) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to replace output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(serialized, encoding="utf-8")


def _string(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str):
        raise ValueError(f"{key} must be a string")
    return item


def _optional_string(value: dict[str, Any], key: str) -> str | None:
    item = value.get(key)
    if item is not None and not isinstance(item, str):
        raise ValueError(f"{key} must be a string or null")
    return item


def _optional_object(value: dict[str, Any], key: str) -> dict[str, Any] | None:
    item = value.get(key)
    if item is not None and not isinstance(item, dict):
        raise ValueError(f"{key} must be an object or null")
    return cast(dict[str, Any], item) if item is not None else None


def _integer(value: dict[str, Any], key: str) -> int:
    item = value.get(key)
    if not isinstance(item, int):
        raise ValueError(f"{key} must be an integer")
    return item


def _boolean(value: dict[str, Any], key: str) -> bool:
    item = value.get(key)
    if not isinstance(item, bool):
        raise ValueError(f"{key} must be a boolean")
    return item
