"""Local embedding function (all-MiniLM-L6-v2), lazily loaded so uvicorn
--reload and non-vector code paths stay fast. Tests may inject a fake."""

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

        print("Loading embedding model all-MiniLM-L6-v2 (first run downloads ~90 MB)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model.encode(texts, normalize_embeddings=True).tolist()
