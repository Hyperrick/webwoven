from __future__ import annotations

from webwoven_pipeline.commons import parse_commons_response


def _page(title: str, license_name: str, *, artist: str = "Ada", license_url: str = "url") -> dict:
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
