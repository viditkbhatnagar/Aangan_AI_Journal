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


def get_collection():
    global _client, _collection
    if _collection is None:
        if _client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            from config import settings

            _client = chromadb.PersistentClient(
                path=settings.chroma_path,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        _collection = _client.get_or_create_collection(
            COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
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
