"""Track open WebSocket connections and invalidate them on re-login."""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import WebSocket
from starlette.websockets import WebSocketState


@dataclass
class RoomConnection:
    websocket: WebSocket
    token: str
    login: str
    room_id: str


@dataclass
class PresenceHub:

    by_token: dict[str, list[RoomConnection]] = field(default_factory=dict)
    by_room: dict[str, list[RoomConnection]] = field(default_factory=dict)

    def register(self, conn: RoomConnection) -> None:
        self.by_token.setdefault(conn.token, []).append(conn)
        self.by_room.setdefault(conn.room_id, []).append(conn)

    def unregister(self, conn: RoomConnection) -> None:
        token_list = self.by_token.get(conn.token)
        if token_list and conn in token_list:
            token_list.remove(conn)
            if not token_list:
                del self.by_token[conn.token]
        room_list = self.by_room.get(conn.room_id)
        if room_list and conn in room_list:
            room_list.remove(conn)
            if not room_list:
                del self.by_room[conn.room_id]

    def has_open_ws_for_login(self, login: str) -> bool:
        for conns in self.by_token.values():
            for c in conns:
                if c.login == login:
                    return True
        return False

    async def close_token(self, token: str, code: int = 4001, reason: str = "session replaced") -> None:
        conns = list(self.by_token.get(token, []))
        for conn in conns:
            try:
                if conn.websocket.client_state == WebSocketState.CONNECTED:
                    await conn.websocket.close(code=code, reason=reason)
            except Exception:
                pass
            self.unregister(conn)

    async def broadcast_room(self, room_id: str, payload: dict) -> None:
        for conn in list(self.by_room.get(room_id, [])):
            try:
                if conn.websocket.client_state == WebSocketState.CONNECTED:
                    await conn.websocket.send_json(payload)
            except Exception:
                self.unregister(conn)


presence_hub = PresenceHub()
