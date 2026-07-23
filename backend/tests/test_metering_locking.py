"""Regression: metering must persist even while the capture pipeline holds
SQLite's write lock. A separate-connection insert silently failed there — the
fix rides the caller's session. This test uses a REAL file-backed database
with distinct connections (unlike the shared StaticPool fixture)."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base
from models import LlmCall, User
from services import metering


def test_record_llm_persists_mid_transaction(tmp_path: Path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'lock.db'}",
        connect_args={"check_same_thread": False, "timeout": 1},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    session = Session()
    session.add(User(name="A", email="a@x.test", password_hash="x"))
    session.flush()  # transaction open -> SQLite write lock held

    with metering.context(user_id=1, db=session):
        metering.record_llm("Summarizer", "openai", "test-model", 10, 5, 100)

    session.commit()  # the metering row rides the caller's commit
    check = Session()
    rows = check.query(LlmCall).all()
    assert len(rows) == 1
    assert rows[0].agent == "Summarizer" and rows[0].user_id == 1
    check.close()
    session.close()
    engine.dispose()
