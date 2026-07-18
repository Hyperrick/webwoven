"""Live Relay lobby and race routes."""

from fastapi import APIRouter, status

from webwoven_api.http.contracts.rooms import (
    RoomCreateRequest,
    RoomInviteResponse,
    RoomReadyRequest,
    RoomRematchRequest,
    RoomResponse,
)
from webwoven_api.http.dependencies import ContainerDependency, GuestDependency
from webwoven_api.http.presentation.rooms import room_invite_response, room_response

router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    body: RoomCreateRequest,
    guest: GuestDependency,
    container: ContainerDependency,
) -> RoomResponse:
    room = await container.rooms.create(
        guest,
        body.difficulty,
        category=body.category,
        round_id=body.round_id,
    )
    return room_response(room, guest.id, container.graph)


@router.post("/{code}/join", response_model=RoomResponse)
async def join_room(
    code: str,
    guest: GuestDependency,
    container: ContainerDependency,
) -> RoomResponse:
    room = await container.rooms.join(code.upper(), guest)
    return room_response(room, guest.id, container.graph)


@router.get("/{code}/invite", response_model=RoomInviteResponse)
async def get_room_invite(
    code: str,
    guest: GuestDependency,
    container: ContainerDependency,
) -> RoomInviteResponse:
    room = await container.rooms.get_for_invite(code.upper())
    return room_invite_response(room, guest.id)


@router.post("/{code}/ready", response_model=RoomResponse)
async def ready_room(
    code: str,
    body: RoomReadyRequest,
    guest: GuestDependency,
    container: ContainerDependency,
) -> RoomResponse:
    room = await container.rooms.set_ready(code.upper(), guest.id, body.ready)
    return room_response(room, guest.id, container.graph)


@router.post("/{code}/start", response_model=RoomResponse)
async def start_room(
    code: str,
    guest: GuestDependency,
    container: ContainerDependency,
) -> RoomResponse:
    room = await container.rooms.start(code.upper(), guest.id)
    return room_response(room, guest.id, container.graph)


@router.post("/{code}/rematch", response_model=RoomResponse)
async def vote_room_rematch(
    code: str,
    body: RoomRematchRequest,
    guest: GuestDependency,
    container: ContainerDependency,
) -> RoomResponse:
    room = await container.rooms.vote_rematch(code.upper(), guest.id, body.accept)
    return room_response(room, guest.id, container.graph)


@router.get("/{code}", response_model=RoomResponse)
async def get_room(
    code: str,
    guest: GuestDependency,
    container: ContainerDependency,
) -> RoomResponse:
    room = await container.rooms.get_for_guest(code.upper(), guest.id)
    return room_response(room, guest.id, container.graph)
