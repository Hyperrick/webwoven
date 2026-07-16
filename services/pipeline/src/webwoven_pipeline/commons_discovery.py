from __future__ import annotations

import hashlib
import json
import re
import time
import unicodedata
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .commons import COMMONS_API_URL
from .http_transport import JsonTransport, UrllibJsonTransport
from .json_values import json_object
from .media_context import MediaContextHint

COMMONS_DISCOVERY_CACHE_VERSION = 1
_GENERIC_LABEL_TOKENS = {
    "and",
    "art",
    "association",
    "award",
    "best",
    "city",
    "committee",
    "foundation",
    "for",
    "global",
    "honorary",
    "international",
    "medal",
    "member",
    "network",
    "prize",
    "society",
    "the",
}
_REVIEWED_SEARCH_EXCLUSIONS = {
    "Berwickshire Landscape , Something's gotta give - geograph.org.uk - 8064866.jpg",
}


class CommonsDiscoveryError(RuntimeError):
    """Raised when exact or semantic Commons discovery cannot finish safely."""


@dataclass(frozen=True, slots=True)
class CommonsDiscoveryCandidate:
    file_name: str
    provenance: str


class CommonsDiscoveryClient:
    """Discover entity media from exact categories and Commons MediaSearch."""

    def __init__(
        self,
        cache_dir: Path,
        user_agent: str,
        *,
        transport: JsonTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        max_retries: int = 6,
        timeout: float = 30.0,
        request_interval: float = 0.1,
    ) -> None:
        if not user_agent.strip() or "webwoven" not in user_agent.casefold():
            raise ValueError("user_agent must identify the Webwoven project")
        if max_retries < 0 or request_interval < 0:
            raise ValueError("Commons discovery retries and pacing cannot be negative")
        self._cache_dir = cache_dir
        self._user_agent = user_agent
        self._transport = transport or UrllibJsonTransport()
        self._sleeper = sleeper
        self._max_retries = max_retries
        self._timeout = timeout
        self._request_interval = request_interval

    def fetch_category_candidates(
        self,
        entity_ids: Iterable[str],
        categories_by_qid: Mapping[str, str],
        labels_by_qid: Mapping[str, str],
    ) -> dict[str, tuple[CommonsDiscoveryCandidate, ...]]:
        results: dict[str, tuple[CommonsDiscoveryCandidate, ...]] = {}
        for qid in sorted(set(entity_ids), key=_qid_number):
            category = categories_by_qid.get(qid)
            if not category:
                continue
            payload = self._fetch(
                "category",
                f"{qid}:{category}",
                _category_url(category),
            )
            titles = _category_titles(payload)
            candidates = _candidates(
                titles,
                labels_by_qid.get(qid, ""),
                f"commons_category:{category}",
            )
            if candidates:
                results[qid] = candidates
        return results

    def fetch_depicts_candidates(
        self,
        entity_ids: Iterable[str],
        labels_by_qid: Mapping[str, str],
    ) -> dict[str, tuple[CommonsDiscoveryCandidate, ...]]:
        results: dict[str, tuple[CommonsDiscoveryCandidate, ...]] = {}
        for qid in sorted(set(entity_ids), key=_qid_number):
            query = f"depicts:{qid} filetype:bitmap"
            payload = self._fetch("depicts", qid, _search_url(query, limit=20))
            candidates = _candidates(
                _search_titles(payload),
                labels_by_qid.get(qid, ""),
                f"commons_depicts:{qid}",
            )
            if candidates:
                results[qid] = candidates
        return results

    def fetch_label_candidates(
        self,
        entity_ids: Iterable[str],
        labels_by_qid: Mapping[str, str],
    ) -> dict[str, tuple[CommonsDiscoveryCandidate, ...]]:
        results: dict[str, tuple[CommonsDiscoveryCandidate, ...]] = {}
        for qid in sorted(set(entity_ids), key=_qid_number):
            label = labels_by_qid.get(qid, "").strip()
            if not label:
                continue
            payload = self._fetch(
                "label",
                f"{qid}:{label}",
                _search_url(f'"{label}" filetype:bitmap', limit=20),
            )
            candidates = _candidates(
                _search_titles(payload),
                label,
                f"commons_search:{label}",
                require_label_overlap=True,
                require_exact_label=True,
            )
            if candidates:
                results[qid] = candidates
        return results

    def fetch_broad_candidates(
        self,
        entity_ids: Iterable[str],
        labels_by_qid: Mapping[str, str],
    ) -> dict[str, tuple[CommonsDiscoveryCandidate, ...]]:
        results: dict[str, tuple[CommonsDiscoveryCandidate, ...]] = {}
        for qid in sorted(set(entity_ids), key=_qid_number):
            label = labels_by_qid.get(qid, "").strip()
            if not label:
                continue
            payload = self._fetch(
                "broad",
                f"{qid}:{label}",
                _search_url(f"{label} filetype:bitmap", limit=30),
            )
            candidates = _candidates(
                _search_titles(payload),
                label,
                f"commons_media_search:{label}",
                require_label_overlap=True,
            )
            if candidates:
                results[qid] = candidates
        return results

    def fetch_context_candidates(
        self,
        entity_ids: Iterable[str],
        context_by_qid: Mapping[str, tuple[MediaContextHint, ...]],
    ) -> dict[str, tuple[CommonsDiscoveryCandidate, ...]]:
        results: dict[str, tuple[CommonsDiscoveryCandidate, ...]] = {}
        for qid in sorted(set(entity_ids), key=_qid_number):
            candidates: list[CommonsDiscoveryCandidate] = []
            for hint in context_by_qid.get(qid, ()):
                payload = self._fetch(
                    "context",
                    f"{qid}:{hint.entity_id}:{hint.label}",
                    _search_url(f"{hint.label} filetype:bitmap", limit=30),
                )
                candidates.extend(
                    _candidates(
                        _search_titles(payload),
                        hint.label,
                        (f"commons_context:{hint.relation_key}:{hint.entity_id}:{hint.label}"),
                        require_label_overlap=True,
                    )
                )
            if candidates:
                results[qid] = _unique_candidates(candidates)
        return results

    def _fetch(self, strategy: str, key: str, url: str) -> dict[str, Any]:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self._cache_dir / _cache_name(strategy, key)
        if cache_path.exists():
            return _decode_object(cache_path.read_bytes(), cache_path)
        payload = self._request_with_retry(url)
        payload_bytes = _canonical_bytes(payload)
        try:
            with cache_path.open("xb") as handle:
                handle.write(payload_bytes)
        except FileExistsError:
            return _decode_object(cache_path.read_bytes(), cache_path)
        return payload

    def _request_with_retry(self, url: str) -> dict[str, Any]:
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
                        raise _RetryableCommonsDiscoveryError("Commons reported maxlag")
                    raise CommonsDiscoveryError(f"Commons API error: {code or 'unknown'}")
                if not isinstance(payload.get("query"), Mapping):
                    raise CommonsDiscoveryError("Commons response has no query object")
                if self._request_interval:
                    self._sleeper(self._request_interval)
                return payload
            except (HTTPError, URLError, TimeoutError, _RetryableCommonsDiscoveryError) as exc:
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
                    raise CommonsDiscoveryError(
                        f"non-retryable Commons HTTP error {http_code}"
                    ) from exc
                if attempt == attempts - 1:
                    raise CommonsDiscoveryError(
                        f"Commons discovery failed after {attempts} attempts"
                    ) from exc
                self._sleeper(min(2**attempt, 30))
        raise AssertionError("retry loop did not return or raise")


