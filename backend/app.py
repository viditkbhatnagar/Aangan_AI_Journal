"""Aangan backend. Run from backend/: uvicorn app:app --reload --port 8000"""
import os

from fastapi import FastAPI

from config import settings
from db import Base, engine
from routes import auth_routes, circle_routes, entry_routes, rule_routes

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


@app.get("/health")
def health():
    return {"ok": True}
