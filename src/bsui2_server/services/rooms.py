"""Room and membership helpers."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bsui2_server.models import Membership, Room, User
from bsui2_server.schemas import RoomInfo


async def create_room(session: AsyncSession, creator: User, name: str) -> Room:
    room = Room(
        id=str(uuid.uuid4()),
        name=name,
        is_group=True,
        created_by=creator.id,
    )
    session.add(room)
    session.add(Membership(room_id=room.id, user_id=creator.id))
    await session.commit()
    await session.refresh(room)
    return room


async def get_room_or_404(session: AsyncSession, room_id: str) -> Room:
    room = await session.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


async def require_membership(session: AsyncSession, room_id: str, user_id: int) -> Membership:
    result = await session.execute(
        select(Membership).where(Membership.room_id == room_id, Membership.user_id == user_id)
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a room member")
    return membership


async def list_my_rooms(session: AsyncSession, user: User) -> list[RoomInfo]:
    result = await session.execute(
        select(Room)
        .join(Membership, Membership.room_id == Room.id)
        .where(Membership.user_id == user.id)
        .options(selectinload(Room.memberships).selectinload(Membership.user))
        .order_by(Room.created_at)
    )
    rooms = result.scalars().unique().all()
    out: list[RoomInfo] = []
    for room in rooms:
        logins = sorted(m.user.login for m in room.memberships)
        out.append(
            RoomInfo(id=room.id, name=room.name, is_group=room.is_group, users=logins)
        )
    return out


async def invite_users(
    session: AsyncSession, room_id: str, inviter: User, logins: list[str]
) -> None:
    await get_room_or_404(session, room_id)
    await require_membership(session, room_id, inviter.id)

    for login in logins:
        result = await session.execute(select(User).where(User.login == login))
        invitee = result.scalar_one_or_none()
        if invitee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown login: {login}",
            )
        existing = await session.execute(
            select(Membership).where(
                Membership.room_id == room_id, Membership.user_id == invitee.id
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(Membership(room_id=room_id, user_id=invitee.id))
    await session.commit()
