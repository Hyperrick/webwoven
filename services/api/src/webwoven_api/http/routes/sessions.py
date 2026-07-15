"""Route Race session routes."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from webwoven_api.domain.errors import DomainError, StaleStateError
from webwoven_api.http.contracts.sessions import (
    BackRequest,
    CommandResponse,
    FollowEdgeRequest,
    SessionCommandRequest,
    SessionCreateRequest,
    SessionSnapshot,
    StaleCommandResponse,
)
from webwoven_api.http.dependencies import ContainerDependency, GuestDependency
from webwoven_api.sessions.models import (
    BackCommand,
    FollowEdgeCommand,
    SessionCommand,
    SessionMode,
    UseHintCommand,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=SessionSnapshot, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreateRequest,
    guest: GuestDependency,
    container: ContainerDependency,
) -> SessionSnapshot:
    if body.mode is SessionMode.RELAY:
        raise DomainError("relay_requires_room", "Live Relay sessions are created by a room.")
    session = await container.sessions.create(
        guest_id=guest.id,
        mode=body.mode,
        round_id=body.round_id,
        category=body.category,
        difficulty=body.difficulty,
    )
    return container.session_presenter.snapshot(session)


@router.get("/{session_id}", response_model=SessionSnapshot)
async def get_session(
    session_id: str,
    guest: GuestDependency,
    container: ContainerDependency,
) -> SessionSnapshot:
    session = await container.sessions.get_for_guest(session_id, guest.id)
    return container.session_presenter.snapshot(session)


@router.post(
    "/{session_id}/commands",
    response_model=CommandResponse,
    responses={status.HTTP_409_CONFLICT: {"model": StaleCommandResponse}},
)
async def command_session(
    session_id: str,
    body: SessionCommandRequest,
    guest: GuestDependency,
    container: ContainerDependency,
) -> CommandResponse | JSONResponse:
    command = _domain_command(body)
    try:
        result = await container.sessions.execute(
            session_id=session_id,
            guest_id=guest.id,
            command=command,
        )
    except StaleStateError as error:
        current = await container.sessions.get_for_guest(session_id, guest.id)
        payload = StaleCommandResponse(
            message=str(error),
            current=container.session_presenter.snapshot(current),
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=payload.model_dump(mode="json"),
        )
    if result.session.room_code is not None:
        await container.rooms.sync_session(result.session)
    return CommandResponse(
        applied=result.applied,
        duplicate=result.duplicate,
        hint=container.session_presenter.hint_response(result.hint),
        session=container.session_presenter.snapshot(result.session),
    )


def _domain_command(body: SessionCommandRequest) -> SessionCommand:
    if isinstance(body, FollowEdgeRequest):
        return FollowEdgeCommand(
            command_id=body.client_command_id,
            expected_state_version=body.expected_state_version,
            edge_token=body.edge_token,
        )
    if isinstance(body, BackRequest):
        return BackCommand(
            command_id=body.client_command_id,
            expected_state_version=body.expected_state_version,
        )
    return UseHintCommand(
        command_id=body.client_command_id,
        expected_state_version=body.expected_state_version,
        hint_type=body.hint_type,
        relation_key=body.relation_property_id,
        entity_id=body.entity_qid,
    )
