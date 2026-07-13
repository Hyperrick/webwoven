"""Atomic fixed-window Valkey rate limits."""

from time import time

from webwoven_api.persistence.valkey.client import ValkeyClient
from webwoven_api.persistence.valkey.keys import ValkeyKeys
from webwoven_api.security.rate_limits import RateLimitDecision


class ValkeyRateLimiter:
    def __init__(self, client: ValkeyClient) -> None:
        self._client = client

    async def check(
        self,
        *,
        scope: str,
        identity: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        bucket = int(time()) // window_seconds
        key = ValkeyKeys.rate_limit(scope, identity, bucket)
        count, ttl = await self._client.fixed_window_increment(key, window_seconds)
        return RateLimitDecision(
            allowed=count <= limit,
            remaining=max(limit - count, 0),
            retry_after_seconds=max(ttl, 1),
        )

    async def acquire_concurrent(
        self,
        *,
        scope: str,
        identity: str,
        limit: int,
        ttl_seconds: int,
    ) -> bool:
        key = ValkeyKeys.concurrent_limit(scope, identity)
        return await self._client.concurrent_acquire(key, limit, ttl_seconds)

    async def release_concurrent(self, *, scope: str, identity: str) -> None:
        await self._client.concurrent_release(ValkeyKeys.concurrent_limit(scope, identity))