class _RetryableCommonsDiscoveryError(RuntimeError):
    pass


def _category_url(category: str) -> str:
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmnamespace": "6",
        "cmtype": "file",
        "cmlimit": "20",
        "maxlag": "5",
    }
    return f"{COMMONS_API_URL}?{urlencode(params)}"


def _search_url(query: str, *, limit: int) -> str:
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "list": "search",
        "srnamespace": "6",
        "srlimit": str(limit),
        "srsearch": query,
        "maxlag": "5",
    }
    return f"{COMMONS_API_URL}?{urlencode(params)}"


def _category_titles(payload: Mapping[str, Any]) -> tuple[str, ...]:
    query_value: object = payload.get("query")
    query = json_object(query_value)
    values: object = query.get("categorymembers")
    return _titles(values)


def _search_titles(payload: Mapping[str, Any]) -> tuple[str, ...]:
    query_value: object = payload.get("query")
    query = json_object(query_value)
    values: object = query.get("search")
    return _titles(values)


def _titles(values: object) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()
    result: list[str] = []
    for item_value in cast(list[object], values):
        item = json_object(item_value)
        title: object = item.get("title")
        if isinstance(title, str) and title.startswith("File:"):
            result.append(title.removeprefix("File:").replace("_", " ").strip())
    return tuple(result)


