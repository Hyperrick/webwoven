"""Versioned JSON mapping for immutable gameplay-session state."""

from datetime import datetime

from webwoven_api.domain.hints import HintResult, HintType
from webwoven_api.domain.navigation import NavigationState
from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import Round
from webwoven_api.persistence.serialization.values import (
    optional_date,
    optional_datetime,
    optional_int,
    optional_string,
    require_bool,
    require_datetime,
    require_int,
    require_list,
    require_object,
    require_string,
)
from webwoven_api.sessions.models import (
    CommandExecution,
    GameSession,
    HintUse,
    SessionMode,
    SessionStatus,
)

_SCHEMA_VERSION = 1


def session_to_dict(session: GameSession) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "id": session.id,
        "guest_id": session.guest_id,
        "mode": session.mode.value,
        "graph_version": session.graph_version,
        "round": _round_to_dict(session.round),
        "navigation": {
            "stack": list(session.navigation.stack),
            "trail": list(session.navigation.trail),
            "moves": session.navigation.moves,
        },
        "status": session.status.value,
        "state_version": session.state_version,
        "started_at": session.started_at.isoformat(),
        "hints": [_hint_use_to_dict(hint) for hint in session.hints],
        "completed_at": _datetime_value(session.completed_at),
        "final_score": session.final_score,
        "room_code": session.room_code,
        "daily_day": session.daily_day.isoformat() if session.daily_day is not None else None,
    }


def session_from_dict(value: object) -> GameSession:
    data = require_object(value, "session")
    _require_schema_version(data)
    navigation_data = require_object(data.get("navigation"), "session.navigation")
    stack = _string_tuple(navigation_data.get("stack"), "session.navigation.stack")
    trail = _string_tuple(navigation_data.get("trail"), "session.navigation.trail")
    if not stack:
        raise ValueError("session.navigation.stack cannot be empty")
    hints = tuple(
        _hint_use_from_dict(item) for item in require_list(data.get("hints"), "session.hints")
    )
    return GameSession(
        id=require_string(data.get("id"), "session.id"),
        guest_id=require_string(data.get("guest_id"), "session.guest_id"),
        mode=SessionMode(require_string(data.get("mode"), "session.mode")),
        graph_version=require_string(data.get("graph_version"), "session.graph_version"),
        round=_round_from_dict(data.get("round")),
        navigation=NavigationState(
            stack=stack,
            trail=trail,
            moves=require_int(navigation_data.get("moves"), "session.navigation.moves"),
        ),
        status=SessionStatus(require_string(data.get("status"), "session.status")),
        state_version=require_int(data.get("state_version"), "session.state_version"),
        started_at=require_datetime(data.get("started_at"), "session.started_at"),
        hints=hints,
        completed_at=optional_datetime(data.get("completed_at"), "session.completed_at"),
        final_score=optional_int(data.get("final_score"), "session.final_score"),
        room_code=optional_string(data.get("room_code"), "session.room_code"),
        daily_day=optional_date(data.get("daily_day"), "session.daily_day"),
    )


def command_execution_to_dict(result: CommandExecution) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "session": session_to_dict(result.session),
        "applied": result.applied,
        "duplicate": result.duplicate,
        "hint": _hint_result_to_dict(result.hint) if result.hint is not None else None,
    }


def command_execution_from_dict(value: object) -> CommandExecution:
    data = require_object(value, "command_execution")
    _require_schema_version(data)
    hint_value = data.get("hint")
    return CommandExecution(
        session=session_from_dict(data.get("session")),
        applied=require_bool(data.get("applied"), "command_execution.applied"),
        duplicate=require_bool(data.get("duplicate"), "command_execution.duplicate"),
        hint=_hint_result_from_dict(hint_value) if hint_value is not None else None,
    )


def _round_to_dict(round_: Round) -> dict[str, object]:
    return {
        "id": round_.id,
        "start_id": round_.start_id,
        "target_id": round_.target_id,
        "category": round_.category,
        "difficulty": round_.difficulty.value,
        "optimal_distance": round_.optimal_distance,
        "time_window": round_.time_window,
        "published": round_.published,
    }


def _round_from_dict(value: object) -> Round:
    data = require_object(value, "session.round")
    return Round(
        id=require_string(data.get("id"), "session.round.id"),
        start_id=require_string(data.get("start_id"), "session.round.start_id"),
        target_id=require_string(data.get("target_id"), "session.round.target_id"),
        category=require_string(data.get("category"), "session.round.category"),
        difficulty=Difficulty(require_string(data.get("difficulty"), "session.round.difficulty")),
        optimal_distance=require_int(
            data.get("optimal_distance"), "session.round.optimal_distance"
        ),
        time_window=require_int(data.get("time_window"), "session.round.time_window"),
        published=require_bool(data.get("published"), "session.round.published"),
    )


def _hint_use_to_dict(hint: HintUse) -> dict[str, object]:
    return {
        "hint_type": hint.hint_type.value,
        "penalty": hint.penalty,
        "relation_key": hint.relation_key,
        "entity_id": hint.entity_id,
        "message": hint.message,
        "used_at": hint.used_at.isoformat(),
    }


def _hint_use_from_dict(value: object) -> HintUse:
    data = require_object(value, "session.hints[]")
    return HintUse(
        hint_type=HintType(require_string(data.get("hint_type"), "hint.hint_type")),
        penalty=require_int(data.get("penalty"), "hint.penalty"),
        relation_key=optional_string(data.get("relation_key"), "hint.relation_key"),
        entity_id=optional_string(data.get("entity_id"), "hint.entity_id"),
        message=require_string(data.get("message"), "hint.message"),
        used_at=require_datetime(data.get("used_at"), "hint.used_at"),
    )


def _hint_result_to_dict(hint: HintResult) -> dict[str, object]:
    return {
        "hint_type": hint.hint_type.value,
        "penalty": hint.penalty,
        "relation_key": hint.relation_key,
        "entity_id": hint.entity_id,
        "message": hint.message,
    }


def _hint_result_from_dict(value: object) -> HintResult:
    data = require_object(value, "command_execution.hint")
    return HintResult(
        hint_type=HintType(require_string(data.get("hint_type"), "result.hint_type")),
        penalty=require_int(data.get("penalty"), "result.penalty"),
        relation_key=optional_string(data.get("relation_key"), "result.relation_key"),
        entity_id=optional_string(data.get("entity_id"), "result.entity_id"),
        message=require_string(data.get("message"), "result.message"),
    )


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    return tuple(require_string(item, f"{field}[]") for item in require_list(value, field))


def _require_schema_version(data: dict[str, object]) -> None:
    version = require_int(data.get("schema_version"), "schema_version")
    if version != _SCHEMA_VERSION:
        raise ValueError(f"Unsupported persistence schema version: {version}")


def _datetime_value(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
