"""Aangan backend. Run from backend/: uvicorn app:app --reload --port 8000"""
import os

from fastapi import FastAPI

from config import settings
from db import Base, engine
from routes import (
    action_routes,
    activity_routes,
    alert_routes,
    ask_routes,
    auth_routes,
    circle_routes,
    entry_routes,
    keepsake_routes,
    nudge_routes,
    rule_routes,
)

app = FastAPI(title="Aangan", version="1.0")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    os.makedirs(settings.audio_dir, exist_ok=True)
    os.makedirs(settings.actions_dir, exist_ok=True)


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


@app.get("/health")
def health():
    return {"ok": True}
