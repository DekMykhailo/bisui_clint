"""WebSocket room fan-out."""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bsui2_server.db import SessionLocal
from bsui2_server.models import Membership, Session
from bsui2_server.schemas import WsInbound
from bsui2_server.services import messages as message_service
from bsui2_server.services.presence import RoomConnection, presence_hub

router = APIRouter(tags=["ws"])


@router.websocket("/ws/{room_id}")
async def room_ws(websocket: WebSocket, room_id: str) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401, reason="Missing token")
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(Session).where(Session.token == token).options(selectinload(Session.user))
        )
        sess = result.scalar_one_or_none()
        if sess is None:
            await websocket.close(code=4401, reason="Invalid token")
            return
        user = sess.user
        membership = await session.execute(
            select(Membership).where(
                Membership.room_id == room_id, Membership.user_id == user.id
            )
        )
        if membership.scalar_one_or_none() is None:
            await websocket.close(code=4403, reason="Not a room member")
            return
        login = user.login

    await websocket.accept()
    conn = RoomConnection(websocket=websocket, token=token, login=login, room_id=room_id)
    presence_hub.register(conn)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                inbound = WsInbound.model_validate(data)
            except (json.JSONDecodeError, ValidationError):
                await websocket.send_json({"error": "invalid payload; expected {\"message\": \"...\"}"})
                continue

            async with SessionLocal() as session:
                still = await session.execute(select(Session).where(Session.token == token))
                if still.scalar_one_or_none() is None:
                    await websocket.close(code=4001, reason="session replaced")
                    break
                frame = await message_service.save_message(
                    session, room_id, login, inbound.message
                )
            await presence_hub.broadcast_room(room_id, frame.model_dump())
    except WebSocketDisconnect:
        pass
    finally:
        presence_hub.unregister(conn)
