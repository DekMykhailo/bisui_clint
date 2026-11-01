"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import uvicorn
from fastapi import FastAPI

from bsui2_server import config
from bsui2_server.db import init_db
from bsui2_server.routes import auth_routes, room_routes, status_routes, ws_routes


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield


app = FastAPI(
    title="BSUI2 Messenger Server",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_routes.router)
app.include_router(room_routes.router)
app.include_router(status_routes.router)
app.include_router(ws_routes.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    kwargs: dict = {
        "host": config.HOST,
        "port": config.PORT,
    }
    cert = config.SSL_CERTFILE
    key = config.SSL_KEYFILE
    from pathlib import Path

    if Path(cert).is_file() and Path(key).is_file():
        kwargs["ssl_certfile"] = cert
        kwargs["ssl_keyfile"] = key
    uvicorn.run("bsui2_server.main:app", **kwargs)


if __name__ == "__main__":
    run()
