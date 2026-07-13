"""Application lifecycle for memory and production persistence resources."""

import hashlib
from pathlib import Path
from typing import Protocol

from webwoven_api.persistence.postgres import PostgresDatabase, PostgresGraphRegistry
from webwoven_api.persistence.valkey.broker import ValkeyRoomEventBroker
from webwoven_api.persistence.valkey.client import ValkeyClient


class PersistenceLifecycle(Protocol):
    async def start(self) -> None: ...

    async def is_ready(self) -> bool: ...

    async def close(self) -> None: ...


class MemoryPersistenceLifecycle:
    async def start(self) -> None:
        return None

    async def is_ready(self) -> bool:
        return True

    async def close(self) -> None:
        return None


class ProductionPersistenceLifecycle:
    def __init__(
        self,
        *,
        database: PostgresDatabase,
        valkey: ValkeyClient,
        room_broker: ValkeyRoomEventBroker,
        graph_registry: PostgresGraphRegistry,
        graph_version: str,
        manifest_path: Path,
        graph_path: Path,
        auto_create_schema: bool,
    ) -> None:
        self._database = database
        self._valkey = valkey
        self._room_broker = room_broker
        self._graph_registry = graph_registry
        self._graph_version = graph_version
        self._manifest_path = manifest_path
        self._graph_path = graph_path
        self._auto_create_schema = auto_create_schema

    async def start(self) -> None:
        if self._auto_create_schema:
            await self._database.create_schema()
        if not await self._database.ping():
            raise RuntimeError("PostgreSQL is unavailable")
        if not await self._valkey.ping():
            raise RuntimeError("Valkey is unavailable")
        await self._graph_registry.register(
            self._graph_version,
            _bundle_sha256(self._manifest_path, self._graph_path),
        )

    async def is_ready(self) -> bool:
        database_ready, valkey_ready = await self._database.ping(), await self._valkey.ping()
        return database_ready and valkey_ready

    async def close(self) -> None:
        try:
            await self._room_broker.close()
        finally:
            try:
                await self._valkey.close()
            finally:
                await self._database.close()


def _bundle_sha256(manifest_path: Path, graph_path: Path) -> str:
    source = manifest_path if manifest_path.is_file() else graph_path
    if not source.is_file():
        raise FileNotFoundError(f"Graph provenance source is missing: {source}")
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
