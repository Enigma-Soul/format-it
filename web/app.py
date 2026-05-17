from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from web.routes import router, session_manager as _  # noqa: F401
from web.sessions import SessionManager

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app() -> FastAPI:
    import web.routes as routes

    app = FastAPI(title="格式化公文工具")

    routes.session_manager = SessionManager(base_tmp_dir=_PROJECT_ROOT / "tmp")

    app.include_router(routes.router)
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")

    return app
