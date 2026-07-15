from __future__ import annotations

from webwoven_pipeline.commons import parse_commons_response


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


def test_license_filter_rejects_share_alike_and_incomplete_attribution() -> None:
    payload = {
        "query": {
            "pages": [
                _page("SA.jpg", "CC BY-SA 4.0"),
                _page("Incomplete.jpg", "CC BY 4.0", artist="", license_url=""),
            ]
        }
    }

    assert parse_commons_response(payload) == ()


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


def test_metadata_filter_rejects_restrictions_and_preserves_required_credit() -> None:
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

    assert len(records) == 1
    assert records[0].creator == "Example creator"
    assert records[0].attribution_text == (
        "Required credit line · Example creator — CC BY 4.0 — Wikimedia Commons"
    )
    assert records[0].restrictions == ""
    assert records[0].explicit_attribution == "Required credit line"


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
