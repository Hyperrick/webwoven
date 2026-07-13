"""Transport-independent request-rate decision boundary."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: int


class RateLimiter(Protocol):
    async def check(
        self,
        *,
        scope: str,
        identity: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision: ...

    async def acquire_concurrent(
        self,
        *,
        scope: str,
        identity: str,
        limit: int,
        ttl_seconds: int,
    ) -> bool: ...

    async def release_concurrent(self, *, scope: str, identity: str) -> None: ...
