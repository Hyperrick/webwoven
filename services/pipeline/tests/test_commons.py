from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from webwoven_pipeline.commons import (
    CommonsClient,
    _bounded_file_batches,
    parse_commons_response,
)


def _page(
    title: str,
    license_name: str,
    *,
    artist: str = "Ada",
    license_url: str = "https://creativecommons.org/licenses/by/4.0/",
) -> dict:
    return {
        "title": f"File:{title}",
        "imageinfo": [
            {
                "url": "https://upload.wikimedia.org/original.jpg",
                "thumburl": "https://upload.wikimedia.org/thumb.jpg",
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:Example.jpg",
                "extmetadata": {
                    "LicenseShortName": {"value": license_name},
                    "Artist": {"value": artist},
                    "LicenseUrl": {"value": license_url},
                },
            }
        ],
    }


def test_license_filter_accepts_complete_cc_by_and_public_domain() -> None:
    payload = {
        "query": {
            "pages": [
                _page("By.jpg", "CC BY 4.0", artist="<b>Ada</b>"),
                _page("PD.jpg", "Public domain", artist="", license_url=""),
            ]
        }
    }

    records = parse_commons_response(payload)

    assert [item.license_id for item in records] == ["CC_BY_4_0", "PUBLIC_DOMAIN"]
    assert records[0].creator == "Ada"
    assert records[1].creator == "Unknown creator"
    assert records[1].license_url == "https://creativecommons.org/publicdomain/mark/1.0/"


def test_license_filter_accepts_share_alike_and_rejects_incomplete_attribution() -> None:
    payload = {
        "query": {
            "pages": [
                _page(
                    "SA.jpg",
                    "CC BY-SA 4.0",
                    license_url="https://creativecommons.org/licenses/by-sa/4.0/",
                ),
                _page("Incomplete.jpg", "CC BY 4.0", artist="", license_url=""),
            ]
        }
    }

    records = parse_commons_response(payload)

    assert [item.license_id for item in records] == ["CC_BY_SA_4_0"]
    assert records[0].attribution_text == "Ada — CC BY-SA 4.0 — Wikimedia Commons"


def test_license_filter_accepts_supported_cc_by_versions() -> None:
    payload = {
        "query": {
            "pages": [
                _page(
                    "By2.jpg",
                    "CC BY 2.0",
                    license_url="https://creativecommons.org/licenses/by/2.0/",
                ),
                _page(
                    "ShareAlike3.jpg",
                    "CC BY-SA 3.0",
                    license_url="https://creativecommons.org/licenses/by-sa/3.0/",
                ),
            ]
        }
    }

    records = parse_commons_response(payload)

    assert [item.license_id for item in records] == ["CC_BY_2_0", "CC_BY_SA_3_0"]


def test_license_filter_accepts_historical_http_and_ported_cc_urls() -> None:
    records = parse_commons_response(
        {
            "query": {
                "pages": [
                    _page(
                        "Http.jpg",
                        "CC BY-SA 3.0",
                        license_url="http://creativecommons.org/licenses/by-sa/3.0/",
                    ),
                    _page(
                        "Ported.jpg",
                        "CC BY-SA 3.0 de",
                        license_url=("https://creativecommons.org/licenses/by-sa/3.0/de/deed.en"),
                    ),
                ]
            }
        }
    )

    assert [item.license_id for item in records] == ["CC_BY_SA_3_0", "CC_BY_SA_3_0"]
    assert records[0].license_url == "https://creativecommons.org/licenses/by-sa/3.0/"
    assert records[1].license_url.endswith("/by-sa/3.0/de/deed.en")


def test_metadata_filter_rejects_non_wikimedia_media_or_license_hosts() -> None:
    redirected_media = _page("Redirect.jpg", "Public domain")
    redirected_media["imageinfo"][0]["thumburl"] = "https://example.test/image.jpg"
    redirected_license = _page(
        "License.jpg",
        "CC BY 4.0",
        license_url="https://example.test/license",
    )
    mismatched_license = _page(
        "Wrong license.jpg",
        "CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by-sa/4.0/",
    )

    assert (
        parse_commons_response(
            {"query": {"pages": [redirected_media, redirected_license, mismatched_license]}}
        )
        == ()
    )


def test_metadata_preserves_non_copyright_notices_and_required_credit() -> None:
    restricted = _page("Trademark.svg", "Public domain")
    restricted["imageinfo"][0]["extmetadata"]["Restrictions"] = {"value": "trademarked"}
    attributed = _page("Attributed.jpg", "CC BY 4.0", artist="Example creator")
    attributed["imageinfo"][0]["extmetadata"].update(
        {
            "AttributionRequired": {"value": "true"},
            "Attribution": {"value": "<b>Required credit line</b>"},
        }
    )

    records = parse_commons_response({"query": {"pages": [restricted, attributed]}})

    assert len(records) == 2
    assert records[0].creator == "Example creator"
    assert records[0].attribution_text == (
        "Required credit line · Example creator — CC BY 4.0 — Wikimedia Commons"
    )
    assert records[0].restrictions == ""
    assert records[0].explicit_attribution == "Required credit line"
    assert records[1].restrictions == "trademarked"


def test_required_attribution_never_replaces_creator_with_generic_credit() -> None:
    attributed = _page("Own work.jpg", "CC BY 4.0", artist="Named creator")
    attributed["imageinfo"][0]["extmetadata"].update(
        {
            "AttributionRequired": {"value": "true"},
            "Credit": {"value": "Own work"},
        }
    )

    record = parse_commons_response({"query": {"pages": [attributed]}})[0]

    assert record.attribution_text == "Named creator — CC BY 4.0 — Wikimedia Commons"


def test_metadata_batches_stay_below_safe_get_url_size() -> None:
    names = tuple(f"A very long Commons file name number {index}.jpg" for index in range(100))

    batches = tuple(_bounded_file_batches(names, max_url_length=700))

    assert len(batches) > 1
    assert tuple(name for batch in batches for name in batch) == names


class RejectingTitleTransport:
    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
    ) -> dict[str, object]:
        titles = parse_qs(urlparse(url).query)["titles"][0].split("|")
        if any(title == "File:Bad.jpg" for title in titles):
            return {"error": {"code": "urlparamnormal"}}
        return {
            "query": {
                "pages": [_page(title.removeprefix("File:"), "CC BY 4.0") for title in titles]
            }
        }


def test_metadata_client_isolates_a_rejected_file_title(tmp_path: Path) -> None:
    client = CommonsClient(
        "Webwoven tests",
        transport=RejectingTitleTransport(),
        sleeper=lambda _: None,
    )

    records = client.fetch_metadata(["Good.jpg", "Bad.jpg"])

    assert list(records) == ["Good.jpg"]
