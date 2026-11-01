"""Message persistence and framing."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bsui2_server.models import Message
from bsui2_server.schemas import MessageFrame


def format_timestamp(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def to_frame(msg: Message) -> MessageFrame:
    return MessageFrame(
        Timestamp=format_timestamp(msg.timestamp),
        who=msg.author_login,
        message=msg.content,
    )


async def save_message(
    session: AsyncSession, room_id: str, author_login: str, content: str
) -> MessageFrame:
    msg = Message(
        room_id=room_id,
        author_login=author_login,
        content=content,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return to_frame(msg)


async def get_messages(
    session: AsyncSession, room_id: str, limit: int = 100
) -> list[MessageFrame]:
    limit = max(1, min(limit, 1000))
    result = await session.execute(
        select(Message)
        .where(Message.room_id == room_id)
        .order_by(Message.timestamp.desc(), Message.id.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))
    return [to_frame(m) for m in rows]
