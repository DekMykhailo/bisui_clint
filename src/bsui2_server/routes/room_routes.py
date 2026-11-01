"""Room CRUD, invite, and message history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from bsui2_server.auth import get_current_user
from bsui2_server.db import get_session
from bsui2_server.models import User
from bsui2_server.schemas import (
    CreateRoomRequest,
    CreateRoomResponse,
    InviteRequest,
    InviteResponse,
    MessagesResponse,
    MyRoomsResponse,
)
from bsui2_server.services import messages as message_service
from bsui2_server.services import rooms as room_service

router = APIRouter(tags=["rooms"])


@router.post("/create", response_model=CreateRoomResponse)
async def create_room(
    body: CreateRoomRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CreateRoomResponse:
    room = await room_service.create_room(session, user, body.name)
    return CreateRoomResponse(id=room.id)


async def _my_rooms(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MyRoomsResponse:
    rooms = await room_service.list_my_rooms(session, user)
    return MyRoomsResponse(rooms=rooms)


router.add_api_route("/my_rooms", _my_rooms, methods=["GET"], response_model=MyRoomsResponse)
router.add_api_route("/myrooms", _my_rooms, methods=["GET"], response_model=MyRoomsResponse)


@router.post("/invite/{room_id}", response_model=InviteResponse)
async def invite(
    room_id: str,
    body: InviteRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> InviteResponse:
    await room_service.invite_users(session, room_id, user, body.users)
    return InviteResponse(kod="ok")


@router.get("/get_msg/{room_id}", response_model=MessagesResponse)
async def get_msg(
    room_id: str,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(default=100, ge=1, le=1000),
) -> MessagesResponse:
    await room_service.get_room_or_404(session, room_id)
    await room_service.require_membership(session, room_id, user.id)
    frames = await message_service.get_messages(session, room_id, limit=limit)
    return MessagesResponse(messages=frames)
