"""Explicit dependency composition for transport adapters."""

from dataclasses import dataclass

from webwoven_api.daily.completion import DailyCompletionRecorder
from webwoven_api.daily.repository import DailyRepository
from webwoven_api.daily.service import DailyService
from webwoven_api.graph.bundle import load_graph_bundle
from webwoven_api.graph.contracts import GraphReader
from webwoven_api.graph.memory_reader import MemoryGraphReader
from webwoven_api.guests.repository import GuestRepository
from webwoven_api.guests.service import GuestService
from webwoven_api.http.presentation.sessions import SessionPresenter
from webwoven_api.persistence.lifecycle import (
    MemoryPersistenceLifecycle,
    PersistenceLifecycle,
    ProductionPersistenceLifecycle,
)
from webwoven_api.persistence.memory.daily import MemoryDailyRepository
from webwoven_api.persistence.memory.guests import MemoryGuestRepository
from webwoven_api.persistence.memory.rate_limits import MemoryRateLimiter
from webwoven_api.persistence.memory.reports import MemoryContentReportRepository
from webwoven_api.persistence.memory.rooms import MemoryRoomRepository
from webwoven_api.persistence.memory.round_selections import MemoryRoundSelectionRepository
from webwoven_api.persistence.memory.sessions import MemorySessionRepository
from webwoven_api.persistence.postgres import (
    PostgresCompletedRoomRepository,
    PostgresContentReportRepository,
    PostgresDailyRepository,
    PostgresDatabase,
    PostgresGraphRegistry,
    PostgresGuestRepository,
    PostgresRoundSelectionRepository,
    PostgresSessionRepository,
)
from webwoven_api.persistence.valkey import (
    RedisValkeyClient,
    ValkeyRateLimiter,
    ValkeyRoomEventBroker,
    ValkeyRoomRepository,
)
from webwoven_api.reports.repository import ContentReportRepository
from webwoven_api.reports.service import ContentReportService
from webwoven_api.rooms.authorization import RelayCommandAuthorizer
from webwoven_api.rooms.broker import MemoryRoomEventBroker, RoomEventBroker
from webwoven_api.rooms.repository import RoomRepository
from webwoven_api.rooms.service import RoomService
from webwoven_api.security.rate_limits import RateLimiter
from webwoven_api.security.tokens import EdgeTokenSigner, GuestCookieSigner
from webwoven_api.sessions.repository import SessionRepository
from webwoven_api.sessions.selection import RoundSelectionRepository, RoundSelector
from webwoven_api.sessions.service import SessionService
from webwoven_api.settings import Settings


@dataclass(frozen=True, slots=True)
class AppContainer:
    settings: Settings
    graph: GraphReader
    guests: GuestService
    daily: DailyService
    sessions: SessionService
    session_presenter: SessionPresenter
    rooms: RoomService
    room_broker: RoomEventBroker
    reports: ContentReportService
    guest_cookies: GuestCookieSigner
    rate_limiter: RateLimiter
    persistence: PersistenceLifecycle

    async def start(self) -> None:
        await self.persistence.start()

    async def is_ready(self) -> bool:
        return await self.persistence.is_ready()

    async def close(self) -> None:
        await self.persistence.close()


@dataclass(frozen=True, slots=True)
class _PersistenceAdapters:
    guests: GuestRepository
    sessions: SessionRepository
    round_selections: RoundSelectionRepository
    daily: DailyRepository
    rooms: RoomRepository
    reports: ContentReportRepository
    room_broker: RoomEventBroker
    rate_limiter: RateLimiter
    lifecycle: PersistenceLifecycle


