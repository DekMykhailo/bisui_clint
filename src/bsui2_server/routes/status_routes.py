"""Presence / active-session status."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bsui2_server.db import get_session
from bsui2_server.models import User
from bsui2_server.schemas import ActiveResponse
from bsui2_server.services.presence import presence_hub

router = APIRouter(tags=["status"])


@router.get("/is_active/{user_id}", response_model=ActiveResponse)
async def is_active(
    user_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ActiveResponse:
    result = await session.execute(
        select(User).where(User.login == user_id).options(selectinload(User.session))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown login")
    active = user.session is not None or presence_hub.has_open_ws_for_login(user.login)
    return ActiveResponse(login=user.login, active=active)
