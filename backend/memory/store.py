"""Chroma setup, upsert, and visibility-filtered query.

Chroma metadata must be scalar, so `custom_viewer_ids` is stored as a
comma-padded string (",3,7,") and the `where` filter can only be a
conservative prefilter: it excludes every private document not authored by
the asker, and over-fetches `custom` documents. The Librarian re-checks every
hit against the live relational row before anything is returned — that check
is authoritative, this filter is the first fence.
"""
from models import Fact, JournalEntry, Visibility

COLLECTION_NAME = "family_memory"

_client = None
_collection = None


def set_client(client):
    """Test hook: inject an EphemeralClient. Resets the cached collection."""
    global _client, _collection
    _client = client
    _collection = None


class EmbeddingModelMismatch(RuntimeError):
    """The persisted collection was built by a different embedding model."""


def _ensure_client():
    global _client
    if _client is None:
        import chromadb
        from chromadb.config import Settings as ChromaSettings

        from config import settings

        _client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    global _client, _collection
    if _collection is None:
        from config import settings

        _ensure_client()
        # Stamp the collection with the model that built it. Vectors from a
        # different model are silently incompatible (same dim ≠ same space),
        # so a mismatch must stop the app, not degrade retrieval.
        _collection = _client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "embedding_model": settings.embedding_model},
        )
        stamped = (_collection.metadata or {}).get("embedding_model")
        if stamped is not None and stamped != settings.embedding_model:
            raise EmbeddingModelMismatch(
                f"chroma_data was built with '{stamped}' but EMBEDDING_MODEL is "
                f"'{settings.embedding_model}'. Run scripts/reindex.py to rebuild "
                "the vectors (or set EMBEDDING_MODEL back)."
            )
    return _collection


def _viewer_ids_string(viewer_ids: list[int]) -> str:
    return "," + ",".join(str(v) for v in sorted(viewer_ids)) + "," if viewer_ids else ""


def entry_metadata(entry: JournalEntry, viewer_ids: list[int]) -> dict:
    return {
        "entry_id": entry.id,
        "fact_id": 0,  # sentinel: chroma metadata cannot hold None
        "author_id": entry.author_id,
        "circle_id": entry.circle_id,
        "visibility": entry.visibility.value,
        "custom_viewer_ids": _viewer_ids_string(viewer_ids),
        "type": "summary",
        "created_at": entry.created_at.isoformat(),
    }


def fact_metadata(fact: Fact, viewer_ids: list[int]) -> dict:
    return {
        "entry_id": fact.entry_id,
        "fact_id": fact.id,
        "author_id": fact.author_id,
        "circle_id": fact.circle_id,
        "visibility": fact.visibility.value,
        "custom_viewer_ids": _viewer_ids_string(viewer_ids),
        "type": fact.type,
        "created_at": fact.created_at.isoformat(),
    }


def reset_collection() -> None:
    """Drop and recreate the collection (fresh model stamp, fresh dimension).
    Used by seed.py and scripts/reindex.py — NOT a per-document delete.
    Deliberately skips the mismatch guard: rebuilding IS the fix."""
    global _collection
    client = _ensure_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = None
    get_collection()


def upsert_documents(ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
    if not ids:
        return
    from memory.embeddings import embed_texts

    get_collection().upsert(
        ids=ids, documents=texts, embeddings=embed_texts(texts), metadatas=metadatas
    )


def delete_documents(ids: list[str]) -> None:
    if ids:
        get_collection().delete(ids=ids)


def visibility_where(asker_id: int, circle_id: int) -> dict:
    """Conservative prefilter (see module docstring). Private docs of other
    authors never leave Chroma; custom docs are over-fetched on purpose."""
    return {
        "$and": [
            {"circle_id": {"$eq": circle_id}},
            {
                "$or": [
                    {"author_id": {"$eq": asker_id}},
                    {"visibility": {"$eq": Visibility.circle.value}},
                    {"visibility": {"$eq": Visibility.custom.value}},
                ]
            },
        ]
    }


def query(text: str, where: dict, n_results: int) -> list[dict]:
    """Returns hits as dicts: {id, text, metadata, distance}."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    from memory.embeddings import embed_texts

    res = collection.query(
        query_embeddings=embed_texts([text]),
        n_results=min(n_results, collection.count()),
        where=where,
    )
    hits = []
    for i in range(len(res["ids"][0])):
        hits.append(
            {
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i] if res.get("distances") else None,
            }
        )
    return hits