def build_container(settings: Settings) -> AppContainer:
    """Compose domain services around memory or production infrastructure adapters."""
    graph: GraphReader
    if settings.graph_path.is_file():
        graph = load_graph_bundle(
            settings.graph_path,
            settings.graph_manifest_path,
            required_kind=("test_fixture" if settings.environment == "testing" else "wikidata"),
        )
    elif settings.environment == "testing":
        graph = MemoryGraphReader.demo()
    else:
        raise FileNotFoundError(f"Graph bundle not found: {settings.graph_path}")

    adapters = (
        _memory_adapters()
        if settings.use_memory_persistence
        else _production_adapters(settings, graph)
    )

    guests = GuestService(adapters.guests)
    daily = DailyService(graph, adapters.daily)
    completion = DailyCompletionRecorder(daily, guests)
    edge_tokens = EdgeTokenSigner(
        settings.edge_secret,
        ttl_seconds=settings.edge_token_ttl_seconds,
    )
    round_selector = RoundSelector(graph, adapters.round_selections)
    sessions = SessionService(
        graph=graph,
        repository=adapters.sessions,
        daily=daily,
        edge_tokens=edge_tokens,
        completion_recorder=completion,
        command_authorizer=RelayCommandAuthorizer(adapters.rooms),
        round_selector=round_selector,
        start_delay_seconds=settings.round_intro_seconds,
    )
    rooms = RoomService(
        graph=graph,
        repository=adapters.rooms,
        broker=adapters.room_broker,
        sessions=sessions,
        round_selector=round_selector,
        start_delay_seconds=settings.round_intro_seconds,
    )
    return AppContainer(
        settings=settings,
        graph=graph,
        guests=guests,
        daily=daily,
        sessions=sessions,
        session_presenter=SessionPresenter(graph, sessions),
        rooms=rooms,
        room_broker=adapters.room_broker,
        reports=ContentReportService(adapters.reports),
        guest_cookies=GuestCookieSigner(settings.session_secret),
        rate_limiter=adapters.rate_limiter,
        persistence=adapters.lifecycle,
    )


def _memory_adapters() -> _PersistenceAdapters:
    return _PersistenceAdapters(
        guests=MemoryGuestRepository(),
        sessions=MemorySessionRepository(),
        round_selections=MemoryRoundSelectionRepository(),
        daily=MemoryDailyRepository(),
        rooms=MemoryRoomRepository(),
        reports=MemoryContentReportRepository(),
        room_broker=MemoryRoomEventBroker(),
        rate_limiter=MemoryRateLimiter(),
        lifecycle=MemoryPersistenceLifecycle(),
    )


def _production_adapters(settings: Settings, graph: GraphReader) -> _PersistenceAdapters:
    database = PostgresDatabase(settings.database_url)
    valkey = RedisValkeyClient(settings.valkey_url)
    room_archive = PostgresCompletedRoomRepository(database)
    room_repository = ValkeyRoomRepository(
        valkey,
        room_archive,
        active_ttl_seconds=settings.room_active_ttl_seconds,
        completed_ttl_seconds=settings.room_completed_ttl_seconds,
        lock_lease_seconds=settings.room_lock_lease_seconds,
        lock_wait_seconds=settings.room_lock_wait_seconds,
    )
    room_broker = ValkeyRoomEventBroker(
        valkey,
        stream_max_length=settings.room_event_stream_max_length,
        stream_ttl_seconds=settings.room_active_ttl_seconds,
    )
    lifecycle = ProductionPersistenceLifecycle(
        database=database,
        valkey=valkey,
        room_broker=room_broker,
        graph_registry=PostgresGraphRegistry(database),
        graph_version=graph.graph_version,
        manifest_path=settings.graph_manifest_path,
        graph_path=settings.graph_path,
        auto_create_schema=settings.auto_create_schema,
    )
    return _PersistenceAdapters(
        guests=PostgresGuestRepository(database),
        sessions=PostgresSessionRepository(database),
        round_selections=PostgresRoundSelectionRepository(database),
        daily=PostgresDailyRepository(database),
        rooms=room_repository,
        reports=PostgresContentReportRepository(database),
        room_broker=room_broker,
        rate_limiter=ValkeyRateLimiter(valkey),
        lifecycle=lifecycle,
    )
