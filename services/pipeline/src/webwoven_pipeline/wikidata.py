from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .http_transport import JsonTransport, UrllibJsonTransport

WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"


class WikidataError(RuntimeError):
    """Raised after a Wikidata batch cannot be acquired safely."""


@dataclass(frozen=True, slots=True)
class WikidataBatch:
    qids: tuple[str, ...]
    cache_path: Path
    sha256: str
    payload: dict[str, Any]


class WikidataClient:
    """Batched, retrying and immutable-cache adapter for wbgetentities."""

    def __init__(
        self,
        cache_dir: Path,
        user_agent: str,
        *,
        transport: JsonTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        max_retries: int = 8,
        timeout: float = 30.0,
        max_lag: int = 5,
        request_interval: float = 0.0,
    ) -> None:
        if not user_agent.strip() or "webwoven" not in user_agent.casefold():
            raise ValueError("user_agent must identify the Webwoven project")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if not 1 <= max_lag <= 120:
            raise ValueError("max_lag must be between 1 and 120 seconds")
        if request_interval < 0:
            raise ValueError("request_interval cannot be negative")
        self._cache_dir = cache_dir
        self._user_agent = user_agent
        self._transport = transport or UrllibJsonTransport()
        self._sleeper = sleeper
        self._max_retries = max_retries
        self._timeout = timeout
        self._max_lag = max_lag
        self._request_interval = request_interval

    def fetch_entities(self, qids: Iterable[str]) -> tuple[WikidataBatch, ...]:
        unique = tuple(sorted(set(qids), key=_qid_number))
        if any(not _is_qid(qid) for qid in unique):
            raise ValueError("all entity IDs must be Wikidata QIDs")
        return tuple(self._fetch_batch(batch) for batch in _chunked(unique, 50))

    def _fetch_batch(self, qids: tuple[str, ...]) -> WikidataBatch:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self._cache_dir / _cache_name(qids)
        if cache_path.exists():
            payload_bytes = cache_path.read_bytes()
            payload = _decode_object(payload_bytes, cache_path)
            return WikidataBatch(
                qids,
                cache_path,
                hashlib.sha256(payload_bytes).hexdigest(),
                payload,
            )

        payload = self._request_with_retry(qids)
        payload_bytes = _canonical_bytes(payload)
        try:
            with cache_path.open("xb") as handle:
                handle.write(payload_bytes)
        except FileExistsError:
            payload_bytes = cache_path.read_bytes()
            payload = _decode_object(payload_bytes, cache_path)
        return WikidataBatch(qids, cache_path, hashlib.sha256(payload_bytes).hexdigest(), payload)

    def _request_with_retry(self, qids: tuple[str, ...]) -> dict[str, Any]:
        url = _build_url(qids, self._max_lag)
        attempts = self._max_retries + 1
        for attempt in range(attempts):
            try:
                payload = self._transport.get_json(
                    url,
                    headers={"User-Agent": self._user_agent, "Accept": "application/json"},
                    timeout=self._timeout,
                )
                error = payload.get("error")
                if isinstance(error, Mapping):
                    error_object = cast(Mapping[str, Any], error)
                    code = error_object.get("code")
                    if code == "maxlag":
                        raise _RetryableWikidataError("Wikidata reported maxlag")
                    raise WikidataError(f"Wikidata API error: {code or 'unknown'}")
                if not isinstance(payload.get("entities"), dict):
                    raise WikidataError("Wikidata response has no entities object")
                if self._request_interval:
                    self._sleeper(self._request_interval)
                return payload
            except (HTTPError, URLError, TimeoutError, _RetryableWikidataError) as exc:
                if isinstance(exc, HTTPError) and exc.code not in {429, 500, 502, 503, 504}:
                    raise WikidataError(f"non-retryable Wikidata HTTP error {exc.code}") from exc
                if attempt == attempts - 1:
                    raise WikidataError(f"Wikidata batch failed after {attempts} attempts") from exc
                self._sleeper(min(2**attempt, 30))
        raise AssertionError("retry loop did not return or raise")


class _RetryableWikidataError(RuntimeError):
    pass


def entities_from_batches(batches: Iterable[WikidataBatch]) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for batch in batches:
        value = batch.payload["entities"]
        if not isinstance(value, dict):
            raise WikidataError("cached batch has no valid entities object")
        entity_map = cast(dict[str, Any], value)
        for qid, entity in entity_map.items():
            if _is_qid(qid) and isinstance(entity, dict):
                entities[qid] = cast(dict[str, Any], entity)
    return dict(sorted(entities.items(), key=lambda item: _qid_number(item[0])))


def _build_url(qids: tuple[str, ...], max_lag: int) -> str:
    params = {
        "action": "wbgetentities",
        "format": "json",
        "formatversion": "2",
        "ids": "|".join(qids),
        "props": "labels|descriptions|aliases|claims",
        "languages": "en",
        "languagefallback": "1",
        "maxlag": str(max_lag),
    }
    return f"{WIKIDATA_API_URL}?{urlencode(params)}"


def _cache_name(qids: tuple[str, ...]) -> str:
    digest = hashlib.sha256("\n".join(qids).encode()).hexdigest()[:20]
    return f"wbgetentities-{qids[0]}-{len(qids)}-{digest}.json"


def _chunked(values: tuple[str, ...], size: int) -> Iterable[tuple[str, ...]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (serialized + "\n").encode()


def _decode_object(payload: bytes, path: Path) -> dict[str, Any]:
    value: object = json.loads(payload)
    if not isinstance(value, dict):
        raise WikidataError(f"cached batch {path} is not an object")
    return cast(dict[str, Any], value)


def _is_qid(value: str) -> bool:
    return len(value) > 1 and value[0] == "Q" and value[1:].isdigit()


def _qid_number(value: str) -> int:
    if not _is_qid(value):
        raise ValueError(f"invalid QID: {value}")
    return int(value[1:])
