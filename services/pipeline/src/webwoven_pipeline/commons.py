from __future__ import annotations

import html
import re
import time
from collections.abc import Callable, Iterable, Mapping
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse

from .http_transport import JsonTransport, UrllibJsonTransport
from .media_licenses import (
    LICENSE_SPECS,
    SUPPORTED_LICENSE_IDS,
    license_id_from_short_name,
    license_spec,
)
from .models import MediaRecord

COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
ALLOWED_LICENSES = SUPPORTED_LICENSE_IDS
CANONICAL_LICENSE_URLS = {
    identifier: spec.canonical_url for identifier, spec in LICENSE_SPECS.items()
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
        sleeper: Callable[[float], None] = time.sleep,
        max_retries: int = 6,
        request_interval: float = 0.0,
    ) -> None:
        if not user_agent.strip() or "webwoven" not in user_agent.casefold():
            raise ValueError("user_agent must identify the Webwoven project")
        if max_retries < 0 or request_interval < 0:
            raise ValueError("Commons metadata retries and pacing cannot be negative")
        self._user_agent = user_agent
        self._transport = transport or UrllibJsonTransport()
        self._timeout = timeout
        self._sleeper = sleeper
        self._max_retries = max_retries
        self._request_interval = request_interval

    def fetch_metadata(self, file_names: Iterable[str]) -> dict[str, MediaRecord]:
        normalized = tuple(sorted({_normalize_file_name(name) for name in file_names}))
        records: dict[str, MediaRecord] = {}
        for names in _bounded_file_batches(normalized):
            for record in self._fetch_batch_records(names):
                records[record.file_name] = record
        return dict(sorted(records.items()))

    def _fetch_batch_records(self, names: tuple[str, ...]) -> tuple[MediaRecord, ...]:
        try:
            return parse_commons_response(self._request_with_retry(names))
        except CommonsFileNameError:
            if len(names) == 1:
                return ()
            midpoint = len(names) // 2
            return self._fetch_batch_records(names[:midpoint]) + self._fetch_batch_records(
                names[midpoint:]
            )

    def _request_with_retry(self, names: tuple[str, ...]) -> dict[str, Any]:
        attempts = self._max_retries + 1
        for attempt in range(attempts):
            try:
                payload = self._transport.get_json(
                    _build_url(names),
                    headers={"User-Agent": self._user_agent, "Accept": "application/json"},
                    timeout=self._timeout,
                )
                error_value: object = payload.get("error")
                if isinstance(error_value, Mapping):
                    error = cast(Mapping[str, Any], error_value)
                    code_value: object = error.get("code")
                    code = code_value if isinstance(code_value, str) else None
                    if code == "maxlag":
                        raise _RetryableCommonsError("Commons reported maxlag")
                    if code in {"urlparamnormal", "badtitle", "invalidtitle"}:
                        raise CommonsFileNameError(f"Commons rejected a file title: {code}")
                    raise CommonsError(f"Commons API error: {code or 'unknown'}")
                if self._request_interval:
                    self._sleeper(self._request_interval)
                return payload
            except (HTTPError, URLError, TimeoutError, _RetryableCommonsError) as exc:
                http_code = exc.code if isinstance(exc, HTTPError) else None
                non_retryable_http = http_code is not None and http_code not in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }
                if isinstance(exc, HTTPError):
                    exc.close()
                if non_retryable_http:
                    raise CommonsError(f"non-retryable Commons HTTP error {http_code}") from exc
                if attempt == attempts - 1:
                    raise CommonsError(
                        f"Commons metadata failed after {attempts} attempts"
                    ) from exc
                self._sleeper(min(2**attempt, 30))
        raise AssertionError("retry loop did not return or raise")


class _RetryableCommonsError(RuntimeError):
    pass


class CommonsFileNameError(CommonsError):
    """Raised when Commons refuses one or more requested file titles."""


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
    license_id = license_id_from_short_name(_metadata_value(metadata, "LicenseShortName"))
    spec = license_spec(license_id or "")
    if license_id is None or spec is None:
        return None

    creator = _plain_text(_metadata_value(metadata, "Artist"))
    license_url = _metadata_value(metadata, "LicenseUrl").strip()
    restrictions = _plain_text(_metadata_value(metadata, "Restrictions"))
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
    if spec.requires_creator and (not creator or not matches_license_url(license_url, license_id)):
        return None
    if not spec.requires_creator:
        creator = creator or "Unknown creator"
    license_url = _normalized_license_url(license_url, license_id)

    explicit_attribution = _plain_text(_metadata_value(metadata, "Attribution"))
    attribution_credit = creator
    if explicit_attribution:
        attribution_credit = (
            explicit_attribution
            if creator.casefold() in explicit_attribution.casefold()
            else f"{explicit_attribution} · {creator}"
        )

    return MediaRecord(
        file_name=title.removeprefix("File:"),
        original_url=original_url,
        derivative_url=derivative_url,
        source_url=source_url,
        license_id=license_id,
        creator=creator,
        license_url=license_url,
        attribution_text=f"{attribution_credit} — {spec.label} — Wikimedia Commons",
        restrictions=restrictions,
        explicit_attribution=explicit_attribution,
    )


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
        "iiurlwidth": "800",
        "maxlag": "5",
    }
    return f"{COMMONS_API_URL}?{urlencode(params)}"


def _normalize_file_name(value: str) -> str:
    name = value.removeprefix("File:").strip().replace("_", " ")
    if not name:
        raise ValueError("Commons file name cannot be empty")
    return name


def _bounded_file_batches(
    names: tuple[str, ...],
    *,
    max_url_length: int = 1800,
    max_files: int = 50,
) -> Iterable[tuple[str, ...]]:
    batch: list[str] = []
    for name in names:
        candidate = (*batch, name)
        if batch and (len(candidate) > max_files or len(_build_url(candidate)) > max_url_length):
            yield tuple(batch)
            batch = [name]
        else:
            batch.append(name)
    if batch:
        yield tuple(batch)


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _wikimedia_url(value: str, expected_host: str) -> str | None:
    parsed = urlparse(value)
    return value if parsed.scheme == "https" and parsed.hostname == expected_host else None


def matches_license_url(value: str, license_id: str) -> bool:
    parsed = urlparse(value)
    expected = urlparse(CANONICAL_LICENSE_URLS[license_id])
    actual_path = parsed.path.rstrip("/")
    expected_path = expected.path.rstrip("/")
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname == expected.hostname
        and (actual_path == expected_path or actual_path.startswith(f"{expected_path}/"))
        and not parsed.query
        and not parsed.fragment
    )


def _normalized_license_url(value: str, license_id: str) -> str:
    if not value or not matches_license_url(value, license_id):
        return CANONICAL_LICENSE_URLS[license_id]
    parsed = urlparse(value)
    return parsed._replace(scheme="https").geturl()


def _as_mapping(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return cast(Mapping[str, Any], value)
