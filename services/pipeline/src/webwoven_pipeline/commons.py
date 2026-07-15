from __future__ import annotations

import html
import re
from collections.abc import Iterable, Mapping
from typing import Any, cast
from urllib.parse import urlencode, urlparse

from .http_transport import JsonTransport, UrllibJsonTransport
from .models import MediaRecord

COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
ALLOWED_LICENSES = frozenset({"PUBLIC_DOMAIN", "CC0_1_0", "CC_BY_4_0"})
CANONICAL_LICENSE_URLS = {
    "PUBLIC_DOMAIN": "https://creativecommons.org/publicdomain/mark/1.0/",
    "CC0_1_0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC_BY_4_0": "https://creativecommons.org/licenses/by/4.0/",
}


class CommonsError(RuntimeError):
    """Raised when Wikimedia Commons metadata is incomplete or malformed."""


class CommonsClient:
    """Offline-build adapter for Commons image and attribution metadata."""

    def __init__(
        self,
        user_agent: str,
        *,
        transport: JsonTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        if not user_agent.strip() or "webwoven" not in user_agent.casefold():
            raise ValueError("user_agent must identify the Webwoven project")
        self._user_agent = user_agent
        self._transport = transport or UrllibJsonTransport()
        self._timeout = timeout

    def fetch_metadata(self, file_names: Iterable[str]) -> dict[str, MediaRecord]:
        normalized = tuple(sorted({_normalize_file_name(name) for name in file_names}))
        records: dict[str, MediaRecord] = {}
        for names in _chunked(normalized, 50):
            payload = self._transport.get_json(
                _build_url(names),
                headers={"User-Agent": self._user_agent, "Accept": "application/json"},
                timeout=self._timeout,
            )
            for record in parse_commons_response(payload):
                records[record.file_name] = record
        return dict(sorted(records.items()))


def parse_commons_response(payload: Mapping[str, Any]) -> tuple[MediaRecord, ...]:
    query_value = payload.get("query")
    query = _as_mapping(query_value)
    pages_value = query.get("pages")
    pages = cast(list[Any], pages_value) if isinstance(pages_value, list) else None
    if not isinstance(pages, list):
        raise CommonsError("Commons response has no formatversion=2 pages list")

    records: list[MediaRecord] = []
    for page in pages:
        if not isinstance(page, Mapping):
            continue
        page_object = cast(Mapping[str, Any], page)
        if page_object.get("missing") is True:
            continue
        title = page_object.get("title")
        image_info_value = page_object.get("imageinfo")
        image_info = (
            cast(list[Any], image_info_value) if isinstance(image_info_value, list) else None
        )
        if not isinstance(title, str) or not isinstance(image_info, list) or not image_info:
            continue
        info_value = image_info[0]
        if not isinstance(info_value, Mapping):
            continue
        info = cast(Mapping[str, Any], info_value)
        record = _parse_record(title, info)
        if record is not None:
            records.append(record)
    return tuple(sorted(records, key=lambda record: record.file_name))


def _parse_record(title: str, info: Mapping[str, Any]) -> MediaRecord | None:
    metadata_value = info.get("extmetadata")
    if not isinstance(metadata_value, Mapping):
        return None
    metadata = cast(Mapping[str, Any], metadata_value)
    license_id = _license_id(_metadata_value(metadata, "LicenseShortName"))
    if license_id not in ALLOWED_LICENSES:
        return None

    creator = _plain_text(_metadata_value(metadata, "Artist"))
    license_url = _metadata_value(metadata, "LicenseUrl").strip()
    restrictions = _plain_text(_metadata_value(metadata, "Restrictions"))
    if restrictions:
        return None
    original_url = _wikimedia_url(_string(info.get("url")), "upload.wikimedia.org")
    derivative_url = _wikimedia_url(
        _string(info.get("thumburl")) or (original_url or ""),
        "upload.wikimedia.org",
    )
    source_url = _wikimedia_url(
        _string(info.get("descriptionurl")),
        "commons.wikimedia.org",
    )
    if original_url is None or derivative_url is None or source_url is None:
        return None
    if license_id == "CC_BY_4_0" and (
        not creator or not _matches_license_url(license_url, license_id)
    ):
        return None
    if license_id in {"PUBLIC_DOMAIN", "CC0_1_0"}:
        creator = creator or "Unknown creator"
    license_url = CANONICAL_LICENSE_URLS[license_id]

    explicit_attribution = _plain_text(_metadata_value(metadata, "Attribution"))
    attribution_credit = creator
    if explicit_attribution:
        attribution_credit = (
            explicit_attribution
            if creator.casefold() in explicit_attribution.casefold()
            else f"{explicit_attribution} · {creator}"
        )

    readable_license = {
        "PUBLIC_DOMAIN": "Public Domain",
        "CC0_1_0": "CC0 1.0",
        "CC_BY_4_0": "CC BY 4.0",
    }[license_id]
    return MediaRecord(
        file_name=title.removeprefix("File:"),
        original_url=original_url,
        derivative_url=derivative_url,
        source_url=source_url,
        license_id=license_id,
        creator=creator,
        license_url=license_url,
        attribution_text=f"{attribution_credit} — {readable_license} — Wikimedia Commons",
        restrictions=restrictions,
        explicit_attribution=explicit_attribution,
    )


def _license_id(raw: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", raw.casefold()).strip()
    if normalized in {"public domain", "pd"}:
        return "PUBLIC_DOMAIN"
    if normalized in {"cc0", "cc0 1 0"}:
        return "CC0_1_0"
    if normalized in {"cc by 4 0", "cc by 4.0"}:
        return "CC_BY_4_0"
    return "UNSUPPORTED"


def _metadata_value(metadata: Mapping[str, Any], key: str) -> str:
    item_value = metadata.get(key)
    item = _as_mapping(item_value)
    value = item.get("value")
    return value if isinstance(value, str) else ""


def _plain_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(without_tags).split())


def _build_url(names: tuple[str, ...]) -> str:
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "imageinfo",
        "titles": "|".join(f"File:{name}" for name in names),
        "iiprop": "url|extmetadata",
        "iiurlwidth": "1200",
        "maxlag": "5",
    }
    return f"{COMMONS_API_URL}?{urlencode(params)}"


def _normalize_file_name(value: str) -> str:
    name = value.removeprefix("File:").strip().replace("_", " ")
    if not name:
        raise ValueError("Commons file name cannot be empty")
    return name


def _chunked(values: tuple[str, ...], size: int) -> Iterable[tuple[str, ...]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _wikimedia_url(value: str, expected_host: str) -> str | None:
    parsed = urlparse(value)
    return value if parsed.scheme == "https" and parsed.hostname == expected_host else None


def _matches_license_url(value: str, license_id: str) -> bool:
    parsed = urlparse(value)
    expected = urlparse(CANONICAL_LICENSE_URLS[license_id])
    return (
        parsed.scheme == "https"
        and parsed.hostname == expected.hostname
        and parsed.path.rstrip("/") == expected.path.rstrip("/")
        and not parsed.query
        and not parsed.fragment
    )


def _as_mapping(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return cast(Mapping[str, Any], value)
