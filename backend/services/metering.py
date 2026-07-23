"""LLM usage metering. A context var carries who/what triggered the calls so
agents/llm.py can record without threading parameters through every agent.
Metering must never break the product — every write is guarded."""
from contextlib import contextmanager
from contextvars import ContextVar

_ctx: ContextVar[dict | None] = ContextVar("llm_meter_ctx", default=None)


@contextmanager
def context(**fields):
    token = _ctx.set({**(_ctx.get() or {}), **fields})
    try:
        yield
    finally:
        _ctx.reset(token)


def update_context(**fields) -> None:
    current = _ctx.get()
    if current is not None:
        _ctx.set({**current, **fields})


def record_llm(
    agent: str,
    provider: str,
    model: str | None,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
) -> None:
    try:
        from models import LlmCall

        ctx = _ctx.get() or {}
        row = LlmCall(
            agent=agent,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            user_id=ctx.get("user_id"),
            entry_id=ctx.get("entry_id"),
            ask_id=ctx.get("ask_id"),
        )
        caller_session = ctx.get("db")
        if caller_session is not None:
            # ride the caller's transaction: the pipeline holds SQLite's write
            # lock mid-capture, so a separate connection would silently fail
            caller_session.add(row)
            return
        import db as db_module

        session = db_module.SessionLocal()
        try:
            session.add(row)
            session.commit()
        finally:
            session.close()
    except Exception:
        pass  # never let metering break the product


# provenance of the most recent completion, for AskRecord.answered_by
last_provenance: dict = {"provider": "fallback", "model": None}
