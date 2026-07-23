"""Rebuild the vector store with the CURRENT embedding model. Run from
backend/ after changing EMBEDDING_MODEL:

    .venv/bin/python scripts/reindex.py

Drops the collection (old vectors are unusable in the new model's space)
and re-indexes every journal entry through the same librarian.upsert_entry
path capture uses, so visibility metadata is rebuilt identically.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from agents import librarian
from config import settings
from db import SessionLocal
from memory import store
from models import JournalEntry


def main() -> None:
    print(f"Rebuilding vectors with {settings.embedding_model}…")
    store.reset_collection()
    db = SessionLocal()
    try:
        entries = db.query(JournalEntry).order_by(JournalEntry.id.asc()).all()
        for i, entry in enumerate(entries, 1):
            librarian.upsert_entry(db, entry)
            if i % 20 == 0:
                print(f"  {i}/{len(entries)} entries re-indexed…")
        print(f"Done: {len(entries)} entries re-indexed. ✔")
    finally:
        db.close()


if __name__ == "__main__":
    main()
