from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from .acquisition import acquire_graph
from .cli_serialization import (
    nested_string_mapping as _nested_string_mapping,
)
from .cli_serialization import (
    object_list as _object_list,
)
from .cli_serialization import (
    parse_content_request as _content_request,
)
from .cli_serialization import (
    parse_edges as _edges,
)
from .cli_serialization import (
    parse_entities as _entities,
)
from .cli_serialization import (
    parse_rounds as _rounds,
)
from .cli_serialization import (
    read_json as _read_json,
)
from .cli_serialization import (
    read_object as _read_object,
)
from .cli_serialization import (
    string_mapping as _string_mapping,
)
from .cli_serialization import (
    write_new_json as _write_new_json,
)
from .codex_artifacts import ingest_codex_artifact
from .commons import CommonsClient
from .commons_assets import (
    acquire_commons_assets,
    enrich_entities_with_commons,
    load_commons_media_bundle,
)
from .commons_discovery import CommonsDiscoveryClient
from .compiler import compile_graph
from .fixture import generate_smoke_fixture
from .manifest import verify_manifest
from .media_candidates import wikidata_media_candidate
from .media_context import build_media_context_hints
from .media_discovery import CommonsLicenseValidator, discover_media
from .media_discovery_hints import commons_category_name, wikipedia_sitelinks
from .normalization import normalize_edges, normalize_entities
from .registry import load_registry
from .reviewed_media import REVIEWED_MEDIA_CANDIDATES, REVIEWED_MEDIA_OVERRIDES
from .rounds import DEFAULT_SELECTION_SEED, generate_rounds
from .seeds import load_seeds
from .semantic_refresh import refresh_wikidata_relationships
from .wikidata import WikidataClient
from .wikidata_bundle import build_wikidata_bundle
from .wikipedia_articles import attach_wikipedia_articles
from .wikipedia_media import WikipediaMediaClient

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
    elif command == "acquire-commons":
        _acquire_commons(args)
    elif command == "discover-media":
        _discover_media(args)
    elif command == "renormalize-semantics":
        _renormalize_semantics(args)
    elif command == "generate-rounds":
        _generate_rounds(args)
    elif command == "compile":
        _compile(args)
    elif command == "build-wikidata-pack":
        _build_wikidata_pack(args)
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
    acquire.add_argument("--max-lag", type=int, default=5)
    acquire.add_argument("--request-interval", type=float, default=0.25)

    commons = commands.add_parser("commons-metadata", help="fetch and filter Commons metadata")
    commons.add_argument("--files", type=Path, required=True)
    commons.add_argument("--output", type=Path, required=True)
    commons.add_argument("--user-agent", required=True)
    commons_assets = commands.add_parser(
        "acquire-commons",
        help="download allowlisted Commons media for every graph entity",
    )
    commons_assets.add_argument("--graph-source", type=Path, required=True)
    commons_assets.add_argument("--output", type=Path, required=True)
    commons_assets.add_argument("--user-agent", required=True)
    commons_assets.add_argument("--created-at", required=True)
    commons_assets.add_argument("--download-interval", type=float, default=1.0)
    commons_assets.add_argument("--download-workers", type=int, default=4)
    commons_assets.add_argument(
        "--require-complete",
        action="store_true",
        help="fail unless every graph entity publishes a validated local image",
    )
    commons_assets.add_argument(
        "--reuse-manifest",
        type=Path,
        help="reuse hash-verified assets from an earlier Commons media pack",
    )
    discover_media_command = commands.add_parser(
        "discover-media",
        help="select license-validated Commons media for exact graph entities",
    )
    discover_media_command.add_argument("--graph-source", type=Path, required=True)
    discover_media_command.add_argument("--cache", type=Path, required=True)
    discover_media_command.add_argument("--output", type=Path, required=True)
    discover_media_command.add_argument("--user-agent", required=True)
    discover_media_command.add_argument("--request-interval", type=float, default=0.1)
    semantic_refresh = commands.add_parser(
        "renormalize-semantics",
        help="rebuild relationship wording from hash-verified cached Wikidata batches",
    )
    _registry_argument(semantic_refresh)
    semantic_refresh.add_argument("--graph-source", type=Path, required=True)
    semantic_refresh.add_argument("--cache", type=Path, required=True)
    semantic_refresh.add_argument("--output", type=Path, required=True)
    round_command = commands.add_parser(
        "generate-rounds",
        help="generate locked round distribution",
    )
    round_command.add_argument("--graph-source", type=Path, required=True)
    round_command.add_argument("--output", type=Path, required=True)
    round_command.add_argument(
        "--seeds",
        type=Path,
        help="restrict round starts and targets to curated anchors",
    )
    round_command.add_argument("--selection-seed", default=DEFAULT_SELECTION_SEED)
    compile_command = commands.add_parser("compile", help="compile normalized JSON to SQLite")
    _registry_argument(compile_command)
    compile_command.add_argument("--graph-source", type=Path, required=True)
    compile_command.add_argument("--rounds", type=Path, required=True)
    compile_command.add_argument("--output", type=Path, required=True)
    wikidata_pack = commands.add_parser(
        "build-wikidata-pack",
        help="assemble a validated real-data bundle",
    )
    _registry_argument(wikidata_pack)
    wikidata_pack.add_argument("--seeds", type=Path, required=True)
    wikidata_pack.add_argument("--graph-source", type=Path, required=True)
    wikidata_pack.add_argument("--output", type=Path, required=True)
    wikidata_pack.add_argument("--created-at", required=True)
    wikidata_pack.add_argument(
        "--commons-manifest",
        type=Path,
        help="validated local Commons media manifest to include in the bundle",
    )
    wikidata_pack.add_argument("--selection-seed", default=DEFAULT_SELECTION_SEED)
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
    client = WikidataClient(
        args.cache,
        args.user_agent,
        max_lag=args.max_lag,
        request_interval=args.request_interval,
    )
    acquired = acquire_graph(
        seeds,
        registry,
        client,
        hops=args.hops,
        max_entities=args.max_entities,
    )
    entities = normalize_entities(acquired.entities, acquired.category_by_qid)
    edges = normalize_edges(
        acquired.entities,
        registry,
        allowed_qids=(item.id for item in entities),
    )
    batches = [
        {
            "path": batch.cache_path.name,
            "qids": list(batch.qids),
            "sha256": batch.sha256,
        }
        for batch in acquired.batches
    ]
    media_candidate_records = {
        item.id: candidate
        for item in entities
        if (candidate := wikidata_media_candidate(acquired.entities[item.id])) is not None
    }
    commons_categories = {
        item.id: category_name
        for item in entities
        if (category_name := commons_category_name(acquired.entities[item.id])) is not None
    }
    article_sitelinks = {
        item.id: sitelinks
        for item in entities
        if (sitelinks := wikipedia_sitelinks(acquired.entities[item.id]))
    }
    _write_new_json(
        args.output,
        {
            "schema_version": 2,
            "source": "wikidata",
            "entities": [item.to_dict() for item in entities],
            "edges": [item.to_dict() for item in edges],
            "source_batches": batches,
            "commons_media_candidates": {
                qid: candidate.file_name for qid, candidate in media_candidate_records.items()
            },
            "commons_media_sources": {
                qid: candidate.property_id for qid, candidate in media_candidate_records.items()
            },
            "commons_category_candidates": commons_categories,
            "wikipedia_sitelinks": article_sitelinks,
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


def _acquire_commons(args: argparse.Namespace) -> None:
    source = _read_object(args.graph_source)
    if source.get("schema_version") != 2 or source.get("source") != "wikidata":
        raise ValueError("graph source must be a Wikidata schema-v2 acquisition")
    candidates = _string_mapping(
        source.get("commons_media_candidates"),
        "commons_media_candidates",
    )
    entities = _entities(source.get("entities"))
    bundle = acquire_commons_assets(
        candidates,
        (item.id for item in entities),
        args.output,
        user_agent=args.user_agent,
        created_at=args.created_at,
        download_interval=args.download_interval,
        download_workers=args.download_workers,
        require_complete=args.require_complete,
        reuse_bundle=(
            load_commons_media_bundle(args.reuse_manifest) if args.reuse_manifest else None
        ),
    )
    print(bundle.manifest_path)


def _discover_media(args: argparse.Namespace) -> None:
    source = _read_object(args.graph_source)
    if source.get("schema_version") != 2 or source.get("source") != "wikidata":
        raise ValueError("graph source must be a Wikidata schema-v2 acquisition")
    entities = _entities(source.get("entities"))
    direct_candidates = _string_mapping(
        source.get("commons_media_candidates"),
        "commons_media_candidates",
    )
    direct_sources = _string_mapping(
        source.get("commons_media_sources"),
        "commons_media_sources",
    )
    entity_ids = {entity.id for entity in entities}
    for qid, candidate in REVIEWED_MEDIA_OVERRIDES.items():
        if qid in entity_ids:
            direct_candidates[qid] = candidate.file_name
            direct_sources[qid] = candidate.provenance
    sitelinks = _nested_string_mapping(
        source.get("wikipedia_sitelinks"),
        "wikipedia_sitelinks",
    )
    commons_categories = _string_mapping(
        source.get("commons_category_candidates"),
        "commons_category_candidates",
    )
    labels = {entity.id: entity.label for entity in entities}
    edges = _edges(source.get("edges"))
    result = discover_media(
        (entity.id for entity in entities),
        direct_candidates,
        direct_sources,
        sitelinks,
        wikipedia_client=WikipediaMediaClient(
            args.cache / "wikipedia",
            args.user_agent,
            request_interval=args.request_interval,
        ),
        license_validator=CommonsLicenseValidator(
            args.cache / "commons-validation",
            args.user_agent,
        ),
        commons_client=CommonsDiscoveryClient(
            args.cache / "commons-discovery",
            args.user_agent,
            request_interval=args.request_interval,
        ),
        commons_categories=commons_categories,
        entity_labels=labels,
        context_hints=build_media_context_hints(
            (entity.id for entity in entities),
            labels,
            edges,
        ),
        reviewed_candidates=REVIEWED_MEDIA_CANDIDATES,
    )
    enriched = dict(source)
    enriched["commons_media_candidates"] = result.files_by_entity
    enriched["commons_media_sources"] = result.sources_by_entity
    enriched["media_discovery"] = {
        "strategy": "ranked_wikimedia_entity_media_with_documented_graph_context",
        "requested_entities": len(entities),
        "published_entities": len(result.selections),
        "direct_entities": result.direct_count,
        "wikipedia_entities": result.wikipedia_count,
        "category_entities": result.category_count,
        "depicts_entities": result.depicts_count,
        "search_entities": result.search_count,
        "broad_search_entities": result.broad_search_count,
        "wikipedia_article_entities": result.wikipedia_article_count,
        "context_entities": result.context_count,
        "reviewed_entities": result.reviewed_count,
        "missing_entities": list(result.missing_entity_ids),
    }
    _write_new_json(args.output, enriched)
    print(
        f"{len(result.selections)}/{len(entities)} entities selected; "
        f"{len(result.missing_entity_ids)} unresolved"
    )


def _renormalize_semantics(args: argparse.Namespace) -> None:
    source = _read_object(args.graph_source)
    entities = _entities(source.get("entities"))
    refreshed = refresh_wikidata_relationships(
        source,
        args.cache,
        load_registry(args.registry),
        (entity.id for entity in entities),
    )
    _write_new_json(args.output, refreshed)
    print(f"{len(refreshed['edges'])} relationships renormalized without network access")


def _generate_rounds(args: argparse.Namespace) -> None:
    source = _read_object(args.graph_source)
    entities = _entities(source.get("entities"))
    edges = _edges(source.get("edges"))
    endpoint_ids = load_seeds(args.seeds).qids if args.seeds else None
    rounds = generate_rounds(
        entities,
        edges,
        selection_seed=args.selection_seed,
        endpoint_ids=endpoint_ids,
    )
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


def _build_wikidata_pack(args: argparse.Namespace) -> None:
    source = _read_object(args.graph_source)
    if source.get("schema_version") != 2 or source.get("source") != "wikidata":
        raise ValueError("graph source must be a Wikidata schema-v2 acquisition")
    registry = load_registry(args.registry)
    seeds = load_seeds(args.seeds)
    source_batches = _object_list(source.get("source_batches"), "source_batches")
    commons_media = (
        load_commons_media_bundle(args.commons_manifest) if args.commons_manifest else None
    )
    commons_media_candidates = (
        _string_mapping(
            source.get("commons_media_candidates"),
            "commons_media_candidates",
        )
        if commons_media is not None
        else None
    )
    entities = attach_wikipedia_articles(
        _entities(source.get("entities")),
        _nested_string_mapping(source.get("wikipedia_sitelinks"), "wikipedia_sitelinks"),
    )
    commons_media_sources = (
        _string_mapping(source.get("commons_media_sources"), "commons_media_sources")
        if commons_media is not None
        else None
    )
    if commons_media is not None:
        entities = enrich_entities_with_commons(
            entities,
            commons_media,
            commons_media_sources,
        )
    build_id = build_wikidata_bundle(
        args.output,
        registry,
        entities,
        _edges(source.get("edges")),
        source_batches,
        endpoint_ids=seeds.qids,
        created_at=args.created_at,
        selection_seed=args.selection_seed,
        commons_media=commons_media,
        commons_media_candidates=commons_media_candidates,
        commons_media_sources=commons_media_sources,
        require_complete_media=commons_media is not None,
    )
    print(build_id)
