from __future__ import annotations

from webwoven_pipeline.normalization import (
    commons_file_name,
    normalize_edges,
    normalize_entities,
)


def _statement(
    target: str,
    statement_id: str,
    *,
    rank: str = "normal",
    series_ordinal: str | None = None,
) -> dict:
    statement = {
        "id": statement_id,
        "rank": rank,
        "mainsnak": {
            "snaktype": "value",
            "datavalue": {"value": {"id": target}},
        },
    }
    if series_ordinal is not None:
        statement["qualifiers"] = {
            "P1545": [
                {
                    "snaktype": "value",
                    "datavalue": {"value": series_ordinal},
                }
            ]
        }
    return statement


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
        {
            "Q1": "people",
            "Q2": "places_architecture",
            "Q3": "places_architecture",
            "Q4": "places_architecture",
        },
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


def test_normalizer_uses_ranked_selection_semantics_in_both_directions(registry) -> None:
    raw = {
        "Q1": {
            "labels": {"en": {"value": "Animal Farm"}},
            "descriptions": {"en": {"value": "1945 novella by George Orwell"}},
            "claims": {
                "P166": [_statement("Q2", "Q1$list", series_ordinal="13")],
            },
        },
        "Q2": {
            "labels": {"en": {"value": "NPR Top 100 Science Fiction and Fantasy Books"}},
            "descriptions": {"en": {"value": "literature award in 2011 based on public votes"}},
            "claims": {
                "P31": [
                    _statement("Q378427", "Q2$award"),
                    _statement("Q49958", "Q2$poll"),
                ]
            },
        },
    }

    edges = normalize_edges(raw, registry)

    expected = "Animal Farm ranked #13 on the NPR Top 100 Science Fiction and Fantasy Books."
    assert {(edge.inverse, edge.explanation) for edge in edges} == {
        (False, expected),
        (True, expected),
    }
    assert {edge.series_ordinal for edge in edges} == {"13"}


def test_normalizer_uses_language_country_semantics_in_both_directions(registry) -> None:
    raw = {
        "Q1": {
            "labels": {"en": {"value": "English"}},
            "descriptions": {"en": {"value": "West Germanic language"}},
            "claims": {
                "P31": [_statement("Q33742", "Q1$language")],
                "P17": [_statement("Q2", "Q1$country")],
            },
        },
        "Q2": {
            "labels": {"en": {"value": "United States"}},
            "descriptions": {"en": {"value": "country in North America"}},
            "claims": {"P31": [_statement("Q6256", "Q2$country")]},
        },
    }

    entities = normalize_entities(raw, {"Q1": "literature_language", "Q2": "places_architecture"})
    edges = normalize_edges(raw, registry)

    assert {(edge.inverse, edge.explanation) for edge in edges} == {
        (False, "English is used in the United States."),
        (True, "English is used in the United States."),
    }
    assert next(entity for entity in entities if entity.id == "Q1").semantic_tags == ("language",)


def test_normalizer_uses_neutral_copy_for_unclassified_recognition(registry) -> None:
    raw = {
        "Q1": {
            "labels": {"en": {"value": "Bauhaus"}},
            "descriptions": {"en": {"value": "German art school"}},
            "claims": {"P166": [_statement("Q2", "Q1$recognition")]},
        },
        "Q2": {
            "labels": {"en": {"value": "8502 Bauhaus"}},
            "descriptions": {"en": {"value": "asteroid"}},
            "claims": {},
        },
    }

    entities = normalize_entities(
        raw,
        {"Q1": "art_design", "Q2": "science_technology"},
    )
    edges = normalize_edges(raw, registry)

    assert next(entity for entity in entities if entity.id == "Q2").semantic_tags == (
        "recognition",
    )
    assert {edge.explanation for edge in edges} == {
        "Bauhaus has a recorded recognition connection to the 8502 Bauhaus."
    }


def test_normalizer_does_not_infer_language_from_incidental_description_text() -> None:
    raw = {
        "Q1": {
            "labels": {"en": {"value": "\u200eMcGill University"}},
            "descriptions": {"en": {"value": "English-language public research university\u200b"}},
            "claims": {"P31": [_statement("Q3918", "Q1$university")]},
        }
    }

    entities = normalize_entities(raw, {"Q1": "education_knowledge"})

    assert entities[0].label == "McGill University"
    assert entities[0].description == "English-language public research university"
    assert entities[0].semantic_tags == ("organization",)


def test_normalizer_uses_safe_country_fallback_without_structured_subject_semantics(
    registry,
) -> None:
    raw = {
        "Q1": {
            "labels": {"en": {"value": "Bombe"}},
            "descriptions": {"en": {"value": "codebreaking device created at Bletchley Park"}},
            "claims": {"P17": [_statement("Q4", "Q1$country")]},
        },
        "Q2": {
            "labels": {"en": {"value": "Bavarian Order of Merit"}},
            "descriptions": {"en": {"value": "state decoration of Bavaria"}},
            "claims": {"P17": [_statement("Q5", "Q2$country")]},
        },
        "Q3": {
            "labels": {"en": {"value": "Bauhaus and its Sites in Weimar, Dessau and Bernau"}},
            "descriptions": {
                "en": {"value": "World Heritage Site associated with the Bauhaus art school"}
            },
            "claims": {"P17": [_statement("Q5", "Q3$country")]},
        },
        "Q4": {
            "labels": {"en": {"value": "United Kingdom"}},
            "descriptions": {"en": {"value": "sovereign country"}},
            "claims": {},
        },
        "Q5": {
            "labels": {"en": {"value": "Germany"}},
            "descriptions": {"en": {"value": "sovereign country"}},
            "claims": {},
        },
        "Q6": {
            "labels": {"en": {"value": "Example recipient"}},
            "descriptions": {"en": {"value": "fictional person"}},
            "claims": {"P166": [_statement("Q2", "Q6$recognition")]},
        },
    }

    edges = normalize_edges(raw, registry)
    country_explanations = {edge.explanation for edge in edges if edge.relation_key == "P17"}

    assert country_explanations == {
        "Bombe is associated with the United Kingdom.",
        "Bavarian Order of Merit is associated with Germany.",
        "Bauhaus and its Sites in Weimar, Dessau and Bernau is associated with Germany.",
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
