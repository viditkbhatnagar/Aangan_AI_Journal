"""Agent activity feed: a small in-memory, per-user timeline of what each
agent is doing, so the UI can show the machinery at work. Events are scoped
to the user whose request triggered them — never anyone else's."""
import itertools
import time
from collections import defaultdict, deque

_feeds: dict[int, deque] = defaultdict(lambda: deque(maxlen=150))
_ids = itertools.count(1)


def emit(user_id: int | None, agent: str, message: str) -> None:
    if user_id is None:
        return
    _feeds[user_id].append(
        {"id": next(_ids), "ts": time.time(), "agent": agent, "message": message}
    )


def feed(user_id: int, after_id: int = 0) -> list[dict]:
    return [e for e in _feeds[user_id] if e["id"] > after_id]
