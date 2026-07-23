"""A changed EMBEDDING_MODEL against an old vector store must stop the app
with instructions, never silently degrade retrieval. Downloadless: only the
collection stamp is exercised, no model weights load."""
import chromadb
import pytest

from config import settings
from memory import store


def test_mismatched_model_raises_and_reset_rebuilds(monkeypatch):
    store.set_client(chromadb.EphemeralClient())
    monkeypatch.setattr(settings, "embedding_model", "model-a")
    created = store.get_collection()
    assert created.metadata["embedding_model"] == "model-a"

    # simulate a restart with a different configured model
    store._collection = None
    monkeypatch.setattr(settings, "embedding_model", "model-b")
    with pytest.raises(store.EmbeddingModelMismatch, match="model-a"):
        store.get_collection()

    # the documented fix rebuilds the collection under the new stamp
    store.reset_collection()
    rebuilt = store.get_collection()
    assert rebuilt.metadata["embedding_model"] == "model-b"


def test_pre_stamp_collections_are_grandfathered(monkeypatch):
    """Collections created before stamping existed (no embedding_model key)
    must keep working — reseed/reindex will stamp them eventually."""
    client = chromadb.EphemeralClient()
    client.get_or_create_collection(store.COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    store.set_client(client)
    monkeypatch.setattr(settings, "embedding_model", "model-c")
    assert store.get_collection() is not None
