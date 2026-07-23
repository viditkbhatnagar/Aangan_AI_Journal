"""Aangan backend. Run from backend/: uvicorn app:app --reload --port 8000"""
import logging
import logging.handlers
import os
from pathlib import Path

from fastapi import FastAPI

from config import settings
from db import Base, engine


def _configure_logging() -> None:
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        log_dir / "aangan.log", maxBytes=2_000_000, backupCount=3
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger("aangan")
    root.setLevel(logging.INFO)
    if not root.handlers:
        root.addHandler(handler)


_configure_logging()
from routes import (
    action_routes,
    activity_routes,
    alert_routes,
    ask_routes,
    auth_routes,
    circle_routes,
    entry_routes,
    fact_routes,
    feedback_routes,
    keepsake_routes,
    legal_routes,
    nudge_routes,
    plus_routes,
    rule_routes,
)

app = FastAPI(title="Aangan", version="1.0")


@app.on_event("startup")
def startup():
    if settings.aangan_env == "production" and settings.jwt_secret == "change-me":
        raise RuntimeError(
            "Refusing to start in production with the default JWT_SECRET — "
            "set a strong secret in backend/.env."
        )
    Base.metadata.create_all(engine)
    os.makedirs(settings.audio_dir, exist_ok=True)
    os.makedirs(settings.actions_dir, exist_ok=True)


@app.middleware("http")
async def rate_limit(request, call_next):
    from fastapi.responses import JSONResponse

    from services import ratelimit

    path = request.url.path
    scope = None
    if path.startswith("/auth/"):
        scope, cap = "auth", settings.rate_limit_auth_max
    elif path == "/ask":
        scope, cap = "ask", settings.rate_limit_ask_max
    if scope is not None:
        ip = request.client.host if request.client else "unknown"
        if not ratelimit.allow(ip, scope, cap, settings.rate_limit_window_sec):
            return JSONResponse(
                status_code=429,
                content={"detail": "Let's take a small breath — try again in a minute. 🌿"},
            )
    return await call_next(request)


app.include_router(auth_routes.router)
app.include_router(circle_routes.router)
app.include_router(entry_routes.router)
app.include_router(rule_routes.router)
app.include_router(ask_routes.router)
app.include_router(alert_routes.router)
app.include_router(action_routes.router)
app.include_router(nudge_routes.router)
app.include_router(keepsake_routes.router)
app.include_router(activity_routes.router)
app.include_router(legal_routes.router)
app.include_router(plus_routes.router)
app.include_router(fact_routes.router)
app.include_router(feedback_routes.router)


@app.get("/health")
def health():
    return {"ok": True}


# --- single-container deployment: serve the built frontend (SPA) ---
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    from fastapi.responses import FileResponse

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = (_FRONTEND_DIST / path).resolve()
        if (
            path
            and candidate.is_file()
            and str(candidate).startswith(str(_FRONTEND_DIST))
        ):
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST / "index.html")
