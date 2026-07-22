import hashlib
import math
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import db as db_module
from db import Base
from memory import embeddings, store
from models import Fact, FamilyCircle, JournalEntry, Membership, User, Visibility


def fake_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic 16-dim embedding; no network, no torch."""
    out = []
    for text in texts:
        digest = hashlib.sha256(text.encode()).digest()
        vec = [(b - 128) / 128 for b in digest[:16]]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        out.append([v / norm for v in vec])
    return out


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    # route any code that grabs its own session (services) at the same engine
    old_engine, old_sessionlocal = db_module.engine, db_module.SessionLocal
    db_module.engine, db_module.SessionLocal = engine, TestingSession
    yield session
    session.close()
    db_module.engine, db_module.SessionLocal = old_engine, old_sessionlocal


@pytest.fixture(autouse=True)
def vector_store():
    embeddings.set_embedder(fake_embed)
    client = chromadb.EphemeralClient()
    store.set_client(client)
    yield store
    try:
        client.delete_collection(store.COLLECTION_NAME)
    except Exception:
        pass
    store.set_client(None)
    embeddings.set_embedder(None)


@pytest.fixture()
def client(db):
    from fastapi.testclient import TestClient

    import db as db_mod
    from app import app

    def override_get_db():
        yield db

    app.dependency_overrides[db_mod.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_headers(user):
    from auth import create_token

    return {"Authorization": f"Bearer {create_token(user)}"}


class Family:
    def __init__(self, circle, aditya, deepa, mumma, abhishek):
        self.circle = circle
        self.aditya = aditya
        self.deepa = deepa
        self.mumma = mumma
        self.abhishek = abhishek


@pytest.fixture()
def family(db):
    users = {}
    for name, lang in [("Aditya", "en"), ("Deepa", "en"), ("Mumma", "hi"), ("Abhishek", "en")]:
        user = User(
            name=name,
            email=f"{name.lower()}@ghar.test",
            password_hash="x",
            language=lang,
        )
        db.add(user)
        users[name] = user
    db.flush()
    circle = FamilyCircle(name="Ghar", invite_code="GHAR01", created_by=users["Aditya"].id)
    db.add(circle)
    db.flush()
    for user in users.values():
        db.add(Membership(circle_id=circle.id, user_id=user.id))
    db.commit()
    return Family(circle, users["Aditya"], users["Deepa"], users["Mumma"], users["Abhishek"])


@pytest.fixture()
def outsider(db):
    user = User(name="Stranger", email="stranger@else.test", password_hash="x", language="en")
    db.add(user)
    db.commit()
    return user


def make_entry(
    db,
    author,
    circle,
    transcript,
    *,
    summary=None,
    visibility=Visibility.private,
    facts=(),
    created_at=None,
    index=True,
):
    """facts: iterable of dicts {type, content, structured?, visibility?}"""
    entry = JournalEntry(
        author_id=author.id,
        circle_id=circle.id,
        transcript=transcript,
        summary=summary or transcript,
        language=author.language,
        visibility=visibility,
        created_at=created_at or datetime.utcnow(),
    )
    db.add(entry)
    db.flush()
    fact_rows = []
    for spec in facts:
        fact = Fact(
            entry_id=entry.id,
            author_id=author.id,
            circle_id=circle.id,
            type=spec["type"],
            content=spec["content"],
            structured=spec.get("structured", {}),
            source_quote=spec.get("source_quote"),
            visibility=spec.get("visibility", Visibility.private),
            created_at=created_at or datetime.utcnow(),
        )
        db.add(fact)
        fact_rows.append(fact)
    db.commit()
    if index:
        from agents import librarian

        librarian.upsert_entry(db, entry, fact_rows)
    return entry, fact_rows
