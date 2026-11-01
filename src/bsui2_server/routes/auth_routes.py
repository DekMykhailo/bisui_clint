"""Registration and login."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from bsui2_server.auth import hash_password, new_token, verify_password
from bsui2_server.db import get_session
from bsui2_server.models import Session, User
from bsui2_server.schemas import LoginRequest, RegisterRequest, StatusOk, TokenResponse
from bsui2_server.services.presence import presence_hub

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=StatusOk)
async def register(
    body: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> StatusOk:
    existing = await session.execute(select(User).where(User.login == body.login))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Login taken")
    user = User(login=body.login, password_hash=hash_password(body.password))
    session.add(user)
    await session.commit()
    return StatusOk()


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    result = await session.execute(select(User).where(User.login == body.login))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")

    old = await session.execute(select(Session).where(Session.user_id == user.id))
    old_session = old.scalar_one_or_none()
    if old_session is not None:
        await presence_hub.close_token(old_session.token, code=4001, reason="session replaced")
        await session.execute(delete(Session).where(Session.user_id == user.id))

    token = new_token()
    session.add(Session(token=token, user_id=user.id))
    await session.commit()
    return TokenResponse(token=token)
