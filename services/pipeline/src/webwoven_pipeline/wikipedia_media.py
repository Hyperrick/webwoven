from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .http_transport import JsonTransport, UrllibJsonTransport
from .json_values import json_object
from .media_discovery_hints import WIKIPEDIA_SITE_PRIORITY

WIKIPEDIA_MEDIA_CACHE_VERSION = 1
_GENERIC_MATCH_TOKENS = {
    "award",
    "best",
    "book",
    "city",
    "film",
    "icon",
    "logo",
    "medal",
    "prize",
    "school",
    "symbol",
    "the",
}


class WikipediaMediaError(RuntimeError):
    """Raised when Wikipedia media discovery cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class WikipediaMediaCandidate:
    file_name: str
    site: str
    article_title: str
    kind: str = "lead"

    @property
    def provenance(self) -> str:
        return f"wikipedia_{self.kind}:{self.site}:{self.article_title}"


class WikipediaMediaClient:
    """Resolve exact Wikidata sitelinks to their Wikipedia lead images."""

    def __init__(
        self,
        cache_dir: Path,
        user_agent: str,
        *,
        transport: JsonTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        max_retries: int = 6,
        timeout: float = 30.0,
        request_interval: float = 0.0,
    ) -> None:
        if not user_agent.strip() or "webwoven" not in user_agent.casefold():
            raise ValueError("user_agent must identify the Webwoven project")
        if max_retries < 0 or request_interval < 0:
            raise ValueError("Wikipedia retries and pacing cannot be negative")
        self._cache_dir = cache_dir
        self._user_agent = user_agent
        self._transport = transport or UrllibJsonTransport()
        self._sleeper = sleeper
        self._max_retries = max_retries
        self._timeout = timeout
        self._request_interval = request_interval

    def fetch_lead_candidates(
        self,
        sitelinks_by_qid: Mapping[str, Mapping[str, str]],
        *,
        entity_ids: Iterable[str] | None = None,
    ) -> dict[str, tuple[WikipediaMediaCandidate, ...]]:
        selected_ids = set(entity_ids) if entity_ids is not None else set(sitelinks_by_qid)
        candidates: dict[str, list[WikipediaMediaCandidate]] = {}
        for site in WIKIPEDIA_SITE_PRIORITY:
            qids_by_title: dict[str, list[str]] = {}
            for qid in sorted(selected_ids, key=_qid_number):
                title = sitelinks_by_qid.get(qid, {}).get(site)
                if title:
                    qids_by_title.setdefault(title, []).append(qid)
            titles = tuple(sorted(qids_by_title, key=str.casefold))
            for batch in _bounded_title_batches(site, titles):
                payload = self._fetch_batch(site, batch)
                images = lead_images_by_title(payload, batch)
                for title, file_name in images.items():
                    for qid in qids_by_title[title]:
                        candidates.setdefault(qid, []).append(
                            WikipediaMediaCandidate(file_name, site, title)
                        )
        return {
            qid: _rank_candidates(items)
            for qid, items in sorted(candidates.items(), key=lambda item: _qid_number(item[0]))
        }

    def fetch_article_candidates(
        self,
        sitelinks_by_qid: Mapping[str, Mapping[str, str]],
        labels_by_qid: Mapping[str, str],
        *,
        entity_ids: Iterable[str],
        max_sites: int = 3,
    ) -> dict[str, tuple[WikipediaMediaCandidate, ...]]:
        candidates: dict[str, list[WikipediaMediaCandidate]] = {}
        for qid in sorted(set(entity_ids), key=_qid_number):
            sitelinks = sitelinks_by_qid.get(qid, {})
            articles = [
                (site, title) for site in WIKIPEDIA_SITE_PRIORITY if (title := sitelinks.get(site))
            ][:max_sites]
            for site, title in articles:
                payload = self._fetch_article(site, title)
                candidates.setdefault(qid, []).extend(
                    WikipediaMediaCandidate(file_name, site, title, "article")
                    for file_name in article_image_names(payload)
                )
        return {
            qid: _rank_article_candidates(items, labels_by_qid.get(qid, ""))
            for qid, items in sorted(candidates.items(), key=lambda item: _qid_number(item[0]))
            if items
        }

    def _fetch_batch(self, site: str, titles: tuple[str, ...]) -> dict[str, Any]:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self._cache_dir / _cache_name(site, titles)
        if cache_path.exists():
            return _decode_object(cache_path.read_bytes(), cache_path)
        payload = self._request_with_retry(site, titles)
        payload_bytes = _canonical_bytes(payload)
        try:
            with cache_path.open("xb") as handle:
                handle.write(payload_bytes)
        except FileExistsError:
            return _decode_object(cache_path.read_bytes(), cache_path)
        return payload

    def _fetch_article(self, site: str, title: str) -> dict[str, Any]:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self._cache_dir / _article_cache_name(site, title)
        if cache_path.exists():
            return _decode_object(cache_path.read_bytes(), cache_path)
        payload = self._request_url_with_retry(_build_article_url(site, title))
        payload_bytes = _canonical_bytes(payload)
        try:
            with cache_path.open("xb") as handle:
                handle.write(payload_bytes)
        except FileExistsError:
            return _decode_object(cache_path.read_bytes(), cache_path)
        return payload

    def _request_with_retry(self, site: str, titles: tuple[str, ...]) -> dict[str, Any]:
        return self._request_url_with_retry(_build_url(site, titles))

    def _request_url_with_retry(self, url: str) -> dict[str, Any]:
        attempts = self._max_retries + 1
        for attempt in range(attempts):
            try:
                payload = self._transport.get_json(
                    url,
                    headers={"User-Agent": self._user_agent, "Accept": "application/json"},
                    timeout=self._timeout,
                )
                error_value: object = payload.get("error")
                if isinstance(error_value, Mapping):
                    error = cast(Mapping[str, Any], error_value)
                    code_value: object = error.get("code")
                    code = code_value if isinstance(code_value, str) else None
                    if code == "maxlag":
                        raise _RetryableWikipediaError("Wikipedia reported maxlag")
                    raise WikipediaMediaError(f"Wikipedia API error: {code or 'unknown'}")
                if not isinstance(payload.get("query"), Mapping):
                    raise WikipediaMediaError("Wikipedia response has no query object")
                if self._request_interval:
                    self._sleeper(self._request_interval)
                return payload
            except (HTTPError, URLError, TimeoutError, _RetryableWikipediaError) as exc:
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
                    raise WikipediaMediaError(
                        f"non-retryable Wikipedia HTTP error {http_code}"
                    ) from exc
                if attempt == attempts - 1:
                    raise WikipediaMediaError(
                        f"Wikipedia batch failed after {attempts} attempts"
                    ) from exc
                self._sleeper(min(2**attempt, 30))
        raise AssertionError("retry loop did not return or raise")


class _RetryableWikipediaError(RuntimeError):
    pass


def lead_images_by_title(
    payload: Mapping[str, Any],
    requested_titles: Iterable[str],
) -> dict[str, str]:
    query_value = payload.get("query")
    if not isinstance(query_value, Mapping):
        raise WikipediaMediaError("Wikipedia response has no query object")
    query = cast(Mapping[str, Any], query_value)
    aliases: dict[str, str] = {}
    for key in ("normalized", "redirects", "converted"):
        values_value: object = query.get(key)
        if not isinstance(values_value, list):
            continue
        for value_item in cast(list[object], values_value):
            if not isinstance(value_item, Mapping):
                continue
            value = cast(Mapping[str, Any], value_item)
            source: object = value.get("from")
            target: object = value.get("to")
            if isinstance(source, str) and isinstance(target, str):
                aliases[source] = target

    pages_value = query.get("pages")
    pages = cast(list[object], pages_value) if isinstance(pages_value, list) else []
    image_by_page: dict[str, str] = {}
    for page_value in pages:
        if not isinstance(page_value, Mapping):
            continue
        page = cast(Mapping[str, Any], page_value)
        if page.get("missing") is True:
            continue
        title: object = page.get("title")
        file_name: object = page.get("pageimage")
        if isinstance(title, str) and isinstance(file_name, str) and file_name.strip():
            image_by_page[title] = file_name.removeprefix("File:").replace("_", " ").strip()

    images: dict[str, str] = {}
    for requested in requested_titles:
        resolved = requested
        for _ in range(10):
            target = aliases.get(resolved)
            if target is None or target == resolved:
                break
            resolved = target
        file_name = image_by_page.get(resolved) or image_by_page.get(resolved.replace("_", " "))
        if file_name:
            images[requested] = file_name
    return images


def article_image_names(payload: Mapping[str, Any]) -> tuple[str, ...]:
    query_value: object = payload.get("query")
    query = json_object(query_value)
    pages_value: object = query.get("pages")
    pages = cast(list[object], pages_value) if isinstance(pages_value, list) else []
    names: list[str] = []
    for page_value in pages:
        page = json_object(page_value)
        images_value: object = page.get("images")
        if not isinstance(images_value, list):
            continue
        for image_value in cast(list[object], images_value):
            image = json_object(image_value)
            title: object = image.get("title")
            if not isinstance(title, str) or not title.startswith("File:"):
                continue
            file_name = title.removeprefix("File:").replace("_", " ").strip()
            if _article_file_allowed(file_name):
                names.append(file_name)
    return tuple(dict.fromkeys(names))


def _rank_candidates(
    candidates: Iterable[WikipediaMediaCandidate],
) -> tuple[WikipediaMediaCandidate, ...]:
    values = tuple(candidates)
    frequency = Counter(candidate.file_name for candidate in values)
    site_priority = {site: index for index, site in enumerate(WIKIPEDIA_SITE_PRIORITY)}
    ranked = sorted(
        values,
        key=lambda candidate: (
            -frequency[candidate.file_name],
            site_priority[candidate.site],
            candidate.file_name.casefold(),
        ),
    )
    selected: list[WikipediaMediaCandidate] = []
    seen_files: set[str] = set()
    for candidate in ranked:
        if candidate.file_name not in seen_files:
            selected.append(candidate)
            seen_files.add(candidate.file_name)
    return tuple(selected)


def _rank_article_candidates(
    candidates: Iterable[WikipediaMediaCandidate],
    entity_label: str,
) -> tuple[WikipediaMediaCandidate, ...]:
    label_tokens = _meaningful_tokens(entity_label)
    values = tuple(
        candidate
        for candidate in candidates
        if label_tokens & _meaningful_tokens(candidate.file_name.rpartition(".")[0])
    )
    frequency = Counter(candidate.file_name for candidate in values)
    site_priority = {site: index for index, site in enumerate(WIKIPEDIA_SITE_PRIORITY)}
    ranked = sorted(
        values,
        key=lambda candidate: (
            -len(label_tokens & _meaningful_tokens(candidate.file_name.rpartition(".")[0])),
            -frequency[candidate.file_name],
            site_priority[candidate.site],
            candidate.file_name.casefold(),
        ),
    )
    selected: list[WikipediaMediaCandidate] = []
    seen_files: set[str] = set()
    for candidate in ranked:
        if candidate.file_name not in seen_files:
            selected.append(candidate)
            seen_files.add(candidate.file_name)
    return tuple(selected)


def _build_url(site: str, titles: tuple[str, ...]) -> str:
    if site not in WIKIPEDIA_SITE_PRIORITY:
        raise ValueError(f"unsupported Wikipedia site: {site}")
    language = site.removesuffix("wiki")
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "pageimages",
        "piprop": "name",
        "redirects": "1",
        "converttitles": "1",
        "titles": "|".join(titles),
        "maxlag": "5",
    }
    return f"https://{language}.wikipedia.org/w/api.php?{urlencode(params)}"


def _build_article_url(site: str, title: str) -> str:
    if site not in WIKIPEDIA_SITE_PRIORITY:
        raise ValueError(f"unsupported Wikipedia site: {site}")
    language = site.removesuffix("wiki")
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "images",
        "imlimit": "100",
        "redirects": "1",
        "converttitles": "1",
        "titles": title,
        "maxlag": "5",
    }
    return f"https://{language}.wikipedia.org/w/api.php?{urlencode(params)}"


def _cache_name(site: str, titles: tuple[str, ...]) -> str:
    digest = hashlib.sha256("\n".join(titles).encode()).hexdigest()[:20]
    return f"wikipedia-leads-v{WIKIPEDIA_MEDIA_CACHE_VERSION}-{site}-{len(titles)}-{digest}.json"


def _article_cache_name(site: str, title: str) -> str:
    digest = hashlib.sha256(title.encode()).hexdigest()[:24]
    return f"wikipedia-article-images-v{WIKIPEDIA_MEDIA_CACHE_VERSION}-{site}-{digest}.json"


def _article_file_allowed(file_name: str) -> bool:
    lowered = file_name.casefold()
    if not lowered.endswith((".gif", ".jpeg", ".jpg", ".png", ".svg", ".tif", ".tiff", ".webp")):
        return False
    return not lowered.startswith(
        (
            "ambox",
            "commons-logo",
            "color icon white",
            "edit-clear",
            "folder hexagonal icon",
            "oojs ui icon",
            "pd-icon",
            "question book",
            "symbol category class",
            "symbol portal class",
            "symbol support vote",
            "wikidata-logo",
            "wikipedia-logo",
        )
    )


def _tokens(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    ascii_value = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return {token for token in re.findall(r"[a-z0-9]+", ascii_value) if len(token) > 2}


def _meaningful_tokens(value: str) -> set[str]:
    return _tokens(value) - _GENERIC_MATCH_TOKENS


def _bounded_title_batches(
    site: str,
    titles: tuple[str, ...],
    *,
    max_url_length: int = 1800,
    max_titles: int = 50,
) -> Iterable[tuple[str, ...]]:
    batch: list[str] = []
    for title in titles:
        candidate = (*batch, title)
        if batch and (
            len(candidate) > max_titles or len(_build_url(site, candidate)) > max_url_length
        ):
            yield tuple(batch)
            batch = [title]
        else:
            batch.append(title)
    if batch:
        yield tuple(batch)


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (serialized + "\n").encode()


def _decode_object(payload: bytes, path: Path) -> dict[str, Any]:
    value: object = json.loads(payload)
    if not isinstance(value, dict):
        raise WikipediaMediaError(f"cached Wikipedia batch {path} is not an object")
    return cast(dict[str, Any], value)


def _qid_number(value: str) -> int:
    if len(value) < 2 or value[0] != "Q" or not value[1:].isdigit():
        raise ValueError(f"invalid QID: {value}")
    return int(value[1:])
