from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db, close_db
from .routers import analysis


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="Analysis Service", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _startup() -> None:
        await init_db()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await close_db()

    app.include_router(analysis.router, prefix="/api/v1")
    app.include_router(analysis.router, prefix="/api")

    return app


app = create_app()