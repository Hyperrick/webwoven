from __future__ import annotations

import time
from collections.abc import Callable
from threading import Lock
from urllib.error import HTTPError, URLError

from .http_transport import BinaryResponse, BinaryTransport


class CommonsDownloadError(RuntimeError):
    """Raised when a Commons derivative remains unavailable after bounded retries."""


class DownloadPacer:
    """Space request starts globally while allowing response bodies to overlap."""

    def __init__(self, interval: float, sleeper: Callable[[float], None]) -> None:
        self._interval = interval
        self._sleeper = sleeper
        self._lock = Lock()
        self._next_request = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = max(0.0, self._next_request - now)
            self._next_request = max(now, self._next_request) + self._interval
        if delay:
            self._sleeper(delay)


def download_with_retry(
    transport: BinaryTransport,
    url: str,
    *,
    user_agent: str,
    sleeper: Callable[[float], None],
    interval: float,
    max_retries: int,
    max_bytes: int,
    pacer: DownloadPacer | None = None,
) -> BinaryResponse:
    attempts = max_retries + 1
    for attempt in range(attempts):
        try:
            if pacer is not None:
                pacer.wait()
            response = transport.get_bytes(
                url,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "image/webp,image/png,image/jpeg,image/gif",
                },
                timeout=45.0,
                max_bytes=max_bytes,
            )
            if interval and pacer is None:
                sleeper(interval)
            return response
        except (HTTPError, URLError, TimeoutError) as exc:
            retryable = not isinstance(exc, HTTPError) or exc.code in {
                429,
                500,
                502,
                503,
                504,
            }
            retry_delay = _retry_delay(exc, attempt)
            if isinstance(exc, HTTPError):
                exc.close()
            if not retryable or attempt == attempts - 1:
                raise CommonsDownloadError(
                    f"Commons derivative failed after {attempt + 1} attempts"
                ) from exc
            sleeper(retry_delay)
    raise AssertionError("Commons retry loop did not return or raise")


def download_with_fallback(
    transport: BinaryTransport,
    preferred_url: str,
    fallback_url: str,
    *,
    user_agent: str,
    sleeper: Callable[[float], None],
    interval: float,
    max_retries: int,
    max_bytes: int,
    pacer: DownloadPacer | None = None,
) -> tuple[str, BinaryResponse]:
    """Fall back to a bounded original when Wikimedia cannot render a thumbnail."""
    try:
        response = download_with_retry(
            transport,
            preferred_url,
            user_agent=user_agent,
            sleeper=sleeper,
            interval=interval,
            max_retries=max_retries,
            max_bytes=max_bytes,
            pacer=pacer,
        )
        return preferred_url, response
    except CommonsDownloadError:
        if fallback_url == preferred_url:
            raise
        response = download_with_retry(
            transport,
            fallback_url,
            user_agent=user_agent,
            sleeper=sleeper,
            interval=interval,
            max_retries=max_retries,
            max_bytes=max_bytes,
            pacer=pacer,
        )
        return fallback_url, response


def _retry_delay(error: OSError, attempt: int) -> float:
    header_value = error.headers.get("Retry-After") if isinstance(error, HTTPError) else None
    try:
        retry_after = float(header_value) if header_value is not None else 0.0
    except ValueError:
        retry_after = 0.0
    return min(max(2**attempt, retry_after), 30.0)
