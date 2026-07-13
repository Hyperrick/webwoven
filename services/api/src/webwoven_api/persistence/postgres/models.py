"""SQLAlchemy schema for durable production records."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class GuestRow(Base):
    __tablename__ = "guests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(24))
    csrf_token: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class GraphRegistrationRow(Base):
    __tablename__ = "graph_registrations"

    version: Mapped[str] = mapped_column(String(100), primary_key=True)
    manifest_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), index=True)
    graph_version: Mapped[str] = mapped_column(String(100), index=True)
    round_id: Mapped[str] = mapped_column(String(100), index=True)
    mode: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), index=True)
    state_version: Mapped[int] = mapped_column(Integer)
    state_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    final_score: Mapped[int | None] = mapped_column(Integer)


class SessionCommandRow(Base):
    __tablename__ = "session_commands"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True
    )
    client_command_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    expected_state_version: Mapped[int] = mapped_column(Integer)
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SessionEventRow(Base):
    __tablename__ = "session_events"
    __table_args__ = (Index("ix_session_events_order", "session_id", "state_version", "id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(40))
    state_version: Mapped[int] = mapped_column(Integer)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DailyAssignmentRow(Base):
    __tablename__ = "daily_assignments"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    graph_version: Mapped[str] = mapped_column(String(100))
    round_id: Mapped[str] = mapped_column(String(100))


class DailyScoreRow(Base):
    __tablename__ = "daily_scores"
    __table_args__ = (Index("ix_daily_rank", "day", "score", "elapsed_ms", "moves"),)

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), unique=True)
    score: Mapped[int] = mapped_column(Integer)
    moves: Mapped[int] = mapped_column(Integer)
    hints_used: Mapped[int] = mapped_column(Integer)
    elapsed_ms: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CompletedRoomRow(Base):
    __tablename__ = "completed_rooms"

    code: Mapped[str] = mapped_column(String(6), primary_key=True)
    graph_version: Mapped[str] = mapped_column(String(100))
    round_id: Mapped[str] = mapped_column(String(100))
    result_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ContentReportRow(Base):
    __tablename__ = "content_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.id"), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(40))
    edge_id: Mapped[str | None] = mapped_column(String(100))
    round_id: Mapped[str | None] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(String(30))
    details: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AnalyticsEventRow(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (Index("ix_analytics_name_time", "event_name", "occurred_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pseudonymous_guest_id: Mapped[str | None] = mapped_column(String(64), index=True)
    event_name: Mapped[str] = mapped_column(String(80))
    properties_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
