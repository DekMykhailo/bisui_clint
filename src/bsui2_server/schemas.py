"""Pydantic request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    login: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class LoginRequest(BaseModel):
    login: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class StatusOk(BaseModel):
    status: str = "ok"


class TokenResponse(BaseModel):
    token: str


class CreateRoomRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CreateRoomResponse(BaseModel):
    id: str


class RoomInfo(BaseModel):
    id: str
    name: str
    is_group: bool
    users: list[str]


class MyRoomsResponse(BaseModel):
    rooms: list[RoomInfo]


class InviteRequest(BaseModel):
    users: list[str] = Field(min_length=1)


class InviteResponse(BaseModel):
    kod: str = "ok"


class MessageFrame(BaseModel):
    Timestamp: str
    who: str
    message: str


class MessagesResponse(BaseModel):
    messages: list[MessageFrame]


class ActiveResponse(BaseModel):
    login: str
    active: bool


class WsInbound(BaseModel):
    message: str = Field(min_length=1)
