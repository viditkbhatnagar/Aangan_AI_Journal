"""Librarian: every read of family memory goes through here, filtered to what
the asker is allowed to see (spec Section 7). The visibility test runs on the
relational row for EVERY hit — Chroma's metadata filter is only a prefilter,
never trusted on its own. There is no code path around this module that lets
the Companion read another member's private content.
"""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from auth import get_user_circle_id
from memory import store
from models import Fact, JournalEntry, ShareTarget, User, Visibility

OVERFETCH = 4  # over-fetch factor: post-filter attrition still yields k snippets
STOPWORDS = {
    "what", "when", "where", "would", "could", "should", "does", "did", "the",
    "and", "for", "with", "her", "his", "their", "about", "want", "like",
    "from", "have", "has", "was", "were", "will", "how", "who", "she", "him",
    "this", "that", "tell", "know", "day", "today",
}


@dataclass
class Snippet:
    text: str
    entry_id: int
    fact_id: int | None
    author_id: int
    author_name: str
    created_at: datetime
    source: str  # "entry" or the fact type


def custom_viewer_ids(db: Session, *, entry_id: int | None = None, fact_id: int | None = None) -> list[int]:
    q = db.query(ShareTarget.user_id)
    q = q.filter(ShareTarget.fact_id == fact_id) if fact_id else q.filter(
        ShareTarget.entry_id == entry_id, ShareTarget.fact_id.is_(None)
    )
    return [row[0] for row in q.all()]


def is_visible(db: Session, asker: User, *, entry_id: int | None = None, fact_id: int | None = None) -> bool:
    """The Section 7 visibility test, against the live relational row.
    Authoritative second guard for every vector hit."""
    if fact_id:
        row = db.get(Fact, fact_id)
    else:
        row = db.get(JournalEntry, entry_id) if entry_id else None
    if row is None:
        return False  # deleted since indexing — never return it
    if row.author_id == asker.id:
        return True
    asker_circle = get_user_circle_id(db, asker)
    if asker_circle is None or row.circle_id != asker_circle:
        return False
    if row.visibility == Visibility.circle:
        return True
    if row.visibility == Visibility.custom:
        kwargs = {"fact_id": row.id} if fact_id else {"entry_id": row.id}
        return asker.id in custom_viewer_ids(db, **kwargs)
    return False  # private: only the author, handled above


def upsert_entry(db: Session, entry: JournalEntry, facts: list[Fact] | None = None) -> None:
    """(Re-)index an entry summary and its facts with current visibility
    metadata. Called on capture and again on every visibility change so the
    two stores converge."""
    if facts is None:
        facts = list(entry.facts)
    ids, texts, metas = [], [], []
    if entry.summary or entry.transcript:
        ids.append(f"entry:{entry.id}")
        texts.append(entry.summary or entry.transcript)
        metas.append(store.entry_metadata(entry, custom_viewer_ids(db, entry_id=entry.id)))
    for fact in facts:
        ids.append(f"fact:{fact.id}")
        texts.append(fact.content)
        metas.append(store.fact_metadata(fact, custom_viewer_ids(db, fact_id=fact.id)))
    store.upsert_documents(ids, texts, metas)


def _snippet_from_row(db: Session, meta: dict, text: str) -> Snippet:
    author = db.get(User, meta["author_id"])
    return Snippet(
        text=text,
        entry_id=meta["entry_id"],
        fact_id=meta["fact_id"] or None,
        author_id=meta["author_id"],
        author_name=author.name if author else "someone",
        created_at=datetime.fromisoformat(meta["created_at"]),
        source=meta["type"] if meta["type"] != "summary" else "entry",
    )


def _keyword_facts(db: Session, asker: User, circle_id: int, question: str, k: int) -> list[Fact]:
    """Structured lookup for exact things (names, gift tags, dates)."""
    terms = [w.strip(".,?!\"'").lower() for w in question.split()]
    terms = [t for t in terms if len(t) >= 3 and t not in STOPWORDS]
    if not terms:
        return []
    candidates = (
        db.query(Fact)
        .filter(Fact.circle_id == circle_id)
        .order_by(Fact.created_at.desc())
        .limit(200)
        .all()
    )
    hits = []
    for fact in candidates:
        haystack = (fact.content + " " + str(fact.structured)).lower()
        if any(t in haystack for t in terms):
            hits.append(fact)
        if len(hits) >= k:
            break
    return hits


def search(db: Session, asker: User, question: str, k: int = 8) -> list[Snippet]:
    circle_id = get_user_circle_id(db, asker)
    if circle_id is None:
        return []

    snippets: list[Snippet] = []
    seen: set[str] = set()

    # 1) vector search with the conservative prefilter
    where = store.visibility_where(asker.id, circle_id)
    for hit in store.query(question, where, n_results=k * OVERFETCH):
        meta = hit["metadata"]
        fact_id = meta["fact_id"] or None
        entry_id = meta["entry_id"]
        # authoritative check on the live row — the second guard
        if not is_visible(db, asker, entry_id=entry_id, fact_id=fact_id):
            continue
        if hit["id"] in seen:
            continue
        seen.add(hit["id"])
        snippets.append(_snippet_from_row(db, meta, hit["text"]))
        if len(snippets) >= k:
            break

    # 2) structured lookup, same visibility test on every row
    for fact in _keyword_facts(db, asker, circle_id, question, k):
        if f"fact:{fact.id}" in seen:
            continue
        if not is_visible(db, asker, fact_id=fact.id):
            continue
        seen.add(f"fact:{fact.id}")
        author = db.get(User, fact.author_id)
        snippets.append(
            Snippet(
                text=fact.content,
                entry_id=fact.entry_id,
                fact_id=fact.id,
                author_id=fact.author_id,
                author_name=author.name if author else "someone",
                created_at=fact.created_at,
                source=fact.type,
            )
        )

    snippets.sort(key=lambda s: s.created_at, reverse=True)
    return snippets[: k + 4]