def _candidates(
    titles: Iterable[str],
    entity_label: str,
    provenance: str,
    *,
    require_label_overlap: bool = False,
    require_exact_label: bool = False,
) -> tuple[CommonsDiscoveryCandidate, ...]:
    unique = set(titles) - _REVIEWED_SEARCH_EXCLUSIONS
    if require_exact_label:
        unique = {title for title in unique if _has_exact_label_phrase(title, entity_label)}
    if require_label_overlap:
        unique = {title for title in unique if _has_label_overlap(title, entity_label)}
    return tuple(
        CommonsDiscoveryCandidate(title, provenance)
        for title in sorted(unique, key=lambda title: _title_score(title, entity_label))
    )


def _unique_candidates(
    candidates: Iterable[CommonsDiscoveryCandidate],
) -> tuple[CommonsDiscoveryCandidate, ...]:
    unique: dict[str, CommonsDiscoveryCandidate] = {}
    for candidate in candidates:
        unique.setdefault(candidate.file_name, candidate)
    return tuple(unique.values())


def _title_score(file_name: str, entity_label: str) -> tuple[float, int, str]:
    label_tokens = _tokens(entity_label)
    file_tokens = _tokens(file_name.rpartition(".")[0])
    overlap = len(label_tokens & file_tokens) / max(len(label_tokens), 1)
    generic_penalty = sum(
        token in file_tokens for token in {"icon", "logo", "symbol", "placeholder", "question"}
    )
    return (-overlap, generic_penalty, file_name.casefold())


def _tokens(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    ascii_value = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return {token for token in re.findall(r"[a-z0-9]+", ascii_value) if len(token) > 2}


def _has_label_overlap(file_name: str, entity_label: str) -> bool:
    label_tokens = {
        token
        for token in _tokens(entity_label)
        if token not in _GENERIC_LABEL_TOKENS and token.isalpha()
    }
    file_tokens = {
        token
        for token in _tokens(file_name.rpartition(".")[0])
        if token not in _GENERIC_LABEL_TOKENS and token.isalpha()
    }
    return bool(label_tokens & file_tokens)


def _has_exact_label_phrase(file_name: str, entity_label: str) -> bool:
    def phrase(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).casefold()
        ascii_value = "".join(
            character for character in normalized if not unicodedata.combining(character)
        )
        return " ".join(re.findall(r"[a-z0-9]+", ascii_value))

    return phrase(entity_label) in phrase(file_name.rpartition(".")[0])


def _cache_name(strategy: str, key: str) -> str:
    digest = hashlib.sha256(key.encode()).hexdigest()[:24]
    return f"commons-discovery-v{COMMONS_DISCOVERY_CACHE_VERSION}-{strategy}-{digest}.json"


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (serialized + "\n").encode()


def _decode_object(payload: bytes, path: Path) -> dict[str, Any]:
    value: object = json.loads(payload)
    if not isinstance(value, dict):
        raise CommonsDiscoveryError(f"cached Commons discovery {path} is not an object")
    return cast(dict[str, Any], value)


def _qid_number(value: str) -> int:
    if len(value) < 2 or value[0] != "Q" or not value[1:].isdigit():
        raise ValueError(f"invalid QID: {value}")
    return int(value[1:])
