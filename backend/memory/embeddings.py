"""Local embedding function, lazily loaded so uvicorn --reload and non-vector
code paths stay fast. The model name comes from settings.EMBEDDING_MODEL —
changing it requires a re-index (scripts/reindex.py) because vectors from
different models live in incompatible spaces. Tests may inject a fake."""

_model = None
_override = None


def set_embedder(fn):
    """Test hook: replace the embedder with a deterministic fake."""
    global _override
    _override = fn


def embed_texts(texts: list[str]) -> list[list[float]]:
    if _override is not None:
        return _override(texts)
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        from config import settings

        print(
            f"Loading embedding model {settings.embedding_model} "
            "(first run downloads it once)..."
        )
        _model = SentenceTransformer(settings.embedding_model)
    return _model.encode(texts, normalize_embeddings=True).tolist()
