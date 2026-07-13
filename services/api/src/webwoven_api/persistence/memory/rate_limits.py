"""Process-local rate limiter for tests and single-process development."""

import asyncio
from time import time

from webwoven_api.security.rate_limits import RateLimitDecision


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._counts: dict[tuple[str, str, int], int] = {}
        self._concurrent: dict[tuple[str, str], int] = {}
        self._lock = asyncio.Lock()

    async def check(
        self,
        *,
        scope: str,
        identity: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        now = int(time())
        bucket = now // window_seconds
        key = (scope, identity, bucket)
        async with self._lock:
            count = self._counts.get(key, 0) + 1
            self._counts[key] = count
            if len(self._counts) > 1000:
                self._counts = {
                    item_key: value
                    for item_key, value in self._counts.items()
                    if item_key[2] >= bucket - 1
                }
        retry_after = window_seconds - (now % window_seconds)
        return RateLimitDecision(
            allowed=count <= limit,
            remaining=max(limit - count, 0),
            retry_after_seconds=max(retry_after, 1),
        )

    async def acquire_concurrent(
        self,
        *,
        scope: str,
        identity: str,
        limit: int,
        ttl_seconds: int,
    ) -> bool:
        del ttl_seconds
        key = (scope, identity)
        async with self._lock:
            current = self._concurrent.get(key, 0)
            if current >= limit:
                return False
            self._concurrent[key] = current + 1
        return True

    async def release_concurrent(self, *, scope: str, identity: str) -> None:
        key = (scope, identity)
        async with self._lock:
            current = self._concurrent.get(key, 0)
            if current <= 1:
                self._concurrent.pop(key, None)
            else:
                self._concurrent[key] = current - 1
