from __future__ import annotations

from webwoven_pipeline.normalization import normalize_edges, normalize_entities


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
