"""Durable PostgreSQL adapters for server-owned game records."""

from webwoven_api.persistence.postgres.analytics import PostgresAnalyticsRepository
from webwoven_api.persistence.postgres.daily import PostgresDailyRepository
from webwoven_api.persistence.postgres.database import PostgresDatabase
from webwoven_api.persistence.postgres.guests import PostgresGuestRepository
from webwoven_api.persistence.postgres.registry import PostgresGraphRegistry
from webwoven_api.persistence.postgres.reports import PostgresContentReportRepository
from webwoven_api.persistence.postgres.rooms import PostgresCompletedRoomRepository
from webwoven_api.persistence.postgres.round_selections import PostgresRoundSelectionRepository
from webwoven_api.persistence.postgres.sessions import PostgresSessionRepository

__all__ = [
    "PostgresAnalyticsRepository",
    "PostgresCompletedRoomRepository",
    "PostgresContentReportRepository",
    "PostgresDailyRepository",
    "PostgresDatabase",
    "PostgresGraphRegistry",
    "PostgresGuestRepository",
    "PostgresRoundSelectionRepository",
    "PostgresSessionRepository",
]
