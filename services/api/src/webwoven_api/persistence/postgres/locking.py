"""Stable PostgreSQL advisory-lock keys for cross-process serialization."""

import hashlib

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def advisory_key(scope: str, identity: str) -> int:
    digest = hashlib.sha256(f"{scope}:{identity}".encode()).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=True)


async def acquire_transaction_lock(
    session: AsyncSession,
    *,
    scope: str,
    identity: str,
) -> None:
    await session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": advisory_key(scope, identity)},
    )
