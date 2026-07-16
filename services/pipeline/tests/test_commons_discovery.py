from collections.abc import Mapping
from pathlib import Path

from webwoven_pipeline.commons_discovery import CommonsDiscoveryClient
from webwoven_pipeline.media_context import MediaContextHint


class FakeTransport:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls = 0

    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
    ) -> dict[str, object]:
        self.calls += 1
        return self.payload


def test_category_candidates_rank_entity_title_match_first(tmp_path: Path) -> None:
    transport = FakeTransport(
        {
            "query": {
                "categorymembers": [
                    {"title": "File:Unrelated icon.svg"},
                    {"title": "File:Ada Lovelace portrait.jpg"},
                ]
            }
        }
    )
    client = CommonsDiscoveryClient(
        tmp_path,
        "Webwoven tests",
        transport=transport,
        request_interval=0,
    )

    result = client.fetch_category_candidates(
        ["Q7259"],
        {"Q7259": "Ada Lovelace"},
        {"Q7259": "Ada Lovelace"},
    )

    assert [candidate.file_name for candidate in result["Q7259"]] == [
        "Ada Lovelace portrait.jpg",
        "Unrelated icon.svg",
    ]
    assert result["Q7259"][0].provenance == "commons_category:Ada Lovelace"
    assert transport.calls == 1
    client.fetch_category_candidates(
        ["Q7259"],
        {"Q7259": "Ada Lovelace"},
        {"Q7259": "Ada Lovelace"},
    )
    assert transport.calls == 1


def test_depicts_and_label_search_candidates(tmp_path: Path) -> None:
    transport = FakeTransport(
        {
            "query": {
                "search": [
                    {"title": "File:Analytical Engine.jpg"},
                    {"title": "File:Ada Lovelace portrait.jpg"},
                    {"title": "File:Charles Babbage portrait.jpg"},
                ]
            }
        }
    )
    client = CommonsDiscoveryClient(
        tmp_path,
        "Webwoven tests",
        transport=transport,
        request_interval=0,
    )

    depicts = client.fetch_depicts_candidates(["Q7259"], {"Q7259": "Ada Lovelace"})
    labels = client.fetch_label_candidates(["Q7259"], {"Q7259": "Ada Lovelace"})
    broad = client.fetch_broad_candidates(["Q7259"], {"Q7259": "Ada Lovelace"})
    context = client.fetch_context_candidates(
        ["Q7259"],
        {"Q7259": (MediaContextHint("Q42", "Charles Babbage", "P50"),)},
    )

    assert depicts["Q7259"][0].provenance == "commons_depicts:Q7259"
    assert [candidate.file_name for candidate in labels["Q7259"]] == ["Ada Lovelace portrait.jpg"]
    assert labels["Q7259"][0].provenance == "commons_search:Ada Lovelace"
    assert broad["Q7259"][0].provenance == "commons_media_search:Ada Lovelace"
    assert [candidate.file_name for candidate in context["Q7259"]] == [
        "Charles Babbage portrait.jpg"
    ]
    assert context["Q7259"][0].provenance == "commons_context:P50:Q42:Charles Babbage"
