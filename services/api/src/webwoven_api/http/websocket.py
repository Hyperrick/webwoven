"""Authenticated ordered room-event WebSocket with snapshot resume."""

import asyncio
from contextlib import suppress
from time import monotonic
from typing import cast

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from webwoven_api.container import AppContainer
from webwoven_api.domain.errors import ForbiddenError, NotFoundError
from webwoven_api.http.contracts.rooms import RoomEventResponse
from webwoven_api.http.presenters import room_response
from webwoven_api.http.rate_limit_identity import guest_rate_identity
from webwoven_api.rooms.models import RoomEvent

router = APIRouter(tags=["rooms"])


@router.websocket("/api/v1/ws/rooms/{code}")
async def room_events(websocket: WebSocket, code: str, after: int = 0) -> None:
    container = cast(AppContainer, websocket.app.state.container)
    origin = websocket.headers.get("origin")
    allowed_origins = {
        container.settings.origin.rstrip("/"),
        container.settings.api_origin.rstrip("/"),
    }
    if origin is None or origin.rstrip("/") not in allowed_origins:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    token = websocket.cookies.get(container.settings.cookie_name)
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        guest_id = container.guest_cookies.verify(token)
        await container.guests.get(guest_id)
    except (ForbiddenError, NotFoundError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    identity = guest_rate_identity(guest_id, container.settings.session_secret)
    try:
        decision = await container.rate_limiter.check(
            scope="ws-resume",
            identity=identity,
            limit=container.settings.rate_limit_ws_resumes,
            window_seconds=container.settings.rate_limit_window_seconds,
        )
    except Exception:
        await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
        return
    if not decision.allowed:
        await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
        return

    try:
        acquired = await container.rate_limiter.acquire_concurrent(
            scope="ws-connection",
            identity=identity,
            limit=container.settings.websocket_concurrent_per_guest,
            ttl_seconds=container.settings.websocket_max_lifetime_seconds + 60,
        )
    except Exception:
        await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
        return
    if not acquired:
        await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
        return

    room_code = code.upper()
    queue: asyncio.Queue[RoomEvent] | None = None
    connected = False
    try:
        queue = await container.room_broker.subscribe(room_code)
        room, replay = await container.rooms.connect(room_code, guest_id, max(after, 0))
        connected = True
        await websocket.accept()
        sent_sequence = max(after, 0)
        if after > 0 and replay:
            for event in replay:
                await _send_event(websocket, event)
                sent_sequence = max(sent_sequence, event.sequence)
        else:
            snapshot = room_response(room, guest_id, container.graph).model_dump(mode="json")
            await websocket.send_json(
                {
                    "sequence": room.sequence,
                    "type": "room.snapshot",
                    "occurred_at": room.updated_at.isoformat(),
                    "payload": snapshot,
                }
            )
            sent_sequence = room.sequence
        await _event_loop(
            websocket,
            container,
            room_code,
            queue,
            sent_sequence,
            idle_timeout_seconds=container.settings.websocket_idle_timeout_seconds,
            max_lifetime_seconds=container.settings.websocket_max_lifetime_seconds,
        )
    except (ForbiddenError, NotFoundError):
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    except WebSocketDisconnect:
        pass
    finally:
        try:
            if queue is not None:
                await container.room_broker.unsubscribe(room_code, queue)
            if connected:
                await container.rooms.disconnect(room_code, guest_id)
        finally:
            with suppress(Exception):
                await container.rate_limiter.release_concurrent(
                    scope="ws-connection",
                    identity=identity,
                )


async def _event_loop(
    websocket: WebSocket,
    container: AppContainer,
    room_code: str,
    queue: asyncio.Queue[RoomEvent],
    sent_sequence: int,
    *,
    idle_timeout_seconds: int,
    max_lifetime_seconds: int,
) -> None:
    connected_at = monotonic()
    last_client_activity = connected_at
    while True:
        now = monotonic()
        max_remaining = max_lifetime_seconds - (now - connected_at)
        idle_remaining = idle_timeout_seconds - (now - last_client_activity)
        if max_remaining <= 0:
            await websocket.close(code=status.WS_1001_GOING_AWAY, reason="Reconnect required")
            return
        if idle_remaining <= 0:
            await websocket.close(code=status.WS_1001_GOING_AWAY, reason="Connection idle")
            return
        receive_task = asyncio.create_task(websocket.receive_text())
        event_task = asyncio.create_task(queue.get())
        done, pending = await asyncio.wait(
            {receive_task, event_task},
            timeout=min(15, max_remaining, idle_remaining),
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        if not done:
            room = await container.rooms.get_for_guest(
                room_code,
                container.guest_cookies.verify(websocket.cookies[container.settings.cookie_name]),
            )
            await websocket.send_json(
                {"sequence": room.sequence, "type": "heartbeat", "payload": {}}
            )
            continue
        if event_task in done:
            event = event_task.result()
            if event.sequence > sent_sequence:
                await _send_event(websocket, event)
                sent_sequence = event.sequence
        if receive_task in done:
            message = receive_task.result()
            last_client_activity = monotonic()
            if message == "ping":
                await websocket.send_text("pong")


async def _send_event(websocket: WebSocket, event: RoomEvent) -> None:
    payload = RoomEventResponse(
        sequence=event.sequence,
        type=event.type,
        occurred_at=event.occurred_at,
        payload=event.payload,
    )
    await websocket.send_json(payload.model_dump(mode="json"))
