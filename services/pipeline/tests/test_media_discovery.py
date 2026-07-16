from collections.abc import Iterable, Mapping
from pathlib import Path

from webwoven_pipeline.media_discovery import (
    CommonsLicenseValidator,
    discover_media,
)
from webwoven_pipeline.models import MediaRecord
from webwoven_pipeline.wikipedia_media import WikipediaMediaClient


class FakeWikipediaTransport:
    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
    ) -> dict[str, object]:
        return {
            "query": {
                "pages": [
                    {"title": "Missing direct", "pageimage": "Lead image.jpg"},
                    {"title": "Rejected direct", "pageimage": "Replacement image.jpg"},
                ]
            }
        }


class FakeCommonsClient:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_metadata(self, file_names: Iterable[str]) -> dict[str, MediaRecord]:
        self.calls += 1
        accepted = {"Direct image.jpg", "Lead image.jpg", "Replacement image.jpg"}
        return {file_name: _record(file_name) for file_name in file_names if file_name in accepted}


class AcceptAllCommonsClient:
    def fetch_metadata(self, file_names: Iterable[str]) -> dict[str, MediaRecord]:
        return {file_name: _record(file_name) for file_name in file_names}


class SharedImageWikipediaTransport:
    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
    ) -> dict[str, object]:
        return {
            "query": {
                "pages": [
                    {"title": "First subject", "pageimage": "Shared portrait.jpg"},
                    {"title": "Second subject", "pageimage": "Shared portrait.jpg"},
                ]
            }
        }


def test_discovery_replaces_rejected_direct_media_with_wikipedia_lead(
    tmp_path: Path,
) -> None:
    commons = FakeCommonsClient()
    validator = CommonsLicenseValidator(tmp_path / "commons", "Webwoven tests", client=commons)
    wikipedia = WikipediaMediaClient(
        tmp_path / "wikipedia",
        "Webwoven tests",
        transport=FakeWikipediaTransport(),
    )

    result = discover_media(
        ["Q1", "Q2", "Q3"],
        {"Q1": "Direct_image.jpg", "Q2": "Unsupported.jpg"},
        {"Q1": "P18", "Q2": "P18"},
        {
            "Q2": {"enwiki": "Rejected direct"},
            "Q3": {"enwiki": "Missing direct"},
        },
        wikipedia_client=wikipedia,
        license_validator=validator,
    )

    assert result.files_by_entity == {
        "Q1": "Direct image.jpg",
        "Q2": "Replacement image.jpg",
        "Q3": "Lead image.jpg",
    }
    assert result.sources_by_entity["Q2"] == "wikipedia_lead:enwiki:Rejected direct"
    assert result.direct_count == 1
    assert result.wikipedia_count == 2
    assert result.category_count == 0
    assert result.depicts_count == 0
    assert result.search_count == 0
    assert result.broad_search_count == 0
    assert result.wikipedia_article_count == 0
    assert result.context_count == 0
    assert result.reviewed_count == 0
    assert result.missing_entity_ids == ()

    calls = commons.calls
    assert validator.accepted_files(["Direct_image.jpg", "Unsupported.jpg"]) == {"Direct image.jpg"}
    assert commons.calls == calls


def test_discovery_keeps_a_shared_exact_image_for_both_entities(tmp_path: Path) -> None:
    commons = AcceptAllCommonsClient()
    validator = CommonsLicenseValidator(tmp_path / "commons", "Webwoven tests", client=commons)
    wikipedia = WikipediaMediaClient(
        tmp_path / "wikipedia",
        "Webwoven tests",
        transport=SharedImageWikipediaTransport(),
    )
    result = discover_media(
        ["Q1", "Q2"],
        {},
        {},
        {
            "Q1": {"enwiki": "First subject"},
            "Q2": {"enwiki": "Second subject"},
        },
        wikipedia_client=wikipedia,
        license_validator=validator,
    )

    assert result.files_by_entity == {
        "Q1": "Shared portrait.jpg",
        "Q2": "Shared portrait.jpg",
    }


def _record(file_name: str) -> MediaRecord:
    return MediaRecord(
        file_name=file_name,
        original_url="https://upload.wikimedia.org/original.jpg",
        derivative_url="https://upload.wikimedia.org/thumb.jpg",
        source_url="https://commons.wikimedia.org/wiki/File:Example.jpg",
        license_id="CC0_1_0",
        creator="Creator",
        license_url="https://creativecommons.org/publicdomain/zero/1.0/",
        attribution_text="Creator — CC0 1.0 — Wikimedia Commons",
        restrictions="",
        explicit_attribution="",
    )
