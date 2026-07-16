from pathlib import Path
from urllib.parse import parse_qs, urlparse

from webwoven_pipeline.wikipedia_media import (
    WikipediaMediaClient,
    _bounded_title_batches,
    article_image_names,
    lead_images_by_title,
)


class FakeTransport:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.calls: list[str] = []

    def get_json(
        self,
        url: str,
        *,
        headers: object,
        timeout: float,
    ) -> dict[str, object]:
        self.calls.append(url)
        return self.payload


def test_lead_images_follow_normalization_and_redirects() -> None:
    payload = {
        "query": {
            "normalized": [{"from": "ada_lovelace", "to": "Ada lovelace"}],
            "redirects": [{"from": "Ada lovelace", "to": "Ada Lovelace"}],
            "pages": [
                {
                    "title": "Ada Lovelace",
                    "pageimage": "Ada_Lovelace_portrait.jpg",
                }
            ],
        }
    }

    assert lead_images_by_title(payload, ["ada_lovelace"]) == {
        "ada_lovelace": "Ada Lovelace portrait.jpg"
    }


def test_client_ranks_image_used_by_more_wikipedias_first(tmp_path: Path) -> None:
    payload = {
        "query": {
            "pages": [
                {"title": "Ada Lovelace", "pageimage": "Ada portrait.jpg"},
            ]
        }
    }
    transport = FakeTransport(payload)
    client = WikipediaMediaClient(
        tmp_path,
        "Webwoven tests",
        transport=transport,
    )

    candidates = client.fetch_lead_candidates(
        {"Q7259": {"enwiki": "Ada Lovelace", "dewiki": "Ada Lovelace"}}
    )

    assert [candidate.file_name for candidate in candidates["Q7259"]] == ["Ada portrait.jpg"]
    assert candidates["Q7259"][0].site == "enwiki"
    assert len(transport.calls) == 2
    assert parse_qs(urlparse(transport.calls[0]).query)["prop"] == ["pageimages"]


def test_client_reuses_immutable_cache(tmp_path: Path) -> None:
    payload = {"query": {"pages": [{"title": "Earth", "pageimage": "Earth.jpg"}]}}
    transport = FakeTransport(payload)
    client = WikipediaMediaClient(
        tmp_path,
        "Webwoven tests",
        transport=transport,
    )
    sitelinks = {"Q2": {"enwiki": "Earth"}}

    assert client.fetch_lead_candidates(sitelinks)["Q2"][0].file_name == "Earth.jpg"
    assert client.fetch_lead_candidates(sitelinks)["Q2"][0].file_name == "Earth.jpg"
    assert len(transport.calls) == 1


def test_title_batches_stay_below_safe_get_url_size() -> None:
    titles = tuple(f"A very long Wikipedia article title number {index}" for index in range(100))

    batches = tuple(_bounded_title_batches("enwiki", titles, max_url_length=600))

    assert len(batches) > 1
    assert tuple(title for batch in batches for title in batch) == titles


def test_article_images_filter_non_visual_wikipedia_chrome() -> None:
    payload = {
        "query": {
            "pages": [
                {
                    "title": "Example",
                    "images": [
                        {"title": "File:Wikipedia-logo.svg"},
                        {"title": "File:OOjs UI icon edit-ltr-progressive.svg"},
                        {"title": "File:Symbol category class.svg"},
                        {"title": "File:Relevant portrait.jpg"},
                        {"title": "File:Spoken article.ogg"},
                    ],
                }
            ]
        }
    }

    assert article_image_names(payload) == ("Relevant portrait.jpg",)


def test_article_candidates_require_entity_specific_filename_evidence(
    tmp_path: Path,
) -> None:
    payload = {
        "query": {
            "pages": [
                {
                    "title": "Golden Arrow Award",
                    "images": [
                        {"title": "File:Film-award-stub.svg"},
                        {"title": "File:Golden Arrow Award ceremony.jpg"},
                    ],
                }
            ]
        }
    }
    client = WikipediaMediaClient(
        tmp_path,
        "Webwoven tests",
        transport=FakeTransport(payload),
    )

    candidates = client.fetch_article_candidates(
        {"Q1": {"enwiki": "Golden Arrow Award"}},
        {"Q1": "Golden Arrow Award"},
        entity_ids=("Q1",),
    )

    assert [candidate.file_name for candidate in candidates["Q1"]] == [
        "Golden Arrow Award ceremony.jpg"
    ]
