"""Lease-backed distributed locks for Valkey room transactions."""

import asyncio
import secrets
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from time import monotonic

from webwoven_api.persistence.valkey.client import ValkeyClient


class ValkeyLockManager:
    def __init__(
        self,
        client: ValkeyClient,
        *,
        lease_seconds: int,
        wait_seconds: float,
    ) -> None:
        self._client = client
        self._lease_seconds = lease_seconds
        self._wait_seconds = wait_seconds

    @asynccontextmanager
    async def lock(self, key: str) -> AsyncGenerator[None]:
        token = secrets.token_urlsafe(24)
        deadline = monotonic() + self._wait_seconds
        while not await self._client.set(
            key,
            token,
            ttl_seconds=self._lease_seconds,
            only_if_absent=True,
        ):
            if monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for distributed lock {key}")
            await asyncio.sleep(0.05)
        renewal = asyncio.create_task(self._renew(key, token))
        try:
            yield
        finally:
            renewal.cancel()
            with suppress(asyncio.CancelledError):
                await renewal
            await self._client.compare_delete(key, token)

    async def _renew(self, key: str, token: str) -> None:
        interval = max(self._lease_seconds / 3, 0.25)
        while True:
            await asyncio.sleep(interval)
            renewed = await self._client.compare_expire(
                key,
                token,
                self._lease_seconds,
            )
            if not renewed:
                return
