from __future__ import annotations

from webwoven_pipeline.normalization import (
    commons_file_name,
    normalize_edges,
    normalize_entities,
)


def _statement(target: str, statement_id: str, *, rank: str = "normal") -> dict:
    return {
        "id": statement_id,
        "rank": rank,
        "mainsnak": {
            "snaktype": "value",
            "datavalue": {"value": {"id": target}},
        },
    }


def test_normalizer_filters_claims_and_materializes_configured_inverse(registry) -> None:
    raw = {
        "Q1": {
            "labels": {"en": {"value": "One"}},
            "descriptions": {"en": {"value": "First"}},
            "claims": {
                "P19": [
                    _statement("Q1", "Q1$self"),
                    _statement("Q2", "Q1$valid"),
                    _statement("Q3", "Q1$deprecated", rank="deprecated"),
                    _statement("Q4", "Q1$unlabelled"),
                ]
            },
        },
        "Q2": {"labels": {"en": {"value": "Two"}}, "claims": {}},
        "Q3": {"labels": {"en": {"value": "Three"}}, "claims": {}},
        "Q4": {"claims": {}},
    }

    entities = normalize_entities(
        raw,
        {"Q1": "history_people", "Q2": "places", "Q3": "places", "Q4": "places"},
    )
    edges = normalize_edges(raw, registry, allowed_qids=(item.id for item in entities))

    assert [item.label for item in entities] == ["One", "Two", "Three"]
    assert {(item.source_id, item.target_id, item.explanation, item.inverse) for item in edges} == {
        (
            "Q1",
            "Q2",
            "One was born in Two.",
            False,
        ),
        (
            "Q2",
            "Q1",
            "One was born in Two.",
            True,
        ),
    }


def test_commons_candidate_prefers_preferred_rank_before_file_name() -> None:
    raw = {
        "claims": {
            "P18": [
                _media_statement("A normal image.jpg", rank="normal"),
                _media_statement("Z preferred image.jpg", rank="preferred"),
                _media_statement("Deprecated.jpg", rank="deprecated"),
            ]
        }
    }

    assert commons_file_name(raw) == "Z preferred image.jpg"


def test_commons_candidate_uses_ranked_entity_specific_media_properties() -> None:
    raw = {
        "claims": {
            "P154": [_media_statement("Entity logo.svg", rank="preferred")],
            "P242": [_media_statement("Entity locator map.png", rank="normal")],
        }
    }

    assert commons_file_name(raw) == "Entity locator map.png"


def test_commons_candidate_never_uses_audio_media() -> None:
    raw = {
        "claims": {
            "P443": [_media_statement("Pronunciation.ogg", rank="preferred")],
        }
    }

    assert commons_file_name(raw) is None


def _media_statement(file_name: str, *, rank: str) -> dict:
    return {
        "rank": rank,
        "mainsnak": {
            "snaktype": "value",
            "datavalue": {"value": file_name},
        },
    }
