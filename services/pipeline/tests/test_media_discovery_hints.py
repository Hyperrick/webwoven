from webwoven_pipeline.media_discovery_hints import (
    commons_category_name,
    wikipedia_sitelinks,
)


def _statement(value: str, rank: str = "normal") -> dict:
    return {
        "rank": rank,
        "mainsnak": {
            "snaktype": "value",
            "datavalue": {"value": value},
        },
    }


def test_commons_category_prefers_preferred_non_deprecated_claim() -> None:
    raw = {
        "claims": {
            "P373": [
                _statement("Normal category"),
                _statement("Preferred category", "preferred"),
                _statement("Deprecated category", "deprecated"),
            ]
        }
    }

    assert commons_category_name(raw) == "Preferred category"


def test_wikipedia_sitelinks_keep_supported_sites_in_priority_order() -> None:
    raw = {
        "sitelinks": {
            "commonswiki": {"title": "Category:Example"},
            "frwiki": {"title": "Exemple"},
            "enwiki": {"title": "Example"},
            "simplewiki": {"title": "Example"},
        }
    }

    assert wikipedia_sitelinks(raw) == {
        "enwiki": "Example",
        "frwiki": "Exemple",
    }
